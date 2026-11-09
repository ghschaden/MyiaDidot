"""Give the bold styles' dots the shape of their source style's.

make_bold widens a stroke far more than it heightens it (AX against AY),
so every round dot came out an oval: the Bold's period 357 x 262 (1.36:1)
of the Regular's 256 round, i's dot 278 x 256, the dotted circle's dots
1.5:1, the Bold Italic's period 366 x 272. The references' bold dots are
round (1.00-1.05: Bodoni Moda, Libre Bodoni, Old Standard, Charis,
Libertinus, EB Garamond). Chosen 2026-11-09 from a sheet (same area or
same width as now): each dot is redrawn as its source glyph's dot (the
Regular's for the Bold, the Italic's for the Bold Italic) scaled evenly
to the area the emboldened one has. A glyph whose dots include one on the
baseline (. ! ? ⋮) keeps that dot's bottom, the others in it moved alike
(and along the slant); one whose dots all stand above the x-height (i's,
the accents) keeps the top of its highest, on its zone (i's at 1496); in
the rest (※ ⸓) each dot keeps its centre.

Dots: closed all-curve contours under 450 units, ellipse-filled (0.74-0.82
of their box), not inside another contour nor holding one. A glyph whose
bold dots do not pair one to one with its source's (by count, in reading
order) is left as it is; finish() returns the names changed.
"""

import math
from copy import deepcopy
from pathlib import Path

import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointInsidePen import PointInsidePen
from i_bar_dot import STYLES as OWNED  # set by i_bar_dot.py from the final i and j, after this pass

ROOT = Path(__file__).resolve().parent.parent
SOURCE = {"Bold": "Regular", "Bold Italic": "Italic"}

MAX = 450
FILL = (0.74, 0.82)
ROUND = (0.9, 1.12)  # a source dot: about as wide as high
BASELINE = 0  # a dot whose bottom is at or under this sits on the baseline
# the capitals' dieresis (on the small caps its top is at the cap height's
# zone, 1434): at 211 its dots are just over a pixel at 10 ppem, and the
# CFF hinting sets the small caps' tops 0.8 px above the zone (ä.sc ë.sc ...,
# 2026-11-09; 200 and 204 hint on it), so they are kept under one
TALLEST = {"Dieresis": 204}


def _bounds(contour):
    pen = BoundsPen(None)
    contour.draw(pen)
    return pen.bounds


def _area(contour):
    pen = AreaPen()
    contour.draw(pen)
    return abs(pen.value)


def _inside(contour, x, y):
    pen = PointInsidePen(None, (x, y))
    contour.draw(pen)
    return pen.getResult()


def dots(glyph):
    """The glyph's dot contours, in reading order (top to bottom, left to right)."""
    found = []
    for c in glyph.contours:
        if len(c.points) < 8 or any(p.type in ("line", "qcurve") for p in c.points):
            continue
        b = _bounds(c)
        if not b:
            continue
        w, h = b[2] - b[0], b[3] - b[1]
        if not (60 < w < MAX and 60 < h < MAX and FILL[0] < _area(c) / (w * h) < FILL[1]):
            continue
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        others = [o for o in glyph.contours if o is not c]
        if any(_inside(o, cx, cy) for o in others):
            continue  # a counter, or a dot inside a ring
        if any(all(_inside(c, p.x, p.y) for p in o.points if p.type) for o in others):
            continue  # a ring's outside
        found.append((c, b))
    return sorted(found, key=lambda d: (-round(d[1][3] / 20), d[1][0]))


def _round_dots(glyph, source, slope, xheight):
    have, want = dots(glyph), dots(source)
    if not have or len(have) != len(want):
        return False
    if not all(ROUND[0] < (b[2] - b[0]) / (b[3] - b[1]) < ROUND[1] for _, b in want):
        return False
    made = []
    for (c, b), (s, sb) in zip(have, want):
        k = math.sqrt(_area(c) / _area(s))
        if glyph.name in TALLEST:
            k = min(k, TALLEST[glyph.name] / (sb[3] - sb[1]))
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        sx, sy = (sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2
        half = k * (sb[3] - sb[1]) / 2
        made.append((c, s, k, cx, cy, sx, sy, b[1] - (cy - half), b[3] - (cy + half)))
    # on the baseline: that dot's bottom kept; above the x-height: the top
    # of the highest kept; the glyph's other dots moved alike
    if any(b[1] <= BASELINE for _, b in have):
        dy = max((m[7] for m, (_, b) in zip(made, have) if b[1] <= BASELINE), key=abs)
    elif all(b[1] >= xheight for _, b in have):
        dy = max(zip(made, have), key=lambda d: d[1][1][3])[0][8]
    else:
        dy = 0
    for c, s, k, cx, cy, sx, sy, _, _ in made:
        new = deepcopy(s)
        for p in new.points:
            y = cy + dy + k * (p.y - sy)
            p.x = round(cx + dy * slope + k * (p.x - sx))
            p.y = round(y)
        c.points[:] = new.points
        if slope:
            # the Italic's dot, scaled up, runs past its nodes: split it there
            from italic_contours import _add_extrema

            _add_extrema(c.points, lambda x, y: True)
    return True


def finish(font):
    style = SOURCE.get(font.info.styleName)
    if not style:
        return []
    source = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    slope = math.tan(math.radians(-(font.info.italicAngle or 0)))
    changed = []
    for name in sorted(font.keys()):
        if name in OWNED.get(font.info.styleName, ()) or name not in source or not font[name].contours:
            continue
        if _round_dots(font[name], source[name], slope, font.info.xHeight):
            changed.append(name)
    return changed
