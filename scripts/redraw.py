"""Redraw an outline onto a clean node structure: the shape kept, the nodes rebuilt.

    python scripts/redraw.py SRC.ufo OUT.ufo GLYPH ... [--tol 2] [--spec FILE] [--json FILE]
    python scripts/redraw.py SRC.ufo OUT.ufo GLYPH ... --install --date D --review DOC

Today's outline is the target; the structure is taken from the target's
own geometry, by the rules the Regular is drawn to:

  corner   where the target turns more than CORNER degrees at a node
           (a turn under that is a kink, meant smooth: it becomes smooth)
  line     the ends of a straight edge (one of SHORT_LINE units or less
           between two curves is a crotch's leftover and is closed)
  extreme  where a curve runs level or upright (true extremes, in the
           font's own frame, the slanted one for an italic), found on the
           curve, not taken from the old nodes
  extra    only where one cubic between two of the above leaves the
           target by more than the tolerance: at the inflection if the
           span has one, else at the old node nearest the worst place,
           else where the span has made half its turn

Between two nodes one cubic (or the line), its end directions given by the
nodes (level or upright at an extreme, the line's at a line's end, the
target's own at a corner or an extra node), its handle lengths by least
squares on the distance to the target. Nodes and handles land on whole
units; a handle off the axes is rounded to the whole point that keeps its
direction best, so a smooth node stays smooth.

The result is a candidate for review, written to OUT.ufo (never to
sources/ but with --install, after the review: the glyph's contours are
replaced in SRC.ufo, an Italic glyph marked "drawn" so that make_italic
keeps it, the redraw recorded in lib org.myiadidot.redrawn). Each glyph
gets a report (--json) and a verdict by `gate`: see docs/claude/redraw.md
for the method, the numbers and what goes back to the designer.

The node structure can be corrected per glyph in a spec file (JSON,
scripts/data/redraw-STYLE.json is read by default):

    {"g": {"extra": [[445, -372]], "drop": [[660, 659]], "corner": [],
           "smooth": [], "keep": [], "tol": 3}}

extra: a node at the target's point nearest to it; drop: the structure's
node nearest to it goes (within NEAR units); corner / smooth: the old node
nearest to it is taken as that, whatever its turn; keep: the short line
ending there (within 3 units) is not closed; tol: this glyph's tolerance.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))

CORNER = 8.0      # degrees: a node turning more is a corner (checks.py: 1-8 is a kink)
SHORT_LINE = 8.0  # units: a line this short between two curves is closed
BULGE = 5.0       # units: an extreme less than this beyond its neighbouring nodes gets no node (checks.py's extreme)
MIN_SPAN = 12.0   # units: no extreme this near a corner or a line's end
TOL = 2.0         # units: a cubic further from the target is split by an extra node
FINE = 1.0        # units: the tolerance of the shortest curves (span_tol)
WIDEN = 1.4       # the tolerance's factor when a redraw needs more nodes than the target has
DEPTH = 2         # how often a span may be split
NEAR = 15.0       # units: how far a spec's point may lie from what it names
DEV = 4.0         # units: the gate's limit for the redrawn outline against the target
JUMP = 0.5        # the gate's remark for a curvature jump at a smooth node (see curvature_jump)
S_TURN = 3.0      # degrees: a curve turning less than this the other way at one end bends twice by accident
K_FLAT = 1 / 1500  # curvature under which an edge counts as flat (radius over 1500 units)
FAIR_ROOM = 0.5   # of its tolerance: how much further a curve may go for one curvature at its ends
G2_WEIGHT = 10.0  # what a curvature jump of 1 costs, in units of deviation along both curves
KEY = "org.myiadidot.redrawn"
ITALIC_SOURCE_KEY = "org.myiadidot.italicSource"


def unit(v):
    n = math.hypot(v[0], v[1])
    return v / n if n > 1e-12 else v * 0.0


def cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def angle_between(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(unit(a) @ unit(b))))))


# ---- the target: segments, points, tangents

def segments(contour):
    """a closed contour's segments in order: arrays of 2 (line) or 4 (cubic) points"""
    P = list(contour.points)
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    if len(ons) < 2 or any(P[i].type not in ("line", "curve") for i in ons):
        raise ValueError("an open, quadratic or one-node contour is not redrawn")
    segs = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
        pts = np.array([(P[q].x, P[q].y) for q in (i, *offs, j)], float)
        if len(pts) not in (2, 4):
            raise ValueError("a curve with one handle is not redrawn")
        segs.append(pts)
    return segs


def point(seg, t):
    if len(seg) == 2:
        return seg[0] + (seg[1] - seg[0]) * t
    u = 1 - t
    return u ** 3 * seg[0] + 3 * u * u * t * seg[1] + 3 * u * t * t * seg[2] + t ** 3 * seg[3]


def deriv(seg, t):
    if len(seg) == 2:
        return seg[1] - seg[0]
    u = 1 - t
    return 3 * (u * u * (seg[1] - seg[0]) + 2 * u * t * (seg[2] - seg[1]) + t * t * (seg[3] - seg[2]))


def deriv2(seg, t):
    if len(seg) == 2:
        return np.zeros(2)
    return 6 * ((1 - t) * (seg[2] - 2 * seg[1] + seg[0]) + t * (seg[3] - 2 * seg[2] + seg[1]))


def tangent(seg, t):
    """the unit direction at t, also where a handle lies on its node"""
    d = deriv(seg, t)
    if math.hypot(*d) < 1e-6:
        d = deriv(seg, t + 1e-3 if t < 0.5 else t - 1e-3)
    if math.hypot(*d) < 1e-9:
        d = seg[-1] - seg[0]
    return unit(d)


