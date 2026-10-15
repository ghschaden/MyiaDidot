"""Derive the Bold master from the Regular.

    python scripts/make_bold.py [REGULAR.ufo] [BOLD.ufo]

A Didone bold is mostly the regular with heavier stems: the hairlines stay
nearly as fine, so the contrast grows. Every outline of a letter, figure or
sign is scaled across by KX (so the counters do not close up), its upright
strokes thickened by AX and its horizontal ones by AY (moving the outline
along its normals), and shifted right by AX/2, its advance growing by AX.
Accents and marks are only made a little heavier (MARK_AX, MARK_AY) and stay
where they are. Anchors and the offsets of components move with the
outlines, so composites land where the Regular's would; those the anchor
rules of composites.py can make are then rebuilt from the Bold's anchors,
after its stacking anchors are recomputed from its ink. Kerning is scaled
by KX, and so are the horizontal values of the hand-set positioning in the
features. Pinholes and crumbs the emboldening leaves are cleaned
(glyph_lint.py). Afterwards: smallcaps.py on the Bold, make normalize.

This regenerates the whole Bold from the Regular: until the Bold has its own
reviewed edits, rerun it after changes to the Regular.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composites import SPECIAL, Builder, stack_anchors
from derive import embolden
from glyph_lint import fix

ROOT = Path(__file__).resolve().parent.parent
KX = 1.04  # widening, so the counters keep their light
AX, AY = 90, 8  # stems 164 -> 254 (lowercase), 208 -> 298 (capitals); hairlines +8
MARK_AX, MARK_AY = 30, 8  # accents a little heavier


def mark_like(g):
    """Accents and combining marks: zero width, the spacing modifier
    symbols (´ ˆ ΄ ᾿ ..., whatever their width) and the unencoded 880-wide
    spacing accents (Acute ...)."""
    if g.width == 0:
        return True
    if g.unicode is not None:
        return unicodedata.category(chr(g.unicode)) in ("Sk", "Mn")
    return g.width == 880


def attach_point(font, mark, bases, centre):
    """Where a mark component attaches, in the Regular's composite and in the
    Bold's: the anchor of the base component nearest to the mark's ink, or
    failing that the mark's own attachment point (centre)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    mdx, mdy = mark.transformation[4], mark.transformation[5]

    def moved(x):  # unanchored: the composite's outline moves so
        return x, x * KX + AX / 2

    if ink is None:
        return moved(mdx + centre[mark.baseGlyph])
    mx, my = mdx + (ink[0] + ink[2]) / 2, mdy + (ink[1] + ink[3]) / 2
    best = None
    for base, bdx, bdy in bases:
        for a in font[base].anchors:
            if a.name.startswith("_"):
                continue
            ax, ay = a.x + bdx, a.y + bdy
            d = abs(ax - mx) + abs(ay - my)
            if best is None or d < best[0]:
                # in the Bold: the base's anchor and its offset, rounded as
                # they are written, so the mark lands exactly where mark
                # positioning puts it
                best = (d, ax, round(a.x * KX + AX / 2) + round(bdx * KX))
    return best[1:] if best else moved(mdx + centre[mark.baseGlyph])


def contours_only(g):
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    return rec


def redraw(g, glyph):
    """Replace g's contours with those of glyph (an emboldened ufoLib2 Glyph)."""
    g.clearContours()
    pen = g.getPointPen()
    for c in glyph.contours:
        c.drawPoints(pen)


