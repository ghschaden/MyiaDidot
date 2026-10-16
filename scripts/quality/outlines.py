"""outlines.py UFO: construction of the outlines (glyphs drawn as contours)."""
import collections
import math
import sys

import ufoLib2

font = ufoLib2.Font.open(sys.argv[1])
src_key = "org.myiadidot.italicSource"
counts = collections.Counter()
worst = collections.defaultdict(list)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def turn(d0, d1):
    t = (d1 - d0 + math.pi) % (2 * math.pi) - math.pi
    return abs(math.degrees(t))


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def curvature(p0, p1, p2, p3, t):
    # first and second derivatives of the cubic
    u = 1 - t
    d1 = [3 * u * u * (p1[i] - p0[i]) + 6 * u * t * (p2[i] - p1[i]) + 3 * t * t * (p3[i] - p2[i]) for i in (0, 1)]
    d2 = [6 * u * (p2[i] - 2 * p1[i] + p0[i]) + 6 * t * (p3[i] - 2 * p2[i] + p1[i]) for i in (0, 1)]
    n = math.hypot(*d1)
    return (d1[0] * d2[1] - d1[1] * d2[0]) / n**3 if n > 1e-9 else 0


for g in font:
    if not g.contours:
        continue
    gname = g.name
    for c in g.contours:
        pts = list(c.points)
        n = len(pts)
        if n < 2:
            continue
        for i, p in enumerate(pts):
            if p.x != round(p.x) or p.y != round(p.y):
                counts["off-grid point"] += 1
                worst["off-grid point"].append(gname)
            if p.type is None:
                continue
            prev, nxt = pts[i - 1], pts[(i + 1) % n]
            a, b = (prev.x, prev.y), (nxt.x, nxt.y)
            here = (p.x, p.y)
            if a == here or b == here:
                continue
            t = turn(ang(a, here), ang(here, b))
            if p.smooth and t > 1.0 and (prev.type is None or nxt.type is None):
                counts["smooth point not smooth"] += 1
                worst["smooth point not smooth"].append((round(t, 1), gname, (p.x, p.y)))
            if not p.smooth and 0.5 < t < 8:
                counts["kink (corner nearly flat)"] += 1
                worst["kink (corner nearly flat)"].append((round(t, 1), gname, (p.x, p.y)))
        # curves: missing extremes, tiny handles, curvature jumps at smooth nodes
        segs = []
        start = next((k for k, p in enumerate(pts) if p.type), None)
        if start is None:
            continue
        ring = pts[start:] + pts[:start]
        k = 0
        while k < len(ring):
            p0 = ring[k]
            j = k + 1
            offs = []
            while j <= len(ring) and (ring[j % len(ring)].type is None):
                offs.append(ring[j % len(ring)])
                j += 1
            p3 = ring[j % len(ring)]
            if len(offs) == 2:
                P = [(p0.x, p0.y), (offs[0].x, offs[0].y), (offs[1].x, offs[1].y), (p3.x, p3.y)]
                segs.append((P, p0, p3))
                for h, base in ((P[1], P[0]), (P[2], P[3])):
                    if 0 < math.dist(h, base) < 2:
                        counts["handle under 2 units"] += 1
                        worst["handle under 2 units"].append(gname)
                xs = [bez(*P, t / 20) for t in range(21)]
                for axis in (0, 1):
                    lo = min(q[axis] for q in xs); hi = max(q[axis] for q in xs)
                    e0, e1 = sorted((P[0][axis], P[3][axis]))
                    over = max(e0 - lo, hi - e1)
                    if over > 3:
                        counts["missing extreme point"] += 1
                        worst["missing extreme point"].append((round(over, 1), gname, P[0]))
            k = j
            if j >= len(ring):
                break
        # curvature continuity at smooth on-curve points between two curves
        for (P, a0, a3), (Q, b0, b3) in zip(segs, segs[1:] + segs[:1]):
            if a3 is not b0 or not a3.smooth:
                continue
            k1, k2 = curvature(*P, 1.0), curvature(*Q, 0.0)
            big = max(abs(k1), abs(k2))
            if big > 1 / 400:  # a turn tighter than radius 400 somewhere at the join
                r = (min(abs(k1), abs(k2)) / big) if big else 1
                if r < 0.33 and math.dist(P[0], P[3]) > 60 and math.dist(Q[0], Q[3]) > 60:
                    counts["curvature jump at smooth point (x3+)"] += 1
                    worst["curvature jump at smooth point (x3+)"].append((round(1 / max(r, 1e-3), 1), gname, (a3.x, a3.y)))
print(sys.argv[1].split("/")[-1])
for k, v in counts.most_common():
    items = worst[k]
    if items and isinstance(items[0], tuple):
        items = sorted(items, reverse=True)
        sample = " ".join(f"{n}({v_})" for v_, n, _ in items[:14])
        glyphs = len({n for _, n, _ in items})
    else:
        sample = " ".join(sorted(set(items))[:14])
        glyphs = len(set(items))
    print(f"  {k:38} {v:6} in {glyphs:4} glyphs   e.g. {sample}")
