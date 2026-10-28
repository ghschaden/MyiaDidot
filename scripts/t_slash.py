"""Close the residual counter between Bold Italic Ⱦ's slash and foot serif."""

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen


def finish(font):
    """Fill only small, low counters in Ⱦ; preserve its upper opening."""
    if font.info.styleName != "Bold Italic" or "uni023E" not in font:
        return
    glyph = font["uni023E"]
    areas = []
    for contour in glyph.contours:
        pen = AreaPen()
        contour.draw(pen)
        areas.append(pen.value)
    if not areas:
        return
    outer = max(areas, key=abs)
    for contour, area in zip(list(glyph.contours), areas):
        bounds = BoundsPen(None)
        contour.draw(bounds)
        if bounds.bounds is None:
            continue
        _, y0, _, y1 = bounds.bounds
        # (by strokes the slash comes from its recipe on the stroked T: the
        # counter grew from about 400 units² to 3000, up to 200 high)
        if area * outer < 0 and abs(area) <= 4000 and 0 < y0 < y1 < 220:
            glyph.contours.remove(contour)
