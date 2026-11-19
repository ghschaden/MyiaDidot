"""A compact review sheet: each glyph's old outline (red) over its new (black), a grid, pages.

    python scripts/overlay_sheet.py OUT.pdf OLD.ufo NEW.ufo "GLYPH NAME or CHAR ..." [--title T] [--per-page 40]

Glyphs by name or by character, as they are in NEW; the same name is taken from OLD.
Each cell: the overlay at 0.05 em, the name below, how far the advance and the
ink's top and bottom moved. Pages are made with rsvg-convert and joined with pdfunite.
"""

import argparse
import subprocess
import tempfile
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen


def path(font, name):
    p = SVGPathPen(font)
    font[name].draw(p)
    return p.getCommands()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("glyphs")
    ap.add_argument("--title", default="")
    ap.add_argument("--per-page", type=int, default=40)
    a = ap.parse_args()
    old, new = ufoLib2.Font.open(a.old), ufoLib2.Font.open(a.new)
    cmap = {chr(u): g.name for g in new for u in g.unicodes}
    names = [cmap.get(t, t) for t in a.glyphs.split()]
    names = [n for n in names if n in new and n in old]
    S, cols, cw, ch = 0.06, 8, 130, 190
    top, bottom = 1650, 560
    pages = []
    tmp = Path(tempfile.mkdtemp())
    for pi in range(0, len(names), a.per_page):
        chunk = names[pi:pi + a.per_page]
        rows = (len(chunk) + cols - 1) // cols
        W, H = cols * cw + 20, rows * ch + 40
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">',
             f'<rect width="{W}" height="{H}" fill="#fff"/>',
             f'<text x="10" y="18" font-size="11" font-family="DejaVu Sans" font-weight="bold">{a.title} ({pi // a.per_page + 1}/{(len(names) + a.per_page - 1) // a.per_page}), old red, new black</text>']
        for i, n in enumerate(chunk):
            x0, y0 = 10 + (i % cols) * cw, 30 + (i // cols) * ch
            base = y0 + top * S
            bo, bn = BoundsPen(old), BoundsPen(new)
            old[n].draw(bo)
            new[n].draw(bn)
            dw = new[n].width - old[n].width
            dy = ""
            if bo.bounds and bn.bounds:
                dy = f" top{bn.bounds[3] - bo.bounds[3]:+.0f} bot{bn.bounds[1] - bo.bounds[1]:+.0f}"
            ox = x0 + 30 * S
            s.append(f'<path transform="translate({ox},{base}) scale({S},{-S})" d="{path(old, n)}" fill="#e22" fill-opacity="0.55"/>')
            s.append(f'<path transform="translate({ox},{base}) scale({S},{-S})" d="{path(new, n)}" fill="#000" fill-opacity="0.55"/>')
            s.append(f'<text x="{x0}" y="{y0 + (top + bottom) * S + 10}" font-size="6.5" font-family="DejaVu Sans">{n}</text>')
            s.append(f'<text x="{x0}" y="{y0 + (top + bottom) * S + 18}" font-size="5.5" font-family="DejaVu Sans" fill="#555">w{dw:+d}{dy}</text>')
        s.append("</svg>")
        f = tmp / f"p{pi // a.per_page:03d}.svg"
        f.write_text("".join(s))
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(f.with_suffix(".pdf")), str(f)], check=True)
        pages.append(str(f.with_suffix(".pdf")))
    subprocess.run(["pdfunite", *pages, a.out], check=True) if len(pages) > 1 else Path(a.out).write_bytes(Path(pages[0]).read_bytes())
    print(a.out, len(names), "glyphs", len(pages), "pages")


if __name__ == "__main__":
    main()
