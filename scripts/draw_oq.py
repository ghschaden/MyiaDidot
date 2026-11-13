"""The Italic's O and Q drawn, not fitted (docs/claude/redraw.md, "O and Q
drawn").

Old Standard's italic O holds its flanks with two curves a side inside;
redraw.py, fitting one, took 3 units off the round stem, and O is the
measure of every enlarged letter. Here O is drawn on the Regular's
structure, four extremes a contour, each curve the best one that passes
through the old outline at mid height: both round stems, the counter's
width there and the hairlines at the letter's middle are today's to a
sixth of a unit, the nodes (so bounds,
overshoots, hairlines) are today's, and what moves is the flanks away from
mid height.

Q is built from that O: its bowl is O's curves, cut where the tail's
corners meet them; the tail and its loop are redraw.py's candidate for
today's Q.

    .venv/bin/python -I scripts/draw_oq.py sources/MyiaDidot-Italic.ufo \
        build/redraw/OQ-drawn.ufo [--install --date DATE --review SHEET]
"""

import argparse
import copy
import sys
from pathlib import Path

import numpy as np
import ufoLib2
from ufoLib2.objects import Contour, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redraw  # noqa: E402
from drawn import is_drawn  # noqa: E402

STEM = 0.15  # units the outline may leave the old one by where the strokes are measured
TS = np.linspace(0, 1, 201)


def cubic(ctrl, ts=TS):
    p = np.asarray(ctrl, float)
    t = np.asarray(ts, float)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t**2 * p[2] + t**3 * p[3]


def flat(segs):
    """the segments as one polyline"""
    return np.concatenate([cubic(s) if len(s) == 4 else np.array(s, float) for s in segs])


def to_line(pts, line):
    """each point's distance to a polyline"""
    a, b = line[:-1], line[1:]
    ab = b - a
    t = np.einsum("pld,ld->pl", pts[:, None] - a[None], ab) / np.maximum(np.einsum("ld,ld->l", ab, ab), 1e-9)
    foot = a[None] + np.clip(t, 0, 1)[..., None] * ab[None]
    return np.sqrt(((pts[:, None] - foot) ** 2).sum(-1)).min(1)


def apart(a, b):
    """the greater of the two one-sided distances between polylines"""
    return float(max(to_line(a, b).max(), to_line(b, a).max()))


def x_at(line, y):
    """where a polyline that runs one way in y crosses the height y"""
    ys, xs = line[:, 1], line[:, 0]
    if ys[0] > ys[-1]:
        ys, xs = ys[::-1], xs[::-1]
    return float(np.interp(y, ys, xs))


def arc(p0, p3, target, mid, centre):
    """the cubic from extreme p0 to extreme p3 (one upright, one level)
    nearest the target polyline, through it where it crosses the height
    mid (the round stem) and the abscissa centre (the hairline)"""
    p0, p3 = np.array(p0, float), np.array(p3, float)
    d = p3 - p0
    upright_first = abs(target[1][0] - p0[0]) < abs(target[1][1] - p0[1])
    u0 = np.array([0, np.sign(d[1])]) if upright_first else np.array([np.sign(d[0]), 0])
    u3 = np.array([np.sign(d[0]), 0]) if upright_first else np.array([0, np.sign(d[1])])
    amax, bmax = abs(d @ u0), abs(d @ u3)
    flip = target[:, ::-1]
    stem = x_at(target, mid) if min(p0[1], p3[1]) < mid < max(p0[1], p3[1]) else None
    hair = x_at(flip, centre) if min(p0[0], p3[0]) < centre < max(p0[0], p3[0]) else None

    def cost(a, b):
        line = cubic([p0, p0 + a * u0, p3 - b * u3, p3], TS[::2])
        off = max(abs(x_at(line, mid) - stem) if stem is not None else 0.0,
                  abs(x_at(line[:, ::-1], centre) - hair) if hair is not None else 0.0)
        return apart(target[::2], line) + 50 * max(0.0, off - STEM), off

    best = None
    grid = [(a, b) for a in np.arange(16, amax, 32) for b in np.arange(16, bmax, 32)]
    for step in (8, 2, 1, 0):
        for a, b in grid:
            c = cost(a, b)
            if best is None or c[0] < best[0][0]:
                best = (c, a, b)
        _, a0, b0 = best
        grid = [(a, b) for a in np.arange(max(1, a0 - 4 * step), min(amax, a0 + 4 * step + 1), max(step, 1))
                for b in np.arange(max(1, b0 - 4 * step), min(bmax, b0 + 4 * step + 1), max(step, 1))]
    (c, off), a, b = best
    return [tuple(p0), tuple(p0 + a * u0), tuple(p3 - b * u3), tuple(p3)], c, off


