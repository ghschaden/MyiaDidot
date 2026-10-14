"""Build reference binaries straight from the upstream SFD with FontForge.

    fontforge -quiet -lang=py -script scripts/sfd_reference.py SRC.sfd OUTDIR

Mirrors upstream's theano-generate.py (OTF from the "Fore" layer, TTF from
the hand-made "TTF" layer) but keeps the 2048 UPM, so the result can be
compared 1:1 against our fontmake build.
"""

import os
import sys

import fontforge


def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    font = fontforge.open(src)
    font.generate(os.path.join(outdir, base + ".ttf"), flags=("opentype",), layer="TTF")
    font.generate(os.path.join(outdir, base + ".otf"), flags=("opentype",), layer="Fore")
    font.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
