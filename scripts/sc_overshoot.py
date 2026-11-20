#!/usr/bin/env python3
"""Bring the Regular's small caps' round overshoot to the capitals' own,
scaled to the small-cap height: O's 28 over 1434 is 20 over 1040.

A contour of a base small cap (name ends .sc, no further dot) whose top
lies 15..30 past the small-cap height, or whose bottom lies 15..30 below
the baseline, has its points past the zone moved so that the extreme
sits at TARGET; nodes and handles together, by the same factor. Flat
letters (overshoot under 15) and tails (over 30) are left. Run on the
Regular; in the generated styles only on glyphs marked drawn (the
generators keep those as saved), the slant followed
(--drawn-only).

    .venv/bin/python -I scripts/sc_overshoot.py [--write] [--drawn-only] [UFO]
"""
import math
import sys

import ufoLib2

HEIGHT = 1040
TARGET = 20
LOW, HIGH = 15, 30


def run(path, write, drawn_only=False):
    font = ufoLib2.Font.open(path)
    height = font.lib.get("org.myiadidot.smallcapHeight", HEIGHT)
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    changed = []
    for g in font:
        if not g.name.endswith(".sc") or "." in g.name[:-3] or g.components:
            continue
        if drawn_only and "org.myiadidot.drawn" not in g.lib:
            continue
        hit = False
        for c in g.contours:
            ys = [p.y for p in c.points]
            top, bot = max(ys) - height, -min(ys)
            for sign, extreme in ((1, top), (-1, bot)):
                if not LOW <= extreme <= HIGH or abs(extreme - TARGET) <= 1:
                    continue
                # only the extreme's own nodes and handles (the same y, as the
                # round's tangent is level there) move; a point beside it that
                # stays would otherwise have its tangent bent
                zone = height if sign > 0 else 0
                want = zone + sign * TARGET
                for p in c.points:
                    if abs(sign * (p.y - zone) - extreme) <= 1:
                        p.x += round((want - p.y) * slant)  # along the slant
                        p.y = want
                hit = True
        if hit:
            changed.append(g.name)
    print(f"{path}: {len(changed)} glyphs", *changed[:400])
    if write:
        font.save()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run(args[0] if args else "sources/MyiaDidot-Regular.ufo", "--write" in sys.argv,
        "--drawn-only" in sys.argv)
