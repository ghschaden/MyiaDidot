"""Approved curl connections are local, clean and repeatable."""

from copy import deepcopy

import ufoLib2
from conftest import DATA, ROOT
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint_glyph
from quality.checks import construction
from w_curl import finish


def test_curl_connection_preserves_body_and_metadata():
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    glyph = font['uni2C72']
    approved = deepcopy(glyph)
    glyph.clearContours()
    readGlyphFromString((DATA / 'w-curl-before.glif').read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    glyph.lib.update(approved.lib)  # the fixture is the outline before; the lib is the glyph's own
    before = deepcopy(glyph)
    finish(font)
    assert glyph == approved
    # Global tangent finishing may shift a handle by one unit; body nodes stay.
    for a, b in zip(glyph.contours[1].points, before.contours[1].points, strict=True):
        assert a.type == b.type
        if a.type:
            assert (a.x, a.y) == (b.x, b.y)
        else:
            assert max(abs(a.x-b.x), abs(a.y-b.y)) <= 1
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.unicodes == before.unicodes
    assert glyph.lib == before.lib
    assert glyph.getBounds(font) == before.getBounds(font)
    assert not construction(glyph)
    assert not lint_glyph(font, glyph)
    finish(font)
    assert glyph == approved


def test_curl_other_styles_unchanged():
    for style in ('Regular', 'Italic', 'Bold'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['uni2C72'])
        finish(font)
        assert font['uni2C72'] == before
