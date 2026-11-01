"""The derived-glyph checks (scripts/quality/derived.py) catch what they are
for: a letter made from the wrong source. The Italic's ɗ was once the
Regular's hooked d sloped and narrowed; put back in that state, the checks
must find it. (Their findings on the sources themselves are held by
test_quality.py, with the other quality kinds.)"""

import copy
import json
import math
import sys

import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from derived import derived, report


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


def test_attachment_style_uses_both_inputs_and_still_finds_roman_ink():
    italic = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    regular = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    found, metrics = derived(italic, regular=regular, only={"uni026E"})
    assert not found
    assert metrics["uni026E"]["iou_recipe"] > 0.9
    # The second input must not turn the style check into an exemption:
    # replacing the joined letter with the sloped roman is still wrong.
    glyph = italic["uni026E"]
    glyph.clearContours()
    glyph.clearComponents()
    rec = DecomposingRecordingPen(regular)
    regular[glyph.name].draw(rec)
    slant = math.tan(math.radians(-italic.info.italicAngle))
    rec.replay(TransformPen(glyph.getPen(), (1, 0, slant, 1, 0, 0)))
    found = derived(italic, regular=regular, only={glyph.name})[0]
    assert any(kind == "style" for _, kind, _, _ in found)


def test_report_is_plain_repeatable_and_tells_a_changed_glyph():
    path = SOURCES / "MyiaDidot-BoldItalic.ufo"
    font = ufoLib2.Font.open(path)
    only = {"uni019C", "uni0289"}
    made = report(font, path, *derived(font, path, only))
    assert json.loads(json.dumps(made)) == made
    assert made == report(font, path, *derived(font, path, only))
    assert (made["glyphs"]["uni019C"]["op"], made["glyphs"]["uni019C"]["source"]) == ("twin", "U")
    assert (made["glyphs"]["uni0289"]["op"], made["glyphs"]["uni0289"]["dx"]) == ("bar", 0)
    font["U"].width += 1
    moved = report(font, path, *derived(font, path, only))
    assert moved["glyphs"]["uni019C"]["source_sha256"] != made["glyphs"]["uni019C"]["source_sha256"]
    assert moved["glyphs"]["uni019C"]["glyph_sha256"] == made["glyphs"]["uni019C"]["glyph_sha256"]
