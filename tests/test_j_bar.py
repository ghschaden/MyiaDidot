"""Bold Italic ɉ's bar projects clearly beyond its heavier stem."""

from copy import deepcopy

import pathops
import ufoLib2
from conftest import ROOT
from glyph_lint import ink, lint
from j_bar import finish


def arms(glyph):
    """(left, right): how far the bar's terminals stand past the stem's
    corners, at the bar's bottom and top."""
    pts = [(p.x, p.y) for p in glyph.contours[0].points if p.type == "line" and 390 < p.y < 490]
    out = []
    for y in sorted({y for _, y in pts}):
        xs = sorted(x for x, yy in pts if yy == y)
        out.append((xs[1] - xs[0], xs[-1] - xs[-2]))
    return out


def test_j_bar_extension():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = font["uni0249"]
    expected = deepcopy(glyph)
    thickness = 474 - 410
    # both arms 1.25 of the bar's thickness past the stem, at its top and bottom
    assert arms(glyph) == [(round(1.25 * thickness),) * 2] * 2
    # cut back to the stem's corners and lengthened again: only the four
    # terminal corners move, the ink only grows
    points = glyph.contours[0].points
    for y in (410, 474):
        row = sorted((p for p in points if p.type == "line" and p.y == y), key=lambda p: p.x)
        row[0].x, row[-1].x = row[1].x - 10, row[-2].x + 10
    before = ink(font, glyph)
    finish(font)
    assert glyph == expected
    after = ink(font, glyph)
    assert pathops.op(before, after, pathops.PathOp.DIFFERENCE).area == 0
    assert pathops.op(after, before, pathops.PathOp.DIFFERENCE).area > 5000
    assert not lint(font, [glyph.name])
    finish(font)
    assert glyph == expected


def test_j_bar_other_styles_unchanged():
    for style in ("Regular", "Bold", "Italic"):
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        before = deepcopy(font["uni0249"])
        finish(font)
        assert font["uni0249"] == before
