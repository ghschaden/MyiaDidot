"""Counter gate traces explain omissions without changing recognition."""
import math
import sys
from pathlib import Path

import pytest
from fontTools.misc.transform import Transform
from ufoLib2.objects import Component

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from relationships.arches import upper_arches
from relationships.candidate_diagnostics import candidate_diagnostics
from relationships.geometry import Outline
from relationships.returns import lower_returns
from test_lower_returns import fixture


def contours(font):
    outline = Outline()
    font['u'].draw(outline)
    return outline.contours


@pytest.mark.parametrize('mode', ['normal', 'reverse', 'start', 'shear', 'subdivide', 'angular'])
@pytest.mark.parametrize('policy', ['baseline', 'wide-morphology'])
def test_tracing_preserves_both_observers_and_policies(mode, policy):
    font = fixture(mode)
    shape = contours(font)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    for observe in [lambda trace: lower_returns(shape, [], 1000, slant, terminal_policy=policy, diagnostics=trace),
                    lambda trace: upper_arches(shape, 1000, slant, terminal_policy=policy, diagnostics=trace)]:
        trace = []
        assert observe(trace) == observe(None)
        assert trace
        assert all(t['stage'] in ('ink-side', 'shoulders', 'bend', 'opening', 'clearance', 'candidate') for t in trace)


def test_sharp_v_is_recorded_as_rejected_and_has_no_terminal_evidence():
    trace = []
    rows, _ = lower_returns(contours(fixture('angular')), [], 1000, diagnostics=trace)
    angular = [t for t in trace if t['stage'] == 'bend']
    assert not rows and len(angular) == 1
    assert angular[0]['point'] == (200, 100)
    assert angular[0]['measurements']['bend_degrees'] == pytest.approx(90)
    assert angular[0]['status'] == 'rejected'
    assert not any('terminal_context' in t for t in trace)


def test_shoulder_failure_retains_partial_rise_without_claiming_later_gates():
    shape = [[tuple((x, y*.05) for x, y in s) for s in c] for c in contours(fixture())]
    trace = []
    assert not lower_returns(shape, [], 1000, diagnostics=trace)[0]
    failed = [t for t in trace if t['stage'] == 'shoulders']
    assert failed
    assert all(max(t['measurements']['arm_rise_em']) < .08 for t in failed)
    assert all('opening_em' not in t['measurements'] for t in failed)


def test_interrupted_clearance_is_not_angular_or_terminal_rejection():
    font = fixture()
    pen = font['u'].getPen()
    pen.moveTo((50, 140))
    for point in [(350, 140), (350, 160), (50, 160)]:
        pen.lineTo(point)
    pen.closePath()
    trace = []
    assert not lower_returns(contours(font), [], 1000, diagnostics=trace)[0]
    failed = [t for t in trace if t['stage'] == 'clearance']
    assert len(failed) == 1
    assert failed[0]['measurements']['clear_sections'] < 8


def test_upper_diagnostics_restore_source_frame_and_preserve_provenance():
    font = fixture('upper')
    font.newGlyph('copy').components.append(Component('u', Transform(1, 0, 0, 1, 30, 40)))
    before = font.json_dumps()
    result = candidate_diagnostics(font, ['copy'], 'pinned')
    accepted = [t for t in result['traces'] if t['status'] == 'accepted']
    assert len(accepted) == 1
    assert accepted[0]['detector'] == 'upper_arches'
    assert accepted[0]['point'] == (230, 540)
    assert accepted[0]['contour_origin']['component_path'] == [0]
    assert accepted[0]['contour_origin']['source_glyph'] == 'u'
    assert accepted[0]['source_sha256'] == 'pinned'
    assert candidate_diagnostics(font, ['copy'], 'other')['traces'][0]['id'] != result['traces'][0]['id']
    assert font.json_dumps() == before


def test_incomplete_outline_is_withheld_from_gate_traces():
    font = fixture()
    font.newGlyph('broken').components.extend([Component('u'), Component('absent')])
    result = candidate_diagnostics(font, ['broken'], 'pinned')
    assert not result['traces']
    assert result['observations']['broken']['status'] == 'unresolved'
    assert result['observations']['broken']['issues']
