"""Ⱦ retains its upper counter while its residual foot counter is closed."""

from copy import deepcopy

import pathops
import ufoLib2
from conftest import ROOT
from glyph_lint import ink, lint
from t_slash import finish


def test_t_slash_counter_repair():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = font["uni023E"]
    expected = deepcopy(glyph)
    # Reintroduce the actual residual counter from the uncorrected master.
    pen = glyph.getPen()
    pen.moveTo((427, 75))
    pen.lineTo((464, 135))
    pen.lineTo((459, 117))
    pen.curveTo((454, 96), (443, 83), (427, 75))
    pen.closePath()
    assert lint(font, [glyph.name])
    before = ink(font, glyph)
    finish(font)
    after = ink(font, glyph)
    assert pathops.op(after, before, pathops.PathOp.DIFFERENCE).area == 402
    assert pathops.op(before, after, pathops.PathOp.DIFFERENCE).area == 0
    assert glyph == expected  # All other contours, metadata and anchors survive.
    assert len(glyph.contours) == 2  # Outer outline and upper opening.
    assert not lint(font, [glyph.name])
    finish(font)
    assert glyph == expected


def test_t_slash_other_styles_unchanged():
    for style in ("Regular", "Bold", "Italic"):
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        before = deepcopy(font["uni023E"])
        finish(font)
        assert font["uni023E"] == before