def length(seg, t0=0.0, t1=1.0):
    ts = np.linspace(t0, t1, 17)
    pts = np.array([point(seg, t) for t in ts])
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def cleaned(segs, notes, keep=()):
    """segs without empty segments and without the short lines between two
    curves (their ends drawn together to the middle, on whole units); a
    line with an end within 3 units of a point in keep (the spec's) stays"""
    keep = [np.array(xy, float) for xy in keep]
    segs = [s.copy() for s in segs if np.linalg.norm(s[-1] - s[0]) > 1e-6 or len(s) == 4 and length(s) > 1e-6]
    while True:
        n = len(segs)
        for k, s in enumerate(segs):
            before, after = segs[k - 1], segs[(k + 1) % n]
            if any(min(np.linalg.norm(s[0] - xy), np.linalg.norm(s[1] - xy)) <= 3 for xy in keep):
                continue
            if len(s) == 2 and np.linalg.norm(s[1] - s[0]) <= SHORT_LINE and len(before) == 4 and len(after) == 4 and n > 3:
                mid = np.round((s[0] + s[1]) / 2)
                notes.append(f"line of {np.linalg.norm(s[1] - s[0]):.0f} units at {s[0][0]:.0f},{s[0][1]:.0f} closed")
                # a handle lying on the old end moves with it
                for seg, end, hand in ((before, 3, 2), (after, 0, 1)):
                    if np.allclose(seg[hand], seg[end]):
                        seg[hand] = mid
                    seg[end] = mid
                del segs[k]
                break
        else:
            return segs


class Break:
    """a node of the structure: at u = k + t on the target (segment k, parameter t)"""

    def __init__(self, u, at, kind, tin, tout, why=""):
        self.u, self.at, self.kind, self.tin, self.tout, self.why = u, np.array(at, float), kind, tin, tout, why

    def __repr__(self):
        return f"{self.kind}({self.at[0]:.0f},{self.at[1]:.0f})"


