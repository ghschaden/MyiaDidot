"""Finish the reviewed joins of the italic derived letters at their final size.

The recipes and Boolean joins are rounded before this pass. Work only in
the reviewed regions: align the short handles at shallow joins, ease the
two straight edges at ƈ's shoulder, and split curves at missing extrema.
The base letters, advances, anchors and terminal sizes stay as drawn.
Called before clearance kerning; rounds and cleans these letters first,
using the same rounding policy as their generator's final write.
"""

import math

from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT
from ufoLib2.objects import Point

# Boxes in the upright frame, sheared about the x-height's midpoint (442),
# after spacing. These cover the added pieces and their joins, not the
# inherited bodies. They apply to both weights.
REGIONS = {
    "uni0188": (450, 800, 1000, 1150),   # ƈ: c's shoulder and the hook entrance
    "uni0291": (500, -50, 1100, 400),    # ʑ: the lower loop and tail
    "uni026E": (450, 650, 850, 750),     # ɮ: the shoulder beside l
    "uni0284": (300, 1000, 1100, 1500),  # ʄ: the top hook's extrema
    "uni0496": (1100, -300, 1900, 230),  # Җ: the right leg and curl
    "uni0497": (750, -300, 1400, 230),   # җ: the right leg and curl
    "uni049A": (500, -300, 1300, 230),   # Қ: the right leg and curl
    "uni049B": (400, -300, 1100, 230),   # қ: the right leg and curl
}


def _turn(a, p, b):
    u, v = (p.x - a.x, p.y - a.y), (b.x - p.x, b.y - p.y)
    return abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))


def _fair_lines(points, inside):
    """Ease a shallow line/line corner over at most 20 units on each side."""
    for i in range(len(points) - 1, -1, -1):
        a, p, b = points[i - 1], points[i], points[(i + 1) % len(points)]
        if not (p.type and a.type and b.type and inside(p.x, p.y)):
            continue
        if not 1 < _turn(a, p, b) < 8:
            continue
        la, lb = math.hypot(p.x - a.x, p.y - a.y), math.hypot(b.x - p.x, b.y - p.y)
        if min(la, lb) < 20:
            continue
        radius = min(20, la / 3, lb / 3)
        u, v = ((p.x - a.x) / la, (p.y - a.y) / la), ((b.x - p.x) / lb, (b.y - p.y) / lb)
        entry = (p.x - radius * u[0], p.y - radius * u[1])
        exit_ = (p.x + radius * v[0], p.y + radius * v[1])
        points[i:i + 1] = [
            Point(*entry, type="line", smooth=True),
            Point(entry[0] + 2 * radius * u[0] / 3, entry[1] + 2 * radius * u[1] / 3),
            Point(exit_[0] - 2 * radius * v[0] / 3, exit_[1] - 2 * radius * v[1] / 3),
            Point(*exit_, type="curve", smooth=True),
        ]


def _align_handles(points, inside):
    """Keep nodes and handle lengths; align shallow joins to one tangent.

    Straight edges and horizontal/vertical extreme tangents determine the
    direction. Otherwise favor the longer handle, whose angle is less
    sensitive to rounding. Sharp corners and short handles are left alone.
    """
    for i, p in enumerate(points):
        if not p.type or not inside(p.x, p.y):
            continue
        a, b = points[i - 1], points[(i + 1) % len(points)]
        la, lb = math.hypot(p.x - a.x, p.y - a.y), math.hypot(b.x - p.x, b.y - p.y)
        if min(la, lb) < 10 or not 1 < _turn(a, p, b) < 8 or (a.type and b.type):
            continue
        u, v = ((p.x - a.x) / la, (p.y - a.y) / la), ((b.x - p.x) / lb, (b.y - p.y) / lb)
        if a.type:
            direction = u
        elif b.type:
            direction = v
        elif a.x == p.x or b.x == p.x:
            direction = (0, 1 if u[1] + v[1] > 0 else -1)
        elif a.y == p.y or b.y == p.y:
            direction = (1 if u[0] + v[0] > 0 else -1, 0)
        else:
            dx, dy = u[0] * la**2 + v[0] * lb**2, u[1] * la**2 + v[1] * lb**2
            length = math.hypot(dx, dy)
            direction = (dx / length, dy / length)
        dx, dy = direction
        if not a.type:
            a.x, a.y = p.x - la * dx, p.y - la * dy
        if not b.type:
            b.x, b.y = p.x + lb * dx, p.y + lb * dy
        p.smooth = True


