"""The README's specimen image: lines set in the four built styles, drawn as
vector paths (no font needed to view it), on a white ground.

    python scripts/specimen.py [--out docs/specimen.svg]

Needs the built OpenType fonts (make otf).
"""
import argparse
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "fonts" / "otf" / "MyiaDidot-{}.otf"

# (style, size in px, features, text, gap after in px)
LINES = [
    ("Regular", 84, {}, "Myia Didot", 14),
    ("Italic", 26, {}, "A Didot for Latin, Greek and Cyrillic, in four styles with true small caps", 22),
    ("Regular", 38, {}, "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν", 10),
    ("Italic", 38, {}, "Quousque tandem abutere, Catilina, patientia nostra?", 10),
    ("Bold", 38, {}, "Съешь же ещё этих мягких французских булок", 10),
    ("BoldItalic", 38, {}, "Ça déjà, Łódź, Tiếng Việt, Ŋgɔ, Ɛʋe, ẞTRASSE", 18),
    ("Regular", 30, {"smcp": True, "onum": True}, "Small Capitals & Old-style Figures 1234567890", 8),
    ("Italic", 30, {"smcp": True, "onum": True}, "Italic Small Capitals 1789 & 1848", 8),
    ("Bold", 30, {"c2sc": True, "smcp": True}, "BOLD SMALL CAPITALS · ΑΒΓΔ · АБВГД", 8),
]
WIDTH, MARGIN = 1200, 40


def draw(out, style, size, features, text, x, base):
    path = str(FONT).format(style)
    tt = TTFont(path)
    gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
    upm = tt["head"].unitsPerEm
    font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, **features})
    k = size / upm
    d = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = SVGPathPen(gs)
        gs[order[info.codepoint]].draw(TransformPen(pen, (k, 0, 0, -k, x + pos.x_offset * k, base - pos.y_offset * k)))
        d.append(pen.getCommands())
        x += pos.x_advance * k
    out.append(f'<path d="{" ".join(d)}" fill="#111"/>')
    return x


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(ROOT / "docs" / "specimen.svg"))
    args = ap.parse_args()
    body, y = [], MARGIN
    for style, size, features, text, gap in LINES:
        y += size
        right = draw(body, style, size, features, text, MARGIN, y)
        if right > WIDTH - MARGIN:
            raise SystemExit(f"too long at {size}px: {text}")
        y += size * 0.32 + gap
    height = round(y + MARGIN - 10)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
           '<title>Myia Didot specimen</title>',
           f'<rect width="{WIDTH}" height="{height}" fill="#ffffff"/>', *body, "</svg>"]
    Path(args.out).write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
