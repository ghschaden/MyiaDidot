"""Independent geometric controls for experimental stroke-section pairing."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.boundaries import paired_boundaries


def polygon(points):
    return [(a, b) for a, b in zip(points, points[1:]+points[:1])]


def rectangle(x=0):
    return polygon([(x, 0), (x+100, 0), (x+100, 600), (x, 600)])


def test_rectangle_has_known_width():
    pairs, _ = paired_boundaries([rectangle()], 1000)
    assert pairs
    assert all(p['metrics']['median_width_em'] == pytest.approx(.1) for p in pairs)
    assert all(abs(p['metrics']['linear_taper']) < 1e-10 for p in pairs)


def test_white_gap_does_not_become_a_stroke():
    pairs, _ = paired_boundaries([rectangle(), rectangle(160)], 1000)
    assert len(pairs) >= 2
    for pair in pairs:
        assert pair['metrics']['median_width_em'] == pytest.approx(.1)
        for s in pair['sections']:
            assert s['source_contour'] == s['target_contour']


def test_taper_is_measured():
    pairs, _ = paired_boundaries([polygon([(0, 0), (80, 0), (120, 600), (0, 600)])], 1000)
    assert pairs
    best = max(pairs, key=lambda p: p['length_em'])
    assert best['metrics']['maximum_width_em'] > best['metrics']['minimum_width_em']+.02
    assert abs(best['metrics']['linear_taper']) == pytest.approx(40/600, abs=.003)


@pytest.mark.parametrize('mode', ['reverse', 'start', 'split', 'rotate', 'shear'])
def test_equivalent_representations_preserve_width(mode):
    c = rectangle(); slant = 0
    if mode == 'reverse':
        c = [tuple(reversed(s)) for s in reversed(c)]
    elif mode == 'start':
        c = c[2:]+c[:2]
    elif mode == 'split':
        c[1:2] = [((100, 0), (100, 300)), ((100, 300), (100, 600))]
    elif mode == 'rotate':
        a = .4
        c = [tuple((x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)) for x, y in s) for s in c]
    else:
        slant = .25
        c = [tuple((x+slant*y, y) for x, y in s) for s in c]
    pairs, _ = paired_boundaries([c], 1000, slant)
    assert pairs
    assert max(pairs, key=lambda p: p['length_em'])['metrics']['median_width_em'] == pytest.approx(.1, abs=1e-5)


def test_counter_is_not_ink():
    outer = polygon([(0, 0), (300, 0), (300, 600), (0, 600)])
    inner = polygon([(60, 60), (60, 540), (240, 540), (240, 60)])
    pairs, _ = paired_boundaries([outer, inner], 1000)
    assert pairs
    assert all(p['metrics']['median_width_em'] == pytest.approx(.06, abs=.001) for p in pairs)


def test_branch_is_not_spanned_as_one_uniform_stroke():
    tee = polygon([(0, 0), (100, 0), (100, 350), (250, 350), (250, 450), (-150, 450), (-150, 350), (0, 350)])
    pairs, notes = paired_boundaries([tee], 1000)
    assert pairs and notes
    assert all(p['metrics']['maximum_width_em'] < .15 for p in pairs)


def test_curved_ribbon_has_radial_width():
    angles = [-.25+i*.5/80 for i in range(81)]
    outside = [(540*math.cos(a), 540*math.sin(a)) for a in angles]
    inside = [(460*math.cos(a), 460*math.sin(a)) for a in reversed(angles)]
    pairs, _ = paired_boundaries([polygon(outside+inside)], 1000)
    assert pairs
    assert max(pairs, key=lambda p: p['length_em'])['metrics']['median_width_em'] == pytest.approx(.08, abs=.0005)
