"""The sign drawings survive regeneration without altering other glyphs."""

import sys

import pytest
import ufoLib2
from conftest import ROOT
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(ROOT / "scripts"))
from cyrillic_signs import NAMES, redraw


def snapshot(glyph):
    pen = RecordingPen()
    glyph.draw(pen)
    return pen.value, glyph.width, [(a.name, a.x, a.y) for a in glyph.anchors]


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_sign_drawings_regenerate(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    before = {g.name: snapshot(g) for g in font}
    # Corrupt each drawing so a no-op redraw cannot satisfy the check.
    for name in NAMES:
        font[name].clearContours()
        font[name].width += 20
        for anchor in font[name].anchors:
            anchor.x += 10
    redraw(font)
    assert {g.name: snapshot(g) for g in font} == before
    redraw(font)
    assert {g.name: snapshot(g) for g in font} == before
    # ы shares the complete soft sign, not an independently weighted copy.
    assert font["uni044B"].contours[:2] == font["uni044C"].contours
