"""What the generated styles would change if they were made again: in seconds.

    python scripts/stale.py                  # glyphs whose source changed since the last generate
    python scripts/stale.py stamp            # record the sources as generated (make generate does)
    python scripts/stale.py mark-regular [STATUS]  # record that make check-regular ran on this Regular
    python scripts/stale.py guard            # exit 1 unless they did for the Regular as it is now

`make generate` makes the Italic and Bold from the Regular, then the Bold
Italic from the Italic. At its end the stamp records each source glyph's
fingerprint (built_from.fingerprint: decomposed outline, width, anchors)
and a hash of every generator file. Afterwards:

- a source glyph whose fingerprint differs is stale in the styles made from
  it, and so is every composite that contains it (the fingerprint is
  decomposed): the Regular's for the Italic and Bold, the Italic's for the
  Bold Italic (so a hand fix in a drawn Italic glyph shows up there);
- a changed generator file makes everything possibly stale; the stroke
  cache (stroke_cache.py) decides what a run really redoes.

It does not say what a run will make of them (a glyph marked drawn is kept
as saved); `make reproduce` stays the proof. Not covered: kerning and
features, which the generators also read.

`guard` is the check `make generate` begins with: the Regular must have
been through `make check-regular` as it now stands (`mark-regular`), unless
SKIP_CHECK is set in the environment.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
DIR = ROOT / "build" / "stale"
STAMP = DIR / "stamp.json"
REGULAR_MARK = DIR / "regular-checked.json"
FAMILY = "MyiaDidot"

# what a style is made from
SOURCE_OF = {"Italic": "Regular", "Bold": "Regular", "BoldItalic": "Italic"}
GENERATOR_GLOBS = [
    "make_italic.py", "make_bold.py", "smallcaps.py", "derive.py", "stroke*.py", "fair_arcs.py",
    "data_*.py", "drawn.py", "ufo_io.py", "fontforge_inputs.py", "smallcaps_draft.py",
]


def fingerprints(style):
    font = ufoLib2.Font.open(SOURCES / f"{FAMILY}-{style}.ufo")
    return {g.name: fingerprint(font, g.name) for g in font}


def generator_hashes():
    out = {}
    for pattern in GENERATOR_GLOBS:
        for p in sorted((ROOT / "scripts").glob(pattern)):
            out[p.name] = hashlib.sha1(p.read_bytes()).hexdigest()[:12]
    return out


def regular_hash():
    h = hashlib.sha1()
    for name, fp in sorted(fingerprints("Regular").items()):
        h.update(f"{name}:{fp}\n".encode())
    return h.hexdigest()[:16]


def stamp():
    DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "sources": {src: fingerprints(src) for src in sorted(set(SOURCE_OF.values()))},
        "generators": generator_hashes(),
    }
    STAMP.write_text(json.dumps(data))
    print(f"stamped {sum(len(v) for v in data['sources'].values())} source glyphs, "
          f"{len(data['generators'])} generator files")


def report():
    if not STAMP.exists():
        print("no stamp yet: it is written at the end of the next make generate "
              "(python scripts/stale.py stamp records the sources as they are now)")
        return 0
    old = json.loads(STAMP.read_text())
    code = generator_hashes()
    changed_code = sorted(n for n in set(code) | set(old["generators"]) if code.get(n) != old["generators"].get(n))
    if changed_code:
        print("generator files changed since the stamp (everything may differ; the stroke cache "
              "decides what a run redoes):", *changed_code)
    total = 0
    for src, was in old["sources"].items():
        now = fingerprints(src)
        diff = sorted(n for n in set(now) | set(was) if now.get(n) != was.get(n))
        total += len(diff)
        styles = [s for s, of in SOURCE_OF.items() if of == src]
        print(f"{src} -> {', '.join(styles)}: {len(diff)} glyphs changed since generate"
              + (":" if diff else ""))
        if diff:
            shown = diff if len(diff) <= 60 else diff[:60] + [f"... {len(diff) - 60} more"]
            print("  " + " ".join(shown))
    if not total and not changed_code:
        print("nothing stale: make generate would change nothing")
    return 0


def mark_regular(status="0"):
    DIR.mkdir(parents=True, exist_ok=True)
    REGULAR_MARK.write_text(json.dumps({"regular": regular_hash(), "passed": status == "0"}))
    print("the Regular is marked as checked" + ("" if status == "0" else " (with failures: review them)"))


def guard():
    if os.environ.get("SKIP_CHECK"):
        print("SKIP_CHECK set: the Regular's check is not required")
        return 0
    if REGULAR_MARK.exists():
        mark = json.loads(REGULAR_MARK.read_text())
        if mark.get("regular") == regular_hash():
            if not mark.get("passed"):
                print("note: make check-regular had failures on this Regular; generating on the "
                      "strength of their review")
            return 0
    print("make generate: the Regular has changed since `make check-regular` last ran "
          "(or it never did). Run it first (a minute or two), or set SKIP_CHECK=1.")
    return 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    rest = sys.argv[2:]
    sys.exit({"report": report, "stamp": lambda: stamp() or 0,
              "mark-regular": lambda: mark_regular(*rest) or 0, "guard": guard}[cmd]())
