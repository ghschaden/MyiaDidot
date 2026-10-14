"""Draft arrows, geometric shapes and circled letters.

    python scripts/draft_symbols.py UFO [--redraft]

Arrows: a shaft of 72 units with a filled head, horizontal ones 1600 wide
on the math axis (514, the middle of the minus), the others the same arrow
turned. Geometric shapes: filled (black) or outlined with a 72-unit stroke
(white), large ones 1028 high like + and <, small ones half that, centred
on the math axis. Circled letters: the letter at 60% inside a circle of
the font's hairline weight. All glyphs are drafts; existing glyphs are
kept unless they are unreviewed drafts and --redraft is given.
"""

import argparse
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import BIG, draw_path, path_op, rect_path, to_path

DRAFT_KEY = "org.myiadidot.draft"
AXIS = 514
LINE = 72
LARGE, SMALL = 1028, 514
KAPPA = 0.5523


def poly(pts):
    rec = RecordingPen()
    rec.moveTo(pts[0])
    for p in pts[1:]:
        rec.lineTo(p)
    rec.closePath()
    return to_path(None, rec=rec)


def circle(cx, cy, r):
    rec = RecordingPen()
    k = KAPPA * r
    rec.moveTo((cx + r, cy))
    rec.curveTo((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
    rec.curveTo((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
    rec.curveTo((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
    rec.curveTo((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))
    rec.closePath()
    return to_path(None, rec=rec)


def union(*paths):
    out = paths[0]
    for p in paths[1:]:
        out = path_op(out, p, "UNION")
    return out


def transformed(path, t):
    rec = RecordingPen()
    path.draw(TransformPen(rec, t))
    return to_path(None, rec=rec)


def rotated(path, deg, cx, cy):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return transformed(path, (c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy))


def outlined(shape, scale_in, cx, cy):
    """The shape minus itself shrunk about (cx, cy): an outline."""
    inner = transformed(shape, (scale_in, 0, 0, scale_in, cx * (1 - scale_in), cy * (1 - scale_in)))
    return path_op(shape, inner, "DIFFERENCE")


# -- arrows -----------------------------------------------------------------

ARROW_W = 1600


X0, X1, HEAD, HALF, NOTCH = 120, 1480, 360, 230, 70


def head_right(x1):
    return poly([(x1, AXIS), (x1 - HEAD, AXIS + HALF), (x1 - HEAD + NOTCH, AXIS),
                 (x1 - HEAD, AXIS - HALF)])


def head_left(x0):
    return poly([(x0, AXIS), (x0 + HEAD, AXIS - HALF), (x0 + HEAD - NOTCH, AXIS),
                 (x0 + HEAD, AXIS + HALF)])


def arrow_right():
    # the shaft runs into the head past its notch, so no gap is left beside it
    shaft = rect_path(X0, AXIS - LINE / 2, X1 - HEAD + NOTCH + 30, AXIS + LINE / 2)
    return union(shaft, head_right(X1))


def arrow_both():
    # one shaft between the two heads: neither end is crossed by a shaft
    shaft = rect_path(X0 + HEAD - NOTCH - 30, AXIS - LINE / 2, X1 - HEAD + NOTCH + 30, AXIS + LINE / 2)
    return union(shaft, head_right(X1), head_left(ARROW_W - X1))


ARROWS = [  # name, code point, rotation of the right arrow (or 'both'), width
    ("arrowleft", 0x2190, 180, ARROW_W), ("arrowup", 0x2191, 90, 1000),
    ("arrowright", 0x2192, 0, ARROW_W), ("arrowdown", 0x2193, 270, 1000),
    ("arrowboth", 0x2194, "both", ARROW_W), ("arrowupdn", 0x2195, "both90", 1000),
    ("uni2196", 0x2196, 135, 1300), ("uni2197", 0x2197, 45, 1300),
    ("uni2198", 0x2198, 315, 1300), ("uni2199", 0x2199, 225, 1300),
]


def arrow(rot, width):
    cx, cy = ARROW_W / 2, AXIS
    if rot in ("both", "both90"):
        path, rot = arrow_both(), (0 if rot == "both" else 90)
    else:
        path = arrow_right()
    path = rotated(path, rot, cx, cy)
    if rot % 180:  # vertical or diagonal: centre in the new width, a bit higher
        path = transformed(path, (1, 0, 0, 1, width / 2 - cx, 640 - cy if rot % 90 == 0 else 600 - cy))
        if rot % 90:
            k = 0.82  # diagonal arrows: as long as the horizontal one is wide
            path = transformed(path, (k, 0, 0, k, width / 2 * (1 - k), 600 * (1 - k)))
    return path


# -- geometric shapes -------------------------------------------------------

def square(size):
    h = size / 2
    return poly([(-h, -h), (-h, h), (h, h), (h, -h)])


def triangle(size, deg):
    # equilateral, pointing up, centred on its centroid; then turned
    side = size * 1.08
    r = side / math.sqrt(3)
    pts = [(r * math.cos(math.radians(90 + 120 * i)), r * math.sin(math.radians(90 + 120 * i)))
           for i in range(3)]
    return rotated(poly(pts[::-1]), deg, 0, 0)


def diamond(size):
    h = size / 2 * 1.15
    return poly([(0, -h), (-h * 0.8, 0), (0, h), (h * 0.8, 0)])


def disc(size):
    return circle(0, 0, size / 2)


def inset(size, kind):
    """Scale of the inner shape for an outline of LINE units."""
    inr = {"square": size / 2, "triangle": size * 1.08 / (2 * math.sqrt(3)),
           "diamond": size / 2 * 1.15 * 0.8 / math.hypot(1, 0.8), "disc": size / 2}[kind]
    return (inr - LINE) / inr


SHAPE_MAKERS = {"square": square, "diamond": diamond, "disc": disc}


def shape(kind, size, filled, deg=0):
    path = triangle(size, deg) if kind == "triangle" else SHAPE_MAKERS[kind](size)
    if not filled:
        path = outlined(path, inset(size, kind), 0, 0)
    return path


SHAPES = [  # name, code point, kind, size, filled, direction
    ("filledbox", 0x25A0, "square", LARGE, True, 0), ("H22073", 0x25A1, "square", LARGE, False, 0),
    ("H18543", 0x25AA, "square", SMALL, True, 0), ("H18551", 0x25AB, "square", SMALL, False, 0),
    ("triagup", 0x25B2, "triangle", LARGE, True, 0), ("uni25B3", 0x25B3, "triangle", LARGE, False, 0),
    ("uni25B4", 0x25B4, "triangle", SMALL, True, 0), ("uni25B5", 0x25B5, "triangle", SMALL, False, 0),
    ("uni25B6", 0x25B6, "triangle", LARGE, True, -90), ("uni25B7", 0x25B7, "triangle", LARGE, False, -90),
    ("uni25B8", 0x25B8, "triangle", SMALL, True, -90), ("uni25B9", 0x25B9, "triangle", SMALL, False, -90),
    ("triagdn", 0x25BC, "triangle", LARGE, True, 180), ("uni25BD", 0x25BD, "triangle", LARGE, False, 180),
    ("uni25BE", 0x25BE, "triangle", SMALL, True, 180), ("uni25BF", 0x25BF, "triangle", SMALL, False, 180),
    ("uni25C0", 0x25C0, "triangle", LARGE, True, 90), ("uni25C1", 0x25C1, "triangle", LARGE, False, 90),
    ("uni25C2", 0x25C2, "triangle", SMALL, True, 90), ("uni25C3", 0x25C3, "triangle", SMALL, False, 90),
    ("uni25C6", 0x25C6, "diamond", LARGE, True, 0), ("uni25C7", 0x25C7, "diamond", LARGE, False, 0),
    ("circle", 0x25CB, "disc", LARGE, False, 0), ("H18533", 0x25CF, "disc", LARGE, True, 0),
    ("openbullet", 0x25E6, "disc", 456, False, 0),
]

# -- circled letters --------------------------------------------------------

CIRCLED = [("uni24B6", 0x24B6, "A"), ("uni24B9", 0x24B9, "D"), ("uni24D0", 0x24D0, "a")]
RING_R, RING_T = 820, 56


def circled(font, letter):
    from smallcaps import ink_bounds

    w = 2 * RING_R + 160
    cx, cy = w / 2, 640
    ring = path_op(circle(cx, cy, RING_R), circle(cx, cy, RING_R - RING_T), "DIFFERENCE")
    b = ink_bounds(font, letter)
    k = 0.6 * (1 if b[3] - b[1] > 1000 else 1.3)
    lx, ly = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    rec = RecordingPen()
    to_path(font, font[letter]).draw(TransformPen(rec, (k, 0, 0, k, cx - k * lx, cy - k * ly)))
    return union(ring, to_path(None, rec=rec)), w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    made, kept = [], []

    def put(name, cp, path, width):
        cmap = {u: g.name for g in font for u in g.unicodes}
        name = cmap.get(cp, f"uni{cp:04X}")
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                kept.append(chr(cp))
                return
            del font[name]
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

    for name, cp, rot, width in ARROWS:
        put(name, cp, arrow(rot, width), width)
    for name, cp, kind, size, filled, deg in SHAPES:
        path = shape(kind, size, filled, deg)
        width = size + (200 if size == LARGE else 160)
        put(name, cp, transformed(path, (1, 0, 0, 1, width / 2, AXIS)), width)
    for name, cp, letter in CIRCLED:
        path, width = circled(font, letter)
        put(name, cp, path, width)
    font.save()
    print(f"drafted {len(made)}: {' '.join(made)}")
    if kept:
        print(f"kept {len(kept)}: {' '.join(kept)}")


if __name__ == "__main__":
    main()
