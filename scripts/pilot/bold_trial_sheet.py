#!/usr/bin/env python3
"""The review sheet for F4's trial (docs/claude/bold.md, bold_trial.py):
today's Bold, the trial Bolds and Old Standard Bold under each other at
144 pt (less where more than five rows share the page), then a paragraph of each at 12 pt.

    .venv/bin/python -I scripts/pilot/bold_trial_sheet.py OUT.pdf "label=PATH" ...

PATH is a UFO or a TTF. Set from the outlines and advances alone: no
kerning and no features in any row, so that the rows differ only in the
letters and their side space.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

BIG = ("naegso mhur", "vwxk HOXK r", "OCGQ rare for")
SIZE, TEXT = 144, 12
PARAGRAPH = ("In the morning the engineers examined a thousand numbers, human and humane; "
             "noon sun on linen, a minimum of room, hammer and anvil. Have we any oxen now? "
             "MAXIMUM HOOK, KNOX AND HOMO; Grave goose eggs are a season's message.")
W, H = 1190, 842  # A3 across


class Face:
    def __init__(self, path):
        if str(path).endswith(".ufo"):
            font = ufoLib2.Font.open(path)
            self.upm = font.info.unitsPerEm
            self.glyphs = font
            self.cmap = {u: g.name for g in font for u in g.unicodes}
            self.width = lambda n: font[n].width
        else:
            tt = TTFont(path)
            self.upm = tt["head"].unitsPerEm
            self.glyphs = tt.getGlyphSet()
            self.cmap = tt.getBestCmap()
            self.width = lambda n: self.glyphs[n].width

    def line(self, text, x, y, size):
        scale = size / self.upm
        d, pos = [], 0
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name is None:
                continue
            rec = DecomposingRecordingPen(self.glyphs)
            self.glyphs[name].draw(rec)
            pen = SVGPathPen(None, ntos=lambda v: f"{v:.2f}")
            rec.replay(TransformPen(pen, (scale, 0, 0, -scale, x + pos * scale, y)))
            d.append(pen.getCommands())
            pos += self.width(name)
        return f'<path d="{" ".join(d)}"/>', pos * scale


def label(x, y, s, size=8):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="#555">{s}</text>'


def svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>{"".join(body)}</svg>')


def wrap(face, text, size, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and face.line(trial, 0, 0, size)[1] > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("faces", nargs="+", help="label=PATH")
    args = ap.parse_args()
    faces = [(lab, Face(path)) for lab, path in (f.split("=", 1) for f in args.faces)]
    pages = []
    step = (H - 50) / len(faces)
    size = round(min(SIZE, step * 0.95))
    for text in BIG:
        body = [label(30, 22, f"F4's trial: the upright Bold, {size} pt, no kerning", 10)]
        for i, (lab, face) in enumerate(faces):
            y = 40 + step * i
            body.append(label(30, y + 4, lab))
            body.append(face.line(text, 30, y + step * 0.78, size)[0])
        pages.append(svg(body))
    body = [label(30, 22, f"F4's trial: the upright Bold, {TEXT} pt, no kerning", 10)]
    cols = 3
    cw = (W - 60) / cols - 20
    for i, (lab, face) in enumerate(faces):
        x = 30 + (i % cols) * (cw + 20)
        y = 50 + (i // cols) * 180
        body.append(label(x, y, lab))
        for k, ln in enumerate(wrap(face, PARAGRAPH, TEXT, cw)):
            body.append(face.line(ln, x, y + 20 + k * TEXT * 1.3, TEXT)[0])
    pages.append(svg(body))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, page in enumerate(pages):
        f = out.with_name(f"{out.stem}-{i}.svg")
        f.write_text(page)
        pdf = f.with_suffix(".pdf")
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(f)], check=True)
        f.unlink()
        parts.append(pdf)
    subprocess.run(["pdfunite", *map(str, parts), str(out)], check=True)
    for p in parts:
        p.unlink()
    print(f"{out}: {len(pages)} pages", file=sys.stderr)


if __name__ == "__main__":
    main()
