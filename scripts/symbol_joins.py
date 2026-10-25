"""Reviewed roman diagonal joins and their central baseline alignment."""


def close_roman_counter(glyph, start, end, target):
    """Extend the diagonal directly to its upright, eliminating the slit.

    The old return curve ran almost parallel to the upright, leaving a
    narrow white channel under the serif. Intersect the existing diagonal
    and upright edges instead; keep the surrounding strokes fixed.
    """
    for contour in glyph.contours:
        points = contour.points
        for i, p in enumerate(points):
            if (p.x, p.y) != start:
                continue
            # The old run is diagonal end, two controls, curved top, then
            # the upright top. Its preceding point lies on the diagonal.
            if (points[i + 4].x, points[i + 4].y) != end:
                raise ValueError(f"{glyph.name}: counter return changed")
            previous = points[i - 1]
            x = end[0]
            y = round(previous.y + (p.y - previous.y) * (x - previous.x) / (p.x - previous.x))
            p.x, p.y, p.type, p.smooth = x, y, "line", False
            if (x, y) != target:
                raise ValueError(f"{glyph.name}: diagonal intersection changed")
            del points[i + 1:i + 5]
            return
    if any((p.x, p.y, p.type) == (*target, "line") for c in glyph.contours for p in c.points):
        return
    raise ValueError(f"{glyph.name}: counter signature missing")


def regular(font):
    """Apply once to the Regular master before regenerating its children."""
    for name, start, end, target in (("M", (370, 1315), (350, 1382), (350, 1378)),
                                    ("uni043C", (269, 756), (256, 836), (256, 793)),
                                    ("uni2116", (569, 1298), (553, 1382), (553, 1328)),
                                    ("trademark", (1221, 1368), (1208, 1448), (1208, 1405))):
        close_roman_counter(font[name], start, end, target)
    for name, y, baseline in (("M", -28, 0), ("uni043C", -26, 0), ("trademark", 586, 612)):
        for contour in font[name].contours:
            for point in contour.points:
                if point.y == y:
                    point.y = baseline


def trademark(font):
    """Fair the weighted T shoulders and parallelize M's two outer stems."""
    if font.info.styleName != "Bold Italic":
        return
    # Whole-unit coordinates after the normal generated-style writer.
    changes = {
        # M: right edge of left hairline already follows the italic angle.
        # Correct its left edge and upper tangent, plus the right stem's
        # inner edge. Its central diagonal remains untouched.
        (1518, 1335): (1568, 1335),
        (1524, 1367): (1577, 1367),
        (2102, 1229): (2078, 1229),
        (1919, 648): (1920, 648),
        # T: replace the two excessive backward shoulder handles.
        (1061, 1379): (1090, 1379),
        (1018, 1379): (1076, 1379),
        (823, 1379): (793, 1379),
        (867, 1379): (810, 1379),
    }
    glyph = font["trademark"]
    found = set()
    for contour in glyph.contours:
        for point in contour.points:
            key = point.x, point.y
            if key in changes:
                point.x, point.y = changes[key]
                found.add(key)
    if not found and all(any((p.x, p.y) == after for c in glyph.contours for p in c.points)
                         for after in changes.values()):
        return
    if found != changes.keys():
        raise ValueError("Bold Italic trademark changed; review the shoulder/stem repair")


def finish(font):
    trademark(font)
    if font.info.styleName == "Bold":
        # Generic optical fitting responds to the filled corner; this local
        # ink repair deliberately keeps the established spacing instead.
        glyph = font["uni2116"]
        left = glyph.getBounds(font).xMin
        if left not in (57, 59):
            raise ValueError("Bold numero's optical fit changed; review its placement")
        for contour in glyph.contours:
            for point in contour.points:
                point.x += 57 - left
        glyph.width = 2475


if __name__ == "__main__":
    import sys

    import ufoLib2

    for path in sys.argv[1:]:
        font = ufoLib2.Font.open(path)
        regular(font)
        font.save()
