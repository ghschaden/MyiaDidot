"""Derive the Bold master from the Regular (and the Bold Italic from the Italic).

    python scripts/make_bold.py [REGULAR.ufo] [BOLD.ufo]
    python scripts/make_bold.py sources/MyiaDidot-Italic.ufo sources/MyiaDidot-BoldItalic.ufo

A Didone bold is mostly the regular with heavier stems: the hairlines stay
nearly as fine, so the contrast grows. Every outline of a letter, figure or
sign is scaled across by KX (so the counters do not close up), its upright
strokes thickened by AX and its horizontal ones by AY (moving the outline
along its normals), and shifted right by AX/2, its advance growing by AX.
Accents and marks are only made a little heavier (MARK_AX, MARK_AY) and stay
where they are. Anchors and the offsets of components move with the
outlines, so composites land where the Regular's would; those the anchor
rules of composites.py can make are then rebuilt from the Bold's anchors,
after its stacking anchors are recomputed from its ink. The letters are then
spaced tighter (BOLD_CUT, scripts/respace.py). Kerning is scaled
by KX, and so are the horizontal values of the hand-set positioning in the
features. Pinholes and crumbs the emboldening leaves are cleaned
(glyph_lint.py). Afterwards: smallcaps.py on the Bold, make normalize.

This regenerates the whole Bold from the Regular: until the Bold has its own
reviewed edits, rerun it after changes to the Regular. From an italic
source (the Bold Italic from the Italic) the same is done in the upright
frame: each outline, anchor and offset deslanted by the source's italic
angle, emboldened, and slanted again (tx), so the stems gain AX across.
"""

import argparse
import math
import re
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import KEY as BUILT_KEY
from composites import SPECIAL, Builder, stack_anchors
from derive import embolden, embolden_simple, rezone
from glyph_lint import fix
from respace import CUT_KEY, classifier, respace, sidebearings
from space_figures import space as space_figures

ROOT = Path(__file__).resolve().parent.parent
KX = 1.04  # widening, so the counters keep their light
AX, AY = 90, 8  # stems 164 -> 254 (lowercase), 208 -> 298 (capitals); hairlines +8
MARK_AX, MARK_AY = 30, 8  # accents a little heavier
# lib: derived letters left emboldened whole, with why (follow_bases);
# tests/test_emboldened.py holds them to a list that only shrinks
WHOLE_KEY = "org.myiadidot.emboldenedWhole"
# recipes that scale or reshape their one source outline, adding no piece:
# no junction to thicken, emboldened whole as any letter is
RESHAPES = {"enlarge", "stretch", "superior", "lower", "ezh", "esh", "nodot"}
# the Bold's letters are spaced tighter than the Regular's (the Regular's
# sidebearings times KX), as a bold's are: 40 off each side in all of the
# Regular's 20 (times KX) and BOLD_CUT, Greek lowercase 25 of 10 and BOLD_CUT_GREEK
BOLD_CUT, BOLD_CUT_GREEK = 19, 15
# the Bold Italic's Greek lowercase tighter still: emboldened from the
# Italic's (Old Standard's) it stood 0.10 of an n n gap looser than its Latin
# against Greek references (scripts/quality/greek_pairs.py)
BOLD_ITALIC_CUT_GREEK = BOLD_CUT_GREEK + 16
# the figures, which respace.py leaves alone, are tighter too: emboldened
# they stand looser than the Bold's letters (1.08 of their side space, where
# bold text faces have 0.8-1.0); one cut for all keeps them tabular, and the
# figure space and dash keep their width
BOLD_FIGURE_CUT = 28
FIGURE_NAMES = {f"{n}{s}" for n in ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
                for s in ("", "oldstyle")} | {"uni2007", "figuredash"}
