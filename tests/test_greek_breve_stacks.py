"""The grave stays separate from the breve after weighting legacy stacks."""

from copy import deepcopy

import pytest
import ufoLib2
from composites import STACK_GAP_LC
from conftest import ROOT
from fontTools.pens.boundsPen import BoundsPen
from glyph_lint import lint
from make_bold import separate_breve_grave_stacks


@pytest.mark.parametrize("style", ["Bold", "BoldItalic"])
def test_breve_grave_clearance(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    names = [f"brevecmb_uni{b}_gravecomb.grek" for b in ("0313", "0314")]
    original = {name: deepcopy(font[name]) for name in names}
    for name in names:
        upper, breve = font[name].components
        upper.transformation = upper.transformation._replace(dy=320)
    separate_breve_grave_stacks(font)
    for name in names:
        assert font[name] == original[name]
        upper, breve = font[name].components
        a, b = BoundsPen(font), BoundsPen(font)
        font[upper.baseGlyph].draw(a)
        font[breve.baseGlyph].draw(b)
        gap = a.bounds[1] + upper.transformation.dy - (b.bounds[3] + breve.transformation.dy)
        assert STACK_GAP_LC <= gap < STACK_GAP_LC + 1
    assert not lint(font, names)
    separate_breve_grave_stacks(font)
    assert all(font[name] == original[name] for name in names)
