"""The bold styles' small caps on their lines, their serifs' brackets, and
two drawn: the Bold's k.sc join, the Bold Italic's x.sc.

The pointed feet overshoot by 18 to 35 units. Heavier they end
flat and broad, and a flat foot that deep hangs under its neighbours (ZWÖLF,
BOXKÄMPFER, the person, 2026-11-01): 6 units, the same for each foot. w's
and v's serifs stood 9 units over the height of their neighbours, and w
looked the larger for it.

A stroke emboldened past its serif leaves the bracket's handle on the serif
behind where the curve starts, and the curve turns back: a wobble at the foot
(ä.sc). That handle goes halfway along the bracket. Only on the top of a foot
serif: on a round's extreme a handle may stand so, and the bowl needs it.
"""

from ufoLib2.objects.point import Point

DEPTH = 6
HEIGHT = 1040
SERIF_TOP = range(65, 80)
# the Bold Italic's x.sc: its arm and leg run into their serifs as the
# Italic's do; by its strokes alone, a knee at each (the person, 2026-11-01)
X_SC = ("-38,0 -12,73 75,73 150,73o 217,120o 267,171c 543,454 326,891 312,920o 306,960o 285,960c "
        "143,960 166,1040 716,1040 695,961 638,961 612,961o 585,939o 585,913c 585,901o 591,894o 595,886c "
        "721,627 880,803 905,830o 911,862o 906,905c 903,940o 889,959o 852,959c 757,959 780,1040 1329,1040 "
        "1306,958 1213,958 1150,958o 1093,935o 1051,888c 764,566 990,139 1012,97o 1030,71o 1070,71c "
        "1150,71 1128,0 587,0 609,70 682,70 702,70o 739,73o 739,103c 739,117o 732,124o 725,135c "
        "588,393 406,207 392,193o 386,171o 386,149c 386,111o 405,72o 438,72c 523,72 499,0")


def brackets(glyph):
    for contour in glyph.contours:
        P, n = contour.points, len(contour.points)
        for i, p3 in enumerate(P):
            if p3.type != "curve":
                continue
            p0, h1, h2 = P[(i - 3) % n], P[(i - 2) % n], P[(i - 1) % n]
            if h1.type or h2.type:
                continue
            for flat, inner, near in ((h2, p3, p0), (h1, p0, p3)):
                if (flat.y == inner.y and inner.y in SERIF_TOP and near.y > inner.y
                        and (flat.x - near.x) * (inner.x - near.x) < 0):
                    flat.x = round((near.x + inner.x) / 2)


def x_sc(font):
    glyph = font["x.sc"]
    contour = glyph.contours[0]
    first = contour.points[0]
    if first.y != 0 or len(contour.points) != 70:
        raise ValueError("Bold Italic x.sc changed; review its drawing")
    dx = first.x + 38  # as spaced
    points = []
    for item in X_SC.split():
        kind = {"o": None, "c": "curve"}.get(item[-1], "line")
        x, y = item.rstrip("oc").split(",")
        points.append(Point(x=int(x) + dx, y=int(y), type=kind, smooth=kind == "curve"))
    contour.points[:] = points


def k_sc(font):
    """The arm and leg run straight into the stem: their ends bent there."""
    points = font["k.sc"].contours[0].points
    keys = [(p.x, p.y) for p in points]
    if (500, 585) not in keys or (475, 522) not in keys:
        raise ValueError("Bold k.sc changed; review its join")
    for key, to in (((468, 571), (468, 548)), ((468, 519), (468, 531))):
        points[keys.index(key)].x, points[keys.index(key)].y = to
    for key in ((500, 585), (475, 522)):
        del points[[(p.x, p.y) for p in points].index(key)]


def finish(font):
    if font.info.styleName == "Bold":
        k_sc(font)
    else:
        x_sc(font)
    for name in ("m.sc", "v.sc", "w.sc"):
        points = [p for c in font[name].contours for p in c.points]
        for p in points:
            p.y = min(p.y, HEIGHT)
        low = min(p.y for p in points)
        if low < -DEPTH:
            for p in points:
                if p.y < 0:
                    p.y = round(p.y * DEPTH / -low)
    if font.info.styleName == "Bold Italic":
        for glyph in font:
            if glyph.name.endswith(".sc") and glyph.contours:
                brackets(glyph)
