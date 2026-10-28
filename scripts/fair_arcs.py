"""Whole arcs of an outline refitted fair: their curvature changing
gently along them, continuous where two curves meet, rising from nothing
where a curve leaves a line.

An arc runs between two corners (all of a contour without one: o): its
lines and curves, joined smoothly. Its nodes and handles are moved
together (Levenberg-Marquardt) to lessen the curvature's relative change
along the arc (the squared change of log |k| per unit, FAIR: a tight turn
that rises and falls cleanly costs no more than a gentle one, so the
Italic's sharp inner turns stay sharp), its jump at each join (JOIN), a
curve bending back where it bent one way (BEND); the outline is held by
the old outline's samples, each to its nearest point on the new. A curve
next to a line is split in two (a transition, its curvature only fading
towards the line). A node at a corner stays; one between a line and a
curve slides along the line (the curve starts earlier or later); an
extreme slides along its tangent and keeps it, its handles no shorter
than drawn; any other node moves and turns. An arc is taken only where it stays within LIMIT units of the old
one; one holding a cubic too short to bend or doubling back (the
cleaning's leftovers) is left as it is, and a short run of curves between two
lines (a serif's bracket) and a curve at a slit are held as drawn.

The person's review (2026-10-28, combs today | faired): FONT-DESIGN.md.
Run from stroke_bold (the Bold Italic) on the cleaned outline; as a study
on a UFO's glyphs:

    .venv/bin/python -I scripts/fair_arcs.py IN.ufo OUT.ufo [glyph ...]
"""
import math
import sys

import numpy as np

FAIR = 3000.0  # weight of the curvature's relative change
K0 = 1e-3  # (a curvature under this counts as about straight)
JOIN = 3e4  # weight of a jump at a join (per 1/unit)
BEND = 1e5  # weight of a curve bending back, or a transition swelling (per 1/unit)
LIMIT = 6.0  # units the new arc may stray from the old (3: n m h u v w refused)
SLIT = 120  # degrees: a crotch turning more is a slit
BRACKET = 120  # units: curves between two lines shorter than this are a bracket
SHORT = 8  # units: a cubic with a shorter chord is not refitted
SMOOTH = math.cos(math.radians(3))  # a node turning less is a smooth join (made exactly so)
NK = 16  # curvature samples per cubic
STEP = 4.0  # units between the old outline's samples
OUTER = 3  # rounds of matching the samples to the new outline
INNER = 15  # steps per round (6 and 30: within a unit of these)
DENSE = 150  # points per segment the samples are first matched to


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def bez(p, t):
    t = np.asarray(t, float)[..., None]
    u = 1 - t
    return u ** 3 * p[0] + 3 * u * u * t * p[1] + 3 * u * t * t * p[2] + t ** 3 * p[3]


def dbez(p, t):
    t = np.asarray(t, float)[..., None]
    u = 1 - t
    return 3 * u * u * (p[1] - p[0]) + 6 * u * t * (p[2] - p[1]) + 3 * t * t * (p[3] - p[2])


def ddbez(p, t):
    t = np.asarray(t, float)[..., None]
    return 6 * (1 - t) * (p[2] - 2 * p[1] + p[0]) + 6 * t * (p[3] - 2 * p[2] + p[1])


def kappa(p, t):
    d1, d2 = dbez(p, t), ddbez(p, t)
    sp = np.linalg.norm(d1, axis=-1)
    return (d1[..., 0] * d2[..., 1] - d1[..., 1] * d2[..., 0]) / np.maximum(sp, 1e-9) ** 3, sp


def split(p, t):
    a, b = p[0] + (p[1] - p[0]) * t, p[1] + (p[2] - p[1]) * t
    c = p[2] + (p[3] - p[2]) * t
    d, e = a + (b - a) * t, b + (c - b) * t
    f = d + (e - d) * t
    return np.array([p[0], a, d, f]), np.array([f, e, c, p[3]])


def tangents(s):
    """a segment's direction at its start and end"""
    a = next((s[i] - s[0] for i in range(1, len(s)) if np.linalg.norm(s[i] - s[0]) > 1e-9), s[-1] - s[0])
    b = next((s[-1] - s[i] for i in range(len(s) - 2, -1, -1) if np.linalg.norm(s[-1] - s[i]) > 1e-9), s[-1] - s[0])
    return unit(a), unit(b)


