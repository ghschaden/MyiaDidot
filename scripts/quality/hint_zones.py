"""hint_zones.py TTF|OTF [PPEM ...]: hinted contours off their alignment zone.

A zone is the top or bottom of a reference glyph (REFS: x, o, H, O, l, p,
h.sc, o.sc), in the font's own units.  Hinted, every contour whose top (bottom)
is at exactly that height should end on the reference's row; a contour any of
whose on-curve points ends half a pixel or more beyond it (M's apex poking
above the serif, A's apex snapped to the ascender zone instead of O's) is
listed, per ppem.  Only letters are measured (Unicode Lu Ll Lt Lo, and the
small caps, localized forms and ligatures made of them): accents, superiors,
tone letters and symbols that share a zone's height are not on the zone.
Heights that only some glyphs share are no zone: ttfautohint
has none for them, and a few contours at one height may rightly part (ɺ's top
and f's).

Measured with FreeType under both TrueType interpreters: v40 (what FreeType
uses now; it reports ClearType, so ttfautohint's ClearType stem modes run) and
v35 (the classic grayscale one, close to GDI).  An OTF is measured by whole
glyphs with FreeType's CFF engine (measure_cff).
"""
import ctypes
import sys
import unicodedata
from collections import Counter

import freetype
from fontTools.ttLib import TTFont

REFS = (("top", "x"), ("top", "o"), ("top", "H"), ("top", "O"), ("top", "l"),
        ("top", "h.sc"), ("top", "o.sc"),
        ("bot", "H"), ("bot", "o"), ("bot", "O"), ("bot", "p"))
OFF = 0.5
PPEMS = range(8, 33)  # text and heading sizes; above, overshoots are kept
INTERPRETERS = (40, 35)


def set_interpreter(version):
    value = ctypes.c_uint(version)
    freetype.FT_Property_Set(freetype.get_handle(), b"truetype", b"interpreter-version",
                             ctypes.byref(value))


def contours(glyf, name):
    """[(top, top points, bottom, bottom points, on-curve points)] of a glyph's
    contours, by point index in the glyf table."""
    g = glyf[name]
    if not g.numberOfContours or g.isComposite():
        return []
    coords, ends, flags = g.getCoordinates(glyf)
    out, start = [], 0
    for end in ends:
        on = [i for i in range(start, end + 1) if flags[i] & 1]
        if len(on) >= 2:
            top = max(coords[i][1] for i in on)
            bot = min(coords[i][1] for i in on)
            out.append((top, [i for i in on if coords[i][1] == top],
                        bot, [i for i in on if coords[i][1] == bot], on))
        start = end + 1
    return out


def letters(tt):
    """Glyph names of letters: encoded as one, or named after letters (h.sc,
    uni0436.loclBGR, f_f_j, ffi)."""
    by_name = {}
    for code, name in tt.getBestCmap().items():
        by_name.setdefault(name, code)

    def letter(name):
        if name in by_name:
            return unicodedata.category(chr(by_name[name])) in ("Lu", "Ll", "Lt", "Lo")
        return False

    out = set()
    for name in tt.getGlyphOrder():
        base = name.split(".")[0]
        parts = base.split("_") if "_" in base else [base]
        if all(letter(part) for part in parts) or (base not in by_name and base
                                                   and all(letter(c) for c in base)):
            out.add(name)
    return out


def outlines(tt):
    """The letters' contours, and {(side, height): reference glyph}."""
    glyf = tt["glyf"]
    order = set(tt.getGlyphOrder())
    keep = letters(tt)
    data = {n: contours(glyf, n) for n in tt.getGlyphOrder() if n in keep}
    zones = {}
    for side, ref in REFS:
        if ref in order and data[ref]:
            f = max if side == "top" else min
            zones.setdefault((side, f(c[0 if side == "top" else 2] for c in data[ref])), ref)
    return data, zones


