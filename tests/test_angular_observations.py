"""Angular arms have their own observation scope and no inherited roles."""
import math
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.misc.transform import Transform
from ufoLib2.objects import Component

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.angular import angular_observations, angular_report, bounded_arm
from relationships.geometry import Outline
from relationships.returns import lower_returns
from shape_relationships import ROOT, run


def fixture(mode='normal', short=False):
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Angular'
    shape = [(0, 600), (0, 0), (400, 0), (400, 600),
             (300, 600), (300, 200), (200, 100), (100, 200), (100, 600)]
    if short:
        shape = [(200+(x-200)*.1, 100+(y-100)*.1) for x, y in shape]
    if mode == 'reverse':
        shape.reverse()
    elif mode == 'start':
        shape = shape[4:]+shape[:4]
    elif mode == 'subdivide':
        shape = [p for a, b in zip(shape, shape[1:]+shape[:1])
                 for p in [a, ((a[0]+b[0])/2, (a[1]+b[1])/2)]]
    elif mode == 'shear':
        font.info.italicAngle = -math.degrees(math.atan(.25))
        shape = [(x+.25*y, y) for x, y in shape]
    elif mode == 'upper':
        shape = [(x, 600-y) for x, y in shape]
    pen = font.newGlyph('junction').getPen()
    pen.moveTo(shape[0])
    for p in shape[1:]:
        pen.lineTo(p)
    pen.closePath()
    return font


def contours(font):
    pen = Outline()
    font['junction'].draw(pen)
    return pen.contours


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'subdivide', 'shear'])
def test_known_angular_arms_are_observed_outside_rounded_scope(mode):
    font = fixture(mode)
    shape = contours(font)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    assert not lower_returns(shape, [], 1000, slant)[0]
    result = angular_observations(shape, 1000, slant)
    assert len(result) == 1
    row = result[0]
    assert row['status'] == 'visible-angular-arms'
    assert row['bend_degrees'] == pytest.approx(90)
    assert row['point'] == pytest.approx((200, 100))
    assert all(a['reaches_window'] for a in row['arms'])
    assert [a['path'][-1] for a in row['arms']] == pytest.approx([(120, 180), (280, 180)])
    assert row['counter_sections'][-1]['clearance_units'] == pytest.approx(160)
    assert len(row['counter_sections']) == 8
    assert row['role'] == 'unresolved'
    assert row['terminal_evidence'] == 'not-evaluated'
    assert 'terminal_context' not in row


def test_short_merge_keeps_both_partial_paths_without_smaller_window():
    row = angular_observations(contours(fixture(short=True)), 1000)[0]
    assert row['status'] == 'unresolved'
    assert row['clearance_failure'] == 'arm-window-unavailable'
    assert all(not a['reaches_window'] and a['stop'] == 'backtrack' for a in row['arms'])
    assert [a['achieved_rise_em'] for a in row['arms']] == pytest.approx([.05, .05])
    assert all(a['path'] for a in row['arms'])
    assert len(row['counter_sections']) == 5
    assert row['terminal_evidence'] == 'not-evaluated'


def test_reflection_restores_paths_sections_point_and_topology_probe():
    lower = angular_observations(contours(fixture()), 1000)[0]
    upper = angular_observations(contours(fixture('upper')), 1000)[0]
    assert upper['seed_detector'] == 'upper_arches'
    assert upper['point'] == pytest.approx((200, 500))
    assert upper['counter_topology']['probe'][1] == pytest.approx(499)
    assert upper['paths'] == [[(x, 600-y) for x, y in p] for p in lower['paths']]
    assert upper['counter_sections'] == [{**s, 'y': 600-s['y']} for s in lower['counter_sections']]


def test_intervening_ink_prevents_complete_visibility():
    font = fixture()
    pen = font['junction'].getPen()
    pen.moveTo((50, 140))
    for p in [(350, 140), (350, 160), (50, 160)]:
        pen.lineTo(p)
    pen.closePath()
    row = next(r for r in angular_observations(contours(font), 1000) if r['point'] == [200, 100])
    assert all(a['reaches_window'] for a in row['arms'])
    assert row['status'] == 'unresolved'
    assert row['clearance_failure'] == 'interrupted-clearance'
    assert len(row['counter_sections']) < 8


def test_closed_angular_counter_keeps_containment_and_no_branch_role():
    font = ufoLib2.Font()
    pen = font.newGlyph('junction').getPen()
    for points in [[(0, 0), (400, 0), (400, 600), (0, 600)],
                   [(100, 100), (100, 500), (300, 500), (300, 100)]]:
        pen.moveTo(points[0])
        for p in points[1:]:
            pen.lineTo(p)
        pen.closePath()
    result = angular_observations(contours(font), 1000)
    assert len(result) == 2
    assert all(r['counter_topology']['kind'] == 'closed-counter' for r in result)
    assert all(r['role'] == 'unresolved' for r in result)


def test_components_and_incomplete_fields_retain_pinned_provenance():
    font = fixture()
    font.newGlyph('wrapper').components.append(Component('junction', Transform(1, 0, 0, 1, 30, 40)))
    font.newGlyph('broken').components.extend([Component('junction'), Component('absent')])
    before = font.json_dumps()
    result = angular_report(font, {'source_identity': 'pinned'}, ['wrapper', 'broken'])
    assert len(result['results']) == 1
    row = result['results'][0]
    assert row['point'] == pytest.approx((230, 140))
    assert row['contour_origin']['component_path'] == [0]
    assert row['contour_origin']['source_glyph'] == 'junction'
    assert row['source_sha256'] == 'pinned'
    assert result['observations']['broken']['status'] == 'unresolved'
    assert result['omissions']
    assert font.json_dumps() == before


def test_optional_run_channel_preserves_all_existing_report_fields(tmp_path):
    source = tmp_path/'angular.ufo'
    fixture().save(source)
    common = dict(proof_names=['junction'], boundary_glyphs=['junction'], returns=True, arches=True)
    base = run(source, ROOT/'build/test-angular-observations/baseline', **common)
    trial = run(source, ROOT/'build/test-angular-observations/opt-in', angular=True, **common)
    observation = trial.pop('angular_junctions')
    assert trial == base
    assert observation['results'][0]['status'] == 'visible-angular-arms'
    assert '#007c91' in (ROOT/'build/test-angular-observations/opt-in/angular.svg').read_text()
    assert 'angular.svg' in (ROOT/'build/test-angular-observations/opt-in/index.html').read_text()


@pytest.mark.parametrize('em,slant', [(0, 0), (float('nan'), 0), (1000, float('inf'))])
def test_invalid_frames_are_rejected(em, slant):
    with pytest.raises(ValueError, match='coordinate frame'):
        angular_observations([], em, slant)


def test_slow_reversal_is_bounded_before_a_remote_lobe():
    path = [(0, 0), (10, 50), *[(10+k, 50-k) for k in range(1, 12)], (30, 100)]
    arm = {'path': path, 'reaches_window': True, 'achieved_rise_em': .1,
           'stop': 'window-reached'}
    result = bounded_arm(arm, 0, 1000)
    assert not result['reaches_window']
    assert result['stop'] == 'cumulative-backtrack'
    assert result['achieved_rise_em'] == .05
    assert result['path'][-1] == (13, 47)
    assert arm['path'] == path  # The shared return diagnostics are not modified.
