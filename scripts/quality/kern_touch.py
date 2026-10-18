"""Kerning that brings inks together: a review sheet.

    python scripts/quality/kern_touch.py UFO [--sheet PDF] [--show N]

Each kerning entry whose letters' inks come within kern_clear.CLEAR units
across (outlines intersected, not only rows compared: interlocking shapes
that keep apart, χ Υ, are not found), with the letters it decides.
Printed: the entry, its value, how many of its pairs touch, the worst, and
the value kern_clear.py would give it. The sheet shows each entry's worst
pairs (up to --show) as kerned, ink in common red, ink nearer than CLEAR
orange, and beside them at kern_clear's value; a person decides which are
collisions (add the entry to kern_clear.PAIRS) and which are meant.
"""

import argparse
import subprocess
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kern_clear
from kern_coverage import Profiles

ROOT = Path(__file__).resolve().parent.parent.parent


def label(font, name):
    g = font[name]
    if g.unicodes:
        return chr(g.unicodes[0])
    base = name.split(".")[0]
    if base in font and font[base].unicodes:
        return chr(font[base].unicodes[0]) + "." + name.split(".", 1)[1]
    return name


def touching(font):
    """[(entry, value, [(member pair, gap estimate)], value at clearance)],
    worst first."""
    _, entry = kern_clear.kern_lookup(font)
    ink = kern_clear.Ink(font)
    prof = Profiles(font)
    found = []
    for (left, right), v in font.kerning.items():
        if v >= 0:
            continue
        pairs = [(a, b) for a in kern_clear.members(font, left) for b in kern_clear.members(font, right)
                 if entry(a, b) == (left, right)]
        # rows first (cheap): only pairs whose rows come near are intersected
        near = []
        for a, b in pairs:
            g = prof.gap(a, b, v)
            if g is not None and g < kern_clear.CLEAR and ink.touch(a, b, v):
                near.append(((a, b), g))
        if not near:
            continue
        near.sort(key=lambda t: t[1])
        worst = [p for p, _ in near[:3]]
        clear_at = kern_clear.needed(ink, worst, v)
        found.append(((left, right), v, near, clear_at))
    found.sort(key=lambda f: -(f[3] - f[1]) if f[3] is not None else 0)
    return found, ink


def draw(font, ink, a, b, kern, x, base, parts):
    """The pair at kern from x on the baseline base (SVG, y down); returns
    the width drawn."""
    dx = font[a].width + kern
    for name, off in ((a, 0), (b, dx)):
        pen = SVGPathPen(font)
        font[name].draw(TransformPen(pen, (1, 0, 0, -1, x + off, base)))
        parts.append(f'<path d="{pen.getCommands()}" fill="black"/>')
    pa, pb = ink.path(a, 0), ink.path(b, dx)
    for path, colour in ((pathops.op(pa, ink.path(b, dx - kern_clear.CLEAR), pathops.PathOp.INTERSECTION), "#f90"),
                         (pathops.op(pa, pb, pathops.PathOp.INTERSECTION), "#e00")):
        if abs(path.area) > 1:
            pen = SVGPathPen(None)
            path.draw(TransformPen(pen, (1, 0, 0, -1, x, base)))
            parts.append(f'<path d="{pen.getCommands()}" fill="{colour}"/>')
    return dx + font[b].width


def sheet(font, found, ink, out, show):
    row_h, parts, y = 3100, [], 700
    width = 0
    parts.append(f'<text x="100" y="400" font-size="260" font-family="sans-serif">{Path(out).stem}: '
                 f'as kerned (red: ink in common, orange: nearer than {kern_clear.CLEAR}) | at kern_clear\'s '
                 f'value; the entry, its value and the pairs it decides below</text>')
    for (left, right), v, near, clear_at in found:
        x = 100
        base = y + 2150
        for (a, b), _ in near[:show]:
            x += draw(font, ink, a, b, v, x, base, parts) + 250
        x += 250
        if clear_at is not None:
            parts.append(f'<line x1="{x - 250}" y1="{y + 200}" x2="{x - 250}" y2="{y + 2500}" stroke="#bbb" '
                         f'stroke-width="12"/>')
            for (a, b), _ in near[:show]:
                x += draw(font, ink, a, b, clear_at, x, base, parts) + 250
        width = max(width, x)
        pairs = " ".join(label(font, a) + label(font, b) for (a, b), _ in near[:6])
        more = f" +{len(near) - 6}" if len(near) > 6 else ""
        text = (f"{left.replace('public.', '')} {right.replace('public.', '')}  {v}"
                f"{f' → {clear_at}' if clear_at is not None else ''}   {len(near)} touching: {pairs}{more}")
        text = text.replace("&", "&amp;").replace("<", "&lt;")
        parts.append(f'<text x="100" y="{y + 2800}" font-size="230" font-family="sans-serif">{text}</text>')
        y += row_h
    w, h = max(width, 9000), max(y, row_h)
    svg = Path(out).with_suffix(".svg")
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                   f'<rect width="{w}" height="{h}" fill="white"/>{"".join(parts)}</svg>')
    subprocess.run(["rsvg-convert", "-f", "pdf", "-w", "1000", "-o", str(out), str(svg)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--sheet", help="a PDF of the entries, their worst pairs drawn")
    ap.add_argument("--show", type=int, default=3)
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    found, ink = touching(font)
    for (left, right), v, near, clear_at in found:
        (a, b), _ = near[0]
        print(f"{left} {right} {v} -> {clear_at}: {len(near)} touching, worst "
              f"{unicodedata.normalize('NFC', label(font, a) + label(font, b))}")
    if args.sheet:
        sheet(font, found, ink, args.sheet, args.show)
    print(f"{Path(args.ufo).name}: {len(found)} kerning entries bring inks within {kern_clear.CLEAR}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
