"""Give Bold Italic ɉ a visible right bar arm at its own weight."""


def finish(font):
    """Extend the bar by 1.25 of its thickness beyond the right stem edge.

    The four line corners at the right join survive whole emboldening,
    but its two terminal corners end inside the heavier stem. Keep the
    stem corners and the rest of the glyph; align the terminal to the
    existing bar's top and bottom, with a slanted end.
    """
    if font.info.styleName != "Bold Italic" or "uni0249" not in font:
        return
    glyph = font["uni0249"]
    for contour in glyph.contours:
        points = contour.points
        for i in range(len(points) - 3):
            top, end_top, end_bottom, bottom = points[i:i + 4]
            if not all(p.type == "line" for p in (top, end_top, end_bottom, bottom)):
                continue
            if not (450 < top.y < 490 and 390 < bottom.y < 430):
                continue
            if abs(end_top.y - top.y) > 4 or abs(end_bottom.y - bottom.y) > 4:
                continue
            thickness = top.y - bottom.y
            extension = round(1.25 * thickness)
            end_top.x, end_top.y = top.x + extension, top.y
            end_bottom.x, end_bottom.y = bottom.x + extension, bottom.y
            return
