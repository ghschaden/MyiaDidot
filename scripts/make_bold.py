"""Derive the Bold master from the Regular (and the Bold Italic from the Italic).

    python scripts/make_bold.py [REGULAR.ufo] [BOLD.ufo]
    python scripts/make_bold.py sources/MyiaDidot-Italic.ufo sources/MyiaDidot-BoldItalic.ufo

A Didone bold is mostly the regular with heavier stems: the hairlines stay
nearly as fine, so the contrast grows. Every outline of a letter, figure or
sign is scaled across by KX (so the counters do not close up), its thick
strokes thickened by AX across in whatever direction they run and every edge
by AY (derive.embolden_by_weight: an edge moves by the weight of the stroke
it is on, so the upright hairlines stay hairlines and a thick diagonal gains
as much as a stem), and shifted right by AX/2, its advance growing by AX.
Accents and marks are only made a little heavier (MARK_AX, MARK_AY) and stay
where they are. Anchors and the offsets of components move with the
outlines, so composites land where the Regular's would; those the anchor
rules of composites.py can make are then rebuilt from the Bold's anchors,
after its stacking anchors are recomputed from its ink. The letters are then
spaced tighter (BOLD_CUT, scripts/respace.py). Kerning is scaled
by KX, and so are the horizontal values of the hand-set positioning in the
features. Pinholes and crumbs the emboldening leaves are cleaned
(glyph_lint.py). Afterwards: smallcaps.py on the Bold, make normalize.

This regenerates the whole Bold from the Regular: until the Bold has its own
reviewed edits, rerun it after changes to the Regular. From an italic
source (the Bold Italic from the Italic) the same is done in the upright
frame: each outline, anchor and offset deslanted by the source's italic
angle, emboldened, and slanted again (tx), so the stems gain AX across.
"""

import argparse
import functools
import math
import os
import re
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arithmetic  # noqa: F401  (first: one thread, AVX2 at most, before numpy loads)
import case_forms
import italic_inside
import kern_clear
import stroke_cache
from built_from import KEY as BUILT_KEY
from composites import SPECIAL, STACK_GAP_LC, Builder, stack_anchors
from data_bold import (
    ANCHOR_NUDGE,
    AX,
    AY,
    BOLD_BY_WEIGHT,
    BOLD_CUT,
    BOLD_CUT_GREEK,
    BOLD_FIGURE_CUT,
    BOLD_FIT_AS_IS,
    BOLD_KEEP_WHOLE,
    BOLD_KERNING,
    BOLD_REBUILD,
    BOLD_RECIPES,
    BOLD_REFERENCE_BY_WEIGHT,
    BOLD_REFERENCE_ROUNDER,
    BOLD_ROUNDER,
    BOLD_SIDEBEARINGS,
    KX,
    MARK_AX,
    MARK_AY,
    MOVED_EXACT_FOR,
    OVALS,
    SLASHED,
    THICK,  # noqa: F401  (read as make_bold.THICK elsewhere)
    THIN,  # noqa: F401  (read as make_bold.THIN elsewhere)
)
from data_bold_italic import (
    BOLD_ITALIC_CUT,
    BOLD_ITALIC_CUT_GREEK,
    CURL_ARM,  # noqa: F401  (read as make_bold.CURL_ARM elsewhere)
    CURL_CAP,  # noqa: F401  (read as make_bold.CURL_CAP elsewhere)
    CURL_LOW,  # noqa: F401  (read as make_bold.CURL_LOW elsewhere)
    ITALIC_ANCHOR_NUDGE,
    ITALIC_AX,
    ITALIC_BOLD_BY_POINTS,
    ITALIC_BOLD_BY_WEIGHT,
    ITALIC_BOLD_CAP_FREE,
    ITALIC_BOLD_FIT_AS_IS,
    ITALIC_BOLD_HAIR_KEPT,
    ITALIC_BOLD_HEAVIER,
    ITALIC_BOLD_JOINS,
    ITALIC_BOLD_KEEP_WHOLE,
    ITALIC_BOLD_KERNING,
    ITALIC_BOLD_KNEES,
    ITALIC_BOLD_REBUILD,
    ITALIC_BOLD_REBUILD_OPS,
    ITALIC_BOLD_RECIPES,
    ITALIC_BOLD_ROOTS,
    ITALIC_BOLD_ROUNDER,
    ITALIC_BOLD_SMOOTH_COUNTER,
    ITALIC_BOLD_SPLIT,
    ITALIC_BOLD_UNJOINED,
    ITALIC_CAPITAL_ROUNDS,
    ITALIC_FIT_CORRECTIONS,
    ITALIC_HAIR,
    ITALIC_LOOSER,
    ITALIC_OVALS,
    ITALIC_REFERENCE_ROUNDER,
    ITALIC_SIDEBEARINGS,
    ITALIC_THICK,
    ITALIC_THIN,
)
from derive import embolden, embolden_by_weight, embolden_simple, rezone
from glyph_lint import fix
from respace import CUT_KEY, classifier, respace, sidebearings
from space_figures import space as space_figures
from stroke_bold import SLIVER, emboldened, smooth_counter

ROOT = Path(__file__).resolve().parent.parent
JOBS = int(os.environ.get("MYIA_JOBS", "4"))  # processes at most (the project's limit: 4, 2026-11-03)
# a turned, mirrored or flipped letter is its base moved when this share of
# the base's spans is its own (follow_bases); for one letter, less: the
# Italic's ʁ has its bowl's inside redone (bowl_counters), r.sc's stands as
# drafted (the slant makes the two no mirror of each other), 6 to 10 units
# apart over 50 units of height: 0.985 until r.sc moved a unit with R's
# redraw (2026-11-11), 0.978 since, and ʁ was left emboldened whole
MOVED_EXACT = 0.98
# lib: derived letters left emboldened whole, with why (follow_bases);
# tests/test_emboldened.py holds them to a list that only shrinks
WHOLE_KEY = "org.myiadidot.emboldenedWhole"


def lezh_band(font):
    """the Regular's ɮ recipe (derive.RECIPES) on font's l and ʒ: the ʒ
    where its spur leaves the l's stem at its right edge at 600 (as in the
    Regular, 107 units right), the l's foot serif cut right of its stem"""
    import derive
    from derive import BIG

    stem = derive.stems_at(font, "l", 700)[0][1]
    spur = derive.stems_at(font, "uni0292", 600)[0][1]
    dx = round(stem - spur)
    foot = max(p.y for c in font["l"].contours for p in c.points if p.y < 200)
    return ("x", [(stem + 20, -BIG, BIG, foot)],
            [("uni0292", (-BIG, -BIG, BIG, BIG), (0, 0), (1, 1, dx, 0))], dx + font["uni0292"].width)


def fishhook_band(font):
    """the Regular's ɾ recipe (derive.RECIPES) placed on font's r and f:
    f taken from just above its crossbar up, brought down until its top is
    r's, onto r's stem cut there"""
    import derive

    top = lambda n: max(p.y for c in font[n].contours for p in c.points)  # noqa: E731
    dy = top("r") - top("f")
    # above f's crossbar, where its stem still runs straight (920 in the Regular)
    bar = max(p.y for c in font["f"].contours for p in c.points if p.type and p.y <= 1.02 * font.info.xHeight)
    hook = bar + 36
    f0, r0 = derive.stems_at(font, "f", hook - 200)[0][0], derive.stems_at(font, "r", hook + dy - 200)[0][0]
    return ("x", [(-10000, hook + dy, 10000, 10000)],
            [("f", (-10000, hook, 10000, 10000), (0, 0), (1, 1, r0 - f0, dy))])


# the Bold Italic's ff ffi ffl ffj: the second f this much further right
# than the Italic sets it. Both fs have the hook below (2026-11-11); the
# Italic leaves 36 units between the second's ball and the first's tail,
# and at the Bold Italic's weight the two closed on each other (a white
# island between the stems). Chosen by the designer, 2026-11-11, over one
# hook only and over leaving them joined.
ITALIC_BOLD_FF_APART = 100
FF_LIGATURES = ("ff", "ffi", "ffl", "f_f_j")
FF_STRETCH = 0.6  # of the way between the stems the arch is stretched over; the head's join to the second stem moves whole


def part_ff(font, apart=ITALIC_BOLD_FF_APART):
    """font's (the Italic's, before it is emboldened) ff-ligatures with the
    second f and all after it moved apart to the right: above the baseline
    the white between the two stems stretched (lines stay lines, the first
    f's arch a little wider), below it the first f with its hook where it
    is and the second with its hook moved whole. Advance, anchors and
    carets with them."""
    import derive

    for name in FF_LIGATURES:
        g = font[name]
        (_, b1), (a2, _) = derive.stems_at(font, name, 700)[:2]
        # upright by the stem's own slant (the Italic's f leans 15.7 degrees,
        # the font 15.2: over the descender the difference is the white
        # between the hooks)
        slant = (b1 - derive.stems_at(font, name, 200)[0][1]) / 500
        b1, a2 = b1 - slant * 700, a2 - slant * 700
        m = b1 + FF_STRETCH * (a2 - b1)
        low = [p.x - slant * p.y for c in g.contours for p in c.points if p.type and p.y < -20]
        if any(b1 + 1 < x < b1 + 8 for x in low):
            raise ValueError(f"{name}: the two hooks are not apart at the first stem's edge")

        def moved(x, y, b1=b1, m=m, slant=slant):
            u = x - slant * y
            if y < -20:
                return apart if u > b1 + 8 else 0
            return apart * min(1.0, max(0.0, (u - b1) / (m - b1)))

        for c in g.contours:
            for pt in c.points:
                pt.x = round(pt.x + moved(pt.x, pt.y))
        for a in g.anchors:
            a.x = round(a.x + moved(a.x, a.y))
        g.width += apart



# recipes that scale or reshape their one source outline, adding no piece:
# no junction to thicken, emboldened whole as any letter is
RESHAPES = {"enlarge", "stretch", "superior", "lower", "ezh", "esh", "nodot", "upright"}
FIGURE_NAMES = {f"{n}{s}" for n in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
                for s in ("", "oldstyle")} | {"uni2007", "figuredash"}
LINING_FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


def tabular_figures(font):
    """The lining figures tabular again: emboldening widens each by its own
    strokes (Bold 1202-1231, Bold Italic 1199-1240 after the cut, where the
    Regular's and the Italic's share one width), so columns of figures no
    longer lined up. Each takes the mean of their widths, the difference
    split evenly between its sides (its fit as emboldened, moved as a whole);
    the figure space and figure dash take the same width. Returns it."""
    width = round(sum(font[n].width for n in LINING_FIGURES) / len(LINING_FIGURES))
    deltas = {}
    for n in LINING_FIGURES + ("uni2007", "figuredash"):
        d = width - font[n].width
        deltas[n] = (d // 2, d - d // 2)
    sidebearings(font, deltas)
    return width
# by strokes, a letter's side whose ink stands further out than by weight
# gets that white back (letters only: figures, punctuation, signs as fitted) (MYIA_STROKE_OUT_LOG=FILE lists them)
STROKE_OUT_LOG = os.environ.get("MYIA_STROKE_OUT_LOG")
# gains under this are the measure's noise (1-3 units, most at straight sides:
# H's, m's; the finished letters' side bearings are held within a unit)
STROKE_OUT_MIN = 4


def slashed(wide, ring, make, refit, bar):
    """wide (a slashed round) as its round emboldened as the round itself is
    (make, then refit: oval, italic_counter or None) joined to its slash (what it has beyond ring, the
    round's own wide outline: slivers where the two rings differ left out)
    emboldened apart (bar: by weight; by strokes its hairline edge runs on
    along the counter and the union leaves crumbs of curve there)."""
    def path(rec):
        p = pathops.Path()
        (rec.replay if hasattr(rec, "replay") else rec.draw)(p.getPen())
        return p

    def contours(rec):
        out = []
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    rest = RecordingPen()
    pathops.op(path(wide), path(ring), pathops.PathOp.DIFFERENCE).draw(rest)
    # the slash whole, as one straight bar (the hull of its pieces' straight
    # edges): cut at the ring, its ends would be thin wedges along it,
    # emboldened into fins; where the two rings differ the pieces carry
    # slivers of ring along
    pts = set()
    for c in contours(rest):
        start = cur = c[0][1][0]
        for op, ps in c[1:]:
            end = ps[-1] if ps else start
            if op in ("lineTo", "closePath") and math.dist(cur, end) > 50:
                pts |= {cur, end}
            cur = end
    pts = sorted(pts)

    def half(seq):
        h = []
        for p in seq:
            while len(h) > 1 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                  - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]

    hull = half(pts) + half(pts[::-1])
    slash = RecordingPen()
    slash.moveTo(hull[0])
    for p in hull[1:]:
        slash.lineTo(p)
    slash.closePath()
    whole = make(ring)
    if refit:
        whole = refit(ring, whole)
    before, rec = RecordingPen(), RecordingPen()
    (whole.replay if hasattr(whole, "replay") else whole.draw)(before)
    pathops.op(path(whole), path(bar(slash)), pathops.PathOp.UNION).draw(rec)
    # wound as the round is (pathops winds its own way)
    glyph = ufoLib2.objects.Glyph()
    pen = glyph.getPen()
    if (max(map(area, contours(rec)), key=abs) > 0) != (max(map(area, contours(before)), key=abs) > 0):
        pen = ReverseContourPen(pen)
    rec.replay(pen)
    return glyph


