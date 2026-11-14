"""Render fixed HarfBuzz-shaped specimens as standalone SVG proof sheets.

    python scripts/proof_svg.py FONT.otf [FONT.otf ...] --out build/proofs/ci

Glyphs are drawn as paths from the font, so the proof does not depend on a
browser having Myia Didot installed. The SVGs are intended for visual review,
not pixel-exact pass/fail comparisons.
"""

import argparse
import html
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SCALE = 0.02
WIDTH = 1800
MARGIN = 70
ROW_HEIGHT = 104
SAMPLES = [
    ("Latin text and punctuation", "AVATAR. To Wa: kerning, fi ffi fl.", {}, None, None),
    ("Kerning review pairs", "Th Gr uf ga if Re va gh wa ay ut fr", {}, "latn", "en"),
    ("Discretionary ligatures", "ct st sp", {"dlig": True}, None, None),
    ("Old-style figures", "0123456789 · 1789", {"onum": True}, None, None),
    ("Proportional lining figures (default)", "0123456789 · 1789 · 1711", {}, None, None),
    ("Tabular figures", "0123456789 · 1789 · 1711", {"tnum": True}, None, None),
    ("Slashed zero", "1 000 · 2050 · 0x00F0", {"zero": True}, None, None),
    ("Ordinals, inferiors", "1º 2ª No 5 · H2O CO2", {"ordn": True, "sinf": True}, None, None),
    ("Capital spacing", "MYIA DIDOT · ΕΛΛΗΝΙΚΑ · КИРИЛЛИЦА", {"cpsp": True}, None, None),
    ("Fractions", "1/2   3/4   12/345", {"frac": True}, None, None),
    ("Small capitals", "Myia Didot · Small Capitals", {"smcp": True}, None, None),
    ("Romanian localized forms", "Știință, țară, ŞşŢţ", {}, "latn", "ro"),
    ("Polytonic Greek", "Ἄνθρωπος · ᾠδή · ἑλληνικὴ γραφή", {}, "grek", "el"),
    ("Cyrillic", "Гражданский шрифт · Љубав · ђак", {}, "cyrl", "ru"),
    ("Stacked and Vietnamese accents", "Ấ ấ · Ủ ặ ộ", {}, "latn", "vi"),
]


def shape(font, ttfont, text, features=None, script=None, language=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if script:
        buf.script = script
    if language:
        buf.language = language
    hb.shape(font, buf, features or {})
    order = ttfont.getGlyphOrder()
    return [(order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions, strict=True)]


def glyph_paths(glyphset, shaped, baseline):
    x, paths = 0, []
    for name, advance, x_offset, y_offset in shaped:
        pen = SVGPathPen(glyphset)
        transform = (
            SCALE, 0, 0, -SCALE,
            MARGIN + (x + x_offset) * SCALE,
            baseline - y_offset * SCALE,
        )
        glyphset[name].draw(TransformPen(pen, transform))
        d = pen.getCommands()
        if d:
            paths.append(f'<path d="{d}"/>')
        x += advance
    return "\n".join(paths), x * SCALE


def render(path, output):
    ttfont = TTFont(path)
    glyphset = ttfont.getGlyphSet()
    hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    style = path.stem.removeprefix("MyiaDidot-")
    height = 130 + ROW_HEIGHT * len(SAMPLES)
    parts = [
        (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
         f'viewBox="0 0 {WIDTH} {height}">'),
        '<rect width="100%" height="100%" fill="#fff"/>',
        ('<style>text{font-family:sans-serif;fill:#444}.glyph{fill:#171717}'
         '.rule{stroke:#ddd;stroke-width:1}</style>'),
        (f'<text x="{MARGIN}" y="48" font-size="28" font-weight="600">'
         f'Myia Didot {html.escape(style)} · Phase 3 specimen</text>'),
    ]
    for index, sample in enumerate(SAMPLES):
        label, text, features, script, language = sample
        top = 76 + index * ROW_HEIGHT
        baseline = top + 67
        parts.append(f'<text x="{MARGIN}" y="{top + 15}" font-size="13">'
                     f'{html.escape(label)}</text>')
        shaped = shape(hbfont, ttfont, text, features, script, language)
        paths, advance = glyph_paths(glyphset, shaped, baseline)
        if advance > WIDTH - 2 * MARGIN:
            raise ValueError(f"specimen row is too wide for {WIDTH}px SVG: {label}")
        parts.append(f'<g class="glyph">{paths}</g>')
        parts.append(f'<line class="rule" x1="{MARGIN}" y1="{top + ROW_HEIGHT - 5}" '
                     f'x2="{WIDTH - MARGIN}" y2="{top + ROW_HEIGHT - 5}"/>')
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for font in args.fonts:
        target = args.out / f"{font.stem}.svg"
        render(font, target)
        print(target)


if __name__ == "__main__":
    main()
