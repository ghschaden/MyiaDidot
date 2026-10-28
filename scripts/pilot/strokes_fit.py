"""Pilot, step 2: the stroke pilot's weights drawn with the Italic's curves.

strokes_pilot.py moves the Italic's outline (sampled every STEP units) out
by each stroke section's weight, smoothed along the outline; its refit put
nodes wherever a cubic stopped holding, a third more than the Italic has,
and kinks. Here every sample keeps the Italic segment it came from, so the
moved outline is redrawn with the Italic's own segments: one cubic for
each Italic curve, one line for each line, its ends where the Italic's
nodes moved to. Tangents at a smooth node: the moved outline's there (one
direction for both sides), held horizontal or upright (in the slanted
frame) where the Italic has an extreme; at a corner each side's own.
Each cubic's handle lengths by least squares. Convex corners are mitred;
a crotch's moved sides cross and the cleaning (pathops, on the curves)
cuts them at their meeting point.

    .venv/bin/python -I scripts/pilot/strokes_fit.py OUT.ufo glyph ...

A study (FONT-DESIGN.md, Bold Italic from strokes), not part of the build.
"""
import math
import os
import sys

import numpy as np

sys.path[:0] = ["scripts", "scripts/quality", "scripts/pilot"]
import make_bold as mb
import ufoLib2
from derive import merged_glyph
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from strokes_pilot import (
    AX,
    AY,
    CORNER,
    KX,
    PARALLEL,
    SIGMA,
    SLANT,
    STEP,
    THICK,
    THIN,
    bez,
    dbez,
    fit_cubic,
    raycast,
    src,
    unit,
)

# advances as today's Bold Italic (spacing is not this study's)
bold = ufoLib2.Font.open("sources/MyiaDidot-BoldItalic.ufo")
# what a hairline gains across (units, both sides together), fading into
# the stem's AX as the stroke thickens (step 3, the person's choice);
# references: Bodoni Moda's hairlines gain nothing, Libre Bodoni's a quarter
HAIR = float(os.environ.get("HAIR", 12))  # the person's choice 2026-10-28
UPRIGHT = unit(np.array([-SLANT, 1.0]))  # the slanted frame's vertical, deslanted


def sample(contour):
    """the contour's segments, each [(point, tangent)] from its start node
    (t = 0) up to its end; per node: is it a corner (in, out tangents),
    its Italic tangent, is it an extreme; per segment: a line?"""
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
        seg = []
        for s in range(m):
            t = s / m
            d = dbez(pts, t)
            if np.linalg.norm(d) < 1e-9:
                d = dbez(pts, min(1, t + 1e-3)) if t < 0.5 else dbez(pts, t - 1e-3)
            seg.append((bez(pts, t), unit(d)))
        segs.append(seg)
        # the node: tangents in and out (from its neighbouring points)
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
            if abs(t[1]) < 0.02:
                extreme = np.array([math.copysign(1, t[0]), 0.0])
            elif abs(t[0] - t[1] * UPRIGHT[0] / UPRIGHT[1]) < 0.02:
                extreme = UPRIGHT * math.copysign(1, t[1])
        nodes.append({"corner": corner, "tin": tin, "tout": tout, "extreme": extreme})
    return segs, lines, nodes


def weights(contours, sign):
    """each sample's weight (0 hairline .. 1 stem), paired across its section
    and smoothed along the outline, as strokes_pilot.offset_glyph"""
    flat = [s for c in contours for seg in c[0] for s in seg]
    pts = np.array([s[0] for s in flat])
    segs = np.array([(pts[q], pts[q + 1]) for q in range(len(pts) - 1)])
    # (segments across a contour's seam and between contours: harmless,
    # the closing ones added explicitly)
    starts = np.cumsum([0] + [sum(len(seg) for seg in c[0]) for c in contours])
    closing = [(pts[starts[q + 1] - 1], pts[starts[q]]) for q in range(len(contours))]
    keep = np.ones(len(segs), bool)
    keep[starts[1:-1] - 1] = False
    segs = np.concatenate([segs[keep], np.array(closing)])
    raw, facing = np.full(len(flat), np.nan), np.full(len(flat), -1)
    for q, (p, t) in enumerate(flat):
        nrm = sign * np.array([t[1], -t[0]])
        d, th = raycast(p, -nrm, segs)
        if d is not None and abs(float(t @ th)) > PARALLEL:
            raw[q] = min(1.0, max(0.0, (d - THIN) / (THICK - THIN)))
            facing[q] = int(np.argmin(np.linalg.norm(pts - (p - nrm * d), axis=1)))
    other = np.where(facing >= 0, raw[np.maximum(facing, 0)], np.nan)
    paired = np.where(np.isnan(other), raw, np.nanmean(np.stack([raw, other]), axis=0))
    out = []
    for c in range(len(contours)):
        ks = paired[starts[c]:starts[c + 1]].copy()
        P = pts[starts[c]:starts[c + 1]]
        N = len(P)
        arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        total = arc[-1] + np.linalg.norm(P[0] - P[-1])
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
        out.append(sm)
    return out


