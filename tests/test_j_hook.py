"""The Bold Italic j-hook retains its own ɟ descender and lower stem."""

import sys

import pathops
import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(ROOT / "scripts"))
from derive import rect_path, to_path
from make_bold import WHOLE_KEY
from make_italic import ITALIC_SIDEBEARINGS


def test_bold_italic_j_hook_keeps_its_base_below_the_bar():
    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")
    assert "uni0284" not in font.lib[WHOLE_KEY]
    # Match the recipe's inherited left-sidebearing adjustment. Compare the
    # complete lower body, including the curled descender, independently
    # of the quality check's sampled spans. Fairing and integer rounding
    # may move its edges slightly; whole emboldening differs by about 5%.
    dx = ITALIC_SIDEBEARINGS["uni0284"][0]
    base = pathops.Path()
    to_path(font, font["uni025F"]).draw(TransformPen(base.getPen(), (1, 0, 0, 1, dx, 0)))
    clip = rect_path(-10000, -10000, 10000, 400)
    base = pathops.op(base, clip, pathops.PathOp.INTERSECTION)
    body = pathops.op(to_path(font, font["uni0284"]), clip, pathops.PathOp.INTERSECTION)
    def area(path):
        pen = AreaPen(None)
        path.draw(pen)
        return abs(pen.value)

    # Union minus intersection measures symmetric difference without the
    # Skia XOR winding fault on these oppositely wound source outlines.
    union = pathops.op(base, body, pathops.PathOp.UNION)
    overlap = pathops.op(base, body, pathops.PathOp.INTERSECTION)
    assert area(union) - area(overlap) < area(base) * 0.015