def italic_counter(wide, bold):
    """bold (a two-contour round, the Bold Italic's, upright frame) with its
    counter replaced by wide's (the Italic's) mapped onto the stroked
    counter's box, then scaled about its middle to that counter's area: an
    affine image keeps the Italic's curves as smooth as they are (the
    oval's handle tension, matching the area, drove them into cusps here),
    the ink and its weight stay as stroked."""
    def contours(path):
        rec, out = RecordingPen(), []
        (path.replay if hasattr(path, "replay") else path.draw)(rec)
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    def bounds(c):
        pen = BoundsPen(None)
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.bounds

    def moved(c, t):
        a, d, e, f = t
        return [(op, tuple((a * x + e, d * y + f) for x, y in pts)) for op, pts in c]

    old, new = contours(wide), contours(bold)
    if len(old) != 2 or len(new) != 2:
        raise ValueError("italic_counter: two contours each")
    old.sort(key=lambda c: abs(area(c)))
    new.sort(key=lambda c: abs(area(c)))
    (x0, y0, x1, y1), (u0, v0, u1, v1) = bounds(old[0]), bounds(new[0])
    sx, sy = (u1 - u0) / (x1 - x0), (v1 - v0) / (y1 - y0)
    c = moved(old[0], (sx, sy, u0 - x0 * sx, v0 - y0 * sy))
    k = math.sqrt(abs(area(new[0])) / abs(area(c)))
    cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
    c = moved(c, (k, k, cx * (1 - k), cy * (1 - k)))
    out = RecordingPen()
    for op, pts in new[1]:
        getattr(out, op)(*pts)
    pen = out if (area(c) > 0) == (area(new[0]) > 0) else ReverseContourPen(out)
    for op, pts in c:
        getattr(pen, op)(*pts)
    return out


def inside_from(wide, bold, name):
    """bold (an open round, upright frame) with the run facing its bowl
    redrawn from wide's (italic_inside); as it was where they do not match"""
    w, b = ufoLib2.objects.Glyph(), ufoLib2.objects.Glyph()
    for path, glyph in ((wide, w), (bold, b)):
        (path.replay if hasattr(path, "replay") else path.draw)(glyph.getPen())
    try:
        italic_inside.replace(w, b, *italic_inside.RUNS[name])
    except ValueError as e:
        print(f"  {name}: inside kept as stroked ({e})")
        return bold
    out = RecordingPen()
    b.draw(out)
    return out


def oval(wide, bold):
    """bold (a two-contour round) redrawn with wide's curves: each contour of
    the lighter round fitted to the box of the emboldened one, then its
    handles lengthened or shortened alike (smooth nodes stay smooth) until
    it holds the same area, so the ink and its weight stay as emboldened."""
    def contours(path):
        rec, out = RecordingPen(), []
        (path.replay if hasattr(path, "replay") else path.draw)(rec)
        for op, pts in rec.value:
            if op == "moveTo":
                out.append([])
            out[-1].append((op, pts))
        return out

    def area(c):
        pen = AreaPen()
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.value

    def bounds(c):
        pen = BoundsPen(None)
        for op, pts in c:
            getattr(pen, op)(*pts)
        return pen.bounds

    def tension(c, k):
        """each curve's handles k times as long, from the nodes they leave"""
        out, cur = [], None
        for op, pts in c:
            if op == "curveTo":
                (h1, h2, p) = pts
                h1 = (cur[0] + k * (h1[0] - cur[0]), cur[1] + k * (h1[1] - cur[1]))
                h2 = (p[0] + k * (h2[0] - p[0]), p[1] + k * (h2[1] - p[1]))
                pts = (h1, h2, p)
            out.append((op, pts))
            if pts:
                cur = pts[-1]
        return out

    def fit(c, box):
        (x0, y0, x1, y1), (u0, v0, u1, v1) = bounds(c), box
        sx, sy = (u1 - u0) / (x1 - x0), (v1 - v0) / (y1 - y0)
        return [(op, tuple((u0 + (x - x0) * sx, v0 + (y - y0) * sy) for x, y in pts)) for op, pts in c]

    old, new = contours(wide), contours(bold)
    if len(old) != 2 or len(new) != 2 or any(op not in ("moveTo", "curveTo", "lineTo", "closePath")
                                             for c in old for op, _ in c):
        raise ValueError("oval: two contours each, drawn")
    old.sort(key=lambda c: abs(area(c)))
    new.sort(key=lambda c: abs(area(c)))
    out = RecordingPen()
    for src, dst in zip(old, new):
        box, target = bounds(dst), abs(area(dst))
        c = fit(src, box)
        for _ in range(4):  # the handles move the box a little: fitted again
            lo, hi = 0.5, 1.5
            for _ in range(40):
                k = (lo + hi) / 2
                if abs(area(tension(c, k))) < target:
                    lo = k
                else:
                    hi = k
            c = fit(tension(c, (lo + hi) / 2), box)
        for op, pts in c:
            getattr(out, op)(*pts)
    return out


def bridge(glyph, maxgap=24, overlap=8):
    """glyph with the narrow gaps between straight edges that face each other
    (serif ends that emboldening brought within maxgap: x's inner feet, the
    top of ч) filled, so the parts join instead of leaving a slit."""
    import math

    from derive import draw_path

    path = pathops.Path()
    for c in glyph.contours:
        c.draw(path.getPen())
    path = pathops.simplify(path)
    edges = []
    for c in glyph.contours:
        ons = [p for p in c.points if p.type]
        for p0, p1 in zip(ons, ons[1:] + ons[:1], strict=True):
            if p1.type == "line" and math.dist((p0.x, p0.y), (p1.x, p1.y)) >= overlap:
                edges.append(((p0.x, p0.y), (p1.x, p1.y)))
    fills = []
    for i, (a0, a1) in enumerate(edges):
        ax, ay = a1[0] - a0[0], a1[1] - a0[1]
        la = math.hypot(ax, ay)
        ux, uy = ax / la, ay / la
        for b0, b1 in edges[i + 1:]:
            bx, by = b1[0] - b0[0], b1[1] - b0[1]
            lb = math.hypot(bx, by)
            if (ux * bx + uy * by) / lb > -0.985:  # facing edges run opposite ways, parallel
                continue
            # B's distance from A's line, and their overlap along it
            gap = (b0[0] - a0[0]) * -uy + (b0[1] - a0[1]) * ux
            if not 0 < abs(gap) < maxgap:
                continue
            t = sorted(((b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy, (b1[0] - a0[0]) * ux + (b1[1] - a0[1]) * uy))
            lo, hi = max(0, t[0]), min(la, t[1])
            if hi - lo < overlap:
                continue
            nx, ny = -uy * gap, ux * gap
            mid = (a0[0] + ux * (lo + hi) / 2 + nx / 2, a0[1] + uy * (lo + hi) / 2 + ny / 2)
            probe = pathops.Path()
            pen = probe.getPen()
            pen.moveTo((mid[0] - 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] + 0.5))
            pen.lineTo((mid[0] - 0.5, mid[1] + 0.5))
            pen.closePath()
            if pathops.op(path, probe, pathops.PathOp.INTERSECTION).bounds != (0, 0, 0, 0):
                continue  # ink between them: not a gap
            q = [(a0[0] + ux * lo, a0[1] + uy * lo), (a0[0] + ux * hi, a0[1] + uy * hi)]
            fill = pathops.Path()
            pen = fill.getPen()
            pen.moveTo(q[0])
            pen.lineTo(q[1])
            pen.lineTo((q[1][0] + nx, q[1][1] + ny))
            pen.lineTo((q[0][0] + nx, q[0][1] + ny))
            pen.closePath()
            fills.append(fill)
    if not fills:
        return glyph
    for f in fills:
        path = pathops.op(path, f, pathops.PathOp.UNION)
    out = ufoLib2.objects.Glyph()
    draw_path(None, glyph, out, path)
    return out


PART_GAP = 300  # serifs nearer than this (units) may meet when emboldened
PART_KEEP = 0.5  # of the source's gap that stays open where they would only touch
PART_STEP = 8
GAP_SHARE = 0.9  # of the share the source's gap has of the white between the strokes (keep_gaps)
GAP_AT = 221  # units into the letter from the serifs' edge where that white is measured: a quarter of the x-height
GAP_MIN_WHITE = 120  # a white narrower than this between the strokes is no counter
GAP_STEP = 4


def _ink(p, box):
    r = pathops.Path()
    pen = r.getPen()
    x0, y0, x1, y1 = box
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    out = pathops.op(p, r, pathops.PathOp.INTERSECTION)
    return abs(out.area) if out.contours else 0


def _simple_path(g):
    p = pathops.Path()
    for c in g.contours:
        c.draw(p.getPen())
    return pathops.simplify(p)


def _shortened(wide, pairs, s):
    """wide with both tips of each pair moved s apart: each point with its
    handles, so a smooth join stays smooth"""
    moved = ufoLib2.objects.Glyph()
    wide.replay(moved.getPen())
    for ta, tb, *_ in pairs:
        for tips, dx in ((ta, -s), (tb, s)):
            for ci, i in tips:
                pts = moved.contours[ci].points
                near = {i}
                for step in (-1, 1):
                    j = (i + step) % len(pts)
                    if pts[j].type is None:
                        near.add(j)
                for j in near:
                    pts[j].x += dx
    rec = RecordingPen()
    moved.draw(rec)
    return rec


def serif_pairs(src):
    """The serif tips that face each other across less than PART_GAP in src:
    [(tips a, tips b, mid x, gap, band, shortest edge, ink above)]; band is
    the serifs' height at the gap, ink above says on which side of the flat
    edge the letter lies."""
    path = pathops.Path()
    for c in src.contours:
        c.draw(path.getPen())
    ink = _ink
    # flat edges: (contour, start index, end index, y, xmin, xmax, ink above)
    edges = []
    for ci, c in enumerate(src.contours):
        pts = c.points
        n = len(pts)
        for i in range(n):
            p0, p1 = pts[i], pts[(i + 1) % n]
            if p0.type and p1.type == "line" and p0.y == p1.y and abs(p1.x - p0.x) >= 30:
                mx = (p0.x + p1.x) / 2
                above = ink(path, (mx - 1, p0.y, mx + 1, p0.y + 4)) > 4
                edges.append((ci, i, (i + 1) % n, p0.y, min(p0.x, p1.x), max(p0.x, p1.x), above))

    def tip(ci, i, step):
        """The tip's two points: the edge's end i and the corner beside it on
        the serif's other face (the next point away from the edge)."""
        pts = src.contours[ci].points
        j = (i + step) % len(pts)
        q = pts[j]
        if q.type == "line" and 10 <= abs(q.y - pts[i].y) <= 150:
            return [(ci, i), (ci, j)], abs(q.y - pts[i].y)
        return [(ci, i)], None

    pairs = []
    for a in edges:
        for b in edges:
            if a[3] != b[3] or a[6] != b[6] or not 0 < b[4] - a[5] < PART_GAP:
                continue
            # a's right end faces b's left end
            ia = a[1] if src.contours[a[0]].points[a[1]].x == a[5] else a[2]
            ib = b[1] if src.contours[b[0]].points[b[1]].x == b[4] else b[2]
            sa = 1 if ia == a[2] else -1  # away from a's edge
            sb = 1 if ib == b[2] else -1
            ta, ha = tip(a[0], ia, sa)
            tb, hb = tip(b[0], ib, sb)
            t = min(h for h in (ha, hb) if h) if (ha or hb) else 40
            gap = b[4] - a[5]
            band = (a[3], a[3] + t) if a[6] else (a[3] - t, a[3])
            pairs.append((ta, tb, (a[5] + b[4]) / 2, gap, band, min(a[5] - a[4], b[5] - b[4]), a[6]))
    return pairs


