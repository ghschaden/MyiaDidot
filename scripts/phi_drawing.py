"""Approved Bold Italic ɸ: wider white counters; its inner returns as the
refitted o draws them (make_bold.oval), no longer replaced here."""

from copy import deepcopy
from math import radians, tan

import derive
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from italic_geometry import XH, shear
from ufoLib2.objects import Glyph
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
    fitted = Glyph()
    candidate.draw(TransformPen(RoundingPen(fitted.getPen()), (1, 0, slant, 1, -slant*XH/2, 0)))
    add_extrema(fitted)
    fair_joins(fitted)
    glyph = font[NAME]
    glyph.clearContours()
    glyph.clearComponents()
    fitted.draw(glyph.getPen())
