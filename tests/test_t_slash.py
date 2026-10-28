"""Ⱦ retains its upper counter while its residual foot counter is closed."""

from copy import deepcopy

import pathops
import ufoLib2
from conftest import ROOT
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from glyph_lint import ink, lint
from t_slash import finish


def test_t_slash_counter_repair():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = font["uni023E"]
    expected = deepcopy(glyph)
    # A residual counter as the uncorrected master had, placed in the ink
    # by the foot (the stroked outline's ink, not fixed coordinates).
    path = ink(font, glyph)
    x = next(x for x in range(200, 800, 5)
             if all(path.contains((x + dx, 100 + dy)) for dx in (-5, 0, 40) for dy in (-30, 0, 40)))
    dx, dy = x - 445, 100 - 105
    area = AreaPen()
    glyph.draw(area)
    # drawn against the outline's winding (a hole)
    pen = glyph.getPen() if area.value > 0 else ReverseContourPen(glyph.getPen())
    pen.moveTo((427 + dx, 75 + dy))
    pen.lineTo((464 + dx, 135 + dy))
    pen.lineTo((459 + dx, 117 + dy))
    pen.curveTo((454 + dx, 96 + dy), (443 + dx, 83 + dy), (427 + dx, 75 + dy))
    pen.closePath()
    assert lint(font, [glyph.name])
    before = ink(font, glyph)
    finish(font)
    after = ink(font, glyph)
    assert pathops.op(after, before, pathops.PathOp.DIFFERENCE).area > 300
    assert pathops.op(before, after, pathops.PathOp.DIFFERENCE).area == 0
    assert glyph == expected  # All other contours, metadata and anchors survive.
    assert len(glyph.contours) == 2  # Outer outline and upper opening.
    assert not lint(font, [glyph.name])
    finish(font)
    assert glyph == expected


def test_t_slash_other_styles_unchanged():
    for style in ("Regular", "Bold", "Italic"):
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        before = deepcopy(font["uni023E"])
        finish(font)
        assert font["uni023E"] == before
