"""Italic belts must connect to their stems without changing the base letters."""

from copy import deepcopy

import pytest
import ufoLib2
from conftest import DATA, ROOT, respaced
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint
from l_belt import finish


@pytest.mark.parametrize('name', ['uni026C', 'uniA7AD'])
def test_belts_join_and_preserve_surroundings(name):
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Italic.ufo')
    expected = deepcopy(font[name])
    glyph = font[name]
    glyph.clearContours()
    readGlyphFromString((DATA / f'l-belt-before-{name}.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    glyph.lib.update(expected.lib)  # the fixture is the outline before; the lib is the glyph's own
    before = deepcopy(glyph)
    bases = {n: deepcopy(font[n]) for n in ['l', 'L']}
    assert len(glyph.contours) == 3  # Three floating pieces, not a closed belt.
    if name == 'uni026C':
        assert len(lint(font, [name])[name]) == 3
    finish(font)
    assert glyph == expected
    assert len(glyph.contours) == 2  # Joined outside outline and enclosed counter.
    assert not lint(font, [name])
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    for n, base in bases.items():
        assert font[n] == base
    # Stem tips and foot curves outside the attachment band keep their points.
    lo, hi = (590, 928) if name == 'uni026C' else (542, 917)
    def outside(g):
        return sorted((p.x, p.y, p.type or '') for c in g.contours for p in c.points
                      if p.y < lo or p.y > hi)
    assert outside(glyph) == outside(before)
    finish(font)
    assert glyph == expected


def test_other_styles_keep_their_belt_outlines():
    for style in ['Regular', 'Bold', 'BoldItalic']:
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = {n: deepcopy(font[n]) for n in ['uni026C', 'uniA7AD']}
        finish(font)
        assert all(font[n] == g for n, g in before.items())


@pytest.mark.parametrize('name,base', [('uni026C', 'l'), ('uniA7AD', 'L')])
def test_bold_belts_keep_spacing_and_follow_final_base(name, base):
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    glyph = font[name]
    before = deepcopy(glyph)
    before.clearContours()
    readGlyphFromString((DATA / f'l-belt-before-BoldItalic-{name}.glif').read_text(),
                       glyphObject=before, pointPen=before.getPointPen())
    respaced(before)  # (recorded at the Bold's cut)
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.getBounds(font).yMax == font[base].getBounds(font).yMax
    assert not lint(font, [name])
