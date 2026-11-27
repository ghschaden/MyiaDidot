"""degenerate.py UFO ... [--fix]: outline pieces that are there by accident.

Three exact, geometric faults (2026-11-27, found by eye on the Bold Italic's
T and ʈ ɭ; no check saw them):

- zero: a segment whose start and end are the same point (T's 732,1352: a
  line of no length after a curve's end);
- unsmooth: an on-curve point whose two handles (or line neighbours) lie on
  one line through it, within LINED degrees, but which is not marked smooth
  (an editor then lets the two sides drift apart; T's 732,1352 again);
- stub: a curve shorter than STUB units between two corner points (ʈ ɭ's
  curl, 589,-116 -> 582,-127, 13 units between two corners).

The first two are mended exactly, nothing moving (`mend`): the zero
segment's end point deleted (a zero curve's handles with it, when they sit
on the point too), the lined-up point marked smooth. The generators mend
what they write (derive.py, smallcaps.py, make_bold.finalize, which the
Italic's writer shares); `--fix` mends the glyphs drawn by hand (the
Regular's, and those kept as drawn in a generated style), then make
normalize. glyph_lint.py reports all three kinds (KINDS there); zero and
unsmooth are held at none, stubs to their list (some are drawn serif
corners).

One line a finding: glyph, kind, x,y. Composites are not read (their base is).
"""

import argparse
import math
import sys
from pathlib import Path

import ufoLib2

LINED = 0.5  # degrees
STUB = 16  # units (derive.smooth_curves' `tiny`)


def _angle(a, b):
    """degrees between directions a and b"""
    return abs(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1])))


def _closed(contour):
    return len(contour.points) > 1 and contour.points[0].type != "move"


def _lined(pts, i):
    """point i is a corner whose sides leave it along one line"""
    n = len(pts)
    p, prev, nxt = pts[i], pts[(i - 1) % n], pts[(i + 1) % n]
    a = (p.x - prev.x, p.y - prev.y)
    b = (nxt.x - p.x, nxt.y - p.y)
    return (not p.smooth and math.hypot(*a) > 1 and math.hypot(*b) > 1
            and (prev.type is None or nxt.type is None) and _angle(a, b) <= LINED)


def _zero_after(pts, i):
    """(j, handles) for the segment after on-curve point i when it has no
    length: j its end, handles the off-curve indices between (all on the
    point); None otherwise"""
    n = len(pts)
    p = pts[i]
    handles = []
    j = (i + 1) % n
    while pts[j].type is None:
        handles.append(j)
        j = (j + 1) % n
    q = pts[j]
    if j == i or (p.x, p.y) != (q.x, q.y):
        return None
    if any((pts[h].x, pts[h].y) != (p.x, p.y) for h in handles):
        return None  # a loop, not nothing: left to be seen
    return j, handles


def findings(glyph):
    out = []
    for contour in glyph.contours:
        if not _closed(contour):
            continue
        pts = contour.points
        n = len(pts)
        on = [i for i, p in enumerate(pts) if p.type]
        for k, i in enumerate(on):
            p = pts[i]
            j = on[(k + 1) % len(on)]
            q = pts[j]
            if (p.x, p.y) == (q.x, q.y) and i != j:
                out.append(("zero", p.x, p.y))
            if _lined(pts, i):
                out.append(("unsmooth", p.x, p.y))
            # a curve from p to q (handles between), both ends corners
            if q.type == "curve" and pts[(i + 1) % n].type is None and not p.smooth and not q.smooth:
                if 0 < math.dist((p.x, p.y), (q.x, q.y)) < STUB:
                    out.append(("stub", q.x, q.y))
    return out


def mend(glyph):
    """glyph's zero segments deleted and lined-up corners marked smooth, in
    place, no point moving; the number of mends"""
    count = 0
    for contour in glyph.contours:
        if not _closed(contour):
            continue
        pts = contour.points
        again = True
        while again:  # one deletion at a time: the indices shift
            again = False
            on = [i for i, p in enumerate(pts) if p.type]
            if len(on) < 3:
                break
            for i in on:
                z = _zero_after(pts, i)
                if z:
                    j, handles = z  # (whether i is smooth: _lined below)
                    first = j == on[0]
                    keep = pts[i]
                    for idx in sorted([j, *handles], reverse=True):
                        del pts[idx]
                    if first:  # the contour starts where it did, on the point kept
                        at = next(k for k, p in enumerate(pts) if p is keep)
                        pts[:] = pts[at:] + pts[:at]
                    count += 1
                    again = True
                    break
        for i, p in enumerate(pts):
            if p.type and _lined(pts, i):
                p.smooth = True
                count += 1
    return count


def mend_font(font, names=None, skip=()):
    """mend every contour glyph of font (or of names), skipping skip; the
    names of the glyphs changed"""
    changed = []
    for name in names or sorted(font.keys()):
        if name in skip or name not in font:
            continue
        g = font[name]
        if g.contours and mend(g):
            changed.append(name)
    return changed


def found(font):
    return {g.name: f for g in font if g.contours and (f := findings(g))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo", nargs="+")
    ap.add_argument("--fix", action="store_true", help="mend the zero segments and lined-up corners in place")
    args = ap.parse_args()
    for path in args.ufo:
        font = ufoLib2.Font.open(path)
        if args.fix:
            changed = mend_font(font)
            font.save()
            print(f"{Path(path).name}: mended {len(changed)} glyphs: {' '.join(changed)}", file=sys.stderr)
        got = found(font)
        kinds = {}
        for f in got.values():
            for k, *_ in f:
                kinds[k] = kinds.get(k, 0) + 1
        print(Path(path).stem.split("-")[-1], len(got), "glyphs", kinds)
        for name, f in sorted(got.items()):
            print(f"   {name:14}", "  ".join(f"{k} {x:.0f},{y:.0f}" for k, x, y in f))


if __name__ == "__main__":
    main()
