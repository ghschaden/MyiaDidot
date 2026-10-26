"""Shared italic-frame geometry; no generator orchestration imports."""

import copy
import math

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

ANGLE = 15.2
SLANT = math.tan(math.radians(ANGLE))
XH, CAP = 884, 1434
# units a slanted curve may run past its end points before it is split at
# its extreme (as scripts/quality/checks.py finds them)
EXTREME_PAST = 5


def redraw(g, glyph):
    """Replace g's contours with those of glyph (an emboldened ufoLib2 Glyph);
    quadratic segments (pathops' results may hold some) made cubic."""
    g.clearContours()
    if any(p.type == "qcurve" for c in glyph.contours for p in c.points):
        from derive import CubicPen

        for c in glyph.contours:
            c.draw(CubicPen(g.getPen()))
        return
    pen = g.getPointPen()
    for c in glyph.contours:
        c.drawPoints(pen)


def shear(g, s, y0=XH / 2, extremes=False):
    """Slant (s > 0) or unslant (s < 0) a glyph about the height y0; with
    extremes, its curves split where they now run past their points
    (EXTREME_PAST: a slanted bowl's extremes move off them), for a glyph
    that stays slanted."""
    if g.contours:
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
        out = ufoLib2.objects.Glyph()
        slanted = RecordingPen()
        rec.replay(TransformPen(slanted, (1, 0, s, 1, -s * y0, 0)))
        if extremes:
            from derive import with_extremes

            with_extremes(slanted, out.getPen(), round_points=False, past=EXTREME_PAST)
        else:
            slanted.replay(out.getPen())
        redraw(g, out)
    for c in g.components:
        xx, xy, yx, yy, dx, dy = c.transformation
        c.transformation = (xx, xy, yx, yy, round(dx + dy * s), dy)
    for a in g.anchors:
        a.x = round(a.x + (a.y - y0) * s)



def upright(font):
    """The whole font unslanted: what is made in it is slanted back."""
    up = copy.deepcopy(font)
    for g in up:
        shear(g, -SLANT)
    return up

