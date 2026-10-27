"""Independent geometry and source-protection tests for connected fitting."""

import copy
import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_seams as seams


def test_subdivision_preserves_curve_at_independent_parameters():
    curve = ((0, 0), (30, 100), (70, -20), (100, 50))
    part = seams.subcurve(curve, .2, .8)
    for t in (0, .1, .5, .9, 1):
        assert seams.ports.evaluate(part, t) == pytest.approx(seams.ports.evaluate(curve, .2+.6*t))


def test_fit_retains_target_endpoints_tangents_and_donor_core():
    donor = [((0, 0), (0, 40), (100, 40), (100, 0))]
    target = [((0, 3), (10, 43), (80, 40), (100, 2))]
    fitted, report = seams.fit_arc(donor, target, (0, 0, 100, 40), (0, 0, 100, 40), seams.POLICY)
    assert fitted[0][0] == target[0][0]
    assert fitted[-1][-1] == target[-1][-1]
    assert seams.unit(*fitted[0][:2]) == pytest.approx(seams.unit(*target[0][:2]))
    assert seams.unit(*fitted[-1][-2:]) == pytest.approx(seams.unit(*target[0][-2:]))
    # Neither interior endpoints nor their tangent controls may move.
    first, tail = seams.split(donor[0], .25)
    middle, last = seams.split(tail, .75)
    assert fitted[0][2:] == first[2:]
    assert fitted[1] == middle
    assert fitted[-1][:2] == last[:2]
    assert report["endpoint_error_units"] == 0


def test_fitting_refuses_large_seam_correction():
    donor = [((0, 0), (0, 40), (100, 40), (100, 0))]
    target = [((0, 30), (10, 50), (80, 40), (100, 2))]
    with pytest.raises(ValueError, match="budget"):
        seams.fit_arc(donor, target, (0, 0, 100, 40), (0, 0, 100, 40), seams.POLICY)


def test_partition_recombines_same_ink_and_keeps_outside_curve_spans():
    contours = [[((0, 0), (100, 0)), ((100, 0), (100, 100)),
                 ((100, 100), (0, 100)), ((0, 100), (0, 0))]]
    chunks = seams.partition(contours, [-10, 40, 110, 80])
    outside = [chunk for chunk in chunks[0] if not chunk["inside"]]
    assert len(outside) == 2
    recombined = [[curve for chunk in chunks[0] for curve in chunk["curves"]]]
    assert seams.derive.path_op(seams.path_for(contours), seams.path_for(recombined), "XOR").area == 0
    assert set(seams.arcs(chunks, [-10, 40, 110, 80])) == {("bottom", "top"), ("top", "bottom")}


def test_font_validation_detects_unrelated_metadata_change():
    before = ufoLib2.Font()
    before.newGlyph("a").width = 100
    after = copy.deepcopy(before)
    after["a"].width = 101
    with pytest.raises(ValueError, match="metadata"):
        seams.validate_font(before, after, set())


@pytest.mark.parametrize("style", seams.consistency.STYLES)
def test_real_seams_have_declared_topology_and_repeatable_bounded_fits(style):
    font = ufoLib2.Font.open(seams.consistency.source_paths()[style])
    snapshot = font.json_dumps()
    for recipe in seams.POLICY["recipes"]:
        first, shear, report = seams.fit(font, recipe)
        second, repeated_shear, repeated_report = seams.fit(font, recipe)
        assert not report["failures"]
        assert first == second and shear == repeated_shear and report == repeated_report
        assert report["outside_curve_spans_unchanged"]
        assert all(a["endpoint_error_units"] == 0 for a in report["arcs"])
    assert font.json_dumps() == snapshot
