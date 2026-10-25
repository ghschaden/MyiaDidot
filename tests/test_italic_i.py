"""The accepted lighter I is installed once and retains its fit."""
from copy import deepcopy

import ufoLib2
from conftest import ROOT
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ufoLib.glifLib import readGlyphFromString
from italic_i import DATA, install
from ufoLib2.objects import Glyph


def outline(glyph):
    pen = RecordingPen()
    glyph.draw(pen)
    return pen.value


def test_production_i_matches_approved_trial():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    approved = Glyph()
    readGlyphFromString(DATA.read_text(), glyphObject=approved, pointPen=approved.getPointPen())
    assert outline(font["I"]) == outline(approved)
    assert font["I"].width == approved.width
    assert font["I"].anchors == approved.anchors


def test_install_preserves_fit_and_is_idempotent():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    old = deepcopy(font["I"])
    other = deepcopy(font["r"])
    install(font)
    assert (font["I"].width, font["I"].anchors, font["I"].lib, font["I"].unicodes) == (
        old.width, old.anchors, old.lib, old.unicodes)
    settled = deepcopy(font["I"])
    install(font)
    assert font["I"] == settled
    assert font["r"] == other
