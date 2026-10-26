"""Focused proof generation must handle source glyphs without mutating them."""

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import ufoLib2
from build_support import content_hash
from ufoLib2.objects import Anchor, Component

SCRIPT = Path(__file__).resolve().parents[1] / "skills/glyph-review/scripts/proof.py"
spec = importlib.util.spec_from_file_location("glyph_review_proof", SCRIPT)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def source(path, *, composite=True, upm=1000):
    font = ufoLib2.Font()
    font.info.unitsPerEm, font.info.xHeight, font.info.capHeight = upm, 500, 700
    font.info.styleName = "Review fixture"
    glyph = font.newGlyph("A")
    glyph.width = 600
    pen = glyph.getPen()
    pen.moveTo((-80, -350)); pen.lineTo((300, 1200)); pen.lineTo((480, -350)); pen.closePath()
    glyph.anchors.append(Anchor(name="top&test", x=250, y=1300))
    font.newGlyph("space").width = 300
    if composite:
        font.newGlyph("A.component").components.append(Component("A", (1, 0, 0, 1, 10, 30)))
    font.save(path)


def test_source_proof_handles_components_empty_ink_and_missing_baseline(tmp_path):
    current, before = tmp_path / "current.ufo", tmp_path / "before.ufo"
    source(current)
    source(before, composite=False, upm=2000)
    hashes = content_hash(current), content_hash(before)
    output = tmp_path / "proof.svg"
    proof.render(current, ["A", "space", "A.component"], output, before=before, anchors=True)
    svg = ET.parse(output).getroot()
    assert float(svg.attrib["height"]) > 3 * 200
    labels = " ".join(svg.itertext())
    assert "Not present in this source" in labels
    assert "top&test" in labels
    assert "advance 300" in labels
    transforms = [p.attrib.get("transform", "") for p in svg.findall("{*}path")]
    assert any("scale(0.112000,-0.112000)" in value for value in transforms)
    assert any("scale(0.056000,-0.056000)" in value for value in transforms)
    assert (content_hash(current), content_hash(before)) == hashes


def test_missing_current_glyph_does_not_publish_proof(tmp_path):
    current = tmp_path / "current.ufo"
    source(current)
    output = tmp_path / "proof.svg"
    with pytest.raises(ValueError, match="missing from current"):
        proof.render(current, ["does-not-exist"], output)
    assert not output.exists()


def test_proof_cannot_overwrite_source_files(tmp_path):
    current = tmp_path / "current.ufo"
    source(current)
    original = content_hash(current)
    with pytest.raises(ValueError, match="outside source"):
        proof.render(current, ["A"], current / "fontinfo.plist")
    assert content_hash(current) == original


def test_source_change_during_rendering_does_not_publish(tmp_path, monkeypatch):
    current = tmp_path / "current.ufo"
    source(current)
    draw = proof.outline

    def concurrent_change(*args):
        (current / "concurrent-edit.txt").write_text("another editor changed this input")
        return draw(*args)

    monkeypatch.setattr(proof, "outline", concurrent_change)
    output = tmp_path / "proof.svg"
    with pytest.raises(ValueError, match="source changed"):
        proof.render(current, ["A"], output)
    assert not output.exists()