class Target:
    """one cleaned contour, its nodes classified"""

    def __init__(self, segs, spec=None):
        self.segs = segs
        self.n = n = len(segs)
        self.line = [len(s) == 2 for s in segs]
        spec = spec or {}
        self.turn = [angle_between(tangent(segs[k - 1], 1.0), tangent(segs[k], 0.0)) for k in range(n)]
        self.corner = [self.turn[k] > CORNER or (self.line[k - 1] and self.line[k]) for k in range(n)]
        for name, value in (("corner", True), ("smooth", False)):
            for xy in spec.get(name, []):
                k = min(range(n), key=lambda k: np.linalg.norm(segs[k][0] - np.array(xy, float)))
                if np.linalg.norm(segs[k][0] - np.array(xy, float)) > NEAR:
                    raise ValueError(f"spec {name} {xy}: no node within {NEAR:.0f} units")
                self.corner[k] = value

    def at(self, u):
        k = int(math.floor(u)) % self.n
        return point(self.segs[k], u - math.floor(u))

    def tangent(self, u):
        k = int(math.floor(u)) % self.n
        return tangent(self.segs[k], u - math.floor(u))

    def node_tangents(self, k):
        return tangent(self.segs[k - 1], 1.0), tangent(self.segs[k], 0.0)

    def between(self, ua, ub, step=2.0):
        """dense points of the target from ua to ub (ub after ua, around the contour)"""
        if ub <= ua + 1e-12:
            ub += self.n
        pts, u = [], ua
        while u < ub - 1e-12:
            k = int(math.floor(u + 1e-12))
            t0, t1 = u - k, min(ub, k + 1) - k
            seg = self.segs[k % self.n]
            m = max(6, int(length(seg, t0, t1) / step) + 1)
            pts += [point(seg, t) for t in np.linspace(t0, t1, m)[:-1]]
            u = k + t1
        pts.append(self.at(ub))
        return np.array(pts)

    def arc(self, ua, ub):
        return float(np.linalg.norm(np.diff(self.between(ua, ub), axis=0), axis=1).sum())

    def nearest(self, xy):
        """u of the target's point nearest to xy, and its distance"""
        xy = np.array(xy, float)
        best = (1e18, 0.0)
        for k, seg in enumerate(self.segs):
            for t in np.linspace(0, 1, 65)[:-1]:
                d = float(np.linalg.norm(point(seg, t) - xy))
                best = min(best, (d, k + t))
        return best[1], best[0]

    # -- the structure

    def extremes(self):
        """Breaks where a curve runs level or upright: the sign of the
        tangent's x or y changes, inside a curve or at a smooth node
        between two curves"""
        out = []
        M = 24
        ts = [(i + 0.5) / M for i in range(M)]
        for k in range(self.n):
            if self.line[k]:
                continue
            seg = self.segs[k]
            for axis in (0, 1):
                vals = [float(tangent(seg, t)[axis]) for t in ts]
                # inside the curve, between its first and last sample
                for i in range(M - 1):
                    if vals[i] * vals[i + 1] < 0:
                        out.append(self.extreme(k + self.root(seg, axis, ts[i], ts[i + 1]), axis))
                # its head: from the node to the first sample
                head = float(tangent(seg, 0.0)[axis])
                if abs(head) > 1e-6 and head * vals[0] < 0:
                    out.append(self.extreme(k + self.root(seg, axis, 0.0, ts[0]), axis))
                # its tail
                tail = float(tangent(seg, 1.0)[axis])
                if abs(tail) > 1e-6 and tail * vals[-1] < 0:
                    out.append(self.extreme(k + self.root(seg, axis, ts[-1], 1.0), axis))
                # at the node it starts from, if that joins two curves smoothly
                prev = self.segs[k - 1]
                if self.corner[k] or self.line[k - 1]:
                    continue
                before = float(tangent(prev, 1.0)[axis])
                b = before if abs(before) > 1e-6 else float(tangent(prev, ts[-1])[axis])
                a = head if abs(head) > 1e-6 else vals[0]
                if b * a < 0 and (abs(before) <= 1e-6 or abs(head) <= 1e-6 or before * head < 0):
                    out.append(self.extreme(float(k), axis))
        return out

    @staticmethod
    def root(seg, axis, lo, hi):
        flo = tangent(seg, lo)[axis]
        for _ in range(50):
            mid = (lo + hi) / 2
            f = tangent(seg, mid)[axis]
            if f * flo > 0:
                lo, flo = mid, f
            else:
                hi = mid
        return (lo + hi) / 2

    def extreme(self, u, axis):
        k = int(math.floor(u)) % self.n
        t = u - math.floor(u)
        # the direction of travel there, set on the axis
        if t < 1e-9:
            d = unit(tangent(self.segs[k - 1], 1.0) + tangent(self.segs[k], 0.0))
        else:
            d = tangent(self.segs[k], t)
        e = np.zeros(2)
        e[1 - axis] = math.copysign(1.0, d[1 - axis])
        return Break(u % self.n, self.at(u), "extreme", e, e, "level" if axis == 1 else "upright")

    def structure(self, spec=None, notes=None):
        spec, notes = spec or {}, notes if notes is not None else []
        fixed = []
        for k in range(self.n):
            tin, tout = self.node_tangents(k)
            if self.corner[k]:
                fixed.append(Break(float(k), self.segs[k][0], "corner", tin, tout))
                if 1 < self.turn[k] <= CORNER and not (self.line[k - 1] and self.line[k]):
                    notes.append(f"{self.segs[k][0][0]:.0f},{self.segs[k][0][1]:.0f} kept a corner by the spec")
            elif self.line[k - 1] or self.line[k]:
                d = tin if self.line[k - 1] else tout
                fixed.append(Break(float(k), self.segs[k][0], "line", d, d))
        for k in range(self.n):
            if not self.corner[k] and self.turn[k] > 1:
                notes.append(f"kink of {self.turn[k]:.1f} degrees at "
                             f"{self.segs[k][0][0]:.0f},{self.segs[k][0][1]:.0f} made smooth")
        breaks = list(fixed)
        for e in sorted(self.extremes(), key=lambda b: b.u):
            if any(min(self.arc(f.u, e.u), self.arc(e.u, f.u)) < MIN_SPAN for f in fixed):
                continue
            if any(b.kind == "extreme" and b.why == e.why and min(self.arc(b.u, e.u), self.arc(e.u, b.u)) < 1
                   for b in breaks):
                continue
            breaks.append(e)
        # an extreme the curve hardly passes (a bracket leaning over by the
        # slant) gets no node: under BULGE units beyond its neighbours
        while True:
            for i, e in enumerate(breaks := sorted(breaks, key=lambda b: b.u)):
                if e.kind != "extreme" or len(breaks) < 4:
                    continue
                a, b = breaks[i - 1], breaks[(i + 1) % len(breaks)]
                q = 0 if e.why == "upright" else 1
                lo, hi = sorted((a.at[q], b.at[q]))
                if lo - BULGE < e.at[q] < hi + BULGE:
                    notes.append(f"no node at the {e.why} extreme {e.at[0]:.0f},{e.at[1]:.0f}: "
                                 f"under {BULGE:g} units beyond its neighbours")
                    del breaks[i]
                    break
            else:
                break
        for xy in spec.get("drop", []):
            b = min(breaks, key=lambda b: np.linalg.norm(b.at - np.array(xy, float)))
            if np.linalg.norm(b.at - np.array(xy, float)) > NEAR:
                raise ValueError(f"spec drop {xy}: no node of the structure within {NEAR:.0f} units")
            breaks.remove(b)
        for xy in spec.get("extra", []):
            u, d = self.nearest(xy)
            if d > NEAR:
                raise ValueError(f"spec extra {xy}: the outline is {d:.0f} units away")
            breaks.append(self.extra(u, "spec"))
        return sorted(breaks, key=lambda b: b.u)

    def extra(self, u, why):
        k = int(math.floor(u)) % self.n
        if u - math.floor(u) < 1e-9:
            tin, tout = self.node_tangents(k)
            t = unit(tin + tout)
        else:
            t = self.tangent(u)
        return Break(u % self.n, self.at(u), "extra", t, t, why)

    def inflections(self, ua, ub):
        """us between ua and ub where the target's bend changes sides, with
        at least 4 degrees turned on either side of it"""
        if ub <= ua:
            ub += self.n
        us = []
        u = ua
        while u < ub - 1e-12:
            k = int(math.floor(u + 1e-12))
            t0, t1 = u - k, min(ub, k + 1) - k
            us += [k + t for t in np.linspace(t0, t1, 33)[:-1]]
            u = k + t1
        us.append(ub)
        tans = [self.tangent(x if x - math.floor(x) > 1e-9 or x == ua else x - 1e-9) for x in us]
        turns = [math.degrees(math.asin(max(-1, min(1, cross(tans[i], tans[i + 1]))))) for i in range(len(us) - 1)]
        total = np.concatenate([[0], np.cumsum(turns)])
        # the turning's inner peaks and troughs
        out = []
        for i in range(1, len(total) - 1):
            lo = total[:i + 1]
            hi = total[i:]
            if (total[i] - lo.min() >= 4 and total[i] - hi.min() >= 4 and total[i] >= total[i - 1]
                    and total[i] > total[i + 1]) or (
                    lo.max() - total[i] >= 4 and hi.max() - total[i] >= 4 and total[i] <= total[i - 1]
                    and total[i] < total[i + 1]):
                out.append(us[i])
        return out

    def split(self, a, b, where):
        """the Break to add between a and b, the fit worst at u = where"""
        ua, ub = a.u, b.u if b.u > a.u else b.u + self.n
        far = lambda u: self.arc(ua, u) >= MIN_SPAN and self.arc(u, ub) >= MIN_SPAN  # noqa: E731
        infl = [u for u in self.inflections(ua, ub) if far(u)]
        if infl:
            return self.extra(min(infl, key=lambda u: abs(u - where)), "inflection")
        nodes = [float(k) for k in range(int(math.floor(ua)) + 1, int(math.ceil(ub))) if far(k)]
        if nodes:
            return self.extra(min(nodes, key=lambda u: abs(u - where)), "old node")
        pts = self.between(ua, ub)
        tans = [unit(q - p) for p, q in zip(pts, pts[1:])]
        turned = np.cumsum([abs(math.degrees(math.asin(max(-1, min(1, cross(s, t)))))) for s, t in zip(tans, tans[1:])])
        if not len(turned) or turned[-1] < 1:
            return None
        i = int(np.searchsorted(turned, turned[-1] / 2)) + 1
        u, _d = self.nearest(pts[i])
        return self.extra(u, "half turn") if far(u) else None


