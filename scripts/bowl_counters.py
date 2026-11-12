#!/usr/bin/env python3
"""The inside of a bowl on a stem (D Ь Ы Ъ Б and their small caps) as two curves.

    python scripts/bowl_counters.py UFO                    what would be redone, and by how much
    python scripts/bowl_counters.py UFO --out OUT.ufo      the candidates, for a sheet
    python scripts/bowl_counters.py UFO GLYPH ... --out OUT.ufo

The designer, 2026-11-10: "The insides of curves - e.g. in D - are not
good." The Bold Italic's small-cap D ran from its top into a tight
shoulder, then straight down to a corner above its widest point, and
out of that in a diagonal: five curves, a corner and an inflection where
the Regular has two curves. The italic small caps are FontForge's drafts
of Old Standard's capitals, the Bold Italic's their strokes emboldened;
neither draws a counter.

A bowl's counter here is an inner contour's run of curves between two
level flats (the top's underside and the foot's top), more than HEIGHT
apart, bulging to one side. It is redone as the Regular draws it: one
node at its widest point, upright there, one curve from each flat to it,
leaving the flat level; the handle lengths by least squares on the run as
it was (redraw.fit_cubic), so the counter keeps its size and its place
and loses what one curve cannot say. A run that is two such curves
already is left alone. Whole units; the flats, the stem's edge and its
brackets are not touched. A bowl's outside between two flats is redone
the same way, but only where it is broken (a corner between two of its
curves, a curve bending back): Old Standard's bowls run into a diagonal
at the lower right through smooth nodes, and that is left. A run that is two such curves is left as it is
(`sound`), so a second pass changes nothing.
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redraw as R  # noqa: E402

HEIGHT = 250  # units between the two flats, at least
FLAT = 20     # units: a level line this long is a flat
REACH = 0.9   # of the way to the corner: a handle's most
MOST = 15.0   # units: a run further from its two curves is no bowl (Д's counter, 43), left and named


def _area(contour):
    pts = [(p.x, p.y) for p in contour.points if p.type]
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


def _level(seg):
    # (2 units off level is a flat still: ы.sc's bar, 496 to 498)
    return len(seg) == 2 and abs(seg[0][1] - seg[1][1]) <= 2 and abs(seg[0][0] - seg[1][0]) >= FLAT


def _sample(seg, n=24):
    t = np.linspace(0, 1, n + 1)[:, None]
    p0, p1, p2, p3 = seg
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def runs(segs):
    """[(first, count)]: the runs of curves of a contour's segments that
    are a bowl's inside, between two level flats"""
    n, out = len(segs), []
    for i in range(n):
        if not _level(segs[i - 1]) or len(segs[i]) != 4:
            continue
        m = 0
        while m < n and len(segs[(i + m) % n]) == 4:
            m += 1
        if m >= n or not _level(segs[(i + m) % n]):
            continue
        a, b = segs[i][0], segs[(i + m - 1) % n][3]
        if abs(a[1] - b[1]) < HEIGHT:
            continue
        out.append((i, m))
    return out


def sound(one, two):
    """two curves that are a bowl's inside as it should be: level out of
    the flats, upright through the node between them, each bending one way"""
    return (one[1][1] == one[0][1] and two[2][1] == two[3][1]
            and one[2][0] == one[3][0] == two[1][0]
            and R.wrong_turn(one) is None and R.wrong_turn(two) is None)


KINK = 1.5  # degrees: two curves meeting at more are not smooth


def broken(run):
    """a run of curves with a corner between two of them (ы.sc's bowl came
    to a point of 15 degrees at its widest) or one that bends back"""
    for one, two in zip(run, run[1:]):
        if R.angle_between(one[3] - one[2], two[1] - two[0]) > KINK:
            return True
    return any(R.wrong_turn(c) is not None for c in run)


