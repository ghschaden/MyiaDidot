"""Finish the accepted roman aleph and the italic joins distorted by weighting."""


_LOWER_BEFORE = (
    (719, -6, "curve"),
    (721, 3, None), (745, 10, None), (749, 19, "curve"),
    (746, 18, "line"),
    (746, 18, None), (737, 17, None), (748, 57, "curve"),
    (748, 58, None), (740, 59, None), (740, 59, "curve"),
)
_LOWER_AFTER = (
    (719, -6, "curve"),
    (721, 3, None), (729, 22, None), (740, 59, "curve"),
)
_UPPER_BEFORE = (
    (978, 588, "curve"),
    (977, 588, None), (934, 583, None), (919, 596, "curve"),
    (917, 598, None), (930, 606, None), (929, 606, "curve"),
    (925, 606, None), (882, 598, None), (855, 574, "curve"),
    (825, 547, None), (864, 514, None), (850, 478, "curve"),
)
_UPPER_AFTER = (
    (978, 588, "curve"),
    (951, 588, None), (941, 606, None), (929, 606, "curve"),
    (830, 606, None), (864, 514, None), (850, 478, "curve"),
)


def _lower_return(glyph):
    """Restore the source's smooth lower return, preserving its surroundings.

    The Old Standard Italic source has no ledge at this tip. Weighting adds
    both a three-unit straight return and an eight-unit curved return just
    above it. Replace that run with one cubic, keeping its endpoints and
    first handle. The new second handle meets the following original handle
    (751, 96) at exactly the same tangent, (11, 37).
    """
    for contour in glyph.contours:
        points = contour.points
        signature = tuple((p.x, p.y, p.type) for p in points)
        for i in range(len(points)):
            if signature[i:i + len(_LOWER_BEFORE)] == _LOWER_BEFORE:
                points[i + 2].x, points[i + 2].y = 729, 22
                points[i + len(_LOWER_BEFORE) - 1].smooth = True
                del points[i + 3:i + len(_LOWER_BEFORE) - 1]
                return
            if signature[i:i + len(_LOWER_AFTER)] == _LOWER_AFTER:
                return
    raise ValueError("Bold Italic aleph's lower tip changed; review the return repair")


def _upper_join(glyph):
    """Remove a reverse spur and the following S-shaped edge at the stem.

    The Italic source flows left through a shallow shoulder and then down
    to the stem. Weighting reverses the first curve and makes the following
    edge turn left, right and left again. Two cubics restore that flow. The
    shoulder joins remain horizontal; the last endpoint and handle retain
    the original direction into the unchanged central diagonal.
    """
    for contour in glyph.contours:
        points = contour.points
        signature = tuple((p.x, p.y, p.type) for p in points)
        for i in range(len(points)):
            if signature[i:i + len(_UPPER_BEFORE)] == _UPPER_BEFORE:
                points[i + 1].x, points[i + 1].y = 951, 588
                points[i + 2].x, points[i + 2].y = 941, 606
                points[i + 7].x, points[i + 7].y = 830, 606
                points[i + 8].x, points[i + 8].y = 864, 514
                del points[i + 9:i + 12]
                del points[i + 3:i + 6]
                return
            if signature[i:i + len(_UPPER_AFTER)] == _UPPER_AFTER:
                return
    raise ValueError("Bold Italic aleph's upper join changed; review the join repair")


def finish(font):
    """Apply the style's repairs, including when they are already present."""
    if "uni2135" not in font:
        return
    if font.info.styleName == "Bold":
        from upright_aleph import install

        install(font)
    elif font.info.styleName == "Bold Italic":
        _lower_return(font["uni2135"])
        _upper_join(font["uni2135"])
