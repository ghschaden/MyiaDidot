"""A review sheet for redrawn glyphs (scripts/redraw.py): one row a glyph.

    python scripts/redraw_sheet.py OUT.pdf "n a e o s g" \
        --col "Old Standard=sources/oldstand/OldStandard-Italic.ufo" \
        --col "today=sources/MyiaDidot-Italic.ufo" \
        --col "redrawn=build/redraw/pilot.ufo" \
        [--over today,redrawn] [--words "nonsense oases ..."] [--title TEXT]

Each row: the glyph in every column as a node view (corners square, smooth
nodes round, a smooth node off the extremes and off a line's end ringed
orange: what the gate counts), with its node count and, where the UFO has
a report beside it (NAME.json by redraw.py --json), its distance from the
target and worst curvature jump; then the two columns named by --over on
each other (the first red, the second black) enlarged; then every column
filled at 144 pt. Last, words at 24 and 12 pt, a line per column: the
second column's font (today's) with that column's glyphs put in, advances
only, no kerning.

A UFO at another em (Old Standard's 1000) is scaled to the second
column's. Glyphs are found by character in each UFO.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))

NODE = 0.34        # points per unit in the node views
BIG = 0.44         # in the overlay
PAD = 24


def path_d(glyph, scale, ox, oy, k=1.0):
    """the glyph's contours as an SVG path (k: its units to the sheet's font units)"""
    out = []
    for c in glyph.contours:
        pts = list(c.points)
        n = len(pts)
        start = next((i for i, q in enumerate(pts) if q.type), None)
        if start is None:
            continue
        P = lambda q: f"{ox + q.x * k * scale:.2f} {oy - q.y * k * scale:.2f}"  # noqa: E731
        out.append("M" + P(pts[start]))
        buf = []
        for m in range(1, n + 1):
            q = pts[(start + m) % n]
            if not q.type:
                buf.append(q)
                continue
            if len(buf) == 2:
                out.append(f"C{P(buf[0])} {P(buf[1])} {P(q)}")
            elif len(buf) == 1:
                out.append(f"Q{P(buf[0])} {P(q)}")
            else:
                out.append("L" + P(q))
            buf = []
        out.append("Z")
    return "".join(out)


def off_structure(pts, i):
    """is the smooth node pts[i] neither at an extreme nor at a line's end?"""
    n = len(pts)
    p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
    if p.type == "line" or b.type == "line":
        return False
    for h in (a, b):
        if not h.type and (h.x, h.y) != (p.x, p.y):
            return abs(h.x - p.x) > 0.5 and abs(h.y - p.y) > 0.5
    return False


def node_view(glyph, scale, ox, oy, k=1.0):
    X = lambda q: ox + q.x * k * scale  # noqa: E731
    Y = lambda q: oy - q.y * k * scale  # noqa: E731
    out = [f'<path d="{path_d(glyph, scale, ox, oy, k)}" fill="#e4e4e4" fill-rule="nonzero" stroke="#222" stroke-width="0.5"/>']
    for c in glyph.contours:
        pts = list(c.points)
        n = len(pts)
        for i, q in enumerate(pts):
            if not q.type:
                out.append(f'<circle cx="{X(q):.2f}" cy="{Y(q):.2f}" r="1.1" fill="#3c6ec8"/>')
                continue
            for nb in (pts[i - 1], pts[(i + 1) % n]):
                if not nb.type:
                    out.append(f'<line x1="{X(q):.2f}" y1="{Y(q):.2f}" x2="{X(nb):.2f}" y2="{Y(nb):.2f}" stroke="#78a0dc" stroke-width="0.4"/>')
            if not q.smooth:
                out.append(f'<rect x="{X(q) - 1.8:.2f}" y="{Y(q) - 1.8:.2f}" width="3.6" height="3.6" fill="#d23c28"/>')
            elif off_structure(pts, i):
                out.append(f'<circle cx="{X(q):.2f}" cy="{Y(q):.2f}" r="2.6" fill="none" stroke="#f08c00" stroke-width="1.2"/>')
                out.append(f'<circle cx="{X(q):.2f}" cy="{Y(q):.2f}" r="1.2" fill="#d23c28"/>')
            else:
                out.append(f'<circle cx="{X(q):.2f}" cy="{Y(q):.2f}" r="1.9" fill="#d23c28"/>')
    return "".join(out)


def nodes(glyph):
    on = [(list(c.points), i) for c in glyph.contours for i, p in enumerate(c.points) if p.type]
    return len(on), sum(1 for pts, i in on if pts[i].smooth and off_structure(pts, i))


