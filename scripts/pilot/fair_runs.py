"""Runs of an outline redrawn with as few curves as hold it, each bending
one way only.

Emboldening moves each node of the lighter style by the weight of the
stroke there; where neighbouring nodes move by different amounts, the
curves between them bend in and out again (the Bold Italic e's stem below
its bar, n's downstroke above its foot). Here the nodes that fix a shape
stay: corners and extremes. What runs between two of them is redrawn as
one cubic bending one way, or, where one does not hold it within TOL
units, split (at the run's own inflection, else at its node nearest the
middle) and each part so redrawn. A corner's tangent may turn a little
(TURN degrees) where that lets the run bend one way. A glyph takes the
result only where it does not bend back more often than before
(quality.checks.reversals).

A study (FONT-DESIGN.md, Bold Italic from strokes), not part of the build:
it takes out e's and s's wobbles, not n's (their nodes sit off).
"""

import math

import numpy as np
from derive import inflects

TOL = 5.0  # units the redrawn run may stray from the run, either way
TURN = 25.0  # degrees a corner's tangent may turn
CORNER = 3.0  # degrees the outline turns at a corner


def _bez(p, t):
    u = 1 - t
    return u ** 3 * p[0] + 3 * u * u * t * p[1] + 3 * u * t * t * p[2] + t ** 3 * p[3]


def _unit(v):
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else None


def _tangents(P, i):
    """the directions arriving at and leaving on-curve point i"""
    n = len(P)
    here = np.array([P[i].x, P[i].y], float)
    back = next((np.array([P[(i - k) % n].x, P[(i - k) % n].y], float) for k in range(1, n)
                 if (P[(i - k) % n].x, P[(i - k) % n].y) != (P[i].x, P[i].y)), here)
    on = next((np.array([P[(i + k) % n].x, P[(i + k) % n].y], float) for k in range(1, n)
               if (P[(i + k) % n].x, P[(i + k) % n].y) != (P[i].x, P[i].y)), here)
    return _unit(here - back), _unit(on - here)


def _corner(P, i):
    """an on-curve point where the outline turns (by its tangents, not its flag)"""
    t_in, t_out = _tangents(P, i)
    return t_in is None or t_out is None or float(t_in @ t_out) < math.cos(math.radians(CORNER))


def _fixed(P, i):
    """a node that stays: a corner, or a straight edge's end (stems stay
    straight); extremes are drawn anew at the redrawn runs' own"""
    if not P[i].type:
        return False
    return _corner(P, i) or P[i].type == "line" or P[(i + 1) % len(P)].type == "line"


def _samples(P, i, j):
    """points along the outline from node i to node j, and where each node
    in between falls among them (index, its tangent)"""
    n = len(P)
    pts, nodes = [], []
    k = i
    while k != j:
        m = (k + 1) % n
        while not P[m].type:
            m = (m + 1) % n
        idx = [k] + [(k + q) % n for q in range(1, (m - k) % n)] + [m]
        seg = [np.array([P[q].x, P[q].y], float) for q in idx]
        if k != i:
            nodes.append((len(pts), _tangents(P, k)[1]))
        if len(seg) == 2:
            steps = max(2, int(np.hypot(*(seg[1] - seg[0])) / 4))
            pts += [seg[0] + (seg[1] - seg[0]) * t for t in np.linspace(0, 1, steps, endpoint=False)]
        else:
            length = sum(float(np.hypot(*(seg[q + 1] - seg[q]))) for q in range(3))
            pts += [_bez(seg, t) for t in np.linspace(0, 1, max(4, int(length / 4)), endpoint=False)]
        k = m
    pts.append(np.array([P[j].x, P[j].y], float))
    return np.array(pts), nodes


def _fit(pts, t0, t1):
    """one cubic from pts[0] to pts[-1] leaving along t0, arriving along t1,
    its handle lengths by least squares: (controls, deviation) or None"""
    P0, P3 = pts[0], pts[-1]
    d = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    if d[-1] < 1e-6:
        return None
    u = d / d[-1]
    ts = np.linspace(0, 1, 160)
    for _ in range(4):
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        A1, A2 = b1[:, None] * t0, -b2[:, None] * t1
        R = pts - (b0 + b1)[:, None] * P0 - (b2 + b3)[:, None] * P3
        M = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
        try:
            la, lb = np.linalg.solve(M, np.array([np.sum(A1 * R), np.sum(A2 * R)]))
        except np.linalg.LinAlgError:
            return None
        if la <= 0 or lb <= 0 or la > d[-1] or lb > d[-1]:
            return None
        ctrl = [P0, P0 + la * t0, P3 - lb * t1, P3]
        curve = np.array([_bez(ctrl, t) for t in ts])
        dist = np.hypot(*(pts[:, None, :] - curve[None, :, :]).transpose(2, 0, 1))
        u = ts[np.argmin(dist, axis=1)]
    # both ways: the run from the curve, the curve from the run
    return ctrl, float(max(dist.min(axis=1).max(), dist.min(axis=0).max()))


