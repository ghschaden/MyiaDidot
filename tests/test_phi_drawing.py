"""Accepted phi counters reproduce cleanly without disturbing spacing."""

from copy import deepcopy

import ufoLib2
from conftest import ROOT
from glyph_lint import lint_glyph
from phi_drawing import finish
from quality.checks import construction


def test_phi_rebuild_and_metadata():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    before = deepcopy(font)
    # The final pass rebuilds from o/l, not from the previous phi outline.
    font['uni0278'].clearContours()
    finish(font)
    glyph = font['uni0278']
    assert glyph == before['uni0278']
    assert not construction(glyph)
    assert not lint_glyph(font, glyph)
    assert font.lib == before.lib
    assert set(font.keys()) == set(before.keys())
    for name in font.keys() - {'uni0278'}:
        assert font[name] == before[name]
    finish(font)
    assert glyph == before['uni0278']
    # Stem weight really follows the final l, rather than a frozen drawing.
    for contour in font['l'].contours:
        for point in contour.points:
            point.x *= 1.05
    finish(font)
    assert glyph.contours != before['uni0278'].contours
    assert glyph.width == before['uni0278'].width
    assert glyph.anchors == before['uni0278'].anchors
    assert glyph.lib == before['uni0278'].lib
    assert glyph.unicodes == before['uni0278'].unicodes


def test_phi_other_styles_unchanged():
    for style in ('Regular', 'Italic', 'Bold'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni0278'])
        finish(font)
        assert font['uni0278'] == before
