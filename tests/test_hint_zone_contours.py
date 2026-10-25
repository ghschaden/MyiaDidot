"""Alignment zones apply to outer ink boundaries, not counter holes."""
import sys

import pytest
from conftest import ROOT
from fontTools.pens.ttGlyphPen import TTGlyphPen

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from hint_zones import contours


@pytest.mark.parametrize("reverse", [False, True])
def test_counter_is_excluded_but_disconnected_ink_and_indices_are_kept(reverse):
    pen = TTGlyphPen(None)
    # The counter top coincides with an unrelated alignment zone. A second
    # outer piece after it checks that filtering preserves glyf point indices.
    rings = [
        [(0, 0), (0, 1400), (1000, 1400), (1000, 0)],
        [(200, 300), (800, 300), (800, 1077), (200, 1077)],
        [(1100, 0), (1100, 884), (1300, 884), (1300, 0)],
    ]
    for points in rings:
        if reverse:
            points = list(reversed(points))
        pen.moveTo(points[0])
        for point in points[1:]:
            pen.lineTo(point)
        pen.closePath()
    glyf = {"test": pen.glyph()}
    found = contours(glyf, "test")
    assert [c[0] for c in found] == [1400, 884]
    assert [c[2] for c in found] == [0, 0]
    assert [c[4] for c in found] == [list(range(4)), list(range(8, 12))]
