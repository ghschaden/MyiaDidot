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
node slid to where the moved outline is so again; then refitted so that
two curves meeting smoothly share one curvature, G2), one line for each line
(moved parallel by its mean weight). Convex corners are mitred; a crotch's
moved sides cross and the cleaning (pathops) cuts them at their meeting
point; a concave round too tight to be moved (radius under half the
offset: r's ball meeting its arm) becomes such a crotch. The cleaning's
splits at smooth nodes are joined again. Last, each whole arc of the
cleaned outline is refitted fair (fair_arcs: curvature continuous and
changing gently, rising from nothing where a curve leaves a line).

The review, the study and its choices: FONT-DESIGN.md (Bold
Italic from strokes), scripts/pilot/strokes_fit.py.
"""
import math
import os

import numpy as np
import pathops
import ufoLib2
from derive import ZONE_BOTTOMS, ZONE_TOPS, merged_glyph
from fair_arcs import LIMIT, SHORT, arcs, draw, fair_contour, segments
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
# 2026-10-28)
FULL = 0.75
ZONES = ZONE_TOPS + ZONE_BOTTOMS
CLEAR = 0.25  # of the white in front, the most a side may move into it
ROOT = 160  # units from a crotch over which a hairline's root weight fades (data_bold_italic.ITALIC_BOLD_ROOTS)
ZONE_NEAR = 100  # units
SHALLOW = 0.55  # (about 33 degrees from level, fading to 44)
ACROSS = 0.45  # (z's spine, 25° from level, read as a hairline at 1: 2026-10-28)
OPEN = 1e9  # (smooth's length of a run that does not close)
TINY = 4  # units: a line this short left by the overlap removal is dropped (7: 3)
SLIVER = 800        # area under which a cleaned contour is a crotch's crossing sides
BLEND = 120  # units of a curve over which it takes on the weight of the line it runs into
BLEND_SHORT = 40  # units: only where the curve next to the line is shorter (no room for its fit to take it up)
BLEND_STEP = 4  # units: only where the two would be moved further apart than this
# a sideways step (steps): the edge, followed every unit along it, turning
# out by STEP_TURN degrees or more and back to its course (at least half
# way) within STEP_REACH units each way, the turn under STEP_WIDTH units
# wide (at half its height), the edge moved STEP_SIDE units aside or more;
# not a bar or notch drawn with a corner at each end NOTCH units apart or
# more (calibrated 2026-10-29 on the steps stroke_bold made before Strokes.blend,
# 25 to 72 degrees, and the controls n h u v w o: u's knee into its bowl 18)
STEP_TURN = 20
# a knee: a curve beside a line whose fit bends back though the source's
# turns one way (Strokes.draw), with a step of KNEE_TURN degrees or more left
# within KNEE_NEAR units of it in the stroked outline (u's inner stem into its
# bowl, 10 here, 18 finished; none in n h m v w a b d p q r:
# 2026-10-29): blended into its line whatever its curve's length, over
# KNEE_BLEND units
KNEE_BLEND = 240.0  # (120 kinked u at its line once rounded, 500 a little below; 200-300 clean)
KNEE_TURN = 8
KNEE_NEAR = 20
# a knee taken (or found beside one taken: ш's middle stem) is then drawn as
# the Italic turns there, seen slanted: the edge from its line to upright,
# then round into the counter's bottom, ending on the bowl's own curve
# (2026-10-29: blended, it still went inward before turning,
# and turned too tight); the quarter KNEE_QUARTER times the downstroke
# weight wide (46 units at 160; 30 and 38 tried), KNEE_RATIO times that
# high, the upright KNEE_CLEAR times it right of the line, handles as the
# Italic's u (KNEE_HANDLES: the line's, the upright's going in and out,
# the bottom's, of the drop or of the quarter)
KNEE_QUARTER = 46 / 160
KNEE_RATIO = 1.48
KNEE_CLEAR = 0.364
KNEE_HANDLES = (0.21, 0.31, 0.53, 0.76)
STEP_REACH = 40
STEP_WIDTH = 30
STEP_SIDE = 1.0
NOTCH = 12
# findings of a candidate and of the outline it would replace (compared)
# are the same one when each is the other's nearest of its kind within NEAR
# units, and worse when its measure grows by over WORSE (and half a unit)
NEAR = 20
WORSE = 0.1
BEND_NEAR = 40  # (an inflection on a nearly straight stretch slides along it: ʲ's stem, Џ's tail)
# a blended candidate (embolden_by_strokes, guarded) may move the outline
# only within REGION times ax of the source's points it blended (declared
# before fitting), elsewhere by OUTSIDE units at most; across its strokes
# there its ink no narrower or wider than without by over WIDTH units, its
# width rising and falling no more often, no less white in front
REGION = 1.0
OUTSIDE = 1.0
WIDTH = 3.0
LEFTOVER = SHORT  # units (fair_arcs's, the same by design): a piece of the cleaned outline shorter is merged into its neighbours
TS = np.linspace(0, 1, 200)  # the fit's sampling of a cubic
# curvature continuous at the smooth joins of curves (G2), a curve kept as
# fitted where that would move it over G2_ERR units (2026-10-28); not where
# a curve runs on from a line (its end straight there too: a dead end,
# docs/claude/stroking.md)
G2_ERR = 3.0
TS_G2 = np.linspace(0, 1, 80)  # (its distances, measured coarser)
# then each whole arc refitted fair (fair_arcs, 2026-10-28;
# embolden_by_strokes(fair=False): as fitted)
SPLIT_ERR = 3.0  # units a moved side's one cubic may stray from its points (split: data_bold_italic.ITALIC_BOLD_SPLIT)
# an arc leaving a line that turns one way in the source (its first curve
# turning back by ONE_WAY_TOL degrees at most: Old Standard's n) but whose
# moved points turn back by over ONE_WAY_DIP degrees there, its weight
# fading along it faster than it turns (the Bold Italic's entry strokes
# into their left downstroke, u n and their families: 2026-11-09 review):
# the moved edge kept turning one way from the line's moved end, at least
# ONE_WAY_SHARE of the source's turn (more pinched the hook's counter, 0.8
# and 1 tried), and what that shifts it given back further on where the
# edge runs along the shift (sliding on itself, the hook's top; given back
# by the turning a foot's tight turn folded into a cusp, eased along the
# arc it bent back again), so the arc's far end stays; taken only where it
# then turns back nowhere new, its curve fitted bending one way too
# (one_way_fit). The knees are found first, on the outline as moved, and
# left to their own repair (Strokes.one_way; embolden_by_strokes(one_way=False)
# to compare)
ONE_WAY_TOL = 3.0
ONE_WAY_DIP = 1.0
ONE_WAY_MAX = 10.0  # (more: not the fade's, a crotch's 20 to 25)
ONE_WAY_SHARE = 0.5
# (only a stem fading into a hook: its weight at the line ONE_WAY_STEM or
# more, at the curve's end ONE_WAY_HOOK or more and ONE_WAY_FADE less)
ONE_WAY_STEM, ONE_WAY_HOOK, ONE_WAY_FADE = 0.7, 0.3, 0.2
ONE_WAY_UPRIGHT = 30  # degrees: its line at most this far from upright, a stem (s S ʂ's spines, 55: accepted as they are)
ONE_WAY_GIVE = 20.0  # degrees the rest of the arc must turn to take it back
ONE_WAY_LIMIT = 4.0  # units: its fit made to bend one way within this of its points
ONE_WAY_SCALES = np.linspace(0.1, 1.6, 31)  # (the handle lengths tried, times the fit's)
ONE_WAY_SHARP = 2.0  # (its curvature at most this times the fit's sharpest: a short handle spikes)
ONE_WAY_HANDLE = 12  # units, its handles at least (a short one rounds off its course: 3.6 units by 15 degrees; 12, 2.4 at most)


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


def ddbez(p, t):
    t = np.asarray(t, float)[..., None]
    return 6 * (1 - t) * (p[2] - 2 * p[1] + p[0]) + 6 * t * (p[3] - 2 * p[2] + p[1])


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


def curvatures(ctrl):
    """a cubic's signed curvature at its start and end"""
    P0, P1, P2, P3 = ctrl
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]  # noqa: E731
    a, b = np.linalg.norm(P1 - P0), np.linalg.norm(P3 - P2)
    k0 = 2 / 3 * cross(P1 - P0, P2 - P1) / a ** 3 if a > 1e-9 else 0.0
    k1 = 2 / 3 * cross(P2 - P1, P3 - P2) / b ** 3 if b > 1e-9 else 0.0
    return k0, k1


def apart(pts, ctrl):
    """how far cubic ctrl and the points pts are apart, both ways (a curve
    can bulge out between points that all lie near it)"""
    d = np.linalg.norm(pts[:, None, :] - bez(ctrl, TS_G2)[None, :, :], axis=2)
    return max(d.min(axis=1).max(), d.min(axis=0).max())