# ---- the fit

def bezier(ctrl, ts):
    ts = np.asarray(ts, float)[:, None]
    u = 1 - ts
    return u ** 3 * ctrl[0] + 3 * u * u * ts * ctrl[1] + 3 * u * ts * ts * ctrl[2] + ts ** 3 * ctrl[3]


def polyline_distance(pts, line):
    """each of pts' distance to the polyline"""
    a, b = line[:-1], line[1:]
    ab = b - a
    den = np.maximum((ab * ab).sum(axis=1), 1e-12)
    t = np.clip(((pts[:, None, :] - a[None]) * ab[None]).sum(axis=2) / den[None], 0, 1)
    foot = a[None] + t[..., None] * ab[None]
    return np.linalg.norm(pts[:, None, :] - foot, axis=2).min(axis=1)


def deviation(ctrl, pts):
    """how far the cubic and the target's points lie apart (both ways), and
    the index of the target's worst point"""
    curve = bezier(ctrl, np.linspace(0, 1, 201))
    there = polyline_distance(pts, curve)
    back = polyline_distance(curve, pts)
    return float(max(there.max(), back.max())), int(there.argmax())


def feet(ctrl, pts, u):
    """each point's parameter on the cubic, a Newton step nearer its foot"""
    B = bezier(ctrl, u)
    uu = u[:, None]
    D1 = 3 * ((1 - uu) ** 2 * (ctrl[1] - ctrl[0]) + 2 * (1 - uu) * uu * (ctrl[2] - ctrl[1]) + uu ** 2 * (ctrl[3] - ctrl[2]))
    D2 = 6 * ((1 - uu) * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + uu * (ctrl[3] - 2 * ctrl[2] + ctrl[1]))
    num = ((B - pts) * D1).sum(axis=1)
    dd = (D1 * D1).sum(axis=1) + ((B - pts) * D2).sum(axis=1)
    ok = np.abs(dd) > 1e-9
    u = np.clip(u - np.where(ok, num / np.where(ok, dd, 1), 0), 0, 1)
    u[0], u[-1] = 0, 1
    return u


def handle_bounds(p0, t0, p3, t3):
    """(least, most a, most b) for the handle lengths: without an inflection
    between the ends the handles stay inside the triangle their directions make"""
    chord = float(np.linalg.norm(p3 - p0))
    amax = bmax = 2 * chord
    den = cross(t0, t3)
    if abs(den) > 1e-6:
        sa, sb = cross(p3 - p0, t3) / den, cross(p3 - p0, t0) / den
        if sa > 0 and sb > 0:  # the directions meet ahead of both ends: one bend
            amax, bmax = sa, sb
    return 0.02 * chord, amax, bmax


def fit_cubic(pts, p0, t0, p3, t3):
    """the cubic from p0 (leaving along t0) to p3 (arriving along t3) nearest
    to pts: handle lengths by least squares, the points' parameters found
    again by Newton steps (Schneider). Without an inflection between the
    ends the handles stay inside the triangle their directions make."""
    chord = float(np.linalg.norm(p3 - p0))
    if chord < 1e-6:
        return np.array([p0, p0, p3, p3]), 0.0
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    u = d / d[-1] if d[-1] > 0 else np.linspace(0, 1, len(pts))
    lo, amax, bmax = handle_bounds(p0, t0, p3, t3)
    la = lb = chord / 3

    def solve(u):
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        A1, A2 = b1[:, None] * t0, -b2[:, None] * t3
        R = pts - (b0 + b1)[:, None] * p0 - (b2 + b3)[:, None] * p3
        m11, m12, m22 = np.sum(A1 * A1), np.sum(A1 * A2), np.sum(A2 * A2)
        r1, r2 = np.sum(A1 * R), np.sum(A2 * R)
        det = m11 * m22 - m12 * m12
        if abs(det) < 1e-9:
            return None
        a, b = (r1 * m22 - r2 * m12) / det, (r2 * m11 - r1 * m12) / det
        if not (lo <= a <= amax and lo <= b <= bmax):  # at a bound: the other alone
            a = min(max(a, lo), amax)
            b = min(max((r2 - m12 * a) / m22 if m22 > 1e-9 else b, lo), bmax)
            a = min(max((r1 - m12 * b) / m11 if m11 > 1e-9 else a, lo), amax)
        return a, b

    for _ in range(40):
        got = solve(u)
        if got is None:
            break
        moved = abs(got[0] - la) + abs(got[1] - lb)
        la, lb = got
        ctrl = np.array([p0, p0 + la * t0, p3 - lb * t3, p3])
        u = feet(ctrl, pts, u)
        if moved < 1e-4:
            break
    return np.array([p0, p0 + la * t0, p3 - lb * t3, p3])


def wrong_turn(ctrl):
    """(end, degrees) where a cubic's handles make it bend the other way a
    little at one end (0: its start, 1: its end), None if it bends one way
    or is an S meant as one. Its curvature at an end has the sign of the
    turn there of the line through its four points; a handle past the
    point where the two directions meet turns the first of them back: an
    inflection a few units into the curve, which no eye sees and every
    tool finds (Skia cuts the curve there, the Bold's stroke steps aside:
    n's 809,649, 2026-11-10)."""
    a, b, c = ctrl[1] - ctrl[0], ctrl[2] - ctrl[1], ctrl[3] - ctrl[2]
    if min(math.hypot(*a), math.hypot(*b), math.hypot(*c)) < 1e-9:
        return None
    t0, t1 = cross(a, b), cross(b, c)
    if t0 * t1 >= 0:
        return None
    d0, d1 = angle_between(a, b), angle_between(b, c)
    end, small, large = (0, d0, d1) if d0 < d1 else (1, d1, d0)
    return (end, small) if small < S_TURN and large > 3 * small else None


