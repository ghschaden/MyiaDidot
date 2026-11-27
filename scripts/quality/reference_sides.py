"""reference_sides.py [--style S ...] [--no-sc] [--sheet]: forms that face
or grow the other way than the references' (TODO T11, forms against the
references; asked 2026-11-24 after Ɦ's hook was found curled right over the
counter where Charis, Libertinus and the rest curl it left).

Candidates for a sheet, not a gate: the designer decides each (the reference
rule: Charis and Libertinus agreeing against Myia = change, with the
memory's exceptions; a dated verdict kept, or a mend in the recipe).

Two measures, each style against the same style of Charis SIL and
Libertinus Serif (build/refs, pinned by scripts/data/reference-inputs.json),
outlines deslanted by each font's italic angle, Myia read from sources/*.ufo
(no build needed):

- recipe: each encoded letter that data_regular.RECIPES builds from one
  encoded base (Ɦ from H), scaling recipes (alias, superior, enlarge, lower)
  left out. Per font the ink's growth past the base's ink box on each side
  (left and right over the base's width, top and bottom over its height; a
  side "grown" past GROW), and the lean of its centre of mass against the
  base's, over the width. Flagged when every reference grows a side Myia
  does not, or Myia grows one no reference does, or every reference leans
  the other way.
- raster: every letter, figure and symbol Myia shares with both references,
  its ink box rendered at RES x RES (proportions dropped: only the
  orientation counts), against each reference as drawn, mirrored, upside
  down and turned. Flagged when Myia is nearer every reference's
  transformed image than the image itself by MARGIN and near it (GOOD), the
  reference being far enough from its own transform (ASYM) for that to mean
  something. Coarse: a letter whose point or stem sits off centre the other
  way (Italic ѵ) reads as mirrored too; Italic Δ's thick stroke on the left
  is the kind it is for.

The small caps (unless --no-sc) through Myia's smcp and c2sc lookups in
features.fea and the references' smcp and c2sc shaped by HarfBuzz.

Writes build/quality/reference-sides-STYLE.txt; --sheet also
reference-sides-STYLE.pdf, each candidate Myia above the references, the
base in grey beside a recipe letter, large and filled.

    python -I scripts/quality/reference_sides.py --style Regular --sheet
"""

import argparse
import math
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
import skia
import ufoLib2
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import data_regular  # noqa: E402
from common import OUT, REFDIR, ROOT  # noqa: E402

STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
REFERENCES = (("Charis", "CharisSIL-{}.ttf"), ("Libertinus", "LibertinusSerif-{}.otf"))
# where one of the two lacks a letter (Libertinus most IPA small caps, the
# middle tildes): the system's Noto Serif, not pinned, named in the line
STAND_IN = ("Noto", "/usr/share/fonts/noto/NotoSerif-{}.ttf")
GROW = 0.06  # a side's growth past the base's box, over its width or height
LEAN = 0.04  # the references' lean, over the width, for theirs to count
SCALING = {"alias", "superior", "enlarge", "lower"}
RES = 32
MARGIN = 0.03  # mean pixel difference by which the transform must be nearer
ASYM = 0.08  # a reference this far from its own transform at least
GOOD = 0.30  # and Myia this near to it: a closer match to a poor one is another design, not a reversal
TRANSFORMS = ("mirrored", "upside down", "turned")
CATEGORIES = ("L", "N", "S")


class Face:
    """one font's outlines by character (and small cap), deslanted"""

    def __init__(self, name, glyphs, cmap, angle, sc, upm=1000):
        self.name, self.gs, self.cmap, self.sc = name, glyphs, cmap, sc
        self.slant = math.tan(math.radians(angle or 0))
        self.em = 1000 / upm  # every font drawn at 1000 units per em
        self._cache = {}

    @classmethod
    def ufo(cls, path):
        font = ufoLib2.Font.open(path)
        cmap = {u: g.name for g in font for u in g.unicodes}
        return cls("Myia", font, cmap, font.info.italicAngle, sc_from_features(font.features.text, cmap),
                   font.info.unitsPerEm or 1000)

    @classmethod
    def binary(cls, name, path):
        f = TTFont(path)
        cmap = f.getBestCmap()
        return cls(name, f.getGlyphSet(), cmap, f["post"].italicAngle, sc_by_shaping(path, f, cmap),
                   f["head"].unitsPerEm)

    def glyph(self, ch, sc=False):
        """the glyph name drawing ch (its small cap with sc), or None"""
        name = self.sc.get(ord(ch)) if sc else self.cmap.get(ord(ch))
        return name if name in self.gs else None

    def draw(self, name, pen):
        # italicAngle is negative for a rightward lean: x' = x + y tan(angle)
        e = self.em
        self.gs[name].draw(TransformPen(pen, (e, 0, self.slant * e, e, 0, 0)))

    def stats(self, name):
        """(ink box, centre of mass x) deslanted, or None for no ink"""
        if name not in self._cache:
            b = BoundsPen(self.gs)
            self.draw(name, b)
            s = StatisticsPen(self.gs)
            self.draw(name, s)
            self._cache[name] = (b.bounds, s.meanX) if b.bounds else None
        return self._cache[name]


