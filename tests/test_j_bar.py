"""Bold Italic ɉ's bar projects clearly beyond its heavier stem."""

from copy import deepcopy

import pathops
import ufoLib2
from conftest import ROOT
from glyph_lint import ink, lint
from j_bar import finish


def test_j_bar_extension():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = font["uni0249"]
    expected = deepcopy(glyph)
    points = glyph.contours[0].points
    top = next(i for i, p in enumerate(points) if (p.x, p.y) == (572, 474))
    end_top, end_bottom = points[top + 1:top + 3]
    assert (end_top.x, end_top.y) == (652, 474)
    assert (end_bottom.x, end_bottom.y) == (632, 410)
    end_top.x, end_top.y = 553, 471
    end_bottom.x, end_bottom.y = 537, 413
    before = ink(font, glyph)
    finish(font)
    assert glyph == expected  # Only the two terminal corners change.
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
