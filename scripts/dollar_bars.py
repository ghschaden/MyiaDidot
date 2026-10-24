"""Keep Bold Italic dollar's four exposed bar edges on parallel lines."""

import math

# The inherited top and bottom terminals imply a 15-degree through-stroke.
# Retain their 86-unit width and 95-unit clear gap. Shift the common lines
# ten units right so the straight left edge clears the existing lower ball.
SLOPE = math.tan(math.radians(15))
BOTTOM = -155
EDGES = (343, 429, 524, 610)


def finish(font):
    """Undo unequal bar expansion at bowl joins after whole emboldening.

    Identify the sixteen exposed straight segments geometrically, then
    align their endpoints to four common edge lines. Short connecting bowl
    arcs are stretched with their endpoints; longer bowl curves retain
    their bodies and only translate the handle adjoining a moved endpoint.
    The ball terminals, vertical coordinates and glyph metadata survive.
    """
    if font.info.styleName != "Bold Italic" or "dollar" not in font:
        return
    glyph = font["dollar"]
    targets = []
    counts = [0] * 4
    for contour in glyph.contours:
        points = contour.points
        moves = {}
        for i, p in enumerate(points):
            a = points[i - 1]
            if p.type != "line" or not a.type or abs(p.y - a.y) < 120:
                continue
            x = (p.x + a.x - SLOPE * (p.y + a.y - 2 * BOTTOM)) / 2
            edge = min(range(4), key=lambda k: abs(EDGES[k] - x))
            if abs(EDGES[edge] - x) > 50:
                raise ValueError("dollar bar geometry changed: inspect its edge assignment")
            counts[edge] += 1
            for j in ((i - 1) % len(points), i):
                q = points[j]
                moves[j] = round(EDGES[edge] + SLOPE * (q.y - BOTTOM)) - q.x
        targets.append(moves)
    if counts != [4, 4, 4, 4]:
        raise ValueError(f"dollar bar geometry changed: exposed edges {counts}")

    for contour, moves in zip(glyph.contours, targets):
        points = contour.points
        constrained = sorted(moves)
        additional = {}
        for k, start in enumerate(constrained):
            end = constrained[(k + 1) % len(constrained)]
            span = [(start + n) % len(points)
                    for n in range(1, (end - start) % len(points))]
            if not span:
                continue
            a, b = points[start], points[end]
            yy = [points[i].y for i in [start, *span, end]]
            if max(yy) - min(yy) < 80:
                # These are the small bowl arcs across the bars' clear gap.
                # Interpolate in the unslanted frame, preserving horizontal
                # tangents at their existing extrema.
                ax, bx = a.x - SLOPE * a.y, b.x - SLOPE * b.y
                for i in span:
                    p = points[i]
                    t = (p.x - SLOPE * p.y - ax) / (bx - ax)
                    additional[i] = round(p.x + moves[start] * (1 - t) + moves[end] * t) - p.x
            else:
                if points[span[0]].type is None:
                    additional[span[0]] = moves[start]
                if points[span[-1]].type is None:
                    additional[span[-1]] = moves[end]
        for i, dx in (moves | additional).items():
            points[i].x += dx
