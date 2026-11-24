"""The Bold's ! ¡: their wedge's straight sides run smoothly into its curves.

! ¡ from Old Standard (scripts/regular_signs.py, 2026-11-24): in the
Regular each straight side of the wedge runs into the curve beside it in
line (85.4 and 85.5 degrees). Emboldened by weight, the wedge thickens
more at its wide end than at its point, the sides tilt and the curves'
handles do not follow: smooth nodes 1.7-2.2 degrees off (¡ 414,203 listed
at 2.2, ! 1.8). At each smooth node between a line and a curve, the
curve's handle is put on the line's direction, its length kept.
"""

import math

NAMES = ("exclam", "exclamdown")


def finish(font):
    if font.info.styleName != "Bold":
        return
    for name in NAMES:
        for contour in font[name].contours:
            P = contour.points
            n = len(P)
            for i, p in enumerate(P):
                if not p.type or not p.smooth:
                    continue
                a, b = P[i - 1], P[(i + 1) % n]
                if (a.type is None) == (b.type is None):
                    continue  # two curves or two lines
                line, handle = (a, b) if a.type else (b, a)
                dx, dy = p.x - line.x, p.y - line.y
                d = math.hypot(dx, dy)
                length = math.hypot(handle.x - p.x, handle.y - p.y)
                if not d or not length:
                    continue
                handle.x = round(p.x + dx / d * length)
                handle.y = round(p.y + dy / d * length)
