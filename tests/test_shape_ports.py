"""Boundary measurement on independent analytic examples."""

import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import derive
import shape_ports as ports


def rectangle(pen, x0, y0, x1, y1, reverse=False):
    points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if reverse:
        points.reverse()
    pen.moveTo(points[0])
    for pt in points[1:]:
        pen.lineTo(pt)
    pen.closePath()


def outline(counter=False):
    font = ufoLib2.Font()
    glyph = font.newGlyph("test")
    rectangle(glyph.getPen(), 0, 0, 100, 100)
    if counter:
        rectangle(glyph.getPen(), 25, 25, 75, 75, reverse=True)
    return derive.to_path(font, glyph)


def test_counter_is_not_an_attachment_interval():
    result = ports.measure(outline(counter=True), [50, -10, 110, 110])
    left = result[0]
    assert left["status"] == "measured"
    assert [p["cut_width_units"] for p in left["ports"]] == [25, 25]
    assert all(s["status"] == "no-port" for s in result[1:])


def test_coincident_edges_and_crop_corners_are_unresolved():
    result = ports.measure(outline(), [0, 20, 50, 80])
    assert result[0]["status"] == "ambiguous"
    assert any("coincident" in issue for issue in result[0]["issues"])
    assert all(s["status"] == "ambiguous" and not s["ports"] for s in result)


def test_native_frame_preserves_italic_shear():
    result = ports.measure(outline(), [50, -10, 110, 110], slant=.2)[0]
    assert result["ports"][0]["cut_width_units"] == 100
    top = result["events"][-1]
    assert top["position"] == [50, 100]
    assert top["native_position"] == [70, 100]
    assert top["native_tangent"] == [-1, 0]


def test_cubic_has_all_three_intersections():
    # x(t) = (t-.2)(t-.5)(t-.8); independently known roots.
    points = [(-.08, 0), (.14, 1/3), (-.14, 2/3), (.08, 1)]
    assert ports.roots(points, 0, 0) == pytest.approx([.2, .5, .8])
    assert ports.evaluate(points, .5) == pytest.approx((0, .5))


def test_tangency_does_not_create_port():
    font = ufoLib2.Font()
    glyph = font.newGlyph("curve")
    pen = glyph.getPen()
    pen.moveTo((0, 0))
    pen.qCurveTo((50, 100), (100, 0))
    pen.closePath()
    side = ports.measure(derive.to_path(font, glyph), [-10, -10, 110, 50])[-1]
    assert side["status"] == "ambiguous"
    assert any("tangent" in e["flags"] for e in side["events"])
    assert not side["ports"]


def test_open_contour_rejected():
    pen = ports.Segments()
    pen.moveTo((0, 0))
    pen.lineTo((100, 0))
    with pytest.raises(ValueError, match="closed"):
        pen.endPath()


def test_comparison_refuses_ambiguous_or_different_topology():
    simple = {"sides": ports.measure(outline(), [50, -10, 110, 110])}
    counter = {"sides": ports.measure(outline(counter=True), [50, -10, 110, 110])}
    corner = {"sides": ports.measure(outline(), [0, 20, 50, 80])}
    assert ports.compare(simple, counter)["status"] == "different-cut-topology"
    assert ports.compare(simple, corner)["status"] == "needs-seam-design"
    result = ports.compare(simple, simple)
    assert result["status"] == "measured-constraints"
    assert result["pairs"][0]["cut_width_difference_units"] == 0
    assert result["pairs"][0]["edge_tangent_difference_degrees"] == [0, 0]