def part_serifs(wide, bold, make):
    """bold (wide emboldened by make) with neighbouring serifs kept apart
    where emboldening brings their tips together only partly: the italics'
    v.sc w.sc y.sc tops and ʌ.sc's feet, 125 units apart in the Italic,
    meet in a notch over a joint a few units thick.  Serifs joined over their
    whole height (x.sc's inner feet, by bridge; ш.sc's base) and serifs that
    stay apart are left alone.  Both tips of such a pair are shortened in the
    source by the same amount, in steps, until PART_KEEP of the source's gap
    stays open.  Returns (glyph, number of pairs parted)."""
    src = ufoLib2.objects.Glyph()
    wide.replay(src.getPen())
    pairs = serif_pairs(src)
    ink, bold_path = _ink, _simple_path

    def partly(p, mid, band):
        h = ink(p, (mid - 1, band[0], mid + 1, band[1])) / 2
        return 0.05 < h / (band[1] - band[0]) < 0.95

    bp = bold_path(bold)
    bad = [pr for pr in pairs if partly(bp, pr[2], pr[4])]
    if not bad:
        return bold, 0
    for s in range(PART_STEP, int(min(pr[5] for pr in bad)) - 20, PART_STEP):
        out = make(_shortened(wide, bad, s))
        op = bold_path(out)
        if all(ink(op, (mid - gap * PART_KEEP / 2, band[0], mid + gap * PART_KEEP / 2, band[1])) == 0
               for _, _, mid, gap, band, _, _ in bad):
            return out, len(bad)
    return bold, 0


def _white(path, x, y):
    """The white run across through (x, y): its width; 0 where there is ink,
    or no ink on one of the sides."""
    reach = 900
    strip = pathops.Path()
    pen = strip.getPen()
    pen.moveTo((x - reach, y - 1))
    pen.lineTo((x + reach, y - 1))
    pen.lineTo((x + reach, y + 1))
    pen.lineTo((x - reach, y + 1))
    pen.closePath()
    left = right = None
    for c in pathops.op(path, strip, pathops.PathOp.INTERSECTION).contours:
        x0, _, x1, _ = c.bounds
        if x0 <= x <= x1:
            return 0
        if x1 < x and (left is None or x1 > left):
            left = x1
        if x0 > x and (right is None or x0 < right):
            right = x0
    return right - left if left is not None and right is not None else 0


def keep_gaps(wide, bold, make):
    """bold (wide emboldened by make) with the gaps between facing serifs
    kept in proportion (the upright Bold; docs/claude/bold.md, B1, approved
    2026-11-11).  The stems grow toward each other and the serifs keep their
    reach, so the gap between n's feet fell to 0.39 of the Regular's while
    the counter kept 0.82; the reference bolds keep the gap's share of the
    counter (0.89 to 0.91).  For part_serifs' pairs: where the gap's share
    of the white between the strokes, measured GAP_AT into the letter, is
    below GAP_SHARE of the source's, both tips are shortened in the source
    in steps of GAP_STEP until it is.  A glyph where that is not reached
    within the serifs' length stays as it is.  The far tip of a diagonal's
    serif follows by a few units: embolden_by_weight weighs a serif's edge
    at its middle, which the shortening moves.  Returns (glyph, pairs)."""
    src = ufoLib2.objects.Glyph()
    wide.replay(src.getPen())
    sp, bp = _simple_path(src), _simple_path(bold)
    todo = []
    for pair in serif_pairs(src):
        ta, tb, mid, gap, band, _, above = pair
        if len(ta) < 2 or len(tb) < 2:
            continue  # no serif's end but a stroke's flat foot (M's vertex): shortening it would thin the stroke
        y, side = (band[0], 1) if above else (band[1], -1)
        w_src, w_bold = _white(sp, mid, y + side * GAP_AT), _white(bp, mid, y + side * GAP_AT)
        g_bold = _white(bp, mid, y + side * 6)
        if w_src >= max(GAP_MIN_WHITE, gap) and w_bold >= GAP_MIN_WHITE and g_bold \
                and g_bold < GAP_SHARE * gap / w_src * w_bold - 2:
            todo.append((*pair, y + side * 6, y + side * GAP_AT, GAP_SHARE * gap / w_src))
    if not todo:
        return bold, 0
    for s in range(GAP_STEP, int(min(t[5] for t in todo)) - 20, GAP_STEP):
        out = make(_shortened(wide, todo, s))
        op = _simple_path(out)
        if all(_white(op, t[2], t[7]) >= t[9] * _white(op, t[2], t[8]) - 2 for t in todo):
            return out, len(todo)
    return bold, 0


FAULTS = {}  # faults' counts by outline, for the run (each letter asks up to five times)


def faults(g, font):
    """How many notches (a slit between parts that come close), slivers and
    twists (an outline crossing itself at a tight terminal) g's contours have
    (only the contours: font does not change it)."""
    key = repr([[(p.x, p.y, p.type, p.smooth) for p in c.points] for c in g.contours])
    if key not in FAULTS:
        FAULTS[key] = _faults(g, font)
    return FAULTS[key]


def _faults(g, font):
    from glyph_lint import notch_findings, vector_findings

    p = pathops.Path()
    for c in g.contours:
        c.draw(p.getPen())
    if not p.contours:
        return 0
    only = ufoLib2.objects.Glyph()
    for c in g.contours:
        c.drawPoints(only.getPointPen())
    vec = [f for f in vector_findings(pathops.simplify(p)) if f[0] in ("sliver", "twist")]
    return len(notch_findings(font, only, p.bounds)) + len(vec)


def slit(glyph, before, font):
    """Whether glyph (emboldened contours) has a fault the Regular's glyph
    (before) has not."""
    return faults(glyph, font) > faults(before, font)


def mark_like(g):
    """Accents and combining marks: zero width, the spacing modifier
    symbols (´ ˆ ΄ ᾿ ..., whatever their width) and the unencoded 880-wide
    spacing accents (Acute ...), not a small cap that width (the Italic's
    ґ.sc, 880 wide, emboldened as an accent)."""
    if g.width == 0:
        return True
    if g.unicode is not None:
        return unicodedata.category(chr(g.unicode)) in ("Sk", "Mn")
    return g.width == 880 and not g.name.endswith(".sc")


SLANT = 0.0  # the source's slant (tan of its italic angle), set in main()


def optical_fit(ref, new, h, depth=0.2, steps=40):
    """(left, right) side space to add to new (an outline, upright) so that
    the white beside its ink across 0..h is ref's, as space_figures.optical
    measures white (rows across the band, deep white clipped): both
    measured from the same edges and clipped in ref's window, so a part
    shorter than ref's (the f's bar end) counts as the white it adds across
    the band, not as the whole side moving."""
    from space_figures import _runs

    paths = []
    for rec in (ref, new):
        p = pathops.Path()
        rec.replay(p.getPen())
        p = pathops.simplify(p)
        if not p.contours:
            return None
        paths.append(p)
    x0 = min(p.bounds[0] for p in paths)
    x1 = max(p.bounds[2] for p in paths)
    rows = [[_runs(p, h * (i + 0.5) / steps) for i in range(steps)] for p in paths]
    out = []
    for which in "LR":
        dist = [[None if not rr else (rr[0][0] - x0 if which == "L" else x1 - rr[-1][1]) for rr in r] for r in rows]
        real = [v for v in dist[0] if v is not None]
        if not real:
            return None
        cap = min(real) + depth * h
        mean = [sum(min(v, cap) if v is not None else cap for v in d) / steps for d in dist]
        out.append(round(mean[0] - mean[1]))
    return tuple(out)


def band_height(font, name):
    """The height a glyph's side space is judged over: the x-height for
    lowercase, the small caps' for small caps, the cap height for the rest."""
    if name.split(".")[1:2] == ["sc"]:
        return font.lib.get("org.myiadidot.smallcapHeight", 1040)
    # a ligature is judged as the unencoded ones are, whatever its code
    # point (U+FB05 U+FB06 on ſt st moved them 9 units, 2026-11-08)
    ch = chr(font[name].unicode) if font[name].unicode and "_" not in name else ""
    if ch and unicodedata.category(ch) == "Ll":
        return font.info.xHeight or 884
    return font.info.capHeight or 1434


def bold_rec(glyph):
    rec = RecordingPen()
    glyph.draw(rec)
    return rec


def rec_bounds(rec):
    """The ink bounds of a recording or glyph (overlaps merged)."""
    p = pathops.Path()
    (rec.replay if hasattr(rec, "replay") else rec.draw)(p.getPen())
    p = pathops.simplify(p)
    return p.bounds if p.contours else None


def tx(x, y):
    """Where an x at height y lands in the Bold: in the upright frame scaled
    across by KX and moved AX / 2 right."""
    return (x - y * SLANT) * KX + AX / 2 + y * SLANT


def tx_offset(dx, dy):
    """A component offset in the Bold: scaled across in the upright frame."""
    return (dx - dy * SLANT) * KX + dy * SLANT


