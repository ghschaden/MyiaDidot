"""Draft small capitals with FontForge's stem-compensating generator.

    fontforge -quiet -lang=py -script scripts/smallcaps_draft.py SRC.ufo OUT.ufo \
        SCHEIGHT LCSTEM [GLYPH ...]

Opens SRC.ufo, runs addSmallCaps on the given capitals (default: every
encoded uppercase letter without components) and writes the whole font to
OUT.ufo; the generated drafts are the glyphs named "<lowercase>.sc", which
scripts/smallcaps.py imports. FontForge is only a drafting tool here:
the master stays the UFO, and every draft is meant to be reviewed.
"""

import sys
import unicodedata

import fontforge

CAP_HEIGHT = 1434
UC_STEM = 208


def main(src, out, scheight, lcstem, *names):
    font = fontforge.open(src)
    if not names:
        names = [
            g.glyphname for g in font.glyphs()
            if g.unicode > 0 and unicodedata.category(chr(g.unicode)) == "Lu"
            and not g.references and g.isWorthOutputting()
        ]
    font.selection.none()
    for n in names:
        font.selection.select(("more",), n)
    before = {g.glyphname for g in font.glyphs()}
    font.addSmallCaps(
        scheight=float(scheight),
        capheight=CAP_HEIGHT,
        lcstem=float(lcstem),
        ucstem=UC_STEM,
        symbols=False,
    )
    created = sorted({g.glyphname for g in font.glyphs()} - before)
    # FontForge's -quiet swallows stdout.
    sys.stderr.write(f"{len(names)} capitals selected, {len(created)} drafts: {' '.join(created)}\n")
    font.generate(out)
    font.close()


if __name__ == "__main__":
    main(*sys.argv[1:])
