"""generate(name, style): one recipe glyph (attach, bar, curl, hook) of the
Bold or the Bold Italic made again on the finished base of its style, in
seconds, into a scratch UFO and a sheet (docs/claude/only.md, stage B, the
common case only: no stroker, no whole-font passes).

It does what make_bold.rederive does for one letter: the style's glyphs
deslanted (make_bold.SLANT set from the italic angle), derive.build,
drop_specks, fix, the style's side bearings, slant_back.

    .venv/bin/python -I scripts/only_glyph.py STYLE GLYPH... [--out DIR]
        [--override "{'Ƈ': ('attach', 'C', band)}"]

STYLE is Bold or BoldItalic; GLYPH a character. The scratch UFO is DIR/
<style>.ufo (default build/only_glyph), the sheet DIR/sheet.png. In code:
`generate("BoldItalic", "Ƈ", recipe=...)` returns the new glyph (slanted
back, advance set) and leaves sources/ alone. The outline equals the full
run's up to a translation in x (rederive then sets the old letter's side
bearings, and later passes shift again) and 1-2 units of the slant's
round trip; the advance is the recipe's own. Which letters a recipe
rests on (its base, the strokes' reference o) must be finished in the
style: a letter whose base is itself a recipe of the same run is not
safe here. The recipes' numbers are in the frame rederive meets, which the
saved font is not (later passes shift it): build/only_glyph/frame-STYLE.ufo,
written by one full run with MYIA_DUMP_FRAME=<path> (make_bold.rederive).
"""

import argparse
import copy
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "quality"))

import derive  # noqa: E402
import make_bold as mb  # noqa: E402
import ufoLib2  # noqa: E402
from fontTools.pens.svgPathPen import SVGPathPen  # noqa: E402

SOURCES = {"Bold": ("Regular", "Bold"), "BoldItalic": ("Italic", "BoldItalic")}


def _frame(style):
    """(source font, the style's font, the style's deslanted copy, italic)"""
    src, dst = SOURCES[style]
    source = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{src}.ufo")
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{dst}.ufo")
    angle = -(source.info.italicAngle or 0)
    mb.SLANT = math.tan(math.radians(angle))
    italic = bool(angle)
    if italic:
        mb.AX, mb.THIN, mb.THICK = mb.ITALIC_AX, mb.ITALIC_THIN, mb.ITALIC_THICK
    # the font as rederive meets it (MYIA_DUMP_FRAME, one full run), not the
    # saved one, which later passes shift: the recipes' numbers are in that frame
    dumped = ROOT / f"build/only_glyph/frame-{style}.ufo"
    if dumped.exists():
        up = ufoLib2.Font.open(dumped)
    else:
        print(f"warning: no {dumped.name}; the saved font's frame may differ from the recipes'", file=sys.stderr)
        up = copy.deepcopy(font)
    if italic:
        for g in up:
            mb.shear(g, -mb.SLANT)
    return source, font, up, italic


def _recipe(ch, italic, up, source):
    """(op, base, band, strokes scale) as rederive takes them"""
    own = (mb.ITALIC_BOLD_RECIPES if italic else mb.BOLD_RECIPES).get(ch)
    if own:
        op, base, band = own
        if isinstance(band, str):  # placed on the style's own glyphs
            band = {"fishhook_band": mb.fishhook_band, "lezh_band": mb.lezh_band}[band](up)
        return op, base, band, (1, 1)
    from derived import recipes

    found = [r for r in recipes(italic) if r[0] == ch]
    if not found:
        raise KeyError(f"{ch}: no recipe")
    _, op, base, band = found[0]
    (_, stem, hair), (_, stem0, hair0) = derive.strokes(up, "o"), derive.strokes(source, "o")
    scale = (stem / stem0, hair / hair0)
    if italic:
        from make_italic import recipe_scale

        tuned = recipe_scale(stem0, hair0, weight=0)
        scale = (scale[0] * tuned[0], scale[1] * tuned[1])
    return op, base, band, scale


def generate(style, ch, recipe=None, frame=None):
    """the glyph `ch` of STYLE made again by its recipe (or `recipe`, an
    (op, base, band) overriding it): (new glyph slanted back, name)"""
    source, font, up, italic = frame or _frame(style)
    cmap = {u: g.name for g in up for u in g.unicodes}
    name = derive.resolve(cmap, ch)
    op, base, band, scale = _recipe(ch, italic, up, source)
    if recipe:
        op, base, band = recipe
        scale = (1, 1)
    up.lib[derive.STROKE_KEY] = scale
    if len(base) == 1 or (derive.variant(base) and not base[0].isascii()):
        base = derive.resolve(cmap, base)
    tmp = f"_only.{name}"
    order, cats = up.glyphOrder, dict(up.lib.get("public.openTypeCategories", {}))
    try:
        new = derive.build(up, ch, op, base, band, tmp)
    finally:
        up.glyphOrder = order
        up.lib["public.openTypeCategories"] = cats
    mb.drop_specks(new)
    mb.fix(up, [tmp])
    delta = (mb.SOURCE_SPACING.get(name) if italic else derive.SPACING.get(ch))
    if delta:
        mb.sidebearings(up, {tmp: delta})
    glyph = ufoLib2.objects.Glyph()
    y0 = mb.XH / 2 if italic else 0
    mb.slant_back(new, glyph.getPen(), [(1, 0, mb.SLANT, 1, -mb.SLANT * y0, 0)],
                  italic and name not in mb.POINT_REPAIRS)
    glyph.width = new.width
    glyph.unicodes = [ord(ch)]
    del up[tmp]
    return glyph, name, font


def sheet(cells, out, box=(1050, -300, 900, 2000), w=300):
    """cells: (title, glyph, font) in one row-wrapped SVG, then PNG"""
    x0, y0, bw, bh = box
    n = 4
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * n}" height="{int(w * 1.4) * ((len(cells) + n - 1) // n)}" style="background:white">']
    for i, (t, g, f) in enumerate(cells):
        p = SVGPathPen(f)
        g.draw(p)
        ox, oy = (i % n) * w, (i // n) * int(w * 1.4)
        parts.append(f'<g transform="translate({ox},{oy})"><text x="6" y="16" font-size="13">{t}</text>'
                     f'<svg x="0" y="20" width="{w}" height="{int(w * 1.4) - 20}" viewBox="0 {-1700} {max(g.width, 800)} 2300">'
                     f'<g transform="scale(1,-1)"><path d="{p.getCommands()}" fill="#222"/></g></svg></g>')
    parts.append("</svg>")
    Path(out, "sheet.svg").write_text("".join(parts))
    subprocess.run(["rsvg-convert", str(Path(out, "sheet.svg")), "-o", str(Path(out, "sheet.png"))], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("style", choices=sorted(SOURCES))
    ap.add_argument("chars", nargs="+")
    ap.add_argument("--out", default=str(ROOT / "build/only_glyph"))
    ap.add_argument("--override", help="python dict {char: (op, base, band)}")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    over = eval(args.override) if args.override else {}
    frame = _frame(args.style)
    scratch = copy.deepcopy(frame[1])
    cells = []
    for ch in args.chars:
        glyph, name, font = generate(args.style, ch, over.get(ch), frame)
        scratch[name].clearContours()
        scratch[name].clearComponents()
        glyph.draw(scratch[name].getPen())
        scratch[name].width = glyph.width
        cells.append((f"{ch} {name}", glyph, font))
    scratch.save(out / f"{args.style}.ufo", overwrite=True)
    sheet(cells, out)
    print(out / f"{args.style}.ufo", out / "sheet.png")


if __name__ == "__main__":
    main()
