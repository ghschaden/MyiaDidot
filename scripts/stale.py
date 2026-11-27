"""What the generated styles would change if they were made again: in seconds.

    python scripts/stale.py                  # glyphs whose source changed since the last generate
    python scripts/stale.py stamp [STYLE ...]  # record the sources as generated, for those styles (make generate does)
    python scripts/stale.py styles           # the styles a run must make (make generate STYLES=auto)
    python scripts/stale.py proven [STAMP]   # exit 0 if make reproduce would only repeat the last run
    python scripts/stale.py unproven [STAMP] # the styles make reproduce must make again (the hook's)
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
as saved); `make reproduce` stays the proof. A source's kerning, groups and
features count as three entries of its own (`@kerning` ...).

The stamp is kept per style, so a run that makes only some styles stamps
only those. `styles` names the styles a run must make: a style whose
source changed, or one of whose generator files did (`REACHES`: which
generator files can change which style, the rest reaching all), and the
Bold Italic whenever the Italic is made (it is made from it).

`guard` is the check `make generate` begins with: the Regular must have
been through `make check-regular` as it now stands (`mark-regular`), unless
SKIP_CHECK is set in the environment.
"""

import ast
import hashlib
import json
import os
import plistlib
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
    "data_*.py", "drawn.py", "ufo_io.py", "winding.py", "fontforge_inputs.py", "smallcaps_draft.py",
]


STYLES = ["Italic", "Bold", "BoldItalic"]
# generator files that can change only some styles (checked 2026-11-21 in
# make_bold.py: every use of data_italic's and data_bold_italic's tables,
# and every import from make_italic, is behind its `italic` flag, so the
# upright Bold reads none of them); a file not named reaches every style
REACHES = {
    "make_italic.py": {"Italic", "BoldItalic"},
    "data_italic.py": {"Italic", "BoldItalic"},
    "fontforge_inputs.py": {"Italic", "BoldItalic"},
    "smallcaps_draft.py": {"Italic", "BoldItalic"},
    "data_bold_italic.py": {"BoldItalic"},
}
EXTRA_FILES = ("kerning.plist", "groups.plist", "features.fea")


def fingerprints(style):
    path = SOURCES / f"{FAMILY}-{style}.ufo"
    font = ufoLib2.Font.open(path)
    out = {g.name: fingerprint(font, g.name) for g in font}
    for name in EXTRA_FILES:
        f = path / name
        out["@" + name.split(".")[0]] = hashlib.sha1(f.read_bytes()).hexdigest()[:12] if f.exists() else None
    return out


ENTRIES = ("make_italic", "make_bold", "smallcaps")


def generator_hashes():
    """the generator files: GENERATOR_GLOBS (smallcaps_draft.py is run by
    FontForge, not imported) and every project module the generators import
    at any depth (stroke_cache.modules; 2026-11-21: the globs alone missed
    composites, kern_clear, respace and some thirty more)"""
    import stroke_cache

    names = {p.name for pattern in GENERATOR_GLOBS for p in (ROOT / "scripts").glob(pattern)}
    for entry in ENTRIES:
        names |= {f"{m}.py" for m in stroke_cache.modules(entry)}
    return {n: hashlib.sha1(code_bytes(ROOT / "scripts" / n)).hexdigest()[:12] for n in sorted(names)}


def code_bytes(path):
    """what a script file contributes to a run: for Python its syntax tree
    without docstrings (comments are not in it, line numbers left out), so
    an edit to comments or docstrings alone keeps the stamp and the proof
    (T8, 2026-11-27); any other file, or Python that does not parse, as its
    bytes"""
    data = path.read_bytes()
    if path.suffix != ".py":
        return data
    try:
        tree = ast.parse(data)
    except (SyntaxError, ValueError):
        return data
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:]
    return ast.dump(tree).encode()


def scripts_digest(root=None):
    """scripts/ as a run reads it: every file but those in dot-directories
    (ruff's .ruff_cache, which only the working copy has: with it the proof
    stamped there never held in the hook's snapshot, 2026-11-27) and
    __pycache__, Python by code_bytes"""
    root = Path(root) if root else ROOT / "scripts"
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        rel = item.relative_to(root)
        if not item.is_file() or "__pycache__" in rel.parts or any(p.startswith(".") for p in rel.parts[:-1]):
            continue
        digest.update(str(rel).encode() + b"\0" + code_bytes(item) + b"\0")
    return digest.hexdigest()


