#!/usr/bin/env python3
"""The Regular's old-style figures at the weight of the lowercase.

    python scripts/lighten_figures.py [UFO] [--dry-run]

Upstream's old-style figures stood heavier than the text around them: their
thick strokes 12-26 % over the lowercase's (the 0 208 to o's 184, the 1 184
to n's 164), where GFS Didot, Libertinus and EB Garamond draw them at about
the lowercase's weight. Each figure's thick strokes are made lighter (the
hairlines left as they are: make_italic.weight_thick, negative) to 1.03 of
its reference: n's stem for the straight figures (1 4 7), o's side for the
round ones; then they are spaced again by their shapes (space_figures.py,
which rebuilds the tabular .tf ones). The Bold follows when make_bold.py
runs; the Italic's figures are made lighter already (make_italic.py).

Recorded in lib org.myiadidot.figuresLightened; a second run refuses.
"""

import argparse
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))

ROOT = Path(__file__).resolve().parent.parent
KEY = "org.myiadidot.figuresLightened"
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
STRAIGHT = {"one", "four", "seven"}
OVER = 1.03  # the figures' thick strokes over their reference


def thick(font, name, xh):
    """A figure's thick stroke: the median, over heights across the
    x-height, of its widest span no wider than a stroke can be (a bar or
    the 2's foot is not a stroke)."""
    from derived import Outline

    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    o = Outline(font, name, (1, 0, -slant, 1, 0, 0))
    widths = []
    for k in (0.3, 0.4, 0.5, 0.6, 0.7):
        spans = [b - a for a, b in o.spans(xh * k + 0.37) if b - a < 0.4 * xh]
        if spans:
            widths.append(max(spans))
    widths.sort()
    return widths[len(widths) // 2] if widths else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("--dry-run", action="store_true", help="measure and say, change nothing")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    if font.lib.get(KEY) and not args.dry_run:
        sys.exit(f"{args.ufo}: figures lightened already ({font.lib[KEY]})")
    from make_italic import weight_thick
    from space_figures import space

    xh = font.info.xHeight
    ref = {"straight": thick(font, "n", xh), "round": thick(font, "o", xh)}
    done = {}
    for fig in FIGURES:
        name = fig + "oldstyle"
        kind = "straight" if fig in STRAIGHT else "round"
        now, target = thick(font, name, xh), OVER * ref[kind]
        amount = round(now - target)
        print(f"{name:14} thick {now:5.0f}  {kind} reference {ref[kind]:.0f} -> {target:.0f}: "
              + (f"{-amount}" if amount > 4 else "as it is"))
        if amount <= 4 or args.dry_run:
            continue
        g = font[name]
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
        g.clearContours()
        weight_thick(rec, -amount).draw(RoundingPen(g.getPen()))  # on whole units
        done[name] = -amount
    if args.dry_run:
        return
    space(font)
    font.lib[KEY] = done
    font.save()
    print(f"{args.ufo}: {len(done)} figures lighter, spaced again")


if __name__ == "__main__":
    main()
