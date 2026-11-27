"""The families of recipes that read their bases (scripts/recipe_bands.py),
each against its rule (TODO.md, "Recipes that read their bases").

Tail: the stem runs straight on from above the cut into the curl. Its
edges, in the upright frame, stay within TOL of where they stand at the
line's top, down to -40 (above every curl's start). When a band copied
numbers that had gone stale, the build pulled the stem onto the stale
line: the Bold Italic's Ʈ Ɽ ʈ.sc leaned 8-10 units, ɽ.sc's left edge 40-60
(2026-11-27); measured, all are within 2.
"""

import math
from pathlib import Path

import derive
import pytest
import ufoLib2
from italic_geometry import shear
from recipe_bands import Tail

ROOT = Path(__file__).resolve().parent.parent
TOL = 3
STEP = 20
MERGED = 0.15  # a row this much wider than at the top: the stem met a bowl or serif there
# stems with one edge free, the other meeting a bowl through its crotch
ONE_EDGE = {"ɖ": "right"}  # (d's bowl runs into the stem's left edge from 300 down to 0)
# stems that are not straight in their base either, with why
NOT_STRAIGHT = {"ɳ": "n's leg tapers in the italics, and the faired tail goes on with it (1006 -> 981 at the right "
                     "edge from 300 to -30, the same before and after the band read it, 2026-11-27)"}


def tails():
    from data_bold_italic import ITALIC_BOLD_RECIPES

    return {ch: band for ch, (_, _, band) in ITALIC_BOLD_RECIPES.items() if isinstance(band, Tail)}


@pytest.fixture(scope="module")
def bold_italic():
    return ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")


def lean(font, ch, band, bottom=-40):
    """(y, left, right): the row where the stem's edges stray furthest from
    where they stand at the line's top, in units"""
    cmap = {u: g.name for g in font for u in g.unicodes}
    name = derive.resolve(cmap, ch)
    up = ufoLib2.Font()
    up[name] = font[name].copy()
    shear(up[name], -math.tan(math.radians(-font.info.italicAngle)))
    worst, prev = (0, 0, 0), None
    for y in range(int(band.top), bottom - 1, -STEP):
        runs = derive.stems_at(up, name, y)
        if prev is None:  # the line's top: the run picked as the band picks it
            prev = runs[band.pick]
            x0, x1 = prev
        # followed down: the run that overlaps the one above
        prev = min(runs, key=lambda r: abs(r[0] + r[1] - prev[0] - prev[1]))
        if prev[1] - prev[0] > (1 + MERGED) * (x1 - x0):
            continue
        row = (y, 0 if ONE_EDGE.get(ch) == "right" else prev[0] - x0, prev[1] - x1)
        worst = max(worst, row, key=lambda r: max(abs(r[1]), abs(r[2])))
    return worst


@pytest.mark.parametrize("ch", sorted(set(tails()) - set(NOT_STRAIGHT)))
def test_tail_stem_runs_straight(bold_italic, ch):
    y, left, right = lean(bold_italic, ch, tails()[ch])
    assert max(abs(left), abs(right)) <= TOL, (
        f"{ch}: at y {y} the stem's edges {left:+.0f} / {right:+.0f} off where they stand at the line's top")
