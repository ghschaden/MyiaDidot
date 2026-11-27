"""Every glyph winds as the Regular does: outsides clockwise, counters
counter-clockwise (scripts/winding.py). A glyph wound both ways loses ink
where one of its pieces is merged across another (ʢ's bar, 2026-11-24);
the generators turn what they make the other way (winding.orient, in
style_write.write and smallcaps)."""

import ufoLib2
from ufoLib2.objects import Glyph
from winding import judge, orient


def ring(g, x0, y0, x1, y1, clockwise):
    pts = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
    if not clockwise:
        pts.reverse()
    pen = g.getPen()
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()


def o(outer_cw, inner_ccw):
    g = Glyph("o")
    ring(g, 0, 0, 500, 500, outer_cw)
    ring(g, 100, 100, 400, 400, not inner_ccw)
    return g


def directions(g):
    return [judge_one(c) for c in g.contours]


def judge_one(contour):
    from winding import _area

    return _area(contour) < 0


def test_rule():
    assert judge(o(True, True)) == "ok"
    assert judge(o(False, False)) == "turn"
    assert judge(o(True, False)) == "mixed"


def test_orient_turns_and_keeps_points():
    font = ufoLib2.Font()
    font.layers.defaultLayer.insertGlyph(o(False, False), "o")
    font.layers.defaultLayer.insertGlyph(o(True, False), "q")
    before = {n: sorted((p.x, p.y) for c in font[n].contours for p in c.points) for n in "oq"}
    turned, left = orient(font)
    assert sorted(turned) == ["o", "q"] and not left
    for n in "oq":
        assert directions(font[n]) == [True, False]
        assert sorted((p.x, p.y) for c in font[n].contours for p in c.points) == before[n]


def test_stray_point_and_overlaps():
    g = o(True, True)
    pp = g.getPointPen()
    pp.beginPath()
    pp.addPoint((10, 10), "line")
    pp.endPath()
    assert judge(g) == "ok"
    # two outsides overlapping, wound both ways: not decided, left alone
    h = Glyph("x")
    ring(h, 0, 0, 300, 300, True)
    ring(h, 200, 0, 500, 300, False)
    assert judge(h) == "undecided"


def test_style(ufo, ufo_path):
    wrong = {g.name: v for g in ufo if (v := judge(g)) != "ok"}
    assert not wrong, f"{ufo_path.name}: wound against the Regular: {wrong}"
