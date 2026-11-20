"""bi_colour.py: where the Bold Italic is darker or lighter than its weight explains.

    python scripts/quality/bi_colour.py [--out build/bi-review/colour.md]

Per letter (a-z, the common Cyrillic and Greek lowercase, A-Z): the ink's share of
the advance x x-height box ("colour"; capitals: x cap height) in the Italic and
the Bold Italic, and their ratio. The Bold's ratio to the Regular is the upright
reference. A letter whose ratio stands far from the median of its set (in the
Bold Italic against the Italic) is one the emboldening made darker or lighter than
the others: a dark knot at a join, a filled aperture, or a thin one. Candidates
for the designer's eye, not verdicts (CLAUDE.md: the tools find candidates).
Reads sources/ only; writes the table.
"""

import argparse
import statistics
from pathlib import Path

import ufoLib2
from fontTools.pens.areaPen import AreaPen

ROOT = Path(__file__).resolve().parent.parent.parent
SETS = {
    "latin lower": "abcdefghijklmnopqrstuvwxyz",
    "latin upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "cyrillic lower": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "greek lower": "αβγδεζηθικλμνξοπρστυφχψω",
}


def colour(font, ch, height):
    g = font[next(x.name for x in font if x.unicode == ord(ch))]
    pen = AreaPen(font)
    g.draw(pen)
    return abs(pen.value) / (g.width * height) if g.width else None


def heights(font):
    return font.info.xHeight, font.info.capHeight


def table(a, b):
    """{set: [(char, colour a, colour b, ratio)]} of two fonts"""
    xa, ca = heights(a)
    xb, cb = heights(b)
    out = {}
    for name, chars in SETS.items():
        rows = []
        for ch in chars:
            h = (ca, cb) if name.endswith("upper") else (xa, xb)
            try:
                ka, kb = colour(a, ch, h[0]), colour(b, ch, h[1])
            except StopIteration:
                continue
            if ka and kb:
                rows.append((ch, ka, kb, kb / ka))
        out[name] = rows
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "build/bi-review/colour.md"))
    a = ap.parse_args()
    fonts = {n: ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{n}.ufo") for n in ("Regular", "Italic", "Bold", "BoldItalic")}
    bi, up = table(fonts["Italic"], fonts["BoldItalic"]), table(fonts["Regular"], fonts["Bold"])
    lines = ["# Bold Italic colour against the Italic", "",
             "colour = ink / (advance x x-height; capitals: cap height). ratio = Bold Italic / Italic;",
             "dev = the ratio against its set's median, in percent; the Bold / Regular ratio beside it.", ""]
    flagged = []
    for name, rows in bi.items():
        med = statistics.median(r[3] for r in rows)
        upm = statistics.median(r[3] for r in up[name]) if up[name] else None
        upr = {r[0]: r[3] for r in up[name]}
        lines += [f"## {name} (median ratio {med:.2f}; the Bold's {upm:.2f})" if upm else f"## {name} (median {med:.2f})", "",
                  "| letter | Italic | Bold Italic | ratio | dev % | Bold/Regular |", "|---|---|---|---|---|---|"]
        for ch, ka, kb, r in sorted(rows, key=lambda x: -abs(x[3] / med - 1)):
            dev = (r / med - 1) * 100
            lines.append(f"| {ch} | {ka:.3f} | {kb:.3f} | {r:.2f} | {dev:+.0f} | "
                         f"{upr[ch]:.2f} |" if ch in upr else f"| {ch} | {ka:.3f} | {kb:.3f} | {r:.2f} | {dev:+.0f} | |")
            if abs(dev) >= 8:
                flagged.append((ch, dev))
        lines.append("")
    lines.append("flagged (|dev| >= 8 %): " + " ".join(f"{c} {d:+.0f}" for c, d in flagged))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{a.out}: flagged " + " ".join(f"{c}{d:+.0f}" for c, d in flagged))


if __name__ == "__main__":
    main()
