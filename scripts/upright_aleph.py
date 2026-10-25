"""Accepted upright aleph, from reviewed Old Standard-derived italic drawings.

The GLIFs are design sources frozen at the approved 2026-10-25 proof, not
dependencies on generated UFOs. Keeping them here avoids a roman/italic
generation cycle. Their 15.2-degree shear is inverted before vertical fit.
"""

from math import atan2, degrees, hypot, pi, radians, tan
from pathlib import Path

from fontTools.misc.bezierTools import calcCubicParameters, solveQuadratic, splitCubicAtT
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import readGlyphFromString
from ufoLib2.objects import Glyph
from ufoLib2.objects.component import Component

DATA = Path(__file__).parent / "data" / "aleph"
NAME = "uni2135"
SMALL = NAME + ".sc"
CAP_HEIGHT = 1434


def add_extrema(glyph):
    """Split substantial inherited cubic overshoots without changing curves."""
    rec = RecordingPen()
    glyph.draw(rec)
    out = Glyph()
    pen = RoundingPen(SegmentToPointPen(out.getPointPen()))
    current = None
    for op, args in rec.value:
        if op == "curveTo":
            curve = (current, *args)
            a, b, c, _ = calcCubicParameters(*curve)
            roots = set()
            for axis in (0, 1):
                for t in solveQuadratic(3*a[axis], 2*b[axis], c[axis]):
                    if not 0.001 < t < 0.999:
                        continue
                    u = 1-t
                    value = sum(k*p[axis] for k, p in zip((u**3,3*u*u*t,3*u*t*t,t**3),curve))
                    lo, hi = sorted((curve[0][axis],curve[3][axis]))
                    if max(lo-value,value-hi) > 4:
                        roots.add(t)
            for segment in splitCubicAtT(*curve, *sorted(roots)):
                pen.curveTo(*segment[1:])
        else:
            getattr(pen, op)(*args)
        if op in ("moveTo", "lineTo", "curveTo"):
            current = args[-1]
    glyph.clearContours()
    out.draw(glyph.getPen())


def fair_joins(glyph):
    """Align inherited near-tangent handles after the accepted affine fit.

    Endpoints and straight edges stay fixed. Only handles at turns under
    eight degrees move, retaining their lengths; sharp design corners stay.
    """
    for contour in glyph.contours:
        points = contour.points
        for i, point in enumerate(points):
            if point.type is None:
                continue
            a, b = points[i - 1], points[(i + 1) % len(points)]
            if a.type is not None and b.type is not None:
                continue
            va = point.x - a.x, point.y - a.y
            vb = b.x - point.x, b.y - point.y
            la, lb = hypot(*va), hypot(*vb)
            turn = abs(degrees((atan2(*va[::-1]) - atan2(*vb[::-1]) + pi) % (2*pi) - pi))
            if min(la, lb) < 10 or turn >= 8:
                continue
            direction = va if a.type is not None else vb if b.type is not None else (va[0]/la + vb[0]/lb, va[1]/la + vb[1]/lb)
            length = hypot(*direction)
            ux, uy = direction[0]/length, direction[1]/length
            if a.type is None:
                a.x, a.y = round(point.x - la*ux), round(point.y - la*uy)
            if b.type is None:
                b.x, b.y = round(point.x + lb*ux), round(point.y + lb*uy)
            point.smooth = True
            # Choose an adjacent grid position when integer rounding would
            # otherwise leave the short handle over the two-degree limit.
            def angle(a=a, point=point, b=b):
                return abs(degrees((atan2(point.y-a.y,point.x-a.x)-atan2(b.y-point.y,b.x-point.x)+pi)%(2*pi)-pi))
            best = angle()
            for handle in (a, b):
                if handle.type is not None:
                    continue
                x, y = handle.x, handle.y
                target = x, y
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        handle.x, handle.y = x+ox, y+oy
                        trial = angle()
                        if trial < best:
                            best, target = trial, (x+ox,y+oy)
                handle.x, handle.y = target


def drawing(bold=False, italic=False, tall=False, width=1380):
    source = Glyph()
    readGlyphFromString((DATA / ("BoldItalic.glif" if bold else "Italic.glif")).read_text(),
                       glyphObject=source, pointPen=source.getPointPen())
    upright = Glyph()
    source.draw(TransformPen(upright.getPen(), (1, 0, -tan(radians(15.2)), 1, 0, 0)))
    x0, y0, x1, y1 = upright.getBounds(None)
    sy = CAP_HEIGHT / (y1 - y0) if tall else 1
    dy = -y0 * sy if tall else 0
    dx = (width - (x1 - x0)) / 2 - x0
    out = Glyph()
    if italic:
        # The retained small italic is its original, already reviewed drawing.
        source.draw(out.getPen())
    else:
        upright.draw(TransformPen(RoundingPen(out.getPen()), (1, 0, 0, sy, dx, dy)))
        add_extrema(out)
        fair_joins(out)
    out.width = width
    return out


def install(font):
    """Install roman full-size ink and the retained small alternate per style."""
    if NAME not in font:
        return
    style = (font.info.styleName or "Regular").replace(" ", "")
    italic, bold = "Italic" in style, "Bold" in style
    base = font[NAME]
    if not italic:
        # Preserve the accepted roman spacing across the generic boldener's
        # newly measured outline width (which otherwise rounds up one unit).
        base.width = 1477 if bold else 1380
        out = drawing(bold=bold, tall=True, width=base.width)
        base.clearContours()
        base.clearComponents()
        out.draw(base.getPen())
    small = drawing(bold=bold, italic=italic, width=base.width)
    if italic:
        small.clearContours()
        # The inherited mathematical symbol descends 23 units. Its small-cap
        # alternate sits on the baseline, like the surrounding small caps.
        small.components.append(Component(NAME, (1, 0, 0, 1, 6, 23)))
    font.layers.defaultLayer.insertGlyph(small, name=SMALL, overwrite=True)
    order = [name for name in font.glyphOrder if name != SMALL]
    order.insert(order.index(NAME) + 1, SMALL)
    font.glyphOrder = order
    font.lib.setdefault("public.openTypeCategories", {})[SMALL] = "base"


if __name__ == "__main__":
    import sys

    import ufoLib2

    for path in sys.argv[1:]:
        font = ufoLib2.Font.open(path)
        install(font)
        font.save()
