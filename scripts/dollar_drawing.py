"""Refine the Bold Italic dollar's waist and weighted ball entrances."""

from dollar_bars import BOTTOM, EDGES, SLOPE
from ufoLib2.objects.point import Point


def _point(x, y, kind, smooth=False):
    return Point(x=x, y=y, type=kind, smooth=smooth)


def finish(font):
    if font.info.styleName != "Bold Italic":
        return
    glyph = font['dollar']
    main = glyph.contours[0].points
    if len(main) == 76 and (main[3].x, main[3].y) == (250, 470):
        return
    if len(main) != 82 or (main[3].x, main[3].y) != (309, 485):
        raise ValueError("Bold Italic dollar changed; review its drawing pass")

    # Two parallel diagonal edges, made narrower by 52 vertical units.
    # Intersections are solved against the already corrected bar lines.
    def edge_point(contour, index, edge, intercept):
        y = (intercept - .6*(EDGES[edge] - SLOPE*BOTTOM)) / (1 + .6*SLOPE)
        y = round(y)
        x = EDGES[edge] + SLOPE*(y-BOTTOM)
        point = glyph.contours[contour].points[index]
        point.x, point.y = round(x), round(y)

    for contour, index, edge in ((0, 19, 0), (3, 8, 1), (3, 7, 2), (1, 7, 3)):
        edge_point(contour, index, edge, 1015)
    for contour, index, edge in ((2, 4, 0), (4, 0, 1), (4, 1, 2), (0, 60, 3)):
        edge_point(contour, index, edge, 1217)
    for contour, index, intercept in ((0,20,1015),(0,21,1015),(1,5,1015),(1,6,1015),
                                      (0,61,1217),(0,62,1217),(2,2,1217),(2,3,1217)):
        point = glyph.contours[contour].points[index]
        point.y = round(intercept-.6*point.x)
    # Meet the following straight diagonal on the integer grid.
    handle, point, following = glyph.contours[1].points[5:8]
    handle.y = round(point.y + (handle.x-point.x)*(following.y-point.y)/(following.x-point.x))
    point.smooth = True

    # Four cubic arcs per terminal replace the extra short backward neck
    # curves. Retain the bowl-side endpoints and their original tangents.
    upper = [
        _point(1308,1087,'curve',True),
        _point(1309,960,None),_point(1240,865,None),_point(1135,865,'curve',True),
        _point(1050,865,None),_point(1000,900,None),_point(1000,950,'curve',True),
        _point(1000,1005,None),_point(1055,1030,None),_point(1110,1030,'curve',True),
        _point(1145,1030,None),_point(1154,1095,None),_point(1154,1137,'curve',True),
    ]
    lower = [
        _point(93,275,'curve',True),
        _point(91,382,None),_point(140,470,None),_point(250,470,'curve',True),
        _point(335,470,None),_point(400,430,None),_point(400,380,'curve',True),
        _point(400,325,None),_point(340,300,None),_point(280,300,'curve',True),
        _point(250,300,None),_point(261,250,None),_point(261,220,'curve',True),
    ]
    main[41:57] = upper
    main[:16] = lower