def arcs(segs):
    """the contour's arcs: (first segment, count, closed), runs of
    segments joined smoothly holding a curve"""
    L = len(segs)
    smooth = [float(tangents(segs[k - 1])[1] @ tangents(segs[k])[0]) > SMOOTH for k in range(L)]
    if all(smooth):
        return [(0, L, True)] if any(len(s) == 4 for s in segs) else []
    out = []
    starts = [k for k in range(L) if not smooth[k]]
    for a, b in zip(starts, starts[1:] + [starts[0] + L]):
        if any(len(segs[k % L]) == 4 for k in range(a, b)):
            out.append((a, b - a, False))
    return out


def brackets(run, closed):
    """per segment of an arc: is it a serif's bracket, one of up to three
    curves, under BRACKET units in all, between a line and a line or the
    arc's corner end"""
    m = len(run)
    line = [len(s) == 2 for s in run]
    length = [float(np.linalg.norm(np.diff(s, axis=0), axis=1).sum()) for s in run]
    out = [False] * m
    for a in range(m):  # a run of curves from a, after a line or the arc's start
        if line[a] or not (line[a - 1] if closed or a > 0 else True):
            continue
        b = a
        while b < a + m and not line[b % m] and (closed or b < m):
            b += 1
        inner = [x % m for x in range(a, b)]
        ends_at_line = (closed or b < m) and line[b % m]
        starts_at_line = closed or a > 0
        if (starts_at_line or ends_at_line) and len(inner) <= 3 and sum(length[x] for x in inner) < BRACKET:
            for x in inner:
                out[x] = True
    return out


