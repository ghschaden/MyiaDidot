"""Set OS/2 usWinAscent/usWinDescent to the font's bounding box.

    python scripts/set_win_metrics.py UFO...

Windows clips glyphs outside the win metrics, so they must cover every
glyph. Line spacing comes from the typo/hhea values (USE_TYPO_METRICS) and
is not affected.
"""

import sys

import ufoLib2
from fontTools.pens.boundsPen import ControlBoundsPen


def main():
    for path in sys.argv[1:]:
        ufo = ufoLib2.Font.open(path)
        ymin, ymax = 0, 0
        for g in ufo:
            pen = ControlBoundsPen(ufo)
            g.draw(pen)
            if pen.bounds:
                ymin, ymax = min(ymin, pen.bounds[1]), max(ymax, pen.bounds[3])
        asc, desc = round(ymax), round(-ymin)
        old = ufo.info.openTypeOS2WinAscent, ufo.info.openTypeOS2WinDescent
        ufo.info.openTypeOS2WinAscent, ufo.info.openTypeOS2WinDescent = asc, desc
        if old != (asc, desc):
            ufo.save()
        print(f"{path}: win {asc}/{desc} (was {old[0]}/{old[1]})")


if __name__ == "__main__":
    main()
