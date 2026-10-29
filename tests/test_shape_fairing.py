"""Geometry contracts and source protection for the Bold Italic candidates."""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import shape_fairing as fair


def test_whole_arc_preserves_end_constraints_and_c2_interior():
    original = [((0., 0.), (0., 40.), (100., 40.), (100., 0.))]
    curves = fair.fit_arc(original, 1e-7, pieces=6)
    assert curves[0][0] == original[0][0]
    assert curves[-1][-1] == original[-1][-1]
    for t, curve in ((0, curves[0]), (1, curves[-1])):
        assert fair.curvature.curvature(curve, t) == pytest.approx(fair.curvature.curvature(original[0], t), abs=1e-9)
        assert fair.seams.unit(*curve[:2] if t == 0 else curve[-2:]) == pytest.approx(
            fair.seams.unit(*original[0][:2] if t == 0 else original[0][-2:]))
    for left, right in zip(curves, curves[1:]):
        assert left[-1] == right[0]
        for order in (1, 2):
            a, b = left, right
            for _ in range(order):
                a, b = fair.curvature.derivative(a), fair.curvature.derivative(b)
            assert fair.curvature.evaluate(a, 1) == pytest.approx(fair.curvature.evaluate(b, 0), abs=1e-8)


def test_inconsistent_constraints_are_refused():
    with pytest.raises(ValueError, match='Inconsistent'):
        fair.constrained_fit([[1, 0]], [[0, 0]], [[1, 0], [1, 0]], [[0, 0], [1, 1]])


def test_invalid_fit_and_degenerate_arc_are_refused():
    with pytest.raises(ValueError, match='Invalid'):
        fair.fit_arc([((0, 0), (1, 1))], -1)
    with pytest.raises(ValueError, match='Degenerate'):
        fair.fit_arc([((0, 0), (0, 0))], 1)


def test_cardinal_split_preserves_closed_circle_ink():
    k = .5522847498307936
    circle = [((1, 0), (1, k), (k, 1), (0, 1)),
              ((0, 1), (-k, 1), (-1, k), (-1, 0)),
              ((-1, 0), (-1, -k), (-k, -1), (0, -1)),
              ((0, -1), (k, -1), (1, -k), (1, 0))]
    arcs = fair.extrema_arcs(circle)
    assert len(arcs) == 4
    assert [c for arc in arcs for c in arc] == circle


def test_polygonal_area_converges_for_known_parabolic_region():
    # Region below y=x² from x=0 to x=1 has area 1/3.
    contour = [((0, 0), (.5, 0), (1, 1)), ((1, 1), (1, 0)), ((1, 0), (0, 0))]
    assert fair.flat_path([contour], 128).area == pytest.approx(1/3, abs=2e-5)


@pytest.mark.parametrize('name,builder', [('h', fair.inner_shoulder), ('o', fair.spline_oval)])
def test_bolditalic_candidates_preserve_sources_and_pass_local_gates(name, builder):
    before = ufoLib2.Font.open(fair.seams.consistency.source_paths()['BoldItalic'])
    snapshot = before.json_dumps()
    contours, construction = builder(before)
    after = copy.deepcopy(before)
    fair.seams.install_scratch(after[name], contours, 0)
    metrics = fair.measurements(before, after, name, construction)
    gate = fair.gates(before, after, name, construction, metrics)
    assert gate['passed'], gate['failures']
    assert before.json_dumps() == snapshot
    assert after[name].width == before[name].width
    assert after.json_dumps()  # UFO serialization must accept every fitted coordinate.
    assert metrics['normal_sections']['max_absolute_change_percent'] <= 10
    assert metrics['fitted_interior_inflections'] == (1 if name == 'h' else 0)
    # Independent continuity checks include the o contour's closing join.
    assert max(abs(j['curvature_jump_inverse_units']) for j in gate['joins']) < 1e-7
    assert all(c['minimum_forward_control_projection'] > 0 for c in gate['segment_certificates'])
    if name == 'o':
        assert np.min([c['control_cross_products'] for c in gate['segment_certificates']]) >= 0


def test_inner_shoulder_refuses_unrecognised_topology():
    font = ufoLib2.Font()
    font.info.xHeight = 800
    font.newGlyph('h')
    with pytest.raises(ValueError, match='unique arc'):
        fair.inner_shoulder(font)