class Arc:
    """an arc's segments (fade, per segment: +1 its curvature fades towards
    its end, a line follows; -1 towards its start; 0 free), its free
    parameters and its residuals; up: the frame's upright (an extreme's
    direction, with the level)"""

    def __init__(self, run, closed, fade, up, drawn=None, held=None):
        m = len(run)
        nn = m if closed else m + 1
        self.m, self.closed = m, closed
        self.lines = [len(s) == 2 for s in run]
        self.P = np.array([run[k][0] for k in range(m)] + ([] if closed else [run[-1][-1]]))
        T = []
        for i in range(nn):
            if not closed and i == 0:
                T.append(tangents(run[0])[0])
            elif not closed and i == m:
                T.append(tangents(run[-1])[1])
            else:
                T.append(unit(tangents(run[i - 1])[1] + tangents(run[i % m])[0]))
        self.T = np.array(T)
        # a short run of curves between two lines (a serif's bracket) is
        # held as drawn (stroke_bold moves it whole, keeping its radius)
        bracket = held if held is not None else brackets(run, closed)
        self.slots = []  # (node or segment, what) per free parameter
        extremes = set()
        for i in range(nn):
            if not closed and i in (0, m):
                continue  # a corner
            if bracket[i - 1] or bracket[i % m]:
                continue
            before, after = self.lines[i - 1], self.lines[i % m]
            t = self.T[i]
            if before and after:
                continue
            if before or after:
                # slides along the line, the curve leaving in its direction
                self.T[i] = tangents(run[i - 1])[1] if before else tangents(run[i % m])[0]
                self.slots.append((i, "t"))
            elif abs(t[1]) < 0.02 or abs(t[0] * up[1] - t[1] * up[0]) < 0.02:
                self.T[i] = np.array([math.copysign(1, t[0]), 0.0]) if abs(t[1]) < 0.02 else up * math.copysign(1, t[1] * up[1])
                self.slots.append((i, "t"))  # an extreme slides along its tangent
                extremes.add(i % nn)
            else:
                self.slots += [(i, "t"), (i, "n"), (i, "a")]
        self.h0 = np.array([(np.linalg.norm(s[1] - s[0]), np.linalg.norm(s[3] - s[2])) if len(s) == 4 else (0.0, 0.0)
                            for s in run])
        for j in range(m):
            if not self.lines[j] and not bracket[j]:
                self.slots += [(j, "la"), (j, "lb")]
        kind = {w: np.array([q for q, (_i, what) in enumerate(self.slots) if what == w], int)
                for w in ("t", "n", "a", "la", "lb")}
        self.kind = kind
        self.node = {w: np.array([self.slots[q][0] for q in kind[w]], int) for w in kind}
        self.handles = np.concatenate([kind["la"], kind["lb"]])
        # an extreme's handles no shorter than drawn: its flat stays (OE's
        # top, shortened, was hinted off O's zone)
        # (drawn: each segment's handles before it was split, else its own)
        drawn = drawn or [tuple(h) for h in self.h0]
        flat = [(q, drawn[self.slots[q][0]][0] / self.h0[self.slots[q][0]][0]) for q in kind["la"]
                if self.slots[q][0] in extremes]
        flat += [(q, drawn[self.slots[q][0]][1] / self.h0[self.slots[q][0]][1]) for q in kind["lb"]
                 if (self.slots[q][0] + 1) % nn in extremes]
        self.flat = np.array([q for q, _r in flat], int)
        self.flat_min = np.log(np.array([max(r, 1e-9) for _q, r in flat]))
        self.cubic = ~np.array(self.lines)
        self.ia = np.arange(m)
        self.ib = (self.ia + 1) % nn
        u = np.linspace(0, 1, NK)[:, None]
        v = 1 - u
        self.Bd1 = np.hstack([-3 * v * v, 3 * v * v - 6 * u * v, 6 * u * v - 3 * u * u, 3 * u * u])
        self.Bd2 = np.hstack([6 * v, -12 * v + 6 * u, 6 * v - 12 * u, 6 * u])
        # each curve's bend where it bends one way only (else 0): it may not
        # bend back
        ts = np.linspace(0, 1, NK)
        sign = []
        for s in run:
            if len(s) == 2:
                sign.append(0)
                continue
            k, _sp = kappa(s, ts)
            sg = np.sign(k[np.abs(k) > 2e-4])
            sign.append(int(sg[0]) if len(sg) and (sg == sg[0]).all() else 0)
        self.sign, self.fade = np.array(sign, float), np.array(fade, float)
        js = [j for j in range(m if closed else m - 1) if not (self.lines[j] and self.lines[(j + 1) % m])]
        self.ja, self.jb = np.array(js, int), (np.array(js, int) + 1) % m
        # the old outline's samples, every STEP units
        pts = []
        for s in run:
            length = sum(np.linalg.norm(s[q + 1] - s[q]) for q in range(len(s) - 1))
            c = max(3, int(length / STEP))
            ts = np.arange(c) / c
            pts.append(bez(s, ts) if len(s) == 4 else s[0] + ts[:, None] * (s[1] - s[0]))
        if not closed:
            pts.append(run[-1][-1][None])
        self.target = np.concatenate(pts)
        self.old = run

    def build_x(self, z):
        """the arc's control points (m, 4, 2), a line as a cubic at thirds"""
        P, T = self.P.copy(), self.T.copy()
        k, nd = self.kind, self.node
        nrm = np.stack([-self.T[:, 1], self.T[:, 0]], axis=1)
        P[nd["t"]] += z[k["t"]][:, None] * self.T[nd["t"]]
        P[nd["n"]] += z[k["n"]][:, None] * nrm[nd["n"]]
        c, s = np.cos(z[k["a"]])[:, None], np.sin(z[k["a"]])[:, None]
        T[nd["a"]] = c * self.T[nd["a"]] + s * nrm[nd["a"]]
        hl = self.h0.copy()
        hl[nd["la"], 0] *= np.exp(z[k["la"]])
        hl[nd["lb"], 1] *= np.exp(z[k["lb"]])
        A, B = P[self.ia], P[self.ib]
        cub = self.cubic[:, None]
        X = np.empty((self.m, 4, 2))
        X[:, 0], X[:, 3] = A, B
        X[:, 1] = np.where(cub, A + hl[:, :1] * T[self.ia], A + (B - A) / 3)
        X[:, 2] = np.where(cub, B - hl[:, 1:] * T[self.ib], A + 2 * (B - A) / 3)
        return X

    def build(self, z):
        X = self.build_x(z)
        return [X[j][[0, 3]] if self.lines[j] else X[j] for j in range(self.m)]

    def assign(self, segs):
        """each old sample's nearest point on segs (segment, t): matched
        on a grid, then exactly (Newton on t)"""
        ts = np.linspace(0, 1, DENSE)
        grid = np.concatenate([bez(s, ts) if len(s) == 4 else s[0] + ts[:, None] * (s[1] - s[0]) for s in segs])
        idx = np.linalg.norm(self.target[:, None] - grid[None], axis=2).argmin(axis=1)
        self.nj, self.nt = idx // DENSE, ts[idx % DENSE]
        for j, s in enumerate(segs):
            sel = np.nonzero(self.nj == j)[0]
            q, t = self.target[sel], self.nt[sel]
            for _ in range(4):
                if len(s) == 4:
                    p, d, dd = bez(s, t), dbez(s, t), ddbez(s, t)
                else:
                    p = s[0] + t[:, None] * (s[1] - s[0])
                    d, dd = np.repeat((s[1] - s[0])[None], len(t), axis=0), np.zeros((len(t), 2))
                f = np.sum((p - q) * d, axis=1)
                df = np.sum(d * d, axis=1) + np.sum((p - q) * dd, axis=1)
                t = np.clip(t - f / np.where(np.abs(df) > 1e-9, df, 1e-9), 0, 1)
            self.nt[sel] = t
        u = self.nt[:, None]
        v = 1 - u
        self.Bfit = np.hstack([v ** 3, 3 * v * v * u, 3 * v * u * u, u ** 3])

    def residuals(self, z):
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
            return self._residuals(z)

    def _residuals(self, z):
        X = self.build_x(z)
        out = [(np.einsum("nq,nqd->nd", self.Bfit, X[self.nj]) - self.target).ravel()]
        D1 = np.einsum("kq,mqd->mkd", self.Bd1, X)
        D2 = np.einsum("kq,mqd->mkd", self.Bd2, X)
        sp = np.maximum(np.hypot(D1[..., 0], D1[..., 1]), 1e-9)
        k = (D1[..., 0] * D2[..., 1] - D1[..., 1] * D2[..., 0]) / sp ** 3
        k[~self.cubic] = 0
        c = self.cubic
        ds = (sp[c, :-1] + sp[c, 1:]) / 2 / (NK - 1)
        out.append((math.sqrt(FAIR) * np.diff(np.log(np.abs(k[c]) + K0), axis=1) / np.sqrt(ds)).ravel())
        sign, fade = self.sign[:, None], self.fade[:, None]
        out.append((BEND * np.minimum(0, sign * k) * (sign != 0)).ravel())
        dk = np.diff(np.abs(k), axis=1)
        out.append((BEND * np.maximum(0, np.where(fade > 0, dk, -dk)) * (fade != 0)).ravel())
        out.append(JOIN * (k[self.ja, -1] - k[self.jb, 0]))
        out.append(10 * np.maximum(0, z[self.handles] - 1.0))  # (no loops)
        out.append(1000 * np.minimum(0, z[self.flat] - self.flat_min))
        return np.concatenate(out)

    def solve(self):
        z = np.zeros(len(self.slots))
        if not len(z):
            return self.old
        eps = 1e-4
        for _outer in range(OUTER):
            self.assign(self.build(z))
            lam = 1e-2
            r = self.residuals(z)
            if not np.isfinite(r).all():  # a curve with a cusp: left as it is
                return self.old if _outer == 0 else self.build(z)
            for _ in range(INNER):
                J = np.empty((len(r), len(z)))
                for q in range(len(z)):
                    dz = z.copy()
                    dz[q] += eps
                    J[:, q] = (self.residuals(dz) - r) / eps
                A, g = J.T @ J, J.T @ r
                while lam <= 1e8:
                    step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
                    nr = self.residuals(z + step)
                    if nr @ nr < r @ r:
                        z, r = z + step, nr
                        lam = max(1e-6, lam / 3)
                        break
                    lam *= 10
                if lam > 1e8 or np.abs(step).max() < 1e-6:
                    break
        return self.build(z)


