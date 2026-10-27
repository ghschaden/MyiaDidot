"""Pilot: the Bold Italic from the Italic's strokes, not its nodes.

Each Italic outline (deslanted, widened by KX, overlaps removed) is sampled
every STEP units. At each sample the stroke's section is measured (a ray
into the ink to the facing side); its weight k (0 hairline .. 1 stem, as
embolden_by_weight's thin/thick band) is smoothed along the outline as a
pen's width changes, gradually, and the sample moves out by ax*k/2
across and ay/2 up or down (make_bold's anisotropic gain). Corners stay
corners (mitred). The moved samples are cleaned (pathops) and redrawn with
cubics: nodes at the extremes (slanted frame) and corners only, each run
one cubic if it fits within TOL units, split where it does not.

    .venv/bin/python -I scripts/pilot/strokes_pilot.py OUT.ufo glyph ...

A study (FONT-DESIGN.md, Bold Italic from strokes), not part of the build.
"""
import math
import sys

import numpy as np

sys.path[:0] = ["scripts", "scripts/quality", "scripts/pilot"]
import make_bold as mb
import pathops
import ufoLib2
from derive import merged_glyph
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

STEP = 2.0          # units between samples
SIGMA = 45.0        # smoothing of the weight along the outline (units)
PARALLEL = math.cos(math.radians(40))  # a facing side within this of parallel: a section
CORNER = 28.0       # degrees: a turn this sharp at a node is a corner
TOL = 2.0           # fit tolerance (units)

src = ufoLib2.Font.open("sources/MyiaDidot-Italic.ufo")
SLANT = math.tan(math.radians(-src.info.italicAngle))
AX, AY, THIN, THICK, KX = mb.ITALIC_AX, mb.AY, mb.ITALIC_THIN, mb.ITALIC_THICK, mb.KX


def bez(p, t):
    u = 1 - t
    return (u ** 3 * p[0] + 3 * u * u * t * p[1] + 3 * u * t * t * p[2] + t ** 3 * p[3])


def dbez(p, t):
    u = 1 - t
    return 3 * u * u * (p[1] - p[0]) + 6 * u * t * (p[2] - p[1]) + 3 * t * t * (p[3] - p[2])


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def sample(contour):
    """[(point, tangent, corner)], corner nodes twice (in, out tangents)"""
    P = contour.points
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    out = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
        pts = [np.array([P[q].x, P[q].y], float) for q in (i, *offs, j)]
        if len(pts) == 2:
            pts = [pts[0], pts[0] + (pts[1] - pts[0]) / 3, pts[0] + 2 * (pts[1] - pts[0]) / 3, pts[1]]
        length = sum(np.linalg.norm(pts[q + 1] - pts[q]) for q in range(3))
        m = max(2, int(length / STEP))
        seg = []
        for s in range(m):
            t = s / m
            d = dbez(pts, t)
            if np.linalg.norm(d) < 1e-9:
                d = dbez(pts, min(1, t + 1e-3)) if t < 0.5 else dbez(pts, t - 1e-3)
            seg.append([bez(pts, t), unit(d), False])
        # the node at the segment's start: a corner if the incoming tangent turns sharply
        if out or k:
            pass
        out.append(seg)
    # corners: between a segment's last tangent and the next one's first
    flat = []
    L = len(out)
    for k in range(L):
        seg = out[k]
        # incoming tangent at the node: the previous segment's end tangent
        pk = P[[i for i, p in enumerate(P) if p.type][k]]
        ons = [i for i, p in enumerate(P) if p.type]
        i = ons[k]
        a = np.array([P[i - 1].x, P[i - 1].y], float)
        b = np.array([P[(i + 1) % n].x, P[(i + 1) % n].y], float)
        c = np.array([pk.x, pk.y], float)
        tin, tout = unit(c - a), unit(b - c)
        turn = math.degrees(math.acos(max(-1, min(1, float(tin @ tout)))))
        if turn > CORNER and not pk.smooth:
            flat.append([c, tin, True])  # the corner, arriving
            seg[0][2] = True
        flat += seg
    return flat


