"""Terminal closure evidence must remain independent of stem-band support."""
import sys
from pathlib import Path

import pytest
import ufoLib2
from fontTools.pens.reverseContourPen import ReverseContourPen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.arches import reflect_terminal
from relationships.boundaries import Sections
from relationships.geometry import Outline
from relationships.return_context import CONTEXT_POLICY, locate
from relationships.terminal_context import terminal_context


def fixture(reverse=False, height=200, width=90):
    font = ufoLib2.Font()
    pen = font.newGlyph('terminal').getPen()
    if reverse:
        pen = ReverseContourPen(pen)
    pen.moveTo((0, 0))
    for p in [(30, 0), (70, 100), (width, 150), (40, height), (0, 150)]:
        pen.lineTo(p)
    pen.closePath()
    outline = Outline()
    font['terminal'].draw(outline)
    field = Sections(outline.contours, 1000)
    arc = locate(field.polygons[0], (70, 100))
    return field, arc, -1 if reverse else 1


@pytest.mark.parametrize('reverse', [False, True])
def test_angled_terminal_closes_without_parallel_stem_evidence(reverse):
    field, arc, direction = fixture(reverse)
    section, reason = field.section(0, arc)
    assert section is None and reason  # Not promoted into a stem width.
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'verified-contour-terminal'
    assert result['section']['q'] == pytest.approx((0, 100))
    assert result['trace'][-1] == result['section']['q']
    assert result['arc_length_units'] < 350
    reflected = reflect_terminal(result)
    assert reflected['section']['q'] == pytest.approx((0, -100))
    assert reflected['trace'][-1] == reflected['section']['q']
    assert reflect_terminal(reflected) == result


@pytest.mark.parametrize('height,width', [(400, 90), (200, 140)])
def test_oversize_contour_does_not_gain_terminal_evidence(height, width):
    field, arc, direction = fixture(height=height, width=width)
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert 'window' in result['reason']


def test_wrong_direction_cannot_use_route_through_counter_floor():
    field, arc, direction = fixture()
    result = terminal_context(field, 0, arc, -direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert 'below' in result['reason']


def test_wrong_reverse_boundary_is_refused(monkeypatch):
    field, arc, direction = fixture()
    original = field.hit
    calls = []

    def wrong(p, normal):
        hit, error = original(p, normal)
        calls.append(1)
        if len(calls) == 2:
            hit = (hit[0]+[5, 0], *hit[1:])
        return hit, error

    monkeypatch.setattr(field, 'hit', wrong)
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert 'reverse correspondence' in result['reason']


def test_other_contour_is_not_a_terminal_return(monkeypatch):
    field, arc, direction = fixture()
    original = field.hit

    def other(p, normal):
        hit, error = original(p, normal)
        return (hit[0], 1, *hit[2:]), error

    monkeypatch.setattr(field, 'hit', other)
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert 'another contour' in result['reason']


def test_window_diagnostics_explain_width_failure_without_relaxing_it():
    field, arc, direction = fixture(width=140)
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    checks = result['window_checks']
    assert checks['trace']['passes'] and checks['rise']['passes']
    assert checks['rise']['passes_minimum']
    assert checks['span']['measured_em'] == pytest.approx(.14)
    assert checks['span']['ratio_to_maximum'] == pytest.approx(7/6)
    assert checks['span']['excess_units'] == pytest.approx(20)
    assert not checks['span']['passes']
    assert reflect_terminal(result)['window_checks'] == checks


def test_trace_refusal_does_not_claim_unmeasured_dimensions_pass():
    field, arc, direction = fixture(height=400)
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert set(result['window_checks']) == {'trace'}
    assert not result['window_checks']['trace']['passes']


def test_preclosure_refusal_has_no_window_claims(monkeypatch):
    field, arc, direction = fixture()
    monkeypatch.setattr(field, 'hit', lambda *args: (None, 'ambiguous boundary'))
    result = terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    assert result['status'] == 'unresolved'
    assert result['window_checks'] == {}


@pytest.mark.parametrize('reverse', [False, True])
def test_named_wide_policy_is_morphology_only_and_preserves_default(reverse):
    from relationships.terminal_context import (
        reciprocal_terminal_context,
        scope_terminal_supported,
        terminal_policy,
    )
    field, arc, direction = fixture(reverse, width=140)
    baseline = reciprocal_terminal_context(field, 0, arc, direction, 1000)
    assert baseline == terminal_context(field, 0, arc, direction, 1000, CONTEXT_POLICY)
    wide = reciprocal_terminal_context(field, 0, arc, direction, 1000, 'wide-morphology')
    assert baseline['status'] == wide['baseline_status'] == 'unresolved'
    assert wide['status'] == 'verified-contour-terminal'
    assert not scope_terminal_supported(wide)
    assert not scope_terminal_supported(reflect_terminal(wide))
    assert wide['trace'] == baseline['trace']
    assert terminal_policy()['cap_width_em'] == CONTEXT_POLICY['cap_width_em'] == .12
    assert terminal_policy('wide-morphology')['use_for_roles'] is False
    limits = terminal_policy('wide-morphology')
    limits['cap_width_em'] = 1
    assert terminal_policy('wide-morphology')['cap_width_em'] == .15


@pytest.mark.parametrize('height,width', [(400, 90), (200, 170)])
def test_wide_policy_retains_other_limits(height, width):
    from relationships.terminal_context import reciprocal_terminal_context
    field, arc, direction = fixture(height=height, width=width)
    assert reciprocal_terminal_context(field, 0, arc, direction, 1000,
                                       'wide-morphology')['status'] == 'unresolved'


def test_unknown_policy_is_rejected_even_without_observations():
    from relationships.arches import upper_arches
    from relationships.returns import lower_returns
    from relationships.terminal_context import terminal_policy
    for call in [lambda: terminal_policy('typo'),
                 lambda: lower_returns([], [], 1000, terminal_policy='typo'),
                 lambda: upper_arches([], 1000, terminal_policy='typo')]:
        with pytest.raises(ValueError, match='Unknown reciprocal-terminal policy'):
            call()
