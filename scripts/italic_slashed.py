#!/usr/bin/env python3
"""RECORD, not part of the build (TODO.md T7, 2026-11-27): run once, what
it made was kept in the UFO where accepted (in a generated style marked
drawn); no generator, Makefile target or test calls it. Kept to show how those glyphs were made; do not run it again
on sources/ (it would redo what was since reviewed or drawn over).

Phase 6, step B's loose end: the Italic's slashed rounds (Ø ø) on the
widened O and o (docs/claude/italic.md, "What followed").

    python scripts/italic_slashed.py SRC.ufo OLD.ufo OUT.ufo [--install --date D --review DOC]

Ø and ø are single outlines, the slash merged into the ring, redrawn by
hand (phase 5), so italic_bowls.py cannot widen them. Here each is its
ring as it now stands (SRC's O, o: widened) joined to its slash as OLD
(the UFO before step B) had it: the slash is what OLD's Ø has beyond OLD's
O, taken whole as the hull of its straight edges (as make_bold.slashed does), its upper
right end moved by what the ring grew, its lower left end where it was.
The advance is the ring's.

OUT.ufo is a copy of SRC with the two glyphs replaced (and, without
--install, nothing else changed). With --install SRC itself is written and
the glyphs marked drawn. ø.sc and the composites are not made here: they
follow their bases (smallcaps.py, composites.py).
"""

import argparse
import copy
import math
import shutil
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen

sys.path.insert(0, str(Path(__file__).resolve().parent))

import redraw as R  # noqa: E402

PAIRS = {"Oslash": "O", "oslash": "o"}


def path_of(glyph):
    p = pathops.Path()
    glyph.draw(p.getPen())
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


def slash_points(wide, ring):
    """The ends of the slash: what wide has beyond ring, the points of its
    straight edges longer than 50 units."""
    rest = RecordingPen()
    pathops.op(path_of(wide), path_of(ring), pathops.PathOp.DIFFERENCE).draw(rest)
    pts = set()
    for c in contours(rest):
        start = cur = c[0][1][0]
        for op, ps in c[1:]:
            end = ps[-1] if ps else start
            if op in ("lineTo", "closePath") and math.dist(cur, end) > 50:
                pts |= {cur, end}
            cur = end
    return sorted(pts)


def hull(pts):
    def half(seq):
        h = []
        for p in seq:
            while len(h) > 1 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                  - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]

    pts = sorted(pts)
    return half(pts) + half(pts[::-1])