def fit_g2(pts, t0, t1, k0, k1, ls):
    """one cubic from pts[0] to pts[-1], end tangents t0 t1 and end
    curvatures k0 k1 (None: free, its handle as ls's, the least-squares
    fit's); handle lengths solved for them (Newton from several starts, the
    root nearest pts kept); (control points, largest distance to pts) or
    None where none holds"""
    P0, P3 = pts[0], pts[-1]
    D = P3 - P0
    d = np.linalg.norm(D)
    span = np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]  # noqa: E731
    a0, a1, x = cross(t0, D), cross(D, t1), cross(t0, t1)
    if (k0 is None) != (k1 is None) and abs(k0 if k0 is not None else k1) < 1e-9:
        # straight at one end, the other end's handle is fixed by it alone:
        # the free end keeps its curvature instead of its handle
        own = curvatures([P0, P0 + ls[0] * t0, P3 - ls[1] * t1, P3])
        k0, k1 = (k0, own[1]) if k1 is None else (own[0], k1)
    best = None
    for la, lb in [ls] + [(s0 * span, s1 * span) for s0, s1 in ((1 / 3, 1 / 3), (0.2, 0.5), (0.5, 0.2), (0.6, 0.6))]:
        if best is not None:  # the least-squares fit's own root holds
            break
        for _ in range(40):
            # 3/2 la^2 k0 = a0 - lb x, 3/2 lb^2 k1 = a1 - la x
            f = np.array([a0 - lb * x - 1.5 * k0 * la * la if k0 is not None else la - ls[0],
                          a1 - la * x - 1.5 * k1 * lb * lb if k1 is not None else lb - ls[1]])
            J = np.array([[-3 * k0 * la, -x] if k0 is not None else [1.0, 0.0],
                          [-x, -3 * k1 * lb] if k1 is not None else [0.0, 1.0]])
            try:
                step = np.linalg.solve(J, -f)
            except np.linalg.LinAlgError:
                break
            la, lb = la + step[0], lb + step[1]
            if np.abs(step).max() < 1e-6:
                break
        if np.abs(f).max() > 1e-3 * d:
            continue
        if not (0.02 * span < la < span and 0.02 * span < lb < span):
            continue
        ctrl = [P0, P0 + la * t0, P3 - lb * t1, P3]
        err = apart(pts, ctrl)
        if best is None or err < best[1]:
            best = (ctrl, err)
    return best


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
    frame's (its upright is an extreme's direction); root: a hairline's
    weight where it leaves a crotch, fading over ROOT units (0: none);
    split: Strokes.split_fit at crotches; free: units from a crotch within
    which the white in front does not hold a side back (0: none)"""

    def __init__(self, ax, ay, thin, thick, hair, slant, root=0.0, split=False, free=0.0):
        self.ax, self.ay, self.thin, self.thick, self.hair = ax, ay, thin, thick, hair
        self.root, self.split, self.free = root, split, free
        self.upright = unit(np.array([-slant, 1.0]))
        self.slant = slant
        self.blending, self.blended = True, False  # (blend: asked for, done)
        self.region = []  # where blend changed the source's weights, and rejoined(short=) the outline
        # (contour, segment): a curve beside a line whose fit bends back
        # where the source's turns one way (draw finds them, with their
        # moved samples; knees: those blend then takes on whatever their
        # length, over KNEE_BLEND units)
        self.knees, self.found = set(), {}
        self.turned = []  # (contour, curve, way, degrees): kept turning one way (one_way)
        self.turning, self.untouched = True, set()  # (one_way: asked for; the knees it leaves)

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
            if self.free and cuts:
                # near a crotch the two strokes' crossing decides where they
                # meet, not the white between them: a side capped there by the
                # narrowing counter bent in above it (q.sc's bowl over its loop)
                d = np.min(np.linalg.norm(P[:, None] - P[cuts][None], axis=2), axis=1)
                free = np.clip(1 - d / self.free, 0, 1) ** 2
                cap = np.maximum(cap, free)
                capv = np.maximum(capv, free)
            if self.root and cuts:
                # a hairline springing from a crotch heavier at its root
                # (k's arm, review: thicker in the beginning), both its
                # sides: by the distance from the crotch, not along the outline
                d = np.min(np.linalg.norm(P[:, None] - P[cuts][None], axis=2), axis=1)
                sm = np.maximum(sm, self.root * np.clip(1 - d / ROOT, 0, 1) ** 2)
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

    def one_way(self, segs, lines, nodes, moved, ci, kc, first_at, kline, vline, sign):
        """each arc leaving a line (either way round) whose first curve
        turns one way in the source but back in its moved points: those
        kept turning one way from the line's direction, the shift given
        back along the rest of the arc by its turning (ONE_WAY_*); moved
        changed in place"""
        L = len(segs)
        for k in range(L):
            for step in (1, -1):
                line, first = ((k - 1) % L, k) if step == 1 else ((k + 1) % L, k)
                if (not lines[line] or lines[first] or L < 3 or (ci, first) in self.untouched
                        or nodes[k if step == 1 else (k + 1) % L]["corner"]):
                    continue  # (a smooth run from the line only)
                if abs(segs[line][0][1][0]) > math.sin(math.radians(ONE_WAY_UPRIGHT)):
                    continue  # (a stem's line only: not s's spine)
                back, sense = against(segs[first])
                if back > ONE_WAY_TOL:
                    continue
                # the arc: from the line through smooth nodes to a corner or line
                run, seg = [], first
                while not lines[seg % L] and len(run) < L:
                    run.append(seg % L)
                    end = (seg + 1) % L if step == 1 else seg % L
                    if nodes[end]["corner"]:
                        break
                    seg += step
                if len(run) < 2:
                    continue
                if step == -1:
                    sense = -sense  # (the source followed backwards)
                pts = [np.asarray(q, float) for m in run for q in (moved[m] if step == 1 else moved[m][::-1])]
                src = [t * step for m in run for _p, t in (segs[m] if step == 1 else segs[m][::-1])]
                n0 = len(moved[first])
                # (a stem fading into a hook: from the line's weight to part
                # of it at the curve's end, the rest of the fade further on)
                fw = kc[first_at[first]:first_at[first + 1]]
                w0, w1 = (float(fw[0]), float(fw[-1])) if step == 1 else (float(fw[-1]), float(fw[0]))
                if w0 < ONE_WAY_STEM or not ONE_WAY_HOOK <= w1 <= w0 - ONE_WAY_FADE:
                    continue
                P = np.array(pts)
                # (from the line's moved end, as the nodes are drawn: the
                # curve's first point, moved by its own weight, stands aside
                # of it and its fit swings over; the run shifted onto it)
                nd = nodes[k if step == 1 else (k + 1) % L]
                aside = self.move(segs[k if step == 1 else (k + 1) % L][0][0], unit(nd["tin"] + nd["tout"]),
                                  kline[line], sign, vline[line]) - P[0]
                d = np.diff(P, axis=0)
                ln = np.linalg.norm(d, axis=1)
                if len(ln) < 4 or (ln < 1e-9).any():
                    continue
                phi = np.unwrap(np.arctan2(d[:, 1], d[:, 0])) * sense
                lt = segs[line][0][1] * step
                base = math.atan2(lt[1], lt[0]) * sense
                base += 2 * math.pi * round((phi[0] - base) / (2 * math.pi))
                # (a first difference off the line's course by much is the
                # junction's, not the curve's)
                start = 0
                st = np.array(src)
                tw = np.arctan2(st[:-1, 0] * st[1:, 1] - st[:-1, 1] * st[1:, 0], np.sum(st[:-1] * st[1:], axis=1)) * sense
                # (turning at least ONE_WAY_SHARE of the source's own turn)
                head, prev = [], base
                for i in range(start, n0 - 1):
                    prev = max(float(phi[i]), prev + ONE_WAY_SHARE * max(0.0, float(tw[i - 1]) if i else 0.0))
                    head.append(prev)
                head = np.array(head)
                dip = float((np.maximum.accumulate(np.concatenate([[base], phi[start:n0 - 1]]))[1:] - phi[start:n0 - 1]).max()) if len(head) else 0.0
                if not ONE_WAY_DIP < math.degrees(dip) <= ONE_WAY_MAX:
                    continue
                # the rest of the arc turns the same way enough to take it back
                rest = np.clip(tw[n0 - 1:], 0, None)
                if len(rest) < 2 or math.degrees(rest.sum()) < ONE_WAY_GIVE:
                    continue
                new = phi.copy()
                new[start:n0 - 1] = np.maximum(head, phi[start:n0 - 1])
                ang = new * sense
                Q = np.vstack([P[:1], P[0] + np.cumsum(ln[:, None] * np.stack([np.cos(ang), np.sin(ang)], axis=1), axis=0)])
                D = Q - P
                D[n0:] = D[n0 - 1]  # (beyond the first curve as moved, shifted only)
                D += aside
                # given back where the edge runs along the shift (sliding on
                # itself: the hook's top; given back across it, it bends the
                # edge back, and in a tight turn folds it)
                way = D[-1] / max(float(np.linalg.norm(D[-1])), 1e-9)
                along = np.abs(d[n0 - 1:] @ way) ** 2 / np.maximum(ln[n0 - 1:], 1e-9)
                if along.sum() < 1e-6:
                    continue
                w = np.zeros(len(P))
                share = np.concatenate([[0], np.cumsum(along)])
                w[n0 - 1:] = share / share[-1]
                Q = P + D * (1 - w)[:, None]
                # (taken only where it turns back nowhere the moved points
                # did not: given back over too tight a turn, a foot's, it
                # folds into a cusp)
                dq = np.diff(Q, axis=0)
                if (np.linalg.norm(dq, axis=1) < 1e-9).any():
                    continue
                tq = np.diff(np.unwrap(np.arctan2(dq[:, 1], dq[:, 0]))) * sense
                tp = np.diff(phi)
                bad = tq[n0 - 1:] - np.minimum(tp[n0 - 1:], 0)
                if (bad < -math.radians(ONE_WAY_DIP)).any():
                    continue
                # back into moved, segment by segment
                at = 0
                for m in run:
                    cnt = len(moved[m])
                    part = [Q[at + i] for i in range(cnt)]
                    moved[m] = part if step == 1 else part[::-1]
                    at += cnt
                self.turned.append((ci, first, step, round(math.degrees(dip), 1)))

    def mitre(self, p1, t1, p2, t2):
        den = t1[0] * t2[1] - t1[1] * t2[0]
        if abs(den) < 1e-6:
            return None
        u = ((p2 - p1)[0] * t2[1] - (p2 - p1)[1] * t2[0]) / den
        m = p1 + u * t1
        if np.linalg.norm(m - p1) < 3 * self.ax and np.linalg.norm(m - p2) < 3 * self.ax:
            return m
        return None

    def crossing(self, a, b, nd, prev, here):
        """a crotch's moved sides, the arriving one ending at a and the
        leaving one starting at b (prev, here: a curve's moved samples; None
        for a line), each run on straight past its end: where they cross
        nearest the corner, and how many of prev's samples to keep and from
        which of here's to go on (None: all); None where they do not cross
        within reach"""
        reach = 3 * self.ax
        n_in = int(reach / STEP)
        if prev is None:
            A = [a - nd["tin"] * reach, a]
            off_a = 0
        else:
            A = list(prev[-n_in:]) + [a]
            off_a = len(prev) - (len(A) - 1)
        da = unit(A[-1] - A[max(0, len(A) - 4)]) if prev is not None else nd["tin"]
        A = np.array(A + [A[-1] + da * reach])
        if here is None:
            B = [b, b + nd["tout"] * reach]
        else:
            B = [b] + list(here[1:n_in])
        db = unit(B[min(3, len(B) - 1)] - B[0]) if here is not None else nd["tout"]
        B = np.array([B[0] - db * reach] + B)
        p, e = A[:-1], np.diff(A, axis=0)
        q, f = B[:-1], np.diff(B, axis=0)
        den = e[:, None, 0] * f[None, :, 1] - e[:, None, 1] * f[None, :, 0]
        w = q[None] - p[:, None]
        with np.errstate(divide="ignore", invalid="ignore"):
            u = (w[..., 0] * f[None, :, 1] - w[..., 1] * f[None, :, 0]) / den
            v = (w[..., 0] * e[:, None, 1] - w[..., 1] * e[:, None, 0]) / den
        ok = (np.abs(den) > 1e-12) & (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
        if not ok.any():
            return None
        la = np.concatenate([[0], np.cumsum(np.linalg.norm(e, axis=1))])
        lb = np.concatenate([[0], np.cumsum(np.linalg.norm(f, axis=1))])
        ia, ib = np.nonzero(ok)
        posa = la[ia] + u[ia, ib] * (la[ia + 1] - la[ia])
        posb = lb[ib] + v[ia, ib] * (lb[ib + 1] - lb[ib])
        # nearest the ends, a side run on straight past its end counting
        # four times what a side trimmed back does (ξ's bowl run on to its
        # hairline bent the bowl; its hairline run on to the bowl does not)
        da, db_ = posa - la[-2], posb - lb[1]
        cost = np.where(da > 0, 4 * da, -da) + np.where(db_ < 0, -4 * db_, db_)
        best = int(np.argmin(cost))
        i, j = int(ia[best]), int(ib[best])
        m = p[i] + u[i, j] * e[i]
        na = None
        if prev is not None and i < len(A) - 3:
            na = off_a + i + 1
            if na < 2:
                return None
        nb = None
        if here is not None and j >= 1:
            nb = j
            if len(here) - nb < 2:
                return None
        return m, na, nb

    @staticmethod
    def split_fit(pts, ctrl, depth=3):
        """ctrl, one cubic fitted to pts, as cubics: split where it strays
        furthest from them, while it strays more than SPLIT_ERR units (q.sc's
        bowl inside, its weight falling towards the loop, waved one way and
        the other about its points)"""
        def stray(p, c):
            return float(np.min(np.linalg.norm(p[:, None, :] - bez(c, TS)[None, :, :], axis=2), axis=1).max())

        def pieces(p, c, depth):
            """(cubics, the furthest any strays)"""
            e = stray(p, c)
            if depth == 0 or len(p) < 24 or e <= SPLIT_ERR:
                return [c], e
            err = np.min(np.linalg.norm(p[:, None, :] - bez(c, TS)[None, :, :], axis=2), axis=1)
            i = int(np.argmax(err))
            if not len(p) // 4 <= i <= 3 * len(p) // 4:  # (at an end: halved)
                i = len(p) // 2
            tm = unit(p[i + 3] - p[i - 3])
            first = fit_cubic(p[:i + 1], unit(c[1] - c[0]), tm)[0]
            second = fit_cubic(p[i:], tm, unit(c[3] - c[2]))[0]
            if first is None or second is None:
                return [c], e
            (a, ea), (b, eb) = pieces(p[:i + 1], first, depth - 1), pieces(p[i:], second, depth - 1)
            return (a + b, max(ea, eb)) if max(ea, eb) < 0.8 * e else ([c], e)

        if ctrl is None:
            return [ctrl]
        return pieces(pts, ctrl, depth)[0]

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

    def join_curvature(self, fits, nodes, inner):
        """fits (each curve's samples and cubic, None for a line) refitted so
        that at each smooth node between two curves both have one curvature
        (G2): each node's, between its two curves' own, where the larger of
        their distances from their own fits is least (a short tight curve
        bends more readily than a long one), node by node, a few rounds; a
        node where that is over G2_ERR is left as fitted"""
        L = len(fits)
        if L < 2:
            return
        curve = [f is not None and f[1] is not None for f in fits]
        g1 = [f[1] if c else None for f, c in zip(fits, curve)]
        # (measured from the fit, not the samples: where the samples are far
        # from any cubic, at a crotch, a quite different curve is as far)
        ref = [bez(g, TS_G2) if c else None for g, c in zip(g1, curve)]
        own = [curvatures(g) if c else None for g, c in zip(g1, curve)]
        joins = [k for k in range(L) if curve[k - 1] and curve[k] and not nodes[k]["corner"] and k not in inner]
        target = [None] * L  # at node k, between curve k - 1 and curve k
        # (a curve running on from a line is not made straight there: a dead
        # end, docs/claude/stroking.md)

        def refit(k, t0, t1):
            """curve k with end curvatures t0 t1: (cubic, its extra distance)"""
            c = g1[k]
            if t0 is None and t1 is None:
                return c, 0.0
            ls = (np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[3] - c[2]))
            got = fit_g2(ref[k], unit(c[1] - c[0]), unit(c[3] - c[2]), t0, t1, ls)
            return (None, math.inf) if got is None else got
        for _ in range(3):
            for k in joins:
                i, j = k - 1, (k + 1) % L
                ka, kb = own[i][1], own[k][0]
                def worst(lam, i=i, k=k, j=j, ka=ka, kb=kb):
                    t = ka + (kb - ka) * lam
                    return max(refit(i, target[i], t)[1], refit(k, t, target[j])[1]), t
                best = min(worst(lam) for lam in (0, 0.25, 0.5, 0.75, 1))
                lam = (best[1] - ka) / (kb - ka) if abs(kb - ka) > 1e-12 else 0.5
                best = min([best] + [worst(min(1, max(0, lam + d))) for d in (-0.125, 0.125)])
                target[k] = best[1] if best[0] <= G2_ERR else None
        for k in range(L):
            if curve[k]:
                c, extra = refit(k, target[k], target[(k + 1) % L])
                if c is not None and extra <= G2_ERR:
                    fits[k] = (fits[k][0], c)

    def blend(self, segs, lines, nodes, kc, kv, kline, vline, ci=0):
        """kc, kv with a curve running smoothly into a line taking on the
        line's weight (kline, vline: it moves parallel, by its mean) towards it, over
        BLEND units of the curve (up to its next corner or line): moved
        each by its own, they met in a sideways step (y's descender, where
        its inner line's weight is lowered by the crotch above it)"""
        L = len(segs)
        if L < 2:
            return kc, kv
        first = np.cumsum([0] + [len(s) for s in segs])
        kc, kv = kc.copy(), kv.copy()
        base_c, base_v = kc.copy(), kv.copy()
        N = len(kc)
        pts = np.array([p for seg in segs for p, _t in seg])
        for k in range(L):
            if nodes[k]["corner"] or lines[k - 1] == lines[k]:
                continue
            line = (k - 1) % L if lines[k - 1] else k
            # the curve's samples away from the node, to its next corner or line
            step = 1 if lines[k - 1] else -1
            run, seg, closed = [], k if step == 1 else k - 1, False
            while not (closed := lines[seg % L]) and len(run) < N:
                idx = range(first[seg % L], first[seg % L + 1])
                run += list(idx) if step == 1 else list(reversed(idx))
                end = (seg + 1) % L if step == 1 else seg % L
                if nodes[end]["corner"]:
                    break
                seg += step
            if not run:
                continue
            # (by how far the curve's end is from the line's weight)
            dc = kline[line] - base_c[run[0]]
            dv = vline[line] - base_v[run[0]]
            # (only a short curve next to the line, the cleaning's split at
            # an extreme just before it: a longer one's fit takes up the
            # difference, and the rest of the font stays as reviewed)
            near = k if lines[k - 1] else (k - 1) % L
            # (nor short curves between two lines: moved each by its own
            # mean, they stand apart whatever the curves do)
            knee = (ci, near) in self.knees  # (a long curve's knee: KNEE_TURN)
            if ((len(segs[near]) * STEP > BLEND_SHORT and not knee) or (closed and len(run) * STEP < 2 * BLEND_SHORT)
                    or abs(self.offset(base_c[run[0]] + dc) - self.offset(base_c[run[0]])) < BLEND_STEP):
                continue
            along = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts[run], axis=0), axis=1))])
            span = min(KNEE_BLEND if knee else BLEND, along[-1] + 1e-9)
            fade = np.where(along < span, 0.5 * (1 + np.cos(np.pi * along / span)), 0.0)
            kc[run] += dc * fade
            kv[run] += dv * fade
            self.blended = True
            self.region += list(pts[run][fade > 0])
        return np.clip(kc, 0, 1), np.clip(kv, 0, 1)

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
        for ci, ((segs, lines, nodes), (kc, kv)) in enumerate(zip(contours, ks)):
            self.crotches(segs, lines, nodes, kc, sign)
            whole = self.rigid(segs, lines, nodes, kc, sign)
            inner = {(k + m) % len(segs) for k, n in whole for m in range(1, n)}
            # (the lines' own weights, before the curves take them on)
            first = np.cumsum([0] + [len(s) for s in segs])
            kline = [float(kc[first[k]:first[k + 1]].mean()) if lines[k] else None for k in range(len(segs))]
            vline = [float(kv[first[k]:first[k + 1]].mean()) if lines[k] else None for k in range(len(segs))]
            if self.blending:
                kc, kv = self.blend(segs, lines, nodes, kc, kv, kline, vline, ci)
            moved, q = [], 0
            for seg in segs:
                moved.append([self.move(p, t, kc[q + s], sign, kv[q + s]) for s, (p, t) in enumerate(seg)])
                q += len(seg)
            L = len(segs)
            if self.turning:
                self.one_way(segs, lines, nodes, moved, ci, kc, first, kline, vline, sign)
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
            ends, trims = [], {}
            for k in range(L):
                nd = nodes[k]
                p = segs[k][0][0]
                kk, vv = kc[first[k]], kv[first[k]]
                ka, va = (kk, vv) if kline[k - 1] is None else (kline[k - 1], vline[k - 1])
                if nd["corner"] and kline[k - 1] is None:
                    # a corner arriving from a curve: the curve's end by its
                    # own weight, not by the leaving side's, lighter or
                    # heavier (γ: the arm's lower edge, moved at the crotch
                    # by the descender's stem weight, hooked back into a
                    # step; 2026-11-02, taken for the heavier too 2026-11-03)
                    ka, va = kc[first[k] - 1], kv[first[k] - 1]
                kb, vb = (kk, vv) if kline[k] is None else (kline[k], vline[k])
                if nd["corner"]:
                    a, b = self.move(p, nd["tin"], ka, sign, va), self.move(p, nd["tout"], kb, sign, vb)
                    convex = sign * (nd["tin"][0] * nd["tout"][1] - nd["tin"][1] * nd["tout"][0]) > 0
                    m = self.mitre(a, nd["tin"], b, nd["tout"]) if convex else None
                    if not convex and lines[k - 1] and lines[k]:
                        # a crotch between two lines: where they meet, if on both
                        m = self.meet(a, nd["tin"], b, nd["tout"], segs[k - 1][0][0], segs[(k + 1) % L][0][0])
                    elif not convex and not (
                            # (not a crotch's short line, γ's below its loop:
                            # its two corners are one crotch, as before)
                            (lines[k - 1] and np.linalg.norm(p - segs[k - 1][0][0]) < self.ax / 3)
                            or (lines[k] and np.linalg.norm(segs[(k + 1) % L][0][0] - p) < self.ax / 3)):
                        # a crotch with a curve: its two moved sides run on
                        # (or back) to where they cross, a curve trimmed to
                        # it below (γ's arm and descender, &'s bowl and stem:
                        # joined by a step)
                        got = self.crossing(a, b, nd, None if lines[k - 1] else moved[k - 1],
                                            None if lines[k] else moved[k])
                        if got is not None:
                            m, trims[k] = got[0], got[1:]
                    ends.append((m, m) if m is not None else (a, b))
                elif kline[k - 1] is not None or kline[k] is not None:
                    t = unit(nd["tin"] + nd["tout"])
                    q = self.move(p, t, *((kb, sign, vb) if kline[k] is not None else (ka, sign, va)))
                    ends.append((q, q))
                else:
                    ends.append((moved[k][0], moved[k][0]))
            # a crotch drawn as a short line between two curves (the
            # crotches above, ξ's middle, γ's below its loop): the curves
            # meet where they cross, the line gone to a point (each corner
            # by itself left the heavier side standing past the other, an
            # outcrop)
            # (or the line running on smoothly into the curve after it, ξ's:
            # the line and that curve one side)
            braced = {(k + m) % L for k, n in whole for m in range(n + 1)}
            for k in range(L):
                j = (k + 1) % L
                if (not lines[k] or lines[k - 1] or lines[j] or L < 4
                        or not nodes[k]["corner"] or k in braced or j in braced
                        or np.linalg.norm(segs[j][0][0] - segs[k][0][0]) >= self.ax / 3
                        or sign * (nodes[k]["tin"][0] * nodes[j]["tout"][1]
                                   - nodes[k]["tin"][1] * nodes[j]["tout"][0]) >= 0):
                    continue
                nd = {"tin": nodes[k]["tin"], "tout": nodes[j]["tout"]}
                if nodes[j]["corner"]:
                    got = self.crossing(ends[k][0], ends[j][1], nd, moved[k - 1], moved[j])
                else:
                    on = [ends[k][1]] + list(moved[j])
                    got = self.crossing(ends[k][0], ends[k][1], nd, moved[k - 1], on)
                if got is None:
                    continue
                m, na, nb = got
                ends[k], ends[j] = (m, m), (m, m)
                trims[k] = (na, None)
                if nodes[j]["corner"]:
                    trims[j] = (None, nb)
                else:
                    # (the line's moved start dropped: the curve runs on
                    # from the meeting point, sampled below)
                    moved[j] = on[nb - 1:] if nb and nb > 1 else [m] + list(moved[j])
                    nodes[j]["corner"] = True  # (its tangent from its curve now)
                    trims[j] = (None, None)
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
            # a crotch's curves trimmed to where they cross
            for k, (na, nb) in trims.items():
                if k in shifts:
                    continue
                if na is not None:
                    moved[k - 1] = moved[k - 1][:na]
                if nb is not None:
                    moved[k] = moved[k][:1] + moved[k][nb:]
                # a side run on straight to the meeting point: that run
                # sampled too, its fit following it (ξ's bowl, run on to
                # its hairline: one cubic over the gap drew it in, a waist)
                m = ends[k][0]
                if not lines[k - 1] and len(moved[k - 1]) > 1:
                    gap = np.linalg.norm(m - moved[k - 1][-1])
                    if gap > 2 * STEP:
                        n = int(gap / STEP)
                        moved[k - 1] = moved[k - 1] + [moved[k - 1][-1] + (m - moved[k - 1][-1]) * (i / n)
                                                       for i in range(1, n)]
                if not lines[k] and len(moved[k]) > 1:
                    gap = np.linalg.norm(moved[k][1] - m)
                    if gap > 2 * STEP:
                        n = int(gap / STEP)
                        moved[k] = moved[k][:1] + [m + (moved[k][1] - m) * (i / n) for i in range(1, n)] + moved[k][1:]
            # a corner whose sides meet past their moved ends: the samples
            # beyond the meeting point dropped (they ran back from it, a hook)
            for k in range(L):
                if (not nodes[k]["corner"] or k in shifts or k in trims
                        or not np.allclose(ends[k][0], ends[k][1])):
                    continue
                m = ends[k][0]
                if not lines[k - 1]:
                    prev = moved[k - 1]
                    n = len(prev)
                    while n > 4 and float((prev[n - 1] - m) @ nodes[k]["tin"]) > 0:
                        n -= 1
                    moved[k - 1] = prev[:n]
                if not lines[k]:
                    here = moved[k]
                    n = 1
                    while len(here) - n > 4 and float((m - here[n]) @ nodes[k]["tout"]) > 0:
                        n += 1
                    moved[k] = here[:1] + here[n:]
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
            fits = [None] * L
            for k in range(L):
                if not lines[k]:
                    j = (k + 1) % L
                    pts = np.array([ends[k][1]] + moved[k][1:] + [ends[j][0]])
                    fits[k] = (pts, fit_cubic(pts, tans[k][1], tans[j][0])[0])
            self.join_curvature(fits, nodes, inner)
            for k in range(L):
                if (not lines[k] and fits[k][1] is not None and (lines[k - 1] or lines[(k + 1) % L])
                        and inflections(fits[k][1]) and one_way(segs[k])):
                    self.found[(ci, k)] = fits[k][0]
            # (a curve kept turning one way, its fit too: the nearest
            # handle lengths that bend one way)
            for _c, k, _w, _d in (t for t in self.turned if t[0] == ci):
                if fits[k] is not None and fits[k][1] is not None and inflections(fits[k][1]):
                    refit = one_way_fit(*fits[k])
                    if refit is not None:
                        fits[k] = (fits[k][0], refit)
            rec.moveTo(tuple(ends[0][1]))
            for k in range(L):
                j = (k + 1) % L
                if lines[k] or fits[k][1] is None:
                    rec.lineTo(tuple(ends[j][0]))
                else:
                    # (only a curve running into a crotch's meeting point: run on
                    # or trimmed there, one cubic does not follow it; split
                    # all round, ξ's and q.sc's bowls went faceted)
                    crotch = k in trims or j in trims
                    parts = self.split_fit(fits[k][0], fits[k][1]) if self.split and crotch else [fits[k][1]]
                    anchors += [ctrl[3] for ctrl in parts[:-1]]  # (kept by the cleaning, as nodes are)
                    for ctrl in parts:
                        rec.curveTo(tuple(ctrl[1]), tuple(ctrl[2]), tuple(ctrl[3]))
                if j and not np.allclose(ends[j][0], ends[j][1]):
                    rec.lineTo(tuple(ends[j][1]))
            if not np.allclose(ends[0][0], ends[0][1]):
                rec.lineTo(tuple(ends[0][1]))
            rec.closePath()
        return rec


