"""Glyphs darker or lighter than their kind: the weight of their main stroke.

    python scripts/quality/strokes.py UFO [GLYPH ...] [--all] [--sheet OUT.pdf]

--sheet draws every finding between its kind's references (stem, the glyph,
round), darkest first, for review: what is drawn so (a Didot's ξ and 7 have
no heavy stroke) goes on the known list (tests/data/quality*.txt).

Each letter's and figure's main stroke is measured across the stroke (the
widest ink run on rows through the lower 20-60 % of its zone, narrowed by the stroke's lean, so
a diagonal is not taken for a heavier stem; runs as wide as a bar or a
bowl's top are not strokes), the upper quartile over the rows. It is compared with
its kind's reference strokes: a straight stem with the stem, any other
stroke with the band from the stem's weight to the round's (a Didot's round
strokes stand heavier than its stems, its diagonals at about stem weight):

  lowercase, IPA, old-style figures     n's stem, o's side
  capitals, lining figures              H's stem, O's side
  small caps                            h.sc's stem, o.sc's side

Findings (kind "stroke" for checks.py): a main stroke more than TOL over or
under its reference. Superiors, inferiors and other reduced forms, marks and
signs are not measured, nor glyphs made of components (their base is). The old-style figures stood 12-26 % over the
lowercase until lighten_figures.py.
"""

import math
import statistics
import sys
import unicodedata
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from case_reference import case_reference
from derived import Outline

TOL = 0.10
STEP = 10
LEAN = 8  # rows apart to measure a stroke's lean
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
# reduced or small by design (letters in Lm: ʰ ʲ ᵃ; these by name)
REFS = {"lc": ("n", "o"), "uc": ("H", "O"), "sc": ("h.sc", "o.sc")}
SKIP_SUFFIX = ("superior", "inferior", ".dnom", ".numr", ".sups", ".subs", "comb", ".cap")


def kind_of(font, g):
    """lc, uc, sc, or None (not measured)."""
    name = g.name
    # a glyph of components has its base's strokes (ώ is ω's): measured there
    if any(s in name for s in SKIP_SUFFIX) or not g.contours:
        return None
    if name.endswith(".sc"):
        return "sc"
    base = name.split(".")[0]
    if base.endswith("oldstyle") and base.removesuffix("oldstyle") in FIGURES:
        return "lc"
    if name in FIGURES:
        return "uc"
    if g.unicode is None:
        return None
    cat = unicodedata.category(chr(g.unicode))
    if cat == "Ll" or (cat == "Lo" and g.unicode < 0x3000):
        return "lc"
    if cat in ("Lu", "Lt"):
        return "uc"
    return None


def zone(font, kind):
    sc = font.lib.get("org.myiadidot.smallcapHeight", 1040)
    return {"lc": font.info.xHeight, "uc": font.info.capHeight, "sc": sc}[kind]


def main_stroke(outline, top):
    """(weight, straight): the median over rows of each row's widest stroke,
    measured across it, and whether that stroke keeps one width (a stem)."""
    widest = []
    for k in range(4, 13):  # 20 % to 60 % of the zone (below an arch's join)
        y = top * k / 20 + 0.37
        here, above = outline.spans(y), outline.spans(y + LEAN)
        best = 0.0
        for a, b in here:
            w = b - a
            if w > 0.45 * top or not above:
                continue
            mid = (a + b) / 2
            c, d = min(above, key=lambda s: abs((s[0] + s[1]) / 2 - mid))
            lean = math.atan2((c + d) / 2 - mid, LEAN)
            best = max(best, w * math.cos(lean))
        if best:
            widest.append(best)
    if len(widest) < 3:
        return None, None
    # its thickest stroke: a short one (ε's bowls, ξ's) counts, a stray row not
    widest.sort()
    weight = widest[round(0.75 * (len(widest) - 1))]
    straight = (max(widest) - min(widest)) / statistics.median(widest) < 0.08
    return weight, straight


