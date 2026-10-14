"""Show how a precomposed character and its decomposition are drawn.

    python scripts/nfd_debug.py UFO CHARS...

Builds the UFO, shapes each character precomposed and decomposed (with the
precomposed code points removed from cmap so HarfBuzz cannot recompose) and
prints the glyphs and positions of both, plus each component's ink box.
"""

import sys
import tempfile
import unicodedata
from pathlib import Path

import ufo2ft
import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from conftest import Shaper


def boxes(gs, run):
    x, out = 0, []
    for name, adv, dx, dy in run:
        pen = BoundsPen(gs)
        gs[name].draw(pen)
        b = pen.bounds
        out.append(f"{name}" + (f"[{b[0] + x + dx:.0f},{b[1] + dy:.0f}..{b[2] + x + dx:.0f},{b[3] + dy:.0f}]" if b else "[]"))
        x += adv
    return " ".join(out)


def main():
    ufo = ufoLib2.Font.open(sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full.otf"
        ufo2ft.compileOTF(ufo, useProductionNames=False, optimizeCFF=0).save(full)
        font = TTFont(full)
        for table in font["cmap"].tables:
            for cp in list(table.cmap):
                if len(unicodedata.normalize("NFD", chr(cp))) > 1:
                    del table.cmap[cp]
        dec = Path(tmp) / "dec.otf"
        font.save(dec)
        a, b = Shaper(full), Shaper(dec)
        gs = TTFont(full).getGlyphSet()
        for ch in "".join(sys.argv[2:]):
            nfd = unicodedata.normalize("NFD", ch)
            print(f"{ch} U+{ord(ch):04X} = {' '.join(f'U+{ord(c):04X}' for c in nfd)}")
            print("  precomposed:", boxes(gs, a.shape(ch)))
            print("  decomposed: ", boxes(gs, b.shape(nfd)))


if __name__ == "__main__":
    main()
