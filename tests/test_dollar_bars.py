"""Dollar's two through-strokes remain straight across both bowls."""

import math
from copy import deepcopy

import pytest
import ufoLib2
from conftest import DATA, ROOT
from dollar_bars import finish
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint


def edge_groups(glyph):
    """Measure exposed segments against the four bottom terminal corners."""
    slope = math.tan(math.radians(15))
    bottom = min(p.y for c in glyph.contours for p in c.points)
    origins = sorted(p.x for c in glyph.contours for p in c.points if p.y == bottom)
    assert len(origins) == 4
    groups = [[] for _ in origins]
    for contour in glyph.contours:
        for i, p in enumerate(contour.points):
            a = contour.points[i - 1]
            if p.type != "line" or not a.type or abs(p.y - a.y) < 120:
                continue
            intercepts = [q.x - slope * (q.y - bottom) for q in (a, p)]
            k = min(range(4), key=lambda k: abs(origins[k] - sum(intercepts) / 2))
            groups[k].append((a, p))
            assert all(abs(x - origins[k]) <= 0.5 for x in intercepts)
    assert [len(g) for g in groups] == [4, 4, 4, 4]
    assert origins[1] - origins[0] == origins[3] - origins[2] == 86
    assert origins[2] - origins[1] == 95
    return groups


def test_dollar_bars_repair():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    expected = deepcopy(font["dollar"])
    glyph = font["dollar"]
    glyph.clearContours()
    readGlyphFromString((DATA / "dollar-bars-before.glif").read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())
    before = deepcopy(glyph)
    with pytest.raises(AssertionError):
        edge_groups(before)  # The actual previous drawing fails the measurement.
    finish(font)
    edge_groups(glyph)
    assert glyph == expected
    assert glyph.width == before.width == 1290
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    assert [[p.y for p in c.points] for c in glyph.contours] == [
        [p.y for p in c.points] for c in before.contours]
    # Both ball terminals and their curved entrances remain identical.
    for lo, hi in ((0, 17), (40, 58)):
        assert glyph.contours[0].points[lo:hi] == before.contours[0].points[lo:hi]
    assert not lint(font, ["dollar"])
    finish(font)
    assert glyph == expected


def test_dollar_bars_other_styles_unchanged():
    for style in ("Regular", "Bold", "Italic"):
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        before = deepcopy(font["dollar"])
        finish(font)
        assert font["dollar"] == before
