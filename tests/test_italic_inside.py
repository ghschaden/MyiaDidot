"""italic_inside: an open round's inside redrawn from the Italic's run."""

import copy

import italic_inside
import pathops
import ufoLib2
from conftest import ROOT
from fontTools.pens.recordingPen import DecomposingRecordingPen
from make_bold import SLANT
from make_italic import shear


def _path(font, glyph):
    path = pathops.Path()
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    rec.replay(path.getPen())
    return path


def test_split_extremes_and_rejoin_keep_the_outline():
    """splitting at the upright extremes and joining the untouched curves
    again gives back the outline as it was"""
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = copy.deepcopy(font["C"])
    shear(glyph, -SLANT)
    before = [(p.x, p.y, p.type) for p in glyph.contours[0].points]
    was = italic_inside.split_extremes(glyph.contours[0])
    assert was and len(glyph.contours[0].points) > len(before)
    back = italic_inside._rejoin(glyph.contours[0].points, was)
    assert [(p.x, p.y, p.type) for p in back] == before


def test_the_italic_run_onto_itself_changes_nothing_but_nodes():
    """the Italic's run mapped onto its own: the same ink (each piece's map
    the identity; rounded to units, and its nodes turning less than a
    corner made smooth: under 1 % of the ink), the anchors found in the same order
    on both"""
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    for name, (start, end) in italic_inside.RUNS.items():
        wide, bold = copy.deepcopy(font[name]), copy.deepcopy(font[name])
        shear(wide, -SLANT)
        shear(bold, -SLANT)
        before = _path(font, bold)
        italic_inside.replace(wide, bold, start, end)
        after = _path(font, bold)
        for a, b in ((before, after), (after, before)):
            assert pathops.op(a, b, pathops.PathOp.DIFFERENCE).area < 0.01 * abs(before.area), name


def test_the_bold_italic_runs_are_found():
    """in the Bold Italic as saved each run's anchors are found in the same
    order as the Italic's (a mismatch leaves the inside as stroked; make_bold
    prints it)"""
    italic = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    bold = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    for name, (start, end) in italic_inside.RUNS.items():
        found = []
        for font in (italic, bold):
            glyph = copy.deepcopy(font[name])
            shear(glyph, -SLANT)
            italic_inside.split_extremes(glyph.contours[0])
            keys, step = italic_inside.anchors(glyph.contours[0], start, end)
            found.append((len(keys), step))
        assert found[0] == found[1], name
