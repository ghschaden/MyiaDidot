"""curvature.py UFO [GLYPH ...]: where a smooth outline changes how fast it
turns all at once (prototype, 2026-11-27).

Every check before this one reads directions: a kink is a corner, a smooth
node one whose handles do not line up. None reads how evenly a curve turns,
and the Bold Italic's T came out of the stroker with its left bracket as a
long, nearly straight curve and a tight one under the arm (the designer saw
it on Ʈ: "very unround"); its tangents are continuous, so nothing flagged it.

The measure: at each on-curve point between two curves whose tangents agree
(within SMOOTH degrees), the curvature at the end of the curve before and at
the start of the curve after (a cubic's end curvature: 2/3 |d1 x d2| /
|d1|^3, d1 the handle, d2 the next handle leg). A fair arc keeps the two
within a small ratio; JUMP and more is reported, with the side that is
flatter. Each glyph of a generated style is read against the same glyph of
its source (the Bold Italic's against the Italic's, the Bold's against the
Regular's): a jump the source has nowhere near as large at a node within
NEAR (scaled by the advances) is the style's own.

    python -I scripts/quality/curvature.py sources/MyiaDidot-BoldItalic.ufo T
"""

import math
import sys
from pathlib import Path

import ufoLib2

SMOOTH = 3  # degrees: tangents this close make a smooth join
JUMP = 3.0  # curvature ratio across a smooth join reported
MIN_LEG = 4  # units: a shorter handle leaves the curvature undefined
NEAR = 80  # units: the source's node counted as the same place
SOURCE = {"BoldItalic": "Italic", "Bold": "Regular"}


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def end_curvature(p0, p1, p2):
    """signed curvature of a cubic at p0, p1 its handle, p2 the next one"""
    d1, d2 = _sub(p1, p0), _sub(p2, p1)
    n = math.hypot(*d1)
    if n < MIN_LEG:
        return None
    return 2 / 3 * _cross(d1, d2) / n**3


def joins(glyph):
    """[(x, y, k_before, k_after)] at each smooth join of two curves"""
    out = []
    for contour in glyph.contours:
        pts = [(p.x, p.y, p.type) for p in contour.points]
        n = len(pts)
        for i, (x, y, t) in enumerate(pts):
            if t != "curve" or pts[(i + 1) % n][2] is not None or pts[(i - 1) % n][2] is not None:
                continue
            # the curve after starts at i: its handles i+1, i+2
            if pts[(i + 3) % n][2] != "curve":
                continue
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
            ta, tb = _sub((x, y), a[:2]), _sub(b[:2], (x, y))
            if min(math.hypot(*ta), math.hypot(*tb)) < MIN_LEG:
                continue
            turn = math.degrees(math.atan2(_cross(ta, tb), ta[0] * tb[0] + ta[1] * tb[1]))
            if abs(turn) > SMOOTH:
                continue
            # curvature at the end of the curve before: reversed, from (x, y)
            kb = end_curvature((x, y), a[:2], pts[(i - 2) % n][:2])
            ka = end_curvature((x, y), b[:2], pts[(i + 2) % n][:2])
            if kb is None or ka is None:
                continue
            out.append((x, y, -kb, ka))  # (the reversed curve turns the other way)
    return out


def jumps(glyph):
    """[(x, y, ratio, kb, ka)] the joins whose curvature jumps by JUMP or more"""
    out = []
    for x, y, kb, ka in joins(glyph):
        lo, hi = sorted((abs(kb), abs(ka)))
        same_side = kb * ka > 0
        ratio = hi / lo if lo > 1e-9 else math.inf
        if same_side and ratio >= JUMP:
            out.append((x, y, ratio, kb, ka))
    return out


FLAT = 3.0  # a curve this much flatter inside than at both its ends: a flat spot
SAMPLES = 16
MIN_LENGTH = 60  # units: a shorter curve's flat spot does not show
MIN_TURN = 20  # degrees the curve turns in all: a nearly straight one has no roundness to lose
MAX_RADIUS = 1000  # units: ends flatter than this are no rounder than the middle to the eye