def apart(a, b):
    """how far two runs of segments are apart, both ways"""
    def pts(segs, n):
        ts = np.linspace(0, 1, n)
        return np.concatenate([bez(s, ts) if len(s) == 4 else s[0] + ts[:, None] * (s[1] - s[0]) for s in segs])

    def one_way(p, q):  # p's points to the polyline q
        e = q[1:] - q[:-1]
        best = np.full(len(p), np.inf)
        for i in range(0, len(p), 200):
            w = p[i:i + 200, None] - q[None, :-1]
            t = np.clip(np.sum(w * e[None], axis=2) / np.maximum(np.sum(e * e, axis=1), 1e-12)[None], 0, 1)
            best[i:i + 200] = np.linalg.norm(w - t[..., None] * e[None], axis=2).min(axis=1)
        return best.max()
    return max(one_way(pts(a, 60), pts(b, 300)), one_way(pts(b, 60), pts(a, 300)))


def degenerate(s):
    """a cubic too short to bend or doubling back on its chord"""
    if len(s) == 2:
        return False
    chord = s[3] - s[0]
    if np.linalg.norm(chord) < SHORT:
        return True
    return bool(np.dot(s[1] - s[0], chord) < 0 or np.dot(s[3] - s[2], chord) < 0
                or np.dot(s[2] - s[1], chord) < -0.5 * np.dot(chord, chord))