def move(p, t, k, sign):
    nrm = sign * np.array([t[1], -t[0]])
    return p + np.array([nrm[0] * (HAIR + (AX - HAIR) * k) / 2, nrm[1] * AY / 2])


def mitre(p1, t1, p2, t2):
    den = t1[0] * t2[1] - t1[1] * t2[0]
    if abs(den) < 1e-6:
        return None
    u = ((p2 - p1)[0] * t2[1] - (p2 - p1)[1] * t2[0]) / den
    m = p1 + u * t1
    if np.linalg.norm(m - p1) < 3 * AX and np.linalg.norm(m - p2) < 3 * AX:
        return m
    return None


def tidy(glyph):
    """glyph without the overlap removal's near-zero lines (a node and its
    copy a unit apart): the copy goes, the node takes its smoothness"""
    for c in glyph.contours:
        while True:
            P = c.points
            ons = [i for i, p in enumerate(P) if p.type]
            for k, j in enumerate(ons):
                i = ons[k - 1]
                if P[j].type == "line" and math.hypot(P[j].x - P[i].x, P[j].y - P[i].y) < 2 and len(ons) > 2:
                    P[i].smooth = P[j].smooth
                    if i < j or j:
                        del P[j]
                    break
            else:
                break
    return glyph


def crotches(segs, lines, nodes, kc, sign):
    """a tiny concave round whose radius is under half the offset there (as
    r's ball meeting its arm) turns inside out when moved: drawn as a line
    between two corners, the cleaning cuts the crossing sides at their
    meeting point, a crotch (in place)"""
    L = len(segs)
    first = np.cumsum([0] + [len(s) for s in segs])
    for k in range(L):
        seg = segs[k]
        t0, t1 = seg[0][1], seg[-1][1]
        turn = math.acos(max(-1, min(1, float(t0 @ t1))))
        concave = sign * (t0[0] * t1[1] - t0[1] * t1[0]) < 0
        offset = (HAIR + (AX - HAIR) * float(kc[first[k]:first[k + 1]].mean())) / 2
        if lines[k] or not concave or turn < math.radians(45) or len(seg) * STEP / turn > offset / 2:
            continue
        lines[k] = True
        for n in (nodes[k], nodes[(k + 1) % L]):
            n["corner"], n["extreme"] = True, None
        nodes[k]["tout"] = unit(segs[(k + 1) % L][0][0] - seg[0][0])
        nodes[(k + 1) % L]["tin"] = nodes[k]["tout"]