def measure(path, ppems=PPEMS, interpreter=40):
    """{ppem: [(glyph, side, height, extreme, row, extreme of the contour's top
    (bottom) points, those points)]}."""
    data, zones = outlines(TTFont(path))
    set_interpreter(interpreter)
    face = freetype.Face(str(path))
    found = {}
    for ppem in ppems:
        face.set_pixel_sizes(0, ppem)
        ys = {}
        for n, cs in data.items():
            if cs:
                face.load_glyph(face.get_name_index(n.encode()), freetype.FT_LOAD_DEFAULT)
                ys[n] = [p[1] / 64 for p in face.glyph.outline.points]
        row = {}
        for (side, z), ref in zones.items():
            f = max if side == "top" else min
            row[(side, z)] = f(ys[ref][i] for c in data[ref] for i in c[4])
        found[ppem] = []
        for n, cs in data.items():
            for top, tops, bot, bots, on in cs:
                for side, z, idx in (("top", top, tops), ("bot", bot, bots)):
                    if (side, z) not in zones:
                        continue
                    f = max if side == "top" else min
                    v = f(ys[n][i] for i in on)
                    if abs(v - row[(side, z)]) >= OFF:
                        found[ppem].append((n, side, z, v, row[(side, z)], f(ys[n][i] for i in idx), idx))
    return found


def measure_cff(path, ppems=PPEMS):
    """The same for a CFF font, by whole glyphs (FreeType's CFF engine):
    letters whose top (bottom) is at a reference glyph's, off that glyph's
    row once hinted.  With the Private dict's zones a hinted edge on a zone
    falls on a whole pixel, so the rows must agree exactly (to 1/16 px),
    not within OFF.  {ppem: [(glyph, side, height, extreme, row)]}."""
    from fontTools.pens.boundsPen import BoundsPen

    tt = TTFont(path)
    gs = tt.getGlyphSet()

    def bounds(name):
        pen = BoundsPen(gs)
        gs[name].draw(pen)
        return pen.bounds

    keep = {n: bounds(n) for n in letters(tt)}
    keep = {n: b for n, b in keep.items() if b}
    zones = {}
    for side, ref in REFS:
        if ref in keep:
            zones.setdefault((side, keep[ref][3] if side == "top" else keep[ref][1]), ref)
    face = freetype.Face(str(path))
    found = {}
    for ppem in ppems:
        face.set_pixel_sizes(0, ppem)
        ext = {}
        for n in keep:
            face.load_glyph(face.get_name_index(n.encode()), freetype.FT_LOAD_DEFAULT)
            ys = [q[1] / 64 for q in face.glyph.outline.points]
            ext[n] = (min(ys), max(ys))
        found[ppem] = []
        for n, b in keep.items():
            for side, z, v in (("top", b[3], ext[n][1]), ("bot", b[1], ext[n][0])):
                ref = zones.get((side, z))
                if ref:
                    row = ext[ref][1 if side == "top" else 0]
                    if abs(v - row) > 1 / 16:
                        found[ppem].append((n, side, z, v, row))
    return found


def summary(found):
    per = Counter()
    for items in found.values():
        for n, side, z, *_ in items:
            per[f"{n}:{side}{z}"] += 1
    return per


def main():
    path = sys.argv[1]
    ppems = [int(a) for a in sys.argv[2:]] or PPEMS
    if "CFF " in TTFont(path):
        per = summary(measure_cff(path, ppems))
        print(f"CFF: {sum(per.values())} off-zone (glyph, ppem) in {len(per)} glyphs")
        for key, count in per.most_common():
            print(f"  {key} {count}")
        return
    for version in INTERPRETERS:
        per = summary(measure(path, ppems, version))
        print(f"v{version}: {sum(per.values())} off-zone (contour, ppem) in {len(per)} contours")
        for key, count in per.most_common():
            print(f"  {key} {count}")


if __name__ == "__main__":
    main()
