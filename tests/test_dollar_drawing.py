"""A lighter dollar waist with straight bars and continuous terminal necks."""

from copy import deepcopy
from math import hypot

import ufoLib2
from conftest import DATA, ROOT
from dollar_drawing import finish
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint
from test_dollar_bars import edge_groups


def test_dollar_waist_and_terminals_preserve_bar_geometry_and_spacing():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    glyph = font['dollar']
    glyph.clearContours()
    readGlyphFromString((DATA / 'dollar-drawing-before.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    before = deepcopy(glyph)
    edge_groups(before)
    finish(font)
    edge_groups(glyph)
    # Opposite edges of the waist lie on two common parallel diagonals.
    lower = glyph.contours[3].points[7:9]
    upper = glyph.contours[4].points[:2]
    low = sum(p.y + .6*p.x for p in lower)/2
    high = sum(p.y + .6*p.x for p in upper)/2
    assert abs(low-1015) < 1
    assert abs(high-1217) < 1
    assert 170 < (high-low)/hypot(1,.6) < 175
    assert len(glyph.contours[0].points) == 76
    assert (glyph.contours[0].points[3].x, glyph.contours[0].points[3].y) == (250,470)
    assert len(glyph.contours) == len(before.contours) == 5
    assert glyph.width == before.width == 1290
    assert glyph.anchors == before.anchors
    assert glyph.unicodes == before.unicodes
    assert glyph.lib == before.lib
    assert not lint(font, ['dollar'])
    after = deepcopy(glyph)
    finish(font)
    assert glyph == after


def test_dollar_drawing_other_styles_unchanged():
    for style in ('Regular','Bold','Italic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['dollar'])
        finish(font)
        assert font['dollar'] == before
