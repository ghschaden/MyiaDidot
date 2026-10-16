"""Draft ẞ (U+1E9E) from ß, as a starting point for design.

    python scripts/draft_capital_sharp_s.py UFO

Copies the outline of germandbls into a new glyph uni1E9E, scales it
vertically so the ascender (1496, the top of l and h) meets the cap height
(1434), and thickens the vertical stems from the lowercase 164 to the capital
208 by moving each point sideways in proportion to how far its outline faces
left or right: thick vertical strokes gain the full 44 units, the horizontal
hairlines nothing. Then the bowls and the ball are moved WIDEN to the right
(the arch and the waist hairline stretch) and the ball BALL, so the
letter has a capital's width and the ball stands clear of the stem. The glyph is marked as a draft
(lib DRAFT_KEY) for review.
"""

import math
import sys

import ufoLib2

ASCENDER, CAP_HEIGHT = 1496, 1434
LC_STEM, UC_STEM = 164, 208
WIDEN = 140
BALL = 60  # the ball low down moves less: ß's own already stands off the stem
STEM_X = 220  # where the stem's left edge is put before widening
DRAFT_KEY = "org.myiadidot.draft"


def normals(points):
    """Outward-ish unit normals at each point of a closed contour (x part only matters)."""
    n = len(points)
    out = []
    for i in range(n):
        (x0, y0), (x1, y1) = points[i - 1], points[(i + 1) % n]
        tx, ty = x1 - x0, y1 - y0
        length = math.hypot(tx, ty) or 1.0
        out.append((ty / length, -tx / length))  # right-hand normal
    return out


def embolden_x(glyph, amount):
    """Thicken vertical strokes by `amount`, keeping horizontal ones."""
    for contour in glyph.contours:
        pts = [(p.x, p.y) for p in contour.points]
        # orientation: the right-hand normal points outward on a clockwise
        # (PostScript) outer contour and inward on a counter; area sign tells
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        sign = 1 if area > 0 else -1
        ns = normals(pts)
        for p, (nx, _ny) in zip(contour.points, ns, strict=True):
            p.x = round(p.x + sign * nx * amount / 2)


def widen(glyph, amount, ball):
    """Move what lies right of the stem: the bowls by amount, the ball low
    down by ball.

    Above the waist the shift grows from nothing at the stem to the full
    amount over the arch, so the shoulder stretches without a kink."""
    for contour in glyph.contours:
        for p in contour.points:
            if p.y > 860:
                p.x += round(amount * min(1, max(0, (p.x - 430) / 300)))
            elif p.y < 320 and p.x > 435:  # the ball, fading into the bowl's bottom
                p.x += round(ball + (amount - ball) * min(1, max(0, (p.x - 800) / 40)))
            elif p.x > 470:
                p.x += amount


def main(path):
    font = ufoLib2.Font.open(path)
    src = font["germandbls"]
    if "uni1E9E" in font and not font["uni1E9E"].lib.get(DRAFT_KEY):
        sys.exit("uni1E9E exists and is not a draft; not overwriting it")
    if "uni1E9E" in font:
        del font["uni1E9E"]
    g = font.newGlyph("uni1E9E")
    src.drawPoints(g.getPointPen())
    g.unicodes = [0x1E9E]
    sy = CAP_HEIGHT / ASCENDER
    # the stem's left edge: the leftmost point above the serif
    dx = STEM_X - min(p.x for c in g.contours for p in c.points if 100 < p.y < 1000)
    for contour in g.contours:
        for p in contour.points:
            p.y = round(p.y * sy)
            p.x += dx
    amount = UC_STEM - LC_STEM
    embolden_x(g, amount)
    for contour in g.contours:
        for p in contour.points:
            p.x += amount // 2  # keep the left sidebearing
    widen(g, WIDEN, BALL)
    g.width = src.width + dx + amount + WIDEN
    shift = dx + amount // 2 + WIDEN // 2
    for a in src.anchors:
        if a.name in ("Bottom", "DotBelow", "Cedilla"):
            g.appendAnchor({"name": a.name, "x": a.x + shift, "y": a.y})
    tops = [a for a in src.anchors if a.name == "Top"]
    if tops:
        g.appendAnchor({"name": "TopCap", "x": tops[0].x + shift, "y": 1580})
    g.lib[DRAFT_KEY] = True
    if "uni1E9E" not in font.glyphOrder:
        order = list(font.glyphOrder)
        order.insert(order.index("germandbls") + 1, "uni1E9E")
        font.glyphOrder = order
    font.lib.setdefault("public.openTypeCategories", {})["uni1E9E"] = "base"
    font.save()
    print(f"uni1E9E drafted: width {g.width}")


if __name__ == "__main__":
    main(sys.argv[1])
