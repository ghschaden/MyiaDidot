"""Keep the capital cedilla's attachment tip inside the letter's ink."""

import math

# Capital cedillas attach with dy=122. The italic C's counter starts at
# y=30: keep the top of the attached mark one unit below it. Weighting can
# otherwise push the corner through the inner edge (a sub-unit step).
TOP = -93
ATTACHMENT = -122


def finish(font):
    """Shorten only Cedilla's buried tip, after rounding; keep its anchors."""
    glyph = font["Cedilla"]
    top = max(p.y for c in glyph.contours for p in c.points)
    if top <= TOP:
        return
    slant = -math.tan(math.radians(font.info.italicAngle or 0))
    for contour in glyph.contours:
        for point in contour.points:
            if point.y > ATTACHMENT:
                y = round(ATTACHMENT + (point.y - ATTACHMENT) * (TOP - ATTACHMENT) / (top - ATTACHMENT))
                point.x += round((y - point.y) * slant)
                point.y = y
