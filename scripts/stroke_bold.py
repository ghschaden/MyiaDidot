"""Emboldening by strokes: the Bold Italic drawn with the Italic's curves.

embolden_by_strokes(rec, ...) takes an outline (deslanted, widened) and
moves it out as a pen of a heavier weight would draw it: the outline is
sampled every STEP units, at each sample the stroke's section is measured
(a ray into the ink to the facing side), its weight k (0 hairline .. 1
stem, between thin and thick) shared by both sides of the section and
smoothed along the outline (SIGMA), so a stroke's weight changes gradually
and its cut ends stay thin. A sample moves by (hair + (ax - hair) * k) / 2
across and ay / 2 up or down. Each sample keeps the segment it came from,
so the moved outline is redrawn with the source's own segments: one cubic
for each curve (handle lengths by least squares, tangents from the moved
outline, an extreme kept level or upright in the slanted frame and its
node slid to where the moved outline is so again), one line for each line
(moved parallel by its mean weight). Convex corners are mitred; a crotch's
moved sides cross and the cleaning (pathops) cuts them at their meeting
point; a concave round too tight to be moved (radius under half the
offset: r's ball meeting its arm) becomes such a crotch. The cleaning's
splits at smooth nodes are joined again.

The person's review, the study and its choices: FONT-DESIGN.md (Bold
Italic from strokes), scripts/pilot/strokes_fit.py.
"""
import math

import numpy as np
import ufoLib2
from derive import ZONE_BOTTOMS, ZONE_TOPS, merged_glyph
from fontTools.pens.recordingPen import RecordingPen

STEP = 2.0          # units between samples
BLOCK = 32          # samples whose sections are measured together
SIGMA = 90.0        # smoothing of the weight along the outline (units; 45 left г a knee)
PARALLEL = math.cos(math.radians(40))  # a facing side within this of parallel: a section
CORNER = 28.0       # degrees: a turn this sharp at a node is a corner
# a concave round between two lines (a serif's bracket) under TIGHT times its
# largest offset in radius moves whole (moved point by point its radius would
# shrink by the offset, to a corner and a jog)
TIGHT = 2.0
# a heavy stroke gains this share of its offset up and down too (0: across
# only, z s г spines lighter than the stems; 1, as by weight: rounds dark;
# the person, 2026-10-28)
FULL = 0.75
ZONES = ZONE_TOPS + ZONE_BOTTOMS
CLEAR = 0.25  # of the white in front, the most a side may move into it
ZONE_NEAR = 100  # units
SHALLOW = 0.55  # (about 33 degrees from level, fading to 44)
ACROSS = 0.45  # (z's spine, 25° from level, read as a hairline at 1: the person, 2026-10-28)
OPEN = 1e9  # (smooth's length of a run that does not close)
TINY = 4  # units: a line this short left by the overlap removal is dropped (7: 3)
SLIVER = 800        # area under which a cleaned contour is a crotch's crossing sides
TS = np.linspace(0, 1, 200)  # the fit's sampling of a cubic


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def bez(p, t):
    """cubic p (4 points) at t (a number or an array)"""
    t = np.asarray(t, float)[..., None]
    u = 1 - t
    return u ** 3 * p[0] + 3 * u * u * t * p[1] + 3 * u * t * t * p[2] + t ** 3 * p[3]


def dbez(p, t):
    t = np.asarray(t, float)[..., None]
    u = 1 - t
    return 3 * u * u * (p[1] - p[0]) + 6 * u * t * (p[2] - p[1]) + 3 * t * t * (p[3] - p[2])


def fit_cubic(pts, t0, t1):
    """one cubic from pts[0] to pts[-1], end tangents t0 t1, handle lengths
    by least squares; (control points, each point's distance to it)"""
    P0, P3 = pts[0], pts[-1]
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    if d[-1] < 1e-6:
        return None, 0
    u = d / d[-1]
    for _ in range(3):  # parameters re-estimated by the nearest point
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
        curve = bez(ctrl, TS)
        dist = np.linalg.norm(pts[:, None, :] - curve[None, :, :], axis=2)
        u = TS[np.argmin(dist, axis=1)]
    return ctrl, np.min(dist, axis=1)