def fit_glyph(glyph, report, anchors):
    """glyph (deslanted, merged) -> RecordingPen of the moved outline,
    drawn with the Italic's segments (uncleaned)"""
    def area(c):
        pts = [(p.x, p.y) for p in c.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    sign = 1 if max((area(c) for c in glyph.contours), key=abs) > 0 else -1
    contours = [sample(c) for c in glyph.contours]
    ks = weights(contours, sign)
    rec = RecordingPen()
    for (segs, lines, nodes), kc in zip(contours, ks):
        crotches(segs, lines, nodes, kc, sign)
        # moved samples per segment
        moved, q = [], 0
        for seg in segs:
            moved.append([move(p, t, kc[q + s], sign) for s, (p, t) in enumerate(seg)])
            q += len(seg)
        L = len(segs)
        # an extreme moves along the outline (the offset is wider across
        # than up and down): its node slides to where the moved outline's
        # tangent is the extreme's, within a third of either segment
        for k in range(L):
            nd = nodes[k]
            if nd["extreme"] is None or lines[k - 1] or lines[k] or L < 2:
                continue
            prev, here = moved[k - 1], moved[k]
            both = prev + here
            lo, hi = max(3, len(prev) - len(prev) // 3), min(len(both) - 3, len(prev) + len(here) // 3)

            def off(i, both=both, e=nd["extreme"]):
                t = unit(both[i + 2] - both[i - 2])
                return abs(t[0] * e[1] - t[1] * e[0])
            best = min(range(lo, hi + 1), key=off, default=len(prev))
            moved[k - 1], moved[k] = both[:best], both[best:]
        # each node's moved position(s): (arriving, leaving)
        # a line moves parallel, by its weight along its length (its ends'
        # alone thin where the weight fades towards a cut end)
        first = np.cumsum([0] + [len(s) for s in segs])
        kline = [float(kc[first[k]:first[k + 1]].mean()) if lines[k] else None for k in range(L)]
        ends = []
        for k in range(L):
            nd = nodes[k]
            p = segs[k][0][0]
            kk = kc[first[k]]
            ka = kk if kline[k - 1] is None else kline[k - 1]
            kb = kk if kline[k] is None else kline[k]
            if nd["corner"]:
                a, b = move(p, nd["tin"], ka, sign), move(p, nd["tout"], kb, sign)
                convex = sign * (nd["tin"][0] * nd["tout"][1] - nd["tin"][1] * nd["tout"][0]) > 0
                m = mitre(a, nd["tin"], b, nd["tout"]) if convex else None
                ends.append((m, m) if m is not None else (a, b))
            elif kline[k - 1] is not None or kline[k] is not None:
                t = unit(nd["tin"] + nd["tout"])
                q = move(p, t, kb if kline[k] is not None else ka, sign)
                ends.append((q, q))
            else:
                ends.append((moved[k][0], moved[k][0]))
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
                    t = unit(ends[k][0] - ends[k - 1][1]) if lines[k - 1] else unit(ends[(k + 1) % L][0] - ends[k][1])
                tans.append((t, t))
        anchors += [p for e in ends for p in e]
        rec.moveTo(tuple(ends[0][1]))
        for k in range(L):
            j = (k + 1) % L
            start, end = ends[k][1], ends[j][0]
            if lines[k]:
                rec.lineTo(tuple(end))
            else:
                pts = np.array([start] + moved[k][1:] + [end])
                ctrl, err = fit_cubic(pts, tans[k][1], tans[j][0])
                if ctrl is None:
                    rec.lineTo(tuple(end))
                else:
                    report.append(float(err.max()))
                    rec.curveTo(tuple(ctrl[1]), tuple(ctrl[2]), tuple(ctrl[3]))
            if j and not np.allclose(ends[j][0], ends[j][1]):
                rec.lineTo(tuple(ends[j][1]))
        if not np.allclose(ends[0][0], ends[0][1]):
            rec.lineTo(tuple(ends[0][1]))
        rec.closePath()
    return rec


def contour_area(c):
    pts = [(p.x, p.y) for p in c.points if p.type]
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def rejoined(contour, anchors):
    """contour with the cleaning's splits undone: a smooth node that is
    none of the moved Italic nodes joins the cubics either side (refitted
    through both, exact where they are halves of one cubic)"""
    P = contour.points
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    pt = lambda q: np.array([P[q % n].x, P[q % n].y], float)  # noqa: E731
    segs = []  # (start, ctrl or None, end)
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
    for a, b in zip(keep, keep[1:] + [keep[0] + len(segs)]):
        run = [segs[k % len(segs)] for k in range(a, b)]
        if len(run) == 1:
            sg = run[0]
            if len(sg) == 2:
                rec.lineTo(tuple(sg[1]))
            else:
                rec.curveTo(*(tuple(q) for q in sg[1:]))
            continue
        pts = np.array([bez(sg, t) for sg in run for t in np.linspace(0, 1, 40)[:-1]] + [run[-1][-1]])
        ctrl, _err = fit_cubic(pts, unit(run[0][1] - run[0][0]), unit(run[-1][-1] - run[-1][-2]))
        rec.curveTo(*(tuple(q) for q in ctrl[1:]))
    rec.closePath()
    return rec


def fit(name):
    g = src[name]
    rec = mb.contours_only(g)
    wide = RecordingPen()
    rec.replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), (1, 0, -SLANT, 1, 0, 0)))
    flat = tidy(merged_glyph(wide))
    errors = []
    anchors = []
    drawn = fit_glyph(flat, errors, anchors)
    cleaned = merged_glyph(drawn)
    out = ufoLib2.objects.Glyph(name)
    pen = TransformPen(out.getPen(), (1, 0, SLANT, 1, AX / 2, 0))
    for c in cleaned.contours:
        if contour_area(c) < 800:  # slivers (a crotch's crossing sides)
            continue
        rejoined(c, np.array(anchors)).replay(pen)
    out.width = bold[name].width if name in bold else round(g.width * KX + AX)
    return out, errors


if __name__ == "__main__":
    dst = ufoLib2.Font()
    cmap = {chr(u): g.name for g in src for u in g.unicodes}
    for n in (cmap.get(a, a) for a in sys.argv[2:]):
        g, errors = fit(n)
        dst.newGlyph(n)
        g.draw(RoundingPen(dst[n].getPen()))
        dst[n].width = g.width
        print(f"{n}: {sum(len([p for p in c.points if p.type]) for c in g.contours)} nodes, "
              f"fit error max {max(errors, default=0):.1f}")
    dst.save(sys.argv[1], overwrite=True)