def text(x, y, s, size=8, fill="#000", weight="normal"):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="DejaVu Sans, sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}">{s}</text>'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out")
    ap.add_argument("glyphs", help="characters or glyph names, spaced")
    ap.add_argument("--col", action="append", required=True, metavar="LABEL=UFO")
    ap.add_argument("--over", help="two labels to draw on each other (default: the last two columns)")
    ap.add_argument("--words", default="")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    cols = []
    for spec in a.col:
        label, path = spec.split("=", 1)
        font = ufoLib2.Font.open(path)
        rep = Path(path).with_suffix(".json")
        reports = {r["glyph"]: r for r in json.loads(rep.read_text())} if rep.exists() else {}
        cols.append({"label": label, "font": font, "cmap": {chr(u): g.name for g in font for u in g.unicodes},
                     "reports": reports})
    base = cols[min(1, len(cols) - 1)]
    em = base["font"].info.unitsPerEm
    for c in cols:
        c["k"] = em / c["font"].info.unitsPerEm
    over = a.over.split(",") if a.over else [c["label"] for c in cols[-2:]]
    over = [next(c for c in cols if c["label"] == x) for x in over]
    names = a.glyphs.split()

    def glyph(col, ch):
        name = col["cmap"].get(ch, ch)
        return col["font"][name] if name in col["font"] else None

    asc = (base["font"].info.ascender or 1500) + 60
    desc = -(base["font"].info.descender or -500) + 60
    lows = [g for ch in names if (g := glyph(base, ch)) is not None]
    tall = any(p.y > (base["font"].info.xHeight or 900) + 80 for g in lows for c in g.contours for p in c.points)
    deep = any(p.y < -80 for g in lows for c in g.contours for p in c.points)
    top = asc if tall else (base["font"].info.xHeight or 900) + 120
    bottom = desc if deep else 120
    wide = max((g.width for g in lows), default=1000) + 160
    cw = wide * NODE + PAD
    rh = (top + bottom) * max(NODE, BIG * 0.999) + 46
    ow = wide * BIG + PAD
    fw = wide * 144 / em + 10
    W = PAD + cw * len(cols) + ow + fw * len(cols) + PAD
    head = 54
    word_rows = (len(cols) * 2 * 44 + 40) if a.words else 0
    H = head + rh * len(names) + word_rows + PAD
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}pt" height="{H:.0f}pt" viewBox="0 0 {W:.0f} {H:.0f}">',
         f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff"/>']
    s.append(text(PAD, 22, a.title or "Redrawn glyphs", 13, weight="bold"))
    s.append(text(PAD, 36, "node views: square = corner, round = smooth, ringed orange = smooth node off the extremes "
                  "and off a line's end; overlay: " + f"{over[0]['label']} red, {over[1]['label']} black; then filled at 144 pt", 7.5, "#444"))
    for ci, c in enumerate(cols):
        s.append(text(PAD + ci * cw, head - 4, c["label"], 9, weight="bold"))
        s.append(text(PAD + cw * len(cols) + ow + ci * fw, head - 4, c["label"], 7, "#444"))
    s.append(text(PAD + cw * len(cols), head - 4, f"{over[0]['label']} / {over[1]['label']}", 9, weight="bold"))
    for r, ch in enumerate(names):
        y0 = head + r * rh
        s.append(f'<line x1="{PAD}" y1="{y0:.1f}" x2="{W - PAD:.1f}" y2="{y0:.1f}" stroke="#ccc" stroke-width="0.4"/>')
        by = y0 + 14 + top * BIG  # baseline, shared by the row
        for ci, c in enumerate(cols):
            g = glyph(c, ch)
            if g is None:
                continue
            ox = PAD + ci * cw + 8
            s.append(node_view(g, NODE, ox, by, c["k"]))
            count, offs = nodes(g)
            line = f"{ch}: {count} nodes" + (f", {offs} off the structure" if offs else "")
            s.append(text(ox, y0 + rh - 22, line, 7.5))
            rep = c["reports"].get(g.name)
            if rep:
                s.append(text(ox, y0 + rh - 12, f"{rep['dev']} units from the target at most; curvature jump "
                              f"{rep['jump_before']} -> {rep['jump']}", 6.5, "#444"))
                verdict = "gate: " + ("; ".join(rep["fail"]) if rep.get("fail") else "candidate")
                s.append(text(ox, y0 + rh - 3, verdict[:90], 6.5, "#b00" if rep.get("fail") else "#070"))
            fx = PAD + cw * len(cols) + ow + ci * fw
            s.append(f'<path d="{path_d(g, 144 / em, fx, by, c["k"])}" fill="#000"/>')
        ox = PAD + cw * len(cols) + 8
        for c, colour, width in ((over[0], "#e02020", 0.9), (over[1], "#000", 0.45)):
            g = glyph(c, ch)
            if g is not None:
                s.append(f'<path d="{path_d(g, BIG, ox, by, c["k"])}" fill="none" stroke="{colour}" stroke-width="{width}"/>')
    if a.words:
        y = head + rh * len(names) + 30
        s.append(f'<line x1="{PAD}" y1="{y - 22:.1f}" x2="{W - PAD:.1f}" y2="{y - 22:.1f}" stroke="#ccc" stroke-width="0.4"/>')
        s.append(text(PAD, y - 8, "in words (the second column's font with each column's glyphs put in; advances only, "
                      "no kerning)", 7.5, "#444"))
        for size in (24, 12):
            for c in cols:
                y += 20 + size
                x = PAD + 80
                s.append(text(PAD, y, f"{c['label']} {size} pt", 7, "#444"))
                sc = size / em
                for chx in a.words:
                    g, k = glyph(c, chx), c["k"]
                    if g is None or chx not in names:
                        g, k = glyph(base, chx), 1.0
                    if g is None:
                        x += 0.25 * size
                        continue
                    s.append(f'<path d="{path_d(g, sc, x, y, k)}" fill="#000"/>')
                    x += g.width * k * sc
    s.append("</svg>")
    out = Path(a.out)
    svg = out.with_suffix(".svg")
    svg.write_text("\n".join(s))
    if out.suffix == ".pdf":
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(out), str(svg)], check=True)
        svg.unlink()
    print(out)


if __name__ == "__main__":
    main()