def pieces(contours):
    """the contours (segment arrays) once their overlaps are removed"""
    path = pathops.Path()
    draw(path.getPen(), contours)
    return list(pathops.simplify(path).contours)


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
                    # (the contour's first point too, the closing line's
                    # end: kept, the loop found it again for ever, the
                    # Italic ɾ's emboldening hung, 2026-11-04)
                    del P[j]
                    break
            else:
                break
    return glyph


def contour_area(c):
    pts = [(p.x, p.y) for p in c.points if p.type]
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def rejoined(contour, anchors, short=False, acted=None):
    """contour with the cleaning's splits undone: a smooth node that is
    none of the moved nodes joins the cubics either side (refitted through
    both, exact where they are halves of one cubic); short, (points, r):
    also one within r of those points (where blend acted) joining a curve
    to a short one (under BLEND_SHORT) running on smoothly into a line (the
    cleaning's split at an extreme just before the line, blended: one curve
    into the line, as the source draws it; not elsewhere: ц's tail, joined
    so, overshot its extreme more); acted, a list: where short changed the
    outline is added to it"""
    acted = [] if acted is None else acted
    if short:
        region, r = np.asarray(short[0], float).reshape(-1, 2), short[1]
        short = lambda q: bool(near(np.asarray(q, float)[None], region, r)[0])  # noqa: E731
    else:
        short = lambda q: False  # noqa: E731
    P = contour.points
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    pt = lambda q: np.array([P[q % n].x, P[q % n].y], float)  # noqa: E731
    segs = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
        segs.append([pt(i)] + [pt(q) for q in offs] + [pt(j)])
    # a curve under LEFTOVER units (the cleaning's leftovers where an
    # inside-out loop was cut; a short line is drawn, ɉ's bar end) gone:
    # its neighbours meet at its sharper end (a line's end, where one is),
    # their handles moved with their ends (rejoined into them, it left
    # zigzags: r, z)
    while len(segs) > 3:
        k = next((k for k, s in enumerate(segs) if len(s) == 4 and np.linalg.norm(s[-1] - s[0]) < LEFTOVER), None)
        if k is None:
            break
        s, before, after = segs[k], segs[k - 1], segs[(k + 1) % len(segs)]
        # (at a line's end where one is: the line keeps its place and
        # direction, € bar's underside level)
        # (else at its sharper end: a crotch stays where the cleaning cut it)
        if len(before) == 2 and len(after) == 4:
            mid = s[0]
        elif len(after) == 2 and len(before) == 4:
            mid = s[-1]
        else:
            ts = unit(s[1] - s[0]) if np.linalg.norm(s[1] - s[0]) > 1e-9 else unit(s[-1] - s[0])
            te = unit(s[-1] - s[-2]) if np.linalg.norm(s[-1] - s[-2]) > 1e-9 else unit(s[-1] - s[0])
            turn0 = float(unit(before[-1] - before[-2]) @ ts)
            turn1 = float(te @ unit(after[1] - after[0]))
            mid = s[0] if turn0 < turn1 else s[-1]
        if len(before) == 4:
            before[2] = before[2] + mid - s[0]
        if len(after) == 4:
            after[1] = after[1] + mid - s[-1]
        before[-1], after[0] = mid, mid
        # (short: a piece running on smoothly from a line into a curve, the
        # curve leaving along the line, smooth as the source; Џ's tail)
        on = math.cos(math.radians(3))
        if short(mid) and len(before) == 2 and len(after) == 4 and np.linalg.norm(s[1] - s[0]) > 1e-9:
            line = unit(before[1] - before[0])
            if float(unit(s[1] - s[0]) @ line) > on:
                after[1] = mid + np.linalg.norm(after[1] - after[0]) * line
                acted.append(mid)
        elif short(mid) and len(after) == 2 and len(before) == 4 and np.linalg.norm(s[-1] - s[-2]) > 1e-9:
            line = unit(after[1] - after[0])
            if float(unit(s[-1] - s[-2]) @ line) > on:
                before[2] = mid - np.linalg.norm(before[3] - before[2]) * line
                acted.append(mid)
        del segs[k]

    def runs_into_line(k, step):
        """the curves from segment k on (step 1) or back (step -1) to a line
        are short (their chord under BLEND_SHORT) and run on smoothly into it"""
        L = len(segs)
        start = segs[k % L][0] if step == 1 else segs[k % L][-1]
        for m in range(L):
            c = segs[(k + m * step) % L]
            if len(c) == 2:
                return False
            nxt = segs[(k + (m + 1) * step) % L]
            end = c[-1] if step == 1 else c[0]
            if np.linalg.norm(end - start) >= BLEND_SHORT:
                return False
            if len(nxt) == 2:
                tc = unit(c[-1] - c[-2]) if step == 1 else unit(c[1] - c[0])
                return float(tc @ unit(nxt[1] - nxt[0])) > math.cos(math.radians(3))
        return False

    def split_here(k):
        a, b = segs[k - 1], segs[k]
        here = b[0]
        if len(anchors) and np.min(np.linalg.norm(anchors - here, axis=1)) < 0.5:
            split = True
        elif len(a) == 2 or len(b) == 2:
            split = True
        else:
            split = float(unit(here - a[-2]) @ unit(b[1] - here)) < math.cos(math.radians(2))
        if (short(here) and len(a) == 4 and len(b) == 4
                and float(unit(here - a[-2]) @ unit(b[1] - here)) > math.cos(math.radians(2))
                and (runs_into_line(k, 1) or runs_into_line(k - 1, -1))):
            if split:
                acted.append(here)
            return False
        return split
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
        t0, t1 = unit(run[0][1] - run[0][0]), unit(run[-1][-1] - run[-1][-2])
        ctrl, _err = fit_cubic(pts, t0, t1)
        # the run's own curvature at its ends where it runs on smoothly into
        # a curve (a corner's end is free, and one running on from a line)
        before, after = segs[(a - 1) % len(segs)], segs[b % len(segs)]
        on = math.cos(math.radians(2))
        k0 = k1 = None
        if len(run[0]) == 4 and len(before) == 4 and float(unit(before[-1] - before[-2]) @ t0) > on:
            k0 = curvatures(run[0])[0]
        if len(run[-1]) == 4 and len(after) == 4 and float(t1 @ unit(after[1] - after[0])) > on:
            k1 = curvatures(run[-1])[1]
        ls = (np.linalg.norm(ctrl[1] - ctrl[0]), np.linalg.norm(ctrl[3] - ctrl[2]))
        got = fit_g2(pts[::3], t0, t1, k0, k1, ls) if k0 is not None or k1 is not None else None
        if got is not None and got[1] <= G2_ERR:
            ctrl = got[0]
        rec.curveTo(*(tuple(q) for q in ctrl[1:]))
    rec.closePath()
    return rec