def redone(segs, first, count):
    """(the two curves for the run, how far the run was from them, where),
    or None if the run does not bulge to one side between its ends"""
    n = len(segs)
    run = [segs[(first + k) % n] for k in range(count)]
    pts = np.concatenate([_sample(s)[(1 if k else 0):] for k, s in enumerate(run)])
    a, b = pts[0], pts[-1]
    # which side it bulges to, from the flats' directions: the run leaves
    # along the first flat and arrives against the second
    d0 = R.unit(segs[first - 1][1] - segs[first - 1][0])
    d1 = R.unit(segs[(first + count) % n][1] - segs[(first + count) % n][0])
    if d0[0] * d1[0] >= 0:  # both flats run the same way: no bowl
        return None
    side = 1 if d0[0] > 0 else -1
    k = int(np.argmax(side * pts[:, 0]))
    if k < 3 or k > len(pts) - 4 or side * pts[k][0] - max(side * a[0], side * b[0]) < 20:
        return None
    # a bowl is widest about its middle (not Д's leg, widest under its top)
    if not 0.2 <= (pts[k][1] - a[1]) / (b[1] - a[1]) <= 0.8:
        return None
    e = np.round(pts[k])
    up = np.array([0.0, 1.0 if b[1] > a[1] else -1.0])
    p0, p3 = np.round(a), np.round(b)
    first_half = R.fit_cubic(pts[:k + 1], p0, np.array([float(side), 0.0]), e, up)
    second_half = R.fit_cubic(pts[k:], e, up, p3, np.array([-float(side), 0.0]))
    for c in (first_half, second_half):
        c[1], c[2] = np.round(c[1]), np.round(c[2])
    # level and upright exactly, and no handle further than REACH of the
    # way to the corner the two directions make (a shoulder as square as
    # eth.sc's asked for one past it: the curve bent back)
    first_half[1][1], first_half[2][0] = p0[1], e[0]
    second_half[1][0], second_half[2][1] = e[0], p3[1]
    for c, (flat, h) in ((first_half, (0, 1)), (second_half, (3, 2))):
        most = REACH * abs(e[0] - c[flat][0])
        if abs(c[h][0] - c[flat][0]) > most:
            c[h][0] = np.round(c[flat][0] + side * most)
    for c, (flat, h) in ((first_half, (0, 2)), (second_half, (3, 1))):
        most = REACH * abs(c[flat][1] - e[1])
        if abs(c[h][1] - e[1]) > most:
            c[h][1] = np.round(e[1] + math.copysign(most, c[flat][1] - e[1]))
    worst, where = 0.0, a
    for c, part in ((first_half, pts[:k + 1]), (second_half, pts[k:])):
        err, at = R.deviation(c, part)
        if err > worst:
            worst, where = err, part[at]
    return [first_half, second_half], float(worst), (round(float(where[0])), round(float(where[1])))


def redo(glyph):
    """glyph (in place) with each bowl's inside two curves; returns
    [(x, y of the widest point, nodes before, units from before, where)];
    nodes before 0: a run too far from two curves (MOST), left"""
    from ufoLib2.objects import Point

    if len(glyph.contours) < 2:
        return []
    outer = max(glyph.contours, key=lambda c: abs(_area(c)))
    sign = 1 if _area(outer) > 0 else -1
    done = []
    for contour in glyph.contours:
        inside = contour is not outer and _area(contour) * sign < 0
        try:
            segs = R.segments(contour)
        except ValueError:
            continue
        found = runs(segs)
        if not found:
            continue
        new = {}
        for first, count in found:
            got = redone(segs, first, count)
            if got is None:
                continue
            curves, dev, where = got
            if dev > MOST:
                done.append((int(curves[0][3][0]), int(curves[0][3][1]), 0, round(dev, 1), where))
                continue
            if count == 2 and sound(segs[first], segs[(first + 1) % len(segs)]):
                continue
            # a bowl's outside only where it is broken: Old Standard's
            # runs into a diagonal through smooth nodes, which is its design
            if not inside and not broken([segs[(first + j) % len(segs)] for j in range(count)]):
                continue
            new[first] = (count, curves)
            done.append((int(curves[0][3][0]), int(curves[0][3][1]), count + 1, round(dev, 1), where))
        if not new:
            continue
        out, k, n = [], 0, len(segs)
        skip = {(f + j) % n for f, (c, _) in new.items() for j in range(c)}
        while k < n:
            if k in new:
                out += new[k][1]
            elif k not in skip:
                out.append(segs[k])
            k += 1
        # (a run that wraps past the contour's first segment: start after it)
        pts = []
        smooth_at = {(float(c[1][0][0]), float(c[1][0][1])) for _, c in new.values()}
        for i, seg in enumerate(out):
            before = out[i - 1]
            x, y = float(seg[0][0]), float(seg[0][1])
            old = next((p for p in contour.points if p.type and p.x == x and p.y == y), None)
            pts.append(Point(int(x), int(y), "curve" if len(before) == 4 else "line",
                             smooth=(x, y) in smooth_at or bool(old is not None and old.smooth)))
            if len(seg) == 4:
                pts += [Point(int(seg[1][0]), int(seg[1][1])), Point(int(seg[2][0]), int(seg[2][1]))]
        contour.points[:] = pts
    return done


def finish(font, names=None):
    """every bowl's inside of the font redone, but in glyphs drawn by hand
    (the Italic's marked drawn, the bold styles' drawn.py): {glyph: redo's}"""
    from stem_joins import hand_drawn  # a redrawn letter is not hand-drawn in the bold styles

    out = {}
    for glyph in font:
        if names is not None and glyph.name not in names:
            continue
        if (not glyph.contours or hand_drawn(font, glyph)) and names is None:
            continue
        done = redo(glyph)
        if done:
            out[glyph.name] = done
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--out", help="the font with the counters redone, written here (never to the source)")
    a = ap.parse_args()
    font = ufoLib2.Font.open(a.ufo)
    found = finish(font, set(a.glyphs) if a.glyphs else None)
    for name, done in sorted(found.items(), key=lambda kv: -max(d[3] for d in kv[1])):
        print(f"{name:<18}" + "; ".join(
            (f"widest {x},{y}: {n} nodes -> 3, {dev} units at {w[0]},{w[1]}" if n
             else f"left as it is: {dev} units from two curves at {w[0]},{w[1]}") for x, y, n, dev, w in done))
    print(f"{len(found)} glyphs")
    if a.out:
        if Path(a.out).resolve() == Path(a.ufo).resolve():
            ap.error("--out is the source")
        font.save(a.out, overwrite=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
