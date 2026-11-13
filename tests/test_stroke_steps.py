"""The Bold Italic's strokes run into their lines without a sideways step."""

import math
import sys

import numpy as np
import pytest
import ufoLib2
from conftest import DATA, ROOT, SOURCES
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import readGlyphFromString

sys.path.insert(0, str(ROOT / "scripts"))
from fair_arcs import segments
from stroke_bold import bends, compared, steps

# where a curve split short before its line met it in a step (Strokes.blend),
# ƴ, made of y, and Ɯ, U twinned (data_bold_italic.ITALIC_BOLD_REBUILD)
BLENDED = ["y", "uni028E", "sevenoldstyle", "uni02B2", "uni040F", "uni043C", "uni01B4", "uni019C"]
CONTROLS = ["n", "h", "v", "w", "o"]
# u's inner stem ran into its bowl in a knee (18 degrees finished: the
# stroked curve's fit took up the line's heavier weight, a knee blended,
# KNEE_TURN), and и ш щ џ ų with it, ц too once its tail was left as drawn;
# ƴ's curl met its ball in a dent (21: the ball a few units wider than the
# curl's end; a cap touching both its edges now, derive.curl "end"), and
# ʋ's (15); 2026-10-29: each
# before the fix (tests/data/*-before-*), the turn it is found at, and the
# fixed letters checked at that turn too
KNEED = ["u", "uni0438", "uni0446", "uni0448", "uni0449", "uni045F", "uogonek"]
FIXED = {**{name: ("knee-before", 15) for name in KNEED}, "uni01B4": ("dent-before", 15), "uni028B": ("dent-before", 15)}


def upright(glyph, angle):
    slant = math.tan(math.radians(-angle))
    rec = RecordingPen()
    glyph.draw(TransformPen(rec, (1, 0, -slant, 1, 0, 0)))
    return segments(rec.value)


def places(found):
    return [(x, y) for _, x, y, *_ in found]


@pytest.fixture(scope="module")
def bold_italic():
    return ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")


def drawn_before(font, name, before="steps-before"):
    """name as stroke_bold drew it before Strokes.blend (dc373511; or
    before another fix, FIXED), deslanted"""
    glyph = ufoLib2.objects.Glyph(name)
    readGlyphFromString((DATA / f"{before}-BoldItalic-{name}.glif").read_text(),
                        glyphObject=glyph, pointPen=glyph.getPointPen())
    return upright(glyph, font.info.italicAngle)


@pytest.mark.parametrize("name", BLENDED + CONTROLS)
def test_no_sideways_step(bold_italic, name):
    assert steps(upright(bold_italic[name], bold_italic.info.italicAngle)) == []


@pytest.mark.parametrize("name", KNEED + ["uni01B4", "uni028B"] + CONTROLS)
def test_no_knee_or_dent(bold_italic, name):
    """nor a smaller step, as u's knee and ƴ's dent were (FIXED)"""
    assert steps(upright(bold_italic[name], bold_italic.info.italicAngle), 15) == []


@pytest.mark.parametrize("name", KNEED)
def test_knee_turns_one_way(bold_italic, name):
    """the knee drawn as the Italic turns (stroke_bold.KNEE_QUARTER): from
    the line to upright and round into the counter, no bend (blended only,
    it went inward first: two bends, 355,223 and 341,170 upright;
    2026-10-29); ш щ's middle stem too"""
    knees = [(345, 195)] + ([(830, 215)] if name in ("uni0448", "uni0449") else [])
    found = bends(upright(bold_italic[name], bold_italic.info.italicAngle))
    assert not [f for f in found if any(math.dist(f[1:3], k) < 100 for k in knees)], found


@pytest.mark.parametrize("name", FIXED)
def test_knee_and_dent_found_and_gone(bold_italic, name):
    before, turn = FIXED[name]
    old = steps(drawn_before(bold_italic, name, before), turn)
    gone, added = compared(old, steps(upright(bold_italic[name], bold_italic.info.italicAngle), turn))
    assert old and gone and not added, (name, old, gone, added)


@pytest.mark.parametrize("name", BLENDED)
def test_old_step_found_and_gone(bold_italic, name):
    """each letter's step before the repair is found, gone now, and no
    other step is new or worse"""
    before = steps(drawn_before(bold_italic, name))
    gone, added = compared(before, steps(upright(bold_italic[name], bold_italic.info.italicAngle)))
    assert gone and not added, (name, before, gone, added)


