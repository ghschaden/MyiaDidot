"""Approved figure drawings, tabular inheritance and isolated regeneration."""

from copy import deepcopy

import pytest
import ufoLib2
from conftest import ROOT
from glyph_lint import lint_glyph
from oldstyle_figures import FIGURES, finish
from quality.checks import construction


@pytest.mark.parametrize("style", ("Regular", "Italic"))
def test_approved_figures_rebuild_and_tabular_forms_follow(style):
    font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
    names = [d + 'oldstyle' for d in FIGURES] + ['zerooldstyle.zero']
    affected = set(names + [n + '.tf' for n in names])
    before = deepcopy(font)
    for name in names:
        font[name].clearContours()
    finish(font)
    for name in affected:
        assert font[name] == before[name]
    for name in names:
        glyph = font[name]
        assert not construction(glyph)
        assert not lint_glyph(font, glyph)
        tab = font[name + '.tf']
        assert tab.width == font['zero'].width
        assert tab.components[0].baseGlyph == name
        assert tab.components[0].transformation[4] == round((tab.width-glyph.width)/2)
        assert glyph.anchors == before[name].anchors
        assert glyph.lib == before[name].lib
    assert all(font[n] == before[n] for n in font.keys() - affected)
    assert font.lib == before.lib
    finish(font)
    assert all(font[n] == before[n] for n in affected)
    # The descending 3/4/5 and curled 9 share the reviewed text band.
    for digit in ('three', 'four', 'five', 'nine'):
        bounds = font[digit+'oldstyle'].getBounds(font)
        assert abs(bounds[3]-905) <= 1
        assert abs(bounds[1]+380) <= 1


def test_other_styles_do_not_load_italic_drawings():
    for style in ('Bold', 'BoldItalic'):
        font = ufoLib2.Font.open(ROOT / f'sources/MyiaDidot-{style}.ufo')
        before = deepcopy(font['nineoldstyle'])
        finish(font)
        assert font['nineoldstyle'] == before


def test_bold_reduced_figures_keep_weight_and_room():
    from quality.strokes import strokes

    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Bold.ufo')
    names = [d+'oldstyle' for d in FIGURES] + ['zerooldstyle.zero']
    before = {name: deepcopy(font[name]) for name in names}
    finish(font)
    assert all(font[name] == before[name] for name in names)
    _, measured = strokes(font, only=('threeoldstyle', 'fiveoldstyle'))
    assert all(.80 <= ratio <= 1.10 for _, ratio, *_ in measured.values())
    glyph = font['fouroldstyle']
    left, _, right, _ = glyph.getBounds(font)
    assert left > 0 and glyph.width-right > 0
    assert glyph.width == 820
    assert all(not construction(font[name]) for name in names)
