"""Regenerate the test baselines in tests/data/ on purpose.

    python scripts/update_test_data.py --golden --digest --cmap
    python scripts/update_test_data.py --exceptions   # only adds, with a reason
    python scripts/update_test_data.py --lint --ufo UFO --reason "..."

Every run accepts the font's current behaviour as correct, so run it only
for an intended change, and review `git diff tests/data` before committing.
--cmap only ever adds code points (the coverage ratchet). --exceptions adds
the current NFD/composite/fontbakery failures that are not listed yet, under
the reason given with --reason, and leaves existing entries alone. --lint
rewrites the style's list of known glyph_lint.py findings (glyph-lint.txt,
glyph-lint-Italic.txt ...): those still found keep their reasons, new ones
get --reason, fixed ones go.
"""

import argparse
import json
import sys
from pathlib import Path

import ufo2ft
import ufoLib2
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
DATA = TESTS / "data"
sys.path[:0] = [str(TESTS), str(ROOT / "scripts")]

from conftest import Shaper, style_data
from shaping import full_digest, shape_golden
from test_composites import composite_mismatches, nfd_mismatches, read_list, smallcap_mismatches
from test_fontbakery import fontbakery_failures
from test_glyph_lint import lint_keys


def build(ufo_path, tmp):
    font = ufoLib2.Font.open(ufo_path)
    otf = tmp / "test.otf"
    ufo2ft.compileOTF(font, useProductionNames=False, optimizeCFF=0).save(otf)
    release = tmp / "release.otf"
    ufo2ft.compileOTF(ufoLib2.Font.open(ufo_path)).save(release)
    dec = TTFont(otf)
    import unicodedata

    for table in dec["cmap"].tables:
        for cp in list(table.cmap):
            if len(unicodedata.normalize("NFD", chr(cp))) > 1:
                del table.cmap[cp]
    decp = tmp / "decomposed.otf"
    dec.save(decp)
    return font, otf, release, decp


def append_exceptions(name, keys, reason, header):
    path = DATA / name
    existing = read_list(name)
    add = [(k, why) for k, why in keys if k not in existing]
    if not path.exists():
        path.write_text(header, encoding="utf-8")
    if add:
        with path.open("a", encoding="utf-8") as fh:
            for k, why in add:
                fh.write(f"{k:24} # {reason}: {why}\n")
    print(f"{name}: {len(add)} added, {len(existing)} kept")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ufo", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("--golden", action="store_true")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--cmap", action="store_true")
    ap.add_argument("--exceptions", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--reason", default="baseline")
    args = ap.parse_args()
    if args.lint:
        path = style_data("glyph-lint.txt", args.ufo)
        listed = read_list(path.name)
        found = lint_keys(ufoLib2.Font.open(args.ufo))
        lines = ["# Known glyph_lint.py findings (glyph kind count); fixing one = deleting its line.\n"]
        for k in sorted(found):
            why = listed.get(k) or f"{args.reason}: {found[k]}"[:200]
            lines.append(f"{k:32} # {why}\n")
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{path.name}: {len(found)} findings, {len(set(found) - set(listed))} new, "
              f"{len(set(listed) - set(found))} gone")
        if not any((args.golden, args.digest, args.cmap, args.exceptions)):
            return
    if not any((args.golden, args.digest, args.cmap, args.exceptions)):
        ap.error("say what to update")

    import tempfile

    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ufo, otf, release, decp = build(args.ufo, Path(tmp))
        tt, shaper = TTFont(otf), Shaper(otf)

        if args.golden:
            golden = shape_golden(shaper)
            path = style_data("shaping-golden.json", args.ufo)
            path.write_text(json.dumps(golden, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
            print(f"{path.name}: {len(golden)} cases")
        if args.digest:
            digest, n = full_digest(shaper, tt.getBestCmap())
            path = style_data("shaping-digest.txt", args.ufo)
            path.write_text(f"{digest} {n}\n")
            print(f"{path.name}: {n} strings")
        if args.cmap:
            path = DATA / "cmap.txt"
            old = {int(x, 16) for x in path.read_text().split()} if path.exists() else set()
            new = old | set(tt.getBestCmap())
            path.write_text("\n".join(f"{u:04X}" for u in sorted(new)) + "\n")
            print(f"cmap.txt: {len(new) - len(old)} code points added, {len(new)} total")
        if args.exceptions:
            nfd = nfd_mismatches(tt, shaper, Shaper(decp))
            append_exceptions(
                "nfd-exceptions.txt", sorted(nfd.items()), args.reason,
                "# Precomposed characters allowed to render differently from their\n"
                "# decomposition (base + positioned marks). Remove a line once fixed.\n")
            sc = smallcap_mismatches(tt, shaper, Shaper(decp))
            append_exceptions(
                "smallcap-nfd-exceptions.txt", sorted(sc.items()), args.reason,
                "# Small caps (smcp/c2sc) allowed to differ between precomposed and\n"
                "# decomposed input. Remove a line once fixed.\n")
            comp = composite_mismatches(ufo)
            append_exceptions(
                "composite-exceptions.txt", sorted(comp.items()), args.reason,
                "# Composites allowed to differ from scripts/composites.py's rules.\n")
            fb = fontbakery_failures(release, Path(tmp))
            append_exceptions(
                "fontbakery-allow.txt",
                sorted((k, " ".join(" / ".join(str(m) for m in v).split())[:160])
                       for k, v in fb.items()),
                args.reason, "# fontbakery check-universal failures accepted for now.\n")


if __name__ == "__main__":
    main()
