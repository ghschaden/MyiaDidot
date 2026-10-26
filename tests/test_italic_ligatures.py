"""New italic ligatures follow same-style bases and existing language policy."""
from copy import deepcopy

import pytest
from fontTools.pens.recordingPen import RecordingPen
from glyph_lint import lint_glyph
from italic_ligatures import F_LIGATURES, LONGS, NAMES, make
from quality.checks import construction


def outline(glyph):
    pen = RecordingPen()
    glyph.draw(pen)
    return pen.value


def test_italic_ligatures_are_reproducible_and_clean(ufo):
    if not ufo.info.italicAngle:
        pytest.skip("italic construction")
    trial = deepcopy(ufo)
    assert set(make(trial)) == set(NAMES)
    for name in NAMES:
        glyph = ufo[name]
        assert outline(trial[name]) == outline(glyph), name
        assert trial[name].width == glyph.width > 0, name
        assert trial[name].anchors == glyph.anchors, name
        assert not construction(glyph), (name, construction(glyph))
        assert not lint_glyph(ufo, glyph), (name, lint_glyph(ufo, glyph))
        assert len(glyph.anchors) == len(name.split("_")) - 1, name
    for name in set(ufo.keys()) - set(NAMES):
        assert trial[name] == ufo[name], name
    make(trial)
    for name in NAMES:
        assert trial[name] == ufo[name], name


def test_ligatures_follow_their_final_base(ufo):
    if not ufo.info.italicAngle:
        pytest.skip("italic construction")
    trial = deepcopy(ufo)
    for contour in trial["b"].contours:
        for point in contour.points:
            if point.x > 600 and point.y < 800:
                point.x += 20
    make(trial)
    for name in ("f_b", "f_f_b", "longs_b"):
        assert outline(trial[name]) != outline(ufo[name]), name
    for name in set(NAMES) - {"f_b", "f_f_b", "longs_b"}:
        assert trial[name] == ufo[name], name


def test_new_ligature_feature_and_language_policy(shaper):
    def names(text, features=None, language="en"):
        return [g[0] for g in shaper.shape(text, features, language=language)]

    for name in F_LIGATURES:
        text = name.replace("_", "")
        assert names(text) == [name], text
        assert name not in names(text, {"liga": False}), text
        assert name not in names(text, language="de"), text
    for name, _ in LONGS:
        text = name.replace("longs", "ſ").replace("_", "")
        assert names(text) == [name], text
        assert name not in names(text, {"liga": False}), text
        if text.endswith("i"):
            assert name not in names(text, language="tr"), text
        else:
            assert names(text, language="de") == [name], text
    for text in ("ct", "st"):
        assert names(text) == list(text)
        assert names(text, {"dlig": True}) == ["_".join(text)]
    assert names("ſi", language="tr") == ["longs", "i"]
    assert names("fi", language="tr") == ["f", "i"]
    assert names("ffi") == ["ffi"]
    assert names("ffl") == ["ffl"]
