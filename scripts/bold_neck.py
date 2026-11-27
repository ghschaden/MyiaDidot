"""RECORD, not part of the build (TODO.md T7, 2026-11-27): run once, what
it made was kept in the UFO where accepted (in a generated style marked
drawn); no generator, Makefile target or test calls it. Kept to show how those glyphs were made; do not run it again
on sources/ (it would redo what was since reviewed or drawn over).

The Bold f's neck mended by hand (TODO.md, the Bold's hook batch,
2026-11-24), in f, longs and ʃ alike (each emboldened from the Regular
on its own, the same fault in each).

    python scripts/bold_neck.py UFO [--dry-run]

The inner curve that rises from the ball's left side into the arch (the
Regular's 648,1334 -> 656,1387 -> 576,1464): emboldened, the node at the
ball's side moved 9 units right where its neighbours moved 3-4, and the
arch's handle into it ran 38 units past it (703,1456 against the node's
665). The curve so swells right of its own extreme (checks.extreme, 9
units past) and turns twice (checks.wobble, 18 and 15 degrees), and
rederive carries it into every hook letter cut from f (Ɓ Ɗ Ƥ Ɦ ɓ ɗ ƙ ɦ
ɧ, ƥ.sc ɦ.sc) and draft_ligatures into the f and long-s ligatures.

Mended in the Regular's proportions on the Bold's stem: the node at the
ball's side 5 units left (its handles in line, the curve turning one
way); the arch's inner top where it stands in the Regular between the
stem's right edge and that node (0.72 of the way), its handles at the
Regular's shares (0.52 towards the stem, 0.88 towards the ball). The
outer edge, the ball and the stem stay. Marked drawn afterwards with
scripts/drawn.py.
"""
import argparse
import sys

import ufoLib2

GLYPHS = ("f", "longs", "uni0283")
# in f's coordinates (ʃ and ſ are f shifted right): index from the node at
# the ball's side (y 1383) -> the new point
NEW = {
    -1: (660, 1367),
    0: (660, 1383),
    1: (660, 1418),
    2: (653, 1456),
    3: (602, 1456),
    4: (527, 1456),
}
OLD = {-2: (658, 1354), -1: (665, 1367), 0: (665, 1383), 1: (665, 1419), 2: (703, 1456),
       3: (621, 1456), 4: (506, 1456), 5: (456, 1333)}


def find(glyph):
    """the contour and index of the node at the ball's side, and the shift
    of this glyph from f"""
    for c in glyph.contours:
        pts = c.points
        n = len(pts)
        for i, p in enumerate(pts):
            if p.segmentType and p.y == 1383 and pts[(i + 2) % n].y == 1456:
                dx = p.x - OLD[0][0]
                # all the old points where expected (±2 units: rounding)
                if all(abs(pts[(i + k) % n].x - (x + dx)) <= 2 and abs(pts[(i + k) % n].y - y) <= 1
                       for k, (x, y) in OLD.items()):
                    return c, i, dx
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    font = ufoLib2.Font.open(a.ufo)
    for name in GLYPHS:
        hit = find(font[name])
        if hit is None:
            sys.exit(f"{name}: the neck not found as expected (mended already?)")
        c, i, dx = hit
        n = len(c.points)
        for k, (x, y) in NEW.items():
            p = c.points[(i + k) % n]
            print(f"{name}: {p.x},{p.y} -> {x + dx},{y}")
            p.x, p.y = x + dx, y
    if not a.dry_run:
        font.save()


if __name__ == "__main__":
    main()
