"""bi_sheet.py: the Bold Italic's words beside the Italic's, as a PDF.

    python scripts/quality/bi_sheet.py [--out build/bi-review/bi-words.pdf] [WORD ...]

Each word or phrase shaped with HarfBuzz from fonts/otf (`make otf`; kerning and
features on) at 64 pt and again at 14 pt: one row for the Italic, one for the
Bold Italic, separate, never overlaid. The review's targets (internal white at g f
and the curved letters, dark knots at joins, terminal weight and reach, the
spacing of tight sequences): the words are chosen to hold them. For the
designer's eye; the colour table beside is scripts/quality/bi_colour.py.
"""

import argparse
import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent.parent
WORDS = ["figure grafting offering", "giraffe gift fragile", "agent gaze eggs", "cheese seeks fuzzy",
         "hymn rhythm jazz", "Bold Italic emphasis", "a gig of fifty offices", "Ἑλλάδα γράφω",
         "Жизнь с юга", "Größe, Fuß, Œuvre", "şğıİ Việt Nam"]


def line(path, text, size, x0, y, k=None):
    """the SVG paths of text shaped by the font at path; the width reached"""
    face = hb.Face(hb.Blob.from_file_path(str(path)))
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(path)
    gs, order, upem = tt.getGlyphSet(), tt.getGlyphOrder(), tt["head"].unitsPerEm
    s = size / upem
    x, out = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = SVGPathPen(gs)
        gs[order[info.codepoint]].draw(TransformPen(pen, (s, 0, 0, -s, x0 + (x + pos.x_offset) * s, y - pos.y_offset * s)))
        if pen.getCommands():
            out.append(f'<path d="{pen.getCommands()}"/>')
        x += pos.x_advance
    return "".join(out), x * s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("words", nargs="*")
    ap.add_argument("--out", default=str(ROOT / "build/bi-review/bi-words.pdf"))
    a = ap.parse_args()
    words = a.words or WORDS
    paths = {n: ROOT / f"fonts/otf/MyiaDidot-{n}.otf" for n in ("Italic", "BoldItalic")}
    label = {"Italic": "Italic", "BoldItalic": "Bold Italic"}
    W, pad = 1100, 30
    body, y = [], 30
    body.append(f'<text x="{pad}" y="{y}" font-family="DejaVu Sans" font-size="13" font-weight="bold">'
                "Bold Italic against the Italic: words at 64 pt, then 14 pt (HarfBuzz, kerning on)</text>")
    y += 18
    for size in (64, 14):
        for w in words:
            for n in ("Italic", "BoldItalic"):
                y += size * (1.05 if size > 20 else 1.5)
                svg, width = line(paths[n], w, size, pad + 80, y)
                body.append(f'<text x="{pad}" y="{y}" font-family="DejaVu Sans" font-size="8" fill="#666">{label[n]}</text>')
                body.append(f'<g fill="#000">{svg}</g>')
            y += size * 0.35
        y += 24
    H = y + 20
    svg_doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}">'
               f'<rect width="100%" height="100%" fill="#fff"/>' + "".join(body) + "</svg>")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    svg = out.with_suffix(".svg")
    svg.write_text(svg_doc, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(out), str(svg)], check=True)
    svg.unlink()
    print(out)


if __name__ == "__main__":
    main()
