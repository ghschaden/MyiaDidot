"""Set OS/2 usWinAscent/usWinDescent to the bounding box of the family.

    python scripts/set_win_metrics.py UFO...

Windows clips glyphs outside the win metrics, so they must cover every
glyph; all the UFOs given (the styles of one family) get the same values,
the largest over all of them, so the styles keep one line spacing on
Windows. Line spacing elsewhere comes from the typo/hhea values
(USE_TYPO_METRICS) and is not affected.
"""

import sys

import ufoLib2
from fontTools.pens.boundsPen import ControlBoundsPen


def main():
    ufos = [(path, ufoLib2.Font.open(path)) for path in sys.argv[1:]]
    ymin, ymax = 0, 0
    for _path, ufo in ufos:
        for g in ufo:
            pen = ControlBoundsPen(ufo)
            g.draw(pen)
            if pen.bounds:
                ymin, ymax = min(ymin, pen.bounds[1]), max(ymax, pen.bounds[3])
    asc, desc = round(ymax), round(-ymin)
    for path, ufo in ufos:
        old = ufo.info.openTypeOS2WinAscent, ufo.info.openTypeOS2WinDescent
        ufo.info.openTypeOS2WinAscent, ufo.info.openTypeOS2WinDescent = asc, desc
        if old != (asc, desc):
            ufo.save()
        print(f"{path}: win {asc}/{desc} (was {old[0]}/{old[1]})")


if __name__ == "__main__":
    main()
