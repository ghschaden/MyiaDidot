"""A capital before a small cap (smcp text: P a.sc r.sc i.sc s.sc) against
references with small caps: the optical gap of each kerned capital pair's
letters set so, relative to H h.sc.

    python scripts/quality/capsc_pairs.py STYLE [--tolerance T] [--myia OTF]

The pairs: the capital pairs the style kerns (the first letter of each
kerning entry), the second taken in smcp. The references: those of
greek_pairs.py that have small caps (EB Garamond, GFS Didot, Libertinus,
Charis) and Bodoni Moda; a reference counts for a pair where smcp gives it
a small cap there. Gaps are measured over the small-cap height, deep white
clipped (as pairs.py does over the x-height), outlines deslanted.

Most references do not kern these pairs at all; Myia kerns only those
outside the references' range by more than the tolerance (0.15 of the
H h.sc gap): the proposal prints the kerning, in font units, that brings
each just inside, for smallcaps.py CAP_SC_KERNING (final values).
"""

import argparse
import math
import statistics
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, REFDIR, ROOT, runs
from greek_pairs import refs as greek_refs

DEPTH = 0.2
STEPS = 30
BODONI = {"Regular": "BodoniModa-11-Regular", "Italic": "BodoniModa-11-Italic",
          "Bold": "BodoniModa-11-Bold", "BoldItalic": "BodoniModa-11-BoldItalic"}


def refs(style):
    paths = greek_refs(style)
    bodoni = REFDIR / f"{BODONI[style]}.ttf"
    return paths + ([str(bodoni)] if bodoni.exists() else [])


class Font:
    def __init__(self, path):
        self.name = Path(path).stem
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.cmap = self.tt.getBestCmap()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.slant = -math.tan(math.radians(self.tt["post"].italicAngle))
        self._paths = {}

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "smcp": True})
        return ([self.order[i.codepoint] for i in buf.glyph_infos],
                [p.x_advance for p in buf.glyph_positions])

    def path(self, name):
        if name not in self._paths:
            p = pathops.Path()
            self.gs[name].draw(TransformPen(p.getPen(glyphSet=self.gs), (1, 0, -self.slant, 1, 0, 0)))
            self._paths[name] = pathops.simplify(p)
        return self._paths[name]

    def top(self, name):
        b = BoundsPen(self.gs)
        self.gs[name].draw(b)
        return b.bounds[3]

    def small_cap(self, text):
        """The pair's glyphs if smcp gives its second letter a small cap."""
        if not all(ord(c) in self.cmap for c in text):
            return None
        names, adv = self.shape(text)
        if len(names) != 2 or names[1] == self.cmap[ord(text[1])]:
            return None
        return names, adv

    def gap(self, names, advance, h):
        pa, pb = self.path(names[0]), self.path(names[1])
        vals = []
        for i in range(STEPS):
            y = h * (i + 0.5) / STEPS
            ra, rb = runs(pa, y), runs(pb, y)
            vals.append(advance + rb[0][0] - ra[-1][1] if ra and rb else None)
        real = [v for v in vals if v is not None]
        if not real:
            return None
        near = min(real)
        return sum(min(v, near + DEPTH * h) if v is not None else near + DEPTH * h for v in vals) / STEPS


def capital_pairs(ufo):
    """Text pairs (capital + its second letter's lowercase) of the kerned
    capital pairs, by kerning entry (its group's first letter)."""
    def rep(item):
        if item in ufo:
            return item
        name = item.split(".", 2)[2]
        return name if name in ufo else ufo.groups[item][0]

    out = {}
    for left, right in ufo.kerning:
        if left.endswith(".sc") or right.endswith(".sc"):
            continue
        a, b = (ufo[rep(x)].unicode for x in (left, right))
        if a is None or b is None:
            continue
        a, b = chr(a), chr(b)
        if a.isupper() and b.isupper() and len(b.lower()) == 1:
            out.setdefault(a + b.lower(), (left, right))
    # one pair per kerning entry: its plainest letters (A y, not Ä ÿ)
    plain = {}
    for text in sorted(out, key=lambda t: (len(unicodedata.normalize("NFD", t)), t)):
        plain.setdefault(out[text], text)
    return {text: entry for entry, text in plain.items()}


def measure(style, myia=None):
    ufo = ufoLib2.Font.open(ROOT / "sources" / f"MyiaDidot-{style}.ufo")
    pairs = capital_pairs(ufo)
    fonts = [Font(str(myia or MYIA.format(style)))] + [Font(p) for p in refs(style)]
    norms = {}
    for f in fonts:
        got = f.small_cap("Hh")
        if got:
            h = f.top(got[0][1])
            norms[f.name] = (h, f.gap(got[0], got[1][0], h))
    res = {}
    for text in pairs:
        for f in fonts:
            if f.name not in norms:
                continue
            got = f.small_cap(text)
            if got:
                h, norm = norms[f.name]
                g = f.gap(got[0], got[1][0], h)
                if g is not None:
                    res.setdefault(text, {})[f.name] = (g / norm, got[0])
    return res, fonts[0].name, norms[fonts[0].name][1], ufo


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style")
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--myia", help="the font to measure (the built OTF by default)")
    args = ap.parse_args()
    res, myia, norm, ufo = measure(args.style, args.myia)
    side1 = {m: g for g, ms in ufo.groups.items() if g.startswith("public.kern1.") for m in ms}
    side2 = {m: g for g, ms in ufo.groups.items() if g.startswith("public.kern2.") for m in ms}
    rows = []
    for text, v in res.items():
        others = [x for k, (x, _) in v.items() if k != myia]
        if myia not in v or len(others) < 2:
            continue
        m, names = v[myia]
        lo, hi = min(others), max(others)
        rows.append((text, m, lo, statistics.median(others), hi, len(others), names))
    out = [r for r in rows if r[1] < r[2] - args.tolerance or r[1] > r[4] + args.tolerance]
    print(f"{args.style}: {len(rows)} capital + small cap pairs measured against at least two references; "
          f"{len(out)} outside their range by more than {args.tolerance}")
    seen = set()
    for text, m, lo, med, hi, n, names in sorted(out, key=lambda r: r[1] - r[4]):
        edge = lo if m < lo else hi
        key = (side1.get(names[0], names[0]), side2.get(names[1], names[1]))
        if key in seen:
            continue
        seen.add(key)
        print(f"    {key!r}: {round((edge - m) * norm)},  # {text}: {m:.2f}, references {lo:.2f}..{hi:.2f} "
              f"(median {med:.2f}, {n})")

if __name__ == "__main__":
    sys.exit(main())
