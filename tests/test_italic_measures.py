"""Phase 6's measures (scripts/quality/italic_measures.py) find what they name
on drawn shapes whose values are known, and the gate reads them as
docs/claude/italic.md says."""

import math
import sys

import pathops
import pytest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import italic_measures as im  # noqa: E402


class Drawn:
    """Shapes by character, as bold_measures.Source hands them out."""

    xh, cap, slant = 500, 700, 0.0

    def __init__(self, **shapes):
        self.shapes = shapes

    def has(self, ch):
        return ch in self.shapes

    def path(self, ch):
        p = pathops.Path()
        pen = p.getPen()
        for poly in self.shapes[ch]:
            pen.moveTo(poly[0])
            for pt in poly[1:]:
                pen.lineTo(pt)
            pen.closePath()
        return pathops.simplify(p)

    def zone(self, ch):
        return self.cap if ch.isupper() else self.xh

    def advance(self, ch):
        return 600


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def ellipse(cx, cy, a, b, turn=0.0, n=360):
    """Semi-axes a across and b up, turned clockwise by `turn` degrees."""
    t = math.radians(turn)
    out = []
    for i in range(n):
        u = 2 * math.pi * i / n
        x, y = a * math.cos(u), b * math.sin(u)
        out.append((cx + x * math.cos(t) + y * math.sin(t), cy - x * math.sin(t) + y * math.cos(t)))
    return out


def test_a_stroke_is_measured_across_not_along_the_cut():
    # a bar 20 thick rising at 30 degrees: a column cuts 20 / cos 30 of it
    rise = math.tan(math.radians(30))
    run = 20 / math.cos(math.radians(30))
    src = Drawn(a=[[(0, 0), (400, 400 * rise), (400, 400 * rise + run), (0, run)]])
    c = im.cut(src, "a")
    t, here = im.across(c.col, 200, lambda s: s[0] if s else None)
    assert here[1] - here[0] == pytest.approx(run, abs=0.01)
    assert t == pytest.approx(20, abs=0.05)


def test_stem_a_third_of_the_way_up_not_the_hairline_beside_it():
    # a stem of 80 and a hairline of 20 beside it (an exit hook's tip)
    src = Drawn(n=[box(100, 0, 180, 500), box(300, 0, 320, 250)])
    c = im.cut(src, "n")
    assert im.stem_runs(c) == [pytest.approx((100, 180))]
    assert im.stem(c) == pytest.approx(80)


def test_long_stem_where_it_stands_alone_above_the_x_height_or_below_the_line():
    # d: a bowl's stroke of 90 left, the stem of 70 right, running up to 760;
    # p: the stem of 70 left, running down to -240, the bowl's stroke right
    src = Drawn(d=[box(100, 0, 190, 500), box(300, 0, 370, 760), box(190, 0, 300, 60)],
                p=[box(100, -240, 170, 500), box(280, 0, 370, 500), box(170, 440, 280, 500)])
    for ch, y in (("d", 630), ("p", -120)):
        c = im.cut(src, ch)
        assert im.long_stem(c) == pytest.approx(70)
        assert c.marks[-1][1] == pytest.approx(y)


def test_serif_of_60_by_12_on_a_stem_of_80():
    src = Drawn(I=[box(160, 0, 240, 700), box(100, 0, 300, 12), box(100, 688, 300, 700)])
    f = im.foot(im.cut(src, "I"))
    assert f["L"] == pytest.approx(60) and f["R"] == pytest.approx(60)
    assert f["tip"] == pytest.approx(12) and f["half"] == pytest.approx(12)


def test_foot_at_a_descender_and_on_the_last_stem():
    # q: a bowl's stroke left, the stem right, running to -200 with a foot of 40 | 30
    src = Drawn(q=[box(100, 0, 190, 500), box(300, -200, 380, 500), box(260, -200, 410, -188)])
    f = im.foot(im.cut(src, "q"), -1)
    assert f["L"] == pytest.approx(40) and f["R"] == pytest.approx(30)


def test_ring_thin_places_and_their_angle():
    # a circle of 250 with a counter of 240 by 150 whose long axis is turned
    # 20 degrees clockwise: 10 thick where thinnest, the thin places on that axis
    src = Drawn(o=[ellipse(300, 250, 250, 250), ellipse(300, 250, 150, 240, turn=20)[::-1]])
    r = im.ring(im.cut(src, "o"))
    assert r["top"] == pytest.approx(10, abs=0.5) and r["bottom"] == pytest.approx(10, abs=0.5)
    assert r["stress"] == pytest.approx(20, abs=2)
    upright = Drawn(o=[ellipse(300, 250, 250, 250), ellipse(300, 250, 150, 240)[::-1]])
    assert im.ring(im.cut(upright, "o"))["stress"] == pytest.approx(0, abs=1)


