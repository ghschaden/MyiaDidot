"""Reciprocal angular closure is local morphology, independent of branch roles."""
import copy
import math
import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.angular import angular_observations, angular_terminal_context
from relationships.arches import reflect_terminal
from relationships.terminal_evaluation import evaluate_angular_terminal_arms
from shape_relationships import ROOT, run
from test_angular_observations import contours, fixture
from test_terminal_context import fixture as terminal_fixture
from test_terminal_evaluation import example


def terminal_font(mode='normal'):
    font = ufoLib2.Font()
    font.info.unitsPerEm = 1000
    font.info.styleName = 'Angular terminal'
    shape = [(0, 600), (0, 0), (390, 0), (390, 260), (300, 260),
             (300, 200), (200, 100), (100, 200), (100, 600)]
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


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'subdivide', 'shear', 'upper'])
@pytest.mark.parametrize('policy', ['baseline', 'wide-morphology'])
def test_transformed_angular_terminal_keeps_source_occurrence_and_roles(mode, policy):
    font = terminal_font(mode)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    shape = contours(font)
    off = angular_observations(shape, 1000, slant)
    result = angular_observations(shape, 1000, slant, terminal_policy=policy)
    assert len(result) == 1
    row = result[0]
    left, right = row['terminal_context']
    assert left['status'] == 'unresolved'
    assert right['status'] == 'verified-contour-terminal'
    assert right['section']['p'] == pytest.approx((280, 420 if mode == 'upper' else 180))
    assert right['section']['q'] == pytest.approx((390, 420 if mode == 'upper' else 180))
    assert right['trace'][-1] == pytest.approx(right['section']['q'])
    assert row['role'] == 'unresolved'
    clean = copy.deepcopy(result)
    clean[0].pop('terminal_context')
    clean[0]['terminal_evidence'] = 'not-evaluated'
    assert clean == off


@pytest.mark.parametrize('kind', ['short', 'obstructed'])
def test_incomplete_window_never_calls_closure(monkeypatch, kind):
    font = fixture(short=kind == 'short')
    if kind == 'obstructed':
        pen = font['junction'].getPen()
        pen.moveTo((50, 140))
        for point in [(350, 140), (350, 160), (50, 160)]:
            pen.lineTo(point)
        pen.closePath()
    def unexpected(*args):
        pytest.fail('Closure must not run on an incomplete angular window')
    monkeypatch.setattr('relationships.angular.angular_terminal_context', unexpected)
    rows = angular_observations(contours(font), 1000, terminal_policy='baseline')
    assert rows
    for row in rows:
        assert row['status'] == 'unresolved'
        assert row['terminal_evidence'] == 'withheld-incomplete-window'
        assert all(c['status'] == 'not-evaluated' and not c['window_checks'] for c in row['terminal_context'])


@pytest.mark.parametrize('reverse', [False, True])
def test_known_broad_lobe_control_is_still_admitted_only_by_wider_policy(reverse):
    field, arc, direction = terminal_fixture(reverse, width=140)
    poly = field.polygons[0]
    start = arc-direction*10
    arm = {'start_arc_units': start, 'source_direction': direction,
           'path': [poly.at(start)[0].tolist(), poly.at(arc)[0].tolist()]}
    base = angular_terminal_context(field, 0, arm, 1000, 'baseline')
    wide = angular_terminal_context(field, 0, arm, 1000, 'wide-morphology')
    assert base['status'] == wide['baseline_status'] == 'unresolved'
    assert wide['status'] == 'verified-contour-terminal'
    assert wide['window_checks']['span']['measured_em'] == pytest.approx(.14)
    assert reflect_terminal(reflect_terminal(wide)) == wide


def test_bad_source_arc_is_withheld_instead_of_projected_to_a_nearby_boundary():
    field, arc, direction = terminal_fixture()
    arm = {'start_arc_units': arc+5, 'source_direction': direction,
           'path': [field.polygons[0].at(arc)[0].tolist()]}
    result = angular_terminal_context(field, 0, arm, 1000, 'baseline')
    assert result['status'] == 'not-evaluated'
    assert not result['window_checks']


