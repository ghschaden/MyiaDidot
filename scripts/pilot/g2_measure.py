"""The G2 trial's measure: per glyph, the curvature jumps at smooth joins
of two curves (turning under 2 degrees, both handles SHORT or longer), and how far the second UFO's
outline is from the first's.

    .venv/bin/python -I scripts/pilot/g2_measure.py OLD.ufo NEW.ufo [glyph ...]

Columns: joins, largest jump (1/1000 units) and joins jumping over JUMP,
old then new; the largest distance from a new outline point to the old
outline. A study (FONT-DESIGN.md, Bold Italic from strokes), not part of
the build.
"""
import math
import sys

import numpy as np

sys.path[:0] = ["scripts"]
import ufoLib2
from stroke_bold import bez, curvatures

JUMP = 0.004  # 1/250 units
SHORT = 10  # units: a handle shorter, its curvature is mostly the rounding's


def segments(glyph):
    """each contour's segments as control point arrays (2: a line)"""
    out = []
    for c in glyph.contours:
        P = c.points
        n = len(P)
        ons = [i for i, p in enumerate(P) if p.type]
        segs = []
        for k, i in enumerate(ons):
            j = ons[(k + 1) % len(ons)]
            idx = [i] + [(i + m) % n for m in range(1, (j - i) % n or n)] + [j]
            segs.append(np.array([(P[q].x, P[q].y) for q in idx], float))
        out.append(segs)
    return out


def jumps(glyph, lines=False):
    """the curvature jumps at smooth joins of two curves (lines: of a curve
    and a line, the curve's curvature there)"""
    res = []
    for segs in segments(glyph):
        for a, b in zip(segs[-1:] + segs[:-1], segs):
            if (len(a) == 4 and len(b) == 4) == lines or (len(a) == 2 and len(b) == 2):
                continue
            ta, tb = a[-1] - a[-2], b[1] - b[0]
            if np.linalg.norm(ta) < SHORT or np.linalg.norm(tb) < SHORT:
                continue
            cos = ta @ tb / np.linalg.norm(ta) / np.linalg.norm(tb)
            if cos < math.cos(math.radians(2)):
                continue
            res.append(abs((curvatures(a)[1] if len(a) == 4 else 0) - (curvatures(b)[0] if len(b) == 4 else 0)))
    return res


def samples(glyph):
    ts = np.linspace(0, 1, 60)
    pts = []
    for segs in segments(glyph):
        for s in segs:
            pts.append(bez(s, ts) if len(s) == 4 else s[0] + ts[:, None] * (s[1] - s[0]))
    return np.concatenate(pts) if pts else np.zeros((0, 2))


def distance(old, new):
    a, b = samples(old), samples(new)
    if not len(a) or not len(b):
        return float("nan")
    return float(max(np.linalg.norm(b[i:i + 400, None] - a[None], axis=2).min(axis=1).max()
                     for i in range(0, len(b), 400)))


def main():
    old, new = ufoLib2.Font.open(sys.argv[1]), ufoLib2.Font.open(sys.argv[2])
    cmap = {chr(g.unicode): g.name for g in new if g.unicode}
    names = [cmap.get(a, a) for a in sys.argv[3:]] or sorted(g.name for g in new if g.contours)
    tot = [0, 0, 0, 0]
    lo = ln = 0
    rows = []
    for n in names:
        if n not in old or n not in new or not new[n].contours:
            continue
        jo, jn = jumps(old[n]), jumps(new[n])
        lo += sum(j > JUMP for j in jumps(old[n], True))
        ln += sum(j > JUMP for j in jumps(new[n], True))
        bo, bn = sum(j > JUMP for j in jo), sum(j > JUMP for j in jn)
        tot[0] += bo
        tot[1] += bn
        tot[2] += len(jo)
        tot[3] += len(jn)
        rows.append((n, len(jo), 1000 * max(jo, default=0), bo, len(jn), 1000 * max(jn, default=0), bn,
                     distance(old[n], new[n])))
    for r in rows:
        print("%-16s %3d %6.1f %3d | %3d %6.1f %3d | %5.1f" % r)
    print(f"joins {tot[2]} -> {tot[3]}, over {JUMP}: {tot[0]} -> {tot[1]}; "
          f"curve from line over {JUMP}: {lo} -> {ln}; moved > 5 units: {sum(r[7] > 5 for r in rows)}, > 10: {sum(r[7] > 10 for r in rows)}")


if __name__ == "__main__":
    main()