# t's right side tighter in the Bold: emboldened, it stood looser before
# straight letters than in bold text faces; г and є tight on the right, т on
# the left (measured, scripts/quality/pairs.py and colour.py)
BOLD_SIDEBEARINGS = {"t": (0, -40), "uni0433": (0, 34), "uni0454": (0, 30), "uni0442": (26, 0)}  # t; г є т
# Pair-level corrections measured after the Bold's global kerning scale.
BOLD_KERNING = {
    # Greek: σ's right side stood tight against the Greek references, as
    # the Bold's Latin sets them (scripts/quality/greek_pairs.py)
    ("public.kern1.sigma", "public.kern2.etatonos"): 81,  # ση
    ("public.kern1.sigma", "public.kern2.tau"): 77,  # στ
    ("public.kern1.sigma", "public.kern2.omicron"): 62,  # σο
    ("public.kern1.sigma", "public.kern2.iota"): 55,  # σι
    ("public.kern1.tau", "public.kern2.omega"): 49,  # τω
    ("n", "t"): -28,
    ("a", "t"): -45,
    ("a", "s"): -29,
    ("a", "u"): -24,
    ("k", "t"): -44,
    ("z", "t"): -25,
    ("f", "s"): -41,
    ("S", "m"): -28,
}
# the Bold Italic's own (from the Italic): none yet
ITALIC_SIDEBEARINGS = {}
ITALIC_ANCHOR_NUDGE = {}
# Bold Italic optical-pair corrections from the pinned-reference spacing
# comparison (scripts/quality/pairs.py). Values are final Bold Italic kern
# values in font units; they are applied after the source kerning is scaled.
# Most pairs had no source pair adjustment. va overrides its inherited class
# pair; fr is made 33 units looser relative to the references' range.
ITALIC_BOLD_KERNING = {
    # Greek against Greek references, as the Bold Italic's Latin sets them
    # (scripts/quality/greek_pairs.py)
    ("public.kern1.delta", "public.kern2.iota"): 78,  # δι
    ("public.kern1.omicron", "public.kern2.upsilon"): 69,  # ου
    ("public.kern1.tau", "public.kern2.iota"): -70,  # τι
    ("public.kern1.nu", "public.kern2.delta"): -76,  # νθ
    ("public.kern1.upsilon", "public.kern2.sigma1"): -80,  # υς
    ("public.kern1.tau", "public.kern2.epsilontonos"): -90,  # τε
    ("public.kern1.mugreek", "public.kern2.pi"): -100,  # μπ
    ("u", "t"): 41,
    ("w", "a"): 57,
    ("g", "h"): 43,
    ("f", "r"): -95,
    ("T", "h"): 237,
    ("g", "a"): 89,
    ("i", "f"): 75,
    ("G", "r"): 121,
    ("a", "f"): 66,
    ("a", "y"): 67,
    ("v", "a"): 50,
    ("u", "f"): 92,
    ("R", "e"): 39,
}
# the horn on u a little left: where the Regular's sits, the Bold's heavier
# foot leaves a ledge beside the stem (glyph_lint)
ANCHOR_NUDGE = {("u", "Horn"): -10}


def bridge(glyph, maxgap=24, overlap=8):
    """glyph with the narrow gaps between straight edges that face each other
    (serif ends that emboldening brought within maxgap: x's inner feet, the
    top of ч) filled, so the parts join instead of leaving a slit."""
    import math

    from derive import draw_path

    path = pathops.Path()
    for c in glyph.contours:
        c.draw(path.getPen())
    path = pathops.simplify(path)
    edges = []
    for c in glyph.contours:
        ons = [p for p in c.points if p.type]
        for p0, p1 in zip(ons, ons[1:] + ons[:1], strict=True):
            if p1.type == "line" and math.dist((p0.x, p0.y), (p1.x, p1.y)) >= overlap:
                edges.append(((p0.x, p0.y), (p1.x, p1.y)))
    fills = []
    for i, (a0, a1) in enumerate(edges):
        ax, ay = a1[0] - a0[0], a1[1] - a0[1]
        la = math.hypot(ax, ay)
        ux, uy = ax / la, ay / la
        for b0, b1 in edges[i + 1:]:
            bx, by = b1[0] - b0[0], b1[1] - b0[1]
            lb = math.hypot(bx, by)
            if (ux * bx + uy * by) / lb > -0.985:  # facing edges run opposite ways, parallel
                continue
            # B's distance from A's line, and their overlap along it
            gap = (b0[0] - a0[0]) * -uy + (b0[1] - a0[1]) * ux
            if not 0 < abs(gap) < maxgap:
                continue
            t = sorted(((b0[0] - a0[0]) * ux + (b0[1] - a0[1]) * uy, (b1[0] - a0[0]) * ux + (b1[1] - a0[1]) * uy))
            lo, hi = max(0, t[0]), min(la, t[1])
            if hi - lo < overlap:
                continue
            nx, ny = -uy * gap, ux * gap
            mid = (a0[0] + ux * (lo + hi) / 2 + nx / 2, a0[1] + uy * (lo + hi) / 2 + ny / 2)
            probe = pathops.Path()
            pen = probe.getPen()
            pen.moveTo((mid[0] - 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] - 0.5))
            pen.lineTo((mid[0] + 0.5, mid[1] + 0.5))
            pen.lineTo((mid[0] - 0.5, mid[1] + 0.5))
            pen.closePath()
            if pathops.op(path, probe, pathops.PathOp.INTERSECTION).bounds != (0, 0, 0, 0):
                continue  # ink between them: not a gap
            q = [(a0[0] + ux * lo, a0[1] + uy * lo), (a0[0] + ux * hi, a0[1] + uy * hi)]
            fill = pathops.Path()
            pen = fill.getPen()
            pen.moveTo(q[0])
            pen.lineTo(q[1])
            pen.lineTo((q[1][0] + nx, q[1][1] + ny))
            pen.lineTo((q[0][0] + nx, q[0][1] + ny))
            pen.closePath()
            fills.append(fill)
    if not fills:
        return glyph
    for f in fills:
        path = pathops.op(path, f, pathops.PathOp.UNION)
    out = ufoLib2.objects.Glyph()
    draw_path(None, glyph, out, path)
    return out