def write(font, path):
    """Save font as the Bold: a new UFO, or an existing one updated in place
    (its glyphs replaced, the files of glyphs no longer there removed)."""
    if not path.exists():
        font.save(path)
        return
    if not (path / "metainfo.plist").exists() or not (path / "layercontents.plist").exists():
        font.save(path, overwrite=True)  # what a failed run left: not a UFO yet
        return
    target = ufoLib2.Font.open(path)
    # delete only what is gone: deleting a glyph and inserting it again under
    # the same name gets its file removed on saving
    for name in [n for n in target.keys() if n not in font]:  # noqa: SIM118 (a Font iterates glyphs)
        del target[name]
    for g in font:
        target.layers.defaultLayer.insertGlyph(g, g.name, overwrite=True)
    target.info = font.info
    target.kerning = font.kerning
    target.groups = font.groups
    target.features = font.features
    target.lib = font.lib
    target.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("bold", nargs="?", default=str(ROOT / "sources/MyiaDidot-Bold.ufo"))
    args = ap.parse_args()
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    marks = {g.name for g in regular if mark_like(g)}
    # what a combining mark is made of is an accent too (the spacing
    # ypogegrammeni ͺ is a modifier letter, but uni0345 is built on it)
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            marks.add(g.components[0].baseGlyph)
    # where each mark attaches: its own _ anchor, else the convention's 440
    # (spacing accents) or -440 (combining marks); offsets then move as the
    # anchors do, so a precomposed letter matches mark positioning
    centre = {}
    for name in marks:
        own = [a.x for a in regular[name].anchors if a.name.startswith("_")]
        centre[name] = own[0] if own else (440 if regular[name].width else -440)
    # a spacing accent attaches where the combining mark made of it does
    # (that mark's anchor, 880 to the right): the Greek ones are not at 440
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            c = g.components[0]
            own = [a.x for a in g.anchors if a.name.startswith("_")]
            if own and c.baseGlyph in marks and round(c.transformation[4]) == -880:
                centre[c.baseGlyph] = own[0] + 880

    # the composites the anchor rules make as they are: rebuilt in the Bold
    builder = Builder(regular)
    rule_made = set()
    for g in regular:
        if not g.components or g.contours or g.unicode is None:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = builder.recipe(g.unicode)
        except ValueError:
            continue
        mine = [(c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components]
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) == sorted(mine):  # in any order
            rule_made.add(g.name)

    for g in font:
        is_mark = g.name in marks
        if g.contours:
            rec = contours_only(g)
            if is_mark:
                redraw(g, embolden(rec, MARK_AX, MARK_AY))
            else:
                wide = RecordingPen()
                rec.replay(TransformPen(wide, (KX, 0, 0, 1, 0, 0)))
                bold = embolden(wide, AX, AY)
                moved = ufoLib2.objects.Glyph()
                bold.draw(TransformPen(moved.getPen(), (1, 0, 0, 1, AX / 2, 0)))
                redraw(g, moved)
        if not is_mark:
            # the Regular's offsets, before any is changed below
            bases = [(c.baseGlyph, c.transformation[4], c.transformation[5])
                     for c in g.components if c.baseGlyph not in marks]
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                if c.baseGlyph in marks:
                    # the mark moves as the point it hangs on moves: the
                    # anchor of the base letter it sits on (nearest to it)
                    x, x_bold = attach_point(regular, c, bases, centre)
                    dx = dx + x_bold - x
                else:
                    dx = dx * KX
                c.transformation = (xx, xy, yx, yy, round(dx), dy)
            for a in g.anchors:
                a.x = round(a.x * KX + AX / 2)
            room = [(b, dx) for b, dx, _ in bases if dx > 0]
            if len(bases) == 1 and room and g.width == regular[room[0][0]].width + room[0][1]:
                # a capital given room on its left for its accent (Ἤ): as wide
                # as the base plus that room, rounded as the positioning rule is
                b, dx = room[0]
                g.width = round(regular[b].width * KX + AX) + round(dx * KX)
            elif g.width:
                g.width = round(g.width * KX + AX)

    font.kerning = {pair: round(v * KX) for pair, v in font.kerning.items()}
    # hand-set positioning (room for the accents of Greek capitals, ...):
    # horizontal placement and advance scale with the outlines
    font.features.text = re.sub(
        r"<(-?\d+) (-?\d+) (-?\d+) (-?\d+)>",
        lambda m: f"<{round(int(m[1]) * KX)} {m[2]} {round(int(m[3]) * KX)} {m[4]}>",
        font.features.text)

    info = font.info
    info.styleName = "Bold"
    info.styleMapStyleName = "bold"
    info.openTypeOS2WeightClass = 700
    info.postscriptFontName = "MyiaDidot-Bold"
    info.postscriptFullName = "Myia Didot Bold"
    info.openTypeOS2Selection = [s for s in (info.openTypeOS2Selection or []) if s != 7]

    log = []
    stack_anchors(font, log)
    bold_builder = Builder(font)
    rebuilt = 0
    for name in sorted(rule_made):
        g = font[name]
        r = bold_builder.recipe(g.unicode)
        r.name = name
        lib = dict(g.lib)
        del font[name]
        bold_builder.write(r)
        font[name].lib.update(lib)
        rebuilt += 1
    # letters drawn with their accent in one outline (Ť, Ǫ): in the Bold their
    # accent would be thickened like a letter; made from base and mark like
    # the decomposed text, unless the Regular already renders them apart
    exceptions = {line.split()[0] for line in (ROOT / "tests/data/nfd-exceptions.txt").read_text().splitlines()
                  if line.startswith("U+")}
    outlined = 0
    for g in list(font):
        if g.unicode is None or not g.contours or g.components or f"U+{g.unicode:04X}" in exceptions:
            continue
        if g.name in SPECIAL:  # upstream's deliberate designs stay as drawn (Ǻ)
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = bold_builder.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = g.name, dict(g.lib)
        del font[g.name]
        bold_builder.write(r)
        font[r.name].lib.update(lib)
        outlined += 1
    # what emboldening leaves: counters closed to pinholes, outlines crossing
    # themselves (glyph_lint)
    cleaned = fix(font)
    write(font, Path(args.bold))
    print(f"{args.bold}: {len(font)} glyphs, {rebuilt} composites rebuilt from anchors, "
          f"{outlined} outlined letters made from base and mark, {len(cleaned)} cleaned")


if __name__ == "__main__":
    main()
