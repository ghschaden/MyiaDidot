"""Approved roman and italic old-style design inputs, including their reviewed spacing.

Frozen GLIFs preserve the accepted 2026-10-25 drawings rather than repeatedly
resizing their already resized output. Bold and Bold Italic inherit their
respective bases through the normal weighting generator. Lining figures
remain independent.
"""

from copy import deepcopy
from math import hypot
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import readGlyphFromString
from space_figures import slashed
from ufoLib2.objects import Glyph
from upright_aleph import add_extrema, fair_joins

DATA = Path(__file__).parent / "data" / "oldstyle-italic"
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
NAMES_KEY = "public.postscriptNames"


def production_name(name):
    """the compiled font's name of an old-style figure (one.osf, one.osf.tf,
    zero.osf.zero); None for any other glyph. Its source name, oneoldstyle,
    is the Adobe Glyph List's for U+F731: a PDF reader naming text by glyph
    gets the private-use character, one.osf reads as 1 (the figures are not
    encoded, onum reaches them; the person, 2026-11-03)"""
    base, dot, rest = name.partition(".")
    if base.endswith("oldstyle") and base.removesuffix("oldstyle") in FIGURES:
        return base.removesuffix("oldstyle") + ".osf" + dot + rest
    return None


def production_names(font):
    """{source name: compiled name} for font's old-style figures, as the
    UFO's public.postscriptNames (ufo2ft keeps every glyph it does not
    list under its own name)"""
    return {g.name: production_name(g.name) for g in sorted(font, key=lambda g: g.name) if production_name(g.name)}


def finish(font):
    names = [d + "oldstyle" for d in FIGURES]
    if font.info.styleName == "Bold":
        _bold_weight_and_fit(font)
    if font.info.styleName in ("Bold", "Bold Italic"):
        # Finish the inherited weighted curves without importing light outlines.
        from quality.checks import construction

        for name in names + ["zerooldstyle.zero"]:
            if not construction(font[name]):
                continue
            _remove_shallow_line_corners(font[name])
            add_extrema(font[name])
            fair_joins(font[name])
        return
    if font.info.styleName not in ("Regular", "Italic"):
        return
    data = DATA if font.info.styleName == "Italic" else DATA.with_name("oldstyle-regular")
    for name in names:
        design = Glyph()
        readGlyphFromString((data / (name + ".glif")).read_text(),
                           glyphObject=design, pointPen=design.getPointPen())
        glyph = font[name]
        glyph.clearContours()
        glyph.clearComponents()
        design.draw(glyph.getPen())
        glyph.width = design.width
    # Generate the slash from the final zero, without changing the independent
    # lining slash or adding construction records to this generated style.
    scratch = deepcopy(font)
    slashed(scratch)
    slash_name = "zerooldstyle.zero"
    glyph = font[slash_name]
    glyph.clearContours()
    glyph.clearComponents()
    scratch[slash_name].draw(RoundingPen(glyph.getPen()))
    glyph.width = font['zerooldstyle'].width
    add_extrema(glyph)
    fair_joins(glyph)
    if font.info.styleName == "Regular":
        from built_from import stamp

        stamp(font, slash_name, ["zerooldstyle"])
    tab = font['zero'].width
    for name in names + [slash_name]:
        glyph = font[name + '.tf']
        glyph.clearContours()
        glyph.clearComponents()
        glyph.getPen().addComponent(name, (1, 0, 0, 1, round((tab-font[name].width)/2), 0))
        glyph.width = tab


def _remove_shallow_line_corners(glyph):
    """Drop the tiny extra vertex left at the angular 3's weighted flag."""
    from quality.checks import construction

    flagged = {where for kind, where, _ in construction(glyph) if kind == "kink"}
    for contour in glyph.contours:
        points = contour.points
        for i in reversed(range(len(points))):
            p, a, b = points[i], points[i-1], points[(i+1) % len(points)]
            if f"{round(p.x)},{round(p.y)}" not in flagged:
                continue
            if p.type != "line" or b.type != "line" or not a.type:
                continue
            length = hypot(b.x-a.x, b.y-a.y)
            if not length:
                continue
            distance = abs((p.x-a.x)*(b.y-a.y)-(p.y-a.y)*(b.x-a.x))/length
            if distance < 4:
                del points[i]


def _bold_weight_and_fit(font):
    """Keep reduced Roman 3/5 at Bold weight and give the open 4 room."""
    from make_italic import weight_thick
    # A modest optical increase, applied once to generated bases. The old
    # sample-row metric is discontinuous on the 5's bowl and ball; chasing
    # an exact ratio there can overfill the whole drawing.
    key = "org.myiadidot.oldstyleBoldFinished"
    for name in ("threeoldstyle", "fiveoldstyle"):
        glyph = font[name]
        if glyph.lib.get(key):
            continue
        before = glyph.getBounds(font)
        rec = RecordingPen()
        glyph.draw(rec)
        out = weight_thick(rec, 20)
        after = out.getBounds()
        dx = (before[0]+before[2]-after[0]-after[2])/2
        glyph.clearContours()
        out.draw(TransformPen(RoundingPen(glyph.getPen()), (1, 0, 0, 1, dx, 0)))
        glyph.lib[key] = True
    glyph = font['fouroldstyle']
    # Its old automatic fit left negative bearings after the 25% narrowing.
    # 820 is 1.08 of the reviewed Regular advance, the normal Bold ratio.
    glyph.width = 820
    left, _, right, _ = glyph.getBounds(font)
    dx = round((glyph.width-(right-left))/2-left)
    if dx:
        for contour in glyph.contours:
            for point in contour.points:
                point.x += dx
        for anchor in glyph.anchors:
            anchor.x += dx
    tab = font['fouroldstyle.tf']
    tab.clearComponents()
    tab.getPen().addComponent('fouroldstyle', (1, 0, 0, 1, round((tab.width-glyph.width)/2), 0))
