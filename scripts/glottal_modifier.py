"""Rebuild Bold ˀ from its final base: the superior of the Bold's ʔ.

ˀ is made from ʔ, as ˁ from ʕ (data_regular.py, 2026-11-24; from ɂ until
then, and this pass then fitted the Bold's into the box and advance the
accepted drawing of 2026-10-25 had: 62,639-385,1161, 449). Emboldened from
the Regular's, a modifier's small curves come out uneven; made again from
the finished Bold ʔ by derive.superior, its joins faired, at the
superior's own size, spaced as the Bold's ˁ mirrored.
"""

import derive
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Glyph
from upright_aleph import fair_joins

NAME = "uni02C0"
BASE = "uni0294"
TWIN = "uni02C1"  # ˁ, spaced as its mirror


def finish(font):
    if font.info.styleName != "Bold":
        return
    glyph = font[NAME]
    outline, _ = derive.superior(font, BASE)
    candidate = Glyph()
    derive.draw_path(font, font[BASE], candidate, outline)
    fitted = Glyph()
    candidate.draw(RoundingPen(fitted.getPen()))
    fair_joins(fitted)
    # spaced as ˁ mirrored (in the Regular ˀ's left side 71, ˁ's right 72):
    # ˁ's advance, ˀ's left side ˁ's right
    twin = font[TWIN]
    dx = round(twin.width - twin.getBounds(font).xMax - fitted.getBounds(None).xMin)
    glyph.clearContours()
    glyph.clearComponents()
    fitted.draw(TransformPen(glyph.getPen(), (1, 0, 0, 1, dx, 0)))
    glyph.width = twin.width
