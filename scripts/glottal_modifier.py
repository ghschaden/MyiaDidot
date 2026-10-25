"""Rebuild Bold ˀ from its final base without changing accepted spacing."""

import derive
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Glyph
from upright_aleph import fair_joins

NAME = "uni02C0"
BOUNDS = (62, 639, 385, 1161)
ADVANCE = 449


def finish(font):
    if font.info.styleName != "Bold":
        return
    glyph = font[NAME]
    base = font['uni0242']
    outline, _ = derive.superior(font, 'uni0242')
    candidate = Glyph()
    derive.draw_path(font, base, candidate, outline)
    a, b, c, d = candidate.getBounds(None)
    x0, y0, x1, y1 = BOUNDS
    sx, sy = (x1-x0)/(c-a), (y1-y0)/(d-b)
    fitted = Glyph()
    candidate.draw(TransformPen(RoundingPen(fitted.getPen()), (sx,0,0,sy,x0-sx*a,y0-sy*b)))
    fair_joins(fitted)
    # Do not let a one-unit tangent adjustment push an extreme's handles
    # outside its original ink box and change the compiled sidebearing.
    for contour in fitted.contours:
        for point in contour.points:
            point.x = min(x1, max(x0, point.x))
            point.y = min(y1, max(y0, point.y))
        points = contour.points
        for i, point in enumerate(points):
            if not point.type or not point.smooth:
                continue
            for neighbour in (points[i-1], points[(i+1) % len(points)]):
                if neighbour.type is None:
                    if point.x in (x0, x1):
                        neighbour.x = point.x
                    if point.y in (y0, y1):
                        neighbour.y = point.y
    glyph.clearContours()
    glyph.clearComponents()
    fitted.draw(glyph.getPen())
    glyph.width = ADVANCE
