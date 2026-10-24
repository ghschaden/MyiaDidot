"""The weighted aleph's two repaired joins preserve the surrounding drawing."""

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


def test_aleph_other_styles_are_unchanged():
    for style in ('Regular', 'Bold', 'Italic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni2135'])
        finish(font)
        assert font['uni2135'] == before
