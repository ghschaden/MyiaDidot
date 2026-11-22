"""Join the Italic belted-l pieces to the final l and L stems."""

import math
from copy import deepcopy

from derive import draw_path, path_op, rect_path, stems_at, to_path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

TARGETS = {"uni026C": "l", "uniA7AD": "L"}


def finish(font):
    """Extend only the buried belt ends, keeping the base and visible arms.

    The inherited placements leave the ring and bar a few units away from
    the lighter italic stems. Bridge their three end faces to the measured
    stem edges with three units of overlap. Work in the upright frame so
    the extensions follow the font's slant rather than making wedges.
    """
    if font.info.styleName != "Italic":
        return
    slope = math.tan(math.radians(-(font.info.italicAngle or 0)))
    for name, base in TARGETS.items():
        if name not in font:
            continue
        glyph = font[name]
        if len(glyph.contours) == 2:  # Connected outer outline and belt counter.
            flatten_stem(font, glyph, base, attachment_band(name))
            continue
        if len(glyph.contours) != 3:
            raise ValueError(f"{name}: review the belted-l component construction")
        ring = next(c for c in glyph.contours if 300 < c.bounds.yMax - c.bounds.yMin < 400)
        bar = next(c for c in glyph.contours if len(c.points) == 4)

        def edge(y, side, base=base):
            intervals = stems_at(font, base, y)
            if len(intervals) != 1:
                raise ValueError(f"{base}: expected one stem at belt height {y}")
            return intervals[0][side] - slope * y

        bridges = []
        for i, point in enumerate(ring.points):
            previous = ring.points[i - 1]
            if point.type == 'line' and previous.type == 'curve':
                y0, y1 = sorted((point.y, previous.y))
                x0 = min(p.x - slope * p.y for p in (point, previous)) - 1
                x1 = max(edge(y, 0) for y in (y0, y1)) + 3
                bridges.append(rect_path(x0, y0, x1, y1))
        if len(bridges) != 2:
            raise ValueError(f"{name}: expected the two exposed ring ends")
        y0, y1 = bar.bounds.yMin, bar.bounds.yMax
        left = min(p.x - slope * p.y for p in bar.points)
        bridges.append(rect_path(min(edge(y, 1) for y in (y0, y1)) - 3, y0, left + 1, y1))
        out = to_path(font, glyph)
        for bridge in bridges:
            sloped = RecordingPen()
            bridge.draw(TransformPen(sloped, (1, 0, slope, 1, 0, 0)))
            out = path_op(out, to_path(None, rec=sloped), 'UNION')
        before = deepcopy(glyph)
        glyph.clearContours()
        draw_path(font, before, glyph, out)
        flatten_stem(font, glyph, base, attachment_band(name))


def flatten_stem(font, glyph, base, band, near=6, on=1.5):
    """The stem's edges in glyph (in place) run as the base's: where the
    ring's arc reaches a few units past the stem (ɬ: 3 units on the right
    edge between the bar and the ring, a curve of three nodes with a
    4.4-degree turn), the nodes between two on the base's edge are
    dropped and the edge drawn as a line, within the belt's band only
    (the l's own curves above and below kept; 2026-11-22)."""

    def edges(y):
        runs = stems_at(font, base, y)
        return [x for run in runs for x in run] if len(runs) == 1 else []

    def at_edge(p, tol):
        return band[0] <= p.y <= band[1] and any(abs(p.x - x) <= tol for x in edges(p.y))

    for contour in glyph.contours:
        pts = contour.points
        i = 0
        while i < len(pts):
            n = len(pts)
            if not pts[i].type or not at_edge(pts[i], on):
                i += 1
                continue
            j = (i + 1) % n
            run = []
            while j != i and at_edge(pts[j], near) and not (pts[j].type and at_edge(pts[j], on)):
                run.append(j)
                j = (j + 1) % n
            if run and j != i and pts[j].type and at_edge(pts[j], on) and pts[j].type != "line":
                pts[j].type = "line"
                pts[j].smooth = False
                for k in sorted(run, reverse=True):
                    del pts[k]
                    if k < i:
                        i -= 1
            i += 1


def attachment_band(name):
    """The true pieces' vertical band, excluding base-rounding slivers.

    Italic derivation places the Regular degree recipe before the final
    symbol resizing. Use that same source and recipe, not final Italic's
    resized degree. Two units of margin cover whole-unit intersections.
    """
    from pathlib import Path

    import ufoLib2
    from derive import RECIPES

    regular = ufoLib2.Font.open(Path(__file__).resolve().parent.parent / 'sources/MyiaDidot-Regular.ufo')
    ch = chr(int(name[3:], 16))
    recipe = next(r for r in RECIPES if r[0] == ch)
    ends = []
    for piece, clip, (_, py), (_, sy, _, y, *_) in recipe[3][2]:
        if piece == 'rect':
            ends.extend((clip[1], clip[3]))
        else:
            bounds = regular[piece].getBounds(regular)
            ends.extend((y + sy * (bounds.yMin - py), y + sy * (bounds.yMax - py)))
    return math.floor(min(ends)) - 2, math.ceil(max(ends)) + 2
