"""The Bold Italic open rounds' insides from the Italic's (c C G c.sc g.sc).

Emboldened by strokes, the inside of an open round comes out uneven where
the Italic's is smooth: c's left side bends twice, c.sc's dents, C and G run
flat and turn tight, g.sc steps where its jaw meets the bar (
2026-11-06). The closed rounds take the Italic's counter whole
(make_bold.italic_counter); an open round has no counter contour, so here
the run of its one outline that faces the bowl is replaced: from where it
leaves the upper terminal (its corner, or the inner top) round the bowl to
the inner bottom (or on to the bar's underside), by the Italic's run,
mapped piece by piece between the points they share (inner top, inner
left, inner bottom, the bar's underside): each piece scaled and moved on
its own so its ends land on the stroked run's, which keeps a level tangent
level and an upright one upright, and the Italic's curves as smooth as they
are. The ink outside the run, its weight and the terminals stay as stroked.
"""

import math

from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT
from ufoLib2.objects import Point

# glyph: (where the run begins, where it ends): "top" / "bottom" the inner
# extreme itself, "corner" the next corner beyond it (the terminal's inner
# corner), "bar" on to the far end of the bar's underside (G: the jaw's
# inner edge and its bracket into the bar)
RUNS = {
    "c": ("top", "bottom"),
    "c.sc": ("corner", "bottom"),
    "C": ("corner", "bottom"),
    "G": ("corner", "bar"),
    "g.sc": ("corner", "bar"),
}
LEVEL = 6  # degrees: how near level an extreme's handles stand
UPRIGHT = 8  # and how near upright (the italic c.sc's inner left turns -84
# to -89 at its node, its true extreme too near it to split)
CORNER = 10  # degrees: a turn at a node more than this is a corner
SPLIT = "italic_inside.split"  # (the name of an on-curve point split in)


def _dirs(pts, i):
    """the directions (degrees) into and out of on-curve point i"""
    n = len(pts)
    p, a, b = pts[i], pts[(i - 1) % n], pts[(i + 1) % n]
    return (math.degrees(math.atan2(p.y - a.y, p.x - a.x)),
            math.degrees(math.atan2(b.y - p.y, b.x - p.x)))


def _near(angle, target, tol):
    return abs((angle - target + 90) % 180 - 90) <= tol


def _level(pts, i):
    return all(_near(d, 0, LEVEL) for d in _dirs(pts, i))


def _upright(pts, i):
    return all(_near(d, 90, UPRIGHT) for d in _dirs(pts, i))


def _corner(pts, i):
    din, dout = _dirs(pts, i)
    return abs((dout - din + 180) % 360 - 180) > CORNER


def split_extremes(contour, min_t=0.02):
    """contour's curves split where they stand level or upright between
    their ends (in this frame: the Italic's nodes sit at the slanted
    letter's extremes, upright they fall between), the outline unchanged;
    the points split in are named SPLIT. Returns the curves as they were,
    by their ends: {(start, end): (handle, handle)}."""
    pts = contour.points
    n = len(pts)
    out, was = [], {}
    starts = [i for i, p in enumerate(pts) if p.type]
    for k, i in enumerate(starts):
        j = starts[(k + 1) % len(starts)]
        seg = [pts[(i + m) % n] for m in range((j - i) % n + 1)]
        out.append(seg[0])
        if seg[-1].type == "curve" and len(seg) == 4:
            p0, p1, p2, p3 = ((p.x, p.y) for p in seg)
            ts = set()
            for ax in (0, 1):
                a = -p0[ax] + 3 * p1[ax] - 3 * p2[ax] + p3[ax]
                b = 2 * (p0[ax] - 2 * p1[ax] + p2[ax])
                c = p1[ax] - p0[ax]
                ts |= {round(t, 6) for t in solveQuadratic(a, b, c) if min_t < t < 1 - min_t}
            if ts:
                was[(p0, p3)] = (p1, p2)
                parts = splitCubicAtT(p0, p1, p2, p3, *sorted(ts))
                for q in parts[:-1]:
                    out += [Point(*q[1]), Point(*q[2]), Point(*q[3], "curve", True, SPLIT)]
                out += [Point(*parts[-1][1]), Point(*parts[-1][2])]
                continue
        out += seg[1:-1]
    contour.points[:] = out
    return was


