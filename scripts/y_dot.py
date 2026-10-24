"""Place the italic y's dot below beside its descender, at either weight."""

import math

import pathops
from fontTools.pens.recordingPen import DecomposingRecordingPen

GAP = 25  # Half the first proof's gap: a little closer to the descender.


def y_dot_anchor(font):
    """Keep the dot height and derive its horizontal clearance from final ink."""
    y = font["y"]
    anchor = next(a for a in y.anchors if a.name == "DotBelow")
    mark = font["dotbelowcomb"]
    own = next(a for a in mark.anchors if a.name == "_DotBelow")
    bounds = mark.getBounds(font)
    lo, hi = bounds.yMin + anchor.y - own.y, bounds.yMax + anchor.y - own.y
    recording = DecomposingRecordingPen(font)
    y.draw(recording)
    outline = pathops.Path()
    recording.replay(outline.getPen())
    band = pathops.Path()
    pen = band.getPen()
    ybounds = y.getBounds(font)
    pen.moveTo((ybounds.xMin - 1, lo))
    pen.lineTo((ybounds.xMax + 1, lo))
    pen.lineTo((ybounds.xMax + 1, hi))
    pen.lineTo((ybounds.xMin - 1, hi))
    pen.closePath()
    clipped = pathops.op(outline, band, pathops.PathOp.INTERSECTION)
    anchor.x = math.ceil(clipped.bounds[2] + GAP - bounds.xMin + own.x)
