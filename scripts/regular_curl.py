"""The Regular's `curl` family mended (longtail.md, 2026-11-24): one cause
the operation shares, mended in the kept glyphs, and one letter's own.

    python scripts/regular_curl.py UFO [--small-caps]

(--small-caps: step 4 alone, on letters already mended.)

derive.curl draws the hook as part of a ring leaving the letter's stroke in
one direction (`dir`), the ring's two edges parallel there; it starts the
ring a few degrees back inside the stroke and unites the two. On a
diagonal stroke (Ƙ's thin arm, Y y W w's right arms), whose edges are not
parallel to `dir` nor to each other, the two edges meet at slight angles:

1. The outer join: the ring's first handle stands 2-5 degrees off the
   stroke's edge line (Ƙ 1019,1227 2.6; Ƴ 1061,1150 4.8, a corner; ƴ
   735,700 2.3; Ⱳ 1841,1120 2.1; ⱳ 1242,700 2.1): put in line
   (smooth_joins.align).
2. The other join, hidden from checks.construction by its short
   segments: the ring's edge crosses the stroke's a few units off, leaving
   crumbs of 4-8 units that turn 10-27 degrees (Ƴ 1117,1133; ƴ 787,687;
   Ⱳ 1896,1109; ⱳ 1289,689), and on Ƙ, where the cut runs across the arm,
   a notch on its upper edge: a 14-unit line at 16 degrees between the
   arm (50.8) and the ring (60.9), the ring starting 10 units inside the
   arm's edge (967,1250, 981,1254). The crumbs dropped and the node made
   smooth; Ƙ's ring start moved onto the arm's edge line, the notch's
   corner dropped, the ring's first handle along the line.
3. ʋ's own: the stem's outer edge bends in by 3 units at 923,60 down to
   920,0 (u's is 926 from top to foot): straight at 926, the node dropped.
4. ƙ.sc ƴ.sc ⱳ.sc, enlarged from Ƙ Ƴ Ⱳ (data_regular.py), made again on
   them; ⱳ.sc's node beside the ball, a corner after that, put in line.

The Regular's derived letters are kept once made (derive.py), so this
mends the kept glyphs; their recipes are not changed by it (the italics'
curls are their own recipes'). Run once on the Regular, then make
normalize; the Bold follows in make generate.
"""
import math
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smooth_joins  # noqa: E402
from regular_attach import node, rederive  # noqa: E402

# step 1: the outer join, the ring's handle onto the stroke's edge line
OUTER = {
    "uni0198": [(1019, 1227)],  # Ƙ
    "uni01B3": [(1061, 1150)],  # Ƴ
    "uni01B4": [(735, 700)],  # ƴ
    "uni2C72": [(1841, 1120)],  # Ⱳ
    "uni2C73": [(1242, 700)],  # ⱳ
}
# step 2: the inner join, at the ring's end: the crumbs after it dropped
# (up to INNER_CRUMB units: ƴ's and Ⱳ's last is a 13-unit curve), the ring's
# last handle onto the arm's line, the node smooth
INNER = {
    "uni01B3": [(1119, 1139)],  # Ƴ
    "uni01B4": [(790, 695)],  # ƴ
    "uni2C72": [(1899, 1116)],  # Ⱳ
    "uni2C73": [(1291, 696)],  # ⱳ
}
INNER_CRUMB = 16
# Ƙ's notch: (the arm's edge line: a node below, the K's top of it), the
# corner dropped, the ring's start moved onto the line
K_ARM = ((604, 804), (1075, 1382))
K_NOTCH, K_START = (967, 1250), (981, 1254)
# step 3: ʋ's stem, (node dropped, node moved to x)
V_STEM = ((923, 60), (920, 0), 926)
SMALL_CAPS = {"uni0199.sc": "ƙ.sc", "uni01B4.sc": "ƴ.sc", "uni2C73.sc": "ⱳ.sc"}
# made again, ⱳ.sc's node beside the ball came out a corner of 3.1 degrees
# (hidden from checks by its 11-unit handle; a wobble in the Bold)
SC_ALIGN = {"uni2C73.sc": [(1725, 837)]}
# (aligned, its 11-unit handle still left 1.2 degrees by rounding, 2.8 in
# the Bold: the other handle moved a unit onto the line, 0.0); the short
# curve after it, emboldened, bent back (its second handle 1875,816 above
# the line of its first: a wobble of 4 degrees in the Bold): that handle 5
# shorter, the Bold's then turning one way (-61, -63, -90)
SC_HANDLES = {"uni2C73.sc": [((1697, 896), (1696, 895)), ((1733, 817), (1733, 812))]}


def k_notch(glyph):
    (x0, y0), (x1, y1) = K_ARM
    c, i = node(glyph, *K_START)
    P = c.points
    p, h = P[i], P[(i + 1) % len(P)]
    length = math.dist((p.x, p.y), (h.x, h.y))
    p.x = round(x0 + (x1 - x0) * (p.y - y0) / (y1 - y0))
    u = (x1 - x0, y1 - y0)
    n = math.hypot(*u)
    h.x, h.y = round(p.x + u[0] / n * length), round(p.y + u[1] / n * length)
    p.smooth = True
    c, k = node(glyph, *K_NOTCH)
    del c.points[k]


def v_stem(glyph):
    drop, low, x = V_STEM
    c, i = node(glyph, *low)
    c.points[i].x = x
    c, k = node(glyph, *drop)
    del c.points[k]


def letters(path):
    font = ufoLib2.Font.open(path)
    k_notch(font["uni0198"])
    v_stem(font["uni028B"])
    for name, places in OUTER.items():
        for x, y in places:
            smooth_joins.align(font[name], x, y)
            c, i = node(font[name], x, y)
            c.points[i].smooth = True
    for name, places in INNER.items():
        for x, y in places:
            smooth_joins.crumbs(font[name], x, y, INNER_CRUMB)
            smooth_joins.align(font[name], x, y)
            c, i = node(font[name], x, y)
            c.points[i].smooth = True
    font.save()


def small_caps(path):
    font = rederive(path, SMALL_CAPS)
    for name, places in SC_ALIGN.items():
        for x, y in places:
            smooth_joins.align(font[name], x, y)
            c, i = node(font[name], x, y)
            c.points[i].smooth = True
    for name, moves in SC_HANDLES.items():
        for (x, y), (nx, ny) in moves:
            h = [p for c in font[name].contours for p in c.points if p.type is None and (p.x, p.y) == (x, y)]
            if len(h) != 1:
                raise ValueError(f"{name}: no single handle at {x},{y}")
            h[0].x, h[0].y = nx, ny
    font.save()


def main():
    path = sys.argv[1]
    if "--small-caps" not in sys.argv[2:]:
        letters(path)
    small_caps(path)


if __name__ == "__main__":
    main()