def fair_contour(segs, up):
    """a contour's segments (arrays: 2 points a line, 4 a cubic) with each
    arc refitted fair where it stays within LIMIT; and per arc (start,
    count, how far it moved, taken)"""
    L = len(segs)
    new = [[s] for s in segs]
    report = []
    pts = np.concatenate([s[:-1] for s in segs])
    sign = np.sign(np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1]))

    def slit(t0, t1):
        """a crotch closing to a slit (g's bowl into its stem): concave,
        turning more than SLIT degrees"""
        cross = t0[0] * t1[1] - t0[1] * t1[0]
        return sign * cross < 0 and float(t0 @ t1) < math.cos(math.radians(SLIT))
    for a, n, closed in arcs(segs):
        run = [segs[(a + k) % L] for k in range(n)]
        if any(degenerate(s) for s in run):
            report.append((a, n, math.inf, False))
            continue
        cut, fade, owner, drawn = [], [], [], []
        held = brackets(run, closed)
        if not closed:  # the curves at a slit held as drawn (its width is the drawing's)
            if len(run[0]) == 4 and slit(tangents(segs[(a - 1) % L])[1], tangents(run[0])[0]):
                held[0] = True
            if len(run[-1]) == 4 and slit(tangents(run[-1])[1], tangents(segs[(a + n) % L])[0]):
                held[-1] = True
        for k, s in enumerate(run):
            # (an open arc's ends are corners, not lines)
            before = (closed or k > 0) and len(run[k - 1]) == 2
            after = (closed or k < n - 1) and len(run[(k + 1) % n]) == 2
            if len(s) == 4 and before != after and not held[k]:
                cut += split(s, 0.5)
                h = (np.linalg.norm(s[1] - s[0]), np.linalg.norm(s[3] - s[2]))
                drawn += [(h[0], 0.0), (0.0, h[1])]
                fade += [1 if after else -1] * 2
                owner += [k, k]
            else:
                cut.append(s)
                drawn.append((np.linalg.norm(s[1] - s[0]), np.linalg.norm(s[3] - s[2])) if len(s) == 4 else (0.0, 0.0))
                fade.append(0)
                owner.append(k)
        out = Arc(cut, closed, fade, up, drawn, [held[k] for k in owner]).solve()
        moved = apart(run, out)
        report.append((a, n, moved, moved <= LIMIT))
        if moved <= LIMIT:
            for k in range(n):
                new[(a + k) % L] = [out[q] for q in range(len(out)) if owner[q] == k]
    return [s for piece in new for s in piece], report


def segments(value):
    """a RecordingPen value's contours, as segment arrays (None where it
    holds anything but lines and cubics)"""
    out, cur, at = [], None, None
    for op, args in value:
        if op == "moveTo":
            cur, at = [], np.array(args[0], float)
        elif op == "lineTo":
            q = np.array(args[0], float)
            cur.append(np.array([at, q]))
            at = q
        elif op == "curveTo" and len(args) == 3:
            cur.append(np.array([at, *args], float))
            at = cur[-1][-1]
        elif op in ("closePath", "endPath"):
            if op == "endPath":
                return None
            if cur and np.linalg.norm(at - cur[0][0]) > 1e-6:
                cur.append(np.array([at, cur[0][0]]))
            out.append(cur)
        else:
            return None
    return out


def draw(pen, contours):
    for segs in contours:
        pen.moveTo(tuple(map(float, segs[0][0])))
        for s in segs:
            if len(s) == 2:
                pen.lineTo(tuple(map(float, s[1])))
            else:
                pen.curveTo(*(tuple(map(float, q)) for q in s[1:]))
        pen.closePath()


def main():
    """the study: a UFO's glyphs (its slanted frame) faired"""
    import ufoLib2
    from fontTools.pens.recordingPen import RecordingPen
    src, dst = sys.argv[1], sys.argv[2]
    font = ufoLib2.Font.open(src)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    up = unit(np.array([slant, 1.0]))
    cmap = {chr(u): g.name for g in font for u in g.unicodes}
    names = [cmap.get(a, a) for a in sys.argv[3:]] or sorted(g.name for g in font if g.contours)
    for name in names:
        g = font[name]
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
        cs = segments(rec.value)
        if cs is None:
            continue
        res = [fair_contour(c, up) for c in cs]
        g.clearContours()
        draw(g.getPen(), [r[0] for r in res])
        rep = [x for r in res for x in r[1]]
        print("%-12s arcs %2d  moved %s" % (name, len(rep), [round(float(x[2]), 1) for x in rep if x[3]]),
              "refused", [round(float(x[2]), 1) for x in rep if not x[3]])
    font.save(dst, overwrite=True)


if __name__ == "__main__":
    main()
