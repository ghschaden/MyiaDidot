"""The italic y dot stays beside the descender in both generated weights."""

from copy import deepcopy

import pathops
import pytest
import ufoLib2
from conftest import ROOT
from glyph_lint import ink, lint
from y_dot import y_dot_anchor


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_y_dot_clearance(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    glyph = font["uni1EF5"]
    dot = next(c for c in glyph.components if c.baseGlyph == "dotaccent")
    placed = ink(font, font["dotaccent"]).transform(*dot.transformation)
    base = ink(font, font["y"])
    assert pathops.op(base, placed, pathops.PathOp.INTERSECTION).area == 0
    lo, hi = placed.bounds[1], placed.bounds[3]
    band = pathops.Path()
    pen = band.getPen()
    pen.moveTo((-2000, lo))
    pen.lineTo((3000, lo))
    pen.lineTo((3000, hi))
    pen.lineTo((-2000, hi))
    pen.closePath()
    clipped = pathops.op(base, band, pathops.PathOp.INTERSECTION)
    assert 24 <= placed.bounds[0] - clipped.bounds[2] <= 26
    assert not lint(font, [glyph.name])
    # Same geometry and clearance rule on each final, weighted master.
    anchor = next(a for a in font["y"].anchors if a.name == "DotBelow")
    before = deepcopy(font["y"])
    anchor.x -= 100
    y_dot_anchor(font)
    assert abs(anchor.x - next(a.x for a in before.anchors if a.name == "DotBelow")) <= 1
    assert anchor.y == next(a.y for a in before.anchors if a.name == "DotBelow")
    assert font["y"].contours == before.contours
    assert font["y"].width == before.width
    settled = deepcopy(font["y"])
    y_dot_anchor(font)
    assert font["y"] == settled