def one_way(seg):
    """a source segment's samples [(point, tangent)] turn one way only"""
    t = np.array([q for _p, q in seg])
    turn = t[:-1, 0] * t[1:, 1] - t[:-1, 1] * t[1:, 0]
    turn = turn[np.abs(turn) > 1e-4]
    return bool(len(turn)) and bool((np.sign(turn) == np.sign(turn[0])).all())


def against(seg):
    """degrees a source segment's samples [(point, tangent)] turn against
    their main sense, and that sense (+1, -1; 0: no turn)"""
    t = np.array([q for _p, q in seg])
    turn = np.arctan2(t[:-1, 0] * t[1:, 1] - t[:-1, 1] * t[1:, 0], np.sum(t[:-1] * t[1:], axis=1))
    total = float(turn.sum())
    if abs(total) < 1e-4:
        return math.inf, 0
    sense = 1 if total > 0 else -1
    return math.degrees(-float(turn[np.sign(turn) == -sense].sum()) * sense), sense


def one_way_fit(pts, ctrl):
    """the cubic ctrl (its end tangents kept) with the handle lengths
    nearest its fit to pts that bend one way, within ONE_WAY_LIMIT units of
    pts (both ways: apart); None where none do"""
    P0, P1, P2, P3 = (np.asarray(p, float) for p in ctrl)
    la, lb = np.linalg.norm(P1 - P0), np.linalg.norm(P3 - P2)
    if la < 1e-9 or lb < 1e-9:
        return None
    t0, t1 = (P1 - P0) / la, (P3 - P2) / lb

    def sharpest(sg):
        d, dd = dbez(sg, TS_G2), ddbez(sg, TS_G2)
        sp = np.linalg.norm(d, axis=1)
        return float(np.max(np.abs(d[:, 0] * dd[:, 1] - d[:, 1] * dd[:, 0]) / np.maximum(sp, 1e-9) ** 3))
    # (no sharper than the fit itself turns: a short handle spikes)
    limit = ONE_WAY_SHARP * sharpest([P0, P1, P2, P3])
    best = None
    for a in ONE_WAY_SCALES:
        for b in ONE_WAY_SCALES:
            cand = [P0, P0 + a * la * t0, P3 - b * lb * t1, P3]
            if (min(a * la, b * lb) < ONE_WAY_HANDLE
                    or inflections(cand) or sharpest(cand) > limit):
                continue
            d = apart(pts, cand)
            if d <= ONE_WAY_LIMIT and (best is None or d < best[0]):
                best = (d, cand)
    return best and best[1]