def stretch(segs, start, end):
    """the segments from the node start to the node end, in order"""
    n = len(segs)
    i = next(k for k, s in enumerate(segs) if tuple(s[0]) == tuple(start))
    out = []
    while True:
        out.append([tuple(map(float, p)) for p in segs[i % n]])
        if tuple(out[-1][-1]) == tuple(map(float, end)):
            return out
        i += 1


def draw_o(glyph, notes):
    """O's two contours as four arcs each between today's extremes"""
    b = redraw.bounds(glyph)
    mid, centre = (b[1] + b[3]) / 2, (b[0] + b[2]) / 2
    new = []
    for c in glyph.contours:
        segs = redraw.segments(c)
        ext = [tuple(map(float, s[0])) for s in segs if abs(s[1][0] - s[0][0]) < 0.5 or abs(s[1][1] - s[0][1]) < 0.5]
        ext = [e for e in ext if any(tuple(map(float, s[-1])) == e and (abs(s[-2][0] - e[0]) < 0.5 or abs(s[-2][1] - e[1]) < 0.5) for s in segs)]
        arcs = []
        for p0, p3 in zip(ext, ext[1:] + ext[:1]):
            a, dev, off = arc(p0, p3, flat(stretch(segs, p0, p3)), mid, centre)
            notes.append(f"O {p0[0]:.0f},{p0[1]:.0f} -> {p3[0]:.0f},{p3[1]:.0f}: {dev:.2f} off, {off:.2f} at the stem or hairline")
            arcs.append(a)
        new.append(arcs)
    return new


def split(ctrl, t):
    p = np.asarray(ctrl, float)
    a, b, c = p[0] + t * (p[1] - p[0]), p[1] + t * (p[2] - p[1]), p[2] + t * (p[3] - p[2])
    d, e = a + t * (b - a), b + t * (c - b)
    f = d + t * (e - d)
    return [p[0], a, d, f], [f, e, c, p[3]]


def whole(seg):
    return [tuple(float(round(v)) for v in p) for p in seg]


def nearest_t(ctrl, p, x=None):
    """the parameter of the curve's point nearest p, or at the abscissa x"""
    ts = np.linspace(0, 1, 4001)
    pts = cubic(ctrl, ts)
    if x is not None:
        return float(ts[np.argmin(np.abs(pts[:, 0] - x))])
    return float(ts[np.argmin(((pts - np.array(p, float)) ** 2).sum(1))])


def tail(segs, start, end, p0, p3):
    """the candidate's segments from start to end, their ends put on O"""
    out = stretch(segs, start, end)
    out[0][0], out[-1][-1] = p0, p3
    return out


def draw_q(cand, o, notes):
    """Q: O's arcs cut at the tail's corners, the tail as the candidate has it"""
    (ia0, ia1, ia2, ia3), (oa0, oa1, oa2, oa3) = o  # as O's contours lie: the counter first
    inner, outer, loop = (redraw.segments(c) for c in cand.contours)

    def cut(a, p, x=None):
        t = nearest_t(a, p, x)
        first, second = split(a, t)
        q = whole([first[3]])[0]
        notes.append(f"Q's corner {p[0]},{p[1]} on O at {q[0]:.0f},{q[1]:.0f}")
        first, second = whole(first), whole(second)
        return first, second, q

    first, _, p1 = cut(ia0, (463, 74))
    _, second, p2 = cut(ia1, (798, 87))
    c0 = [first] + tail(inner, (463, 74), (798, 87), p1, p2) + [second, ia2, ia3]
    first, _, pa = cut(oa2, (800, 10), x=800)
    _, second, pb = cut(oa2, (651, -29))
    c1 = [oa0, oa1, first] + tail(outer, (800, 10), (651, -29), pa, pb) + [second, oa3]
    return [c0, c1, [[tuple(map(float, p)) for p in s] for s in loop]], (p1, p2, pa, pb)