def strokes(font, only=None):
    """[(glyph, "stroke", where, detail)] and {glyph: (weight, ratio)}."""
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    deslant = (1, 0, -slant, 1, 0, 0)

    def measure(name, kind):
        return main_stroke(Outline(font, name, deslant), zone(font, kind))

    cmap = {u: g.name for g in font for u in g.unicodes}
    refs = {}
    for kind, (stem, bowl) in REFS.items():
        stem, bowl = cmap.get(ord(stem), stem) if len(stem) == 1 else stem, \
            cmap.get(ord(bowl), bowl) if len(bowl) == 1 else bowl
        if stem in font and bowl in font:
            refs[kind] = (measure(stem, kind)[0], measure(bowl, kind)[0])
    out, measures = [], {}
    for g in font:
        if only and g.name not in only:
            continue
        kind = kind_of(font, g)
        if kind not in refs:
            continue
        weight, straight = measure(g.name, kind)
        if not weight:
            continue
        # a stem against n's stem; any other stroke within the band from the
        # stem's weight to the round's (a diagonal at stem weight is right)
        stem, bowl = refs[kind]
        lo, hi = (stem, stem) if straight else (min(stem, bowl), max(stem, bowl))
        capital = case_reference(font, g) if kind == "sc" else None
        if capital is not None:
            # A gamma's thin ribbon is intentional in its full capital too.
            # Keep the diagnostic relative to that same-style capital/H
            # proportion, rather than expecting a generic small-cap stem.
            capital_weight = measure(capital.name, "uc")[0]
            if not capital_weight or "uc" not in refs or not refs["uc"][0]:
                raise ValueError(f"{g.name}: capital reference has no measurable stroke")
            proportion = capital_weight / refs["uc"][0]
            lo, hi = lo * proportion, hi * proportion
        ref = min(max(weight, lo), hi)
        ratio = weight / ref
        measures[g.name] = (round(weight), round(ratio, 3), kind, "stem" if straight else "round")
        if abs(ratio - 1) > TOL:
            word = "darker" if ratio > 1 else "lighter"
            out.append((g.name, "stroke", kind, f"{weight:.0f} against {ref:.0f} ({ratio:.2f}, {word})"))
    return out, measures


def sheet(font, found, refs_of, out):
    """A PDF of the findings: each between its kind's stem and round
    references, its ratio below."""
    import subprocess

    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen

    cmap = {u: g.name for g in font for u in g.unicodes}

    def ref(c):
        return c if c.endswith(".sc") else cmap.get(ord(c), c)

    cell_h, cols, x0, y0 = 2600, 4, 0, 0
    cells, widths = [], []
    for name, _, kind, detail in found:
        trio = [ref(c) for c in refs_of[kind]]
        trio.insert(1, name)
        widths.append(sum(font[n].width for n in trio) + 400)
        cells.append((trio, f"{name}  {detail.split('(')[1].rstrip(')')}"))
    col_w = max(widths, default=1000)
    parts = []
    for i, (trio, label) in enumerate(cells):
        x0, y0 = (i % cols) * col_w, (i // cols) * cell_h
        x = x0 + 100
        for j, n in enumerate(trio):
            pen = SVGPathPen(font)
            font[n].draw(TransformPen(pen, (1, 0, 0, -1, x, y0 + 1900)))
            parts.append(f'<path d="{pen.getCommands()}" fill="{"black" if j == 1 else "#999"}"/>')
            x += font[n].width
        parts.append(f'<text x="{x0 + 100}" y="{y0 + 2450}" font-size="150" font-family="sans-serif">{label}</text>')
    w, h = cols * col_w, (len(cells) // cols + 1) * cell_h
    svg = Path(out).with_suffix(".svg")
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                   f'<rect width="{w}" height="{h}" fill="white"/>{"".join(parts)}</svg>')
    subprocess.run(["rsvg-convert", "-f", "pdf", "-w", "800", "-o", str(out), str(svg)], check=True)


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--all", action="store_true", help="every measured glyph, by ratio")
    ap.add_argument("--sheet", help="a PDF of the findings with their references")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    found, measures = strokes(font, set(args.glyphs) or None)
    if args.all:
        for n, (w, r, k, s) in sorted(measures.items(), key=lambda kv: kv[1][1]):
            print(f"{n:16} {k} {s:5} {w:5} {r:.2f}")
    else:
        for name, _, where, detail in sorted(found, key=lambda f: f[3]):
            print(f"{name:20} {where:3} {detail}")
    if args.sheet:
        order = sorted(found, key=lambda f: -float(f[3].split("(")[1].split(",")[0]))
        sheet(font, order, REFS, args.sheet)
    print(f"{Path(args.ufo).name}: {len(measures)} measured, {len(found)} beyond {TOL:.0%}", file=sys.stderr)


if __name__ == "__main__":
    main()
