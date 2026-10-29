"""Analytic examples independent of the production outlines."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_curvature as curvature
import shape_seams as seams


def test_line_parabola_and_stationary_point():
    assert curvature.curvature(((0, 0), (3, 4)), .3) == 0
    # B(t) = (t, t²): k(0) = 2, k(1) = 2 / 5**1.5.
    parabola = ((0, 0), (.5, 0), (1, 1))
    assert curvature.curvature(parabola, 0) == 2
    assert curvature.curvature(parabola, 1) == pytest.approx(2/5**1.5)
    assert curvature.curvature(((0, 0), (0, 0), (1, 1)), 0) is None


def test_signed_curvature_scaling_reflection_and_subdivision():
    curve = ((0, 0), (0, 40), (100, 40), (100, 0))
    base = curvature.curvature(curve, .4)
    assert curvature.curvature(tuple((2*x, 2*y) for x, y in curve), .4) == pytest.approx(base/2)
    assert curvature.curvature(tuple((-x, y) for x, y in curve), .4) == pytest.approx(-base)
    part = seams.subcurve(curve, .2, .8)
    assert curvature.curvature(part, 1/3) == pytest.approx(base)


def test_analytic_inflection_and_no_false_line_inflections():
    curve = ((0, 0), (1, 1), (2, -1), (3, 0))
    assert curvature.inflections(curve) == pytest.approx([.5])
    assert curvature.inflections(((0, 0), (1, 0), (2, 0), (3, 0))) == []
    assert curvature.inflections(((0, 0), (0, 1), (1, 1), (1, 0))) == []


def test_g1_join_can_have_curvature_jump():
    curves = [((0, 0), (1, 0)), ((1, 0), (1.5, 0), (2, 1))]
    join = curvature.audit(curves)["joins"][0]
    assert join["position_gap_units"] == 0
    assert join["tangent_angle_degrees"] == 0
    assert join["curvature_jump_inverse_units"] == 2


def test_subdivision_does_not_create_curvature_jump():
    curve = ((0, 0), (0, 40), (100, 40), (100, 0))
    join = curvature.audit(seams.split(curve, .37))["joins"][0]
    assert join["curvature_jump_inverse_units"] == pytest.approx(0, abs=1e-12)


def test_unresolved_join_is_not_reported_as_smooth():
    report = curvature.audit([((0, 0), (0, 0)), ((0, 0), (1, 1))])
    assert report["unresolved_sample_count"] == 33
    assert report["joins"][0]["tangent_angle_degrees"] is None
    assert report["joins"][0]["curvature_jump_inverse_units"] is None