def smooth(ks, arc, total):
    """ks (nan: unmeasured, filled from around) smoothed along a closed
    outline at arc lengths arc (its length total, OPEN: a run, not closed),
    by SIGMA"""
    ks = ks.copy()
    valid = ~np.isnan(ks)
    if not valid.any():
        ks[:] = 0
        valid[:] = True
    ks = np.nan_to_num(ks)
    if total <= 12 * SIGMA:  # all of a short contour
        dd = np.abs(arc[:, None] - arc[None, :])
        dd = np.minimum(dd, total - dd)
        w = np.exp(-0.5 * (dd / SIGMA) ** 2) * valid[None, :]
        ws = w.sum(axis=1)
        return np.where(ws > 1e-6, (w * ks[None, :]).sum(axis=1) / np.maximum(ws, 1e-12), 0)
    # each sample's neighbours within 5 sigma, round the seam
    N = len(arc)
    ext = np.concatenate([arc - total, arc, arc + total])
    first = np.searchsorted(ext, arc - 5 * SIGMA)
    width = int((np.searchsorted(ext, arc + 5 * SIGMA, side="right") - first).max())
    cols = first[:, None] + np.arange(width)[None, :]
    inside = np.abs(ext[np.minimum(cols, 3 * N - 1)] - arc[:, None]) <= 5 * SIGMA
    cols = np.minimum(cols, 3 * N - 1)
    w = np.exp(-0.5 * ((ext[cols] - arc[:, None]) / SIGMA) ** 2) * inside * valid[cols % N]
    ws = w.sum(axis=1)
    return np.where(ws > 1e-6, (w * ks[cols % N]).sum(axis=1) / np.maximum(ws, 1e-12), 0)


