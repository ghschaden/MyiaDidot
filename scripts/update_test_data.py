"""Regenerate the test baselines in tests/data/ on purpose.

    python scripts/update_test_data.py --golden --digest --cmap --expect-changes N
    python scripts/update_test_data.py --exceptions   # only adds, with a reason
    python scripts/update_test_data.py --lint --ufo UFO --reason "..."
    python scripts/update_test_data.py --quality --ufo UFO --reason "..."
    python scripts/update_test_data.py --emboldened --ufo UFO --reason "..."
    python scripts/update_test_data.py --styles --ufo UFO --reason "..."
    python scripts/update_test_data.py --lookups --ufo UFO
    python scripts/update_test_data.py --greek --ufo UFO --reason "..."

Every run accepts the font's current behaviour as correct, so run it only
for an intended change, and review `git diff tests/data` before committing.
--golden and --digest first shape compare_shaping.py's corpus with the
style as committed (HEAD) and as it is now, as `make regress` does, and
refuse unless --expect-changes gives the number of strings that differ:
run once without it, read the differences shown, then give the number.
--cmap only ever adds code points (the coverage ratchet). --exceptions adds
the current NFD/composite/fontbakery failures that are not listed yet, under
the reason given with --reason, and leaves existing entries alone. --lint
rewrites the style's list of known glyph_lint.py findings (glyph-lint.txt,
glyph-lint-Italic.txt ...): those still found keep their reasons, new ones
get --reason, fixed ones go. --quality does the same for the list of known
scripts/quality/checks.py findings (quality.txt, quality-Italic.txt ...).
--emboldened: the derived letters a weighted style leaves emboldened whole
(emboldened-whole-Bold.txt ..., from the style's lib, make_bold.WHOLE_KEY).
--styles: where a generated style differs from the Regular
(styles-agree-Italic.txt ..., tests/test_styles_agree.py). --lookups
rewrites the style's compiled lookup order (lookups.txt, lookups-Italic.txt
..., tests/test_lookups.py): read the diff first. --greek: the Greek pairs
where Charis and Libertinus agree against the style (greek-pairs.txt ...,
tests/test_greek_pairs.py), each with how far off it is now.
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
from test_composites import (
    composite_mismatches,
    nfd_mismatches,
    read_list,
    smallcap_mismatches,
)
from test_fontbakery import fontbakery_failures
from test_glyph_lint import lint_keys
from test_quality import quality_keys


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


def shaping_changes(ufo_path, otf, tmp):
    """(strings shaped, [(text, features, language, HEAD's, now)]) over
    compare_shaping's corpus, against the style as committed; None for a
    style not committed yet."""
    import subprocess

    from compare_shaping import Shaper as CorpusShaper
    from compare_shaping import corpus

    rel = Path(ufo_path).resolve().relative_to(ROOT)
    head = tmp / "head"
    head.mkdir()
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", "HEAD", str(rel)],
                             capture_output=True, check=False)
    if archive.returncode:
        return None
    subprocess.run(["tar", "-x", "-C", str(head)], input=archive.stdout, check=True)
    head_otf = tmp / "head.otf"
    ufo2ft.compileOTF(ufoLib2.Font.open(head / rel), useProductionNames=False, optimizeCFF=0).save(head_otf)
    ref, new = CorpusShaper(str(head_otf)), CorpusShaper(str(otf))
    total, diffs = 0, []
    for text, feats, script, lang in corpus(ref.cmap):
        total += 1
        a, b = ref.shape(text, feats, script, lang), new.shape(text, feats, script, lang)
        if a != b:
            diffs.append((text, feats, lang, a, b))
    return total, diffs


def check_changes(ufo_path, otf, tmp, expected, show=20):
    """Refuse to take a shaping baseline unless the number of strings that
    changed against HEAD is the number the person read (CLAUDE.md: read
    `make regress` before accepting a new baseline)."""
    found = shaping_changes(ufo_path, otf, tmp)
    if found is None:
        print("not committed yet: no shaping to compare against")
        return
    total, diffs = found
    glyphs = sum(1 for *_, a, b in diffs if [g[0] for g in a] != [g[0] for g in b])
    print(f"{total} strings shaped, {len(diffs)} differ from HEAD "
          f"({glyphs} in their glyphs, {len(diffs) - glyphs} in positions only)")
    if expected == len(diffs):
        return
    for text, feats, lang, a, b in diffs[:show]:
        print(f"\n{text!r} {feats or ''} {lang or ''}\n  HEAD: {a}\n  now:  {b}")
    if len(diffs) > show:
        print(f"\n... and {len(diffs) - show} more (make regress shows the Regular's)")
    sys.exit(f"\nbaselines not written: {len(diffs)} strings differ, --expect-changes said "
             f"{expected}. If these are the changes meant, rerun with --expect-changes {len(diffs)}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ufo", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("--golden", action="store_true")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--cmap", action="store_true")
    ap.add_argument("--exceptions", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--quality", action="store_true")
    ap.add_argument("--emboldened", action="store_true")
    ap.add_argument("--styles", action="store_true")
    ap.add_argument("--lookups", action="store_true")
    ap.add_argument("--greek", action="store_true")
    ap.add_argument("--reason", default="baseline")
    ap.add_argument("--expect-changes", type=int, metavar="N",
                    help="strings shaped otherwise than by HEAD's font, as read (--golden, --digest)")
    args = ap.parse_args()
    lists = []
    if args.lint:
        lists.append(("glyph-lint.txt", "glyph_lint.py", lambda: lint_keys(ufoLib2.Font.open(args.ufo))))
    if args.quality:
        lists.append(("quality.txt", "scripts/quality/checks.py",
                      lambda: quality_keys(ufoLib2.Font.open(args.ufo), args.ufo)))
    if args.emboldened:
        from make_bold import WHOLE_KEY

        lists.append(("emboldened-whole.txt", "make_bold.py/make_italic.py emboldened-whole",
                      lambda: dict(ufoLib2.Font.open(args.ufo).lib.get(WHOLE_KEY, {}))))
    if args.styles:
        from test_styles_agree import REGULAR, differences

        lists.append(("styles-agree.txt", "tests/test_styles_agree.py",
                      lambda: differences(ufoLib2.Font.open(REGULAR), ufoLib2.Font.open(args.ufo))))
    for name, tool, keys in lists:
        path = style_data(name, args.ufo)
        listed = read_list(path.name)
        found = keys()
        what = {"emboldened-whole.txt": "glyph: why", "styles-agree.txt": "kind glyph [detail]"}.get(
            name, "glyph kind count")
        lines = [f"# Known {tool} findings ({what}); fixing one = deleting its line.\n"]
        for k in sorted(found):
            why = listed.get(k) or f"{args.reason}: {found[k]}"[:200]
            lines.append(f"{k:32} # {why}\n")
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{path.name}: {len(found)} findings, {len(set(found) - set(listed))} new, "
              f"{len(set(listed) - set(found))} gone")
    shaping = (args.golden, args.digest, args.cmap, args.exceptions, args.lookups, args.greek)
    if lists and not any(shaping):
        return
    if not any(shaping):
        ap.error("say what to update")

    import tempfile

    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ufo, otf, release, decp = build(args.ufo, Path(tmp))
        tt, shaper = TTFont(otf), Shaper(otf)
        if args.golden or args.digest:
            check_changes(args.ufo, otf, Path(tmp), args.expect_changes)

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
        if args.greek:
            from test_greek_pairs import greek_findings

            path = style_data("greek-pairs.txt", args.ufo)
            listed = read_list(path.name)
            found = greek_findings(args.ufo, otf)
            if found is None:
                sys.exit("--greek: references or UDHR texts missing (build/refs/, make udhr)")
            lines = [("# Greek pairs where Charis and Libertinus agree against Myia (pair  # off N: why), "
                      "N in n n gaps; fixing one = deleting its line.\n")]
            for p, off in sorted(found.items()):
                why = listed.get(p, "").split(": ", 1)[-1] if p in listed else args.reason
                lines.append(f"{p:8} # off {off:+.3f}: {why}\n")
            path.write_text("".join(lines), encoding="utf-8")
            print(f"{path.name}: {len(found)} pairs, {len(set(found) - set(listed))} new, "
                  f"{len(set(listed) - set(found))} gone")
        if args.lookups:
            from test_lookups import lookup_summary

            path = style_data("lookups.txt", args.ufo)
            found = lookup_summary(tt)
            old = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
            path.write_text("\n".join(found) + "\n", encoding="utf-8")
            print(f"{path.name}: {len(found)} lookups, {len(set(found) - set(old))} new lines, "
                  f"{len(set(old) - set(found))} gone")
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
