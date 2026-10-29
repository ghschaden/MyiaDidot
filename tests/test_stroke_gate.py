"""What the Bold Italic's stroke repairs (Strokes.blend) must keep.

embolden_by_strokes takes a blended candidate only if it keeps the outline
away from the blend, its contours, bounds, the strokes' widths and the
white between them (stroke_bold.guarded), and its bends (bends, each
matched to its own). Checked here on constructed outlines; then the
finished letters against what they were before the repair (dc373511),
their changes declared.
"""

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
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from checks import construction, reversals
from fair_arcs import segments
from stroke_bold import bends, compared, dbez, ddbez, guarded, pieces

BLENDED = ["y", "uni028E", "sevenoldstyle", "uni02B2", "uni040F", "uni043C", "uni01B4", "uni019C"]
# what the repair changed in the finished letters, reviewed and accepted
# by the person (10ddbcdc): y's DotBelow 5 units right; Ɯ, U twinned, 36
# narrower, a 1.9 degree joint under its middle serif
WIDTHS = {"uni019C": (2476, 2440)}
ANCHORS = {"y": {"DotBelow": (5, 0)}}
FINDINGS = {"uni019C": [("kink", 1227, 1355)]}


def p(x, y):
    return np.array([x, y], float)


def stem(right=((100, 250), (100, 283), (100, 317), (100, 350)), left=0):
    """a stem 100 wide, 600 high, its right edge a curve from y 250 to 350"""
    a, b, c, d = (p(*q) for q in right)
    return [[np.array([p(left, 0), p(100, 0)]), np.array([p(100, 0), a]), np.array([a, b, c, d]),
             np.array([d, p(100, 600)]), np.array([p(100, 600), p(left, 600)]), np.array([p(left, 600), p(left, 0)])]]


REGION, R = [(100, 300)], 60


def test_guarded_keeps_an_unchanged_candidate():
    assert guarded(stem(), stem(), REGION, R) == []


def test_guarded_refuses_a_pinch():
    pinched = stem(((100, 250), (80, 283), (80, 317), (100, 350)))
    assert any(f.startswith("pinched") for f in guarded(stem(), pinched, REGION, R))


def test_guarded_refuses_a_move_away_from_the_blend():
    found = guarded(stem(), stem(left=-3), REGION, R)
    assert any(f.startswith("moved 3.0") for f in found), found


def test_guarded_refuses_a_crossing_and_another_contour():
    crossed = [[np.array([p(0, 0), p(100, 600)]), np.array([p(100, 600), p(100, 0)]),
                np.array([p(100, 0), p(0, 600)]), np.array([p(0, 600), p(0, 0)])]]
    assert "a contour crosses itself or another" in guarded(stem(), crossed, REGION, R)
    dot = [np.array([p(300, 0), p(350, 0)]), np.array([p(350, 0), p(350, 50)]),
           np.array([p(350, 50), p(300, 50)]), np.array([p(300, 50), p(300, 0)])]
    assert "contours, their turn or nesting changed" in guarded(stem(), stem() + [dot], REGION, R)


def test_guarded_refuses_what_it_cannot_measure():
    """no section across the strokes where the blend is: unresolved, the
    original kept"""
    assert guarded(stem(), stem(), [(2000, 2000)], R) == ["unresolved: no sections"]


