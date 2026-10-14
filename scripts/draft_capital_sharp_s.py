"""Draft ẞ (U+1E9E) from ß, as a starting point for design.

    python scripts/draft_capital_sharp_s.py UFO

Copies the outline of germandbls into a new glyph uni1E9E, scales it
vertically so the ascender (1496, the top of l and h) meets the cap height
(1434), and thickens the vertical stems from the lowercase 164 to the capital
208 by moving each point sideways in proportion to how far its outline faces
left or right: thick vertical strokes gain the full 44 units, the horizontal
hairlines nothing. The glyph is marked as a draft (lib DRAFT_KEY) for review.
"""

import math
import sys

import ufoLib2

ASCENDER, CAP_HEIGHT = 1496, 1434
LC_STEM, UC_STEM = 164, 208
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
    for contour in g.contours:
        for p in contour.points:
            p.y = round(p.y * sy)
    amount = UC_STEM - LC_STEM
    embolden_x(g, amount)
    for contour in g.contours:
        for p in contour.points:
            p.x += amount // 2  # keep the left sidebearing
    g.width = src.width + amount
    for a in src.anchors:
        if a.name in ("Bottom", "DotBelow", "Cedilla"):
            g.appendAnchor({"name": a.name, "x": a.x + amount // 2, "y": a.y})
    tops = [a for a in src.anchors if a.name == "Top"]
    if tops:
        g.appendAnchor({"name": "TopCap", "x": tops[0].x + amount // 2, "y": 1580})
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