def angular_example():
    corpus, report = example()
    old = report['upper_arches']['results'][0]
    report['angular_junctions'] = {'source_sha256': report['source']['sha256'],
        'scope': report['upper_arches']['scope'], 'results': [{**old, 'point': old['crown'],
        'seed_detector': 'upper_arches'}]}
    return corpus, report


def test_angular_scores_keep_closure_on_nonterminal_as_a_mismatch_without_mutation():
    corpus, report = angular_example()
    corpus['regions'][0]['terminal_arms']['right'] = 'nonterminal'
    before = copy.deepcopy((corpus, report))
    result = evaluate_angular_terminal_arms(corpus, report, 1000)
    assert [r['outcome'] for r in result['results']] == ['not-promoted', 'terminal-on-nonterminal']
    assert all(r['evidence']['normal_cap'] is None for r in result['results'])
    assert result['scope'] == 'angular-boundaries'
    assert (corpus, report) == before


@pytest.mark.parametrize('case,outcome', [('withheld','unreported'), ('ambiguous-label','unscored'),
                                        ('missing','unobserved'), ('duplicate','ambiguous-assignment')])
def test_angular_scores_do_not_hide_withheld_or_ambiguous_arms(case, outcome):
    corpus, report = angular_example()
    rows = report['angular_junctions']['results']
    if case == 'withheld':
        rows[0]['terminal_context'][1] = {'status': 'not-evaluated'}
    elif case == 'ambiguous-label':
        corpus['regions'][0]['terminal_arms']['right'] = 'ambiguous'
    elif case == 'missing':
        rows.clear()
    else:
        rows.append({**rows[0], 'geometry_id': 'duplicate'})
    result = evaluate_angular_terminal_arms(corpus, report, 1000)
    assert result['results'][1]['outcome'] == outcome


def test_stale_angular_source_and_unknown_policy_are_rejected():
    corpus, report = angular_example()
    report['angular_junctions']['source_sha256'] = 'other'
    with pytest.raises(ValueError, match='Stale angular'):
        evaluate_angular_terminal_arms(corpus, report, 1000)
    with pytest.raises(ValueError, match='Unknown reciprocal'):
        angular_observations([], 1000, terminal_policy='typo')


def test_closure_flag_enables_angular_scope_without_changing_rounded_results(tmp_path):
    source = tmp_path/'angular.ufo'
    terminal_font().save(source)
    common = dict(proof_names=['junction'], boundary_glyphs=['junction'], returns=True, arches=True)
    off = run(source, ROOT/'build/test-angular-terminal/off', angular=True, **common)
    on = run(source, ROOT/'build/test-angular-terminal/on', angular_terminals=True, **common)
    assert on['lower_returns'] == off['lower_returns']
    assert on['upper_arches'] == off['upper_arches']
    assert off['angular_junctions']['format'] == 'myiadidot-angular-observations-v1'
    assert on['angular_junctions']['format'] == 'myiadidot-angular-observations-v2'
    assert on['angular_junctions']['terminal_policy']['cap_width_em'] == .12
    assert '#7141b5' in (ROOT/'build/test-angular-terminal/on/angular.svg').read_text()


def test_closed_counter_is_retained_and_never_gains_a_branch_role():
    font = ufoLib2.Font()
    pen = font.newGlyph('junction').getPen()
    for points in [[(0, 0), (400, 0), (400, 600), (0, 600)],
                   [(100, 100), (100, 500), (300, 500), (300, 100)]]:
        pen.moveTo(points[0])
        for point in points[1:]:
            pen.lineTo(point)
        pen.closePath()
    result = angular_observations(contours(font), 1000, terminal_policy='wide-morphology')
    assert len(result) == 2
    for row in result:
        assert row['counter_topology']['kind'] == 'closed-counter'
        assert row['role'] == 'unresolved'
        assert all(c['status'] == 'unresolved' and 'another contour' in c['reason'] for c in row['terminal_context'])
