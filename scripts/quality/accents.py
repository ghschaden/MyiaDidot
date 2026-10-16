"""accents.py UFO: in accented letters (a base and marks), the gap between
the letter's ink and the mark's, and the mark's centring over the letter
(its ink centre against the centre of the letter's top or bottom ink),
per mark; lists the outliers."""
import collections
import math
import statistics
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

font = ufoLib2.Font.open(sys.argv[1])
slant = math.tan(math.radians(-(font.info.italicAngle or 0)))


def path_of(name, t=(1, 0, 0, 1, 0, 0)):
    p = pathops.Path()
    r = DecomposingRecordingPen(font)
    font[name].draw(r)
    # deslanted, so centring is judged upright
    r.replay(TransformPen(TransformPen(p.getPen(), (1, 0, -slant, 1, 0, 0)), t))
    return p


def clip(p, y0, y1):
    r = pathops.Path(); pen = r.getPen()
    pen.moveTo((-9000, y0)); pen.lineTo((9000, y0)); pen.lineTo((9000, y1)); pen.lineTo((-9000, y1)); pen.closePath()
    return pathops.op(p, r, pathops.PathOp.INTERSECTION)


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from make_bold import mark_like

marks = {g.name for g in font if mark_like(g)}
data = collections.defaultdict(list)
for g in font:
    if not g.components or g.contours or len(g.components) != 2:
        continue
    base, mark = g.components
    if base.baseGlyph in marks or mark.baseGlyph not in marks:
        continue
    bp = path_of(base.baseGlyph, base.transformation)
    mp = path_of(mark.baseGlyph, mark.transformation)
    bb, mb = bp.bounds, mp.bounds
    if bb == (0, 0, 0, 0) or mb == (0, 0, 0, 0):
        continue
    above = mb[1] > (bb[1] + bb[3]) / 2
    if above:
        gap = mb[1] - bb[3]
        top = clip(bp, bb[3] - 150, bb[3] + 1).bounds
    else:
        gap = bb[1] - mb[3]
        top = clip(bp, bb[1] - 1, bb[1] + 150).bounds
    if top == (0, 0, 0, 0):
        continue
    cen = (mb[0] + mb[2]) / 2 - (top[0] + top[2]) / 2
    cap = bb[3] > 1200 and not g.name.endswith(".sc")
    sc = g.name.endswith(".sc")
    kind = ("cap" if cap else "sc" if sc else "lc") + (" above" if above else " below")
    data[(mark.baseGlyph, kind)].append((gap, cen, g.name))
print(sys.argv[1].split("/")[-1])
out = []
for (mk, kind), rows in sorted(data.items()):
    if len(rows) < 4:
        continue
    gaps = [r[0] for r in rows]; cens = [r[1] for r in rows]
    mg, mc = statistics.median(gaps), statistics.median(cens)
    odd = [(r[2], round(r[0] - mg), round(r[1] - mc)) for r in rows if abs(r[0] - mg) > 25 or abs(r[1] - mc) > 30]
    if odd:
        out.append((len(odd), f"  {mk:14} {kind:9} n={len(rows):3} gap {mg:5.0f}  off: " + " ".join(f"{n}(gap{dg:+},x{dc:+})" for n, dg, dc in odd[:10])))
for _, l in sorted(out, reverse=True)[:30]:
    print(l)
print(f"  {sum(len(v) for v in data.values())} accented letters checked, {sum(o[0] for o in out)} off")
