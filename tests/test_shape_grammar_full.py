"""Exact geometry, metadata and failure behaviour of the complete grammar."""

import copy
import json
import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_grammar_full as grammar


@pytest.fixture
def encoded(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    for style in grammar.STYLES:
        font = ufoLib2.Font()
        font.info.familyName = "Grammar test"
        font.info.styleName = style
        font.info.unitsPerEm = 1000
        font.features.text = "feature liga { sub base base by composite; } liga;"
        font.newGlyph(".notdef").width = 500
        glyph = font.newGlyph("base")
        glyph.width = 600
        glyph.unicodes = [97]
        glyph.appendAnchor({"name": "top", "x": 150.125, "y": 700})
        glyph.lib["test.metadata"] = {"value": "preserve me"}
        pen = glyph.getPen()
        for offset in (0, 300):
            pen.moveTo((offset+0.1, 0.2))
            pen.lineTo((offset+100.3, 0.2))
            pen.curveTo((offset+150.4, 50.5), (offset+150.4, 100.6), (offset+100.3, 150.7))
            pen.lineTo((offset+0.1, 150.7))
            pen.closePath()
        glyph.contours[0].identifier = "contour-one"
        glyph.contours[0].points[0].name = "start"
        glyph.contours[0].points[0].identifier = "point-one"
        glyph.contours[0].points[1].smooth = True
        component = font.newGlyph("composite")
        component.width = 1000
        component.getPen().addComponent("base", (-1, 0, .2, 1, 700.5, 20))
        empty = font.newGlyph("space")
        empty.width = 250
        empty.unicodes = [32]
        open_glyph = font.newGlyph("open")
        pen = open_glyph.getPen()
        pen.moveTo((123, 456))
        pen.endPath()
        font.save(sources / f"MyiaDidot-{style}.ufo")
    result, originals = grammar.extract(sources, max_rules=12)
    # Decoding must be independent of source paths and in-memory UFO objects.
    sources.rename(tmp_path / "sources-unavailable")
    return json.loads(json.dumps(result)), originals


def test_full_roundtrip_including_metadata_and_components(encoded, tmp_path):
    data, originals = encoded
    destination = tmp_path / "export"
    destination.mkdir()
    reports, fonts = grammar.validate(data, originals, destination)
    assert all(report["exact_source_match"] for report in reports.values())
    assert all(report["open_contours"] == 1 for report in reports.values())
    assert all(report["glyphs"] == 5 for report in reports.values())
    assert fonts["Regular"]["base"].contours[0].points[0].name == "start"
    assert data["construction"]["fragment_rules"] > 0
    for rule in data["rules"].values():
        assert "join" in rule or rule["primitive"] in ("L", "C")
    for style in data["styles"].values():
        assert not style["font_metadata"]["layers"][0]["glyphs"]


def test_changed_primitive_fails_source_verification(encoded):
    data, _ = encoded
    rule = next(r for r in data["rules"].values() if r.get("primitive") == "C")
    rule["parameters"][0] = "99999"
    with pytest.raises(ValueError, match="font content mismatch"):
        grammar.validate(data)


@pytest.mark.parametrize("rule,match", [
    ({"join": ["bad", "bad"]}, "Cyclic fragment"),
    ({"join": ["absent", "absent"]}, "Missing fragment"),
    ({"primitive": "C", "parameters": ["1", "2"]}, "Invalid primitive"),
    ({"primitive": "L", "parameters": ["NaN", "2"]}, "Non-finite"),
    ({"path": []}, "Invalid rule"),
])
def test_invalid_rule_rejected(rule, match):
    with pytest.raises(ValueError, match=match):
        grammar.Decoder({"format": grammar.FORMAT, "rules": {"bad": rule}})


def test_component_cycle_and_missing_reference_rejected(encoded):
    data, _ = encoded
    recipes = copy.deepcopy(data["styles"]["Regular"]["layers"][0]["glyphs"])
    recipes["base"]["components"] = [{"baseGlyph": "composite"}]
    with pytest.raises(ValueError, match="Cyclic component"):
        grammar.Decoder.validate_components(recipes)
    recipes["base"]["components"] = [{"baseGlyph": "missing"}]
    with pytest.raises(ValueError, match="Missing component"):
        grammar.Decoder.validate_components(recipes)


def test_factor_preserves_nonoverlapping_repeated_pairs():
    rules = {"p": {"primitive": "L", "parameters": ["1", "0"]}}
    sequences = [["p"] * 9, ["p"] * 9]
    grammar.factor(sequences, rules, 20)
    decoder = grammar.Decoder({"format": grammar.FORMAT, "rules": rules})
    assert [sum(len(decoder.expand(name)) for name in seq) for seq in sequences] == [9, 9]


def test_hash_ignores_only_equivalent_numeric_spelling():
    assert grammar.digest({"x": 1}) == grammar.digest({"x": 1.0})
    assert grammar.digest({"x": 1}) != grammar.digest({"x": 1.0000000000001})
