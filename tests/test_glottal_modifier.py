"""Rounded modifier curves use the final Bold base and retain its spacing."""

from copy import deepcopy

import ufoLib2
from conftest import DATA, ROOT
from fontTools.ufoLib.glifLib import readGlyphFromString
from glottal_modifier import finish
from glyph_lint import lint
from quality.checks import construction


def test_modifier_rebuild_cleans_curves_and_preserves_metadata():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Bold.ufo')
    glyph = font['uni02C0']
    glyph.clearContours()
    readGlyphFromString((DATA / 'glottal-modifier-before.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    before = deepcopy(glyph)
    order, keys, lib = list(font.glyphOrder), set(font.keys()), deepcopy(font.lib)
    assert any(kind == 'extreme' for kind, *_ in construction(glyph))
    finish(font)
    assert not construction(glyph)
    assert glyph.getBounds(font) == before.getBounds(font)
    assert glyph.width == before.width == 449
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    assert set(font.keys()) == keys
    assert font.glyphOrder == order
    assert font.lib == lib
    assert [kind for kind, *_ in lint(font, ['uni02C0'])['uni02C0']] == ['notch']
    after = deepcopy(glyph)
    finish(font)
    assert glyph == after
    # A change to the final base really reaches the rebuilt modifier.
    control = next(p for c in font['uni0242'].contours for p in c.points if p.type is None)
    control.x += 20
    finish(font)
    assert glyph.contours != after.contours


def test_modifier_other_styles_unchanged():
    for style in ('Regular', 'Italic', 'BoldItalic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni02C0'])
        finish(font)
        assert font['uni02C0'] == before