def slashed(old_wide, old_ring, new_ring):
    pts = slash_points(old_wide, old_ring)
    # the slash is a straight bar of one thickness: its axis from the farthest
    # apart two points, its thickness across, its ends cut square. Moved as a
    # bar (the upper end by what the ring grew), never point by point: the
    # points on its two edges would give it a thicker or thinner middle
    p0, p1 = max(((p, q) for p in pts for q in pts), key=lambda pq: math.dist(*pq))
    d = ((p1[0] - p0[0]) / math.dist(p0, p1), (p1[1] - p0[1]) / math.dist(p0, p1))
    for _ in range(3):  # the corners' diagonal is a little off the axis: settled by its own ends
        n = (-d[1], d[0])
        along = [x * d[0] + y * d[1] for x, y in pts]
        across = [x * n[0] + y * n[1] for x, y in pts]
        lo, hi = min(along), max(along)
        # the two end cuts, each the points within 15 units of its end: the slash's
        # thickness is the cut's length (the points between lie on the ring's edges)
        cut_lo = [c for t, c in zip(along, across) if t < lo + 15]
        cut_hi = [c for t, c in zip(along, across) if t > hi - 15]
        half = (max(cut_lo) - min(cut_lo)) / 2
        mid_lo = (max(cut_lo) + min(cut_lo)) / 2
        mid_hi = (max(cut_hi) + min(cut_hi)) / 2
        a_ = (lo * d[0] + mid_lo * n[0], lo * d[1] + mid_lo * n[1])
        b_ = (hi * d[0] + mid_hi * n[0], hi * d[1] + mid_hi * n[1])
        d = ((b_[0] - a_[0]) / math.dist(a_, b_), (b_[1] - a_[1]) / math.dist(a_, b_))

    if a_[0] > b_[0]:
        a_, b_ = b_, a_
    # the slash keeps its angle and its place on the ring: across the middle of
    # the ring as it was, so across the middle of the ring as it is (a bar kept
    # at the lower end and moved at the upper turned flatter, and met the
    # counters at other angles than the ones the letter was drawn with), its
    # ends as far beyond the ring's edge as they were
    def inside(ring, pt):
        pen = PointInsidePen(None, pt)
        ring.draw(pen)
        return pen.getResult()

    def exits(ring, a, b):
        """the first and last place on the line a-b inside ring, by walking it"""
        n_ = 2000
        ts = [i / n_ for i in range(-n_, 2 * n_ + 1)]
        ins = [t for t in ts if inside(ring, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))]
        return ins[0], ins[-1]

    t_old = exits(old_ring, a_, b_)
    bb_old, bb_new = old_ring.getBounds(None), new_ring.getBounds(None)
    shift = ((bb_new.xMin + bb_new.xMax) - (bb_old.xMin + bb_old.xMax)) / 2
    a2, b2 = (a_[0] + shift, a_[1]), (b_[0] + shift, b_[1])
    t_new = exits(new_ring, a2, b2)
    t0, t1 = t_new[0] - t_old[0], t_new[1] + (1 - t_old[1])

    def at(t):
        return (a2[0] + t * (b2[0] - a2[0]), a2[1] + t * (b2[1] - a2[1]))

    a_, b_ = at(t0), at(t1)
    L = math.dist(a_, b_)
    dn = ((b_[0] - a_[0]) / L, (b_[1] - a_[1]) / L)
    nn = (-dn[1], dn[0])
    # the ends' corners as high and as low as they were (Ø's top corner 1473, ø's
    # 884: a bar that reaches further runs into the accents and past the zones)
    lo_c = min(a_[1] + s * half * nn[1] for s in (1, -1))
    hi_c = max(b_[1] + s * half * nn[1] for s in (1, -1))
    d_lo = (min(y for _, y in pts) - lo_c) / dn[1]
    d_hi = (max(y for _, y in pts) - hi_c) / dn[1]
    a_ = (a_[0] + d_lo * dn[0], a_[1] + d_lo * dn[1])
    b_ = (b_[0] + d_hi * dn[0], b_[1] + d_hi * dn[1])
    h = [(a_[0] + s * half * nn[0], a_[1] + s * half * nn[1]) for s in (1, -1)]
    h += [(b_[0] + s * half * nn[0], b_[1] + s * half * nn[1]) for s in (-1, 1)]
    bar = RecordingPen()
    bar.moveTo(h[0])
    for p in h[1:]:
        bar.lineTo(p)
    bar.closePath()
    bp = pathops.Path()
    bar.replay(bp.getPen())
    rec = RecordingPen()
    pathops.op(path_of(new_ring), bp, pathops.PathOp.UNION).draw(rec)
    before = RecordingPen()
    new_ring.draw(before)
    out = ufoLib2.objects.Glyph()
    pen = out.getPen()
    if (max(map(area, contours(rec)), key=abs) > 0) != (max(map(area, contours(before)), key=abs) > 0):
        pen = ReverseContourPen(pen)
    rec.replay(pen)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("old")
    ap.add_argument("out")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--review")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review")
    src = ufoLib2.Font.open(a.src)
    old = ufoLib2.Font.open(a.old)
    if not a.install:
        if Path(a.out).exists():
            shutil.rmtree(a.out)
        shutil.copytree(a.src, a.out)
    target = src if a.install else ufoLib2.Font.open(a.out)
    failed = 0
    for name, ring in PAIRS.items():
        raw = slashed(old[name], old[ring], src[ring])
        raw.width = src[ring].width
        for tol in (R.TOL, 1.5, 1.0):
            new, rep = R.redraw(raw, tol, None)
            fail, look = R.gate(rep, None)
            if not fail:
                break
        # the union itself, not the redraw's refit of it: the counters' arcs are the
        # ring's own curves cut at the slash, so as smooth as the ring is; a refit
        # of them put a knee into the counter just past the slash (2026-11-18)
        new = raw
        new.width = raw.width
        print(f"{name:<8}tol {tol:g} {rep['nodes_before']:>3} -> {rep['nodes_after']:>3} nodes by the redraw (kept: the union, {sum(len(c.points) for c in raw.contours)} points)  "
              f"advance {src[name].width} -> {raw.width}  " + ("FAIL: " + "; ".join(fail) if fail else "candidate")
              + ("  [look: " + "; ".join(look) + "]" if look else ""))
        failed += bool(fail)
        g = target[name]
        g.clearContours()
        for c in new.contours:
            g.appendContour(c)
        g.clearAnchors()
        for an in src[ring].anchors:
            g.appendAnchor(copy.deepcopy(an))
        g.width = raw.width
        if a.install and not fail:
            R.install(target, name, new, a.date, a.review, rep)
            target[name].width = raw.width
            target[name].lib[R.KEY]["harmonise"] = "slashed"
    target.save(None if a.install else a.out, overwrite=True)


if __name__ == "__main__":
    main()