def one_bend(ctrl, t0, t3):
    """ctrl (whole units) with the handle shortened that makes it bend the
    other way at one end (wrong_turn): the far one drawn back along its
    direction, a unit at a time, until the curve bends one way"""
    ctrl = ctrl.copy()
    short = [0.0, 0.0, 0.0]  # by how much handle 1 and handle 2 are shortened
    for _ in range(16):
        wrong = wrong_turn(ctrl)
        if wrong is None:
            return ctrl
        # bent back at its start: the end's handle reaches past the meeting point
        k, node, d = (2, ctrl[3], -t3) if wrong[0] == 0 else (1, ctrl[0], t0)
        if not short[k]:
            short[k] = float(np.linalg.norm(ctrl[k] - node))
        short[k] -= 1
        if short[k] < 2:
            break
        ctrl[k] = whole_handle(node, node + short[k] * d, d)
    return ctrl


def whole_handle(node, ideal, direction):
    """the whole-unit point for a handle meant at ideal, leaving node along
    direction: on an axis plainly rounded, else the neighbour that keeps
    the direction best (and the length nearly)"""
    if abs(direction[0]) < 1e-9 or abs(direction[1]) < 1e-9:
        return np.round(ideal)
    want = float(np.linalg.norm(ideal - node))
    if want < 3:
        return np.round(ideal)
    best = None
    bx, by = math.floor(ideal[0]), math.floor(ideal[1])
    for x in range(bx - 1, bx + 3):
        for y in range(by - 1, by + 3):
            v = np.array([x, y], float) - node
            if math.hypot(*v) < 1e-9 or abs(math.hypot(*v) - want) > 2.5:
                continue
            score = angle_between(v, direction) + 0.15 * abs(math.hypot(*v) - want)
            if best is None or score < best[0]:
                best = (score, np.array([x, y], float))
    return best[1] if best else np.round(ideal)


def curvature(ctrl, end):
    """a cubic's signed curvature at its start (end 0) or its end (1)"""
    if end == 0:
        a, b = ctrl[1] - ctrl[0], ctrl[2] - ctrl[1]
    else:
        a, b = ctrl[3] - ctrl[2], ctrl[2] - ctrl[1]
        b = -b
    la = math.hypot(*a)
    if la < 1e-6:
        return None
    k = (2 / 3) * cross(a, b) / la ** 3
    return k if end == 0 else k


def curvature_jump(k0, k1):
    """0 where two curves meet with one curvature, 1 where one of them is
    straight there, 2 where they bend opposite ways alike; against K_FLAT
    where both are flatter than that"""
    if k0 is None or k1 is None:
        return 0.0
    return abs(k0 - k1) / max(abs(k0), abs(k1), K_FLAT)


def fair(out, tol, notes=None):
    """the fitted spans (redraw_contour's [a, b, ctrl, pts]) with one
    curvature where two curves meet smoothly, as far as every curve stays
    within its limit of the target (its tolerance and FAIR_ROOM of it, or what its own fit
    left if that was more): all handle lengths found together (least
    squares on the distance to the target and on the curvature jumps,
    Levenberg-Marquardt), the joint that costs most set free again while
    a curve is over its limit. In place; returns the joints made so."""
    m = len(out)
    curves = [i for i in range(m) if len(out[i][2]) == 4]
    joints = [i for i in curves if out[i][1].kind in ("extreme", "extra") and len(out[(i + 1) % m][2]) == 4]
    if not joints:
        return []
    slot = {i: 2 * n for n, i in enumerate(curves)}
    geo, us = {}, {}
    x0 = np.zeros(2 * len(curves))
    for i in curves:
        a, b, ctrl, pts = out[i]
        lo, amax, bmax = handle_bounds(ctrl[0], a.tout, ctrl[3], b.tin)
        geo[i] = (ctrl[0], a.tout, ctrl[3], b.tin, lo, amax, bmax)
        x0[slot[i]], x0[slot[i] + 1] = np.linalg.norm(ctrl[1] - ctrl[0]), np.linalg.norm(ctrl[3] - ctrl[2])
    lows = np.concatenate([[geo[i][4], geo[i][4]] for i in curves])
    highs = np.concatenate([[geo[i][5], geo[i][6]] for i in curves])
    limit = {i: max(span_tol(out[i][3], tol) * (1 + FAIR_ROOM), deviation(out[i][2], out[i][3])[0] + 0.25)
             for i in curves}
    rows = np.cumsum([0] + [2 * len(out[i][3]) for i in curves])
    scale, weight = {}, {}

    def weight_full(i):
        return G2_WEIGHT * math.sqrt(len(out[i][3]) + len(out[(i + 1) % m][3]))

    for i in joints:
        j = (i + 1) % m
        k0, k1 = curvature(out[i][2], 1), curvature(out[j][2], 0)
        scale[i] = 1 / max(abs(k0 or 0), abs(k1 or 0), K_FLAT)
        weight[i] = weight_full(i)

    def ctrl_of(x, i):
        p0, t0, p3, t3 = geo[i][:4]
        return np.array([p0, p0 + x[slot[i]] * t0, p3 - x[slot[i] + 1] * t3, p3])

    def jump(x, i):
        k0, k1 = curvature(ctrl_of(x, i), 1), curvature(ctrl_of(x, (i + 1) % m), 0)
        return weight[i] * scale[i] * ((k0 or 0) - (k1 or 0))

    def system(x, active):
        """residuals and Jacobian: the distances are linear in the lengths"""
        r = np.zeros(rows[-1] + len(active))
        J = np.zeros((len(r), len(x)))
        for n, i in enumerate(curves):
            u = us[i]
            r[rows[n]:rows[n + 1]] = (bezier(ctrl_of(x, i), u) - out[i][3]).ravel()
            b1, b2 = 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2
            J[rows[n]:rows[n + 1], slot[i]] = (b1[:, None] * geo[i][1]).ravel()
            J[rows[n]:rows[n + 1], slot[i] + 1] = (-b2[:, None] * geo[i][3]).ravel()
        for n, i in enumerate(active):
            row = rows[-1] + n
            r[row] = jump(x, i)
            for q in (slot[i], slot[i] + 1, slot[(i + 1) % m], slot[(i + 1) % m] + 1):
                xq = x.copy()
                xq[q] += 1e-3
                J[row, q] = (jump(xq, i) - r[row]) / 1e-3
        return r, J

    def minimise(x, active):
        lam = 1e-2
        last = None
        for _ in range(12):  # the points' parameters found again
            for _ in range(20):
                r, J = system(x, active)
                A, g = J.T @ J, J.T @ r
                for _ in range(10):
                    xn = np.clip(x + np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g), lows, highs)
                    rn = system(xn, active)[0]
                    if rn @ rn < r @ r:
                        break
                    lam *= 4
                else:
                    break
                gain = (r @ r - rn @ rn) / max(r @ r, 1e-12)
                x, lam = xn, lam / 3
                if gain < 1e-6:
                    break
            for i in curves:
                us[i] = feet(ctrl_of(x, i), out[i][3], us[i])
            if last is not None and np.abs(x - last).max() < 1e-2:
                break
            last = x.copy()
        return x

    for i in curves:
        pts = out[i][3]
        d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        u = d / d[-1]
        for _ in range(8):
            u = feet(out[i][2], pts, u)
        us[i] = u
    active = list(joints)
    x = x0
    for _ in range(40):
        if not active:
            return []
        x = minimise(x, active)
        over = {i: deviation(ctrl_of(x, i), out[i][3])[0] - limit[i] for i in curves}
        bad = [i for i in curves if over[i] > 0]
        if not bad:
            break
        # the joints at the worst curve's ends count for half as much
        worst = max(bad, key=lambda i: over[i])
        beside = [i for i in active if worst in (i, (i + 1) % m)] or list(active)
        for i in beside:
            weight[i] /= 2
            if weight[i] < G2_WEIGHT / 200:
                active.remove(i)
        x = (x + x0) / 2
    else:
        return []
    for i in curves:
        out[i][2] = ctrl_of(x, i)
    if notes is not None:
        for i in joints:
            if i not in active or weight[i] < weight_full(i):
                b = out[i][1]
                notes.append(f"{b.at[0]:.0f},{b.at[1]:.0f}: one curvature only as far as the tolerance allows")
    return active