# what a style's proof is taken over: a run of the generators made these
# outputs from these inputs (the hook's `proven`, instead of make reproduce)
PROOF_FILES = ("Makefile", "pyproject.toml", "uv.lock", ".python-version",
               # read by make_italic and make_bold (their NFD check)
               "tests/data/nfd-exceptions.txt")
DRAFTS = SOURCES / "drafts" / "Italic-smallcaps.ufo"


def proof_inputs(style):
    """a digest of everything a run of style reads: its source UFO (as
    ufo_digest reads it: the acceptances accepted.py writes after a run left
    out, or accepting the Italic's glyphs unproved the Bold Italic made from
    them and cost the hook a reproduce, 2026-11-22), every file under
    scripts/ (scripts_digest: blind to comments and docstrings), the build files and the toolchain (strict: any other change
    there and the proof no longer holds)"""
    from build_support import content_hash, json_digest, toolchain

    parts = {"source": ufo_digest(SOURCES / f"{FAMILY}-{SOURCE_OF[style]}.ufo"),
             "scripts": scripts_digest(),
             "files": {n: content_hash(ROOT / n) for n in PROOF_FILES if (ROOT / n).exists()},
             "toolchain": toolchain()}
    if style == "Italic":
        parts["oldstand"] = content_hash(SOURCES / "oldstand")
    return json_digest(parts)


def ufo_digest(path):
    """the UFO's content, without the acceptances accepted.py writes into a
    generated style after its run (glyph lib KEY; the generators carry them
    over, so they are not what a run makes)"""
    from accepted import KEY

    font = ufoLib2.Font.open(path, lazy=False)

    def glyph(g):
        return [g.width, g.height, sorted(g.unicodes),
                [[(p.x, p.y, p.type, p.smooth) for p in c] for c in g.contours],
                [(c.baseGlyph, tuple(c.transformation)) for c in g.components],
                [(a.name, a.x, a.y) for a in g.anchors],
                {k: v for k, v in g.lib.items() if k != KEY}]

    info = Path(path) / "fontinfo.plist"
    blob = json.dumps({"glyphs": {g.name: glyph(g) for g in font}, "order": font.glyphOrder,
                       "lib": dict(font.lib), "kerning": {" ".join(k): v for k, v in font.kerning.items()},
                       "groups": dict(font.groups), "features": font.features.text,
                       "info": plistlib.loads(info.read_bytes()) if info.exists() else None},
                      sort_keys=True, ensure_ascii=False, default=repr)
    return hashlib.sha256(blob.encode()).hexdigest()


def proof_output(style):
    out = ufo_digest(SOURCES / f"{FAMILY}-{style}.ufo")
    return out + (":" + ufo_digest(DRAFTS) if style == "Italic" and DRAFTS.exists() else "")


def plain_run():
    """no switch that makes a run other than make reproduce's"""
    import stroke_cache

    return not os.environ.get("KEEP_DRAFTS") and not [
        k for k in os.environ if k.startswith("MYIA_") and k not in stroke_cache.STEERING]


def regular_hash():
    h = hashlib.sha1()
    for name, fp in sorted(fingerprints("Regular").items()):
        h.update(f"{name}:{fp}\n".encode())
    return h.hexdigest()[:16]


def load():
    """the stamp per style, {style: {"source": fingerprints, "generators": hashes}}
    (a stamp of the older, whole form stands for every style)"""
    if not STAMP.exists():
        return {}
    data = json.loads(STAMP.read_text())
    if "styles" in data:
        return data["styles"]
    return {s: {"source": data["sources"][SOURCE_OF[s]], "generators": data["generators"]} for s in STYLES}


