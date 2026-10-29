"""The Bold Italic's strokes run into their lines without a sideways step."""

import math
import sys

import pytest
import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(ROOT / "scripts"))
from fair_arcs import segments
from stroke_bold import steps

# where a curve split short before its line met it in a step (Strokes.blend),
# ƴ, made of y, and Ɯ, U twinned (make_bold.ITALIC_BOLD_REBUILD)
BLENDED = ["y", "uni028E", "sevenoldstyle", "uni02B2", "uni040F", "uni043C", "uni01B4", "uni019C"]


@pytest.fixture(scope="module")
def bold_italic():
    return ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")


@pytest.mark.parametrize("name", BLENDED)
def test_no_sideways_step(bold_italic, name):
    slant = math.tan(math.radians(-bold_italic.info.italicAngle))
    rec = RecordingPen()
    bold_italic[name].draw(TransformPen(rec, (1, 0, -slant, 1, 0, 0)))
    assert steps(segments(rec.value)) == 0, name