def inflections(sg):
    """the cubic sg's inflections (t in 0..1): where its curvature's sign
    changes, its numerator B' x B'' (a quadratic in t) passing zero"""
    d, dd = dbez(sg, [0.0, 0.5, 1.0]), ddbez(sg, [0.0, 0.5, 1.0])
    f = d[:, 0] * dd[:, 1] - d[:, 1] * dd[:, 0]
    a = 2 * f[2] - 4 * f[1] + 2 * f[0]
    b = f[2] - f[0] - a
    if abs(a) < 1e-12:
        roots = [-f[0] / b] if abs(b) > 1e-12 else []
    else:
        disc = b * b - 4 * a * f[0]
        roots = [(-b + r) / (2 * a) for r in (math.sqrt(disc), -math.sqrt(disc))] if disc > 0 else []
    return sorted(t for t in roots if 0 < t < 1)


def bends(contours):
    """where the contours (segment arrays) bend back the other way along a
    run of smooth curves (a corner or a line starts a new run; a contour of
    smooth curves only runs on from its end into its start): [("bend", x,
    y, 0)], each cubic's inflections found exactly, a stretch straighter
    than a 10000 unit radius taking no side"""
    out = []
    on = math.cos(math.radians(3))
    for segs in contours:
        L = len(segs)
        joined = [len(segs[k]) == 4 and len(segs[k - 1]) == 4
                  and float(unit(segs[k][1] - segs[k][0]) @ unit(segs[k - 1][-1] - segs[k - 1][-2])) >= on
                  for k in range(L)]
        first = next((k for k in range(L) if not joined[k]), None)
        last = start = None
        for k in ((first + i) % L for i in range(L)) if first is not None else range(L):
            sg = segs[k]
            if not joined[k]:
                last = None
            if len(sg) == 2:
                continue
            cuts = [0.0] + inflections(sg) + [1.0]
            for t0, t1 in zip(cuts, cuts[1:]):
                ts = np.linspace(t0, t1, 9)
                d, dd = dbez(sg, ts), ddbez(sg, ts)
                ks = (d[:, 0] * dd[:, 1] - d[:, 1] * dd[:, 0]) / np.maximum(np.linalg.norm(d, axis=1), 1e-9) ** 3
                side = ks[np.argmax(np.abs(ks))]
                if abs(side) <= 1e-4:
                    continue
                if last is not None and side * last < 0:
                    x, y = bez(sg, t0)
                    out.append(("bend", round(float(x)), round(float(y)), 0.0))
                last = side
                start = side if start is None else start
        if first is None and last is not None and start * last < 0:  # (around)
            x, y = segs[0][0]
            out.append(("bend", round(float(x)), round(float(y)), 0.0))
    return out


