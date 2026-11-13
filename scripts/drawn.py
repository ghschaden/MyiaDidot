"""Glyphs of a generated style (Italic, Bold, Bold Italic) kept as drawn.

    python scripts/drawn.py UFO                                  # list them
    python scripts/drawn.py UFO GLYPH ... --date D --why TEXT    # mark
    python scripts/drawn.py UFO GLYPH ... --release              # unmark

A finished letter of a generated style, fixed by hand (Fontra, FontForge)
or by a one-off script, is marked here (`org.myiadidot.drawn`, the one
mark: docs/claude/drawn.md); make_italic.py, make_bold.py and smallcaps.py
then keep it as saved (outline, components, anchors, width,
lib) instead of making it anew, and build what is derived from it (its
accented forms, its small cap) from it. The generators still make every
other glyph, so a change meant for many letters goes into them; a fault in
one finished letter is fixed in that letter (2026-11-03: the
global repairs of the stroked Bold Italic moved hundreds of letters to fix
a few). In the Italic, marking also sets the provenance
`org.myiadidot.italicSource` to "drawn" (read by the generators to decide
how a glyph is finished, never whether it is kept); releasing leaves it,
and the next make_italic run writes it anew. A style's mark never travels
to the style made from it (`strip`).

A drawn glyph no longer follows the style it is made from: when its Italic
(or Regular) letter changes, `drawn.py UFO` lists it with the source's
change (built_from.fingerprint at marking) so it can be looked at again.
"""

import argparse
import copy
import sys
from datetime import date as _date
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint

KEY = "org.myiadidot.drawn"
SOURCE_KEY = "org.myiadidot.italicSource"


def is_drawn(glyph):
    """the glyph is kept as saved by the generators of its style"""
    return KEY in glyph.lib


def light_italic(font):
    """the font is the (light) Italic, whose provenance key goes with the mark"""
    return bool(font.info.italicAngle) and (font.info.openTypeOS2WeightClass or 400) < 600


def mark(font, name, date, why, source_font=None):
    """name marked drawn in font, against its letter in source_font (the
    style it is made from; by default the UFO beside font's path,
    source_of, or none for an unsaved font)"""
    if source_font is None:
        source_font = _beside(font)
    font[name].lib[KEY] = {"date": date, "why": why,
                           "source": fingerprint(source_font, name) if name in source_font else ""}
    if light_italic(font):
        font[name].lib[SOURCE_KEY] = "drawn"


def mark_by_script(font, name, script):
    """a one-off repair script's mark (T7 retires them): in the Italic the
    one mark, dated today; in a bold style the Italic's provenance as these
    scripts always wrote it (stem_joins.hand_drawn reads it there)"""
    if light_italic(font):
        mark(font, name, _date.today().isoformat(), f"made by {script}")
    else:
        font[name].lib[SOURCE_KEY] = "drawn"


_SOURCES = {}


def _beside(font):
    path = source_of(font.path) if getattr(font, "path", None) else None
    if path is None or not path.exists():
        return ufoLib2.Font()
    if path not in _SOURCES:
        _SOURCES[path] = ufoLib2.Font.open(path)
    return _SOURCES[path]


def release(font, name):
    """the mark off name (its provenance left: the next run writes it anew)"""
    font[name].lib.pop(KEY, None)


def strip(font):
    """the mark off every glyph: a source style's glyphs taken into the style
    made from them (make_bold) are that style's to keep or not; the names"""
    out = [g.name for g in font if KEY in g.lib]
    for name in out:
        del font[name].lib[KEY]
    return out


def saved(path):
    """{name: glyph} of the glyphs marked drawn in the UFO at path (empty
    when it does not exist yet)"""
    if not Path(path).exists():
        return {}
    font = ufoLib2.Font.open(path)
    return {g.name: copy.deepcopy(g) for g in font if is_drawn(g)}


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
    """the UFO a generated style is made from: Italic and Bold from the
    Regular, Bold Italic from the Italic"""
    p = Path(path)
    if "BoldItalic" in p.name:
        return p.with_name(p.name.replace("BoldItalic", "Italic"))
    return p.with_name(p.name.replace("Italic", "Regular").replace("Bold", "Regular"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--date")
    ap.add_argument("--why")
    ap.add_argument("--release", action="store_true")
    args = ap.parse_args()
    if not any(k in Path(args.ufo).name for k in ("Bold", "Italic")):
        raise SystemExit("only the generated styles (Italic, Bold, Bold Italic): the Regular is the master")
    font = ufoLib2.Font.open(args.ufo)
    source = ufoLib2.Font.open(source_of(args.ufo))
    if not args.glyphs:
        old = stale(font, source)
        for g in font:
            if is_drawn(g):
                note = "  (its source letter changed since)" if g.name in old else ""
                print(f"{g.name}: {g.lib[KEY]['date']} {g.lib[KEY]['why']}{note}")
        return
    for name in args.glyphs:
        if args.release:
            release(font, name)
        else:
            if not (args.date and args.why):
                raise SystemExit("--date and --why are needed to mark a glyph drawn")
            mark(font, name, args.date, args.why, source)
    font.save()
    print(f"{'released' if args.release else 'drawn'}: {len(args.glyphs)}")


if __name__ == "__main__":
    main()
