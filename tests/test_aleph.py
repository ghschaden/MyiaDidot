"""Weighted aleph repairs preserve the surrounding drawing and source joins."""

from copy import deepcopy

import ufoLib2
from aleph import _lower_return, finish
from conftest import DATA, ROOT
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint


def test_aleph_return_repair_is_local_and_repeatable():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    final = deepcopy(font['uni2135'])
    glyph = font['uni2135']
    expected = deepcopy(glyph)
    expected.clearContours()
    readGlyphFromString((DATA / 'aleph-upper-before.glif').read_text(),
                       glyphObject=expected, pointPen=expected.getPointPen())
    glyph.clearContours()
    readGlyphFromString((DATA / 'aleph-before.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    before = deepcopy(glyph)
    assert lint(font, ['uni2135'])['uni2135'][0][0] == 'ledge'
    _lower_return(glyph)
    assert glyph == expected
    assert not lint(font, ['uni2135'])
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    old = before.contours[0].points
    new = glyph.contours[0].points
    start = next(i for i, p in enumerate(old) if (p.x, p.y, p.type) == (719, -6, 'curve'))
    end = next(i for i, p in enumerate(old) if (p.x, p.y, p.type) == (740, 59, 'curve'))
    assert new[:start + 2] == old[:start + 2]
    assert new[start + 4:] == old[end + 1:]
    assert [(p.x, p.y, p.type) for p in new[start:start + 4]] == [
        (719, -6, 'curve'), (721, 3, None), (729, 22, None), (740, 59, 'curve'),
    ]
    # The entire replacement rises monotonically, and its upper join has
    # identical incoming/outgoing tangents rather than another return.
    assert all(a.y < b.y for a, b in zip(new[start:start + 3], new[start + 1:start + 4]))
    c, p, d = new[start + 2:start + 5]
    assert (p.x - c.x, p.y - c.y) == (d.x - p.x, d.y - p.y) == (11, 37)
    assert p.smooth
    _lower_return(glyph)
    assert glyph == expected
    finish(font)
    assert glyph == final


def test_aleph_upper_join_preserves_accepted_drawing():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    expected = deepcopy(font['uni2135'])
    glyph = font['uni2135']
    glyph.clearContours()
    readGlyphFromString((DATA / 'aleph-upper-before.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    before = deepcopy(glyph)
    finish(font)
    assert glyph == expected
    assert not lint(font, ['uni2135'])
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    old = before.contours[0].points
    new = glyph.contours[0].points
    start = next(i for i, p in enumerate(old) if (p.x, p.y, p.type) == (978, 588, 'curve'))
    end = next(i for i, p in enumerate(old) if (p.x, p.y, p.type) == (850, 478, 'curve'))
    assert new[:start + 1] == old[:start + 1]
    assert new[start + 6:] == old[end:]
    assert [(p.x, p.y, p.type) for p in new[start:start + 7]] == [
        (978, 588, 'curve'), (951, 588, None), (941, 606, None), (929, 606, 'curve'),
        (830, 606, None), (864, 514, None), (850, 478, 'curve'),
    ]
    assert all(p.y == 588 for p in new[start - 1:start + 2])
    assert all(p.y == 606 for p in new[start + 2:start + 5])
    # The neck's controls cross in x, but its derivative stays negative:
    # the edge never turns back to the right as the weighted drawing did.
    p0, p1, p2, p3 = new[start + 3:start + 7]
    for t in (i / 200 for i in range(201)):
        dx = 3 * ((p1.x - p0.x) * (1 - t) ** 2
                  + 2 * (p2.x - p1.x) * (1 - t) * t + (p3.x - p2.x) * t ** 2)
        assert dx < 0
    finish(font)
    assert glyph == expected


def test_upright_aleph_height_spacing_and_smallcap_features():
    from smallcaps import smcp_map
    from upright_aleph import drawing, install

    for style in ('Regular', 'Bold', 'Italic', 'BoldItalic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni2135'])
        install(font)
        glyph = font['uni2135']
        assert glyph.width == before.width
        assert glyph.anchors == before.anchors
        assert glyph.unicodes == before.unicodes
        if 'Italic' in style:
            assert glyph == before
        else:
            bounds = glyph.getBounds(None)
            assert abs(bounds[1]) < 1
            assert abs(bounds[3] - 1434) < 1
            expected = drawing(bold=style == 'Bold', tall=True, width=glyph.width)
            assert glyph.contours == expected.contours
        small = font['uni2135.sc']
        assert small.unicodes == []
        assert small.width == glyph.width
        assert small.getBounds(font)[3] < 1125
        smcp, c2sc, _, _ = smcp_map(font)
        assert smcp['uni2135'] == c2sc['uni2135'] == 'uni2135.sc'
        first = deepcopy(glyph), deepcopy(small)
        install(font)
        assert (font['uni2135'], font['uni2135.sc']) == first


def test_aleph_smallcap_substitution(shaper):
    assert shaper.shape('ℵ')[0][0] == 'uni2135'
    for features in ({'smcp': True}, {'c2sc': True}, {'smcp': True, 'c2sc': True}):
        assert shaper.shape('ℵ', features)[0][0] == 'uni2135.sc'