def _rejoin(points, was):
    """points with each curve split_extremes split, and left whole, joined
    again: between two of its own on-curve points only split ones"""
    on = [i for i, p in enumerate(points) if p.type]
    n = len(points)
    drop, put = set(), {}
    for k, i in enumerate(on):
        if points[i].name == SPLIT:
            continue
        m = 1
        while points[on[(k + m) % len(on)]].name == SPLIT and m < len(on):
            m += 1
        j = on[(k + m) % len(on)]
        key = ((points[i].x, points[i].y), (points[j].x, points[j].y))
        if m > 1 and key in was:
            inner = [(i + d) % n for d in range(1, (j - i) % n)]
            drop |= set(inner)
            put[inner[0]] = was[key]
    out = []
    for i, p in enumerate(points):
        if i in put:
            out += [Point(*put[i][0]), Point(*put[i][1])]
        if i not in drop:
            out.append(p)
    return out


def anchors(contour, start, end):
    """the run's anchor indices on contour, from its start to its end, and
    the step (+1 or -1 along the contour) that walks it so: its start; the
    inner top T; the inner left extreme L (upright, travelling against the
    outer left's way, the leftmost such within the middle 80 % of the
    height); the inner bottom B (T and B the first level on-curve points
    from L either way); for "bar" the bar's underside, its near end and
    its far end (the run's end)"""
    pts = contour.points
    n = len(pts)
    on = [i for i, p in enumerate(pts) if p.type]
    ys, xs = [p.y for p in pts], [p.x for p in pts]
    y0, y1, cx = min(ys), max(ys), (min(xs) + max(xs)) / 2
    mid = [i for i in on if _upright(pts, i) and pts[i].x < cx
           and y0 + 0.1 * (y1 - y0) < pts[i].y < y0 + 0.9 * (y1 - y0)]
    if len(mid) < 2:
        raise ValueError("italic_inside: no inner left extreme")
    outer = min(mid, key=lambda i: pts[i].x)
    way = math.copysign(1, _dirs(pts, outer)[1])
    inner = [i for i in mid if math.copysign(1, _dirs(pts, i)[1]) != way]
    if not inner:
        raise ValueError("italic_inside: no inner left extreme")
    L = min(inner, key=lambda i: pts[i].x)

    def walk(i, step, test):
        for k in range(1, n):
            j = (i + step * k) % n
            if pts[j].type and test(j, step):
                return j
        raise ValueError("italic_inside: run end not found")

    ends = [walk(L, s, lambda j, _: _level(pts, j)) for s in (1, -1)]
    T, B = sorted(ends, key=lambda j: -pts[j].y)
    if not pts[T].y > pts[L].y > pts[B].y:
        raise ValueError("italic_inside: extremes out of order")
    up = 1 if T == ends[0] else -1  # the step from L towards T
    S = T if start == "top" else walk(T, up, lambda j, _: _corner(pts, j))
    keys = [S, T, L, B]
    if end == "corner":
        keys.append(walk(B, -up, lambda j, _: _corner(pts, j)))
    elif end == "bar":
        def underside(j, step):
            # the point walked just before j: a level line from it to j
            before = (j - step) % n
            end_ = j if step == 1 else before  # where the contour stores the segment
            return (pts[before].type and pts[end_].type == "line"
                    and abs(pts[j].y - pts[before].y) <= 2 and abs(pts[j].x - pts[before].x) > 20)
        E = walk(B, -up, underside)
        keys += [(E + up) % n, E]
    keys = [k for m, k in enumerate(keys) if m == 0 or k != keys[m - 1]]
    return keys, -up


def _forward(n, i0, i1):
    return [(i0 + k) % n for k in range((i1 - i0) % n + 1)]


