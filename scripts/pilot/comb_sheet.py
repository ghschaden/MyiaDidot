"""A sheet of curvature combs, one column per UFO: each glyph's outline
with its curvature drawn as teeth along the inside normal (COMB units of
tooth per 1/1000 units of curvature), its nodes as dots.

    .venv/bin/python -I scripts/pilot/comb_sheet.py OUT.png "n h a" A.ufo B.ufo ...

A study tool (FONT-DESIGN.md, Bold Italic from strokes), not part of the build.
"""
import os
import sys
from pathlib import Path

import numpy as np
import skia
import ufoLib2

sys.path[:0] = [str(Path(__file__).parent), str(Path(__file__).parents[1])]
from g2_measure import segments  # noqa: E402
from node_sheet import path_of  # noqa: E402

SCALE = float(os.environ.get("SCALE", 0.45))
COMB = float(os.environ.get("COMB", 10))  # units of tooth per 1/1000 of curvature
CLAMP = 150  # units: a longer tooth is cut there
CELL, ROW, BASE = int(1300 * SCALE), int(1250 * SCALE), int(1000 * SCALE)


def comb(seg, n=40):
    """samples of a cubic: points, unit normals (left), curvature"""
    t = np.linspace(0, 1, n)[:, None]
    u = 1 - t
    p = seg
    pt = u ** 3 * p[0] + 3 * u * u * t * p[1] + 3 * u * t * t * p[2] + t ** 3 * p[3]
    d1 = 3 * u * u * (p[1] - p[0]) + 6 * u * t * (p[2] - p[1]) + 3 * t * t * (p[3] - p[2])
    d2 = 6 * u * (p[2] - 2 * p[1] + p[0]) + 6 * t * (p[3] - 2 * p[2] + p[1])
    sp = np.linalg.norm(d1, axis=1)
    k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum(sp, 1e-9) ** 3
    nrm = np.stack([-d1[:, 1], d1[:, 0]], axis=1) / np.maximum(sp, 1e-9)[:, None]
    return pt, nrm, k


def main():
    out, names, ufos = sys.argv[1], sys.argv[2].split(), sys.argv[3:]
    fonts = [ufoLib2.Font.open(u) for u in ufos]
    cmaps = [{chr(u): g.name for g in f for u in g.unicodes} for f in fonts]
    W, H = CELL * len(fonts) + 40, ROW * len(names) + 40
    surface = skia.Surface(W, H)
    cv = surface.getCanvas()
    cv.clear(skia.ColorWHITE)
    font = skia.Font(skia.Typeface('DejaVu Sans'), 14)
    ink = skia.Paint(Color=skia.ColorBLACK, AntiAlias=True)
    line = skia.Paint(Color=skia.Color(40, 40, 40), Style=skia.Paint.kStroke_Style, StrokeWidth=1, AntiAlias=True)
    fill = skia.Paint(Color=skia.Color(232, 232, 232), AntiAlias=True)
    tooth = skia.Paint(Color=skia.Color(230, 120, 60), StrokeWidth=1, AntiAlias=True)
    rim = skia.Paint(Color=skia.Color(200, 60, 30), Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, AntiAlias=True)
    node = skia.Paint(Color=skia.Color(40, 90, 200), AntiAlias=True)
    for c, u in enumerate(ufos):
        cv.drawString(Path(u).parent.name + "/" + Path(u).stem[:28], 20 + c * CELL, 18, font, ink)
    for r, ch in enumerate(names):
        for c, (f, cm) in enumerate(zip(fonts, cmaps)):
            name = cm.get(ch) or cmaps[0].get(ch, ch)
            if name not in f:
                continue
            g = f[name]
            ox, oy = 20 + c * CELL + 20, 30 + r * ROW + BASE
            P = lambda q, ox=ox, oy=oy: (ox + q[0] * SCALE, oy - q[1] * SCALE)  # noqa: E731
            cv.drawPath(path_of(g, SCALE, ox, oy), fill)
            cv.drawPath(path_of(g, SCALE, ox, oy), line)
            for segs in segments(g):
                for s in segs:
                    if len(s) != 4:
                        cv.drawCircle(*P(s[0]), 2.5, node)
                        continue
                    pt, nrm, k = comb(s)
                    # teeth on the side the curve bends to (inside), scaled
                    tip = pt - nrm * np.clip(k * 1000 * COMB, -CLAMP, CLAMP)[:, None]
                    for a, b in zip(pt, tip):
                        cv.drawLine(*P(a), *P(b), tooth)
                    pa = skia.Path()
                    pa.moveTo(*P(tip[0]))
                    for q in tip[1:]:
                        pa.lineTo(*P(q))
                    cv.drawPath(pa, rim)
                    cv.drawCircle(*P(s[0]), 2.5, node)
            count = sum(1 for cont in g.contours for q in cont.points if q.type)
            cv.drawString(f"{ch} {count}", ox, oy + 60, font, ink)
    surface.makeImageSnapshot().save(out, skia.kPNG)


if __name__ == "__main__":
    main()