def raycast(origin, direction, segs):
    """distance to the nearest outline segment along direction, its tangent"""
    a, b = segs[:, 0], segs[:, 1]
    e = b - a
    w = a - origin
    den = direction[0] * e[:, 1] - direction[1] * e[:, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / den
        s = (w[:, 0] * direction[1] - w[:, 1] * direction[0]) / den
    ok = (np.abs(den) > 1e-9) & (t > 1.0) & (s >= 0) & (s <= 1)
    if not ok.any():
        return None, None
    idx = np.argmin(np.where(ok, t, np.inf))
    return t[idx], unit(e[idx])


def offset_glyph(glyph):
    """the moved samples as polygons (one per contour), and the weights"""
    def area(c):
        pts = [(p.x, p.y) for p in c.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    areas = [area(c) for c in glyph.contours]
    ccw = max(areas, key=abs) > 0
    samples = [sample(c) for c in glyph.contours]
    segs = []
    for S in samples:
        pts = [s[0] for s in S]
        segs += [(pts[q], pts[(q + 1) % len(pts)]) for q in range(len(pts))]
    segs = np.array(segs)
    polys = []
    sign = 1 if ccw else -1  # outward: the right-hand normal where the ink is on the left
    # every sample's section: its weight, and the sample facing it
    allpts = np.array([s[0] for S in samples for s in S])
    raw, facing = [], []
    for S in samples:
        ks, fs = np.full(len(S), np.nan), np.full(len(S), -1)
        for q, (p, t, _corner) in enumerate(S):
            nrm = sign * np.array([t[1], -t[0]])
            d, th = raycast(p, -nrm, segs)
            if d is not None and abs(float(t @ th)) > PARALLEL:
                ks[q] = min(1.0, max(0.0, (d - THIN) / (THICK - THIN)))
                fs[q] = int(np.argmin(np.linalg.norm(allpts - (p - nrm * d), axis=1)))
        raw.append(ks)
        facing.append(fs)
    flatk = np.concatenate(raw)
    paired = []
    for ks, fs in zip(raw, facing):
        # a section's two sides alike: the mean of the weights either side
        other = np.where(fs >= 0, flatk[np.maximum(fs, 0)], np.nan)
        paired.append(np.where(np.isnan(other), ks, np.nanmean(np.stack([ks, other]), axis=0)))
    for S, ks in zip(samples, paired):
        N = len(S)
        # smoothed along the outline (cyclic), the unmeasured filled from around
        arc = np.concatenate([[0], np.cumsum([np.linalg.norm(S[(q + 1) % N][0] - S[q][0]) for q in range(N - 1)])])
        total = arc[-1] + np.linalg.norm(S[0][0] - S[-1][0])
        valid = ~np.isnan(ks)
        if not valid.any():
            ks[:] = 0
            valid[:] = True
        sm = np.empty(N)
        for q in range(N):
            dd = np.abs(arc - arc[q])
            dd = np.minimum(dd, total - dd)
            w = np.exp(-0.5 * (dd / SIGMA) ** 2) * valid
            sm[q] = (w * np.nan_to_num(ks)).sum() / w.sum() if w.sum() > 1e-6 else 0
        moved = []
        for q, (p, t, _corner) in enumerate(S):
            nrm = sign * np.array([t[1], -t[0]])
            moved.append(p + np.array([nrm[0] * AX * sm[q] / 2, nrm[1] * AY / 2]))
        # corners: the samples either side mitred (where their offset lines meet)
        out = []
        for q in range(N):
            # a convex corner only (turning away from the ink); a crotch's
            # moved sides cross, and the cleaning cuts the loop off
            if S[q][2] and sign * (S[q][1][0] * S[(q + 1) % N][1][1] - S[q][1][1] * S[(q + 1) % N][1][0]) > 0:
                t1, t2 = S[q][1], S[(q + 1) % N][1]
                p1, p2 = moved[q], moved[(q + 1) % N]
                den = t1[0] * t2[1] - t1[1] * t2[0]
                if abs(den) > 1e-6:
                    u = ((p2 - p1)[0] * t2[1] - (p2 - p1)[1] * t2[0]) / den
                    m = p1 + u * t1
                    if np.linalg.norm(m - p1) < 3 * AX and np.linalg.norm(m - p2) < 3 * AX:
                        out.append(m)
                        continue
            out.append(moved[q])
        polys.append(out)
    return polys


def fit_cubic(pts, t0, t1):
    """one cubic from pts[0] to pts[-1], end tangents t0 t1, lengths by least squares"""
    P0, P3 = pts[0], pts[-1]
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    if d[-1] < 1e-6:
        return None, 0
    u = d / d[-1]
    for _ in range(3):  # parameters re-estimated by nearest point (Newton-free: chord)
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        A1 = b1[:, None] * t0
        A2 = -b2[:, None] * t1
        R = pts - (b0 + b1)[:, None] * P0 - (b2 + b3)[:, None] * P3
        M = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
        r = np.array([np.sum(A1 * R), np.sum(A2 * R)])
        try:
            la, lb = np.linalg.solve(M, r)
        except np.linalg.LinAlgError:
            la = lb = d[-1] / 3
        if la <= 1e-3 or lb <= 1e-3 or la > d[-1] or lb > d[-1]:
            la = lb = d[-1] / 3
        ctrl = [P0, P0 + la * t0, P3 - lb * t1, P3]
        # reparametrise: closest t on a fine sampling
        ts = np.linspace(0, 1, 200)
        curve = np.array([bez(ctrl, t) for t in ts])
        dist = np.linalg.norm(pts[:, None, :] - curve[None, :, :], axis=2)
        u = ts[np.argmin(dist, axis=1)]
    err = np.min(dist, axis=1)
    return ctrl, err


def tangent_at(poly, i, w=6):
    n = len(poly)
    return unit(poly[(i + w) % n] - poly[(i - w) % n])


def fit_contour(poly):
    """poly (closed, dense) -> list of cubic/line segments"""
    poly = np.array(poly)
    n = len(poly)
    # corners: a sharp turn between the directions just before and after
    turn = np.zeros(n)
    for i in range(n):
        a = unit(poly[i] - poly[(i - 2) % n])
        b = unit(poly[(i + 2) % n] - poly[i])
        turn[i] = math.degrees(math.acos(max(-1, min(1, float(a @ b)))))
    corners = [i for i in range(n) if turn[i] > CORNER and turn[i] >= turn[(i - 1) % n] and turn[i] >= turn[(i + 1) % n]]
    # dedupe neighbours
    corners = [c for k, c in enumerate(corners) if not corners or k == 0 or c - corners[k - 1] > 3]
    # extrema: tangent x or y changing sign (away from corners)
    splits = set(corners)
    tans = [tangent_at(poly, i) for i in range(n)]
    for i in range(n):
        if any(min((i - c) % n, (c - i) % n) < 6 for c in corners):
            continue
        a, b = tans[i], tans[(i + 1) % n]
        for q in (0, 1):
            if a[q] * b[q] < 0 and abs(a[q]) < 0.2:
                # the sample nearer the zero
                splits.add(i if abs(a[q]) < abs(b[q]) else (i + 1) % n)
    splits = sorted(splits)
    if not splits:
        splits = [0]
    fixed_tan = {}
    for s in splits:
        if s in corners:
            continue
        t = tans[s]
        # an extreme: exactly horizontal or vertical
        if abs(t[0]) < abs(t[1]):
            fixed_tan[s] = np.array([0.0, math.copysign(1, t[1])])
        else:
            fixed_tan[s] = np.array([math.copysign(1, t[0]), 0.0])
    out = []

    def run(i, j):
        idx = [(i + m) % n for m in range(((j - i) % n or n) + 1)]
        pts = poly[idx]
        straight = np.max(np.abs((lambda v, w: v[0] * w[:, 1] - v[1] * w[:, 0])(unit(pts[-1] - pts[0]), pts - pts[0]))) if len(pts) > 2 else 0
        if straight < 0.8:
            out.append(("line", pts[-1]))
            return
        t0 = fixed_tan.get(i, unit(pts[min(3, len(pts) - 1)] - pts[0]))
        t1 = fixed_tan.get(j, unit(pts[-1] - pts[max(0, len(pts) - 4)]))
        if i in corners:
            t0 = unit(pts[min(4, len(pts) - 1)] - pts[0])
        if j in corners:
            t1 = unit(pts[-1] - pts[max(0, len(pts) - 5)])
        ctrl, err = fit_cubic(pts, t0, t1)
        if ctrl is None:
            out.append(("line", pts[-1]))
            return
        if err.max() > TOL and len(pts) > 12:
            k = idx[int(np.argmax(err[3:-3])) + 3] if len(pts) > 8 else idx[len(idx) // 2]
            fixed_tan[k] = tans[k]
            run(i, k)
            run(k, j)
            return
        out.append(("curve", ctrl[1], ctrl[2], ctrl[3]))

    for a, b in zip(splits, splits[1:] + splits[:1]):
        run(a, b)
    return poly[splits[0]], out


def R(p):
    return (round(float(p[0])), round(float(p[1])))


def pilot(name):
    g = src[name]
    rec = mb.contours_only(g)
    wide = RecordingPen()
    rec.replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), (1, 0, -SLANT, 1, 0, 0)))
    flat = merged_glyph(wide)
    polys = offset_glyph(flat)
    path = pathops.Path()
    pen = path.getPen()
    for poly in polys:
        pen.moveTo(tuple(poly[0]))
        for p in poly[1:]:
            pen.lineTo(tuple(p))
        pen.closePath()
    path = pathops.simplify(path, fix_winding=True)
    # back to the slanted frame (and AX/2 right, as make_bold)
    out = ufoLib2.objects.Glyph(name)
    gp = out.getPen()
    rec = RecordingPen()
    path.draw(rec)
    contours = []
    for op, args in rec.value:
        if op == "moveTo":
            contours.append([])
        if args:
            contours[-1].append(np.array(args[-1], float))
    for pts in contours:
        # slivers the cleaning leaves (a crotch's crossing sides)
        if abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2 < 800:
            continue
        pts = [np.array([p[0] + AX / 2 + SLANT * p[1], p[1]]) for p in pts]
        # resample densely (pathops may merge collinear points)
        dense = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            m = max(1, int(np.linalg.norm(b - a) / STEP))
            dense += [a + (b - a) * s / m for s in range(m)]
        start, segs = fit_contour(dense)
        gp.moveTo(R(start))
        for s in segs:
            if s[0] == "line":
                gp.lineTo(R(s[1]))
            else:
                gp.curveTo(R(s[1]), R(s[2]), R(s[3]))
        gp.closePath()
    return out


if __name__ == "__main__":
    dst = ufoLib2.Font()
    for n in sys.argv[2:]:
        g = pilot(n)
        g.width = 0
        dst.newGlyph(n)
        g.draw(dst[n].getPen())
        dst[n].width = src[n].width
    dst.save(sys.argv[1], overwrite=True)
