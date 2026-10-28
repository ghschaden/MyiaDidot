"""A sheet of glyphs with their nodes, one column per UFO: each glyph as
an outline with on-curve nodes (squares: corners, circles: smooth) and
handles, its node count under it, and filled small beside it.

    .venv/bin/python -I scripts/pilot/node_sheet.py OUT.png "a b c" A.ufo B.ufo ...

A study tool (FONT-DESIGN.md, Bold Italic from strokes), not part of the build.
"""
import os
import sys
from pathlib import Path

import skia
import ufoLib2

SCALE = float(os.environ.get("SCALE", 0.30))  # pixels per unit
CELL = int(1400 * SCALE)  # pixels per glyph, outline view (wide)
ROW = int(1750 * SCALE)  # and tall
SMALL = 0.06        # filled view
BASE = int(1250 * SCALE)  # baseline from a cell's top


def path_of(glyph, scale, ox, oy):
    p = skia.Path()
    for c in glyph.contours:
        pts = c.points
        n = len(pts)
        start = next(i for i, q in enumerate(pts) if q.type)
        P = lambda q: (ox + q.x * scale, oy - q.y * scale)  # noqa: E731
        p.moveTo(*P(pts[start]))
        buf = []
        for m in range(1, n + 1):
            q = pts[(start + m) % n]
            if not q.type:
                buf.append(q)
                continue
            if q.type == "line" or not buf:
                p.lineTo(*P(q))
            elif len(buf) == 2:
                p.cubicTo(*P(buf[0]), *P(buf[1]), *P(q))
            else:
                p.quadTo(*P(buf[0]), *P(q))
            buf = []
        p.close()
    return p


def main():
    out, names, ufos = sys.argv[1], sys.argv[2].split(), sys.argv[3:]
    fonts = [ufoLib2.Font.open(u) for u in ufos]
    cmaps = [{chr(u): g.name for g in f for u in g.unicodes} for f in fonts]
    W, H = CELL * len(fonts) + 40, ROW * len(names) + 40 + 110 * len(fonts)
    surface = skia.Surface(W, H)
    cv = surface.getCanvas()
    cv.clear(skia.ColorWHITE)
    font = skia.Font(skia.Typeface('DejaVu Sans'), 14)
    ink = skia.Paint(Color=skia.ColorBLACK, AntiAlias=True)
    line = skia.Paint(Color=skia.Color(40, 40, 40), Style=skia.Paint.kStroke_Style, StrokeWidth=1, AntiAlias=True)
    handle = skia.Paint(Color=skia.Color(120, 160, 220), StrokeWidth=1, AntiAlias=True)
    node = skia.Paint(Color=skia.Color(220, 60, 40), AntiAlias=True)
    off = skia.Paint(Color=skia.Color(60, 110, 200), AntiAlias=True)
    fill = skia.Paint(Color=skia.Color(225, 225, 225), AntiAlias=True)
    for c, u in enumerate(ufos):
        cv.drawString(Path(u).stem[:28], 20 + c * CELL, 18, font, ink)
    for r, ch in enumerate(names):
        for c, (f, cm) in enumerate(zip(fonts, cmaps)):
            name = cm.get(ch) or cmaps[0].get(ch, ch)
            if name not in f:
                continue
            g = f[name]
            ox, oy = 20 + c * CELL + 20, 30 + r * ROW + BASE
            cv.drawPath(path_of(g, SCALE, ox, oy), fill)
            cv.drawPath(path_of(g, SCALE, ox, oy), line)
            for cont in g.contours:
                pts = cont.points
                n = len(pts)
                for i, q in enumerate(pts):
                    x, y = ox + q.x * SCALE, oy - q.y * SCALE
                    if q.type:
                        for nb in (pts[i - 1], pts[(i + 1) % n]):
                            if not nb.type:
                                cv.drawLine(x, y, ox + nb.x * SCALE, oy - nb.y * SCALE, handle)
                        if q.smooth:
                            cv.drawCircle(x, y, 3, node)
                        else:
                            cv.drawRect(skia.Rect(x - 3, y - 3, x + 3, y + 3), node)
                    else:
                        cv.drawCircle(x, y, 2, off)
            count = sum(1 for cont in g.contours for q in cont.points if q.type)
            cv.drawString(f"{ch} {count}", ox, oy + 70, font, ink)
            cv.drawPath(path_of(g, SMALL, ox + CELL - 90, oy + 60), ink)
    # the glyphs filled in a row per UFO, at text size
    for c, (f, cm) in enumerate(zip(fonts, cmaps)):
        x, y = 20, ROW * len(names) + 110 * (c + 1)
        for ch in names:
            name = cm.get(ch) or cmaps[0].get(ch, ch)
            if name in f:
                cv.drawPath(path_of(f[name], 0.07, x, y), ink)
                x += f[name].width * 0.07
        cv.drawString(Path(ufos[c]).stem[:28], x + 20, y, font, ink)
    surface.makeImageSnapshot().save(out, skia.kPNG)


if __name__ == "__main__":
    main()
