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
