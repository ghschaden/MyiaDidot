"""Closed white regions and short terminals must not acquire stem roles."""
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.arches import upper_arches
from relationships.geometry import Outline
from relationships.returns import lower_returns


def bowl(reverse=False, shear=0):
    font = ufoLib2.Font()
    pen = font.newGlyph('bowl').getPen()
    pen = TransformPen(pen, (1, 0, shear, 1, 0, 0))
    if reverse:
        pen = ReverseContourPen(pen)
    for x, y, radius, inner in [(300, 300, 300, False), (300, 300, 200, True)]:
        p = ReverseContourPen(pen) if inner else pen
        k = radius*.55228475
        p.moveTo((x, y-radius))
        p.curveTo((x+k, y-radius), (x+radius, y-k), (x+radius, y))
        p.curveTo((x+radius, y+k), (x+k, y+radius), (x, y+radius))
        p.curveTo((x-k, y+radius), (x-radius, y+k), (x-radius, y))
        p.curveTo((x-radius, y-k), (x-k, y-radius), (x, y-radius))
        p.closePath()
    outline = Outline()
    font['bowl'].draw(outline)
    return outline.contours


@pytest.mark.parametrize('reverse,shear', [(False, 0), (True, 0), (False, .25)])
def test_closed_bowl_retains_candidates_but_never_stem_roles(reverse, shear):
    contours = bowl(reverse, shear)
    lower, _ = lower_returns(contours, [], 1000, shear)
    upper, _ = upper_arches(contours, 1000, shear)
    assert len(lower) == len(upper) == 1
    for row in lower+upper:
        assert row['anatomical_scope']['kind'] == 'closed-counter'
        assert row['role'] == 'unresolved'
        assert row['counter_sections']
        assert not row.get('conflicts')
    assert upper[0]['counter_topology']['probe'][1] > 0


def test_short_terminal_without_stem_band_is_not_a_supported_connection():
    font = ufoLib2.Font()
    pen = font.newGlyph('terminal').getPen()
    pen.moveTo((0, 600))
    for p in [(0, 0), (400, 0), (400, 210), (300, 210), (300, 150)]:
        pen.lineTo(p)
    pen.curveTo((300, 122), (278, 100), (250, 100))
    pen.lineTo((150, 100))
    pen.curveTo((122, 100), (100, 122), (100, 150))
    pen.lineTo((100, 600))
    pen.closePath()
    outline = Outline()
    font['terminal'].draw(outline)
    row = lower_returns(outline.contours, [], 1000)[0][0]
    assert row['anatomical_scope']['kind'] == 'terminal-curve'
    assert row['role'] == row['status'] == 'unresolved'
    assert row['arm_context'][1]['failures']


def test_closed_counter_cannot_be_promoted_by_nearby_paired_stems():
    contours = bowl()
    candidate = lower_returns(contours, [], 1000)[0][0]
    pairs = [{'geometry_id': f'stem-{i}', 'length_em': .5,
              'centerline': [(path[-1][0], 0), (path[-1][0], 600)],
              'edges': [[path[-1]]]} for i, path in enumerate(candidate['paths'])]
    row = lower_returns(contours, pairs, 1000)[0][0]
    assert all(len(n) == 1 for n in row['neighbours'])
    assert row['status'] == 'counter-observed'
    assert row['role'] == 'unresolved'
    assert row['anatomical_scope']['kind'] == 'closed-counter'
