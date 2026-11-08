"""Corners a generated style has where its source is smooth.

For each glyph drawn in both UFOs (contours, not components), every
on-curve point of the generated style whose outline turns there by more
than --min degrees is matched to the nearest on-curve point of the source
glyph (about each glyph's centre, scaled by its size, so the emboldening's
growth does not count). It is a candidate when that point is smooth there
(turns under --smooth degrees) or when no point of the source lies near
(--near, a fraction of the glyph's size). A candidate is not a fault: a
crotch, a ligature join or a sign can be designed so.

    python scripts/quality/corners.py sources/MyiaDidot-Italic.ufo \\
        sources/MyiaDidot-BoldItalic.ufo [--letters] [--max 90] [--sheet build/corners.pdf]

Prints one line per candidate (glyph, point, its turn, the source's turn
or "-" when none is near), worst first.
"""
import argparse
import math

import ufoLib2


def turns(glyph):
    """[(x, y, degrees)] for the on-curve points: how far the outline's
    direction turns there (0 = smooth)."""
    out = []
    for c in glyph.contours:
        pts = list(c.points)
        n = len(pts)
        if n < 3:
            continue
        for i, p in enumerate(pts):
            if p.type is None:
                continue
            a = pts[i - 1]
            b = pts[(i + 1) % n]
            # the tangents: to the neighbouring point, on- or off-curve
            # (a zero-length handle: the next point along)
            j = i - 1
            while (a.x, a.y) == (p.x, p.y) and j > i - n:
                j -= 1
                a = pts[j]
            k = i + 1
            while (b.x, b.y) == (p.x, p.y) and k < i + n:
                k += 1
                b = pts[k % n]
            d1 = math.atan2(p.y - a.y, p.x - a.x)
            d2 = math.atan2(b.y - p.y, b.x - p.x)
            t = abs(math.degrees((d2 - d1 + math.pi) % (2 * math.pi) - math.pi))
            out.append((p.x, p.y, t))
    return out


def bounds(glyph, font):
    b = glyph.getBounds(font)
    return (b.xMin, b.yMin, max(b.xMax - b.xMin, 1), max(b.yMax - b.yMin, 1)) if b else None


def candidates(src, gen, minimum=10.0, smooth=3.0, near=0.06):
    found = []
    for g in gen:
        if not g.contours or g.name not in src or not src[g.name].contours:
            continue
        bg, bs = bounds(g, gen), bounds(src[g.name], src)
        if not bg or not bs:
            continue
        mine = turns(src[g.name])
        size, ssize = max(bg[2], bg[3]), max(bs[2], bs[3])
        for x, y, t in turns(g):
            if t <= minimum or t >= 175:
                continue
            # about the glyph's centre, one scale both ways (a narrow glyph
            # emboldened would otherwise move every point across)
            u, v = (x - bg[0] - bg[2] / 2) / size, (y - bg[1] - bg[3] / 2) / size
            # the source's points near, nearest first: a corner of its own
            # there (a crotch, a serif) and this one is not new
            close = sorted((math.hypot((sx - bs[0] - bs[2] / 2) / ssize - u, (sy - bs[1] - bs[3] / 2) / ssize - v), st)
                           for sx, sy, st in mine)
            close = [(d, st) for d, st in close if d <= near]
            if not close:
                found.append((g.name, x, y, t, None))
            elif max(st for _, st in close) < smooth:
                found.append((g.name, x, y, t, close[0][1]))
    found.sort(key=lambda f: -f[3])
    return found


def is_letter(font, name):
    """A letter or a form of one (.sc, an alternate), not a sign."""
    import unicodedata

    base = name.split(".")[0]
    u = font[name].unicode if name in font else None
    if u is None and base in font:
        u = font[base].unicode
    if u is None:
        return name[0].isalpha() and "_" not in name
    return unicodedata.category(chr(u)).startswith("L")