def slit(glyph, before, font):
    """Whether glyph (emboldened contours) has a fault the Regular's glyph
    (before) has not: a notch (a slit between parts that come close), a
    sliver or a twist (an outline crossing itself at a tight terminal)."""
    from glyph_lint import notch_findings, vector_findings

    def faults(g):
        p = pathops.Path()
        for c in g.contours:
            c.draw(p.getPen())
        if not p.contours:
            return 0
        only = ufoLib2.objects.Glyph()
        for c in g.contours:
            c.drawPoints(only.getPointPen())
        vec = [f for f in vector_findings(pathops.simplify(p)) if f[0] in ("sliver", "twist")]
        return len(notch_findings(font, only, p.bounds)) + len(vec)

    return faults(glyph) > faults(before)


def mark_like(g):
    """Accents and combining marks: zero width, the spacing modifier
    symbols (´ ˆ ΄ ᾿ ..., whatever their width) and the unencoded 880-wide
    spacing accents (Acute ...)."""
    if g.width == 0:
        return True
    if g.unicode is not None:
        return unicodedata.category(chr(g.unicode)) in ("Sk", "Mn")
    return g.width == 880


SLANT = 0.0  # the source's slant (tan of its italic angle), set in main()


def tx(x, y):
    """Where an x at height y lands in the Bold: in the upright frame scaled
    across by KX and moved AX / 2 right."""
    return (x - y * SLANT) * KX + AX / 2 + y * SLANT


def tx_offset(dx, dy):
    """A component offset in the Bold: scaled across in the upright frame."""
    return (dx - dy * SLANT) * KX + dy * SLANT


def attach_point(font, mark, bases, centre):
    """Where a mark component attaches, in the Regular's composite and in the
    Bold's: the anchor of the base component nearest to the mark's ink, or
    failing that the mark's own attachment point (centre)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    mdx, mdy = mark.transformation[4], mark.transformation[5]

    def moved(x, y):  # unanchored: the composite's outline moves so
        return x, tx(x, y)

    if ink is None:
        return moved(mdx + centre[mark.baseGlyph], mdy)
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
                best = (d, ax, round(tx(a.x, a.y)) + round(tx_offset(bdx, bdy)))
    return best[1:] if best else moved(mdx + centre[mark.baseGlyph], my)


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
    (its glyphs replaced, the files of glyphs no longer there removed). Its
    points, anchors and component offsets are rounded to whole units first,
    and what that leaves cleaned (glyph_lint). The Regular's record of what
    its derived glyphs were built from (built_from.py) is left behind: a
    generated style is checked by being generated again."""
    for g in font:
        g.lib.pop(BUILT_KEY, None)
        for c in g.contours:
            for p in c.points:
                p.x, p.y = round(p.x), round(p.y)
        for a in g.anchors:
            a.x, a.y = round(a.x), round(a.y)
        for c in g.components:
            xx, xy, yx, yy, dx, dy = c.transformation
            c.transformation = (xx, xy, yx, yy, round(dx), round(dy))
    fix(font)  # what rounding left (a unit's step)
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


