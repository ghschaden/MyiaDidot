"""Requested filled roman joins, baseline tips and parallel trademark stems."""

from copy import deepcopy
from math import atan, degrees

import ufoLib2
from conftest import DATA, ROOT
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint
from symbol_joins import regular, trademark


def restore(font, style, names):
    for name in names:
        glyph = font[name]
        glyph.clearContours()
        readGlyphFromString((DATA / 'symbol-joins' / f'{style}-{name}.glif').read_text(),
                           glyphObject=glyph, pointPen=glyph.getPointPen())


def test_roman_slits_close_without_moving_stems_spacing_or_anchors():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Regular.ufo')
    names = ('M', 'uni043C', 'trademark', 'uni2116')
    restore(font, 'Regular', names)
    before = {n: deepcopy(font[n]) for n in names}
    assert all(lint(font, names).values())
    regular(font)
    assert not lint(font, names)
    for name in names:
        glyph, old = font[name], before[name]
        assert glyph.width == old.width
        assert glyph.anchors == old.anchors
        assert glyph.unicodes == old.unicodes
        # The direct diagonal/upright intersection replaces five old
        # points with one. All other endpoints stay, apart from baseline tips.
        assert len(glyph.contours[0].points) == len(old.contours[0].points) - 4
    assert font['M'].getBounds(font).yMin == 0
    assert font['uni043C'].getBounds(font).yMin == 0
    assert font['trademark'].getBounds(font).yMin == 612
    after = {n: deepcopy(font[n]) for n in names}
    regular(font)
    assert all(font[n] == after[n] for n in names)


def test_trademark_outer_stems_parallel_and_middle_unchanged():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    restore(font, 'BoldItalic', ('trademark',))
    before = deepcopy(font['trademark'])
    trademark(font)
    glyph = font['trademark']
    m = glyph.contours[0].points
    angles = [degrees(atan((m[a].x-m[b].x)/(m[a].y-m[b].y)))
              for a, b in ((6, 5), (36, 37), (20, 21), (33, 32))]
    assert max(angles) - min(angles) < .25
    assert all(abs(angle-15.2) < .2 for angle in angles)
    assert m[12:15] == before.contours[0].points[12:15]
    assert m[34:37] == before.contours[0].points[34:37]
    t = glyph.contours[1].points
    assert t[10].x > t[11].x > t[12].x > t[13].x
    assert t[28].x <= t[26].x + 10
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert not lint(font, ['trademark'])
    after = deepcopy(glyph)
    trademark(font)
    assert glyph == after