def traced(segs):
    """a closed contour (segment array) every unit or so along it (an
    equal share of its length): (points, the share); (None, 0) if short"""
    pts = []
    for sg in segs:
        t = np.linspace(0, 1, max(8, math.ceil(np.linalg.norm(np.diff(sg, axis=0), axis=1).sum() * 4)))[:-1]
        pts.append(bez(sg, t) if len(sg) == 4 else sg[0] + t[:, None] * (sg[1] - sg[0]))
    p = np.vstack(pts + [segs[0][0][None]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    n = int(s[-1])
    if n <= 2 * STEP_REACH + 2:
        return None, 0
    u = np.arange(n) * s[-1] / n
    return np.stack([np.interp(u, s, p[:, 0]), np.interp(u, s, p[:, 1])], 1), s[-1] / n


def foot(x, c, d, reach):
    """from the top at c, the lowest x going d (+1, -1) while it falls (half
    a degree's leeway), within reach samples"""
    j = low = c
    while abs(j - c) < reach:
        j += d
        if x[j] < x[low]:
            low = j
        elif x[j] > x[low] + math.radians(0.5):
            break
    return low


def steps(contours, turn=STEP_TURN):
    """the sideways steps along the contours (segment arrays, turning out
    turn degrees or more, STEP_TURN):
    [("step", x, y, degrees out and back, units aside)]; from the outline
    followed along its length, so the same however it is cut into segments"""
    out = []
    for segs in contours:
        pts, ds = traced(segs)
        if pts is None:
            continue
        n, m = len(pts), round(STEP_REACH / ds)
        v = np.roll(pts, -1, 0) - pts
        th = np.unwrap(np.arctan2(v[:, 1], v[:, 0]))
        whole = 2 * math.pi * round((th[-1] - th[0]) / (2 * math.pi))
        ext = np.concatenate([th[-m:] - whole, th, th[:m] + whole])  # (around the start)
        corner = np.abs(np.diff(ext)) > math.radians(CORNER)
        found = []
        for sign in (1, -1):
            x = sign * ext
            mid = x[m:m + n]
            for c in m + np.flatnonzero((mid >= x[m - 1:m + n - 1]) & (mid > x[m + 1:m + n + 1])):
                lo, hi = foot(x, c, -1, m), foot(x, c, 1, m)
                top = x[c] - max(x[lo], x[hi])
                if top < math.radians(turn) or abs(x[lo] - x[hi]) > top / 2:
                    continue
                a = b = c
                while a > lo and x[a - 1] > x[c] - top / 2:
                    a -= 1
                while b < hi and x[b + 1] > x[c] - top / 2:
                    b += 1
                aside = abs(float(np.sin(x[lo:hi + 1] - np.linspace(x[lo], x[hi], hi - lo + 1)).sum())) * ds
                turns = [k for k in range(lo, hi) if corner[k]]
                notch = turns and turns[0] < c <= turns[-1] and (turns[-1] - turns[0]) * ds >= NOTCH
                if (b - a + 1) * ds <= STEP_WIDTH and aside >= STEP_SIDE and not notch:
                    found.append((top, a, b, c, aside))
        kept = []
        for top, a, b, c, aside in sorted(found, reverse=True):
            if not any(ka <= c <= kb for _, ka, kb in kept):  # (a ripple on a step's top)
                kept.append((top, a, b))
                x, y = pts[(c - m) % n]
                out.append(("step", round(float(x)), round(float(y)), math.degrees(top), aside))
    return out


def compared(old, new, reach=NEAR):
    """findings [(kind, x, y, measure, ...)] of an outline and of a candidate
    for it, matched one to one by kind and place (not by node: a refit moves
    and recuts the outline; within reach): (the old ones gone, the new ones with no
    match or worse than theirs, WORSE); a finding matched ambiguously (not
    each the other's nearest) counts as new"""
    def nearest(f, pool):
        near = [k for k, g in enumerate(pool) if g[0] == f[0] and math.dist(f[1:3], g[1:3]) <= reach]
        return min(near, key=lambda k: math.dist(f[1:3], pool[k][1:3]), default=None)
    pairs = {}
    for k, f in enumerate(new):
        o = nearest(f, old)
        if o is not None and nearest(old[o], new) == k:
            pairs[k] = o
    gone = [f for k, f in enumerate(old) if k not in pairs.values()]
    added = [f for k, f in enumerate(new)
             if k not in pairs or f[3] > old[pairs[k]][3] + max(0.5, WORSE * old[pairs[k]][3])]
    return gone, added


def dense(segs):
    """a closed contour (segment array) as a polyline, a point a unit or
    closer, its start repeated at its end"""
    pts = []
    for sg in segs:
        t = np.linspace(0, 1, max(2, math.ceil(np.linalg.norm(np.diff(sg, axis=0), axis=1).sum())) + 1)[:-1]
        pts.append(bez(sg, t) if len(sg) == 4 else sg[0] + t[:, None] * (sg[1] - sg[0]))
    return np.vstack(pts + [segs[0][0][None]])


def crossings(p, d, a, e, which=False):
    """how far along d from p each edge (a, a + e) is crossed (beyond a
    tenth of a unit); which: and the edges crossed"""
    w = a - p
    den = d[0] * e[:, 1] - d[1] * e[:, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / den
        u = (w[:, 0] * d[1] - w[:, 1] * d[0]) / den
    hit = (np.abs(den) > 1e-12) & (t > 0.1) & (u >= -1e-9) & (u < 1 + 1e-9)
    return (t[hit], np.flatnonzero(hit)) if which else t[hit]


def across(p, d, a, e, t, own=()):
    """the distance along d from p to the nearest side met, if that side
    runs within PARALLEL of t (a section of a stroke, as Strokes measures
    it), else inf; own: the edges next to p along its contour, not met"""
    dist, idx = crossings(p, d, a, e, which=True)
    keep = ~np.isin(idx, own)
    dist, idx = dist[keep], idx[keep]
    if not len(dist):
        return math.inf
    k = int(np.argmin(dist))
    return float(dist[k]) if abs(float(unit(e[idx[k]]) @ t)) >= PARALLEL else math.inf


def near(pts, region, r):
    """which of pts lie within r of a point of region"""
    if not len(region) or not len(pts):
        return np.zeros(len(pts), bool)
    return nearest(pts, np.asarray(region)) <= r


def nearest(pts, ref):
    """each of pts' distance to the nearest point of ref"""
    out = np.empty(len(pts))
    for i in range(0, len(pts), 256):
        q = pts[i:i + 256]
        out[i:i + 256] = np.sqrt(np.min(((q[:, None, :] - ref[None, :, :]) ** 2).sum(axis=2), axis=1))
    return out


def zone(was, region, r):
    """where a candidate for was may move it, blended at region (the
    source's points): within r of region, and along the arcs of was that
    come within r of it (fair_arcs refits each arc whole), within LIMIT
    units of the arc: (points, their reach)"""
    region = np.asarray(region, float).reshape(-1, 2)
    pts, reach = [region], [np.full(len(region), float(r))]
    for segs in was:
        for a, n, _ in arcs(segs):
            q = dense([segs[(a + k) % len(segs)] for k in range(n)])[:-1:3]
            if near(q, region, r).any():
                pts.append(q)
                reach.append(np.full(len(q), float(LIMIT)))
    return np.vstack(pts), np.concatenate(reach)


def within(pts, where):
    """which of pts lie in where (zone's)"""
    ref, reach = where
    out = np.zeros(len(pts), bool)
    for i in range(0, len(pts), 256):
        q = pts[i:i + 256]
        out[i:i + 256] = (np.sqrt(((q[:, None, :] - ref[None, :, :]) ** 2).sum(axis=2)) <= reach[None, :]).any(axis=1)
    return out


def sections(contours, where):
    """the outline measured across in where (zone's), every two units, at
    the samples whose ink meets a facing side: [(contour, its sample, the
    ink's width, the white's in front, inf where no facing side)]"""
    lines = [dense(sg) for sg in contours]
    a = np.vstack([q[:-1] for q in lines])
    e = np.vstack([np.diff(q, axis=0) for q in lines])
    out, first = [], 0
    for c, q in enumerate(lines):
        pts, n = q[:-1:2], len(q) - 1
        for i in np.flatnonzero(within(pts, where)):
            own = first + (2 * i + np.arange(-8, 9)) % n
            t = unit(pts[(i + 1) % len(pts)] - pts[i - 1])
            nrm = np.array([-t[1], t[0]])
            if len(crossings(pts[i] + 0.5 * nrm, np.array([1.0, 0.3]), a, e)) % 2 == 0:
                nrm = -nrm  # (into the ink)
            ink = across(pts[i], nrm, a, e, t, own)
            if ink < math.inf:
                out.append((c, i, ink, across(pts[i], -nrm, a, e, t, own)))
        first += n
    return out


def ups_and_downs(values, by):
    """the times values turn from rising to falling or back by over by"""
    n, ref, d = 0, values[0], 0
    for v in values[1:]:
        if d >= 0 and v > ref or d <= 0 and v < ref:
            ref = v
        elif abs(v - ref) > by:
            n += d != 0
            d, ref = (1 if v > ref else -1), v
    return n


def evenness(was, kept, where):
    """what the candidate kept does worse than was across its strokes
    in where (zone's; the two edges of a stroke paired by a
    section at each sample, each outline on its own): narrower or wider
    ink than was has there (WIDTH), its width rising and falling more
    often, less white in front; [what], or ["unresolved ..."]"""
    found = []
    old, new = sections(was, where), sections(kept, where)
    if not old or not new:
        return ["unresolved: no sections"]
    wo, wn = [s[2] for s in old], [s[2] for s in new]
    if min(wn) < min(wo) - WIDTH:
        found.append(f"pinched {min(wo):.0f} -> {min(wn):.0f}")
    if max(wn) > max(wo) + WIDTH:
        found.append(f"swollen {max(wo):.0f} -> {max(wn):.0f}")

    def turns(secs):
        runs, n = [], 0
        for c, i, w, _ in secs:
            if runs and runs[-1][0] == c and i - runs[-1][1] == 1:
                runs[-1][2].append(w)
            else:
                runs.append([c, i, [w]])
            runs[-1][1] = i
        for _, _, ws in runs:
            n += ups_and_downs(ws, WIDTH) if len(ws) > 2 else 0
        return n
    if turns(new) > turns(old):
        found.append(f"width rising and falling {turns(old)} -> {turns(new)}")
    co = [s[3] for s in old if s[3] < math.inf]
    cn = [s[3] for s in new if s[3] < math.inf]
    if co and cn and min(cn) < min(co) - WIDTH:
        found.append(f"white in front {min(co):.0f} -> {min(cn):.0f}")
    return found


def kept_outside(was, kept, where):
    """how far the candidate kept moves the outline of was outside where
    (zone's; units, both ways)"""
    far = 0.0
    for one, other in ((kept, was), (was, kept)):
        pts = np.vstack([dense(sg) for sg in one])
        ref = np.vstack([dense(sg) for sg in other])
        same = {tuple(q) for q in np.round(ref, 3)}
        away = np.array([q for q in pts if tuple(np.round(q, 3)) not in same]).reshape(-1, 2)
        away = away[~within(away, where)]
        if len(away):
            far = max(far, float(nearest(away, ref).max()))
    return far


def layout(contours):
    """each contour's turn (+1, -1) and how many others hold it, sorted"""
    lines = [dense(sg) for sg in contours]
    out = []
    for k, q in enumerate(lines):
        area = float(np.sum(q[:-1, 0] * q[1:, 1] - q[1:, 0] * q[:-1, 1]))
        depth = 0
        for j, o in enumerate(lines):
            if j != k:
                depth += len(crossings(q[0], np.array([1.0, 0.3]), o[:-1], np.diff(o, axis=0))) % 2
        out.append((1 if area > 0 else -1, depth))
    return sorted(out)


def guarded(was, kept, region, r):
    """the protections a candidate (kept) for was must keep, blended at
    region (the source's points; zone): [what it breaks]"""
    where = zone(was, region, r)
    found = []
    if len(kept) != len(was) or layout(kept) != layout(was):
        found.append("contours, their turn or nesting changed")
    if len(pieces(kept)) != len(kept):
        found.append("a contour crosses itself or another")
    far = kept_outside(was, kept, where)
    if far > OUTSIDE:
        found.append(f"moved {far:.1f} units away from the blend")
    b1, b0 = (np.vstack([dense(sg) for sg in c]) for c in (kept, was))
    for axis in (0, 1):
        for pick in (np.argmin, np.argmax):
            q1, q0 = b1[pick(b1[:, axis])], b0[pick(b0[:, axis])]
            if abs(q1[axis] - q0[axis]) > OUTSIDE and not within(np.array([q1, q0]), where).all():
                found.append(f"bounds moved {q0[axis]:.0f} -> {q1[axis]:.0f} away from the blend")
    return found + evenness(was, kept, where)


def stroked(strokes, flat, sliver, fair=True):
    """flat emboldened by strokes: (glyph, its contours as segment arrays)"""
    out = ufoLib2.objects.Glyph()
    anchors = []
    cleaned = merged_glyph(strokes.draw(flat, anchors))
    anchors = np.array(anchors)
    pen = out.getPen()
    kept = []
    # (where blend acted, before rejoined adds to it, and along the knees
    # it was asked to take: ш's middle stem, too little apart to blend,
    # joined into its line smooth)
    blended = list(strokes.region) + [q for key in strokes.knees if key in strokes.found for q in strokes.found[key]]
    for c in cleaned.contours:
        if contour_area(c) < sliver:
            continue
        rec = rejoined(c, anchors, short=strokes.blended and (list(blended), REGION * strokes.ax),
                       acted=strokes.region)
        segs = segments(rec.value) if fair else None
        if segs:
            faired = [fair_contour(sg, strokes.upright)[0] for sg in segs]
            # (one crossing itself where the fitted one did not, a twist
            # the size of a unit: as fitted; k's crotch)
            if len(pieces(faired)) > len(pieces(segs)):
                faired = segs
            draw(pen, faired)
            kept += faired
        else:
            rec.replay(pen)
            kept += segments(rec.value) or []
    return out, kept


def smooth_counter(glyph, sigma):
    """glyph (a ufoLib2 Glyph, upright frame) with its smallest contour, a
    small counter, refitted smooth: its outline smoothed over sigma units
    (Gaussian, the window narrowing to its corner), then one cubic between
    each two of its extremes, kept horizontal and vertical; its one corner,
    the sharpest turn, kept (q.sc's loop: the tail's weight changing fast
    along it left its inside edgy, the corner where the tail's diagonal
    meets its bottom as Q's). Unchanged with fewer than two contours."""
    from ufoLib2.objects import Contour, Point

    if len(glyph.contours) < 2:
        return glyph

    def area(c):
        q = np.array([(p.x, p.y) for p in c.points])
        return abs(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])) / 2
    ci = min(range(len(glyph.contours)), key=lambda i: area(glyph.contours[i]))
    pts = [(np.array((p.x, p.y), float), p.type) for p in glyph.contours[ci].points]
    first = next(i for i, (_, t) in enumerate(pts) if t)
    pts = pts[first + 1:] + pts[:first + 1]  # ends on an on-curve point
    dense, cur, off = [], pts[-1][0], []
    for q, t in pts:
        if t is None:
            off.append(q)
            continue
        u = np.linspace(0, 1, 60, endpoint=False)
        dense.extend(bez([cur] + off + [q], u) if len(off) == 2 else cur + np.outer(u, q - cur))
        cur, off = q, []
    dense = np.array(dense)
    ring = np.vstack([dense, dense[:1]])
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))])
    s = np.linspace(0, d[-1], max(int(d[-1] / 2), 16), endpoint=False)  # every 2 units
    P = np.column_stack([np.interp(s, d, ring[:, 0]), np.interp(s, d, ring[:, 1])])
    k = 6  # the corner: the largest turn over 12 units either side
    a, b = P - np.roll(P, k, 0), np.roll(P, -k, 0) - P
    turn = np.abs(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1)))
    run = np.roll(P, -int(np.argmax(turn)), 0)
    run = np.vstack([run, run[:1]])
    m, idx = len(run), np.arange(len(run))
    sm = run.copy()
    for i in range(1, m - 1):
        w = np.exp(-0.5 * ((idx - i) / (sigma / 2)) ** 2)
        w[np.abs(idx - i) > min(i, m - 1 - i)] = 0  # symmetric: the corner stays put
        sm[i] = (w[:, None] * run).sum(0) / w.sum()
    ext = {0, m - 1}
    for axis in (0, 1):
        v = sm[3:m - 3, axis]
        ext |= {e for e in (int(np.argmin(v)) + 3, int(np.argmax(v)) + 3) if 3 < e < m - 4}
    ext = sorted(ext)

    def tangent(i, j):
        t = sm[j] - sm[i] if j > i else sm[i] - sm[j]
        t = t / np.linalg.norm(t)
        big = int(np.argmax(np.abs(t)))
        if abs(t[big]) > 0.97:  # at an extreme: exactly level or upright
            t = np.where(np.arange(2) == big, np.sign(t), 0.0)
        return t
    new = Contour()
    for j, (a, b) in enumerate(zip(ext, ext[1:])):
        ctrl, _ = fit_cubic(sm[a:b + 1], tangent(a, min(m - 1, a + 3)), tangent(b, max(0, b - 3)))
        for q in ctrl[1:3]:
            new.points.append(Point(float(q[0]), float(q[1])))
        new.points.append(Point(float(ctrl[3][0]), float(ctrl[3][1]), type="curve", smooth=j < len(ext) - 2))
    glyph.contours[ci] = new
    return glyph


