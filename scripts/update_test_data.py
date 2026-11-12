"""Regenerate the test baselines in tests/data/ on purpose.

    python scripts/update_test_data.py --golden --digest --cmap --expect-changes N
    python scripts/update_test_data.py --exceptions   # only adds, with a reason
    python scripts/update_test_data.py --lint --ufo UFO --reason "..."
    python scripts/update_test_data.py --quality --ufo UFO --reason "..."
    python scripts/update_test_data.py --emboldened --ufo UFO --reason "..."
    python scripts/update_test_data.py --styles --ufo UFO --reason "..."
    python scripts/update_test_data.py --lookups --ufo UFO
    python scripts/update_test_data.py --greek --ufo UFO --reason "..."
    python scripts/update_test_data.py --hinting --ufo UFO --reason "..."

Every run accepts the font's current behaviour as correct, so run it only
for an intended change, and review `git diff tests/data` before committing.
--golden and --digest first shape compare_shaping.py's corpus with the
style as committed (HEAD) and as it is now, as `make regress` does, and
write a complete JSON report and require --accept-report SHA256 when changes
exist. Review that exact report before accepting. --expect-changes optionally
checks the count as well; a count alone never accepts changed shaping.
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
(styles-agree-Italic.txt ..., tests/test_styles_agree.py). --hinting: the
letters hinted off their zones (hint-zones.txt, hint-zones-Italic.txt ...,
and the CFF fonts' hint-zones-cff.txt ..., tests/test_hinting.py). --lookups
rewrites the style's compiled lookup order (lookups.txt, lookups-Italic.txt
..., tests/test_lookups.py): read the diff first. --greek: the Greek pairs
where Charis and Libertinus agree against the style (greek-pairs.txt ...,
tests/test_greek_pairs.py), each with how far off it is now. --cyrillic:
the Cyrillic pairs outside the references' whole range (cyrillic-pairs.txt
..., tests/test_cyrillic_pairs.py). --latin: the italics' Latin pairs
outside the reference italics' range (latin-pairs-Italic.txt ...,
tests/test_latin_pairs.py), off in shares of the rhythm.
"""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import ufoLib2
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
DATA = TESTS / "data"
sys.path[:0] = [str(TESTS), str(ROOT / "scripts")]

from baseline_support import style_data
from build_support import atomic_output, content_hash, json_digest, publish_files, toolchain
from font_builds import Builds, compiled_variant
from font_shaping import Shaper
from shaping_baselines import full_digest, shape_golden
from test_composites import (
    composite_mismatches,
    nfd_mismatches,
    read_list,
    smallcap_mismatches,
)
from test_fontbakery import fontbakery_failures
from test_glyph_lint import lint_keys
from test_quality import quality_keys


def append_exceptions(outputs, name, keys, reason, header):
    path = DATA / name
    existing = read_list(name)
    add = [(k, why) for k, why in keys if k not in existing]
    text = path.read_text(encoding="utf-8") if path.exists() else header
    text += "".join(f"{k:24} # {reason}: {why}\n" for k, why in add)
    outputs[path] = text
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
    head_otf = compiled_variant(head / rel, "test_otf")
    ref, new = CorpusShaper(str(head_otf)), CorpusShaper(str(otf))
    total, diffs, digest = 0, [], hashlib.sha256()
    for text, feats, script, lang in corpus(ref.cmap):
        total += 1
        a, b = ref.shape(text, feats, script=script, language=lang), new.shape(text, feats, script=script, language=lang)
        digest.update(json.dumps([text, b], ensure_ascii=False).encode())
        if a != b:
            diffs.append({"text": text, "features": feats, "script": script, "language": lang,
                          "before": a, "after": b})
    return total, diffs, (digest.hexdigest() if ref.cmap == new.cmap else None)


