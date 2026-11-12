"""scripts/sc_clearance.py: the Bold Italic's ы.sc and psi.sc keep their parts apart."""

import math
import sys

import ufoLib2
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from derived import Outline  # noqa: E402

LEAST = 40  # units of white, upright (the pass sets 45; rounding and curves take a few)


def rows(font, name, ys):
    slope = math.tan(math.radians(-font.info.italicAngle))
    out = Outline(font, name, (1, 0, -slope, 1, 0, 0))
    return [out.spans(y + 0.37) for y in ys]


def test_yeru_small_cap_parts_apart():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    for spans in rows(font, "uni044B.sc", range(120, 900, 20)):
        assert len(spans) >= 2
        assert spans[-1][0] - spans[-2][1] >= LEAST  # the stick from the bowl


def test_psi_small_cap_serif_clear_of_its_arms():
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    glyph = font["psi.sc"]
    assert len(glyph.contours) == 1  # no white closed between stem and arm
    top = max(p.y for c in glyph.contours for p in c.points if p.type == "line")
    for spans in rows(font, "psi.sc", range(int(top) - 60, int(top) - 5, 6)):
        serif = max(spans, key=lambda s: s[1] - s[0])
        k = spans.index(serif)
        assert 0 < k < len(spans) - 1
        assert serif[0] - spans[k - 1][1] >= LEAST and spans[k + 1][0] - serif[1] >= LEAST