def span_tol(pts, tol):
    """a short curve (a ball's neck, a hook's turn) is held closer: a
    hundredth of its length, between FINE and the tolerance"""
    arc = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
    return min(tol, max(FINE * tol / TOL, arc / 100))


def redraw_contour(segs, tol=TOL, spec=None, report=None):
    """the contour's new segments [(kind of its start node, array of 2 or 4
    whole-unit points)], and what was done in report"""
    report = report if report is not None else {}
    notes = report.setdefault("notes", [])
    tg = Target(cleaned(segs, notes, (spec or {}).get("keep", ())), spec)
    breaks = tg.structure(spec, notes)
    if len(breaks) < 2:
        raise ValueError("fewer than two nodes found")

    def line_span(a, b):
        return (a.u == math.floor(a.u) and b.u == math.floor(b.u) and tg.line[int(a.u)]
                and (int(a.u) + 1) % tg.n == int(b.u))

    def solve(a, b, depth):
        pts = tg.between(a.u, b.u)
        ctrl = fit_cubic(pts, np.round(a.at), a.tout, np.round(b.at), b.tin)
        err, worst = deviation(ctrl, pts)
        if err <= span_tol(pts, tol) or depth == 0:
            return [(a, b)]
        where, _d = tg.nearest(pts[worst])
        if where < a.u:
            where += tg.n
        m = tg.split(a, b, where)
        if m is None:
            return [(a, b)]
        notes.append(f"extra node at {m.at[0]:.0f},{m.at[1]:.0f} ({m.why}): one curve was {err:.1f} units off")
        return solve(a, m, depth - 1) + solve(m, b, depth - 1)

    spans = []
    for i, a in enumerate(breaks):
        b = breaks[(i + 1) % len(breaks)]
        spans += [(a, b)] if line_span(a, b) else solve(a, b, DEPTH)
    # nodes on whole units, the cubics fitted between them
    out = []
    for a, b in spans:
        p0, p3 = np.round(a.at), np.round(b.at)
        if line_span(a, b):
            out.append([a, b, np.array([p0, p3]), None])
        else:
            pts = tg.between(a.u, b.u)
            out.append([a, b, fit_cubic(pts, p0, a.tout, p3, b.tin), pts])
    fair(out, tol, notes)
    # handles on whole units, a smooth node's two in one line
    m = len(out)
    for i in range(m):
        prev, here = out[i - 1], out[i]
        node, b = np.round(here[0].at), here[0]
        if len(prev[2]) == 4:
            d = b.tin
            if b.kind == "line" and len(here[2]) == 2:
                d = unit(here[2][1] - here[2][0])
            prev[2][2] = whole_handle(node, prev[2][2], -d)
        if len(here[2]) == 4:
            d = b.tout
            if b.kind == "line" and len(prev[2]) == 2:
                d = unit(prev[2][1] - prev[2][0])
            elif b.kind == "extra" and len(prev[2]) == 4 and np.linalg.norm(node - prev[2][2]) > 3:
                d = unit(node - prev[2][2])
            here[2][1] = whole_handle(node, here[2][1], d)
    # rounding moves the point where a curve's two directions meet by a
    # unit or two: no handle past it
    for seg in out:
        if len(seg[2]) == 4 and wrong_turn(seg[2]) is not None:
            was = seg[2]
            seg[2] = one_bend(was, unit(was[1] - was[0]), unit(was[3] - was[2]))
            if notes is not None and wrong_turn(seg[2]) is None:
                notes.append(f"{was[0][0]:.0f},{was[0][1]:.0f}: a handle shortened, the curve bent both ways")
    devs, jumps = [], []
    for i in range(m):
        a, b, ctrl, pts = out[i]
        if pts is not None:
            err, worst = deviation(ctrl, pts)
            devs.append((err, pts[worst]))
        nxt = out[(i + 1) % m]
        if b.kind in ("extreme", "extra") and len(ctrl) == 4 and len(nxt[2]) == 4:
            jumps.append((curvature_jump(curvature(ctrl, 1), curvature(nxt[2], 0)), b.at))
    report.setdefault("spans", []).extend(
        {"from": [float(x) for x in np.round(a.at)], "kind": a.kind, "why": a.why,
         "dev": round(devs_i, 2)} for (a, _b, _c, pts), devs_i in zip(
            out, iter([d[0] for d in devs] + [0.0] * m)) if pts is not None)
    report.setdefault("devs", []).extend(devs)
    report.setdefault("jumps", []).extend(jumps)
    report.setdefault("kinds", []).extend(a.kind + (":" + a.why if a.kind == "extra" else "") for a, *_ in out)
    return [(a.kind, ctrl) for a, _b, ctrl, _p in out]