def follow_bases(source, font, italic, kx=None, slant=None, skip=(), whole=None):
    """Derived letters (derive.py's recipes) made of the Bold's own base:
    emboldened whole, a letter's junctions (a slash meeting a stem, a tilde
    crossing a diagonal) thicken unlike its base's strokes, eating the stem
    beside them. One that is its base turned, mirrored or flipped (exactly,
    in the source) becomes the Bold base so moved; one that adds to its
    base without cutting any of it is joined with the Bold base, placed
    where the source's base sits in it, unless the emboldened letter keeps
    that base already. Letters that cut their base (a hook replacing a
    stem's end) stay as emboldened. kx and slant: the widening and the
    italic's slant (make_bold's by default; make_italic's weight pass uses
    it too, unwidened); skip: names to leave; whole: a dict that gets the
    letters left emboldened whole, with the reason. Returns the names
    changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import KEEPS, TRANSFORMS, Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    kx = KX if kx is None else kx
    slant = SLANT if slant is None else slant
    deslant = (1, 0, -slant, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        if c.endswith(".sc") and len(c) == 4:
            return cmap.get(ord(c[0]), derive.glyph_name(c[0])) + ".sc"
        return cmap.get(ord(c), derive.glyph_name(c)) if len(c) == 1 else c

    def ink(name):
        p = pathops.Path()
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(p.getPen())
        return p

    changed, failed = [], []
    whole = {} if whole is None else whole
    for ch, op, base, band in recipes(italic):
        name, base = resolve(ch), resolve(base)
        if name not in source or base not in source or base == "space" or name not in font or name in skip:
            continue
        g = font[name]
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        if g.components:
            continue
        if op not in KEEPS | TRANSFORMS:
            if op not in RESHAPES:
                whole[name] = f"{op}: cuts its base"
            continue
        mine = Outline(source, name, deslant)
        if mine.bounds is None:
            continue
        if op in TRANSFORMS:
            w = source[base].width
            sb = band if isinstance(band, str) else band[0] if isinstance(band, tuple) else "x"
            cy = derive.band_middle(source, sb) if op != "mirror" else 0
            a, _, _, d, e, f = {"turn": (-1, 0, 0, -1, w, 2 * cy), "mirror": (-1, 0, 0, 1, w, 0),
                                "flip": (1, 0, 0, -1, 0, 2 * cy)}[op]
            shares, _, _ = compare(Outline(source, base, (a, 0, -a * slant, d, e, f)), mine)
            if shares["exact"] < 0.98:
                whole[name] = f"{op}: not exactly its base so moved"
                continue
            # the same move of the Bold base, in the upright frame
            bw = font[base].width
            e = bw if op in ("turn", "mirror") else 0
            out = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            moved = TransformPen(TransformPen(TransformPen(out.getPen(), (1, 0, slant, 1, 0, 0)),
                                              (a, 0, 0, d, e, f)), deslant)
            rec.replay(moved)
            g.width = bw
        else:
            shares, dx, _ = compare(Outline(source, base, deslant), mine)
            # only a letter that keeps its whole base in the source: the
            # Italic's ɨ has the dot of its own, not i's, and would get both
            if shares["lost"] > 0.02:
                if op not in RESHAPES:
                    whole[name] = f"{op}: does not keep its whole base"
                continue
            # nothing to mend when the emboldened letter keeps its Bold base
            # (ʘ: O's outline, the dot inside); and Skia's union fails on
            # curves that coincide, as theirs then do
            if compare(Outline(font, base, deslant), Outline(font, name, deslant))[0]["lost"] <= 0.02:
                continue
            placed = pathops.Path()
            rec = DecomposingRecordingPen(font)
            font[base].draw(rec)
            rec.replay(TransformPen(placed.getPen(), (1, 0, 0, 1, dx * kx, 0)))
            # each simplified on its own first: a base rebuilt here (ə turned)
            # winds the other way, and in one path the two would cancel
            a, b = pathops.simplify(ink(name)), pathops.simplify(placed)
            out = pathops.op(a, b, pathops.PathOp.UNION)
            # the union holds all of both, row by row, or it failed (curves
            # that coincide): then the letter is left as emboldened
            joined = Outline(None, None, deslant, path=out)
            if any(compare(Outline(None, None, deslant, path=p), joined)[0]["lost"] > 0.01 for p in (a, b)):
                failed.append(name)
                whole[name] = f"{op}: the union with its base failed"
                continue
        out = pathops.simplify(out)
        glyph = ufoLib2.objects.Glyph()
        out.draw(glyph.getPen())
        redraw(g, glyph)
        changed.append(name)
    if failed:
        print("  derived letters left as emboldened (their union failed):", " ".join(failed))
    return changed


MIN_PIECE = 3000  # units²: an added piece (ɬ.sc's bar is 8000), not a sliver


def attached_small(source, font, italic):
    """Derived letters that attach a glyph scaled down to their base (ɬ's
    ring, the degree sign at 0.45; ⁂'s asterisks): emboldened whole, the
    small piece thickens like a stem and closes up. Made of the Bold base
    and the source's added parts, those emboldened at the weight of their
    scale (a ring at 0.45 gains 0.45 of a stem's AX), as the Bold degree
    sign scaled would be. Recipes that cut the base (Ɲ) stay as they are.
    Returns the names changed."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import derive
    from derived import Outline, compare, recipes
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    deslant = (1, 0, -SLANT, 1, 0, 0)
    cmap = {u: g.name for g in source for u in g.unicodes}

    def resolve(c):
        if c.endswith(".sc") and len(c) == 4:
            return cmap.get(ord(c[0]), derive.glyph_name(c[0])) + ".sc"
        return cmap.get(ord(c), derive.glyph_name(c)) if len(c) == 1 else c

    def path(f, name, t=(1, 0, 0, 1, 0, 0)):
        p = pathops.Path()
        rec = DecomposingRecordingPen(f)
        f[name].draw(rec)
        rec.replay(TransformPen(p.getPen(), t))
        return pathops.simplify(p)

    changed = []
    for ch, op, base, band in recipes(italic):
        if op != "attach" or band[1]:
            continue
        scales = [min(abs(sx), abs(sy)) for piece, _, _, (sx, sy, *_) in band[2]
                  if piece not in ("rect", "line", "poly", "curl")]
        if not scales or min(scales) >= 0.8:
            continue
        name, base = resolve(ch), resolve(base)
        if name not in source or name not in font or base not in source:
            continue
        if italic and source[name].lib.get("org.myiadidot.italicSource") != "derived":
            continue
        k = min(scales)
        mine = path(source, name, deslant)
        added = mine
        dx = 0
        if source[base].contours or source[base].components:
            _, dx, _ = compare(Outline(source, base, deslant), Outline(source, name, deslant))
            added = pathops.op(mine, path(source, base, (1, 0, -SLANT, 1, dx, 0)), pathops.PathOp.DIFFERENCE)
        # only the pieces the recipe added: where the source letter's edge
        # strays a unit from its base's (the Italic's), slivers are left
        kept = pathops.Path()
        for c in added.contours:
            if abs(c.area) >= MIN_PIECE:
                c.draw(kept.getPen())
        rec = RecordingPen()
        kept.draw(TransformPen(rec, (KX, 0, 0, 1, 0, 0)))
        heavier = embolden(rec, AX * k, AY)
        out = pathops.Path()
        heavier.draw(TransformPen(out.getPen(), (1, 0, 0, 1, AX / 2, 0)))
        if source[base].contours or source[base].components:
            b = path(font, base, (1, 0, -SLANT, 1, dx * KX, 0))
            out = pathops.op(pathops.simplify(out), b, pathops.PathOp.UNION)
            # the union holds all of the base, or it failed: left as it was
            if compare(Outline(None, None, path=b), Outline(None, None, path=out))[0]["lost"] > 0.01:
                continue
        glyph = ufoLib2.objects.Glyph()
        pathops.simplify(out).draw(TransformPen(glyph.getPen(), (1, 0, SLANT, 1, 0, 0)))
        redraw(font[name], glyph)
        changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("bold", nargs="?", default=str(ROOT / "sources/MyiaDidot-Bold.ufo"))
    args = ap.parse_args()
    global SLANT
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    angle = -(regular.info.italicAngle or 0)
    SLANT = math.tan(math.radians(angle))
    italic = bool(angle)
    nudge, extra = (ITALIC_ANCHOR_NUDGE, ITALIC_SIDEBEARINGS) if italic else (ANCHOR_NUDGE, BOLD_SIDEBEARINGS)
    up, down = (1, 0, -SLANT, 1, 0, 0), (1, 0, SLANT, 1, 0, 0)  # deslant, slant again
    marks = {g.name for g in regular if mark_like(g)}
    # the paragraphos ⸏ ⸐ ⸑, rules under a line: a mark's weight and
    # advance, though they have one (fontbakery: base_has_width)
    marks |= {g.name for g in regular if g.unicode in (0x2E0F, 0x2E10, 0x2E11)}
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
            if is_mark and not italic:
                redraw(g, embolden(rec, MARK_AX, MARK_AY))
            elif is_mark:
                flat = RecordingPen()
                rec.replay(TransformPen(flat, up))
                heavier = embolden(flat, MARK_AX, MARK_AY)
                sloped = ufoLib2.objects.Glyph()
                heavier.draw(TransformPen(sloped.getPen(), down))
                redraw(g, sloped)
            else:
                wide = RecordingPen()
                rec.replay(TransformPen(TransformPen(wide, (KX, 0, 0, 1, 0, 0)), up))
                bold = bridge(rezone(embolden(wide, AX, AY), AY))  # the flat edges kept on the zones
                if slit(bold, regular[g.name], regular):
                    # parts close to each other (x's inner serifs) closed to a
                    # slit: the rounder emboldening, which leaves them apart
                    bold = rezone(embolden_simple(wide, AX, AY), AY)
                moved = ufoLib2.objects.Glyph()
                bold.draw(TransformPen(TransformPen(moved.getPen(), down), (1, 0, 0, 1, AX / 2, 0)))
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
                    dx = tx_offset(dx, dy)
                c.transformation = (xx, xy, yx, yy, round(dx), dy)
            for a in g.anchors:
                a.x = round(tx(a.x, a.y)) + nudge.get((g.name, a.name), 0)
            room = [(b, dx) for b, dx, _ in bases if dx > 0]
            if len(bases) == 1 and room and g.width == regular[room[0][0]].width + room[0][1]:
                # a capital given room on its left for its accent (Ἤ): as wide
                # as the base plus that room, rounded as the positioning rule is
                b, dx = room[0]
                g.width = round(regular[b].width * KX + AX) + round(dx * KX)
            elif g.width:
                g.width = round(g.width * KX + AX)

    whole = {}
    followed = follow_bases(regular, font, italic, whole=whole)
    followed += attached_small(regular, font, italic)
    font.lib[WHOLE_KEY] = {n: why for n, why in sorted(whole.items()) if n not in followed}

    font.kerning = {pair: round(v * KX) for pair, v in font.kerning.items()}
    if italic:
        font.kerning.update(ITALIC_BOLD_KERNING)
    else:
        font.kerning.update(BOLD_KERNING)
    # hand-set positioning (room for the accents of Greek capitals, ...):
    # horizontal placement and advance scale with the outlines
    font.features.text = re.sub(
        r"<(-?\d+) (-?\d+) (-?\d+) (-?\d+)>",
        lambda m: f"<{round(int(m[1]) * KX)} {m[2]} {round(int(m[3]) * KX)} {m[4]}>",
        font.features.text)

    info = font.info
    info.styleName = "Bold Italic" if italic else "Bold"
    info.styleMapStyleName = "bold italic" if italic else "bold"
    info.openTypeOS2WeightClass = 700
    info.postscriptFontName = "MyiaDidot-BoldItalic" if italic else "MyiaDidot-Bold"
    info.postscriptFullName = "Myia Didot Bold Italic" if italic else "Myia Didot Bold"
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
    greek_cut = BOLD_ITALIC_CUT_GREEK if italic else BOLD_CUT_GREEK
    respace(font, classifier(font, BOLD_CUT, greek_cut))
    respace(font, lambda n: BOLD_FIGURE_CUT if n in FIGURE_NAMES else 0)
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf rebuilt)
    sidebearings(font, extra)
    done = regular.lib.get(CUT_KEY, {"cut": 0, "greekLower": 0})
    font.lib[CUT_KEY] = {"cut": round(done["cut"] * KX) + BOLD_CUT,
                         "greekLower": round(done["greekLower"] * KX) + greek_cut}
    write(font, Path(args.bold))
    print(f"{args.bold}: {len(font)} glyphs, {rebuilt} composites rebuilt from anchors, "
          f"{outlined} outlined letters made from base and mark, {len(followed)} derived letters "
          f"made of their Bold base, {len(cleaned)} cleaned")


if __name__ == "__main__":
    main()
