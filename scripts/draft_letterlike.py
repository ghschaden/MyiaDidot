"""Draft letterlike symbols: ℓ and 𝑙 (script and math italic l), ℮
(estimated), ℵ ℶ (alef, bet), and the mathematical Fraktur 𝔐 𝔓 𝔖 𝔭.

    python scripts/draft_letterlike.py UFO [--redraft]

ℓ is a tall loop (thick on the left, a hairline on the right, as the
font's verticals and horizontals), its left side run down as a stem that
turns out to the right in a hook with a ball (derive.curl), all slanted;
𝑙 is the font's l from above its foot with the same hook, slanted. ℮ is O
open at the lower right with a hairline bar across. ℵ uses the approved
upright italic-derived design (upright_aleph.py); in ℶ the horizontals
are the heavy strokes, as in the Hebrew letter.

The Fraktur 𝔐 𝔓 𝔖 𝔭 is Libertinus Math's (SIL OFL 1.1, The Libertinus
Project Authors), adapted: scaled to this font's heights, its stems and
hairlines brought to the weights here, and its hairline ends given the
font's ball; --libertinus gives the font file. Glyphs are drafts; existing glyphs are kept unless
they are unreviewed drafts and --redraft is given.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import (
    BIG,
    _ellipse,
    curl,
    draw_path,
    embolden,
    path_op,
    rect_path,
    stroke,
    to_path,
)

DRAFT_KEY = "org.myiadidot.draft"
SLANT = 0.18  # the slant of ℓ and 𝑙 (about 10°)


def union(*paths):
    out = paths[0]
    for p in paths[1:]:
        out = path_op(out, p, "UNION")
    return out


def transformed(path, t):
    rec = RecordingPen()
    path.draw(TransformPen(rec, t))
    return to_path(None, rec=rec)


def lines(*segs):
    rec = RecordingPen()
    for p0, p1, t in segs:
        stroke(rec, p0, p1, t)
    return to_path(None, rec=rec)


def rects(*boxes):
    return union(*[rect_path(*b) for b in boxes])


def script_l(font):
    cx, cy, rx, ry, thick, thin = 430, 1030, 200, 470, 150, 40
    outer = _ellipse(cx, cy, rx, ry)
    inner = _ellipse(cx + (thick - thin) / 2, cy, rx - (thick + thin) / 2, ry - thin)
    loop = path_op(outer, inner, "DIFFERENCE")
    stem = rect_path(cx - rx, 140, cx - rx + thick, cy)
    hook = curl(font, "space", [], at=("pt", cx - rx + thick / 2, 150, thick), dir=270, turn="ccw",
                r=(150, 130), sweep=150, ball=50, t=(thick, 45))
    out = union(loop, stem, hook)
    return transformed(out, (1, 0, SLANT, 1, 0, 0)), 900


def italic_l(font):
    a, b = 220, 384  # the stem of l
    top = path_op(to_path(font, font["l"]), rect_path(-BIG, 150, BIG, BIG), "INTERSECTION")
    hook = curl(font, "space", [], at=("pt", (a + b) / 2, 160, b - a), dir=270, turn="ccw",
                r=(170, 140), sweep=150, ball=52, t=(b - a, 48))
    # the ball of the hook overhangs the advance, as italic letters do
    return transformed(union(top, hook), (1, 0, SLANT, 1, 0, 0)), 620


def estimated(font):
    o = path_op(to_path(font, font["O"]), rect_path(900, -BIG, BIG, 560), "DIFFERENCE")
    return union(o, rect_path(146, 690, 1522, 746)), font["O"].width


def alef(font):
    from upright_aleph import drawing

    width = font["uni2135"].width if "uni2135" in font else 1380
    glyph = drawing(tall=True, width=width)
    return to_path(None, rec=_record(glyph)), width


def _record(glyph):
    pen = RecordingPen()
    glyph.draw(pen)
    return pen


def poly(*pts):
    rec = RecordingPen()
    rec.moveTo(pts[0])
    for p in pts[1:]:
        rec.lineTo(p)
    rec.closePath()
    return to_path(None, rec=rec)


# -- Fraktur from Libertinus Math -------------------------------------------
#
# The outlines of Libertinus Math's Fraktur (SIL OFL 1.1, The Libertinus
# Project Authors), adapted to this font: scaled to its cap height
# (capitals) or x-height (𝔭), the vertical strokes brought to its stems
# (208, 164) and the hairlines made a little finer by moving the outline
# along its normals, and the hairline ends given the font's ball instead of
# the pen's tip (the broken feet stay).

SOURCES = {"libertinus": "/usr/share/fonts/libertinus/LibertinusMath-Regular.otf"}
HAIRLINE = -12  # finer hairlines, for the Didot contrast
FRAKTUR = {  # code point: (height in Libertinus, height here, stem correction, balls)
    # balls: the pen's tip (trimmed away) and the ball, set inside the
    # stroke's end so that it grows out of the hairline
    0x1D510: (658, 1434, -23, [((190, 545), (235, 590, 80)), ((1940, 1075), (1895, 1105, 72)),
                               ((1945, 225), (1900, 190, 68))]),
    0x1D513: (658, 1434, -23, [((165, 545), (210, 590, 80)), ((1450, 1068), (1405, 1098, 72))]),
    0x1D516: (658, 1434, -23, [((1440, 1415), (1395, 1375, 72)), ((805, 955), (775, 975, 66))]),
    0x1D52D: (429, 884, -22, [((265, 1228), (295, 1193, 60))]),
}


def fraktur(cp):
    def make(font):
        from fontTools.ttLib import TTFont

        lib = TTFont(SOURCES["libertinus"])
        g = lib.getGlyphSet()[lib.getBestCmap()[cp]]
        src_h, dst_h, ax, balls = FRAKTUR[cp]
        k = dst_h / src_h
        rec = RecordingPen()
        g.draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
        out = RecordingPen()
        embolden(rec, ax, HAIRLINE).draw(out)
        path = to_path(None, rec=out)
        for (tx, ty), (x, y, r) in balls:
            path = path_op(path, _ellipse(tx, ty, r * 0.8, r * 0.8), "DIFFERENCE")
            path = path_op(path, _ellipse(x, y, r, r), "UNION")
        return path, g.width * k + ax
    return make


def bet(font):
    out = rects((150, 1260, 1010, 1410),   # the heavy top
                (150, 1170, 214, 1410),    # its tick at the left
                (930, 130, 1010, 1410),    # the upright
                (100, 0, 1220, 150))       # the heavy base, running out to the right
    return out, 1320


GLYPHS = [  # name, code point, maker
    ("uni2113", 0x2113, script_l), ("u1D459", 0x1D459, italic_l),
    ("estimated", 0x212E, estimated), ("uni2135", 0x2135, alef), ("uni2136", 0x2136, bet),
    *[(f"u{cp:04X}", cp, fraktur(cp)) for cp in FRAKTUR],
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    ap.add_argument("--libertinus", default=SOURCES["libertinus"], help="LibertinusMath-Regular.otf")
    args = ap.parse_args()
    SOURCES["libertinus"] = args.libertinus
    font = ufoLib2.Font.open(args.ufo)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    cmap = {u: g.name for g in font for u in g.unicodes}
    made, kept = [], []
    for name, cp, maker in GLYPHS:
        name = cmap.get(cp, name)
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(chr(cp))
                continue
            del font[name]
        path, width = maker(font)
        g = font.newGlyph(name)
        g.unicodes = [cp]
        g.width = round(width)
        path = path_op(path, rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")
        draw_path(font, font["period"], g, path)
        g.lib[DRAFT_KEY] = True
        cats[name] = "base"
        if name not in font.glyphOrder:
            font.glyphOrder = [*font.glyphOrder, name]
        made.append(chr(cp))
    font.save()
    print(f"drafted {len(made)}: {' '.join(made)}")
    if kept:
        print(f"kept {len(kept)}: {' '.join(kept)}")


if __name__ == "__main__":
    main()
