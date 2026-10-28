"""Words set from glyph outlines, one line per font (UFO, TTF or OTF), for
comparing weights at text size; advances only, no kerning.

    .venv/bin/python -I scripts/pilot/text_strip.py OUT.png "words" FONT ...

A study tool (FONT-DESIGN.md, Bold Italic from strokes), not part of the build.
"""
import sys
from pathlib import Path

import skia
import ufoLib2
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

SIZE = int(__import__("os").environ.get("SIZE", 64))  # pixels per em


class SkiaPen(BasePen):
    def __init__(self, path, scale, ox, oy):
        super().__init__(None)
        self.p, self.s, self.ox, self.oy = path, scale, ox, oy

    def _t(self, pt):
        return self.ox + pt[0] * self.s, self.oy - pt[1] * self.s

    def _moveTo(self, pt):
        self.p.moveTo(*self._t(pt))

    def _lineTo(self, pt):
        self.p.lineTo(*self._t(pt))

    def _curveToOne(self, a, b, c):
        self.p.cubicTo(*self._t(a), *self._t(b), *self._t(c))

    def _qCurveToOne(self, a, b):
        self.p.quadTo(*self._t(a), *self._t(b))

    def _closePath(self):
        self.p.close()


def glyphs(path):
    """char -> (draw(pen), advance), units per em"""
    if path.endswith(".ufo"):
        f = ufoLib2.Font.open(path)
        cm = {chr(u): g.name for g in f for u in g.unicodes}
        cm.update({n: n for n in f.keys() if len(n) == 1 and n not in cm})
        return {c: (drawer(f, n), f[n].width) for c, n in cm.items()}, f.info.unitsPerEm or 2048
    t = TTFont(path)
    gs, hm = t.getGlyphSet(), t["hmtx"]
    return {chr(u): (drawer(gs, n), hm[n][0]) for u, n in t.getBestCmap().items()}, t["head"].unitsPerEm


def drawer(gs, name):
    """name's outline, its components decomposed"""
    def draw(pen):
        rec = DecomposingRecordingPen(gs)
        gs[name].draw(rec)
        rec.replay(pen)
    return draw


def main():
    out, text, fonts = sys.argv[1], sys.argv[2], sys.argv[3:]
    line = int(SIZE * 1.25)
    surface = skia.Surface(int(SIZE * 0.6 * len(text)) + 360, line * len(fonts) + 30)
    cv = surface.getCanvas()
    cv.clear(skia.ColorWHITE)
    ink = skia.Paint(Color=skia.ColorBLACK, AntiAlias=True)
    label = skia.Font(skia.Typeface("DejaVu Sans"), 13)
    for r, font in enumerate(fonts):
        gl, upm = glyphs(font)
        s = SIZE / upm
        x, y = 20.0, 20 + line * (r + 1) - SIZE * 0.3
        path = skia.Path()
        for ch in text:
            if ch in gl:
                draw, adv = gl[ch]
                draw(SkiaPen(path, s, x, y))
                x += adv * s
            else:
                x += SIZE * 0.3
        cv.drawPath(path, ink)
        cv.drawString(Path(font).stem, x + 20, y, label, ink)
    surface.makeImageSnapshot().save(out, skia.kPNG)


if __name__ == "__main__":
    main()
