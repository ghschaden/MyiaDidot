"""A review sheet for scripts/italic_kerning.py: words set in the upright,
in the italic as it is kerned today, and in the italic with the computed
kerning; one page a weight, then both italics at text size.

    python scripts/italic_kerning_sheet.py OUT.pdf [--words "AVATAR Table ..."]

Set from the UFOs (outlines, advances, kerning by glyph and group; no
features, so no ligatures): the third column differs from the second only
in the pairs the rule computes. Under each word the pairs that changed,
today's value and the computed one; red where the rule drops the pair.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import italic_kerning  # noqa: E402
import kern_clear  # noqa: E402

WORDS = ("AVATAR TAYLOR VOYAGE ALTLY PYRAMID BYRON L’AVARE SALVO KOALA ACUTE DYNAMO RAYON "
         "Avenue Ayer Table Tchad Tag Yvonne Ravy kayak backcountry keen every yes "
         "why, luv, subxiphoid excel obvious abject Kyoto Atypical").split()
SIZE = 30  # points
TEXT = 12
W, H = 842, 595  # A4 across
PAIRS_PER_PAGE = 13


class Setter:
    def __init__(self, font, kerning=None):
        self.font = font
        self.kerning = font.kerning if kerning is None else kerning
        self.cmap = {u: g.name for g in font for u in g.unicodes}
        self.keys, _ = kern_clear.kern_lookup(font)
        self._d = {}

    def kern(self, a, b):
        return next((self.kerning[k] for k in self.keys(a, b) if k in self.kerning), 0)

    def path(self, name, x, y, scale):
        if name not in self._d:
            rec = DecomposingRecordingPen(self.font)
            self.font[name].draw(rec)
            self._d[name] = rec
        pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}")
        self._d[name].replay(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        return pen.getCommands()

    def line(self, text, x, y, size):
        """(svg path data, the advance in points, [(a, b, kerning)])"""
        scale = size / self.font.info.unitsPerEm
        names = [self.cmap[ord(c)] for c in text if ord(c) in self.cmap]
        d, pos, pairs = [], 0, []
        for i, n in enumerate(names):
            if i:
                k = self.kern(names[i - 1], n)
                pos += k
                pairs.append((names[i - 1], n, k))
            d.append(self.path(n, x + pos * scale, y, scale))
            pos += self.font[n].width
        return " ".join(d), pos * scale, pairs


def label(x, y, s, size=7, fill="#555"):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="sans-serif" font-size="{size}" fill="{fill}">{s}</text>'


def page(title, cols, words, first):
    """cols: [(heading, Setter)]; the last two are today's and the computed"""
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>', label(30, 24, title, 10, "#000")]
    colw = (W - 60) / len(cols)
    for i, (head, _) in enumerate(cols):
        s.append(label(30 + i * colw, 42, head, 8, "#000"))
    step = (H - 70) / PAIRS_PER_PAGE
    for r, word in enumerate(words):
        y = 50 + (r + 0.62) * step
        set_ = [c.line(word, 30 + i * colw, y, SIZE) for i, (_, c) in enumerate(cols)]
        for d, _, _ in set_:
            s.append(f'<path d="{d}"/>')
        notes = []
        for (a, b, was), (_, _, now) in zip(set_[-2][2], set_[-1][2]):
            if was != now:
                ch = "".join(chr(cols[-1][1].font[n].unicodes[0]) for n in (a, b))
                notes.append((f"{ch} {was} → {now}", "#c00" if now == 0 else "#555"))
        x = 30 + (len(cols) - 1) * colw
        for text, fill in notes:
            s.append(label(x, y + 11, text, 6.5, fill))
            x += 4.2 * len(text) + 8
    s.append(label(W - 60, H - 14, f"{first}", 7))
    s.append("</svg>")
    return "\n".join(s)


def text_page(title, cols, words):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>', label(30, 24, title, 10, "#000")]
    y = 50
    for head, c in cols:
        s.append(label(30, y, head, 8, "#000"))
        y += 18
        x = 30
        for word in words:
            d, adv, _ = c.line(word, x, y, TEXT)
            if x + adv > W - 30:
                x, y = 30, y + TEXT * 1.5
                d, adv, _ = c.line(word, x, y, TEXT)
            s.append(f'<path d="{d}"/>')
            x += adv + TEXT * 0.3
        y += 34
    s.append("</svg>")
    return "\n".join(s)


def computed_kerning(upright, italic, skip=()):
    """The italic's kerning with the rule's values over it (the hand
    tables' entries, already in it, are not in the upright and stay)."""
    k = dict(italic.kerning)
    for pair, row in italic_kerning.compute(upright, italic).items():
        if row["value"] is None or pair in skip:
            continue
        if row["value"]:
            k[pair] = row["value"]
        else:
            k.pop(pair, None)
    return k


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("--words", default=" ".join(WORDS))
    a = ap.parse_args()
    words = a.words.split()
    out = Path(a.out)
    src = ROOT / "sources"
    pages, text_cols = [], []
    from make_bold import BOLD_KERNING

    for up, it, skip in (("Regular", "Italic", ()), ("Bold", "BoldItalic", set(BOLD_KERNING))):
        upright = ufoLib2.Font.open(src / f"MyiaDidot-{up}.ufo")
        italic = ufoLib2.Font.open(src / f"MyiaDidot-{it}.ufo")
        cols = [(up, Setter(upright)), (f"{it}, today", Setter(italic)),
                (f"{it}, computed", Setter(italic, computed_kerning(upright, italic, skip)))]
        for i in range(0, len(words), PAIRS_PER_PAGE):
            pages.append(page(f"Italic kerning from the white the shapes leave: {it} ({SIZE} pt)",
                              cols, words[i:i + PAIRS_PER_PAGE], len(pages) + 1))
        text_cols += cols[1:]
    pages.append(text_page(f"At {TEXT} pt", text_cols, words))
    parts = []
    for i, svg in enumerate(pages):
        f = out.with_name(f"{out.stem}-{i}.svg")
        f.write_text(svg)
        pdf = f.with_suffix(".pdf")
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(f)], check=True)
        f.unlink()
        parts.append(pdf)
    subprocess.run(["pdfunite", *map(str, parts), str(out)], check=True)
    for p in parts:
        p.unlink()
    print(f"{out}: {len(pages)} pages, {len(words)} words")


if __name__ == "__main__":
    sys.exit(main())