def _point_curvature(seg, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg
    u = 1 - t
    d1 = (3 * (u * u * (x1 - x0) + 2 * u * t * (x2 - x1) + t * t * (x3 - x2)),
          3 * (u * u * (y1 - y0) + 2 * u * t * (y2 - y1) + t * t * (y3 - y2)))
    d2 = (6 * (u * (x2 - 2 * x1 + x0) + t * (x3 - 2 * x2 + x1)), 6 * (u * (y2 - 2 * y1 + y0) + t * (y3 - 2 * y2 + y1)))
    pt = (u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
          u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3)
    n = math.hypot(*d1)
    return pt, (_cross(d1, d2) / n**3 if n > 1e-6 else None)


def flats(glyph):
    """[(x, y, ratio, k_min, k_ends)] curves that turn one way throughout but
    go FLAT times flatter inside than at both ends (the Bold Italic's T, its
    left bracket: 2.48 at the ends, 0.43 inside)"""
    out = []
    for contour in glyph.contours:
        pts = [(p.x, p.y, p.type) for p in contour.points]
        n = len(pts)
        for i, (_, _, t) in enumerate(pts):
            if t is None or pts[(i + 1) % n][2] is not None or pts[(i + 3) % n][2] != "curve":
                continue
            seg = [pts[(i + k) % n][:2] for k in range(4)]
            ks = [_point_curvature(seg, j / SAMPLES) for j in range(SAMPLES + 1)]
            if any(k is None for _, k in ks):
                continue
            vals = [k for _, k in ks]
            if not (all(v > 0 for v in vals) or all(v < 0 for v in vals)):
                continue
            ends = min(abs(vals[0]), abs(vals[-1]))
            length = sum(math.dist(ks[m][0], ks[m + 1][0]) for m in range(SAMPLES))
            a0 = _sub(seg[1], seg[0]) if math.dist(seg[0], seg[1]) > 1e-6 else _sub(seg[2], seg[0])
            a1 = _sub(seg[3], seg[2]) if math.dist(seg[2], seg[3]) > 1e-6 else _sub(seg[3], seg[1])
            turn = abs(math.degrees(math.atan2(_cross(a0, a1), a0[0] * a1[0] + a0[1] * a1[1])))
            if length < MIN_LENGTH or turn < MIN_TURN or ends < 1 / MAX_RADIUS:
                continue
            j = min(range(1, SAMPLES), key=lambda m: abs(vals[m]))
            if abs(vals[j]) > 1e-9 and ends / abs(vals[j]) >= FLAT:
                (px, py), _ = ks[j]
                out.append((px, py, ends / abs(vals[j]), abs(vals[j]), ends))
    return out


def own(glyph, source_glyph):
    """the jumps of glyph its source glyph has nothing like near"""
    sx = glyph.width / source_glyph.width if source_glyph.width else 1
    out = []
    for measure in (jumps, flats):
        theirs = measure(source_glyph)
        out += [j for j in measure(glyph)
                if not any(math.dist((j[0], j[1]), (s[0] * sx, s[1])) < NEAR and s[2] >= j[2] / 2 for s in theirs)]
    return out


def main():
    path, names = Path(sys.argv[1]), sys.argv[2:]
    font = ufoLib2.Font.open(path)
    style = path.stem.split("-")[-1]
    source = None
    if style in SOURCE:
        source = ufoLib2.Font.open(path.with_name(path.name.replace(style, SOURCE[style])))
    found = {}
    for g in font:
        if names and g.name not in names or not g.contours:
            continue
        got = own(g, source[g.name]) if source is not None and g.name in source else jumps(g) + flats(g)
        if got:
            found[g.name] = got
    print(style, len(found), "glyphs")
    for name, got in sorted(found.items(), key=lambda kv: -max(j[2] for j in kv[1])):
        print(f"   {name:14}", "  ".join(f"{x:.0f},{y:.0f}: {r:.1f}x" for x, y, r, *_ in sorted(got, key=lambda j: -j[2])[:4]))


if __name__ == "__main__":
    main()
