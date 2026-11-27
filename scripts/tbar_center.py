"""RECORD, not part of the build (TODO.md T7, 2026-11-27): run once, what
it made was kept in the UFO where accepted (in a generated style marked
drawn); no generator, Makefile target or test calls it. Kept to show how those glyphs were made; do not run it again
on sources/ (it would redo what was since reviewed or drawn over).

Centre the crossbar of t on its stem (2026-11-20, the designer: "fix the
t-bar in all styles").

    python scripts/tbar_center.py UFO [--dry-run]

The bar's centre stood right of the stem's by 27 units in the Regular and 44
in the Italic (13 and 21 per mille em; Charis +37, Bodoni Moda +20 / -3,
Old Standard +25, EB Garamond +50 / +22): the f-like italics' bar stands 7
off its stem (f's), so t is set to the same, +6 units. Only the bar's two
ends move (both left, the bar's length kept); the stem, foot and tail stay.
Nothing else moves: not the stem, foot or tail, not the advance (the first
attempt kept the side bearings at the bar's ends and so moved the stem and
narrowed the Italic's advance by 33: the pairs tf tt went tight; the white
at the stem and tail is what faces the next letter, and it stays).

Points are named by index, checked against their coordinates: a t that is
not the one measured is refused. The Bold and the Bold Italic are generated
from these (make generate); the glyphs built on t follow in the same run,
the ligatures with t (ct st tt th ft ...) are drafts of their own
(docs/claude/glyphs.md).
"""

import argparse
import sys

import ufoLib2

# per style: (left end points, right end points), the bar's band, d = shift
STYLES = {
    "Regular": {"left": [(0, 36, 836), (1, 36, 884)], "right": [(13, 600, 884), (14, 600, 836)], "d": 21},
    "Italic": {"left": [(5, 115, 806), (6, 129, 861)], "right": [(11, 622, 861), (12, 608, 806)], "d": 38},
}


def centre(font, spec):
    g = font["t"]
    c = g.contours[0]
    for i, x, y in spec["left"] + spec["right"]:
        p = c.points[i]
        if (round(p.x), round(p.y)) != (x, y):
            raise ValueError(f"t point {i} is {p.x},{p.y}, not {x},{y}: not the t measured")
    w0 = g.width
    for i, *_ in spec["left"] + spec["right"]:
        c.points[i].x -= spec["d"]
    return 0, w0, g.width


# the ligatures with a t (Regular): the free outer ends of t's bar, by
# coordinates (the bar joins its neighbours elsewhere): t_t both ends, t_h the
# left end, the others the right end
LIGATURE_ENDS = {
    "t_t": [(36, 836), (36, 884), (1190, 884), (1190, 836)],
    "t_h": [(36, 836), (36, 884)],
    "f_t": [(1164, 884), (1164, 836)],
    "f_f_t": [(1744, 884), (1744, 836)],
    "c_t": [(1454, 884), (1454, 836)],
    "s_t": [(1350, 884), (1350, 836)],
    "longs_t": [(1164, 884), (1164, 836)],
    "longs_longs_t": [(1744, 884), (1744, 836)],
}


def centre_ends(font, name, ends, d):
    """the listed points (x, y) of a ligature moved left by d (left ends and
    right ends alike: the bar's length kept as in t), then bearings as before"""
    g = font[name]
    pts = []
    for x, y in ends:
        hit = [p for c in g for p in c.points if round(p.x) == x and round(p.y) == y]
        if len(hit) != 1:
            raise ValueError(f"{name}: {len(hit)} points at {x},{y}")
        pts.append(hit[0])
    w0 = g.width
    for p in pts:
        p.x -= d
    return 0, w0, g.width


def centre_band(font, name, band, stem, d):
    """a glyph made from t (ƭ ʈ ⱦ ᵵ), stored: the points of the bar's ends (in
    the bar's band, beyond the stem's edges stem=(left, right) by more than 1)
    moved left by d, the glyph then shifted and its advance set for the old
    side bearings, as centre does for t"""
    g = font[name]
    y0, y1 = band
    ends = [p for c in g for p in c.points if y0 <= p.y <= y1 and (p.x < stem[0] - 1 or p.x > stem[1] + 1)]
    if len(ends) != 4:
        raise ValueError(f"{name}: {len(ends)} bar-end points in the band, 4 expected")
    w0 = g.width
    for p in ends:
        p.x -= d
    return 0, w0, g.width


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-t", action="store_true", help="t itself is done already")
    ap.add_argument("--ligatures", action="store_true", help="the Regular's ligatures with t")
    ap.add_argument("--glyphs", nargs="*", default=[], help="stored glyphs made from t, by name (Regular only)")
    args = ap.parse_args()
    style = next(s for s in STYLES if f"-{s}.ufo" in args.ufo.rstrip("/") + "")
    font = ufoLib2.Font.open(args.ufo)
    if not args.skip_t:
        shift, w0, w1 = centre(font, STYLES[style])
        print(f"{style} t: bar ends -{STYLES[style]['d']}, glyph shifted {shift:+d}, advance {w0} -> {w1}")
    if args.glyphs:
        if style != "Regular":
            raise SystemExit("--glyphs: the Regular's stored glyphs only; the generated styles remake theirs")
        for n in args.glyphs:
            print(n, centre_band(font, n, (836, 884), (210, 372), STYLES[style]["d"]))
    if args.ligatures:
        if style != "Regular":
            raise SystemExit("--ligatures: the Regular's; the other styles' ligatures are made by their own scripts")
        for n, ends in LIGATURE_ENDS.items():
            print(n, centre_ends(font, n, ends, STYLES[style]["d"]))
    if not args.dry_run:
        font.save()
        print("saved: make normalize now")


if __name__ == "__main__":
    sys.exit(main())