def stamp(*styles):
    proof = "--no-proof" not in styles
    styles = [s for s in styles if s != "--no-proof"] or STYLES
    unknown = [s for s in styles if s not in STYLES]
    if unknown:
        raise SystemExit(f"stale.py stamp: no such style {unknown}")
    DIR.mkdir(parents=True, exist_ok=True)
    data, code = load(), generator_hashes()
    prints = {src: fingerprints(src) for src in {SOURCE_OF[s] for s in styles}}
    proof = proof and plain_run()
    for s in styles:
        data[s] = {"source": prints[SOURCE_OF[s]], "generators": code}
        if proof:
            data[s]["proof"] = {"inputs": proof_inputs(s), "output": proof_output(s)}
    STAMP.write_text(json.dumps({"styles": data}))
    print(f"stamped {', '.join(styles)}: {sum(len(v) for v in prints.values())} source entries, "
          f"{len(code)} generator files" + ("" if proof else " (no proof: not a plain run)"))


def unproven(stamp_path=None, say=print):
    """the styles a plain make generate did not make, from inputs exactly as
    they are here, into what they still are: those make reproduce must make
    again (each style's proof on its own; FULL_REPRODUCE: all). The hook
    runs this in its snapshot of the staged tree, with the working copy's
    stamp."""
    path = Path(stamp_path) if stamp_path else STAMP
    if os.environ.get("FULL_REPRODUCE"):
        say("proven: FULL_REPRODUCE set")
        return list(STYLES)
    if not path.exists():
        say("proven: no stamp")
        return list(STYLES)
    data = json.loads(path.read_text()).get("styles", {})
    out = []
    for s in STYLES:
        p = data.get(s, {}).get("proof")
        if not p:
            say(f"proven: {s} has no proof (not made by a plain make generate since)")
        elif p["inputs"] != proof_inputs(s):
            say(f"proven: {s}: its inputs changed since it was made")
        elif p["output"] != proof_output(s):
            say(f"proven: {s} is not what make generate wrote")
        else:
            say(f"proven: {s} is exactly what make generate made from these inputs")
            continue
        out.append(s)
    return out


def proven(stamp_path=None):
    """exit 0 if no style is unproven (make reproduce would only repeat the run)"""
    return 1 if unproven(stamp_path) else 0


def changed(a, b):
    return sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n))


def styles():
    """the styles a run must make, in STYLES' order (all without a stamp)"""
    data, code = load(), generator_hashes()
    prints, need = {}, set()
    for s in STYLES:
        if s not in data:
            need.add(s)
            continue
        files = changed(code, data[s]["generators"])
        if any(s in REACHES.get(f, set(STYLES)) for f in files):
            need.add(s)
            continue
        src = SOURCE_OF[s]
        if src not in prints:
            prints[src] = fingerprints(src)
        if changed(prints[src], data[s]["source"]):
            need.add(s)
    if "Italic" in need:
        need.add("BoldItalic")
    print(" ".join(s for s in STYLES if s in need))
    return 0


def report():
    if not STAMP.exists():
        print("no stamp yet: it is written at the end of the next make generate "
              "(python scripts/stale.py stamp records the sources as they are now)")
        return 0
    data, code, prints = load(), generator_hashes(), {}
    total = 0
    for s in STYLES:
        if s not in data:
            print(f"{s}: never stamped")
            total += 1
            continue
        files = changed(code, data[s]["generators"])
        src = SOURCE_OF[s]
        if src not in prints:
            prints[src] = fingerprints(src)
        diff = changed(prints[src], data[s]["source"])
        total += len(diff) + len(files)
        print(f"{src} -> {s}: {len(diff)} source entries changed since it was made"
              + (f"; generator files changed: {' '.join(files)}" if files else "") + (":" if diff else ""))
        if diff:
            shown = diff if len(diff) <= 60 else diff[:60] + [f"... {len(diff) - 60} more"]
            print("  " + " ".join(shown))
    if not total:
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
    sys.exit({"report": report, "stamp": lambda: stamp(*rest) or 0, "styles": styles, "proven": lambda: proven(*rest),
              "unproven": lambda: print(" ".join(unproven(*rest, say=lambda m: print(m, file=sys.stderr)))) or 0,
              "mark-regular": lambda: mark_regular(*rest) or 0, "guard": guard}[cmd]())
