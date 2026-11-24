"""The Bold's ˀ made again from its final base, ʔ (from ɂ until 2026-11-24,
fitted then into the accepted drawing's box), clean, and spaced as ˁ
mirrored."""

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
    assert not lint(font, ['uni02C0']).get('uni02C0')
    # spaced and sized as ˁ, its mirror
    twin = font['uni02C1']
    box, twin_box = glyph.getBounds(font), twin.getBounds(font)
    assert glyph.width == twin.width
    assert box.xMin == twin.width - twin_box.xMax
    assert (box.yMin, box.yMax) == (twin_box.yMin, twin_box.yMax)
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    assert set(font.keys()) == keys
    assert font.glyphOrder == order
    assert font.lib == lib
    after = deepcopy(glyph)
    finish(font)
    assert glyph == after
    # A change to the final base really reaches the rebuilt modifier.
    control = next(p for c in font['uni0294'].contours for p in c.points if p.type is None)
    control.x += 20
    finish(font)
    assert glyph.contours != after.contours


def test_modifier_other_styles_unchanged():
    for style in ('Regular', 'Italic', 'BoldItalic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni02C0'])
        finish(font)
        assert font['uni02C0'] == before
