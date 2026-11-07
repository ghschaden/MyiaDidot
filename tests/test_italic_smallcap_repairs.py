"""Local small-cap repairs keep connected bowls and smooth stem brackets."""

import copy
import math

import pytest
import ufoLib2
from conftest import SOURCES
from fontTools.pens.areaPen import AreaPen
from italic_geometry import SLANT, shear


def test_barred_d_keeps_the_final_bold_smallcap_base():
    import derive
    from built_from import fingerprint
    from drawn import KEY
    from italic_geometry import upright

    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")
    assert font["uniA7C8.sc"].lib[KEY]["bases"]["d.sc"] == fingerprint(font, "d.sc")
    up = upright(font)
    # Clear of the added bar: the stem and round side remain its final D,
    # allowing the two-unit rounding of the intersection operation.
    for y in (150, 300, 700, 900):
        base, derived = (derive.stems_at(up, n, y) for n in ("d.sc", "uniA7C8.sc"))
        assert len(base) == len(derived)
        assert all(abs(a - b) < 2 for row_a, row_b in zip(base, derived, strict=True)
                   for a, b in zip(row_a, row_b, strict=True))


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_lowered_r_smallcap_has_one_outer_and_one_counter(style):
    ufo = ufoLib2.Font.open(SOURCES / f"MyiaDidot-{style}.ufo")
    areas = []
    for contour in ufo["uni0280.sc"].contours:
        pen = AreaPen(ufo)
        contour.draw(pen)
        areas.append(pen.value)
    # The old cut crossed the bowl, leaving two outside contours with
    # the same winding and no closed counter.
    assert len(areas) == 2 and areas[0] * areas[1] < 0, areas


@pytest.mark.parametrize("name", ["uni0253.sc", "uni0257.sc"])
def test_hook_smallcap_upper_stem_joins_are_smooth(name):
    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    glyph = copy.deepcopy(font[name])
    shear(glyph, -SLANT)
    joins = []
    for contour in glyph.contours:
        pts = contour.points
        for i, point in enumerate(pts):
            if point.type and 180 < point.x < 410 and 925 < point.y < 945:
                prev, nxt = pts[i - 1], pts[(i + 1) % len(pts)]
                a = math.atan2(point.y - prev.y, point.x - prev.x)
                b = math.atan2(nxt.y - point.y, nxt.x - point.x)
                turn = abs(math.degrees((b - a + math.pi) % (2 * math.pi) - math.pi))
                joins.append((point.smooth, turn))
    # One tangent-continuous join on each side, without the old short
    # reversing curves that produced the two little nodges.
    assert len(joins) == 2 and all(smooth and turn < 1.5 for smooth, turn in joins), joins


@pytest.mark.parametrize("name", ["uni0253.sc", "uni0257.sc"])
def test_bold_hook_stem_brackets_do_not_double_back(name):
    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")
    glyph = copy.deepcopy(font[name])
    shear(glyph, -SLANT)
    pts = glyph.contours[0].points
    i = next(i for i, p in enumerate(pts)
             if p.type == "line" and p.y == 69 and pts[i - 1].type == "line"
             and pts[i - 1].y == 69)
    end = next(p for p in pts[i + 1:] if p.type and 90 < p.y < 120)
    # The left foot approaches the stem from its outside, not from
    # inside the stroke, which previously forced a reversing curve.
    assert pts[i].x < end.x - 10 and pts[i].smooth and end.smooth
    i = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 939)
    j = next(j for j in range(i + 1, len(pts)) if pts[j].type and pts[j].y == 1022)
    assert all(p.x <= pts[i].x + 1.5 for p in pts[i + 1:j + 1])
    for contour in glyph.contours[1:]:
        pts = contour.points
        if 95 <= pts[0].y <= 110:
            end = next(p for p in pts[1:] if p.type and p.y == 69)
            assert end.x > pts[0].x + 10 and pts[0].smooth and end.smooth
        if max(p.y for p in pts) == 962:
            i = next(i for i, p in enumerate(pts)
                     if p.type == "line" and p.y == 962 and p.x < 600)
            assert pts[i + 1].x < pts[i].x - 5