def check_changes(ufo_path, otf, tmp, expected, accepted=None, report_path=None):
    """Require acceptance of the exact report, not merely its change count."""
    found = shaping_changes(ufo_path, otf, tmp)
    if found is None:
        raise SystemExit("cannot accept shaping without a committed reference style")
    total, diffs, digest = found
    report = {"source": str(Path(ufo_path).resolve().relative_to(ROOT)),
              "source_sha256": content_hash(ufo_path), "compiled_sha256": content_hash(otf),
              "toolchain": toolchain(), "scripts_sha256": content_hash(ROOT / "scripts"),
              "strings": total, "changes": diffs}
    # Compiler-generated timestamps are deliberately excluded from approval:
    # source content, toolchain and exact shaped changes establish its identity.
    identity = {k: v for k, v in report.items() if k != "compiled_sha256"}
    approval = json_digest(identity)
    report["approval_sha256"] = approval
    report_path = report_path or ROOT / "build" / "baseline-review.json"
    with atomic_output(report_path) as temporary:
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{total} strings shaped, {len(diffs)} differ from HEAD; full report: {report_path}")
    if expected is not None and expected != len(diffs):
        raise SystemExit(f"baselines not written: expected {expected} changes, found {len(diffs)}")
    if diffs and accepted != approval:
        raise SystemExit(f"baselines not written: review {report_path}, then use --accept-report {approval}")
    if accepted is not None and accepted != approval:
        raise SystemExit("baselines not written: accepted report no longer matches the inputs")
    return (digest, total) if digest is not None else None


