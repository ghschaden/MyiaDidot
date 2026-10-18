"""The derived-glyph checks (scripts/quality/derived.py) catch what they are
for: a letter made from the wrong source. The Italic's ɗ was once the
Regular's hooked d sloped and narrowed; put back in that state, the checks
must find it. (Their findings on the sources themselves are held by
test_quality.py, with the other quality kinds.)"""

import copy
import math
import sys

import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from derived import derived


def test_roman_in_the_italic_is_found():
    italic = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    regular = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    slant = math.tan(math.radians(-italic.info.italicAngle))
    g = italic["uni0257"]
    lib = copy.deepcopy(g.lib)
    g.clear()
    rec = DecomposingRecordingPen(regular)
    regular["uni0257"].draw(rec)
    rec.replay(TransformPen(g.getPen(), (0.9, 0, slant * 0.9, 1, 0, 0)))
    g.width = regular["uni0257"].width * 0.9
    g.lib.update(lib)
    found = {(name, kind) for name, kind, _, _ in derived(italic, regular=regular, only={"uni0257"})[0]}
    assert ("uni0257", "base") in found
    assert ("uni0257", "advance") in found


def test_the_italic_d_hook_passes():
    italic = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    regular = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    assert not derived(italic, regular=regular, only={"uni0257"})[0]