def sheet(src, gen, found, path, split=45.0):
    """A vector PDF: per glyph the source and the generated letter side by
    side in black, each candidate ringed in red with its turn; first the
    glyphs whose worst candidate turns under split degrees (rounds gone
    angular, the likelier faults), then the rest (joins). Needs rsvg-convert
    and pdfunite."""
    import subprocess
    import tempfile
    from pathlib import Path

    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen

    by = {}
    for name, x, y, t, _ in found:
        by.setdefault(name, []).append((x, y, t))
    worst = {n: max(t for _, _, t in v) for n, v in by.items()}
    parts = [("Turns under %d degrees: rounds gone angular? (the likelier faults)" % split,
              sorted((n for n in by if worst[n] < split), key=lambda n: worst[n])),
             ("Turns of %d degrees and more: joins (mostly designed)" % split,
              sorted((n for n in by if worst[n] >= split), key=lambda n: worst[n]))]
    W, H, M = 595, 842, 28  # A4 in points
    cols, rows = 2, 5
    cw, ch = (W - 2 * M) / cols, (H - 2 * M - 30) / rows
    scale = ch * 0.62 / 2200

    def path_d(font, name, ox, oy):
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        pen = SVGPathPen(font)
        rec.replay(TransformPen(pen, (scale, 0, 0, -scale, ox, oy)))
        return pen.getCommands()

    pages = []
    for title, names in parts:
        for start in range(0, len(names), cols * rows):
            out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">',
                   '<rect width="100%" height="100%" fill="white"/>',
                   f'<text x="{M}" y="{M + 8}" font-family="sans-serif" font-size="10" font-weight="bold">{title}</text>',
                   (f'<text x="{M}" y="{M + 20}" font-family="sans-serif" font-size="7.5" fill="#555">'
                    'left: Italic (smooth there) | right: Bold Italic, red rings: its corners, degrees turned</text>')]
            for k, name in enumerate(names[start:start + cols * rows]):
                cx, cy = M + (k % cols) * cw, M + 30 + (k // cols) * ch
                base = cy + ch * 0.72  # the baseline
                left = cx + 8
                right = left + (src[name].width if name in src else 1000) * scale + 14
                out.append(f'<rect x="{cx + 2}" y="{cy + 2}" width="{cw - 4}" height="{ch - 4}" fill="none" stroke="#ddd"/>')
                out.append(f'<line x1="{cx + 4}" y1="{base}" x2="{cx + cw - 4}" y2="{base}" stroke="#ccc" stroke-width="0.3"/>')
                if name in src:
                    out.append(f'<path d="{path_d(src, name, left, base)}" fill="black" fill-rule="nonzero"/>')
                out.append(f'<path d="{path_d(gen, name, right, base)}" fill="black" fill-rule="nonzero"/>')
                for x, y, t in by[name]:
                    px, py = right + x * scale, base - y * scale
                    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="none" stroke="red" stroke-width="0.8"/>')
                    out.append(f'<text x="{px + 5:.1f}" y="{py - 4:.1f}" font-family="sans-serif" font-size="5.5" fill="red">{t:.0f}</text>')
                u = gen[name].unicode
                label = f"{name}" + (f"  {chr(u)}  U+{u:04X}" if u else "")
                label = label.replace("&", "&amp;").replace("<", "&lt;")
                out.append(f'<text x="{cx + 6}" y="{cy + ch - 8}" font-family="sans-serif" font-size="8">{label}</text>')
            out.append("</svg>")
            pages.append("\n".join(out))
    with tempfile.TemporaryDirectory() as tmp:
        pdfs = []
        for n, svg in enumerate(pages):
            s, pdf = Path(tmp) / f"{n:03d}.svg", Path(tmp) / f"{n:03d}.pdf"
            s.write_text(svg, encoding="utf-8")
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(s)], check=True)
            pdfs.append(str(pdf))
        subprocess.run(["pdfunite", *pdfs, str(path)], check=True)
    return [str(path)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source")
    ap.add_argument("generated")
    ap.add_argument("--min", type=float, default=10.0, help="least turn counted, degrees")
    ap.add_argument("--smooth", type=float, default=3.0, help="the source's most turn still smooth")
    ap.add_argument("--near", type=float, default=0.06)
    ap.add_argument("--max", type=float, default=175.0, help="most turn counted (sharper: designed joins)")
    ap.add_argument("--letters", action="store_true", help="letters only, not signs")
    ap.add_argument("--sheet", help="a vector PDF of the candidates (source | generated)")
    args = ap.parse_args()
    src, gen = ufoLib2.Font.open(args.source), ufoLib2.Font.open(args.generated)
    found = [f for f in candidates(src, gen, args.min, args.smooth, args.near)
             if f[3] < args.max and (not args.letters or is_letter(gen, f[0]))]
    for name, x, y, t, s in found:
        print(f"{name:20} {x:6.0f},{y:<6.0f} {t:5.1f}  {'-' if s is None else f'{s:.1f}'}")
    print(f"{len(found)} candidates in {len({f[0] for f in found})} glyphs")
    if args.sheet:
        for p in sheet(src, gen, found, args.sheet):
            print(p)


if __name__ == "__main__":
    main()