def blob(lobes, start=0, n=16):
    """a closed contour of smooth cubics around r = 300 + 120 cos(lobes θ)
    (Catmull-Rom through n points), its first node the start-th"""
    q = [np.array([(300 + 120 * math.cos(lobes * t)) * math.cos(t), (300 + 120 * math.cos(lobes * t)) * math.sin(t)])
         for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    q = q[start:] + q[:start]
    return [[np.array([q[k], q[k] + (q[(k + 1) % n] - q[k - 1]) / 6,
                       q[(k + 1) % n] - (q[(k + 2) % n] - q[k]) / 6, q[(k + 1) % n]]) for k in range(n)]]


def cut(contour, t=0.4):
    out = []
    for sg in contour:
        a, b, c, d = sg
        ab, bc, cd = a + (b - a) * t, b + (c - b) * t, c + (d - c) * t
        abc, bcd = ab + (bc - ab) * t, bc + (cd - bc) * t
        m = abc + (bcd - abc) * t
        out += [np.array([a, ab, abc, m]), np.array([m, bcd, cd, d])]
    return out


def sampled(contour):
    """the times the curvature of a contour of smooth curves changes sign,
    sampled densely all around (an oracle independent of bends)"""
    ks = []
    for sg in contour:
        t = np.linspace(0, 1, 2001)
        d, dd = dbez(sg, t), ddbez(sg, t)
        ks += list((d[:, 0] * dd[:, 1] - d[:, 1] * dd[:, 0]) / np.linalg.norm(d, axis=1) ** 3)
    signs = [np.sign(k) for k in ks if abs(k) > 1e-4]
    return sum(a != b for a, b in zip(signs, signs[1:] + signs[:1]))


def test_bends_found_exactly_and_around_the_start():
    """one S cubic bends once (at t 0.5); a round never; a peanut (its
    curves through 16 or 32 points, wavy at its waists) as often as its
    curvature changes sign, however its curves are cut and wherever its
    contour starts"""
    s = [np.array([p(0, 0), p(100, 100), p(200, -100), p(300, 0)]), np.array([p(300, 0), p(0, 0)])]
    assert [f[1:3] for f in bends([s])] == [(150, 0)]
    assert bends(blob(0)) == []
    for n in (16, 32):
        expected = sampled(blob(2, 0, n)[0])
        assert expected >= 4
        for start in range(0, n, 5):
            assert len(bends(blob(2, start, n))) == expected
            assert len(bends([cut(blob(2, start, n)[0])])) == expected


def test_bends_matched_by_place():
    """an inflection sliding along a nearly straight stretch is the same
    one (BEND_NEAR); one elsewhere is new"""
    old = [("bend", 798, -270, 0.0)]
    assert compared(old, [("bend", 797, -296, 0.0)], 40)[1] == []
    assert compared(old, [("bend", 797, -296, 0.0), ("bend", 500, 100, 0.0)], 40)[1] == [("bend", 500, 100, 0.0)]


@pytest.mark.parametrize("name", ["n", "h", "v", "w", "o"])
def test_controls_not_blended(name):
    """the repair leaves the letters without a curve split short before
    its line, nor a knee, as they were: the blend does not even start on
    them"""
    import make_bold as mb
    from stroke_bold import embolden_by_strokes

    italic = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    slant = math.tan(math.radians(-italic.info.italicAngle))
    wide = RecordingPen()
    mb.contours_only(italic[name]).replay(TransformPen(TransformPen(wide, (mb.KX, 0, 0, 1, 0, 0)), (1, 0, -slant, 1, 0, 0)))
    log = []
    embolden_by_strokes(wide, mb.ITALIC_AX, mb.AY, mb.ITALIC_THIN, mb.ITALIC_THICK, mb.ITALIC_HAIR, slant, log=log)
    assert log == []


@pytest.fixture(scope="module")
def bold_italic():
    return ufoLib2.Font.open(SOURCES / "MyiaDidot-BoldItalic.ufo")


def before(name):
    glyph = ufoLib2.objects.Glyph(name)
    readGlyphFromString((DATA / f"steps-before-BoldItalic-{name}.glif").read_text(),
                        glyphObject=glyph, pointPen=glyph.getPointPen())
    return glyph


def found(glyph):
    return ([(k, *(map(int, w.split(",")) if w else (0, 0)), float(d.split()[0])) for k, w, d in construction(glyph)]
            + [("wobble", x, y, d) for x, y, d in reversals(glyph)])


@pytest.mark.parametrize("name", BLENDED)
def test_finished_letter_keeps_what_it_was(bold_italic, name):
    """the repaired letter as finished (slanted, rounded, spaced): its
    advance, anchors, side bearings (within a unit), contours and quality
    findings as before the repair, but for the changes declared"""
    old, new = before(name), bold_italic[name]
    assert (old.width, new.width) == WIDTHS.get(name, (old.width, old.width))
    moved = ANCHORS.get(name, {})
    was = {a.name: (a.x + moved.get(a.name, (0, 0))[0], a.y + moved.get(a.name, (0, 0))[1]) for a in old.anchors}
    assert was == {a.name: (a.x, a.y) for a in new.anchors}
    bo, bn = old.getBounds(), new.getBounds()
    assert abs(bo.xMin - bn.xMin) <= 1 and abs((old.width - bo.xMax) - (new.width - bn.xMax)) <= 1
    assert (bo.yMin, bo.yMax) == pytest.approx((bn.yMin, bn.yMax), abs=1)
    rec = RecordingPen()
    new.draw(rec)
    assert len(new.contours) == len(old.contours) == len(pieces(segments(rec.value)))
    added = [f[:3] for f in compared(found(old), found(new))[1]]
    assert added == FINDINGS.get(name, []), added