def sc_from_features(text, cmap):
    """code point -> small cap glyph from the SmallCapsLower and
    SmallCapsUpper lookups (one-to-one subs)"""
    by_name = {}
    for lookup in ("SmallCapsLower", "SmallCapsUpper"):
        m = re.search(r"lookup %s \{(.*?)\} %s;" % (lookup, lookup), text, re.S)
        for src, dst in re.findall(r"sub \\?(\S+) by \\?(\S+);", m.group(1) if m else ""):
            by_name.setdefault(src, dst)
    return {u: by_name[g] for u, g in cmap.items() if g in by_name}


def sc_by_shaping(path, font, cmap):
    """code point -> the glyph smcp and c2sc give it, where they change it"""
    face = hb.Face(Path(path).read_bytes())
    hfont = hb.Font(face)
    order = font.getGlyphOrder()
    out = {}
    for u in cmap:
        ch = chr(u)
        if unicodedata.category(ch)[0] != "L":
            continue
        buf = hb.Buffer()
        buf.add_str(ch)
        buf.guess_segment_properties()
        hb.shape(hfont, buf, {"smcp": True, "c2sc": True})
        if len(buf.glyph_infos) == 1:
            g = order[buf.glyph_infos[0].codepoint]
            if g != cmap[u]:
                out[u] = g
    return out


# -- recipe: the sides a derived letter grows on --------------------------------


def recipe_pairs(regular):
    """[(letter, base, op)] both encoded single characters"""
    rev = {g: u for u, g in regular.cmap.items()}

    def char(x):
        if len(x) == 1:
            return x
        return chr(rev[x]) if x in rev else None

    out = []
    for target, op, src, _ in data_regular.RECIPES:
        if op in SCALING or not isinstance(src, str):
            continue
        ch, base = char(target), char(src)
        if ch and base and ch != base:
            out.append((ch, base, op))
    return out


def profile(face, ch, base, sc=False):
    """growth past the base's box per side and the lean, or None"""
    g, gb = face.glyph(ch, sc), face.glyph(base, sc)
    if g is None or gb is None:
        return None
    m, mb = face.stats(g), face.stats(gb)
    if not m or not mb:
        return None
    (x0, y0, x1, y1), cx = m
    (a0, b0, a1, b1), bcx = mb
    w, h = a1 - a0, b1 - b0
    if w <= 0 or h <= 0:
        return None
    return {"L": (a0 - x0) / w, "R": (x1 - a1) / w, "T": (y1 - b1) / h, "B": (b0 - y0) / h,
            "lean": (cx - bcx) / w}


def side_notes(mine, refs):
    """what sets Myia's profile apart from every reference's"""
    notes = []
    for side in "LRTB":
        theirs = ", ".join(f"{n} {p[side]:+.2f}" for n, p in refs)
        if all(p[side] > GROW for _, p in refs) and mine[side] <= GROW / 2:
            notes.append(f"refs grow {side} ({theirs}), Myia {mine[side]:+.2f}")
        if not any(p[side] > GROW / 2 for _, p in refs) and mine[side] > 2 * GROW:
            notes.append(f"Myia grows {side} {mine[side]:+.2f}, refs ({theirs})")
    leans = [p["lean"] for _, p in refs]
    if all(v < -LEAN for v in leans) and mine["lean"] > 0 or all(v > LEAN for v in leans) and mine["lean"] < 0:
        notes.append(f"leans {mine['lean']:+.2f}, refs " + ", ".join(f"{n} {p['lean']:+.2f}" for n, p in refs))
    return notes


# -- raster: drawn the other way round -----------------------------------------


class SkiaPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.path = skia.Path()

    def _moveTo(self, p):
        self.path.moveTo(*p)

    def _lineTo(self, p):
        self.path.lineTo(*p)

    def _curveToOne(self, p1, p2, p3):
        self.path.cubicTo(*p1, *p2, *p3)

    def _qCurveToOne(self, p1, p2):
        self.path.quadTo(*p1, *p2)

    def _closePath(self):
        self.path.close()


