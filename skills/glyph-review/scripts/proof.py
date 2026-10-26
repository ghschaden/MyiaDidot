"""Read-only, focused source-outline and shaped-text proofs for Myia Didot."""

import argparse
import json
import sys
from html import escape
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from build_support import atomic_output, content_hash
from font_builds import compiled_variant
from font_shaping import Shaper

EM = 112
TEXT_EM = 24
MARGIN = 28


def label(x, y, text, size=13, color="#444"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color}">'
            f'{escape(str(text))}</text>')


def outline(glyphset, name, x, baseline, scale):
    pen = SVGPathPen(glyphset)
    glyphset[name].draw(pen)
    return (f'<path d="{pen.getCommands()}" fill="#171717" '
            f'transform="translate({x:.3f},{baseline:.3f}) scale({scale:.6f},{-scale:.6f})"/>')


def bounds(font, name):
    box = font[name].getBounds(font)
    return tuple(box) if box is not None else (0, 0, 0, 0)


def render(source, names, output, *, before=None, texts=(), language="en", script=None,
           features=None, anchors=False):
    paths = [("Before", Path(before))] if before else []
    paths.append(("Current", Path(source)))
    output = Path(output)
    if any(output.resolve().is_relative_to(path.resolve()) for _, path in paths) or \
            output.resolve().is_relative_to((ROOT / "sources").resolve()):
        raise ValueError("proof output must be outside source UFOs and sources/")
    identities = {path: content_hash(path) for _, path in paths}
    fonts = [(title, path, ufoLib2.Font.open(path, lazy=False)) for title, path in paths]
    missing = sorted(set(names) - set(fonts[-1][2].keys()))
    if missing:
        raise ValueError("glyphs missing from current UFO: " + ", ".join(missing))
    if not names:
        raise ValueError("choose at least one glyph")

    # Work in em coordinates so different UPMs retain the same physical scale.
    top, bottom, extent = 1.05, -.3, 1.0
    for _, _, font in fonts:
        upm = font.info.unitsPerEm
        if not upm or upm <= 0:
            raise ValueError("UFO must have a positive unitsPerEm")
        for name in names:
            if name not in font:
                continue
            x0, y0, x1, y1 = bounds(font, name)
            top, bottom = max(top, y1 / upm), min(bottom, y0 / upm)
            extent = max(extent, (max(x1, font[name].width) - min(x0, 0)) / upm)
            if anchors:
                for anchor in font[name].anchors:
                    top, bottom = max(top, anchor.y / upm), min(bottom, anchor.y / upm)
    column = max(420, extent * EM + 2 * MARGIN + (220 if anchors else 0))
    shaped = []
    for title, path, _ in fonts:
        if not texts:
            continue
        compiled = compiled_variant(path, "test_otf")
        shaper = Shaper(compiled)
        with TTFont(compiled) as tt:
            glyphset = tt.getGlyphSet()
            scale = TEXT_EM / tt["head"].unitsPerEm
            for text in texts:
                run = shaper.shape(text, features, language=language, script=script)
                x, pieces = 0, []
                for name, advance, dx, dy in run:
                    pen = BoundsPen(glyphset)
                    glyphset[name].draw(pen)
                    if pen.bounds:
                        _, y0, _, y1 = pen.bounds
                        top = max(top, (y1 + dy) / tt["head"].unitsPerEm)
                        bottom = min(bottom, (y0 + dy) / tt["head"].unitsPerEm)
                    pieces.append(outline(glyphset, name, x + dx * scale, -dy * scale, scale))
                    x += advance * scale
                # Bounds may include overhang; leave an em at each end.
                column = max(column, x + 2 * TEXT_EM + 2 * MARGIN)
                shaped.append((title, text, pieces))

    width = max(640, column * len(fonts))
    row_height = 82 + (top - bottom) * EM + (top - bottom) * TEXT_EM
    if anchors:
        row_height = max(row_height, 82 + 12 * max(len(font[name].anchors) for _, _, font in fonts
                                                  for name in names if name in font))
    text_height = max(100, 52 + (top - bottom) * TEXT_EM)
    height = 120 + row_height * len(names) + text_height * len(shaped)
    parts = [(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
              f'viewBox="0 0 {width:.2f} {height:.2f}">'),
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>text{font-family:sans-serif}.guide{stroke:#ccd5df;stroke-width:1}</style>',
             label(MARGIN, 30, "Glyph review · source outlines", 21),
             label(MARGIN, 53, f"Enlarged {EM}px/em; small {TEXT_EM}px/em · not a hinting proof")]
    for col, (title, path, font) in enumerate(fonts):
        left = col * column + MARGIN
        parts.append(label(left, 80, f"{title}: {font.info.styleName or path.stem} · UPM {font.info.unitsPerEm}", 15))
        parts.append(label(left, 100, path.name))
        scale = EM / font.info.unitsPerEm
        for index, name in enumerate(names):
            row_top = 120 + index * row_height
            parts.append(label(left, row_top + 15, name, 15))
            if name not in font:
                parts.append(label(left, row_top + 45, "Not present in this source", color="#a21b1b"))
                continue
            glyph = font[name]
            x0, y0, x1, y1 = bounds(font, name)
            x = left + max(0, -x0 * scale)
            baseline = row_top + 46 + top * EM
            parts.append(label(left, row_top + 34,
                               f"advance {glyph.width:g}; bounds ({x0:g}, {y0:g}, {x1:g}, {y1:g})", 12))
            for y in (0, font.info.xHeight, font.info.capHeight):
                if y is not None:
                    py = baseline - y * scale
                    parts.append(f'<line class="guide" x1="{left}" y1="{py}" '
                                 f'x2="{left + column - 2 * MARGIN}" y2="{py}"/>')
            parts.append(outline(font, name, x, baseline, scale))
            if anchors:
                for anchor_index, anchor in enumerate(glyph.anchors):
                    ax, ay = x + anchor.x * scale, baseline - anchor.y * scale
                    parts.append(f'<path d="M{ax-3},{ay}h6 M{ax},{ay-3}v6" stroke="#b02738" fill="none"/>')
                    legend_x = left + extent * EM + 28
                    parts.append(label(legend_x, row_top + 54 + anchor_index * 12,
                                       f"{anchor.name or 'unnamed'} ({anchor.x:g}, {anchor.y:g})", 10, "#b02738"))
            small_scale = TEXT_EM / font.info.unitsPerEm
            small_baseline = baseline - bottom * EM + 18 + top * TEXT_EM
            copies = min(5, max(1, int((column - 2 * MARGIN) / max(TEXT_EM, glyph.width * small_scale))))
            for repeat in range(copies):
                parts.append(outline(font, name, left + max(0, -x0 * small_scale) + repeat *
                                     max(TEXT_EM, glyph.width * small_scale), small_baseline, small_scale))
    for index, (title, text, pieces) in enumerate(shaped):
        y = 120 + len(names) * row_height + index * text_height
        parts.append(label(MARGIN, y + 16, f"{title} · {language} · {features or {}} · {text}"))
        baseline = y + 38 + top * TEXT_EM
        parts.append(f'<g transform="translate({MARGIN + TEXT_EM},{baseline})">' + "".join(pieces) + "</g>")
    parts.append("</svg>")
    if any(content_hash(path) != identity for path, identity in identities.items()):
        raise ValueError("source changed while rendering the proof; retry from a stable source state")
    with atomic_output(output) as temporary:
        temporary.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ufo", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--glyphs", nargs="+", required=True)
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--language", default="en")
    parser.add_argument("--script")
    parser.add_argument("--features", default="{}", help="JSON object of HarfBuzz feature settings")
    parser.add_argument("--anchors", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        features = json.loads(args.features)
        if not isinstance(features, dict) or not all(isinstance(k, str) and isinstance(v, (bool, int))
                                                    for k, v in features.items()):
            raise ValueError("--features must be a JSON object with boolean or integer settings")
        render(args.ufo, args.glyphs, args.out, before=args.before, texts=args.text,
               language=args.language, script=args.script, features=features, anchors=args.anchors)
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    print(args.out)


if __name__ == "__main__":
    main()
