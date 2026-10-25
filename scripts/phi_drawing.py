"""Approved Bold Italic ɸ: wider white counters and smooth inner returns."""

from copy import deepcopy
from math import radians, tan

import derive
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from make_italic import XH, shear
from ufoLib2.objects import Glyph, Point
from upright_aleph import add_extrema, fair_joins

NAME = "uni0278"


def finish(font):
    if font.info.styleName != "Bold Italic":
        return
    # Measure the final bases in the recipe's upright frame.
    up = deepcopy(font)
    slant = tan(radians(-font.info.italicAngle))
    for name in ("o", "l"):
        shear(up[name], -slant, XH / 2)
    bounds = derive.ink_bounds(up, "o")
    cx = (bounds[0] + bounds[2]) / 2
    a, b = derive.stems_at(up, "l", XH / 2)[0]
    half = (b - a) * .8 / 2
    delta = (bounds[2] - bounds[0]) * .05
    bowl = derive.to_path(up, up["o"])
    bowl.reset()
    # Add the same absolute width to both contours: extra white rather
    # than a proportional increase in the black ring's thickness.
    for contour in up["o"].contours:
        pen = BoundsPen(None)
        contour.draw(pen)
        x0, _, x1, _ = pen.bounds
        scale = (x1 - x0 + delta) / (x1 - x0)
        center = (x0 + x1) / 2
        contour.draw(TransformPen(bowl.getPen(), (scale, 0, 0, 1, center * (1 - scale), 0)))
    outline = derive.path_op(bowl, derive.rect_path(cx-half, -560, cx+half, 1400), "UNION")
    candidate = Glyph()
    outline.draw(candidate.getPen())
    # These counter returns replace the inherited inflected o segments.
    # Sort by x so pathops' contour order is not significant.
    counters = sorted(candidate.contours[1:], key=lambda c: min(p.x for p in c.points))
    left, right = counters
    lp, rp = list(left.points), list(right.points)
    if len(lp) != 13 or len(rp) != 13:
        raise ValueError("ɸ base changed: review the approved counter returns")
    left.points = lp[:4] + [Point(360, 689), Point(380, 790), lp[9]] + lp[10:]
    right.points = rp[:7] + [Point(636, 174), Point(614, 70), rp[12]]
    fitted = Glyph()
    candidate.draw(TransformPen(RoundingPen(fitted.getPen()), (1, 0, slant, 1, -slant*XH/2, 0)))
    add_extrema(fitted)
    fair_joins(fitted)
    glyph = font[NAME]
    glyph.clearContours()
    glyph.clearComponents()
    fitted.draw(glyph.getPen())
