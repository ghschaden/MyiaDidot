"""Give Bold Italic ɉ a visible bar arm on both sides, at its own weight."""


def finish(font):
    """Both bar arms 1.25 of the bar's thickness past the stem's edges.

    Emboldened, the stem eats into the Italic's arms: the right one
    ended inside the heavier stem (2026-10-24: too short), and
    with the Italic's bar centred (2026-11-06) the left one came to 68
    against the right one's 80. The stem corners and the rest of the glyph
    stay; each terminal keeps the bar's top and bottom and its slanted end.
    """
    if font.info.styleName != "Bold Italic" or "uni0249" not in font:
        return
    glyph = font["uni0249"]
    for contour in glyph.contours:
        points = contour.points
        n = len(points)
        for i in range(n):
            a, b, c, d = (points[(i + k) % n] for k in range(4))
            if not all(p.type == "line" for p in (a, b, c, d)):
                continue
            if abs(b.y - a.y) > 4 or abs(c.y - d.y) > 4:
                continue
            # the right arm: stem top, end top, end bottom, stem bottom
            if 450 < a.y < 490 and 390 < d.y < 430 and b.x > a.x and c.x > d.x:
                extension = round(1.25 * (a.y - d.y))
                b.x, b.y = a.x + extension, a.y
                c.x, c.y = d.x + extension, d.y
            # the left arm: stem bottom, end bottom, end top, stem top
            elif 390 < a.y < 430 and 450 < d.y < 490 and b.x < a.x and c.x < d.x:
                extension = round(1.25 * (d.y - a.y))
                b.x, b.y = a.x - extension, a.y
                c.x, c.y = d.x - extension, d.y
