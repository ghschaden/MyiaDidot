"""degenerate.py UFO ...: outline pieces that are there by accident.

Three exact, geometric faults (2026-11-27, found by eye on the Bold Italic's
T and ʈ ɭ; no check saw them):

- zero: a segment whose start and end are the same point (T's 732,1352: a
  line of no length after a curve's end);
- unsmooth: an on-curve point whose two handles (or line neighbours) lie on
  one line through it, within LINED degrees, but which is not marked smooth
  (an editor then lets the two sides drift apart; T's 732,1352 again);
- sliver: a curve shorter than SLIVER units between two corner points (ʈ ɭ's
  curl, 589,-116 -> 582,-127, 13 units between two corners).

One line a finding: glyph, kind, x,y. Composites are not read (their base is).
"""

import math
import sys
from pathlib import Path

import ufoLib2

LINED = 0.5  # degrees
SLIVER = 16  # units (derive.smooth_curves' `tiny`)


def _angle(a, b):
    """degrees between directions a and b"""
    return abs(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1])))


def findings(glyph):
    out = []
    for contour in glyph.contours:
        pts = contour.points
        n = len(pts)
        if n < 2:
            continue
        on = [i for i, p in enumerate(pts) if p.type]
        for k, i in enumerate(on):
            p = pts[i]
            j = on[(k + 1) % len(on)]
            q = pts[j]
            if n > 1 and (p.x, p.y) == (q.x, q.y) and i != j:
                out.append(("zero", p.x, p.y))
            prev, nxt = pts[(i - 1) % n], pts[(i + 1) % n]
            a = (p.x - prev.x, p.y - prev.y)
            b = (nxt.x - p.x, nxt.y - p.y)
            if not p.smooth and math.hypot(*a) > 1 and math.hypot(*b) > 1 and (prev.type is None or nxt.type is None):
                if _angle(a, b) <= LINED:
                    out.append(("unsmooth", p.x, p.y))
            # a curve from p to q (handles between), both ends corners
            if q.type == "curve" and pts[(i + 1) % n].type is None and not p.smooth and not q.smooth:
                if 0 < math.dist((p.x, p.y), (q.x, q.y)) < SLIVER:
                    out.append(("sliver", q.x, q.y))
    return out


def found(font):
    return {g.name: f for g in font if g.contours and (f := findings(g))}


def main():
    for path in sys.argv[1:]:
        got = found(ufoLib2.Font.open(path))
        kinds = {}
        for f in got.values():
            for k, *_ in f:
                kinds[k] = kinds.get(k, 0) + 1
        print(Path(path).stem.split("-")[-1], len(got), "glyphs", kinds)
        for name, f in sorted(got.items()):
            print(f"   {name:14}", "  ".join(f"{k} {x:.0f},{y:.0f}" for k, x, y in f))


if __name__ == "__main__":
    main()
