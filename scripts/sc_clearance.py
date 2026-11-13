"""The Bold Italic's small caps whose parts close up when stroked: ы.sc, psi.sc.

Their Italic letters stand clear (ы.sc's bowl 96 units from its stick,
psi.sc's top serif 50 and 38 from its arms); with the Bold Italic's weight
on both sides the white went: ы.sc's bowl ran into the stick (8 units
apart, then none), psi.sc's serif touched the right arm and closed the
white between stem and arm into a counter, 14 units from the left one
("the two parts touch; should not; same for psi.sc: arms touch the stem",
on the sheet of 2026-11-12). Each gets the white its capital has, at the
small caps' proportion (the Bold Italic's Ы 70, Ψ 83 and 86; the Italic's
small caps stand at 0.62 of their capitals').

- ы.sc: the stick moved right, the advance with it.
- psi.sc: the top serif shortened at both ends; on the right the closed
  counter is opened again, the outline taken along the serif's underside,
  down the stem and up the arm's own left edge.

Run as a finishing pass (finalization.py), on the generated outlines; a
glyph marked drawn, or one that has not the structure read here, is left.
"""

import math

GAP = 45  # units of white, across, in the upright frame


def _rows(font, contours, slope, y0, y1, step=8):
    """{y: [(x0, x1)]} of the contours' ink, upright, between two heights"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
    import pathops
    from derived import Outline

    path = pathops.Path()
    pen = path.getPen()
    for c in contours:
        c.draw(pen)
    out = Outline(None, None, (1, 0, -slope, 1, 0, 0), path=path)
    return {y: out.spans(y + 0.37) for y in range(int(y0), int(y1), step)}


def _drawn(glyph):
    from drawn import is_drawn

    return is_drawn(glyph)


def yeru(font, slope):
    """ы.sc's stick GAP from its bowl; returns the units moved"""
    glyph = font["uni044B.sc"] if "uni044B.sc" in font else None
    if glyph is None or _drawn(glyph) or len(glyph.contours) != 3:
        return 0

    def left(c):
        return min(p.x - slope * p.y for p in c.points)

    stick = max(glyph.contours, key=left)
    rest = [c for c in glyph.contours if c is not stick]
    ys = [p.y for c in rest for p in c.points]
    lo, hi = min(ys) + 100, max(ys) - 100  # between the serifs
    bowl, stem = _rows(font, rest, slope, lo, hi), _rows(font, [stick], slope, lo, hi)
    gaps = [stem[y][0][0] - bowl[y][-1][1] for y in bowl if bowl[y] and stem[y]]
    if not gaps:
        return 0
    move = round(GAP - min(gaps))
    if move <= 0:
        return 0
    x0 = min(p.x for p in stick.points)
    for p in stick.points:
        p.x += move
    for a in glyph.anchors:
        if a.x >= x0:
            a.x += move
    glyph.width += move
    return move


def psi(font, slope):
    """psi.sc's top serif GAP from both arms; returns (left, right) units
    taken off, or None where the outline is not the one read here"""
    from ufoLib2.objects import Point

    glyph = font["psi.sc"] if "psi.sc" in font else None
    if glyph is None or _drawn(glyph) or len(glyph.contours) != 2:
        return None
    outer, counter = sorted(glyph.contours, key=lambda c: -len(c.points))
    pts, n = outer.points, len(outer.points)
    # the serif's top: the longest level line in the upper fifth
    top = max(p.y for p in pts)
    tops = [i for i in range(n) if pts[i].type == "line" and pts[i - 1].type == "line"
            and pts[i].y == pts[i - 1].y > 0.8 * top]
    if not tops:
        return None
    i = max(tops, key=lambda k: abs(pts[k].x - pts[k - 1].x))
    a, b = i - 1, i  # its left and right ends
    if pts[a].x > pts[b].x:
        return None
    foot, touch = pts[a - 1], pts[(b + 1) % n]  # the left end's foot; where the right end meets the arm
    first = pts[(b + 2) % n]
    if foot.type != "line" or touch.type != "line" or first.type is not None:
        return None
    # the counter: its two highest nodes are the serif's underside, from the
    # arm (c1) back to the stem (c0), the line that closes it
    cp, m = counter.points, len(counter.points)
    under = sorted((k for k in range(m) if cp[k].type), key=lambda k: -cp[k].y)[:2]
    c0, c1 = sorted(under, key=lambda k: cp[k].x)
    if cp[c0].y != cp[c1].y or cp[c0].y != foot.y or (c1 + 1) % m != c0 or cp[c0].type != "line":
        return None
    lean = (pts[a].x - foot.x) / (pts[a].y - foot.y)  # the left end's, for both
    # left: the serif's end against the arm's ink beside it
    rows = _rows(font, [outer], slope, foot.y + 6, pts[a].y - 6, step=6)
    whites = []
    for y, spans in rows.items():
        x = foot.x + lean * (y - foot.y) - slope * y  # the end's edge at y, upright
        k = next((j for j, s in enumerate(spans) if abs(s[0] - x) < 3), None)
        if k:
            whites.append(x - spans[k - 1][1])
    off_left = max(0, round(GAP - min(whites))) if whites else 0
    for p in (foot, pts[a]):
        p.x += off_left
    # right: the end GAP from the arm's edge at the underside
    end = cp[c1].x - GAP
    off_right = round(pts[b].x - (end + lean * (pts[b].y - cp[c1].y)))
    if off_right <= 0:
        return None
    pts[b].x -= off_right
    walk = [cp[(c0 + k) % m] for k in range(m)]  # c0 ... c1
    walk[-1].smooth = True
    # the arm's curve from its own edge: the first handle on the edge's
    # tangent, at the old handle's height
    tx, ty = walk[-1].x - walk[-2].x, walk[-1].y - walk[-2].y
    if ty <= 0:
        return None
    handle = Point(round(walk[-1].x + tx / ty * (first.y - walk[-1].y)), first.y)
    new = [Point(round(end), cp[c1].y, "line")] + [Point(p.x, p.y, p.type, smooth=p.smooth) for p in walk] + [handle]
    k = (b + 1) % n
    if k + 2 > n:  # the contour's start falls in the piece replaced
        return None
    outer.points[k:k + 2] = new
    glyph.contours.remove(counter)
    return off_left, off_right


def finish(font):
    if font.info.styleName != "Bold Italic":
        return {}
    slope = math.tan(math.radians(-(font.info.italicAngle or 0)))
    done = {}
    moved = yeru(font, slope)
    if moved:
        done["uni044B.sc"] = moved
    cut = psi(font, slope)
    if cut:
        done["psi.sc"] = cut
    return done