def turned_knees(strokes, kept):
    """kept (segment contours, upright frame) with each of strokes' knees
    drawn as the Italic turns there (KNEE_QUARTER), a new list (looked for
    in every contour: the source's numbering is not the cleaned outline's)"""
    kept = list(kept)
    for key in sorted(strokes.knees & set(strokes.found)):
        for n, c in enumerate(kept):
            turned = knee_turned(c, strokes.found[key], strokes.slant, KNEE_QUARTER * strokes.thick)
            if turned:
                kept[n] = turned
                break
    return kept


def embolden_by_strokes(rec, ax, ay, thin, thick, hair, slant, sliver=SLIVER, root=0.0, split=False, free=0.0,
                        knees=(), log=None, *, fair=True, one_way=True):
    """rec (a RecordingPen, upright frame) emboldened by its strokes, as a
    ufoLib2 Glyph, cleaned (contours under sliver units' area dropped);
    not shifted (the caller moves it by ax / 2); root, split, free: Strokes';
    knees: keys (contour, segment) of curves taken as knees though the
    stroked outline leaves no step there to find them by (the gate then
    asks no step gone of them, and judges the bends with the knees turned);
    log, a list: given, the blend's verdict is added to it; fair, one_way:
    two stages, off only to find which stage makes a fault (a pilot calls
    this itself, past the cache: make_bold's jobs pass the rest
    positionally and cannot set them; docs/claude/stroking.md)"""
    strokes = Strokes(ax, ay, thin, thick, hair, slant, root, split, free)
    flat = tidy(merged_glyph(rec))
    if not flat.contours:
        return ufoLib2.objects.Glyph()
    strokes.turning = False  # (the knees found on the outline as moved)
    out, kept = stroked(strokes, flat, sliver, fair)
    turn = STEP_TURN
    forced = {tuple(k) for k in knees} & set(strokes.found) if strokes.blending else set()
    knees = {key for key, pts in strokes.found.items()
             if any(near(pts, [f[1:3]], KNEE_NEAR).any() for f in steps(kept, KNEE_TURN))} if strokes.blending else set()
    knees |= forced
    if knees or one_way:
        # a knee left in the outline: stroked again, its curve blended into
        # its line too, and judged by the knee's step; the arcs leaving a
        # line kept turning one way (one_way), but for the knees
        again = Strokes(ax, ay, thin, thick, hair, slant, root, split, free)
        again.knees = knees
        again.untouched = set(knees)
        again.turning = one_way
        out, kept = stroked(again, flat, sliver, fair)
        strokes, turn = again, (KNEE_TURN if knees else STEP_TURN)
    if strokes.blended:
        # a blended curve taken only where it removes a step and leaves no
        # step, bend or quality finding (slanted back and rounded) new or
        # worse, each matched to its own; and where it keeps what it must
        # (guarded: the outline away from the blend, contours, bounds, the
        # strokes' widths and the white between them); else as reviewed
        plain = Strokes(ax, ay, thin, thick, hair, slant, root, split, free)
        plain.blending, plain.turning = False, one_way
        plain.untouched = set(knees)
        before, was = stroked(plain, flat, sliver, fair)
        fixed, stepped = compared(steps(was, turn), steps(kept, turn))
        bent = compared(bends(was), bends(turned_knees(strokes, kept) if forced else kept), BEND_NEAR)[1]
        if forced:
            # knees named: the bends judged as they will be drawn (the knees
            # turned) and at the knees (elsewhere the blend may move a bend
            # by a few units, guarded holds the outline: ш's hook, 2.9 units,
            # its bend 67 units further up, 2026-11-12)
            bent = [b for b in bent if any(near(strokes.found[key], [b[1:3]], BEND_NEAR).any() for key in forced)]
        worse = compared(findings(before, slant), findings(out, slant))[1]
        broken = (guarded(was, kept, strokes.region, REGION * ax)
                  if (fixed or forced) and not (stepped or bent or worse) else None)
        taken = broken == []
        if log is not None:
            log.append(f"{'blended' if taken else 'as drawn'}: {'knees ' + str(sorted(strokes.knees)) + '; ' if strokes.knees else ''}"
                       f"{'named ' + str(sorted(forced)) + '; ' if forced else ''}"
                       f"steps gone {fixed}, steps new or worse {stepped}; "
                       f"bends new {bent}; findings new or worse {worse}; "
                       f"guarded {'not reached' if broken is None else broken or 'kept'}")
        if not taken:
            out = before
        elif strokes.knees:
            # each knee then drawn as the Italic turns there (KNEE_QUARTER)
            kept = turned_knees(strokes, kept)
            out = ufoLib2.objects.Glyph()
            draw(out.getPen(), kept)
    return out