def contours(shape, smooth):
    """point contours of [[segment]]; a node is smooth unless smooth says not"""
    out = []
    for segs in shape:
        pts = []
        for k, s in enumerate(segs):
            kind = "curve" if len(segs[k - 1]) == 4 else "line"
            pts.append(Point(int(s[0][0]), int(s[0][1]), kind, smooth=smooth.get(tuple(map(float, s[0])), True)))
            pts += [Point(int(x), int(y)) for x, y in s[1:-1]]
        out.append(Contour(pts))
    return out


def put(glyph, shape, smooth):
    new = copy.deepcopy(glyph)
    new.clearContours()
    for c in contours(shape, smooth):
        new.appendContour(c)
    return new


def measures(font, name, old):
    """what the gate asks of a drawn glyph, as lines"""
    from derive import strokes
    from quality.checks import construction

    g = font[name]
    one = ufoLib2.Font()
    one.info.unitsPerEm, one.info.italicAngle = font.info.unitsPerEm, font.info.italicAngle
    one.layers.defaultLayer.insertGlyph(old, name)
    (_, s0, h0), (_, s1, h1) = strokes(one, name), strokes(font, name)
    dev, at = 0.0, None
    for a, b in zip(old.contours, g.contours):
        a, b = flat(redraw.segments(a)), flat(redraw.segments(b))
        d = to_line(b, a)
        if d.max() > dev:
            dev, at = float(d.max()), b[d.argmax()]
    jumps, smooth = [], {(p.x, p.y) for c in g.contours for p in c.points if p.smooth}
    for c in g.contours:
        segs = [np.array(s, float) for s in redraw.segments(c)]
        for k, s in enumerate(segs):
            if len(s) == 4 and len(segs[k - 1]) == 4 and (int(s[0][0]), int(s[0][1])) in smooth:
                jumps.append((round(float(redraw.curvature_jump(redraw.curvature(segs[k - 1], 1), redraw.curvature(s, 0))), 2), f"{s[0][0]:.0f},{s[0][1]:.0f}"))
    b0, b1 = redraw.bounds(old), redraw.bounds(g)
    return [
        f"{name}: nodes {redraw.node_count(old)} -> {redraw.node_count(g)}, {dev:.2f} units from today's at {at[0]:.0f},{at[1]:.0f}",
        f"  round stem {s0:.2f} -> {s1:.2f}, top hairline {h0:.2f} -> {h1:.2f}",
        f"  ink area {100 * (redraw.area(g) / redraw.area(old) - 1):+.2f} %, bounds moved {max(abs(a - b) for a, b in zip(b0, b1)):.2f}",
        f"  worst curvature jumps {sorted(jumps, reverse=True)[:3]}",
        f"  construction {[list(f) for f in construction(g)]}, bent back {redraw.bent_back(g)}",
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--install", action="store_true", help="after the review: into SRC.ufo, marked drawn")
    ap.add_argument("--date")
    ap.add_argument("--review")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review")
    font = ufoLib2.Font.open(a.src)
    if is_drawn(font["O"]) or is_drawn(font["Q"]):
        sys.exit("O or Q is drawn already: this builds them from Old Standard's outlines only")
    notes = []
    o = draw_o(font["O"], notes)
    cand, _ = redraw.redraw(font["Q"], redraw.TOL, redraw.spec_for(a.src).get("Q"))
    smooth = {(float(p.x), float(p.y)): bool(p.smooth) for c in cand.contours for p in c.points if p.type}
    q, cuts = draw_q(cand, o, notes)
    corners = dict.fromkeys(cuts, False)
    out = ufoLib2.Font()
    for k in ("unitsPerEm", "italicAngle", "xHeight", "capHeight", "ascender", "descender"):
        setattr(out.info, k, getattr(font.info, k))
    out.layers.defaultLayer.insertGlyph(put(font["O"], o, {}), "O")
    out.layers.defaultLayer.insertGlyph(put(font["Q"], q, {**smooth, **corners}), "Q")
    print("\n".join(notes))
    for name in "OQ":
        print("\n".join(measures(out, name, font[name])))
    out.save(a.out, overwrite=True)
    if a.install:
        for name in "OQ":
            redraw.install(font, name, out[name], a.date, a.review, {"tol": 0})
            font[name].lib[redraw.KEY]["by"] = "scripts/draw_oq.py"
        font.save()


if __name__ == "__main__":
    main()