def _seat_ka_leg(points):
    """Seat light қ's outer leg join on its tangent at the recipe's cut.

    The cut at y=200 leaves the outer node two units inside that tangent.
    Rotating the preceding handle inward thins the leg; moving just this node
    outward retains the base's weight and the descender's inner edge.
    """
    joins = [i for i, p in enumerate(points) if p.type and p.y == 200]
    if not joins:
        return
    i = max(joins, key=lambda k: points[k].x)
    a, p, b = points[i - 1], points[i], points[(i + 1) % len(points)]
    if a.type or not b.type or not 1 < _turn(a, p, b) < 8:
        return
    for dx in (1, 2):
        candidate = Point(p.x + dx, p.y)
        if _turn(a, candidate, b) < 1:
            p.x, p.smooth = candidate.x, True
            break


def _add_extrema(points, inside):
    """Split cubics in the final slanted frame, preserving existing metadata.

    Only extrema in the reviewed region that extend over two units past the
    ends need splitting. Ignore roots very near an endpoint to avoid making
    tiny segments which collapse when rounded to the font's integer grid.
    """
    count = len(points)
    oncurve = [i for i, p in enumerate(points) if p.type]
    result = []
    for k, i in enumerate(oncurve):
        j = oncurve[(k + 1) % len(oncurve)]
        offcurve = [points[(i + m) % count] for m in range(1, (j - i) % count or count)]
        result.append(points[i])
        if len(offcurve) != 2:
            result.extend(offcurve)
            continue
        curve = [(p.x, p.y) for p in (points[i], *offcurve, points[j])]
        roots = set()
        for axis in (0, 1):
            a, b, c, d = (p[axis] for p in curve)
            for t in solveQuadratic(3 * (-a + 3 * b - 3 * c + d), 6 * (a - 2 * b + c), 3 * (b - a)):
                if not 0.02 < t < 0.98:
                    continue
                u = 1 - t
                p = tuple(u**3 * curve[0][q] + 3 * u * u * t * curve[1][q]
                          + 3 * u * t * t * curve[2][q] + t**3 * curve[3][q] for q in (0, 1))
                if inside(*p) and max(min(a, d) - p[axis], p[axis] - max(a, d)) > 2:
                    roots.add(t)
        if not roots:
            result.extend(offcurve)
            continue
        segments = splitCubicAtT(*curve, *sorted(roots))
        for k, segment in enumerate(segments):
            result.extend((Point(*segment[1]), Point(*segment[2])))
            if k < len(segments) - 1:
                result.append(Point(*segment[3], type="curve", smooth=True))
    points[:] = result


def finish(font, skip=(), smooth=True):
    """Round, clean and finish the eight reviewed derived letters.

    Callers exclude kept/reviewed glyphs. Drawn exceptions and other glyphs
    are never processed. Widths, anchors and glyph metadata are preserved.
    """
    from glyph_lint import fix
    from make_bold import round_smoothly

    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    names = [name for name in REGIONS if name not in skip and name in font
             and font[name].lib.get("org.myiadidot.italicSource") == "derived"]
    if not names:
        return
    for name in names:
        for contour in font[name].contours:
            if smooth:
                round_smoothly(contour.points)
            else:
                for point in contour.points:
                    point.x, point.y = round(point.x), round(point.y)
    fix(font, names)
    for name in names:
        box = REGIONS[name]

        def inside(x, y, box=box):
            x -= slant * (y - 442)
            return box[0] <= x <= box[2] and box[1] <= y <= box[3]

        for contour in font[name].contours:
            if name == "uni049B" and (font.info.openTypeOS2WeightClass or 400) < 600:
                _seat_ka_leg(contour.points)
            # Rounding a repaired handle can reveal a small extreme. Settle
            # that here so a second finish does not add another point.
            for _ in range(4):
                before = [(p.x, p.y, p.type, p.smooth) for p in contour.points]
                _fair_lines(contour.points, inside)
                _align_handles(contour.points, inside)
                _add_extrema(contour.points, inside)
                round_smoothly(contour.points)
                if before == [(p.x, p.y, p.type, p.smooth) for p in contour.points]:
                    break
            else:
                raise ValueError(f"{name}: contour finishing did not settle")