class Strokes:
    """the gain: ax across a stem, hair across a hairline, ay up and down;
    thin / thick: the section widths of a hairline and a stem; slant: the
    frame's (its upright is an extreme's direction)"""

    def __init__(self, ax, ay, thin, thick, hair, slant):
        self.ax, self.ay, self.thin, self.thick, self.hair = ax, ay, thin, thick, hair
        self.upright = unit(np.array([-slant, 1.0]))

    def offset(self, k):
        return (self.hair + (self.ax - self.hair) * k) / 2

    def sample(self, contour):
        """the contour's segments, each [(point, tangent)] from its start node
        (t = 0) up to its end; per node: is it a corner (in, out tangents),
        is it an extreme; per segment: a line?"""
        P = contour.points
        n = len(P)
        ons = [i for i, p in enumerate(P) if p.type]
        segs, lines, nodes = [], [], []
        for k, i in enumerate(ons):
            j = ons[(k + 1) % len(ons)]
            offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
            pts = [np.array([P[q].x, P[q].y], float) for q in (i, *offs, j)]
            lines.append(len(pts) == 2)
            if len(pts) == 2:
                pts = [pts[0], pts[0] + (pts[1] - pts[0]) / 3, pts[0] + 2 * (pts[1] - pts[0]) / 3, pts[1]]
            length = sum(np.linalg.norm(pts[q + 1] - pts[q]) for q in range(3))
            m = max(2, int(length / STEP))
            ts = np.arange(m) / m
            ps, ds = bez(pts, ts), dbez(pts, ts)
            seg = []
            for s in range(m):
                d = ds[s]
                if np.linalg.norm(d) < 1e-9:
                    t = ts[s]
                    d = dbez(pts, min(1, t + 1e-3)) if t < 0.5 else dbez(pts, t - 1e-3)
                seg.append((ps[s], unit(d)))
            segs.append(seg)
            c = np.array([P[i].x, P[i].y], float)
            a = next(np.array([P[(i - q) % n].x, P[(i - q) % n].y], float) for q in range(1, n + 1)
                     if (P[(i - q) % n].x, P[(i - q) % n].y) != (P[i].x, P[i].y))
            b = next(np.array([P[(i + q) % n].x, P[(i + q) % n].y], float) for q in range(1, n + 1)
                     if (P[(i + q) % n].x, P[(i + q) % n].y) != (P[i].x, P[i].y))
            tin, tout = unit(c - a), unit(b - c)
            turn = math.degrees(math.acos(max(-1, min(1, float(tin @ tout)))))
            corner = turn > CORNER and not P[i].smooth
            t = unit(tin + tout)
            extreme = None
            if not corner:
                up = self.upright
                if abs(t[1]) < 0.02:
                    extreme = np.array([math.copysign(1, t[0]), 0.0])
                elif abs(t[0] - t[1] * up[0] / up[1]) < 0.02:
                    extreme = up * math.copysign(1, t[1])
            nodes.append({"corner": corner, "tin": tin, "tout": tout, "extreme": extreme})
        return segs, lines, nodes

    def weights(self, contours, sign):
        """each sample's weight (0 hairline .. 1 stem), paired across its
        section and smoothed along the outline; and the weight up and down:
        no more than its own section's (a serif beside a stem is a hairline,
        the stem's weight smoothed into it gains across only)"""
        flat = [s for c in contours for seg in c[0] for s in seg]
        pts = np.array([s[0] for s in flat])
        tan = np.array([s[1] for s in flat])
        starts = np.cumsum([0] + [sum(len(seg) for seg in c[0]) for c in contours])
        # the outline's chords, each contour closed on itself
        nxt = np.arange(1, len(pts) + 1)
        nxt[starts[1:] - 1] = starts[:-1]
        a, e = pts, pts[nxt] - pts
        raw, facing = np.full(len(flat), np.nan), np.full(len(flat), -1)
        own = np.full(len(flat), np.nan)  # the section's own weight, for the gain up and down
        gap = np.full(len(flat), np.inf)
        inward = -sign * np.stack([tan[:, 1], -tan[:, 0]], axis=1)
        def nearest(o, dr, chords):
            """each ray's (o + t dr) nearest crossing of the chords: t, the
            chord's index and where on it (inf where none)"""
            ca, ce = a[chords], e[chords]
            w = ca[None] - o[:, None]
            den = dr[:, None, 0] * ce[None, :, 1] - dr[:, None, 1] * ce[None, :, 0]
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (w[..., 0] * ce[None, :, 1] - w[..., 1] * ce[None, :, 0]) / den
                s = (w[..., 0] * dr[:, None, 1] - w[..., 1] * dr[:, None, 0]) / den
            t = np.where((np.abs(den) > 1e-9) & (t > 1.0) & (s >= 0) & (s <= 1), t, np.inf)
            rows = np.arange(len(o))
            col = np.argmin(t, axis=1)
            return t[rows, col], chords[col], s[rows, col]

        # rays into the ink, in blocks of samples, first against the chords
        # within reach of the block; those that meet none there against all
        reach = 2 * self.thick
        lo_c, hi_c = np.minimum(a, a + e), np.maximum(a, a + e)
        every = np.arange(len(a))
        for lo in range(0, len(pts), BLOCK):
            o, dr = pts[lo:lo + BLOCK], inward[lo:lo + BLOCK]
            near = np.nonzero(np.all((hi_c >= o.min(axis=0) - reach) & (lo_c <= o.max(axis=0) + reach), axis=1))[0]
            # the white in front (a counter, a loop's eye), within reach
            gap[lo:lo + BLOCK] = nearest(o, -dr, near)[0]
            d, idx, at = nearest(o, dr, near)
            far = d > reach
            if far.any():
                d[far], idx[far], at[far] = nearest(o[far], dr[far], every)
            el = np.linalg.norm(e[idx], axis=1)
            across = np.abs(np.sum(tan[lo:lo + BLOCK] * e[idx], axis=1)) > PARALLEL * np.maximum(el, 1e-12)
            hit = np.isfinite(d) & across
            q = lo + np.nonzero(hit)[0]
            # a shallow diagonal weighed by its width nearer the horizontal
            # (the gain is across x): across divided by its normal's x, at
            # least ACROSS (1: as measured); not a level stroke (a serif, a
            # bar: as measured, the rule fading in from 10 to 20 degrees)
            short = d[hit] <= reach  # (longer: along a stroke, under a stem)
            nx = np.abs(dr[:, 0])
            fade = np.clip((nx - 0.17) / 0.17, 0, 1)
            # (and not a hairline: z's curl read heavier closed its loop)
            fade = fade * np.clip((d - self.thin + 10) / 20, 0, 1)
            d = d / (1 - fade * (1 - np.maximum(nx, ACROSS)))
            raw[q] = np.clip((d[hit] - self.thin) / (self.thick - self.thin), 0, 1)
            # (a shallow diagonal's only, z's spine, under SHALLOW in its
            # normal's x: an upright stem gains nothing up and down, its weight
            # smoothed into its cut end would drop the foot; a steeper one, κ's
            # arm, would pull a waist where its hairline leg leaves it)
            slant = np.clip((SHALLOW + 0.15 - nx[hit]) / 0.15, 0, 1)
            own[q] = np.where(short, raw[q] * slant, 0)
            # the sample facing it: the hit chord's nearer end
            facing[q] = np.where(at[hit] < 0.5, idx[hit], nxt[idx[hit]])
        other = np.where(facing >= 0, raw[np.maximum(facing, 0)], np.nan)
        paired = np.where(np.isnan(other), raw, np.where(np.isnan(raw), other, (raw + other) / 2))
        out = []
        for c, (segs, _lines, nodes) in enumerate(contours):
            P = pts[starts[c]:starts[c + 1]]
            arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
            total = arc[-1] + np.linalg.norm(P[0] - P[-1])
            ks, mine = paired[starts[c]:starts[c + 1]], np.nan_to_num(own[starts[c]:starts[c + 1]])
            # smoothed between crotches (concave corners: two strokes meet
            # there, a stem's weight smoothed round it thickened the hairline
            # arch springing from it, m's joins filled black)
            first = np.cumsum([0] + [len(sg) for sg in segs])
            cuts = [int(first[k]) for k, nd in enumerate(nodes)
                    if nd["corner"] and sign * (nd["tin"][0] * nd["tout"][1] - nd["tin"][1] * nd["tout"][0]) < 0]
            if not cuts:
                sm, mn = smooth(ks, arc, total), smooth(mine, arc, total)
            else:
                sm, mn = np.empty(len(P)), np.empty(len(P))
                for a, b in zip(cuts, cuts[1:] + [cuts[0] + len(P)]):
                    run = np.arange(a, b) % len(P)
                    along = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P[run], axis=0), axis=1))])
                    sm[run] = smooth(ks[run], along, OPEN)
                    mn[run] = smooth(mine[run], along, OPEN)
            # a side moves at most CLEAR of the white in front of it, across
            # or up and down (z's loop: its eye closed from both sides)
            room = CLEAR * gap[starts[c]:starts[c + 1]]
            cap = smooth(np.clip((2 * room - self.hair) / (self.ax - self.hair), 0, 1), arc, total)
            capv = smooth(np.clip((2 * room / max(FULL, 1e-9) - self.hair) / (self.ax - self.hair), 0, 1), arc, total)
            out.append((np.minimum(sm, cap), np.minimum(np.minimum(sm, mn), capv)))
        return out

    def move(self, p, t, k, sign, kv=0.0):
        nrm = sign * np.array([t[1], -t[0]])
        # across by the stroke's offset; up and down by ay / 2, a heavy
        # stroke (kv, its own section's weight) by FULL its offset there too
        # (a diagonal spine, z's, gains as a stem does, in the direction it runs)
        # (fading out near the zones, ZONE_NEAR: there the extra gain would
        # push a shallow curve, z's top wave, past the overshoot)
        near = min(abs(p[1] - z) for z in ZONES) / ZONE_NEAR
        up = FULL * self.offset(kv) * min(1.0, near)
        return p + np.array([nrm[0] * self.offset(k), nrm[1] * max(self.ay / 2, up)])

    def mitre(self, p1, t1, p2, t2):
        den = t1[0] * t2[1] - t1[1] * t2[0]
        if abs(den) < 1e-6:
            return None
        u = ((p2 - p1)[0] * t2[1] - (p2 - p1)[1] * t2[0]) / den
        m = p1 + u * t1
        if np.linalg.norm(m - p1) < 3 * self.ax and np.linalg.norm(m - p2) < 3 * self.ax:
            return m
        return None

    def meet(self, a, ta, b, tb, start, end):
        """where the moved line arriving at a (from start's side) meets the
        one leaving b (towards end), if within both (None otherwise)"""
        den = ta[0] * tb[1] - ta[1] * tb[0]
        if abs(den) < 1e-6:
            return None
        u = ((b - a)[0] * tb[1] - (b - a)[1] * tb[0]) / den
        m = a + u * ta
        if float((m - start) @ ta) > 0 and float((end - m) @ tb) > 0:
            return m
        return None

    def crotches(self, segs, lines, nodes, kc, sign):
        """a tiny concave round whose radius is under half the offset there
        (r's ball meeting its arm) turns inside out when moved: drawn as a
        line between two corners, the cleaning cuts the crossing sides at
        their meeting point, a crotch (in place)"""
        L = len(segs)
        first = np.cumsum([0] + [len(s) for s in segs])
        for k in range(L):
            seg = segs[k]
            t0, t1 = seg[0][1], seg[-1][1]
            turn = math.acos(max(-1, min(1, float(t0 @ t1))))
            concave = sign * (t0[0] * t1[1] - t0[1] * t1[0]) < 0
            offset = self.offset(float(kc[first[k]:first[k + 1]].mean()))
            if lines[k] or not concave or turn < math.radians(45) or len(seg) * STEP / turn > offset / 2:
                continue
            lines[k] = True
            for nd in (nodes[k], nodes[(k + 1) % L]):
                nd["corner"], nd["extreme"] = True, None
            nodes[k]["tout"] = unit(segs[(k + 1) % L][0][0] - seg[0][0])
            nodes[(k + 1) % L]["tin"] = nodes[k]["tout"]

    def rigid(self, segs, lines, nodes, kc, sign):
        """the serifs' brackets (concave rounds between two lines, one curve
        or a few, radius under TIGHT offsets): moved point by point their
        radius shrinks by the offset, to a corner and a jog where it folds;
        such a round moves whole, by the shift of the corner its two sides
        make (so it meets both moved sides, its shape the source's): their
        (first segment, number of segments)"""
        L = len(segs)
        first = np.cumsum([0] + [len(s) for s in segs])
        found = []
        for k in range(L):
            if lines[k] or not lines[k - 1]:
                continue
            n = next((m for m in range(1, min(4, L - 1)) if lines[(k + m) % L]), None)
            run = [(k + m) % L for m in range(n or 0)]
            if not n or any(nodes[q]["corner"] for q in run + [(k + n) % L]):
                continue

            def concave(t0, t1):
                return sign * (t0[0] * t1[1] - t0[1] * t1[0]) < 0
            if not all(concave(segs[q][0][1], segs[q][-1][1]) for q in run):
                continue
            t0, t1 = segs[k][0][1], segs[run[-1]][-1][1]
            turn = math.acos(max(-1, min(1, float(t0 @ t1))))
            offset = self.offset(max(float(kc[first[q]:first[q + 1]].max()) for q in run))
            if turn < math.radians(30) or sum(len(segs[q]) for q in run) * STEP / turn > TIGHT * offset:
                continue
            found.append((k, n))
        return found

    def draw(self, glyph, anchors):
        """glyph (merged) -> RecordingPen of the moved outline, drawn with
        its segments (uncleaned); the moved nodes added to anchors"""
        def area(c):
            pts = [(p.x, p.y) for p in c.points]
            return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        sign = 1 if max((area(c) for c in glyph.contours), key=abs) > 0 else -1
        contours = [self.sample(c) for c in glyph.contours]
        ks = self.weights(contours, sign)
        rec = RecordingPen()
        for (segs, lines, nodes), (kc, kv) in zip(contours, ks):
            self.crotches(segs, lines, nodes, kc, sign)
            whole = self.rigid(segs, lines, nodes, kc, sign)
            inner = {(k + m) % len(segs) for k, n in whole for m in range(1, n)}
            moved, q = [], 0
            for seg in segs:
                moved.append([self.move(p, t, kc[q + s], sign, kv[q + s]) for s, (p, t) in enumerate(seg)])
                q += len(seg)
            L = len(segs)
            # an extreme moves along the outline (the offset is wider across
            # than up and down): its node slides to where the moved outline's
            # tangent is the extreme's, within a third of either segment
            for k in range(L):
                nd = nodes[k]
                if nd["extreme"] is None or lines[k - 1] or lines[k] or L < 2 or k in inner:
                    continue
                prev, here = moved[k - 1], moved[k]
                both = prev + here
                lo, hi = max(3, len(prev) - len(prev) // 3), min(len(both) - 3, len(prev) + len(here) // 3)

                def off(i, both=both, e=nd["extreme"]):
                    t = unit(both[i + 2] - both[i - 2])
                    return abs(t[0] * e[1] - t[1] * e[0])
                best = min(range(lo, hi + 1), key=off, default=len(prev))
                moved[k - 1], moved[k] = both[:best], both[best:]
            # each node's moved position(s), arriving and leaving; a line
            # moves parallel, by its weight along its length (its ends' alone
            # thin where the weight fades towards a cut end)
            first = np.cumsum([0] + [len(s) for s in segs])
            kline = [float(kc[first[k]:first[k + 1]].mean()) if lines[k] else None for k in range(L)]
            vline = [float(kv[first[k]:first[k + 1]].mean()) if lines[k] else None for k in range(L)]
            ends = []
            for k in range(L):
                nd = nodes[k]
                p = segs[k][0][0]
                kk, vv = kc[first[k]], kv[first[k]]
                ka, va = (kk, vv) if kline[k - 1] is None else (kline[k - 1], vline[k - 1])
                kb, vb = (kk, vv) if kline[k] is None else (kline[k], vline[k])
                if nd["corner"]:
                    a, b = self.move(p, nd["tin"], ka, sign, va), self.move(p, nd["tout"], kb, sign, vb)
                    convex = sign * (nd["tin"][0] * nd["tout"][1] - nd["tin"][1] * nd["tout"][0]) > 0
                    m = self.mitre(a, nd["tin"], b, nd["tout"]) if convex else None
                    if not convex and lines[k - 1] and lines[k]:
                        # a crotch between two lines: where they meet, if on both
                        m = self.meet(a, nd["tin"], b, nd["tout"], segs[k - 1][0][0], segs[(k + 1) % L][0][0])
                    ends.append((m, m) if m is not None else (a, b))
                elif kline[k - 1] is not None or kline[k] is not None:
                    t = unit(nd["tin"] + nd["tout"])
                    q = self.move(p, t, *((kb, sign, vb) if kline[k] is not None else (ka, sign, va)))
                    ends.append((q, q))
                else:
                    ends.append((moved[k][0], moved[k][0]))
            # a bracket moved whole: by the shift D of its sides' corner (D
            # on both sides' moved lines)
            shifts = {}
            for k, n in whole:
                j = (k + n) % L
                pa, pb = segs[k][0][0], segs[j][0][0]
                ta, tb = unit(nodes[k]["tin"] + nodes[k]["tout"]), unit(nodes[j]["tin"] + nodes[j]["tout"])
                ma = self.move(pa, ta, kline[k - 1], sign, vline[k - 1]) - pa
                mb = self.move(pb, tb, kline[j], sign, vline[j]) - pb
                # cross(ta, D - ma) = 0, cross(tb, D - mb) = 0
                A = np.array([[-ta[1], ta[0]], [-tb[1], tb[0]]])
                r = np.array([-ta[1] * ma[0] + ta[0] * ma[1], -tb[1] * mb[0] + tb[0] * mb[1]])
                D = np.linalg.solve(A, r)
                if np.linalg.norm(D) > 3 * self.ax:
                    continue
                for m in range(n + 1):
                    q = (k + m) % L
                    p = segs[q][0][0]
                    shifts[q] = unit(nodes[q]["tin"] + nodes[q]["tout"])
                    ends[q] = (p + D, p + D)
                    if m < n:
                        moved[q] = [p + D for p, _t in segs[q]]
            # each node's tangents on the moved outline (arriving, leaving)
            tans = []
            for k in range(L):
                nd = nodes[k]
                prev, here = moved[k - 1], moved[k]
                if nd["corner"]:
                    ta = unit(ends[k][0] - prev[-3]) if len(prev) > 3 else nd["tin"]
                    tb = unit(here[3] - ends[k][1]) if len(here) > 3 else nd["tout"]
                    tans.append((ta, tb))
                else:
                    t = unit(here[min(3, len(here) - 1)] - prev[-min(3, len(prev))])
                    if nd["extreme"] is not None:
                        t = nd["extreme"] * (1 if float(t @ nd["extreme"]) >= 0 else -1)
                    # a line runs on smoothly into a curve: the curve takes the
                    # moved line's direction (its ends move by different weights)
                    if lines[k - 1] != lines[k]:
                        t = (unit(ends[k][0] - ends[k - 1][1]) if lines[k - 1]
                             else unit(ends[(k + 1) % L][0] - ends[k][1]))
                    tans.append((t, t))
            for k, t in shifts.items():  # a bracket keeps its nodes' directions
                tans[k] = (t, t)
            anchors += [p for e in ends for p in e]
            rec.moveTo(tuple(ends[0][1]))
            for k in range(L):
                j = (k + 1) % L
                start, end = ends[k][1], ends[j][0]
                if lines[k]:
                    rec.lineTo(tuple(end))
                else:
                    pts = np.array([start] + moved[k][1:] + [end])
                    ctrl, _err = fit_cubic(pts, tans[k][1], tans[j][0])
                    if ctrl is None:
                        rec.lineTo(tuple(end))
                    else:
                        rec.curveTo(tuple(ctrl[1]), tuple(ctrl[2]), tuple(ctrl[3]))
                if j and not np.allclose(ends[j][0], ends[j][1]):
                    rec.lineTo(tuple(ends[j][1]))
            if not np.allclose(ends[0][0], ends[0][1]):
                rec.lineTo(tuple(ends[0][1]))
            rec.closePath()
        return rec


def tidy(glyph):
    """glyph without the overlap removal's near-zero lines (a node and its
    copy a unit apart): the copy goes, the node takes its smoothness"""
    for c in glyph.contours:
        while True:
            P = c.points
            ons = [i for i, p in enumerate(P) if p.type]
            for k, j in enumerate(ons):
                i = ons[k - 1]
                if P[j].type == "line" and math.hypot(P[j].x - P[i].x, P[j].y - P[i].y) < TINY and len(ons) > 2:
                    P[i].smooth = P[j].smooth
                    if i < j or j:
                        del P[j]
                    break
            else:
                break
    return glyph


def contour_area(c):
    pts = [(p.x, p.y) for p in c.points if p.type]
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def rejoined(contour, anchors):
    """contour with the cleaning's splits undone: a smooth node that is
    none of the moved nodes joins the cubics either side (refitted through
    both, exact where they are halves of one cubic)"""
    P = contour.points
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    pt = lambda q: np.array([P[q % n].x, P[q % n].y], float)  # noqa: E731
    segs = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
        segs.append([pt(i)] + [pt(q) for q in offs] + [pt(j)])

    def split_here(k):
        a, b = segs[k - 1], segs[k]
        here = b[0]
        if len(anchors) and np.min(np.linalg.norm(anchors - here, axis=1)) < 0.5:
            return True
        if len(a) == 2 or len(b) == 2:
            return True
        ta, tb = unit(here - a[-2]), unit(b[1] - here)
        return float(ta @ tb) < math.cos(math.radians(2))
    keep = [k for k in range(len(segs)) if split_here(k)] or [0]
    rec = RecordingPen()
    rec.moveTo(tuple(segs[keep[0]][0]))
    ts = np.linspace(0, 1, 40)[:-1]
    for a, b in zip(keep, keep[1:] + [keep[0] + len(segs)]):
        run = [segs[k % len(segs)] for k in range(a, b)]
        if len(run) == 1:
            sg = run[0]
            if len(sg) == 2:
                rec.lineTo(tuple(sg[1]))
            else:
                rec.curveTo(*(tuple(q) for q in sg[1:]))
            continue
        pts = np.concatenate([bez(sg, ts) for sg in run] + [run[-1][-1][None]])
        ctrl, _err = fit_cubic(pts, unit(run[0][1] - run[0][0]), unit(run[-1][-1] - run[-1][-2]))
        rec.curveTo(*(tuple(q) for q in ctrl[1:]))
    rec.closePath()
    return rec


def embolden_by_strokes(rec, ax, ay, thin, thick, hair, slant, sliver=SLIVER):
    """rec (a RecordingPen, upright frame) emboldened by its strokes, as a
    ufoLib2 Glyph, cleaned (contours under sliver units' area dropped);
    not shifted (the caller moves it by ax / 2)"""
    strokes = Strokes(ax, ay, thin, thick, hair, slant)
    flat = tidy(merged_glyph(rec))
    out = ufoLib2.objects.Glyph()
    if not flat.contours:
        return out
    anchors = []
    cleaned = merged_glyph(strokes.draw(flat, anchors))
    anchors = np.array(anchors)
    pen = out.getPen()
    for c in cleaned.contours:
        if contour_area(c) < sliver:
            continue
        rejoined(c, anchors).replay(pen)
    return out


def emboldened(job):
    """embolden_by_strokes for a process pool: job = (name, rec's value,
    its arguments); (name, the result's RecordingPen value, or None where
    it failed: the caller falls back)"""
    name, value, args = job
    rec = RecordingPen()
    rec.value = value
    try:
        glyph = embolden_by_strokes(rec, *args)
    except (ValueError, IndexError, ZeroDivisionError, np.linalg.LinAlgError):
        return name, None
    out = RecordingPen()
    glyph.draw(out)
    return name, out.value
