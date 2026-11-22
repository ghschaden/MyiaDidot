"""Italic belts must connect to their stems without changing the base letters."""

from copy import deepcopy

import pytest
import ufoLib2
from conftest import DATA, ROOT, respaced
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint
from l_belt import finish


def test_belted_l_comes_joined_from_the_heavier_stem():
    """ɬ's ring and bar meet l's stem without the belt's bridges since phase 6
    step C (2026-11-19, the stem weighted to n's): the generator's own
    outline is one outside and one counter, lint clean, and finish leaves it
    as it is (the bridging itself is tested on Ɬ below, whose pieces still
    stand clear of its stem; the fixture before-uni026C, ɬ's three pieces
    at the old stem, is no longer used: tests/data/l-belt-before-uni026C.glif)."""
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Italic.ufo')
    glyph = font['uni026C']
    before = deepcopy(glyph)
    assert len(glyph.contours) == 2
    assert not lint(font, ['uni026C'])
    finish(font)
    assert glyph == before


@pytest.mark.parametrize('name', ['uniA7AD'])
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
    # ɬ a unit narrower: l's stem weighted to n's (phase 6 step C, 2026-11-19);
    # ɬ Ɬ a unit narrower again: the Italic's ring has its extremes split at
    # the shear (out of POINT_REPAIRS, 2026-11-22; the shaping report reviewed)
    assert glyph.width == before.width + {'uni026C': -2, 'uniA7AD': -1}.get(name, 0)
    # (ɬ's anchors up to 20 across from the fixture's: l's stem weighted, step C;
    # Ɬ's one unit, with its width, 2026-11-22)
    slack = 20 if name == 'uni026C' else 1
    assert [(a.name, a.y) for a in glyph.anchors] == [(a.name, a.y) for a in before.anchors]
    assert all(abs(a.x - b.x) <= slack for a, b in zip(glyph.anchors, before.anchors))
    assert glyph.getBounds(font).yMax == font[base].getBounds(font).yMax
    assert not lint(font, [name])
