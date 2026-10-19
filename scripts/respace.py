"""Tighten the spacing of the letters: take CUT units off each side.

    python scripts/respace.py UFO --cut 20 --greek-lower 10

Measured against other Didots and text faces (white beside the letters,
x-height-relative), Myia's letters were spaced loosely; the Regular took
20 off each side, its Greek lowercase (already ~10 % tighter than its
Latin) 10. Letters are what Unicode calls letters (Lu Ll Lt Lo; not the
modifier letters, which are mostly accents), and the glyphs made from them:
small caps, alternates, ligatures (by glyph name: "a.sc", "f_i"). Greek
small caps are capitals in form and take the full cut. Figures, punctuation,
signs, spaces and marks keep their spacing.

A cut glyph's outline and anchors move CUT left and its advance shrinks by
2 CUT. A component moves by the difference between its own cut and the
glyph's (a mark in a letter moves left with it, a letter in a letter not
at all), so composites stay where their anchors put them. Kerning is
unchanged. The cuts applied are recorded in the font's lib (CUT_KEY), and a
second run on the same font refuses. make_bold.py and make_italic.py call
respace() on what they make; make_italic.py, tuned on the Regular as it was,
first undoes the Regular's cut (undo()).
"""

import argparse
import sys
import unicodedata

import ufoLib2
from fontTools import agl

CUT_KEY = "org.myiadidot.respaced"
LETTERS = {"Lu", "Ll", "Lt", "Lo"}
NAMES = {"idotaccent": "i"}  # base names neither the font nor the AGL knows (i̇ is a letter)


def is_greek(ch):
    return 0x0370 <= ord(ch) <= 0x03FF or 0x1F00 <= ord(ch) <= 0x1FFF


def classifier(font, cut, greek_lower):
    """The cut for each glyph name: cut for letters, greek_lower for Greek
    lowercase (not their small caps), 0 for the rest."""
    named = {g.name: chr(g.unicode) for g in font if g.unicode is not None}

    def text(part):
        return named.get(part) or NAMES.get(part) or agl.toUnicode(part)

    def cut_for(name):
        g = font[name]
        if g.width == 0:
            return 0
        base, _, suffix = name.partition(".")
        chars = "".join(text(p) for p in base.split("_")) if base else ""
        if g.unicode is not None and "_" not in base and not suffix:
            chars = chr(g.unicode)
        if not chars or any(unicodedata.category(c) not in LETTERS for c in chars):
            return 0
        sc = suffix.split(".")[0] in ("sc", "c2sc")
        if not sc and all(is_greek(c) and unicodedata.category(c) == "Ll" for c in chars):
            return greek_lower
        return cut

    return cut_for


def respace(font, cut_for, names=None):
    """Apply the cuts (cut_for(name) -> units per side) to the glyphs named
    (all by default); returns how many glyphs changed."""
    cuts = {g.name: cut_for(g.name) for g in font}
    names = list(cuts) if names is None else names
    changed = 0
    for name in names:
        g = font[name]
        n = cuts[name]
        moved = False
        if n:
            for c in g.contours:
                for p in c.points:
                    p.x -= n
            for a in g.anchors:
                a.x -= n
            g.width -= 2 * n
            moved = True
        for c in g.components:
            d = cuts.get(c.baseGlyph, 0) - n
            if d:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, dx + d, dy)
                moved = True
        changed += moved
    return changed


def sidebearings(font, deltas):
    """Change sidebearings: deltas {glyph: (left, right)} in units (positive:
    more space). The glyphs built on one (accented letters, aliases: one of
    their components, at no offset) change with it; their marks move with
    the letter. Glyphs that use one otherwise keep their ink where it was.
    Returns the names changed."""
    d = dict(deltas)
    grown = True
    while grown:  # composites on composites
        grown = False
        for g in font:
            if g.name in d or not g.components or g.contours:
                continue
            base = next((c.baseGlyph for c in g.components if c.baseGlyph in d
                         and abs(c.transformation[4]) < 1 and abs(c.transformation[5]) < 1), None)
            if base:
                d[g.name] = d[base]
                grown = True
    for name, (dl, dr) in d.items():
        g = font[name]
        for c in g.contours:
            for p in c.points:
                p.x += dl
        for a in g.anchors:
            a.x += dl
        for c in g.components:
            shift = dl - d.get(c.baseGlyph, (0, 0))[0]
            if shift:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, dx + shift, dy)
        g.width += dl + dr
    # glyphs that use one elsewhere (ʼ as Ľ's caron, in ŉ) keep their ink
    for g in font:
        if g.name in d:
            continue
        for c in g.components:
            if d.get(c.baseGlyph, (0, 0))[0]:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, dx - d[c.baseGlyph][0], dy)
    return list(d)


def undo(font):
    """Put back the spacing a font had before respace (its lib records the
    cuts), for scripts tuned on it (make_italic.py reads the Regular so)."""
    done = font.lib.pop(CUT_KEY, None)
    if done:
        cut_for = classifier(font, done["cut"], done["greekLower"])
        respace(font, lambda n: -cut_for(n))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--cut", type=int, required=True, help="units off each side of a letter")
    ap.add_argument("--greek-lower", type=int, help="units off each side of Greek lowercase (default: --cut)")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    if CUT_KEY in font.lib:
        sys.exit(f"{args.ufo} was respaced already ({font.lib[CUT_KEY]}); not cutting twice")
    greek = args.cut if args.greek_lower is None else args.greek_lower
    changed = respace(font, classifier(font, args.cut, greek))
    font.lib[CUT_KEY] = {"cut": args.cut, "greekLower": greek}
    font.save()
    print(f"{args.ufo}: {changed} glyphs respaced ({args.cut} per side, Greek lowercase {greek})")


if __name__ == "__main__":
    main()
