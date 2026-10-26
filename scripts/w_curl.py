"""Smooth the approved Bold Italic Ⱳ curl/diagonal connection."""

from copy import deepcopy
from math import radians, tan

from fontTools.pens.roundingPen import RoundingPen
from italic_geometry import XH, shear
from ufoLib2.objects import Glyph, Point
from upright_aleph import add_extrema, fair_joins

NAME = "uni2C72"


def finish(font):
    if font.info.styleName != "Bold Italic":
        return
    glyph = font[NAME]
    candidate = deepcopy(glyph)
    slant = tan(radians(-font.info.italicAngle))
    shear(candidate, -slant, XH / 2)
    contour = candidate.contours[0]
    points = contour.points
    # The generated curl has two 48-unit ledges at y=1150. A second
    # finishing pass sees no such ledges and leaves the drawing alone.
    ledges = [i for i, p in enumerate(points)
              if p.type and abs(p.y-1150) < .01
              and points[i-1].type and abs(points[i-1].y-1150) < .01
              and abs(abs(p.x-points[i-1].x)-48) < .01]
    if not ledges:
        return
    if len(points) != 60 or ledges != [25, 50]:
        raise ValueError("Ⱳ source changed: review the approved curl connection")
    p = list(points)
    # Meet the existing inner diagonal at y=1050; preserve everything
    # beyond the two local approaches, including the crown and ball.
    x = 1621.64 + (1231.60-1621.64) * (1150-1050) / (1150+35)
    contour.points = (p[:22] + [Point(1460, 1060), Point(1510, 1259), p[28]]
                      + p[29:47] + [Point(1614, 1219), Point(x+18, 1105), Point(x, 1050, type="curve")]
                      + p[51:])
    shear(candidate, slant, XH / 2)
    fitted = Glyph()
    candidate.draw(RoundingPen(fitted.getPen()))
    add_extrema(fitted)
    fair_joins(fitted)
    glyph.clearContours()
    fitted.draw(glyph.getPen())