def split_cubic(sg, t):
    """the cubic sg cut at t (de Casteljau): (first, second)"""
    a, b, c, d = sg
    ab, bc, cd = a + (b - a) * t, b + (c - b) * t, c + (d - c) * t
    abc, bcd = ab + (bc - ab) * t, bc + (cd - bc) * t
    m = abc + (bcd - abc) * t
    return np.array([a, ab, abc, m]), np.array([m, bcd, cd, d])


def knee_turned(contour, found, slant, w):
    """contour (segment arrays, upright frame) with the knee beside found
    (its curve's moved samples) drawn as the Italic turns (KNEE_QUARTER):
    seen slanted, from the line's end to upright, then a quarter w wide
    round onto the bowl's curve after the counter's bottom; None where
    there is no such line, bottom or room"""
    sl = lambda q: q + np.outer(q[:, 1], [slant, 0])  # noqa: E731
    up = lambda q: q - np.outer(q[:, 1], [slant, 0])  # noqa: E731
    segs = [sl(np.asarray(sg, float)) for sg in contour]
    found = sl(np.asarray(found, float))
    L = len(segs)
    for back in (False, True):
        if back:  # (the contour running the other way: turned, done, turned back)
            segs = [sg[::-1] for sg in segs[::-1]]
        k = next((k for k, sg in enumerate(segs) if len(sg) == 2
                  and min(np.linalg.norm(found[[0, -1]] - sg[1], axis=1)) < KNEE_NEAR), None)
        if k is None:
            continue
        # the counter's bottom: the first node after the line where the
        # edge runs level, a curve after it
        m = None
        for n in range(1, 5):
            sg = segs[(k + n) % L]
            if len(sg) != 4:
                break
            t = sg[3] - sg[2]
            if np.linalg.norm(t) > 1e-9 and abs(unit(t)[1]) < math.sin(math.radians(3)) and len(segs[(k + n + 1) % L]) == 4:
                m = n
                break
        if m is None:
            continue
        P0, Lp = segs[k]
        d = unit(Lp - P0)
        if d[1] >= 0:
            continue
        bowl = segs[(k + m + 1) % L]
        H = KNEE_RATIO * w
        for t in np.linspace(0, 0.9, 1801):
            Bp = bez(bowl, t)
            V = np.array([Bp[0] - w, Bp[1] + H])
            if V[0] - (Lp[0] + (V[1] - Lp[1]) * d[0] / d[1]) >= KNEE_CLEAR * w:
                break
        else:
            continue
        if V[1] >= Lp[1]:
            continue
        rest = split_cubic(bowl, t)[1]
        tb = unit(rest[1] - rest[0])
        hl, hv, hq, hb = KNEE_HANDLES
        drop = Lp[1] - V[1]
        quarter = np.array([V, V - [0, hq * H], Bp - hb * w * tb, Bp])
        # (a node at the counter's bottom, level, as before: the quarter
        # cut at its lowest point, the rest of it fitted into the bowl)
        ts = np.linspace(0, 1, 2001)
        tl = ts[np.argmin(bez(quarter, ts)[:, 1])]
        if 0.02 < tl < 0.98:
            quarter, after = split_cubic(quarter, tl)
            low = quarter[3].copy()
            quarter[2][1] = low[1]
            run = np.concatenate([bez(after, ts[::50]), bez(rest, ts[::25])])
            ctrl, _err = fit_cubic(run, np.array([1.0, 0.0]), unit(rest[3] - rest[2]))
            if ctrl is None:
                continue
            rest = np.array(ctrl)
        new = [np.array([Lp, Lp + hl * drop / abs(d[1]) * d, V + [0, hv * drop], V]), quarter, rest]
        # (in place: the contour starts where it did)
        gone = {(k + j) % L for j in range(1, m + 2)}
        out = []
        for j in range(L):
            if j == (k + 1) % L:
                out += new
            elif j not in gone:
                out.append(segs[j])
        if back:
            out = [sg[::-1] for sg in out[::-1]]
        return [up(sg) for sg in out]
    return None


def findings(glyph, slant):
    """the quality checks' construction findings and reversals of glyph
    (upright frame) slanted back and rounded (but smooth nodes turning
    between two curves: make_bold rounds them smoothly, round_smoothly;
    one at a line it cannot turn): [(kind, x, y, measure)], the measure in
    degrees, units (extreme, step) or nodes (grid)"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
    from checks import construction, reversals
    from fontTools.pens.roundingPen import RoundingPen
    from fontTools.pens.transformPen import TransformPen

    sloped = ufoLib2.objects.Glyph()
    glyph.draw(TransformPen(RoundingPen(sloped.getPen()), (1, 0, slant, 1, 0, 0)))
    def at_line(where):
        x, y = (int(v) for v in where.split(","))
        for c in sloped.contours:
            ons = [p for p in c.points if p.type]
            for i, p in enumerate(ons):
                if (round(p.x), round(p.y)) == (x, y):
                    return p.type == "line" or ons[(i + 1) % len(ons)].type == "line"
        return True
    found = [f for f in construction(sloped) if f[0] != "smooth" or at_line(f[1])]
    return ([(kind, *(map(int, where.split(",")) if where else (0, 0)), float(detail.split()[0]))
             for kind, where, detail in found]
            + [("wobble", x, y, d) for x, y, d in reversals(sloped)])


def emboldened(job):
    """embolden_by_strokes for a process pool: job = (name, rec's value,
    its arguments); (name, the result's RecordingPen value, or None where
    it failed: the caller falls back); with MYIA_BLEND_LOG (a file) the
    blend's verdicts are added to it, a line a glyph"""
    name, value, args = job
    rec = RecordingPen()
    rec.value = value
    log = []
    try:
        glyph = embolden_by_strokes(rec, *args, log=log)
    except (ValueError, IndexError, ZeroDivisionError, np.linalg.LinAlgError):
        return name, None
    if log and os.environ.get("MYIA_BLEND_LOG"):
        with open(os.environ["MYIA_BLEND_LOG"], "a") as f:
            f.write(f"{name}: {log[0]}\n")
    out = RecordingPen()
    glyph.draw(out)
    return name, out.value
