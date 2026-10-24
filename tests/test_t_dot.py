"""The tall italic t clears its dot like z, in NFC and anchor construction."""

from copy import deepcopy

import pytest
import ufoLib2
from conftest import ROOT
from glyph_lint import lint
from make_italic import SLANT, t_dot_anchor


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_t_dot_clearance(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    gaps = []
    for name, base in (("uni1E6B", "t"), ("zdotaccent", "z")):
        glyph = font[name]
        dot = next(c for c in glyph.components if c.baseGlyph == "dotaccent")
        gaps.append(font["dotaccent"].getBounds(font).yMin + dot.transformation.dy
                    - font[base].getBounds(font).yMax)
    assert gaps[0] == gaps[1]
    assert gaps[0] > 0
    assert not lint(font, ["uni1E6B"])


def test_t_dot_anchor_repair():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    anchor = next(a for a in font["t"].anchors if a.name == "Dotaccent")
    expected = deepcopy(anchor)
    anchor.y -= 269
    anchor.x -= round(269 * SLANT)
    before = deepcopy(font)
    t_dot_anchor(font)
    assert anchor == expected
    for name in font.keys():
        if name != "t":
            assert font[name] == before[name]
    old = before["t"]
    assert font["t"].contours == old.contours
    assert font["t"].width == old.width
    for a, b in zip(font["t"].anchors, old.anchors):
        if a.name != "Dotaccent":
            assert a == b
    settled = deepcopy(font["t"])
    t_dot_anchor(font)
    assert font["t"] == settled
