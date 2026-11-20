"""A review sheet with the old and the new glyph in separate cells, and the changed edges magnified.

    python scripts/before_after_sheet.py OUT.pdf OLD.ufo NEW.ufo "GLYPH NAME or CHAR ..." [--title T]
        [--zone 1040] [--per-page 5]

One row per glyph: the old outline, the new, then a 1:1 strip of the top edge
(old, new) and of the bottom edge (old, new) about the ink's own highest and
lowest point, the zone line (the small-cap height, the baseline) drawn grey,
the numbers beside it. Not an overlay: the colours of an overlay hide a small
difference (the designer's rule, 2026-11-20). Pages are made with
rsvg-convert and joined with pdfunite.
"""

import argparse
import subprocess
import tempfile
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen

SCALE = 0.1          # the whole glyph, px per unit
STRIP_W, STRIP_H = 260, 110    # the magnified strips, units == px
CELL = 150
GAP = 14
ROW = 180


def path(font, name):
    p = SVGPathPen(font)
    font[name].draw(p)
    return p.getCommands()


def extreme_x(font, name, top):
    """x of the ink's highest (top) or lowest point."""
    g = font[name]
    best = None
    for c in g.contours:
        for p in c.points:
            if p.type is None:  # a handle: the node's x is wanted
                continue
            if best is None or (p.y > best[1] if top else p.y < best[1]):
                best = (p.x, p.y)
    return best


def strip(font, name, top, zone, x, y0):
    """An SVG strip about the zone, centred on x."""
    ycentre = zone if top else 0
    d = path(font, name)
    return (f'<svg x="{x}" y="{y0}" width="{STRIP_W}" height="{STRIP_H}" '
            f'viewBox="{{cx}} {-(ycentre + STRIP_H / 2)} {STRIP_W} {STRIP_H}" overflow="hidden">'
            f'<rect x="-9999" y="-9999" width="19999" height="19999" fill="#fff"/>'
            f'<line x1="-9999" x2="9999" y1="{-zone if top else 0}" y2="{-zone if top else 0}" stroke="#999" stroke-width="1"/>'
            f'<path d="{d}" transform="scale(1,-1)" fill="#000"/></svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("glyphs")
    ap.add_argument("--title", default="")
    ap.add_argument("--zone", type=int, default=1040)
    ap.add_argument("--per-page", type=int, default=5)
    a = ap.parse_args()
    old, new = ufoLib2.Font.open(a.old), ufoLib2.Font.open(a.new)
    cmap = {chr(u): g.name for g in new for u in g.unicodes}
    names = [cmap.get(t, t) for t in a.glyphs.split()]
    names = [n for n in names if n in new and n in old]
    width = 90 + 2 * CELL + 4 * (STRIP_W + GAP) + 20
    pages = []
    tmp = Path(tempfile.mkdtemp())
    for pi in range(0, len(names), a.per_page):
        chunk = names[pi:pi + a.per_page]
        h = 50 + ROW * len(chunk) + 20
        out = [(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
                f'viewBox="0 0 {width} {h}"><rect width="100%" height="100%" fill="#fff"/>'),
               f'<text x="12" y="22" font-family="sans-serif" font-size="14">{a.title}</text>']
        heads = ("old", "new", "top, old", "top, new", "bottom, old", "bottom, new")
        xs = [90, 90 + CELL] + [90 + 2 * CELL + i * (STRIP_W + GAP) for i in range(4)]
        for x, t in zip(xs, heads):
            out.append(f'<text x="{x}" y="42" font-family="sans-serif" font-size="11" fill="#555">{t}</text>')
        for r, name in enumerate(chunk):
            y = 50 + r * ROW
            nb, ob = BoundsPen(new), BoundsPen(old)
            new[name].draw(nb)
            old[name].draw(ob)
            nbb, obb = nb.bounds or (0, 0, 0, 0), ob.bounds or (0, 0, 0, 0)
            out.append(f'<text x="8" y="{y + 40}" font-family="sans-serif" font-size="12">{name}</text>')
            out.append(f'<text x="8" y="{y + 56}" font-family="sans-serif" font-size="10" fill="#555">top {obb[3]:.0f}→{nbb[3]:.0f}</text>')
            out.append(f'<text x="8" y="{y + 70}" font-family="sans-serif" font-size="10" fill="#555">'
                       f'bottom {obb[1]:.0f}→{nbb[1]:.0f}</text>')
            out.append(f'<text x="8" y="{y + 84}" font-family="sans-serif" font-size="10" fill="#555">'
                       f'adv {old[name].width}→{new[name].width}</text>')
            for font, x in ((old, xs[0]), (new, xs[1])):
                out.append(f'<g transform="translate({x},{y + 20 + 1100 * SCALE}) scale({SCALE},{-SCALE})">'
                           f'<path d="{path(font, name)}" fill="#000"/>'
                           f'<line x1="-100" x2="1600" y1="0" y2="0" stroke="#bbb" stroke-width="6"/>'
                           f'<line x1="-100" x2="1600" y1="{a.zone}" y2="{a.zone}" stroke="#bbb" stroke-width="6"/></g>')
            for top, (xo, xn) in ((True, (xs[2], xs[3])), (False, (xs[4], xs[5]))):
                p = extreme_x(new, name, top) or (0, 0)
                cx = p[0] - STRIP_W / 2
                for font, x in ((old, xo), (new, xn)):
                    out.append(strip(font, name, top, a.zone, x, y + 10).replace("{cx}", f"{cx:.0f}"))
            out.append(f'<line x1="0" x2="{width}" y1="{y + ROW - 10}" y2="{y + ROW - 10}" stroke="#ddd"/>')
        out.append("</svg>")
        svg = tmp / f"p{pi:04d}.svg"
        svg.write_text("\n".join(out))
        pdf = tmp / f"p{pi:04d}.pdf"
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(svg)], check=True)
        pages.append(str(pdf))
    subprocess.run(["pdfunite", *pages, a.out], check=True)
    print(f"{a.out}: {len(names)} glyphs, {len(pages)} pages")


if __name__ == "__main__":
    main()