def test_bar_between_two_stems_and_the_thinner_of_two_strokes():
    src = Drawn(H=[box(100, 0, 190, 700), box(400, 0, 490, 700), box(190, 340, 400, 362)],
                A=[box(100, 0, 130, 700), box(300, 0, 400, 700)])
    assert im.bar(im.cut(src, "H")) == pytest.approx(22)
    assert im.thin_stroke(im.cut(src, "A"), 0.65) == pytest.approx(30)


def test_arch_where_thinnest_between_the_stems():
    # the arch 40 thick, 18 where it leaves the first stem
    src = Drawn(n=[box(100, 0, 180, 500), box(400, 0, 480, 460), box(180, 482, 260, 500),
                   box(260, 460, 480, 500), box(60, 0, 220, 10)])
    assert im.arch(im.cut(src, "n")) == pytest.approx(18)


def test_hooks_reach_and_thickness():
    # an entry of 50 by 14 at the top left, an exit of 70 by 16 at the bottom right
    src = Drawn(i=[box(200, 0, 280, 500), box(150, 470, 200, 484), box(280, 20, 350, 36)])
    c = im.cut(src, "i")
    entry, leave = im.hook(c, "entry"), im.hook(c, "exit")
    assert entry["reach"] == pytest.approx(50) and entry["thin"] == pytest.approx(14)
    assert leave["reach"] == pytest.approx(70) and leave["thin"] == pytest.approx(16)


def test_colour_is_ink_over_advance_by_x_height():
    # a box 100 wide over the whole x-height, on an advance of 600
    src = Drawn(a=[box(100, -100, 200, 600)])
    assert im.colour(im.cut(src, "a"), src, "a") == pytest.approx(100 / 600, abs=0.001)


def data(myia, refs, voice=(1.0, 1.0), name="hairline o top / stem"):
    fonts = [("Myia", "myia", myia), ("A", "range", refs[0]), ("B", "range", refs[1]), ("C", "range", refs[2]),
             ("V", "voice", voice[0]), ("W", "voice", voice[1])]
    return {f: {"part": part, "regular": {name: (1.0, None)}, "italic": {name: (v, None)}} for f, part, v in fonts}


@pytest.mark.parametrize("myia, voice, verdict", [
    (1.05, (1.2, 1.2), "inside"),
    (1.12, (1.2, 1.2), "inside"),  # past the range by less than OUTSIDE
    (1.16, (1.2, 1.0), "candidate"),  # one of the second voice beyond Myia
    (1.16, (1.1, 1.0), "another typeface"),  # both on the range's side
    (1.25, (1.3, 1.3), "another typeface"),  # past by FAR, whatever they say
    (0.94, (0.9, 0.9), "candidate"),
    (0.94, (1.0, 0.95), "another typeface"),
])
def test_gate(myia, voice, verdict):
    row, = im.judge(data(myia, (1.0, 1.05, 1.1), voice))
    assert row["verdict"] == verdict


def test_gate_leaves_out_what_the_references_spread_on_and_keeps_the_capitals_contrast():
    row, = im.judge(data(2.0, (0.8, 1.0, 1.2)))
    assert row["verdict"].startswith("shown")
    row, = im.judge(data(1.5, (1.0, 1.05, 1.1), name="capital hairline H bar / stem"))
    assert row["verdict"] == im.KEPT


def test_gate_takes_a_difference_in_its_own_unit_and_a_hook_by_the_italic_alone():
    row, = im.judge(data(9.0, (1.0, 2.0, 3.0), name="stress o degrees"))  # less the regular's 1.0
    assert row["pos"] == pytest.approx(6.0) and row["verdict"] == "another typeface"
    row, = im.judge(data(6.0, (1.0, 2.0, 3.0), name="stress o degrees"))
    assert row["pos"] == pytest.approx(3.0) and row["verdict"] == "inside"
    d = data(1.2, (1.0, 1.05, 1.1), name="hook n exit thin / stem")
    for f in d.values():
        f["regular"] = {}
    row, = im.judge(d)
    assert row["kind"] == "own" and row["pos"] == pytest.approx(1.2 / 1.1 - 1)