def target_jumps(glyph):
    """the curvature jumps at the target's smooth nodes between two curves"""
    out = []
    for c in glyph.contours:
        try:
            segs = segments(c)
        except ValueError:
            continue
        for k, s in enumerate(segs):
            prev = segs[k - 1]
            if len(s) == 4 and len(prev) == 4 and angle_between(tangent(prev, 1.0), tangent(s, 0.0)) <= CORNER:
                out.append(curvature_jump(curvature(prev, 1), curvature(s, 0)))
    return out


def node_count(glyph):
    return sum(1 for c in glyph.contours for p in c.points if p.type)


def bent_back(glyph):
    """[[x, y, degrees]]: the curves of a glyph that bend the other way a
    little at one end (wrong_turn), at that end"""
    out = []
    for c in glyph.contours:
        for seg in segments(c):
            ctrl = np.array(seg, float)
            if len(ctrl) == 4 and (wrong := wrong_turn(ctrl)) is not None:
                x, y = ctrl[0] if wrong[0] == 0 else ctrl[3]
                out.append([float(x), float(y), round(wrong[1], 2)])
    return out


def redraw_at(glyph, tol, spec):
    from ufoLib2.objects import Contour, Glyph, Point

    if glyph.components:
        raise ValueError("a glyph with components is not redrawn: redraw its parts")
    new = Glyph(glyph.name)
    new.width, new.height, new.unicodes = glyph.width, glyph.height, list(glyph.unicodes)
    new.anchors = [type(a)(a.x, a.y, a.name, a.color, a.identifier) for a in glyph.anchors]
    new.lib.update(json.loads(json.dumps(dict(glyph.lib), default=str)) if glyph.lib else {})
    report = {"glyph": glyph.name, "tol": tol, "nodes_before": node_count(glyph)}
    for c in glyph.contours:
        segs = redraw_contour(segments(c), tol, spec, report)
        pts = []
        for i, (kind, ctrl) in enumerate(segs):
            before = segs[i - 1][1]
            pts.append(Point(float(ctrl[0][0]), float(ctrl[0][1]), "curve" if len(before) == 4 else "line",
                             smooth=kind != "corner"))
            if len(ctrl) == 4:
                pts += [Point(float(ctrl[1][0]), float(ctrl[1][1])), Point(float(ctrl[2][0]), float(ctrl[2][1]))]
        new.contours.append(Contour(pts))
    for p in (p for c in new.contours for p in c.points):
        p.x, p.y = int(p.x), int(p.y)
    devs, jumps = report.pop("devs"), report.pop("jumps")
    worst = max(devs, key=lambda d: d[0], default=(0.0, np.zeros(2)))
    report["nodes_after"] = node_count(new)
    report["dev"] = round(worst[0], 2)
    report["dev_at"] = [round(float(worst[1][0])), round(float(worst[1][1]))]
    wj = max(jumps, key=lambda j: j[0], default=(0.0, np.zeros(2)))
    report["jump"] = round(wj[0], 2)
    report["jump_at"] = [round(float(wj[1][0])), round(float(wj[1][1]))]
    report["jump_before"] = round(max(target_jumps(glyph), default=0.0), 2)
    kinds = report["kinds"]
    report["count"] = {k: sum(1 for x in kinds if x.split(":")[0] == k) for k in ("corner", "line", "extreme", "extra")}
    report["extras"] = [x.split(":")[1] for x in kinds if x.startswith("extra")]
    report["area"] = round(100 * (area(new) / area(glyph) - 1), 2) if area(glyph) else 0.0
    report["bounds_moved"] = round(max(abs(a - b) for a, b in zip(bounds(new), bounds(glyph))), 1)
    from quality.checks import construction

    report["findings"] = [list(f) for f in construction(new)]
    report["bent_back"] = bent_back(new)
    return new, report


def redraw(glyph, tol=TOL, spec=None):
    """(the glyph redrawn: a copy, its contours new; the report). If it
    comes out with more nodes than the target has, the tolerance is
    widened by WIDEN, twice at most (the report's "tol" says how far),
    and taken so if that brings the count down within the gate's distance;
    else the first result stands and the gate remarks the count."""
    spec = spec or {}
    tol = spec.get("tol", tol)
    first = redraw_at(glyph, tol, spec)
    if first[1]["nodes_after"] <= first[1]["nodes_before"] or "tol" in spec:
        return first
    for _ in range(2):
        tol = round(tol * WIDEN, 2)
        new, report = redraw_at(glyph, tol, spec)
        if report["nodes_after"] <= report["nodes_before"] and report["dev"] <= DEV:
            return new, report
    return first


