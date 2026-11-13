"""Ʌ's thin leg straight down to its foot, in the italics.

Ʌ is V turned (derive.py). V's thin arm flares into its top serif over 300
units, one long curve on its inside; turned, that flare is the left leg's
foot, and the leg's inner edge leaves its line a fifth of the way up and
bows 60 units into the counter ("a line bending out in the middle, not
bending into the foot serif", on the sheet of 2026-11-12). Λ's own leg runs
straight to 209 units above its foot and turns into it there: Ʌ's inner
edge is drawn so, the line run on to that height and Λ's two curves set on
its end (the Italic Λ's, in units; the same in the Bold Italic).

A finishing pass (finalization.py) of both italics; a glyph marked drawn,
or one whose leg is not the line and two curves read here, is left.
"""

RISE = 211  # the line's end above the foot's top (Λ: 271 - 62, and the foot 7 higher here)
# Λ's two curves from the line's end: handles and nodes, as offsets from it;
# the last two lie on the foot's top
TURN = ((-32, -46), (-55, -81), (-43, -131))
FOOT = ((-28, -195), 47, 84)


def leg(glyph):
    """(line end, node between the curves, foot, step) of the thin leg's
    inner edge: indices, and the direction they run in (1 or -1: the Bold
    Italic's contour runs the other way); or None"""
    pts = glyph.contours[0].points
    n = len(pts)
    for s in (1, -1):
        for i in range(n):
            p, q, r = pts[i], pts[(i + 3 * s) % n], pts[(i + 6 * s) % n]
            prev, nxt = pts[(i - s) % n], pts[(i + 7 * s) % n]
            if not (p.type and q.type and r.type and prev.type and nxt.type
                    and nxt.y == r.y and r.y < 200 < p.y < 600):
                continue
            if any(pts[(i + k * s) % n].type for k in (1, 2, 4, 5)):
                continue
            # the thin diagonal, coming down leftwards from the apex's inside
            if prev.y - p.y > 400 and prev.x > p.x and q.x < p.x and r.x > q.x:
                return i, (i + 3 * s) % n, (i + 6 * s) % n, s
    return None


def finish(font):
    from drawn import is_drawn

    if font.info.styleName not in ("Italic", "Bold Italic") or "uni0245" not in font:
        return {}
    glyph = font["uni0245"]
    if is_drawn(glyph) or len(glyph.contours) != 1:
        return {}
    found = leg(glyph)
    if found is None:
        return {}
    pts = glyph.contours[0].points
    n = len(pts)
    i, j, k, s = found
    p, prev, top = pts[i], pts[(i - s) % n], pts[k].y
    if p.y - top <= RISE + 20:
        return {}  # straight far enough already
    y = top + RISE
    x = p.x + (prev.x - p.x) * (y - p.y) / (prev.y - p.y)
    was = (p.x, p.y)
    p.x, p.y = round(x), round(y)
    for step, (dx, dy) in zip((1, 2, 3), TURN):
        q = pts[(i + step * s) % n]
        q.x, q.y = round(x + dx), round(y + dy)
    pts[j].smooth = True
    (dx, dy), d1, d2 = FOOT
    q = pts[(j + s) % n]
    q.x, q.y = round(x + dx), max(round(y + dy), top + 8)
    q = pts[(j + 2 * s) % n]
    q.x, q.y = round(x + d1), top
    pts[k].x = min(round(x + d2), pts[(k + s) % n].x - 20)
    return {"uni0245": was}
