"""Resize inherited accents, keeping their stroke weight.

    python scripts/adjust_accents.py UFO

Each accent in ADJUST is scaled about the middle of its foot (x = 440, the
bottom of its ink, so its distance from the letter stays), and its strokes
are brought back to their weight before the scaling. The factors applied
are recorded in the glyph's lib (org.myiadidot.adjusted), so running the
script again changes nothing. Afterwards: composites.py --stack-anchors
--rebuild-stacked, smallcaps.py.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import embolden
from smallcaps import ink_bounds

KEY = "org.myiadidot.adjusted"
# glyph: (scale across, scale up, side stroke, bottom stroke) - the strokes
# measured before scaling, restored after it
ADJUST = {
    # Theano's Latin breve is as wide as the circumflex and deeper than
    # usual; narrower and a little shallower, as in Libertinus and Charis
    "breve": (0.8, 0.85, 74, 96),
    "Breve": (0.8, 0.85, 112, 96),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    done = []
    for name, (kx, ky, side, bottom) in ADJUST.items():
        g = font[name]
        if g.lib.get(KEY) == [kx, ky]:
            continue
        y0 = ink_bounds(font, name)[1]
        rec = RecordingPen()
        g.draw(TransformPen(rec, (kx, 0, 0, ky, 440 * (1 - kx), y0 * (1 - ky))))
        out = embolden(rec, side * (1 - kx), bottom * (1 - ky))
        g.clearContours()
        out.drawPoints(g.getPointPen())
        g.lib[KEY] = [kx, ky]
        done.append(name)
    font.save()
    print("adjusted:", " ".join(done) or "nothing")


if __name__ == "__main__":
    main()