def raster(path, res=RES):
    """the path's ink box filled into res x res, 0..1, row 0 at the top"""
    r = path.computeTightBounds()
    w, h = r.width(), r.height()
    if w <= 0 or h <= 0:
        return None
    surface = skia.Surface(res, res)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorBLACK)
    canvas.translate(0, res)
    canvas.scale(res / w, -res / h)
    canvas.translate(-r.left(), -r.top())
    canvas.drawPath(path, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
    return surface.makeImageSnapshot().toarray()[:, :, 0].astype(np.float32) / 255


def image(face, name):
    key = ("img", name)
    if key not in face._cache:
        pen = SkiaPen(face.gs)
        face.draw(name, pen)
        face._cache[key] = raster(pen.path)
    return face._cache[key]


def transform(img, which):
    return {"mirrored": img[:, ::-1], "upside down": img[::-1, :], "turned": img[::-1, ::-1]}[which]


def diff(a, b):
    return float(np.abs(a - b).mean())


def raster_notes(mine, refs):
    """[(transform, [(ref, d as drawn, d transformed)])] where Myia is
    nearer every reference's transform"""
    out = []
    for which in TRANSFORMS:
        rows = []
        for n, img in refs:
            t = transform(img, which)
            straight, other = diff(mine, img), diff(mine, t)
            if diff(img, t) < ASYM or other > straight - MARGIN or other > GOOD:
                break
            rows.append((n, straight, other))
        else:
            out.append((which, rows))
    return out[:1]  # mirrored before upside down before turned


def raster_chars(myia):
    return [chr(u) for u in sorted(myia.cmap) if unicodedata.category(chr(u))[0] in CATEGORIES]


# -- the run -------------------------------------------------------------------


def label(ch, sc):
    return f"{ch}{'.sc' if sc else ''} (U+{ord(ch):04X} {unicodedata.name(ch, '?')})"


def judges(refs, stand_in, has):
    """the references that judge a letter: Charis and Libertinus where both
    have it (stand_in never outvotes them), else the one that has it and the
    stand-in; [] when fewer than two"""
    got = [r for r in refs if has(r)]
    if len(got) < len(refs) and stand_in is not None and has(stand_in):
        got.append(stand_in)
    return got if len(got) >= 2 else []


def load_refs(style):
    refs = []
    for name, pattern in REFERENCES:
        p = REFDIR / pattern.format(style)
        if not p.exists():
            sys.exit(f"{p} missing: run scripts/quality/fetch_refs.py")
        refs.append(Face.binary(name, p))
    p = Path(STAND_IN[1].format(style))
    return refs, (Face.binary(STAND_IN[0], p) if p.exists() else None)


def run(style, small_caps=True):
    """([candidate dict], Myia's face, the faces that judge) for one style"""
    myia = Face.ufo(ROOT / "sources" / f"MyiaDidot-{style}.ufo")
    refs, stand_in = load_refs(style)
    regular = myia if style == "Regular" else Face.ufo(ROOT / "sources" / "MyiaDidot-Regular.ufo")
    found, seen = [], set()
    for sc in (False, True) if small_caps else (False,):
        for ch, base, op in recipe_pairs(regular):
            mine = profile(myia, ch, base, sc)
            if not mine:
                continue
            theirs = [(r.name, profile(r, ch, base, sc)) for r in judges(refs, stand_in,
                                                                         lambda r, ch=ch, base=base, sc=sc: profile(r, ch, base, sc))]
            notes = side_notes(mine, theirs) if theirs else []
            if notes:
                found.append({"ch": ch, "sc": sc, "base": base, "kind": f"recipe {op} from {base}", "notes": notes})
                seen.add((ch, sc))
        for ch in raster_chars(myia):
            g = myia.glyph(ch, sc)
            if (ch, sc) in seen or g is None or image(myia, g) is None:
                continue
            imgs = [(r.name, image(r, r.glyph(ch, sc))) for r in judges(
                refs, stand_in, lambda r, ch=ch, sc=sc: r.glyph(ch, sc) is not None and image(r, r.glyph(ch, sc)) is not None)]
            for which, rows in raster_notes(image(myia, g), imgs) if imgs else []:
                found.append({"ch": ch, "sc": sc, "base": None, "kind": f"raster {which}",
                              "notes": [f"nearer every reference {which}: " + ", ".join(
                                  f"{n} {o:.2f} against {s:.2f}" for n, s, o in rows)]})
    return found, myia, refs + ([stand_in] if stand_in else [])


def report(style, found):
    lines = [(f"{style}: {len(found)} candidates against Charis and Libertinus, Noto Serif where one lacks the "
             "letter (scripts/quality/reference_sides.py)")]
    for f in found:
        lines.append(f"{label(f['ch'], f['sc'])} [{f['kind']}]: " + "; ".join(f["notes"]))
    return "\n".join(lines) + "\n"


def sheet(out, style, found, faces, per_page=5):
    """the candidates five to a page: per font a column, a recipe letter's
    base in grey on the left of the letter, one scale per candidate"""
    glyph_w, pad, head = 120, 24, 52
    col_w = 2 * glyph_w + 30
    row_h = glyph_w + head + 20
    W = pad * 2 + len(faces) * col_w
    pages = [found[i:i + per_page] for i in range(0, len(found), per_page)]
    out = Path(out)
    svgs = []
    for p, page in enumerate(pages):
        body = [(f'<text x="{pad}" y="28" font-family="DejaVu Sans" font-size="15" font-weight="bold">'
                 f"{style}: forms against the references, {len(found)} candidates (page {p + 1}/{len(pages)})"
                 "</text>"),
                (f'<text x="{pad}" y="44" font-family="DejaVu Sans" font-size="10" fill="#555">'
                 + "  ".join(face.name for face in faces)
                 + " left to right; a recipe letter's base grey on its left; deslanted</text>")]
        for i, f in enumerate(page):
            y0 = 56 + i * row_h
            body.append(f'<text x="{pad}" y="{y0 + 16}" font-family="DejaVu Sans" font-size="13" '
                        f'font-weight="bold">{_esc(label(f["ch"], f["sc"]))}  [{_esc(f["kind"])}]</text>')
            for k, line in enumerate(_wrap("; ".join(f["notes"]), 130)[:2]):
                body.append(f'<text x="{pad}" y="{y0 + 31 + 12 * k}" font-family="DejaVu Sans" font-size="9" '
                            f'fill="#555">{_esc(line)}</text>')
            cols = []
            for face in faces:
                pair = [(face.glyph(f["base"], f["sc"]), "#a8a8a8")] if f["base"] else [(None, None)]
                pair.append((face.glyph(f["ch"], f["sc"]), "#000"))
                cols.append((face, [(n, c, face.stats(n)[0]) for n, c in pair if n and face.stats(n)]))
            boxes = [b for _, items in cols for _, _, b in items]
            top, bot = max(b[3] for b in boxes), min(b[1] for b in boxes)
            wide = max(b[2] - b[0] for b in boxes)
            scale = min((glyph_w - 6) / (top - bot), (glyph_w - 6) / wide)
            baseline = y0 + head + top * scale
            for j, (face, items) in enumerate(cols):
                for name, colour, b in items:
                    k = 0 if colour != "#000" else 1
                    ox = pad + j * col_w + k * glyph_w + (glyph_w - (b[2] - b[0]) * scale) / 2 - b[0] * scale
                    pen = SVGPathPen(face.gs)
                    face.draw(name, TransformPen(pen, (scale, 0, 0, -scale, ox, baseline)))
                    body.append(f'<path d="{pen.getCommands()}" fill="{colour}"/>')
        H = 56 + len(page) * row_h
        svg = out.with_name(f"{out.stem}-{p + 1}.svg")
        svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                       '<rect width="100%" height="100%" fill="#fff"/>' + "".join(body) + "</svg>", encoding="utf-8")
        svgs.append(svg)
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(out), *map(str, svgs)], check=True)
    for svg in svgs:
        svg.unlink()
    return out


def _wrap(s, n):
    lines, cur = [], ""
    for word in s.split(" "):
        if cur and len(cur) + 1 + len(word) > n:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    return lines + [cur] if cur else lines


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--style", action="append", choices=STYLES, help="one style (repeatable); all four by default")
    ap.add_argument("--no-sc", action="store_true", help="leave the small caps out")
    ap.add_argument("--sheet", action="store_true", help="a PDF beside each report")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for style in a.style or STYLES:
        found, myia, refs = run(style, not a.no_sc)
        txt = OUT / f"reference-sides-{style}.txt"
        txt.write_text(report(style, found), encoding="utf-8")
        print(f"{style}: {len(found)} candidates ({sum(f['kind'].startswith('recipe') for f in found)} recipe, "
              f"{sum(f['sc'] for f in found)} small caps) -> {txt.relative_to(ROOT)}")
        if a.sheet and found:
            print("   ", sheet(OUT / f"reference-sides-{style}.pdf", style, found, [myia, *refs]).relative_to(ROOT))


if __name__ == "__main__":
    main()