def split(sg, t):
    """the cubic sg cut at t (de Casteljau)"""
    a, b, c, d = sg
    ab, bc, cd = a + (b - a) * t, b + (c - b) * t, c + (d - c) * t
    abc, bcd = ab + (bc - ab) * t, bc + (cd - bc) * t
    m = abc + (bcd - abc) * t
    return [np.array([a, ab, abc, m]), np.array([m, bcd, cd, d])]


def cut(contour, ts=(0.3, 0.6)):
    """contour with each curve cut in pieces at ts (of what is left)"""
    out = []
    for sg in contour:
        for t in ts if len(sg) == 4 else ():
            first, sg = split(sg, t)
            out.append(first)
        out.append(sg)
    return out


def stem(jog):
    """a stem 100 wide whose right edge, going up, moves jog units aside
    over 20 units at y 300, as a curve between two lines"""
    p = lambda x, y: np.array([x, y], float)  # noqa: E731
    return [[np.array([p(0, 0), p(100, 0)]), np.array([p(100, 0), p(100, 290)]),
             np.array([p(100, 290), p(100, 300), p(100 + jog, 300), p(100 + jog, 310)]),
             np.array([p(100 + jog, 310), p(100 + jog, 700)]), np.array([p(100 + jog, 700), p(0, 700)]),
             np.array([p(0, 700), p(0, 0)])]]


def bowl():
    """an o-like round, four quarter curves outside, four inside"""
    k = 0.5523
    def ring(r, sign):
        q = [(r, 0), (0, r), (-r, 0), (0, -r)][::sign]
        segs = []
        for (x0, y0), (x1, y1) in zip(q, q[1:] + q[:1]):
            segs.append(np.array([(x0, y0), (x0 - k * y0 * sign, y0 + k * x0 * sign),
                                  (x1 + k * y1 * sign, y1 - k * x1 * sign), (x1, y1)], float))
        return segs
    return [ring(300, 1), ring(200, -1)]


def test_steps_found_on_constructed_geometry():
    assert places(steps(stem(8))) == [(104, 300)]
    assert steps(stem(0)) == []
    assert steps(bowl()) == []


@pytest.mark.parametrize("contours", [stem(8), stem(0), bowl()], ids=["stepped", "straight", "round"])
def test_steps_the_same_however_cut(contours):
    """cutting the same curves in pieces, or starting the contour
    elsewhere, finds the same steps"""
    found = steps(contours)
    for other in ([cut(c) for c in contours], [c[2:] + c[:2] for c in contours]):
        again = steps(other)
        assert places(again) == places(found)
        assert [round(f[3]) for f in again] == [round(f[3]) for f in found]


def test_steps_the_same_however_cut_in_a_letter(bold_italic):
    before = drawn_before(bold_italic, "y")
    assert places(steps([cut(c) for c in before])) == places(steps(before))


def test_compared_finding_by_finding():
    """a candidate taking one fault away and adding another is not better;
    a finding moved a little by a refit is the same one"""
    old = [("wobble", 100, 200, 9.0), ("kink", 500, 40, 3.0)]
    assert compared(old, [("wobble", 104, 197, 9.0)]) == ([("kink", 500, 40, 3.0)], [])
    assert compared(old, [("wobble", 104, 197, 9.0), ("kink", 300, 600, 2.0)])[1] == [("kink", 300, 600, 2.0)]
    assert compared(old, [("wobble", 100, 200, 12.0), ("kink", 500, 40, 3.0)])[1] == [("wobble", 100, 200, 12.0)]
    assert compared(old, [("kink", 100, 200, 9.0)]) == (old, [("kink", 100, 200, 9.0)])
    # two new ones at one old: only the nearer is it, the other is new
    assert compared(old[:1], [("wobble", 101, 200, 9.0), ("wobble", 110, 200, 9.0)])[1] == [("wobble", 110, 200, 9.0)]


def test_tidy_ends_on_a_near_zero_line_at_the_start():
    """a contour whose first point is the copy a unit from the last one:
    the copy goes (it was kept, and tidy looped for ever on the Italic ɾ)"""
    from stroke_bold import TINY, tidy

    g = ufoLib2.objects.Glyph("t")
    pen = g.getPen()
    pen.moveTo((0, 0))
    pen.lineTo((100, 0))
    pen.lineTo((100, 100))
    pen.lineTo((0, TINY / 2))
    pen.closePath()
    tidy(g)
    assert [(p.x, p.y) for p in g.contours[0].points if p.type] in (
        [(100, 0), (100, 100), (0, TINY / 2)], [(0, 0), (100, 0), (100, 100)])
