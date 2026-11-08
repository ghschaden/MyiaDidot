"""Glyphs of a generated Bold or Bold Italic kept as drawn.

    python scripts/drawn.py UFO                                  # list them
    python scripts/drawn.py UFO GLYPH ... --date D --why TEXT    # mark
    python scripts/drawn.py UFO GLYPH ... --release              # unmark

A finished letter of the Bold or Bold Italic, fixed by hand (Fontra,
FontForge) or by a one-off script, is marked here; make_bold.py and
smallcaps.py then keep it as saved (outline, components, anchors, width,
lib) instead of making it anew, and build what is derived from it (its
accented forms, its small cap) from it. The generators still make every
other glyph, so a change meant for many letters goes into them; a fault in
one finished letter is fixed in that letter (2026-11-03: the
global repairs of the stroked Bold Italic moved hundreds of letters to fix
a few). The Italic's own mark is make_italic's "drawn" source.

A drawn glyph no longer follows the style it is made from: when its Italic
(or Regular) letter changes, `drawn.py UFO` lists it with the source's
change (built_from.fingerprint at marking) so it can be looked at again.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint

KEY = "org.myiadidot.drawn"


def saved(path):
    """{name: glyph} of the glyphs marked drawn in the UFO at path (empty
    when it does not exist yet)"""
    if not Path(path).exists():
        return {}
    font = ufoLib2.Font.open(path)
    return {g.name: copy.deepcopy(g) for g in font if KEY in g.lib}


def restore(kept, font, spaced=False):
    """the drawn glyphs put back into font, as saved; their names.
    spaced: put back on the side bearings the glyph made anew has in font
    now (make_bold before the derived letters are built: its spacing still
    to come would otherwise space the saved, finished glyph a second time,
    and its accented forms and ligatures with it, Bold Italic k 2026-11-04)"""
    for name, g in kept.items():
        g = copy.deepcopy(g)
        made = font[name] if spaced and name in font else None
        layer = font.layers.defaultLayer
        mb, gb = (made.getBounds(layer) if made is not None else None), g.getBounds(layer)
        if mb is not None and gb is not None:
            dx = round(mb.xMin - gb.xMin)
            g.move((dx, 0))
            g.width = round(gb.xMax + dx + made.width - mb.xMax)
        font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)
    return sorted(kept)


def stale(font, source):
    """drawn glyphs whose letter in source (the style made from) changed
    since they were marked: {name: mark}"""
    out = {}
    for g in font:
        mark = g.lib.get(KEY)
        if mark and g.name in source and mark.get("source") != fingerprint(source, g.name):
            out[g.name] = mark
    return out


def source_of(path):
    """the UFO a generated style is made from"""
    p = Path(path)
    return p.with_name(p.name.replace("BoldItalic", "Italic").replace("Bold", "Regular"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--why")
    ap.add_argument("--release", action="store_true")
    args = ap.parse_args()
    if "Bold" not in Path(args.ufo).name:
        raise SystemExit("only the generated Bold and Bold Italic (the Italic: make_italic's 'drawn')")
    font = ufoLib2.Font.open(args.ufo)
    source = ufoLib2.Font.open(source_of(args.ufo))
    if not args.glyphs:
        old = stale(font, source)
        for g in font:
            if KEY in g.lib:
                note = "  (its source letter changed since)" if g.name in old else ""
                print(f"{g.name}: {g.lib[KEY]['date']} {g.lib[KEY]['why']}{note}")
        return
    for name in args.glyphs:
        if args.release:
            font[name].lib.pop(KEY, None)
        else:
            if not (args.date and args.why):
                raise SystemExit("--date and --why are needed to mark a glyph drawn")
            font[name].lib[KEY] = {"date": args.date, "why": args.why,
                                   "source": fingerprint(source, name) if name in source else ""}
    font.save()
    print(f"{'released' if args.release else 'drawn'}: {len(args.glyphs)}")


if __name__ == "__main__":
    main()
