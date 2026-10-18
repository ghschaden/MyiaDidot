"""The stroke-weight check (scripts/quality/strokes.py) finds what it is for:
a glyph darker than the text around it. The Regular's old-style 0 stood 20
units heavier than o until lighten_figures.py; made so again, the check must
find it, and must leave the references themselves alone. (Its findings on
the sources are held by test_quality.py, with the other quality kinds.)"""

import sys

import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from strokes import strokes


def test_a_heavier_figure_is_found():
    from make_italic import weight_thick

    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    g = font["zerooldstyle"]
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    g.clearContours()
    weight_thick(rec, 30).draw(g.getPen())
    found = {name: detail for name, _, _, detail in strokes(font, {"zerooldstyle"})[0]}
    assert "darker" in found.get("zerooldstyle", "")


def test_the_references_pass():
    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    assert not strokes(font, {"n", "o", "H", "O", "zerooldstyle", "oneoldstyle"})[0]