def attach_point(font, mark, bases, centre):
    """Where a mark component attaches, in the Regular's composite and in the
    Bold's: the anchor of the base component nearest to the mark's ink, or
    failing that the mark's own attachment point (centre)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    mdx, mdy = mark.transformation[4], mark.transformation[5]

    def moved(x, y):  # unanchored: the composite's outline moves so
        return x, tx(x, y)

    if ink is None:
        return moved(mdx + centre[mark.baseGlyph], mdy)
    mx, my = mdx + (ink[0] + ink[2]) / 2, mdy + (ink[1] + ink[3]) / 2
    best = None
    for base, bdx, bdy in bases:
        for a in font[base].anchors:
            if a.name.startswith("_"):
                continue
            ax, ay = a.x + bdx, a.y + bdy
            d = abs(ax - mx) + abs(ay - my)
            if best is None or d < best[0]:
                # in the Bold: the base's anchor and its offset, rounded as
                # they are written, so the mark lands exactly where mark
                # positioning puts it
                best = (d, ax, round(tx(a.x, a.y)) + round(tx_offset(bdx, bdy)))
    return best[1:] if best else moved(mdx + centre[mark.baseGlyph], my)


def slant_back(path, pen, transforms, split):
    """path drawn into pen through transforms (applied in the order given);
    split: its curves split where slanting again sets them past their
    points (italic_geometry.EXTREME_PAST), as the Italic split them."""
    from derive import with_extremes
    from italic_geometry import EXTREME_PAST

    rec = RecordingPen()
    pen_t = rec
    for t in reversed(transforms):
        pen_t = TransformPen(pen_t, t)
    path.draw(pen_t)
    if split:
        with_extremes(rec, pen, round_points=False, past=EXTREME_PAST)
    else:
        rec.replay(pen)


def contours_only(g):
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    return rec


def redraw(g, glyph):
    """Replace g's contours with those of glyph (an emboldened ufoLib2 Glyph);
    quadratic segments (pathops' results may hold some) made cubic."""
    g.clearContours()
    if any(p.type == "qcurve" for c in glyph.contours for p in c.points):
        from derive import CubicPen

        for c in glyph.contours:
            c.draw(CubicPen(g.getPen()))
        return
    pen = g.getPointPen()
    for c in glyph.contours:
        c.drawPoints(pen)


def refit_horns(font):
    """The letters with a horn composed again on the outlines as saved:
    composites.py fits the horn to its base and keeps the marks above
    clear of it by their ink, which rounding and cleaning still move."""
    from composites import Builder

    builder = Builder(font)
    for g in [g for g in font if g.unicode is not None and g.components]:
        if (len(unicodedata.normalize("NFD", chr(g.unicode))) < 2
                or not any(c.baseGlyph in ("horn", "Horn") for c in g.components)):
            continue
        r = builder.recipe(g.unicode)
        if [(c.glyph, c.dx, c.dy) for c in r.components] != [(c.baseGlyph, *c.transformation[4:]) for c in g.components]:
            r.name, lib = g.name, dict(g.lib)
            del font[g.name]
            builder.write(r)
            font[r.name].lib.update(lib)


def in_line(glyph, base, most=5):
    """a curve running into a line (or out of one) within most degrees of
    it, where base has that node (within 1.5 units) running on smoothly
    (under a degree): its handle there put in line, its length kept (a
    letter made again in the upright frame is rounded there, then slanted
    back: ʉ's stem under its bar turned 3.7 degrees where u's runs on,
    more than round_smoothly mends)"""
    def joins(g):
        for c in g.contours:
            P, n = c.points, len(c.points)
            for i, p in enumerate(P):
                prev, nxt = P[(i - 1) % n], P[(i + 1) % n]
                if p.type == "line" and prev.type and not nxt.type:
                    o, h = prev, nxt  # a line in, a curve out
                elif p.type == "curve" and not prev.type and nxt.type == "line":
                    o, h = nxt, prev  # a curve in, a line out
                else:
                    continue
                lx, ly = p.x - o.x, p.y - o.y
                hx, hy = h.x - p.x, h.y - p.y
                ll, hl = math.hypot(lx, ly), math.hypot(hx, hy)
                if ll > 1e-9 and hl > 1e-9:
                    t = math.degrees(math.acos(max(-1.0, min(1.0, (lx * hx + ly * hy) / (ll * hl)))))
                    yield p, h, (lx / ll, ly / ll), hl, t

    smooth = [(p.x, p.y) for p, _, _, _, t in joins(base) if t < 1]
    for p, h, (ux, uy), hl, t in list(joins(glyph)):
        if 0 < t <= most and any(math.dist((p.x, p.y), q) <= 1.5 for q in smooth):
            h.x, h.y = p.x + ux * hl, p.y + uy * hl


def round_smoothly(P):
    """P's points rounded to whole units, a join that ran on (nearly)
    smoothly, under 3 degrees, not broken further: where rounding leaves
    it turning by more than a degree and more than it did, its handles
    moved a unit each, together, to bring it more in line (a 15-unit
    handle rounded turns up to 4 degrees, one moved alone in steps of 3-4),
    a level or upright one (at an extreme) kept so. Handles under 10 units are left as rounded: theirs
    is no angle worth the name (checks.py)."""
    def turn(a, h, b):
        t = math.atan2(h[1] - a[1], h[0] - a[0]) - math.atan2(b[1] - h[1], b[0] - h[0])
        return abs(math.degrees((t + math.pi) % (2 * math.pi) - math.pi))

    def overshoot(k, q):
        """how far the curve through handle k, put at q, bulges past its ends"""
        h = [(P[(k + d) % n].x, P[(k + d) % n].y) for d in (-2, -1, 0, 1, 2)]
        seg = h[1:5] if P[(k - 1) % n].type else h[0:4]
        seg = [q if pt == (P[k].x, P[k].y) else pt for pt in seg]
        most = 0.0
        for step in range(1, 32):
            t = step / 32
            u = 1 - t
            pt = [u ** 3 * seg[0][c] + 3 * u * u * t * seg[1][c] + 3 * u * t * t * seg[2][c] + t ** 3 * seg[3][c]
                  for c in (0, 1)]
            for c in (0, 1):
                lo, hi = sorted((seg[0][c], seg[3][c]))
                most = max(most, lo - pt[c], pt[c] - hi)
        return most

    n = len(P)
    raw = [(p.x, p.y) for p in P]
    for p in P:
        p.x, p.y = round(p.x), round(p.y)
    if n < 3:
        return
    for i, p in enumerate(P):
        if not p.type:
            continue
        a, b = (i - 1) % n, (i + 1) % n
        if min(math.dist(raw[a], raw[i]), math.dist(raw[i], raw[b])) < 1 or turn(raw[a], raw[i], raw[b]) > 3:
            continue
        node = (p.x, p.y)
        ends = [(P[a].x, P[a].y), (P[b].x, P[b].y)]
        least = turn(ends[0], node, ends[1])
        # only what the rounding broke (an outline in whole units, a drawn
        # glyph kept, stays as it is)
        if least <= max(1, turn(raw[a], raw[i], raw[b]) + 0.25) or min(math.dist(e, node) for e in ends) < 10:
            continue
        # each handle's places a unit around it (an on-curve neighbour, a
        # line's end, stays), tried together: one alone, 15-20 units long,
        # turns in steps of 3-4 degrees
        options = []
        for k in (a, b):
            places = [(P[k].x, P[k].y)]
            if not P[k].type:
                bulge = overshoot(k, (P[k].x, P[k].y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (P[k].x + dx, P[k].y + dy)
                        # an extreme's handle stays level or upright
                        if (dx or dy) and math.dist(q, node) >= 10 and not (P[k].x == p.x and q[0] != p.x) \
                                and not (P[k].y == p.y and q[1] != p.y) and overshoot(k, q) <= max(bulge, 2):
                            places.append(q)  # (nor bulging further past its ends: an extreme lost)
            options.append(places)
        best = None
        for qa in options[0]:
            for qb in options[1]:
                t = turn(qa, node, qb)
                moved = abs(qa[0] - P[a].x) + abs(qa[1] - P[a].y) + abs(qb[0] - P[b].x) + abs(qb[1] - P[b].y)
                if t < least - 1e-9 or (best and abs(t - least) < 1e-9 and moved < best[2]):
                    best, least = (qa, qb, moved), t
        if best:
            (P[a].x, P[a].y), (P[b].x, P[b].y) = best[0], best[1]


def separate_breve_grave_stacks(font):
    """Keep the inherited grave/breathing pairs clear of the Greek breve.

    These legacy mark ligatures use fixed component offsets rather than
    Builder's stacking anchors. Weighting makes the grave touch the breve.
    Move the complete upper pair, preserving its internal arrangement and
    the stack's attachment anchor, with the usual lowercase mark gap.
    """
    from smallcaps import ink_bounds

    for breathing in ("0313", "0314"):
        glyph = font[f"brevecmb_uni{breathing}_gravecomb.grek"]
        upper, breve = glyph.components
        upper_bounds = ink_bounds(font, upper.baseGlyph)
        breve_bounds = ink_bounds(font, breve.baseGlyph)
        gap = upper_bounds[1] + upper.transformation.dy - (breve_bounds[3] + breve.transformation.dy)
        if gap < STACK_GAP_LC:
            xx, xy, yx, yy, dx, dy = upper.transformation
            upper.transformation = (xx, xy, yx, yy, dx, dy + math.ceil(STACK_GAP_LC - gap))


def finalize(font, smooth=True, separate_stacks=False, plain=()):
    """Finish a generated style before persistence. Its
    points, anchors and component offsets are rounded to whole units first,
    and what that leaves cleaned (glyph_lint). The Regular's record of what
    its derived glyphs were built from (built_from.py) is left behind: a
    generated style is checked by being generated again.
    smooth: joins the rounding would break kept smooth (round_smoothly).
    plain: glyphs rounded plainly all the same.
    separate_stacks: fit legacy Greek breve/grave stacks after rounding;
    enabled for the bold styles, not for the Italic's shared writer."""
    for g in font:
        g.lib.pop(BUILT_KEY, None)
        for c in g.contours:
            if smooth and g.name not in plain:
                round_smoothly(c.points)
            else:
                for p in c.points:
                    p.x, p.y = round(p.x), round(p.y)
        for a in g.anchors:
            a.x, a.y = round(a.x), round(a.y)
        for c in g.components:
            xx, xy, yx, yy, dx, dy = c.transformation
            c.transformation = (xx, xy, yx, yy, round(dx), round(dy))
    fix(font)  # what rounding left (a unit's step)
    from finalization import finish_glyphs

    finish_glyphs(font)
    if separate_stacks:
        separate_breve_grave_stacks(font)
    refit_horns(font)


def write(font, path, smooth=True, separate_stacks=False, plain=(), kept=None):
    """font finalized and saved to path, the acceptances of the
    style saved there before carried over (accepted.py), and the glyphs
    kept as drawn (drawn.py: kept, as saved) put back as they were."""
    from accepted import acceptances, carry
    from drawn import restore
    from ufo_io import save_font

    finalize(font, smooth=smooth, separate_stacks=separate_stacks, plain=plain)
    carry(acceptances(ufoLib2.Font.open(path)) if Path(path).exists() else {}, font)
    restore(kept or {}, font)
    save_font(font, path)

SMALL_SUFFIXES = ("superior", "inferior", ".numr", ".dnom", ".sups", ".subs")


def small_glyphs(regular, italic):
    """(names, scale): the glyphs that are letters or figures made small (the
    superior and inferior figures, numerators, ª º, the modifier letters),
    and their scale, the superior zero's round stem against the zero's.
    Emboldened by weight at full size their stems (about 100) would gain a
    fraction of AX; as a letter at that scale, they gain AX times it."""
    import derive
    from derived import recipes

    scale = derive.strokes(regular, "zerosuperior")[1] / derive.strokes(regular, "zero")[1]
    names = {g.name for g in regular if g.name.split(".")[0].endswith(SMALL_SUFFIXES[:2])
             or any(g.name.endswith(sfx) for sfx in SMALL_SUFFIXES[2:])}
    names |= {"ordfeminine", "ordmasculine"} & set(regular.keys())
    cmap = {u: g.name for g in regular for u in g.unicodes}
    for ch, op, _base, _band in recipes(italic):
        if op == "superior":
            names.add(derive.resolve(cmap, ch))
    for u, name in cmap.items():
        uname = unicodedata.name(chr(u), "")
        if uname.startswith(("MODIFIER LETTER SMALL", "MODIFIER LETTER CAPITAL")) or "SUPERSCRIPT" in uname \
                or "SUBSCRIPT" in uname:
            names.add(name)
    return names, scale


def saved_flaws(path):
    """The steps and crumbs (glyph_lint) of path as saved, rounded to whole
    units and cleaned (write: a step a unit high taken out), by kind and
    place; None where they cannot be told (a contour rounded away to
    nothing)."""
    from fontTools.pens.roundingPen import RoundingPen
    from glyph_lint import clean, step_findings, vector_findings

    rounded = pathops.Path()
    pathops.simplify(path).draw(RoundingPen(rounded.getPen()))
    try:
        rounded = clean(rounded)
        return {f[:2] for f in step_findings(rounded) + vector_findings(rounded)}
    except (pathops.PathOpsError, StopIteration):
        return None


def follow_bases(source, font, italic, kx=None, slant=None, skip=(), whole=None):
    """Derived letters (derive.py's recipes) made of the Bold's own base:
    emboldened whole, a letter's junctions (a slash meeting a stem, a tilde
    crossing a diagonal) thicken unlike its base's strokes, eating the stem
    beside them. One that is its base turned, mirrored or flipped (exactly,
    in the source) becomes the Bold base so moved; one that adds to its
    base without cutting any of it is joined with the Bold base, placed
    where the source's base sits in it, unless the emboldened letter keeps
    that base already. Letters that cut their base (a hook replacing a
    stem's end) stay as emboldened. kx and slant: the widening and the
    italic's slant (make_bold's by default); skip: names to leave; whole:
    a dict that gets the letters left emboldened whole, with the reason.
    Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import KEEPS, TRANSFORMS, Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    kx = KX if kx is None else kx
    slant = SLANT if slant is None else slant
    # recipes that only cut their base
    recuts = {"unserif": derive.unserif_cut}
    deslant = (1, 0, -slant, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    def ink(name):
        p = pathops.Path()
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(p.getPen())
        return p

    changed, failed = [], []
    whole = {} if whole is None else whole
    for ch, op, base, band in recipes(italic):
        name, base = resolve(ch), resolve(base)
        if name not in source or base not in source or base == "space" or name not in font or name in skip:
            continue
        g = font[name]
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        if g.components:
            continue
        if op in recuts:
            # only a cut of its base (U.horn: the serif's outer arm): the
            # same cut of this font's base, found in the upright frame and
            # made in the font's own (pathops splits curves at the extremes
            # of the frame it cuts in)
            from make_italic import XH, shear

            work = ufoLib2.Font()
            piece = work.newGlyph(base)
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            rec.replay(piece.getPen())
            shear(piece, -slant, XH / 2)
            cut = pathops.Path()
            recuts[op](work, base).draw(TransformPen(cut.getPen(), (1, 0, slant, 1, -slant * XH / 2, 0)))
            out = derive.path_op(derive.to_path(font, font[base]), cut, "DIFFERENCE")
            g.clearContours()
            derive.draw_path(font, font[base], g, out)
            g.width = font[base].width
            changed.append(name)
            continue
        if op not in KEEPS | TRANSFORMS:
            if op not in RESHAPES:
                whole[name] = f"{op}: cuts its base"
            continue
        mine = Outline(source, name, deslant)
        if mine.bounds is None:
            continue
        if op in TRANSFORMS:
            w = source[base].width
            sb = band if isinstance(band, str) else band[0] if isinstance(band, tuple) else "x"
            cy = derive.band_middle(source, sb) if op != "mirror" else 0
            a, _, _, d, e, f = {"turn": (-1, 0, 0, -1, w, 2 * cy), "mirror": (-1, 0, 0, 1, w, 0),
                                "flip": (1, 0, 0, -1, 0, 2 * cy)}[op]
            shares, _, _ = compare(Outline(source, base, (a, 0, -a * slant, d, e, f)), mine)
            if shares["exact"] < MOVED_EXACT_FOR.get(name, MOVED_EXACT):
                whole[name] = f"{op}: not exactly its base so moved"
                continue
            # the same move of the Bold base, in the upright frame the Italic
            # makes its letters in (make_italic.shear: about half the
            # x-height, where the frames agree); about the baseline, a
            # mirrored or turned letter's ink moved right by twice the slant
            # times its height (ɘ ɐ against the next letter)
            from make_italic import XH

            y0 = XH / 2
            bw = font[base].width
            e = bw if op in ("turn", "mirror") else 0
            out = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            # slanted again, its curves split where they run past their
            # points (the Italic's turned and mirrored letters, ɔ ƹ ɜ, are)
            slant_back(rec, out.getPen(), [(1, 0, -slant, 1, slant * y0, 0), (a, 0, 0, d, e, f),
                                           (1, 0, slant, 1, -slant * y0, 0)], bool(slant))
            g.width = bw
        else:
            shares, dx, _ = compare(Outline(source, base, deslant), mine)
            # only a letter that keeps its whole base in the source: the
            # Italic's ɨ has the dot of its own, not i's, and would get both
            if shares["lost"] > 0.02:
                if op not in RESHAPES:
                    whole[name] = f"{op}: does not keep its whole base"
                continue
            # nothing to mend when the emboldened letter keeps its Bold base
            # (ʘ: O's outline, the dot inside); and Skia's union fails on
            # curves that coincide, as theirs then do
            if compare(Outline(font, base, deslant), Outline(font, name, deslant))[0]["lost"] <= 0.02:
                continue
            placed = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            rec.replay(TransformPen(placed.getPen(), (1, 0, 0, 1, dx * kx, 0)))
            # each simplified on its own first: a base rebuilt here (ə turned)
            # winds the other way, and in one path the two would cancel
            a = pathops.simplify(ink(name))
            # the union holds all of both, row by row, or it failed (curves
            # that coincide): then tried with the base a hair lower, higher
            # (ⱥ.sc: a.sc's foot a third of a unit above the letter's) or
            # aside, either way (ǥ.sc's bar on g.sc, 2026-11-05: only to the
            # left), which parts the curves (rounded away on saving), else
            # the letter is left as emboldened
            # (ө.sc's bar on o.sc failed all four once o.sc stood a unit
            # wider, 2026-11-11: then both ways at once, and a little further)
            for nudge in (0, (0, -0.25), (0, 0.25), (0.25, 0), (-0.25, 0),
                          (0.25, 0.25), (-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0, -0.4), (0, 0.4)):
                b = pathops.simplify(placed)
                if nudge:
                    b = pathops.Path()
                    placed.draw(TransformPen(b.getPen(), (1, 0, 0, 1, *nudge)))
                    b = pathops.simplify(b)
                try:
                    out = pathops.op(a, b, pathops.PathOp.UNION)
                except pathops.PathOpsError:  # failed outright: as a union that lost ink
                    held = False
                    continue
                joined = Outline(None, None, deslant, path=out)
                held = all(compare(Outline(None, None, deslant, path=p), joined)[0]["lost"] <= 0.01 for p in (a, b))
                if held and nudge:
                    # a nudged join that leaves a step or a crumb, once
                    # rounded and cleaned as it is saved, is no better
                    flaws = saved_flaws(out)
                    held = flaws is not None and not flaws
                if held:
                    break
            if not held:
                failed.append(name)
                whole[name] = f"{op}: the union with its base failed"
                continue
        out = pathops.simplify(out)
        glyph = ufoLib2.objects.Glyph()
        out.draw(glyph.getPen())
        redraw(g, glyph)
        changed.append(name)
    if failed:
        print("  derived letters left as emboldened (their union failed):", " ".join(failed))
    return changed


MIN_PIECE = 3000  # units²: an added piece (ɬ.sc's bar is 8000), not a sliver
SPECK = 8000  # units²: a cut's remnant apart from the letter (Bulgarian ж's 4590, Bold Italic Ɦ's serif end 6622),
# not a piece (i's dot 40000)


def attached_small(source, font, italic):
    """Derived letters that attach a glyph scaled down to their base (ɬ's
    ring, the degree sign at 0.45; ⁂'s asterisks): emboldened whole, the
    small piece thickens like a stem and closes up. Made of the Bold base
    and the source's added parts, those emboldened at the weight of their
    scale (a ring at 0.45 gains 0.45 of a stem's AX), as the Bold degree
    sign scaled would be. Recipes that cut the base (Ɲ) stay as they are.
    Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    deslant = (1, 0, -SLANT, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    def path(f, name, t=(1, 0, 0, 1, 0, 0)):
        p = pathops.Path()
        rec = DecomposingRecordingPen(f)
        f[name].draw(rec)
        rec.replay(TransformPen(p.getPen(), t))
        return pathops.simplify(p)

    changed = []
    for ch, op, base, band in recipes(italic):
        if op != "attach" or band[1]:
            continue
        scales = [min(abs(sx), abs(sy)) for piece, _, _, (sx, sy, *_) in band[2]
                  if piece not in ("rect", "line", "poly", "counter", "curl")]
        if not scales or min(scales) >= 0.8:
            continue
        name, base = resolve(ch), resolve(base)
        if name not in source or name not in font or base not in source:
            continue
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        k = min(scales)
        mine = path(source, name, deslant)
        added = mine
        dx = 0
        if source[base].contours or source[base].components:
            _, dx, _ = compare(Outline(source, base, deslant), Outline(source, name, deslant))
            added = pathops.op(mine, path(source, base, (1, 0, -SLANT, 1, dx, 0)), pathops.PathOp.DIFFERENCE)
        if italic and name in ("uni026C", "uniA7AD"):
            from l_belt import attachment_band

            low, high = attachment_band(name)
            # Joined belts can carry a thin base-rounding sliver into the
            # same contour as the real piece. Do not embolden that sliver
            # into an extra stem or an ascender extension.
            added = pathops.op(added, derive.rect_path(-derive.BIG, low, derive.BIG, high),
                               pathops.PathOp.INTERSECTION)
        # only the pieces the recipe added: where the source letter's edge
        # strays a unit from its base's (the Italic's), slivers are left
        kept = pathops.Path()
        for c in added.contours:
            if abs(c.area) >= MIN_PIECE:
                c.draw(kept.getPen())
        rec = RecordingPen()
        kept.draw(TransformPen(rec, (KX, 0, 0, 1, 0, 0)))
        heavier = embolden(rec, AX * k, AY)
        out = pathops.Path()
        heavier.draw(TransformPen(out.getPen(), (1, 0, 0, 1, AX / 2, 0)))
        if source[base].contours or source[base].components:
            b = path(font, base, (1, 0, -SLANT, 1, dx * KX, 0))
            out = pathops.op(pathops.simplify(out), b, pathops.PathOp.UNION)
            # the union holds all of the base, or it failed: left as it was
            if compare(Outline(None, None, path=b), Outline(None, None, path=out))[0]["lost"] > 0.01:
                continue
        glyph = ufoLib2.objects.Glyph()
        pathops.simplify(out).draw(TransformPen(glyph.getPen(), (1, 0, SLANT, 1, 0, 0)))
        redraw(font[name], glyph)
        changed.append(name)
    return changed


def small_cap_stems(up, glyph):
    """A small cap made from its capital (derive.enlarge: all its strokes
    brought to o.sc's round by one amount), its stems to h.sc's: the Bold
    Italic's small-cap stems stand heavier against its rounds than its
    capitals' do (h.sc 304, o.sc 263; ƙ.sc ƥ.sc ƭ.sc ɠ.sc ɦ.sc came out
    255, 2026-10-27). Only a letter whose main stroke is a stem; its round
    strokes then reach the stem's weight, within the stroke check's band."""
    from derived import Outline
    from strokes import main_stroke, zone

    top = zone(up, "sc")
    stem = main_stroke(Outline(up, "h.sc"), top)[0]
    weight, straight = main_stroke(Outline(up, glyph.name), top)
    if not (weight and straight and stem and weight < stem):
        return
    ax = stem - weight
    rec = RecordingPen()
    glyph.draw(rec)
    out = embolden(rec, ax, 0)
    glyph.clearContours()
    out.draw(TransformPen(glyph.getPen(), (1, 0, 0, 1, ax / 2, 0)))  # its left side bearing kept
    glyph.width = round(glyph.width + ax)
    for a in glyph.anchors:
        a.x = round(a.x + ax / 2)


def fill_stem_notches(glyph, most=12):
    """glyph (in place) with the notches beside its vertical stems filled:
    a short straight run leaving the stem's edge back the way the edge came
    (a middle tilde whose underside dips below its join with the stem, ᵰ:
    9 units out, 21 down) closed along the edge, the stem running on to the
    run's far end. glyph_lint cleans it as a ledge, shrunk to its middle,
    and so pulled the stem's node aside (ᵰ's left stem leaned 5 units,
    2026-11-04). most: the furthest out the run reaches."""
    from glyph_lint import LEDGE

    for contour in glyph.contours:
        points = contour.points
        i = 0
        while i < len(points):
            n = len(points)
            a, prev = points[i], points[i - 1]
            j = next(k for k in range(i + 1, i + n) if points[k % n].type)
            b = points[j % n]
            run = [points[k % n] for k in range(i + 1, j)]
            # the run straight: its handles on the line from a to b
            straight = all(abs((q.x - a.x) * (b.y - a.y) - (q.y - a.y) * (b.x - a.x))
                           <= math.dist((a.x, a.y), (b.x, b.y)) for q in run)
            up = (a.y - prev.y) if prev.type and abs(prev.x - a.x) < 0.5 else 0
            if (a.type == "line" and up and straight and 0 < abs(b.x - a.x) <= most
                    and math.dist((a.x, a.y), (b.x, b.y)) < LEDGE and (b.y - a.y) * up < 0
                    and abs(b.y - a.y) > abs(b.x - a.x)):
                a.y = b.y
                b.x = a.x
                for k in sorted(range(i + 1, j + 1), reverse=True):
                    del points[k % n]
                i = 0
                continue
            i += 1


def drop_specks(glyph):
    """glyph (in place) without the specks a recipe's cut leaves apart from
    the letter (a corner of the Bold's wider serif outside the cut box, Ɲ's
    feet, Bulgarian ж's and ю's arms): outer contours under SPECK.
    Counters stay (a pinhole is judged as such)."""
    p = pathops.Path()
    glyph.draw(p.getPen())
    contours = list(pathops.simplify(p).contours)
    if len(contours) < 2:
        return
    outer = max(contours, key=lambda c: abs(c.area)).clockwise
    kept = [c for c in contours if c.clockwise != outer or abs(c.area) >= SPECK]
    if len(kept) == len(contours):
        return
    glyph.clearContours()
    pen = glyph.getPen()
    for c in kept:
        c.draw(pen)


def fill_pinholes(glyph, solid, font):
    """glyph (in place) with its pinholes filled where solid, the letter
    emboldened whole, has ink: counters under MIN_PIECE in a join the
    letter had solid (Bold Ɦ's ball over the serif it meets). One the
    emboldened letter has too, a curl closed on its stroke (ң), stays to
    be judged."""
    p = pathops.Path()
    glyph.draw(p.getPen())
    contours = list(pathops.simplify(p).contours)
    if len(contours) < 2:
        return
    outer = max(contours, key=lambda c: abs(c.area)).clockwise
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    ink, rec = pathops.Path(), DecomposingRecordingPen(font)
    solid.draw(rec)
    rec.replay(ink.getPen())
    ink = pathops.simplify(ink, fix_winding=True)
    holes = []
    for c in contours:
        if c.clockwise == outer or abs(c.area) >= MIN_PIECE:
            continue
        hole = pathops.Path()
        c.draw(hole.getPen())
        hole = pathops.op(pathops.simplify(hole, fix_winding=True), ink, pathops.PathOp.DIFFERENCE)
        if abs(hole.area) < 0.05 * abs(c.area):  # covered by the emboldened letter's ink
            holes.append(id(c))
    if not holes:
        return
    glyph.clearContours()
    pen = glyph.getPen()
    for c in contours:
        if id(c) not in holes:
            c.draw(pen)


def serif_top(font, name, pick):
    """Where the foot serif under a letter's first or last stem ends: the
    lowest height at which that stem is no wider than above (None: no foot
    serif)."""
    import derive

    stems = derive.stems_at(font, name, 300)
    if not stems:
        return None
    a, b = stems[0] if pick == "first" else stems[-1]
    for y in range(1, 200):  # above the baseline row (a sliver there in the Bold's d)
        runs = [r for r in derive.stems_at(font, name, y) if r[1] > a and r[0] < b]
        if runs and max(r[1] - r[0] for r in runs) <= 1.05 * (b - a):
            return y if y > 1 else None
    return None


def rederive(source, font, italic, whole):
    """Derived letters left emboldened whole because they cut their base (a
    hook replacing a stem's end, Ц's tail its foot) made again by their
    recipe (derive.py) from the Bold's own glyphs, in the upright frame: a
    Bold base and a Bold f-top hook, each at its weight, joined as in the
    Regular, where emboldened whole the joins thicken and open (ɓ's bowl
    meeting the stem). A recipe placed by the Regular's coordinates can miss
    in the Bold, so the new letter replaces the old only if it stays close
    to it (rows overlapping by IOU, the advance within WIDTH) and has no
    more outline faults (glyph_lint); else it is left as it was, the reason
    in whole updated. Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import copy

    import derive
    from derived import Outline, _best_iou, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from glyph_lint import lint_glyph

    iou, width = 0.85, 0.03
    keep = ITALIC_BOLD_KEEP_WHOLE if italic else BOLD_KEEP_WHOLE
    up = copy.deepcopy(font)
    if italic:
        from make_italic import XH, shear

        for g in up:
            shear(g, -SLANT)
    cmap = {u: g.name for g in up for u in g.unicodes}
    # what the recipes draw by number (a hook's stem, a curl), at the Bold's
    # stems and hairlines, not the source's
    (_, stem, hair), (_, stem0, hair0) = derive.strokes(up, "o"), derive.strokes(source, "o")
    scale = (stem / stem0, hair / hair0)
    if italic:
        # the Italic's recipes are tuned at lighter strokes than the Italic's
        # (make_italic.recipe_scale), here without the Italic's added
        # weight: the Bold Italic's descenders were chosen so (as heavy as
        # ȷ's); with it ң's curl closes on its stroke
        from make_italic import recipe_scale

        tuned = recipe_scale(stem0, hair0, weight=0)
        scale = (scale[0] * tuned[0], scale[1] * tuned[1])

    def resolve(c):
        return derive.resolve(cmap, c)

    def parts(f, g):
        """the outer contours, not the counters (ɯ.sc's closed counter is
        no remnant; simplified, the outer ones all wind like the largest),
        and the pinholes: counters under MIN_PIECE, where a curl closed on
        its stroke (ң emboldened whole)"""
        p = pathops.Path()
        rec = DecomposingRecordingPen(f)
        g.draw(rec)
        rec.replay(p.getPen())
        contours = list(pathops.simplify(p).contours)
        if not contours:
            return 0, 0
        outer = max(contours, key=lambda c: abs(c.area)).clockwise
        return (sum(c.clockwise == outer for c in contours),
                sum(c.clockwise != outer and abs(c.area) < MIN_PIECE for c in contours))

    changed = []
    for ch, op, base, band in recipes(italic):
        name = resolve(ch)
        why = whole.get(name, "")
        rebuild = ITALIC_BOLD_REBUILD if italic else BOLD_REBUILD
        # (only what the Italic made so: its ᵃ is the sloped roman's, its ⁺ ⁼
        # the roman's, not its own a + = made small)
        by_op = (italic and op in ITALIC_BOLD_REBUILD_OPS and name in source
                 and source[name].lib.get("org.myiadidot.italicSource") == "derived")
        if not why.endswith(("cuts its base", "does not keep its whole base")) and name not in rebuild and not by_op:
            continue
        own = ch in (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)
        if own:
            op, base, band = (ITALIC_BOLD_RECIPES if italic else BOLD_RECIPES)[ch]
            if isinstance(band, str):  # placed on the Bold's own glyphs
                band = {"fishhook_band": fishhook_band, "lezh_band": lezh_band}[band](up)
        up.lib[derive.STROKE_KEY] = (1, 1) if own else scale
        if name in keep:
            whole[name] = f"{op}: emboldened whole, made again from the Bold it misses ({keep[name]})"
            continue
        if len(base) == 1 or (derive.variant(base) and not base[0].isascii()):
            base = resolve(base)
        if base not in up:
            continue
        if op == "hook" and band[1].startswith("down"):
            # the stem cut where the source's foot serif ends: the Bold's
            # serif stands taller, cut there the hook took the serif's width
            # (ɭ's a ball as wide as its foot)
            sband, kind, pick, cut, *rest = band
            was, now = serif_top(source, base, pick), serif_top(up, base, pick)
            if was is not None and now is not None and was <= cut <= was + 15:
                band = (sband, kind, pick, cut + now - was, *rest)
        tmp = f"_rederived.{name}"
        order, cats = up.glyphOrder, dict(up.lib.get("public.openTypeCategories", {}))
        try:
            if italic:
                from make_italic import build_own

                # ɗ ɚ ɝ ʔ: the Italic's own constructions, from the Bold Italic's glyphs
                own_built = build_own(up, ch, op, base, band, tmp, resolve)
            new = up[tmp] if italic and own_built else derive.build(up, ch, op, base, band, tmp)
        except Exception as e:  # noqa: BLE001 (a recipe that does not run on the Bold: left whole)
            whole[name] = f"{op}: emboldened whole, its recipe fails on the Bold ({type(e).__name__})"
            continue
        finally:
            up.glyphOrder = order
            up.lib["public.openTypeCategories"] = cats
        if italic:
            from make_italic import ITALIC_JOINS

            joins = {**ITALIC_JOINS, **ITALIC_BOLD_JOINS}
            if ch in joins:  # as the Italic's, before it is judged
                derive.fair_joins(new, *joins[ch])
            from make_italic import ITALIC_CORNERS, ITALIC_RUNS, round_corner, straighten_run

            if ch in ITALIC_RUNS:  # as the Italic's (җ's descender into its c)
                straighten_run(new, *ITALIC_RUNS[ch])
            if ch in ITALIC_CORNERS:
                round_corner(new, *ITALIC_CORNERS[ch])
            from make_italic import SC_DRAFT_SIDES, SC_LEVEL_GAIN, capital_width, level_gain, uncrossed

            if name in SC_DRAFT_SIDES:
                # as the Italic makes them: uncrossed, the main stroke brought
                # to the capital's proportion (small_cap_stems took n.sc's
                # straight diagonal for a stem)
                uncrossed(up, tmp)
                # and its ink to h.sc's as the capital's to H's: the gain
                # widens the Bold Italic's serif ends too (thick here); twice,
                # so weight and width both settle
                for _ in range(2 if name in SC_LEVEL_GAIN else 0):
                    level_gain(up, tmp, *SC_LEVEL_GAIN[name])
                    capital_width(up, tmp, SC_LEVEL_GAIN[name][0])
            elif op == "enlarge" and name.endswith(".sc"):
                small_cap_stems(up, new)
        drop_specks(new)
        fill_pinholes(new, up[name], up)
        if op == "midtilde" and not italic:
            fill_stem_notches(new)
        # the steps and ledges where the recipe's piece meets the base, a
        # unit or two off: cleaned as the font is after (fix), not counted
        # as faults (the stroked bases, 2026-10-28: Ƴ ʄ ҳ)
        fix(up, [tmp])
        # the side bearings the source style gave the letter after its recipe
        # (the Regular's derive.SPACING, the Italic's ITALIC_SIDEBEARINGS):
        # the recipe's width alone has its hook counted in again
        if italic:
            from make_italic import ITALIC_SIDEBEARINGS as SOURCE_SPACING

            delta = SOURCE_SPACING.get(name)
        else:
            delta = derive.SPACING.get(ch)
        if delta:
            sidebearings(up, {tmp: delta})
        old = up[name]
        made, was = Outline(up, tmp), Outline(up, name)
        faults = len(lint_glyph(up, new)) - len(lint_glyph(up, old))
        # a part more than before: a remnant of what the cut should take (a
        # serif's end); a pinhole more or fewer
        (pn, hn), (po, ho) = parts(up, new), parts(up, old)
        faults += max(0, pn - po) + hn - ho
        close = made.bounds is not None and was.bounds is not None and _best_iou(made, was) >= iou
        if (name in rebuild or by_op) and faults <= 0:
            close, wide = True, by_op
        else:
            wide = abs(new.width - old.width) > width * old.width
        if close and wide and faults <= 0:
            # close to the letter but set otherwise (the recipe's spacing, not
            # the optical fit the emboldened letter got): the old side
            # bearings around the new outline
            (x0, _, x1, _), (o0, _, o1, _) = derive.ink_bounds(up, tmp), derive.ink_bounds(up, name)
            dx = round(o0 - x0)
            for contour in new.contours:
                for point in contour.points:
                    point.x += dx
            for anchor in new.anchors:
                anchor.x += dx
            new.width = round(old.width + (x1 - x0) - (o1 - o0))
            wide = False
        if not close or wide or faults > 0:
            if by_op and not why:
                # (a stroked letter the rebuild missed stays as stroked, no
                # letter emboldened whole)
                del up[tmp]
                continue
            whole[name] = (f"{op}: emboldened whole, made again from the Bold it "
                           + ("strays" if not close else "has faults" if faults > 0 else "changes its advance"))
            del up[tmp]
            continue
        glyph = ufoLib2.objects.Glyph()
        # slanted back as unslanted above (make_italic.shear, about half the
        # x-height): about the baseline, the ink stood SLANT * XH / 2 right;
        # its curves split where the slant sets them past their points, as
        # the emboldened letters' are (ɓ.sc's hook ran 80 units past)
        y0 = XH / 2 if italic else 0
        from make_italic import POINT_REPAIRS

        slant_back(new, glyph.getPen(), [(1, 0, SLANT, 1, -SLANT * y0, 0)],
                   italic and name not in POINT_REPAIRS)
        in_line(glyph, font[base])  # (the base's smooth joins kept so)
        if op == "bar" and new.width == font[base].width:
            # a bar on its whole base, set as it (ʉ on u): its accents where
            # the base has them (as emboldened, they stood 3 units left of
            # the ink made again)
            font[name].clearAnchors()
            for anchor in font[base].anchors:
                font[name].appendAnchor({"name": anchor.name, "x": anchor.x, "y": anchor.y})
        redraw(font[name], glyph)
        font[name].width = new.width
        # the recipes after it build on the letter made again, not the
        # emboldened one (ƈ.sc from Ƈ: the Italic's draft emboldened closed
        # its curl, 2026-10-27)
        redraw(up[name], new)
        up[name].width = new.width
        # its aliases as wide as it (ʛ, ɠ.sc)
        for g in font:
            if (len(g.components) == 1 and not g.contours and g.components[0].baseGlyph == name
                    and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
                g.width = up[g.name].width = font[name].width
        del up[tmp]
        whole.pop(name, None)
        changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("bold", nargs="?", default=str(ROOT / "sources/MyiaDidot-Bold.ufo"))
    ap.add_argument("--out", metavar="UFO", help="the whole run into a copy of BOLD, which stays as it is "
                    "(scratch_out.py; then smallcaps.py on it)")
    args = ap.parse_args()
    if args.out:
        from scratch_out import prepare

        args.bold = str(prepare(args.bold, args.out))
    global SLANT, AX, THIN, THICK
    from drawn import restore, saved, strip

    # the glyphs kept as drawn (drawn.py), as last saved: put back before
    # anything is derived from them, and again at the end
    kept = saved(args.bold)
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    # the source style's drawn marks are its own: this style keeps only
    # what it marked itself (kept, above; docs/claude/drawn.md, rule 5)
    strip(font)
    kern_clear.undo(font)  # the source's loosened pairs: this style finds its own
    angle = -(regular.info.italicAngle or 0)
    SLANT = math.tan(math.radians(angle))
    italic = bool(angle)
    if italic:
        AX, THIN, THICK = ITALIC_AX, ITALIC_THIN, ITALIC_THICK
        part_ff(font)
    nudge, extra = (ITALIC_ANCHOR_NUDGE, ITALIC_SIDEBEARINGS) if italic else (ANCHOR_NUDGE, BOLD_SIDEBEARINGS)
    by_weight = ITALIC_BOLD_BY_WEIGHT if italic else BOLD_BY_WEIGHT
    rounder_ones = ITALIC_BOLD_ROUNDER if italic else BOLD_ROUNDER
    fit_as_is = ITALIC_BOLD_FIT_AS_IS if italic else BOLD_FIT_AS_IS
    up, down = (1, 0, -SLANT, 1, 0, 0), (1, 0, SLANT, 1, 0, 0)  # deslant, slant again
    marks = {g.name for g in regular if mark_like(g)}
    # the paragraphos ⸏ ⸐ ⸑, rules under a line: a mark's weight and
    # advance, though they have one (fontbakery: base_has_width)
    marks |= {g.name for g in regular if g.unicode in (0x2E0F, 0x2E10, 0x2E11)}
    # a modifier symbol that is another sign as it is (꞉, the colon): that
    # sign, emboldened and widened with it, not an accent keeping its width
    marks -= {g.name for g in regular if g.name in marks and g.width and not g.contours
              and len(g.components) == 1 and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)
              and unicodedata.category(chr(g.unicode or 0x2C)) == "Sk"
              and not mark_like(regular[g.components[0].baseGlyph])}
    # what a combining mark is made of is an accent too (the spacing
    # ypogegrammeni ͺ is a modifier letter, but uni0345 is built on it)
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            marks.add(g.components[0].baseGlyph)
    # where each mark attaches: its own _ anchor, else the convention's 440
    # (spacing accents) or -440 (combining marks); offsets then move as the
    # anchors do, so a precomposed letter matches mark positioning
    centre = {}
    for name in marks:
        own = [a.x for a in regular[name].anchors if a.name.startswith("_")]
        centre[name] = own[0] if own else (440 if regular[name].width else -440)
    # a spacing accent attaches where the combining mark made of it does
    # (that mark's anchor, 880 to the right): the Greek ones are not at 440
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            c = g.components[0]
            own = [a.x for a in g.anchors if a.name.startswith("_")]
            if own and c.baseGlyph in marks and round(c.transformation[4]) == -880:
                centre[c.baseGlyph] = own[0] + 880

    # the composites the anchor rules make as they are: rebuilt in the Bold
    builder = Builder(regular)
    rule_made = set()
    for g in regular:
        if not g.components or g.contours or g.unicode is None:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = builder.recipe(g.unicode)
        except ValueError:
            continue
        mine = [(c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components]
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) == sorted(mine):  # in any order
            rule_made.add(g.name)

    small, small_scale = small_glyphs(regular, italic)
    fit = {}  # glyph: (left, right) side space to change, after emboldening by weight
    parted = []  # serifs kept apart (part_serifs)
    gapped = []  # gaps between facing serifs kept in proportion (keep_gaps)
    simple = []  # emboldened the rounder way (a slit otherwise)
    from make_italic import POINT_REPAIRS, SOURCE_KEY

    # the Bold Italic's letters emboldened by their strokes, all at once in
    # a pool (each about half a second); a glyph's own outline is looked up,
    # another (part_serifs' shortened serifs) drawn when asked
    def strokes_job(name, w, sc):
        gain = sc * ITALIC_BOLD_HEAVIER.get(name, 1.0)
        return (name, w.value, (ITALIC_AX * gain, AY, ITALIC_THIN * sc, ITALIC_THICK * sc,
                                ITALIC_HAIR * (sc if name in ITALIC_BOLD_HAIR_KEPT else gain), SLANT, SLIVER * sc * sc, ITALIC_BOLD_ROOTS.get(name, 0.0),
                                name in ITALIC_BOLD_SPLIT, ITALIC_BOLD_CAP_FREE.get(name, 0.0), ITALIC_BOLD_KNEES.get(name, ())))

    stroked, unstroked = {}, []
    cache = stroke_cache.Cache() if italic else None
    if italic:
        from concurrent.futures import ProcessPoolExecutor

        jobs = []
        for g in font:
            if g.contours and g.name not in marks and g.name not in ITALIC_BOLD_BY_POINTS:
                wide = RecordingPen()
                contours_only(g).replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                jobs.append(strokes_job(g.name, wide, small_scale if g.name in small else 1.0))
        # those stroked before with the same outline, arguments and code
        # come from the cache (stroke_cache: 9 of make generate's 11 minutes)
        done = cache.get(jobs)
        todo = [job for job in jobs if job[0] not in done]
        if todo:
            with ProcessPoolExecutor(JOBS) as pool:
                new = dict(pool.map(emboldened, todo, chunksize=8))
            cache.put(todo, new)
            done.update(new)
        if cache.db is not None:
            print(f"  emboldened by strokes: {len(jobs) - len(todo)} from the cache, {len(todo)} stroked")
        stroked = {repr(job[1]): done[job[0]] for job in jobs}

    def by_strokes(w, sc, name):
        """w (name's) emboldened by its strokes, a ufoLib2 Glyph (None: failed)"""
        if repr(w.value) in stroked:
            value = stroked[repr(w.value)]
        else:
            job = strokes_job(name, w, sc)
            kept = cache.get([job])
            if name in kept:
                value = kept[name]
            else:
                value = emboldened(job)[1]
                cache.put([job], {name: value})
        if value is None:
            return None
        glyph = ufoLib2.objects.Glyph()
        rec = RecordingPen()
        rec.value = value
        rec.replay(glyph.getPen())
        return glyph

    is_letter = classifier(font, 1, 1)  # the letters respace cuts (stroke_out's)
    stroke_out = {}
    for g in font:
        is_mark = g.name in marks
        if g.contours:
            rec = contours_only(g)
            if is_mark and not italic:
                redraw(g, embolden(rec, MARK_AX, MARK_AY))
            elif is_mark:
                flat = RecordingPen()
                rec.replay(TransformPen(flat, up))
                heavier = embolden(flat, MARK_AX, MARK_AY)
                sloped = ufoLib2.objects.Glyph()
                heavier.draw(TransformPen(sloped.getPen(), down))
                redraw(g, sloped)
            else:
                wide = RecordingPen()
                rec.replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                # thick strokes AX heavier in any direction, hairlines AY
                # (a node moved by the weight of the stroke it is on)
                # a letter or figure made small, as at its scale (ᵃ, ⁰, ª)
                sc = small_scale if g.name in small else 1.0

                def make(w, sc=sc, bends=g.name not in fit_as_is, name=g.name, strokes=True):
                    # the Bold Italic's by its strokes (stroke_bold), where
                    # that fails by weight
                    if italic and strokes and name not in ITALIC_BOLD_BY_POINTS:
                        drawn = by_strokes(w, sc, name)
                        if drawn is not None:
                            if name in ITALIC_BOLD_SMOOTH_COUNTER:
                                drawn = smooth_counter(drawn, ITALIC_BOLD_SMOOTH_COUNTER[name])
                            return bridge(rezone(drawn, AY))
                        unstroked.append(name)
                    # short edges running on into a curve weighed as it in
                    # the Bold (ƒ)
                    return bridge(rezone(embolden_by_weight(w, AX * sc, AY, THIN * sc, THICK * sc,
                                                            runs_on=not italic,
                                                            keep_bends=bends),
                                         AY))

                bold = make(wide)
                # (a slashed round as its round: by weight, ring and slash apart)
                if g.name in rounder_ones or (g.name not in by_weight and g.name not in SLASHED
                                              and slit(bold, regular[g.name], regular)):
                    # parts close to each other (x's inner serifs) closed to a
                    # slit: the rounder emboldening, which leaves them apart,
                    # where it has fewer faults (a thin arch springing from a
                    # thick stem, the italic n's, is a narrow crotch either way)
                    def rounder(w, sc=sc):
                        # smooth nodes kept smooth in the Bold (φ); the Bold
                        # Italic's rounder letters not yet reviewed so
                        return rezone(embolden_simple(w, AX * sc, AY, weighted=True, keep_smooth=not italic, thin=THIN * sc,
                                                      thick=THICK * sc), AY)

                    alt = rounder(wide)
                    if g.name in rounder_ones or faults(alt, regular) < faults(bold, regular):
                        make, bold = rounder, alt
                        simple.append(g.name)
                bold, n = part_serifs(wide, bold, make)
                if n:
                    parted.append(g.name)
                elif not italic:
                    bold, n = keep_gaps(wide, bold, make)
                    if n:
                        gapped.append(g.name)
                refit = (italic_counter if italic else oval) if g.name in (ITALIC_OVALS if italic else OVALS) else None
                if refit:
                    bold = refit(wide, bold)
                if italic and g.name in italic_inside.RUNS:
                    bold = inside_from(wide, bold, g.name)
                if g.name in SLASHED:
                    ring = RecordingPen()
                    contours_only(regular[SLASHED[g.name]]).replay(
                        TransformPen(TransformPen(ring, (KX, 0, 0, 1, 0, 0)), up))
                    round_ = SLASHED[g.name]
                    bold = slashed(wide, ring, make,
                                   (italic_counter if italic else oval) if round_ in (ITALIC_OVALS if italic else OVALS) else None,
                                   functools.partial(make, strokes=False))
                # each side's ink grew by the weight of the stroke there, not
                # as the earlier emboldening grew it (every side AX / 2, its
                # convex corners up to twice that: a serif's tip): the side
                # space set after this loop so that the outermost ink stands
                # where that emboldening put it, the spacing and kerning tuned
                # on it kept (N's hairline sides would gain AX / 2 of white,
                # the italic H's shorter serifs 23 units a side)
                ref = bridge(rezone(embolden(wide, AX, AY), AY))
                if ((g.name in rounder_ones and (italic or g.name not in BOLD_REFERENCE_BY_WEIGHT))
                        or (g.name in (ITALIC_REFERENCE_ROUNDER if italic else BOLD_REFERENCE_ROUNDER))
                        or (g.name not in by_weight and slit(ref, regular[g.name], regular))):
                    ref = rezone(embolden_simple(wide, AX, AY), AY)
                # judged optically (the white beside the ink across the band,
                # as the figures are spaced): a thin stroke end that no longer
                # grows (the italic f's bar, r's arm, s's and e's terminals)
                # leaves white even where the outermost ink stays
                d = optical_fit(bold_rec(ref), bold_rec(bold), band_height(regular, g.name))
                if (italic and g.name not in ITALIC_BOLD_BY_POINTS and g.name not in simple
                        and g.name not in unstroked):
                    # by strokes spaced as by weight (the stems stand where it
                    # put them): fitted to the stroked letter's own white, the
                    # thinner entries and exits drew the letters some 23 units
                    # closer, minimum blacker (2026-10-28)
                    weighted = bridge(rezone(embolden_by_weight(wide, AX * sc, AY, THIN * sc, THICK * sc,
                                                                keep_bends=g.name not in fit_as_is), AY))
                    d = optical_fit(bold_rec(ref), bold_rec(weighted), band_height(regular, g.name))
                    # but never closer than by weight: where the strokes put
                    # ink further out (the rounds, 5-9 % heavier, gained
                    # outward too: O O 0.75 of H H, references 0.87-0.95,
                    # 2026-11-05), that side gets it back; thinner ends,
                    # which leave white, keep the by-weight side. Added with
                    # the other side bearings once the letters made of these
                    # are drawn: the recipes cut and attach at fixed points of
                    # their base's frame (Ƈ's hook moved 9 units onto C)
                    if d and is_letter(g.name):
                        out = optical_fit(bold_rec(weighted), bold_rec(bold), band_height(regular, g.name))
                        out = out and tuple(b if b >= STROKE_OUT_MIN else 0 for b in out)
                        if out and any(out):
                            stroke_out[g.name] = out
                if d:
                    if italic and g.name in ITALIC_FIT_CORRECTIONS:
                        adjustment = ITALIC_FIT_CORRECTIONS[g.name]
                        d = tuple(a + b for a, b in zip(d, adjustment))
                    fit[g.name] = d
                moved = ufoLib2.objects.Glyph()
                # the Italic's slanted letters (its derived ones, sloped
                # romans, small-cap drafts) split at their extremes there:
                # again here, where emboldened upright they move off them
                # (Old Standard's own, and the repairs matching exact
                # points, as they come)
                split = (italic and g.name not in POINT_REPAIRS and regular[g.name].lib.get(SOURCE_KEY)
                         in ("derived", "sloped roman", "small cap draft"))
                slant_back(bold, moved.getPen(), [(1, 0, 0, 1, AX / 2, 0), down], split)
                redraw(g, moved)
        if not is_mark:
            # the Regular's offsets, before any is changed below
            bases = [(c.baseGlyph, c.transformation[4], c.transformation[5])
                     for c in g.components if c.baseGlyph not in marks]
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                if c.baseGlyph in marks:
                    # the mark moves as the point it hangs on moves: the
                    # anchor of the base letter it sits on (nearest to it)
                    x, x_bold = attach_point(regular, c, bases, centre)
                    dx = dx + x_bold - x
                else:
                    dx = tx_offset(dx, dy)
                c.transformation = (xx, xy, yx, yy, round(dx), dy)
            for a in g.anchors:
                a.x = round(tx(a.x, a.y)) + nudge.get((g.name, a.name), 0)
            room = [(b, dx) for b, dx, _ in bases if dx]
            if len(bases) == 1 and room and g.width == regular[room[0][0]].width + room[0][1]:
                # a capital given room on its left for its accent (Ἤ; less
                # than none in the italic's Ἀ): as wide as the base plus that
                # room, rounded as the positioning rule is
                b, dx = room[0]
                g.width = round(regular[b].width * KX + AX) + round(dx * KX)
            elif g.width:
                g.width = round(g.width * KX + AX)

    # the side space emboldening by weight did not take (composites and
    # aliases carried along, their marks with them); a composite of one
    # letter placed anywhere (Έ: Ε given room for its accent) changes as
    # its letter does, as the decomposed form will (NFC and NFD alike)
    grown = True
    while grown:
        grown = False
        for g in font:
            if g.name in fit or g.contours or not g.components:
                continue
            letters = [c.baseGlyph for c in g.components if c.baseGlyph not in marks]
            if len(letters) == 1 and letters[0] in fit:
                fit[g.name] = fit[letters[0]]
                grown = True
    # a slashed round spaced as its round (the Regular's Ø is as wide as O,
    # its ring where O's is): the slash is not fitted
    for name, ring in SLASHED.items():
        fit[name] = fit.get(ring, (0, 0))
    sidebearings(font, {n: d for n, d in fit.items() if d != (0, 0)})
    if italic:
        from italic_contours import finish_bases

        finish_bases(font)
        # (r's shoulders not rounded after: the by-weight r's stepped arch
        # and return, the stroked r has neither)
    else:
        from r_hook import fair_bold_stem

        fair_bold_stem(font, bold=True)  # (the font still named Regular)
        from stem_handles import fair

        fair(font, bold=True)  # curves into a stem kept off its edge (n m u J Œ ...)
    whole = {}
    restore(kept, font, spaced=True)
    # (Ⱳ by strokes keeps its W; joined to it, the curl's join tangled)
    followed = follow_bases(regular, font, italic, whole=whole,
                            skip=set(ITALIC_BOLD_UNJOINED if italic else ()) | set(kept))
    followed += attached_small(regular, font, italic)
    followed += rederive(regular, font, italic, whole)
    restore(kept, font, spaced=True)
    if italic:
        # the joins the Italic faired, faired again (emboldened whole or
        # made again by the recipe)
        from derive import fair_joins
        from make_italic import ITALIC_JOINS

        cmap = {g.unicode: g.name for g in font if g.unicode is not None}
        for ch, band in {**ITALIC_JOINS, **ITALIC_BOLD_JOINS}.items():
            if ord(ch) in cmap and cmap[ord(ch)] not in kept:
                fair_joins(font[cmap[ord(ch)]], *band)
    font.lib[WHOLE_KEY] = {n: why for n, why in sorted(whole.items()) if n not in followed}

    font.kerning = {pair: round(v * KX) for pair, v in font.kerning.items()}
    if not italic:  # the Bold Italic's after its Latin pairs are computed (below)
        font.kerning.update(BOLD_KERNING)
    # hand-set positioning (room for the accents of Greek capitals, ...):
    # horizontal placement and advance scale with the outlines
    font.features.text = re.sub(
        r"<(-?\d+) (-?\d+) (-?\d+) (-?\d+)>",
        lambda m: f"<{round(int(m[1]) * KX)} {m[2]} {round(int(m[3]) * KX)} {m[4]}>",
        font.features.text)

    info = font.info
    info.styleName = "Bold Italic" if italic else "Bold"
    info.styleMapStyleName = "bold italic" if italic else "bold"
    info.openTypeOS2WeightClass = 700
    info.postscriptFontName = "MyiaDidot-BoldItalic" if italic else "MyiaDidot-Bold"
    info.postscriptFullName = "Myia Didot Bold Italic" if italic else "Myia Didot Bold"
    # USE_TYPO_METRICS (bit 7) kept, as in the Regular: without it Word spaces
    # the Bold's lines by the win metrics, 11% looser; ufo2ft sets the
    # bold, italic and regular bits from styleMapStyleName
    info.openTypeOS2Selection = list(info.openTypeOS2Selection or [])

    # the dots round again, as the source style's (emboldening widens them
    # three times as much as it heightens them); before y's dot below is
    # placed and the composites and recipes take them
    from bold_dots import finish as round_dots

    round_dots(font)
    if italic:
        from y_dot import y_dot_anchor

        y_dot_anchor(font)
    log = []
    stack_anchors(font, log)
    bold_builder = Builder(font)
    rebuilt = 0
    for name in sorted(rule_made - set(kept)):
        g = font[name]
        r = bold_builder.recipe(g.unicode)
        r.name = name
        lib = dict(g.lib)
        del font[name]
        bold_builder.write(r)
        font[name].lib.update(lib)
        rebuilt += 1
    # letters drawn with their accent in one outline (Ť, Ǫ): in the Bold their
    # accent would be thickened like a letter; made from base and mark like
    # the decomposed text, unless the Regular already renders them apart
    exceptions = {line.split()[0] for line in (ROOT / "tests/data/nfd-exceptions.txt").read_text().splitlines()
                  if line.startswith("U+")}
    outlined = 0
    for g in list(font):
        if g.unicode is None or not g.contours or g.components or f"U+{g.unicode:04X}" in exceptions:
            continue
        if g.name in SPECIAL or g.name in kept:  # upstream's deliberate designs (Ǻ), ours (drawn.py)
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = bold_builder.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = g.name, dict(g.lib)
        del font[g.name]
        bold_builder.write(r)
        font[r.name].lib.update(lib)
        outlined += 1
    # what emboldening leaves: counters closed to pinholes, outlines crossing
    # themselves (glyph_lint)
    cleaned = fix(font)
    greek_cut = BOLD_ITALIC_CUT_GREEK - ITALIC_LOOSER if italic else BOLD_CUT_GREEK
    cut = BOLD_ITALIC_CUT if italic else BOLD_CUT
    respace(font, classifier(font, cut, greek_cut))
    respace(font, lambda n: BOLD_FIGURE_CUT if n in FIGURE_NAMES else 0)
    tabular_figures(font)
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)
    # a composite follows its base (sidebearings), as the letters made of one;
    # also one set off for its accent (Έ Ἐ Ῥ: the letter at an offset, the
    # mark before it), else it would stand narrower than its NFD
    if italic:
        # the capital rounds' white beyond what the strokes gave back (2026-11-08)
        for n, side in ITALIC_CAPITAL_ROUNDS.items():
            stroke_out[n] = tuple(a + b for a, b in zip(stroke_out.get(n, (0, 0)), side))
    stroke_out = {n: v for n, v in stroke_out.items() if n in font and not font[n].components}
    grown = True
    while grown:
        grown = False
        for g in font:
            if g.name in stroke_out or g.contours or not g.components:
                continue
            bases = [c.baseGlyph for c in g.components if c.baseGlyph in stroke_out]
            if len(bases) == 1 and all(c.baseGlyph in stroke_out or c.baseGlyph in marks for c in g.components):
                stroke_out[g.name] = stroke_out[bases[0]]
                grown = True
    if STROKE_OUT_LOG is not None:
        Path(STROKE_OUT_LOG).write_text("".join(f"{n} {a} {b}\n" for n, (a, b) in stroke_out.items()))
    sidebearings(font, {n: tuple(a + b for a, b in zip(extra.get(n, (0, 0)), stroke_out.get(n, (0, 0))))
                        for n in set(extra) | set(stroke_out)})
    done = regular.lib.get(CUT_KEY, {"cut": 0, "greekLower": 0})
    font.lib[CUT_KEY] = {"cut": round(done["cut"] * KX) + cut,
                         "greekLower": round(done["greekLower"] * KX) + greek_cut}
    case_forms.make(font)  # punctuation raised onto the capitals (case), on the final widths
    if italic:
        from cyrillic_signs import redraw as redraw_cyrillic_signs
        from italic_contours import finish as finish_contours

        redraw_cyrillic_signs(font)
        finish_contours(font)
        # Serbian ѓ: its acute stacked over ī's bar as this style's ḗ,
        # rebuilt from anchors above, stacks it (carried along from the
        # Italic, it kept the Italic's step)
        from make_italic import serbian_bars, serbian_gje

        if "uni0453.loclSRB" in font and "uni0453.loclSRB" not in kept:
            serbian_gje(font)
        # п т: their bars over и ш as this style's ū has its own
        if not {"uni043F.loclSRB", "uni0442.loclSRB"} & set(kept):
            serbian_bars(font)
        # the Latin pairs from the white the finished shapes leave, against
        # the Bold as the Italic's against the Regular (italic_kerning.py,
        # docs/claude/spacing.md), without the Bold's own exceptions; the
        # others stay the Italic's scaled; then the reviewed exceptions
        from italic_kerning import apply as italic_kerning

        # beside the Italic read (make generate: sources/; check_reproducible: its snapshot)
        upright = Path(args.regular).with_name(Path(args.regular).name.replace("Italic", "Bold"))
        if args.out and not upright.exists():
            # a trial Italic in scratch with no trial Bold beside it: the
            # committed Bold (make only STYLE=BoldItalic SOURCE=...)
            upright = ROOT / "sources" / upright.name
            print(f"{args.bold}: no Bold beside {args.regular}, kerned against {upright}")
        kerned = italic_kerning(ufoLib2.Font.open(upright), font, skip=set(BOLD_KERNING))
        print(f"{args.bold}: {kerned[0]} Latin pairs computed against {upright.name} ({kerned[1]} set plain, at 0)")
        font.kerning.update(ITALIC_BOLD_KERNING)
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.bold), separate_stacks=True, kept=kept)
    if parted:
        print("  serifs kept apart:", " ".join(parted))
    if gapped:
        print("  serif gaps kept in proportion:", " ".join(gapped))
    if unstroked:
        print("  emboldened by weight (by strokes failed):", " ".join(sorted(set(unstroked))))
    if simple:
        print("  emboldened the rounder way (embolden_simple; a slit otherwise):", " ".join(simple))
    print(f"{args.bold}: {len(font)} glyphs, {rebuilt} composites rebuilt from anchors, "
          f"{outlined} outlined letters made from base and mark, {len(followed)} derived letters "
          f"made of their Bold base, {len(cleaned)} cleaned")


if __name__ == "__main__":
    main()