def main():
    outputs = {}
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
    ap.add_argument("--hinting", action="store_true")
    ap.add_argument("--lookups", action="store_true")
    ap.add_argument("--greek", action="store_true")
    ap.add_argument("--cyrillic", action="store_true")
    ap.add_argument("--latin", action="store_true")
    ap.add_argument("--reason", default="baseline")
    ap.add_argument("--expect-changes", type=int, metavar="N",
                    help="strings shaped otherwise than by HEAD's font, as read (--golden, --digest)")
    ap.add_argument("--accept-report", metavar="SHA256", help="digest of the exact shaping report reviewed")
    ap.add_argument("--report", type=Path, help="complete shaping report (default: build/baseline-review.json)")
    args = ap.parse_args()
    source_identity = content_hash(args.ufo)

    def publish():
        if content_hash(args.ufo) != source_identity:
            raise SystemExit("baselines not written: source changed during review; retry")
        publish_files(outputs)

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
    if args.hinting:
        from test_hinting import hinting_keys

        def hint_keys():
            with tempfile.TemporaryDirectory() as tmp:
                return hinting_keys(args.ufo, Path(tmp))

        def cff_keys():
            from test_hinting import cff_hinting_keys

            with tempfile.TemporaryDirectory() as tmp:
                return cff_hinting_keys(args.ufo, Path(tmp))

        lists.append(("hint-zones.txt", "scripts/quality/hint_zones.py", hint_keys))
        lists.append(("hint-zones-cff.txt", "scripts/quality/hint_zones.py (CFF)", cff_keys))
    for name, tool, keys in lists:
        path = style_data(name, args.ufo)
        listed = read_list(path.name)
        found = keys()
        what = {"emboldened-whole.txt": "glyph: why", "styles-agree.txt": "kind glyph [detail]",
                "hint-zones.txt": "interpreter glyph:zone sizes",
                "hint-zones-cff.txt": "cff glyph:zone sizes"}.get(
            name, "glyph kind count")
        lines = [f"# Known {tool} findings ({what}); fixing one = deleting its line.\n"]
        for k in sorted(found):
            why = listed.get(k) or (f"{args.reason}: {found[k]}" if found[k] else args.reason)[:200]
            lines.append(f"{k:32} # {why}\n")
        outputs[path] = "".join(lines)
        print(f"{path.name}: {len(found)} findings, {len(set(found) - set(listed))} new, "
              f"{len(set(listed) - set(found))} gone")
    shaping = (args.golden, args.digest, args.cmap, args.exceptions, args.lookups, args.greek, args.cyrillic,
               args.latin)
    if lists and not any(shaping):
        publish()
        return
    if not any(shaping):
        ap.error("say what to update")

    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        builds = Builds(args.ufo, Path(tmp))
        ufo, otf = builds.font, builds.otf
        checked_digest = None
        tt, shaper = TTFont(otf), Shaper(otf)
        if args.golden or args.digest:
            checked_digest = check_changes(args.ufo, otf, Path(tmp), args.expect_changes,
                                           args.accept_report, args.report)

        if args.golden:
            golden = shape_golden(shaper)
            path = style_data("shaping-golden.json", args.ufo)
            outputs[path] = json.dumps(golden, ensure_ascii=False, indent=0) + "\n"
            print(f"{path.name}: {len(golden)} cases")
        if args.digest:
            digest, n = checked_digest or full_digest(shaper, tt.getBestCmap())
            path = style_data("shaping-digest.txt", args.ufo)
            outputs[path] = f"{digest} {n}\n"
            print(f"{path.name}: {n} strings")
        pair_lists = []
        if args.greek:
            from test_greek_pairs import greek_findings

            pair_lists.append(("greek", "greek-pairs.txt", greek_findings,
                               "Greek pairs where Charis and Libertinus agree against Myia"))
        if args.cyrillic:
            from test_cyrillic_pairs import cyrillic_findings

            pair_lists.append(("cyrillic", "cyrillic-pairs.txt", cyrillic_findings,
                               "Cyrillic pairs outside the references' whole range"))
        if args.latin:
            from test_latin_pairs import latin_findings

            pair_lists.append(("latin", "latin-pairs.txt", latin_findings,
                               "The italics' Latin pairs outside the reference italics' range"))
        for flag, name, findings, what in pair_lists:
            path = style_data(name, args.ufo)
            listed = read_list(path.name)
            found = findings(args.ufo, otf)
            if found is None:
                sys.exit(f"--{flag}: references or UDHR texts missing (build/refs/, make udhr)")
            lines = [f"# {what} (pair  # off N: why), N in n n gaps; fixing one = deleting its line.\n"]
            for p, off in sorted(found.items()):
                why = listed.get(p, "").split(": ", 1)[-1] if p in listed else args.reason
                lines.append(f"{p:8} # off {off:+.3f}: {why}\n")
            outputs[path] = "".join(lines)
            print(f"{path.name}: {len(found)} pairs, {len(set(found) - set(listed))} new, "
                  f"{len(set(listed) - set(found))} gone")
        if args.lookups:
            from test_lookups import lookup_summary

            path = style_data("lookups.txt", args.ufo)
            found = lookup_summary(tt)
            old = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
            outputs[path] = "\n".join(found) + "\n"
            print(f"{path.name}: {len(found)} lookups, {len(set(found) - set(old))} new lines, "
                  f"{len(set(old) - set(found))} gone")
        if args.cmap:
            path = DATA / "cmap.txt"
            old = {int(x, 16) for x in path.read_text().split()} if path.exists() else set()
            new = old | set(tt.getBestCmap())
            outputs[path] = "\n".join(f"{u:04X}" for u in sorted(new)) + "\n"
            print(f"cmap.txt: {len(new) - len(old)} code points added, {len(new)} total")
        if args.exceptions:
            nfd = nfd_mismatches(tt, shaper, Shaper(builds.decomposed))
            append_exceptions(
                outputs, "nfd-exceptions.txt", sorted(nfd.items()), args.reason,
                "# Precomposed characters allowed to render differently from their\n"
                "# decomposition (base + positioned marks). Remove a line once fixed.\n")
            sc = smallcap_mismatches(tt, shaper, Shaper(builds.decomposed))
            append_exceptions(
                outputs, "smallcap-nfd-exceptions.txt", sorted(sc.items()), args.reason,
                "# Small caps (smcp/c2sc) allowed to differ between precomposed and\n"
                "# decomposed input. Remove a line once fixed.\n")
            comp = composite_mismatches(ufo)
            append_exceptions(
                outputs, "composite-exceptions.txt", sorted(comp.items()), args.reason,
                "# Composites allowed to differ from scripts/composites.py's rules.\n")
            fb = fontbakery_failures(builds.release, Path(tmp))
            append_exceptions(
                outputs, "fontbakery-allow.txt",
                sorted((k, " ".join(" / ".join(str(m) for m in v).split())[:160])
                       for k, v in fb.items()),
                args.reason, "# fontbakery check-universal failures accepted for now.\n")

    publish()


if __name__ == "__main__":
    main()