def area(glyph):
    """the ink's area (contours' signed areas summed, curves flattened)"""
    total = 0.0
    for c in glyph.contours:
        pts = np.concatenate([np.array([point(s, t) for t in np.linspace(0, 1, 33)[:-1]]) for s in segments(c)])
        x, y = pts[:, 0], pts[:, 1]
        total += float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 2
    return abs(total)


def bounds(glyph):
    pts = np.concatenate([np.array([point(s, t) for t in np.linspace(0, 1, 65)]) for c in glyph.contours for s in segments(c)])
    return (*pts.min(axis=0), *pts.max(axis=0))


def gate(report, counterpart=None):
    """why the redrawn glyph is not yet a candidate ([] if it is), and what
    to look at on the sheet all the same: (failures, remarks)"""
    fail, look = [], []
    if report["dev"] > DEV:
        fail.append(f"{report['dev']} units off the target at {report['dev_at'][0]},{report['dev_at'][1]} (limit {DEV:g})")
    for f in report["findings"]:
        fail.append(f"{f[0]} {f[1]} {f[2]}")
    for x, y, deg in report.get("bent_back", ()):
        fail.append(f"the curve at {x:.0f},{y:.0f} bends {deg} degrees the other way first")
    if report["bounds_moved"] > 1:
        fail.append(f"bounds moved by {report['bounds_moved']} units")
    if abs(report["area"]) > 1:
        fail.append(f"ink area changed by {report['area']} %")
    if report["nodes_after"] > report["nodes_before"]:
        look.append(f"more nodes than before ({report['nodes_after']} against {report['nodes_before']}): "
                    "an extreme that had none, or a shape one curve does not hold")
    if report["tol"] > TOL and "widened" not in report:
        look.append(f"tolerance {report['tol']:g}")
    other = [w for w in report["extras"] if w not in ("inflection", "spec")]
    if other:
        look.append(f"{len(other)} extra node(s) off extremes and inflections ({', '.join(other)})")
    if report["jump"] > max(JUMP, report["jump_before"]):
        look.append(f"curvature jump {report['jump']} at {report['jump_at'][0]},{report['jump_at'][1]} "
                    f"(the target's worst {report['jump_before']})")
    if counterpart is not None and report["nodes_after"] > counterpart + 4:
        look.append(f"{report['nodes_after']} nodes against the Regular's {counterpart}")
    return fail, look


def spec_for(ufo, path=None):
    p = Path(path) if path else Path(__file__).resolve().parent / "data" / f"redraw-{Path(ufo).stem.split('-')[-1]}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def install(font, name, new, date, review, report):
    """new's contours into font[name], kept from now on: the Italic's
    glyph marked drawn (make_italic keeps it), the redraw recorded"""
    from built_from import fingerprint

    g = font[name]
    was = fingerprint(font, name)
    g.clearContours()
    for c in new.contours:
        g.appendContour(c)
    # the mark it had (make_italic.origin reads it: a redrawn Old Standard
    # letter still carries that weight); a second redraw keeps the first's
    source = g.lib.get(ITALIC_SOURCE_KEY, "")
    if source == "drawn":
        source = g.lib.get(KEY, {}).get("source") or source
    g.lib[KEY] = {"date": date, "review": review, "from": was, "source": source, "tol": report["tol"]}
    if ITALIC_SOURCE_KEY in g.lib:
        g.lib[ITALIC_SOURCE_KEY] = "drawn"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("glyphs", nargs="+", help="glyph names or characters")
    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--spec", help="node corrections (default scripts/data/redraw-STYLE.json)")
    ap.add_argument("--json", help="the full reports")
    ap.add_argument("--regular", default="sources/MyiaDidot-Regular.ufo", help="for the node counts beside")
    ap.add_argument("--install", action="store_true", help="after the review: into SRC.ufo, marked drawn")
    ap.add_argument("--date")
    ap.add_argument("--review")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review (the sheet it was accepted on)")
    font = ufoLib2.Font.open(a.src)
    regular = ufoLib2.Font.open(a.regular) if Path(a.regular).exists() else {}
    cmap = {chr(u): g.name for g in font for u in g.unicodes}
    spec = spec_for(a.src, a.spec)
    out = ufoLib2.Font()
    out.info.unitsPerEm, out.info.italicAngle = font.info.unitsPerEm, font.info.italicAngle
    out.info.xHeight, out.info.capHeight = font.info.xHeight, font.info.capHeight
    out.info.ascender, out.info.descender = font.info.ascender, font.info.descender
    reports, failed = [], 0
    print(f"{'glyph':<12}{'nodes':>9}{'Regular':>8}{'dev':>6}{'jump':>12}  verdict")
    for name in (cmap.get(x, x) for x in a.glyphs):
        try:
            new, rep = redraw(font[name], a.tol, spec.get(name))
        except (ValueError, KeyError) as e:
            print(f"{name:<12} refused: {e}")
            failed += 1
            continue
        counterpart = node_count(regular[name]) if name in regular and regular[name].contours else None
        fail, look = gate(rep, counterpart)
        rep["counterpart"], rep["fail"], rep["look"] = counterpart, fail, look
        reports.append(rep)
        out.layers.defaultLayer.insertGlyph(new, name)
        failed += bool(fail)
        print(f"{name:<12}{rep['nodes_before']:>4} ->{rep['nodes_after']:>3}{counterpart if counterpart else '':>8}"
              f"{rep['dev']:>6.1f}{rep['jump_before']:>6.2f}->{rep['jump']:<4.2f}  "
              + ("FAIL: " + "; ".join(fail) if fail else "candidate")
              + ("" if not look else "  [look: " + "; ".join(look) + "]"))
        if a.install and not fail:
            install(font, name, new, a.date, a.review, rep)
    out.save(a.out, overwrite=True)
    if a.json:
        Path(a.json).write_text(json.dumps(reports, indent=1, ensure_ascii=False) + "\n")
    if a.install:
        font.save()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
