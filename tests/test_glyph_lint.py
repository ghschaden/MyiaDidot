"""Outlines gone wrong: no specks, pinholes, slivers, notches or steps beyond
the known ones.

scripts/glyph_lint.py finds them; each style has its list of known findings,
data/glyph-lint.txt (the Regular's), glyph-lint-Italic.txt, glyph-lint-Bold.txt:
one "glyph kind count" per line with a reason. A new finding fails, and so
does a listed one that is gone (delete its line), so the lists only shrink.
After an intended change: scripts/update_test_data.py --lint.
"""

from conftest import style_data
from glyph_lint import lint
from test_composites import read_list


def lint_keys(ufo):
    """{"glyph kind count": the findings, as text} for a font."""
    keys = {}
    for name, items in lint(ufo).items():
        kinds = {}
        for kind, where, detail in items:
            kinds.setdefault(kind, []).append(f"{where} {detail}")
        for kind, found in kinds.items():
            keys[f"{name} {kind} {len(found)}"] = "; ".join(found)
    return keys


def test_glyph_lint(ufo, ufo_path):
    listed = read_list(style_data("glyph-lint.txt", ufo_path).name)
    found = lint_keys(ufo)
    new = {k: v for k, v in found.items() if k not in listed}
    stale = sorted(set(listed) - set(found))
    assert not new, ("outlines gone wrong (python scripts/glyph_lint.py UFO GLYPH; if intended: "
                     f"update_test_data.py --lint): {new}")
    assert not stale, f"glyph-lint findings fixed, remove from the list: {stale}"