def replace(wide, bold, start, end):
    """bold (a one-contour glyph, upright frame; changed in place) with the
    run facing its bowl redrawn from wide's (the Italic's, same frame).
    Returns how many points the run had before and after."""
    if len(wide.contours) != 1 or len(bold.contours) != 1:
        raise ValueError("italic_inside: one contour each")
    wc, bc = wide.contours[0], bold.contours[0]
    split_extremes(wc)
    was = split_extremes(bc)
    (wk, wstep), (bk, bstep) = anchors(wc, start, end), anchors(bc, start, end)
    if wstep != bstep or len(wk) != len(bk):
        raise ValueError("italic_inside: the runs do not match")
    if wstep == -1:  # both walked in the contour's own order
        wk, bk = wk[::-1], bk[::-1]
    wpts, bpts = wc.points, bc.points
    maps = []
    for a, b, a2, b2 in zip(wk, wk[1:], bk, bk[1:]):
        p, q, p2, q2 = wpts[a], wpts[b], bpts[a2], bpts[b2]
        sx = (q2.x - p2.x) / (q.x - p.x) if abs(q.x - p.x) >= 2 else 1.0
        sy = (q2.y - p2.y) / (q.y - p.y) if abs(q.y - p.y) >= 2 else 1.0
        maps.append((sx, p2.x - sx * p.x, sy, p2.y - sy * p.y))
    run = _forward(len(wpts), wk[0], wk[-1])
    new, piece = [], 0
    for i in run[1:-1]:
        p = wpts[i]
        if i in wk:  # an anchor: exactly onto the stroked run's
            b = bpts[bk[wk.index(i)]]
            new.append(Point(b.x, b.y, p.type, p.smooth))
            piece += 1
        else:
            sx, tx, sy, ty = maps[piece]
            new.append(Point(sx * p.x + tx, sy * p.y + ty, p.type, p.smooth))
    # every node on the run that turns less than a corner made smooth: an
    # anchor's two sides scaled apart turn its handles a little off one line
    # (the italic c.sc's inner left stands up to 6 degrees off upright), and
    # the Italic's own nodes there are not all flagged smooth — both handles
    # on their mean direction, their lengths kept
    for k, q in enumerate(new):
        if not q.type or k == 0 or k + 1 == len(new):
            continue
        a, b = new[k - 1], new[k + 1]
        if a.type and b.type:
            continue
        if a.type or b.type:
            # a straight piece into a curve (G's jaw): the handle on the line
            la, lb = math.hypot(q.x - a.x, q.y - a.y), math.hypot(b.x - q.x, b.y - q.y)
            if not la or not lb:
                continue
            turn = math.degrees(math.atan2(b.y - q.y, b.x - q.x) - math.atan2(q.y - a.y, q.x - a.x))
            if abs((turn + 180) % 360 - 180) > CORNER:
                continue
            if a.type:  # the line arrives: the handle out runs on along it
                new[k + 1] = Point(q.x + (q.x - a.x) / la * lb, q.y + (q.y - a.y) / la * lb)
            else:  # the line leaves: the handle in runs along it backwards
                new[k - 1] = Point(q.x - (b.x - q.x) / lb * la, q.y - (b.y - q.y) / lb * la)
            continue
        la, lb = math.hypot(q.x - a.x, q.y - a.y), math.hypot(b.x - q.x, b.y - q.y)
        if not la or not lb:
            continue
        turn = math.degrees(math.atan2(b.y - q.y, b.x - q.x) - math.atan2(q.y - a.y, q.x - a.x))
        if abs((turn + 180) % 360 - 180) > CORNER:
            continue
        dx, dy = (q.x - a.x) / la + (b.x - q.x) / lb, (q.y - a.y) / la + (b.y - q.y) / lb
        d = math.hypot(dx, dy)
        dx, dy = dx / d, dy / d
        new[k - 1] = Point(q.x - dx * la, q.y - dy * la)
        new[k + 1] = Point(q.x + dx * lb, q.y + dy * lb)
        new[k] = Point(q.x, q.y, q.type, True)
    old = len(_forward(len(bpts), bk[0], bk[-1])) - 2
    keep = [bpts[i] for i in _forward(len(bpts), bk[-1], bk[0])]  # its end round to its start
    last = keep[0]
    # (the run's last segment arrives as the Italic's does)
    keep[0] = Point(last.x, last.y, wpts[wk[-1]].type, last.smooth, last.name)
    points = _rejoin(keep + new, was)
    bc.points[:] = [Point(round(p.x), round(p.y), p.type, p.smooth) for p in points]
    return old, len(new)