def _rot(t, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([c * t[0] - s * t[1], s * t[0] + c * t[1]])


def _one(pts, t0, t1, free0, free1):
    """the cubic bending one way that strays least; a corner's end free to turn"""
    turns = np.arange(-TURN, TURN + 0.1, 5.0)
    best = None
    for d0 in (turns if free0 else (0.0,)):
        for d1 in (turns if free1 else (0.0,)):
            res = _fit(pts, _rot(t0, d0), _rot(t1, d1))
            if res and (best is None or res[1] < best[1]) and not inflects(tuple(map(tuple, res[0]))):
                best = res
    return best


def _inflection(pts):
    """the one place the run's bend turns the other way, clearly, or None"""
    q = pts[::6]
    if len(q) < 6:
        return None
    d = np.diff(q, axis=0)
    cr = d[:-1, 0] * d[1:, 1] - d[:-1, 1] * d[1:, 0]
    big = np.abs(cr) > 0.05 * np.abs(cr).max()
    signs = [(i, np.sign(c)) for i, c in enumerate(cr) if big[i]]
    flips = [i for (i, a), (_, b) in zip(signs, signs[1:]) if a != b]
    if len(flips) != 1:
        return None
    k = (flips[0] + 1) * 6
    return k if 12 <= k <= len(pts) - 13 else None


def _run(pts, t0, t1, free0, free1, nodes, room):
    """[controls ...] for the run in at most room cubics, or None"""
    one = _one(pts, t0, t1, free0, free1)
    if one and one[1] <= TOL:
        return [one[0]]
    if room < 2:
        return None
    # split at the run's inflection, else at one of its nodes (nearest the
    # middle first), whichever lets both parts be so redrawn
    splits = sorted(nodes, key=lambda nd: abs(nd[0] - len(pts) / 2))
    k = _inflection(pts)
    if k is not None:
        splits.insert(0, (k, _unit(pts[k + 4] - pts[k - 4])))
    for k, tk in splits:
        if tk is None or not 4 <= k <= len(pts) - 5:
            continue
        first = _run(pts[:k + 1], t0, tk, free0, False, [nd for nd in nodes if nd[0] < k], room - 1)
        if first is None:
            continue
        rest = _run(pts[k:], tk, t1, False, free1, [(i - k, t) for i, t in nodes if i > k], room - len(first))
        if rest is not None:
            return first + rest
    return None


def _at_extremes(ctrl):
    """a cubic split where it runs level or upright inside (its extremes)"""
    from fontTools.misc.bezierTools import splitCubicAtT

    ts = []
    for q in (0, 1):
        a, b, c, d = (float(p[q]) for p in ctrl)
        # the derivative's coefficients: A t^2 + B t + C
        A, B, C = 3 * (-a + 3 * b - 3 * c + d), 6 * (a - 2 * b + c), 3 * (b - a)
        if abs(A) < 1e-9:
            roots = [-C / B] if abs(B) > 1e-9 else []
        else:
            disc = B * B - 4 * A * C
            roots = [] if disc < 0 else [(-B + s * math.sqrt(disc)) / (2 * A) for s in (1, -1)]
        ts += [r for r in roots if 0.02 < r < 0.98]
    if not ts:
        return [ctrl]
    parts = splitCubicAtT(*(tuple(map(float, p)) for p in ctrl), *sorted(set(round(r, 6) for r in ts)))
    return [[np.array(p) for p in part] for part in parts]


def fair_contour(contour, Point):
    """contour (in place) with its runs redrawn; how many nodes it lost"""
    P = list(contour.points)
    # a straight edge of no length (a doubled node) left out
    P = [p for i, p in enumerate(P) if not (p.type == "line" and P[i - 1].type
                                             and (P[i - 1].x, P[i - 1].y) == (p.x, p.y))]
    n = len(P)
    keys = [i for i in range(n) if _fixed(P, i)]
    if len(keys) < 2:
        return 0
    out, lost = [], 0
    for a, b in zip(keys, keys[1:] + keys[:1]):
        between = [(a + q) % n for q in range(1, (b - a) % n or n)]
        ons = [q for q in between if P[q].type]
        out.append(P[a])
        pieces = None
        # a single curve bending both ways (the wobble itself) as well
        single = (len(between) == 2 and inflects(tuple((P[q].x, P[q].y) for q in (a, *between, b))))
        if between and (ons or single):
            pts, nodes = _samples(P, a, b)
            t0, t1 = _unit(pts[1] - pts[0]), _unit(pts[-1] - pts[-2])
            if t0 is not None and t1 is not None:
                pieces = _run(pts, t0, t1, _corner(P, a), _corner(P, b), nodes, len(ons) + 1)
        if pieces:
            pieces = [part for ctrl in pieces for part in _at_extremes(ctrl)]
        if not pieces or len(pieces) > len(ons) + 1 or (len(pieces) == len(ons) + 1 and not single):
            out += [P[q] for q in between]
            continue
        for q, ctrl in enumerate(pieces):
            out += [Point(float(ctrl[1][0]), float(ctrl[1][1])), Point(float(ctrl[2][0]), float(ctrl[2][1]))]
            if q < len(pieces) - 1:
                out.append(Point(float(ctrl[3][0]), float(ctrl[3][1]), "curve", True))
        lost += len(ons) + 1 - len(pieces) + single
    if not lost:
        return 0
    contour.points.clear()
    for p in out:
        contour.points.append(Point(p.x, p.y, p.type, p.smooth))
    return lost


def fair(glyph, reversals):
    """glyph (in place) with its runs redrawn, where it does not bend back
    more often than before; True if it changed"""
    import copy

    from ufoLib2.objects import Point

    before = len(reversals(glyph))
    trial = copy.deepcopy(glyph)
    if not sum(fair_contour(c, Point) for c in trial.contours):
        return False
    if len(reversals(trial)) > before:
        return False
    glyph.clearContours()
    pen = glyph.getPointPen()
    for c in trial.contours:
        pen.beginPath()
        for p in c.points:
            pen.addPoint((p.x, p.y), p.type, p.smooth)
        pen.endPath()
    return True
