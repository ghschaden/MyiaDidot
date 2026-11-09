"""Make the Italic master: Old Standard's italic in Myia's frame.

    python scripts/make_italic.py [REGULAR.ufo] [ITALIC.ufo] [--redraft]

The letters, figures and signs come from Old Standard Italic (Alexey
Kryukov, SIL OFL 1.1; sources/oldstand, converted with FontForge once and
kept there: fontforge_inputs.py, make oldstand), the cursive companion by Theano's own designer. They are
scaled in zones so that its x-height (456 of 1000) lands on Myia's 884 and
its capitals and ascenders (712) on 1434, the descenders in proportion;
their stems and hairlines as Old Standard's (AX, AY), the thick strokes
then made a little heavier (WEIGHT, CAP_WEIGHT). The
glyph set, features, accents and marks are Myia's: the accents sloped to
the italic angle (with their anchors), the accented letters rebuilt from
the anchors by the rules of composites.py, upstream's special composites
kept with each accent moved as the anchor it sits on moves.

What Old Standard does not have is made from what it has, in an upright
frame (the whole font unslanted, the glyph made, slanted again), so that
recipes tuned on the upright Regular apply and mirroring keeps the slant:
the letters of derive.py's recipes (IPA, African, Cyrillic extras), the
old-style figures (its lining figures fitted to the Regular's), the small
caps (FontForge's drafts of its capitals, as for the Regular). Arrows,
geometric shapes and circled letters stay upright, the Regular's. What is left is the roman
sloped. Then smallcaps.py runs on the Italic (accented small caps,
features). Afterwards: make normalize.

Each glyph's lib key org.myiadidot.italicSource says where it came from.
A rerun keeps what was reviewed: glyphs marked "drawn" (hand-edited: set
it after editing any glyph), and drafts ("derived", "figure draft",
"small cap draft") whose draft key has been cleared, as long as the
weights and cuts (MADE_WITH) are those they were made with.
"""

import argparse
import copy
import math
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arithmetic  # noqa: F401  (first: one thread, AVX2 at most, before numpy loads)
import case_forms
import kern_clear
from composites import SPECIAL, Builder, stack_anchors
from derive import BIG, draw_path, embolden, rezone
from fontforge_inputs import source_font
from italic_geometry import ANGLE, CAP, SLANT, XH, shear, upright
from make_bold import WHOLE_KEY, mark_like, redraw, write
from respace import CUT_KEY, classifier, respace, sidebearings, undo
from smallcaps import ink_bounds, ink_slice
from space_figures import space as space_figures

ROOT = Path(__file__).resolve().parent.parent
KX = 1.98  # across: between the x-height (1.939) and cap-height (2.014) scales
OS_XH, OS_CAP = 456, 712
# Old Standard's strokes as they are, scaled (AX, AY across and up: none),
# their thick upright strokes made WEIGHT heavier as they are taken
# (weight_thick: hairlines and thin strokes as they are), the capitals
# CAP_WEIGHT. All made of them (derived letters, small caps, figures) is
# built from those weighted letters, as the Bold's are from the Bold's: a
# letter weighted on its own thickens at its junctions unlike its base. Thinned hairlines (-16, -10) and stems at the
# Regular's (+44) gave a contrast of 4.6 where italics have 3.1-4.2 and a
# colour twice as uneven as Old Standard's (letters of thick strokes, a b g q,
# and the capitals dark, hairline ones light), hard to read on a full page;
# chosen from full pages of variants (2026-10-21)
AX, AY = 0, 0
WEIGHT = 10
CAP_WEIGHT = 0
# what the recipes' drawn strokes (ITALIC_RECIPES' lines and curls, by
# number) were tuned at: Old Standard's strokes thinned by (-16, -10). They
# are drawn scaled to the strokes as they are now (recipe_scale), so a
# descender stays as heavy as the stem it continues
TUNED_AX, TUNED_AY = -16, -10


def recipe_scale(stem, hair, weight=WEIGHT):
    """derive.STROKE_KEY for the Italic's recipes: an o's stem (WEIGHT
    added) and top hairline as they are, against what the numbers were
    tuned at (Old Standard's, thinned by TUNED_AX, TUNED_AY): a drawn
    stroke comes at the stem with the weight of the letter it is drawn on
    (weight: CAP_WEIGHT on a capital's tail)."""
    return (stem - WEIGHT + weight) / (stem - WEIGHT - AX + TUNED_AX), hair / (hair - AY + TUNED_AY)
# off each side of a letter: Old Standard's spacing, scaled, is loose for
# its narrow letters (side space 0.180 of the x-height at a cut of 3, Bodoni
# Moda's and Libre Bodoni's italics 0.172 and 0.162); 13 more chosen
# from full pages cut 10, 13 and 16 more (2026-10-21)
ITALIC_CUT = 16
# the Greek lowercase tighter: Old Standard's Greek, so cut, stood 0.07 of an
# n n gap looser than the Italic's Latin against Greek references
# (scripts/quality/greek_pairs.py)
ITALIC_CUT_GREEK = ITALIC_CUT + 11
# the weights and cuts the reviewed drafts were made with (font lib): a
# rerun with others keeps none of them (kept glyphs are neither weighted nor
# respaced again), they come back as drafts to review
MADE_WITH_KEY = "org.myiadidot.italicMadeWith"
MADE_WITH = {"weight": [AX, AY, WEIGHT, CAP_WEIGHT], "cut": [ITALIC_CUT, ITALIC_CUT_GREEK]}
SOURCE_KEY = "org.myiadidot.italicSource"
DRAFT_KEY = "org.myiadidot.draft"
SMALLCAP_DRAFT_KEY = "org.myiadidot.smallcapDraft"
FIGURES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def capital(font, g):
    """g a capital letter, or an unencoded form of one (Ж.loclBGR)"""
    u = g.unicode
    if u is None:
        base = g.name.split(".")[0]
        u = font[base].unicode if base in font else None
    return u is not None and unicodedata.category(chr(u)) in ("Lu", "Lt")


def reviewed(g):
    """A glyph a rerun must keep: hand-drawn, or a draft that was reviewed."""
    src = g.lib.get(SOURCE_KEY)
    if src == "drawn":
        return True
    return (src in ("derived", "figure draft", "small cap draft")
            and not g.lib.get(DRAFT_KEY) and not g.lib.get(SMALLCAP_DRAFT_KEY))


# signs Old Standard draws for mathematics, far larger than Myia's (+ is
# 1861 wide to the Regular's 1152), and its raised and lowered + − =: the
# Regular's are taken instead, upright
MATH_SIGNS = set(map(ord, "+<=>±×÷¬−≈≠≤≥⁺⁻⁼₊₋₌⊗"))
# Myia's own, sloped, though Old Standard has them: the guillemets
# (draft_symbols.py's chevrons; Old Standard's are small crescents)
# θ closed, not the cursive form Old Standard shares with ϑ: IPA needs the
# two apart; æ ɐ ᵃ the roman's, sloped, keeping the two-storey a apart from
# ɑ as in the roman (Old Standard's æ, of the one-storey a, read as œ; ɐ
# turned from it read as ɒ)
ROMAN_SIGNS = set(map(ord, "‹›θæɐᵃ"))
# unencoded glyphs taken the same way: a in IPA text (locl IPPH)
ROMAN_GLYPHS = {"a.ipa"}


def keeps_upright(u):
    """Signs an italic sets upright (the letterlike and mathematical
    letters 𝔐 𝑙 ℓ ℵ are slanted with the rest)."""
    return (0x2190 <= u <= 0x21FF or 0x2460 <= u <= 0x24FF or 0x25A0 <= u <= 0x25FF
            or 0x3000 <= u <= 0x303F or 0x23D1 <= u <= 0x23D9 or u in (0x22EE, 0x2042)
            or u in MATH_SIGNS)


def ymap(y):
    """Old Standard's heights to Myia's, zone by zone."""
    if y <= OS_XH:
        return y * XH / OS_XH
    return XH + (y - OS_XH) * (CAP - XH) / (OS_CAP - OS_XH)


class Zones(FilterPen):
    def _t(self, pts):
        return [(x * KX, ymap(y)) for x, y in pts]

    def moveTo(self, p):
        self._outPen.moveTo(*self._t([p]))

    def lineTo(self, p):
        self._outPen.lineTo(*self._t([p]))

    def curveTo(self, *ps):
        self._outPen.curveTo(*self._t(ps))

    def qCurveTo(self, *ps):
        self._outPen.qCurveTo(*self._t(ps))

    def closePath(self):
        self._outPen.closePath()

    def endPath(self):
        self._outPen.endPath()


def sloped(t_y0):
    """The italic slant as a transformation, about the height t_y0."""
    return (1, 0, SLANT, 1, -SLANT * t_y0, 0)




# Old Standard's letters that stood out in running text, redrawn (chosen
# from previews in words, 2026-10-21): W crossed and very wide
# (1.47 cap heights, Bodoni Moda 1.28): two Vs narrowed to ITALIC_W_NARROW
# across, their strokes brought back to V's, meeting at the top (1.20);
# a's bowl as heavy as its stem, the counter small (0.407 of the x-height,
# references 0.41-0.46): its thick stroke ITALIC_A_BOWL lighter (0.429)
ITALIC_W_NARROW = 0.75
ITALIC_A_BOWL = -40
# W's thick stems take the Italic I's and H's bracket under their serifs
# (across, up the stem, the handles' shares of each): V's own, its inner
# side curling in under the serif, read as a pinch on W's steeper stems and
# the Bold Italic deepened it; the first V's thin arm runs on straight into
# the next V's thick stem, ITALIC_W_RUN_ON past where their left edges meet,
# without its own serif and flare (in the Bold Italic a bulge on the second
# stem's left; 2026-11-03: the join a plain angle)
ITALIC_W_BRACKET = (60, 58, 0.58, 0.7)
ITALIC_W_RUN_ON = 80
# and its serifs this share of V's gap apart at the least, their inner tips
# cut back (W's 102-114 in the Italic, w.sc's 51-64, the Bold Italic's
# emboldening closed them to 64-78 and to one bar: 2026-11-03)
ITALIC_W_SERIF_GAP = 0.75


def fillet_brackets(glyph, x_edges, y_at, y_under):
    """glyph's brackets from the serif underside (y_under) down onto the
    stem edges at x_edges (at height y_at) redrawn as ITALIC_W_BRACKET:
    tangent to the underside and to the straight edge below the bracket"""
    ra, rb, ka, kb = ITALIC_W_BRACKET
    for c in glyph.contours:
        P = c.points
        n = len(P)
        ons = [i for i, p in enumerate(P) if p.type]
        for idx, i in enumerate(ons):
            j = ons[(idx + 1) % len(ons)]
            if (j - i) % n != 3:
                continue
            if abs(P[i].y - y_under) < 2 and P[j].y < y_under - 20:
                top, bot, below = i, j, ons[(idx + 2) % len(ons)]
            elif abs(P[j].y - y_under) < 2 and P[i].y < y_under - 20:
                top, bot, below = j, i, ons[(idx - 1) % len(ons)]
            else:
                continue
            e, f = P[bot], P[below]  # the stem's edge, up to the bracket
            if f.y >= e.y - 30:
                continue
            if min(abs(e.x + (e.x - f.x) / (e.y - f.y) * (y_at - e.y) - x) for x in x_edges) > 40:
                continue  # not a thick stem's
            d = math.hypot(e.x - f.x, e.y - f.y)
            ux, uy = (e.x - f.x) / d, (e.y - f.y) / d  # up the edge
            cx = e.x + ux / uy * (y_under - e.y)  # the corner the bracket rounds
            side = 1 if P[top].x > cx else -1  # the way the serif runs
            a = (cx + side * ra, y_under)
            b = (cx - ux * rb, y_under - uy * rb)
            handles = ((top + 1) % n, (top + 2) % n) if (bot - top) % n == 3 else ((top - 1) % n, (top - 2) % n)
            P[top].x, P[top].y = a
            P[bot].x, P[bot].y = b
            P[handles[0]].x, P[handles[0]].y = a[0] - side * ra * ka, y_under
            P[handles[1]].x, P[handles[1]].y = b[0] + ux * rb * kb, b[1] + uy * rb * kb


def unbreak(glyph, tol=0.5):
    """on-curve nodes between two straight edges running on in one line
    dropped (the seams where W's thin arm was cut and run on)"""
    for c in glyph.contours:
        changed = True
        while changed:
            changed = False
            P = c.points
            for i, p in enumerate(P):
                a, b = P[i - 1], P[(i + 1) % len(P)]
                if p.type != "line" or not a.type or b.type != "line":
                    continue
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                if d and abs((p.x - a.x) * dy - (p.y - a.y) * dx) / d < tol and min(a.y, b.y) <= p.y <= max(a.y, b.y):
                    del P[i]
                    changed = True
                    break


def _path_slice(path, y):
    """the x where a pathops path's outline crosses height y"""
    g = ufoLib2.objects.Glyph()
    path.draw(g.getPen())
    f = ufoLib2.Font()
    f.layers.defaultLayer.insertGlyph(g, "_")
    return ink_slice(f, "_", y)


def redraw_w(font, w_name="W", v_name="V"):
    """W made of the Italic's V (weighted), narrowed, its strokes as V's,
    the thin stroke of one meeting the thick of the next at the top (their
    centres at 0.94 of V's height, the diagonals run on from 0.28 and
    0.70: 1350, 400, 1000 on the capital); V's side bearings, upright; the
    anchors moved with the ink. w.sc of v.sc likewise (FontForge's draft
    of the narrow W came out light, 0.73 of its kind). The thick stems'
    brackets and the first thin arm's join: ITALIC_W_BRACKET, _RUN_ON."""
    import derive

    up = ufoLib2.Font()
    v = copy.deepcopy(font[v_name])
    up.layers.defaultLayer.insertGlyph(v, "V")
    shear(v, -SLANT)
    h = v.getBounds(up).yMax
    lo, hi, top = 0.28 * h, 0.70 * h, 0.94 * h

    def runs(f, n, y):
        xs = ink_slice(f, n, y)
        return list(zip(xs[::2], xs[1::2]))

    def centre(f, n, i, y):
        """the centre of the first (thick) or last (thin) diagonal at y,
        run on in a line from lo and hi"""
        c0, c1 = (sum(runs(f, n, at)[i]) / 2 for at in (lo, hi))
        return c1 + (c1 - c0) / (hi - lo) * (y - hi)

    def perp(f, n):
        """the thick and thin diagonals' thickness across"""
        out = []
        for i in (0, -1):
            a, b = runs(f, n, lo)[i], runs(f, n, hi)[i]
            s = ((b[0] + b[1]) - (a[0] + a[1])) / 2 / (hi - lo)
            out.append((b[1] - b[0]) / (1 + s * s) ** 0.5)
        return out

    thick, _ = perp(up, "V")
    k = ITALIC_W_NARROW
    narrow = RecordingPen()
    v.draw(TransformPen(narrow, (k, 0, 0, 1, 0, 0)))

    def narrowed(ax):
        g = weight_thick(narrow, ax, thin=0, thick=thick * k)
        up.layers.defaultLayer.insertGlyph(g, "Vn", overwrite=True)
        return abs(perp(up, "Vn")[0] - thick)

    narrowed(min(range(0, 100, 2), key=narrowed))
    vn = up["Vn"]
    y_under = max(p.y for c in vn.contours for p in c if p.type and p.y < h - 10)  # the serifs' underside
    fillet_brackets(vn, runs(up, "Vn", 0.85 * h)[0], 0.85 * h, y_under)
    dx = centre(up, "Vn", -1, top) - centre(up, "Vn", 0, top)

    def line(i, side, y, shift=0):
        """an edge of the first (thick) or last (thin) diagonal at y, run on
        in a line from lo and hi"""
        a, b = runs(up, "Vn", lo)[i][side], runs(up, "Vn", hi)[i][side]
        return a + (b - a) / (hi - lo) * (y - lo) + shift

    # the first V's thin arm, its serif and flare cut away along the white
    # between its strokes (from the opening's middle at hi to the gap's
    # between its serifs), run on straight from lo into the next V's thick
    # stem, ITALIC_W_RUN_ON past where their left edges meet
    a0, a1 = line(-1, 0, lo), line(-1, 0, hi)
    b0, b1 = line(0, 0, lo, dx), line(0, 0, hi, dx)
    meet = lo + (b0 - a0) / ((a1 - a0) - (b1 - b0)) * (hi - lo)
    end = meet + ITALIC_W_RUN_ON
    r, s = runs(up, "Vn", hi), runs(up, "Vn", (y_under + h) / 2)
    cut = RecordingPen()
    cut.moveTo(((r[0][1] + r[-1][0]) / 2, hi))
    cut.lineTo(((s[0][1] + s[1][0]) / 2, (y_under + h) / 2))
    cut.lineTo(((s[0][1] + s[1][0]) / 2, BIG))
    cut.lineTo((BIG, BIG))
    cut.lineTo((BIG, hi))
    cut.closePath()
    arm = RecordingPen()
    arm.moveTo((line(-1, 0, lo), lo))
    arm.lineTo((line(-1, 0, end), end))
    arm.lineTo((line(-1, 1, end), end))
    arm.lineTo((line(-1, 1, lo), lo))
    arm.closePath()
    first = derive.path_op(derive.to_path(up, up["Vn"]), derive.to_path(None, rec=cut), "DIFFERENCE")
    first = derive.path_op(first, derive.to_path(None, rec=arm), "UNION")
    w = derive.path_op(first, derive.shifted(derive.to_path(up, up["Vn"]), dx), "UNION")
    # neighbouring serifs kept ITALIC_W_SERIF_GAP of V's gap apart
    y_mid = (y_under + h) / 2
    v_runs = runs(up, "V", y_mid)
    least = ITALIC_W_SERIF_GAP * (v_runs[1][0] - v_runs[0][1])
    xs = sorted(x for x in _path_slice(w, y_mid))
    tops = list(zip(xs[::2], xs[1::2]))
    for (_, r0), (l1, _) in zip(tops, tops[1:]):
        if l1 - r0 < least:
            mid = (r0 + l1) / 2
            w = derive.path_op(w, derive.rect_path(mid - least / 2, y_under, mid + least / 2, BIG), "DIFFERENCE")
    (x0, _, x1, _), vb = w.bounds, v.getBounds(up)
    lsb, rsb = vb.xMin, v.width - vb.xMax
    g = font[w_name]
    old = copy.deepcopy(g)
    shear(old, -SLANT)
    ob = old.getBounds(font)
    out = ufoLib2.objects.Glyph()
    pen = out.getPen()
    if w.clockwise != derive.to_path(up, v).clockwise:
        # wound as V is (pathops winds the other way: ₩'s bars, joined
        # to it, cut it instead)
        from fontTools.pens.reverseContourPen import ReverseContourPen

        pen = ReverseContourPen(pen)
    w.draw(TransformPen(pen, (1, 0, 0, 1, lsb - x0, 0)))
    out.width = round(lsb + (x1 - x0) + rsb)
    for a in old.anchors:  # where they stood across the ink
        t = (a.x - ob.xMin) / (ob.xMax - ob.xMin)
        out.appendAnchor({"name": a.name, "x": round(lsb + t * (x1 - x0)), "y": a.y})
    unbreak(out)
    shear(out, SLANT)
    g.clearContours()
    g.clearAnchors()
    redraw(g, out)
    for a in out.anchors:
        g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    g.width = out.width


def lighten_a(font):
    """a's bowl, left of the middle of its counter, ITALIC_A_BOWL lighter
    across (embolden by node: the stem and the hairlines as they are)."""
    up = ufoLib2.Font()
    a = copy.deepcopy(font["a"])
    up.layers.defaultLayer.insertGlyph(a, "a")
    shear(a, -SLANT)
    xs = ink_slice(up, "a", XH / 2)
    cut = (xs[1] + xs[2]) / 2  # the counter's middle
    rec = RecordingPen()
    a.draw(rec)
    out = embolden(rec, ITALIC_A_BOWL, 0, lambda x, y, inward: 1.0 if x < cut else 0.0)
    shear(out, SLANT)
    g = font["a"]
    g.clearContours()
    redraw(g, out)




def weight_thick(rec, ax, thin=80, thick=120):
    """rec with its thick upright strokes ax heavier, its hairlines and thin
    strokes as they are (embolden() with a factor per node): none below
    thin, all above thick, by the stroke's thickness measured across the
    ink. A node at the end of a long straight edge takes the thickness at
    the edge's middle, so both ends of the edge move alike (it keeps its
    slant)."""
    import numpy as np

    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())
    # the outline as straight segments, to measure across
    flat = RecordingPen()
    glyph.draw(flat)
    segs, start, cur = [], None, None
    for op, args in flat.value:
        if op == "moveTo":
            start = cur = args[0]
        elif op == "lineTo":
            segs.append((cur, args[0]))
            cur = args[0]
        elif op == "curveTo":
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = cur, *args
            prev = cur
            for k in range(1, 11):
                t = k / 10
                q = ((1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 * x3,
                     (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * y3)
                segs.append((prev, q))
                prev = q
            cur = args[-1]
        elif op in ("closePath", "endPath") and cur != start:
            segs.append((cur, start))
            cur = start
    if not segs:
        return glyph
    a = np.array([s[0] for s in segs], float)
    d = np.array([s[1] for s in segs], float) - a

    def across(px, py, ux, uy):
        """distance from (px, py) along (ux, uy) to the outline's other side"""
        den = d[:, 0] * uy - d[:, 1] * ux
        ok = np.abs(den) > 1e-9
        wx, wy = a[:, 0] - px, a[:, 1] - py
        t = np.where(ok, (d[:, 0] * wy - d[:, 1] * wx) / np.where(ok, den, 1), -1)  # along the ray
        s = np.where(ok, (ux * wy - uy * wx) / np.where(ok, den, 1), -1)  # along the segment
        hit = ok & (t > 3) & (s >= 0) & (s <= 1)
        return float(t[hit].min()) if hit.any() else 0.0

    def k_of(w):
        return min(1.0, max(0.0, (w - thin) / (thick - thin)))

    # the long straight edges: their thickness at the middle, for both ends
    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    edge_k = {}
    for contour, ar in zip(glyph.contours, areas, strict=True):
        sign = 1 if ar > 0 else -1
        if (ar > 0) != outer:
            sign = -sign
        P = contour.points
        ons = [p for p in P if p.type]
        for p0, p1 in zip(ons, ons[1:] + ons[:1], strict=True):
            if p1.type != "line" or math.dist((p0.x, p0.y), (p1.x, p1.y)) < 60:
                continue
            ux, uy = (p1.x - p0.x), (p1.y - p0.y)
            L = math.hypot(ux, uy)
            nx, ny = uy / L, -ux / L  # right-hand normal; outward is sign x it
            mx, my = (p0.x + p1.x) / 2, (p0.y + p1.y) / 2
            k = k_of(across(mx, my, -sign * nx, -sign * ny))
            for q in (p0, p1):
                edge_k.setdefault((q.x, q.y), []).append(k)

    def factor(x, y, inward):
        if (x, y) in edge_k:
            return max(edge_k[(x, y)])
        return k_of(across(x, y, *inward))

    return embolden(rec, ax, 0, factor)


def put(font, up, name, source):
    """A glyph made in the upright frame, slanted into the Italic."""
    import derive
    from glyph_lint import (
        FIXED,
        LEDGE_KEEP,
        ink,
        ledge_findings,
        step_findings,
        vector_findings,
    )

    g = copy.deepcopy(up[name])
    shear(g, SLANT, extremes=name not in POINT_REPAIRS)
    # crumbs the cuts and merges left (specks, pinholes, an outline crossing
    # itself, steps, a curve's end split off at a corner): the outline
    # merged and cleaned (glyph_lint)
    # (again if rounding the merged outline to whole units crossed it anew)
    for _ in range(3):
        if not (g.contours and not g.components):
            break
        path = ink(font, g)
        found = vector_findings(path) + step_findings(path, crumbs=True)
        if name not in LEDGE_KEEP:
            found += ledge_findings(path)
        if not any(k in FIXED for k, *_ in found):
            break
        before = copy.deepcopy(g)
        g.clearContours()
        derive.draw_path(font, before, g, derive.to_path(font, before))
    g.lib[SOURCE_KEY] = source
    font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)


# recipes placed by the Regular's coordinates (attach, curl, graft), and
# hooks on capitals (the Italic's f and ȷ are swashes, its capitals sloped
# romans): transplanted from the Regular instead
TRANSPLANT_OPS = ("attach", "curl", "graft")
LETTERS = {"₨": "Rs"}  # signs that are letters side by side
# ... closer by this much, joined: R's leg runs out into the ball of s
LETTER_JOIN = {"₨": 240}
NO_TRANSPLANT = {"ɞ", "ʝ", "ɕ", "ʂ", "ʑ", "ɚ", "ɝ", "ɮ", "Ɓ", "Ɗ", "Ƥ", "ɺ", "ɰ",
                 "Ƙ", "Ʋ", "Ƴ", "ƴ", "Ƭ", "Ɲ", "Ʈ", "ƥ", "ɖ", "ɗ", "ɭ", "Ɽ",
                 "ң", "ҷ", "қ", "җ", "Қ", "Җ", "ҳ", "ɧ", "ɱ", "ɳ", "ɽ", "ɻ", "Ƒ", "Ꞵ", "Ʝ", "ʄ", "ʋ", "ʈ", "Ɦ", "Ⱳ", "ⱳ.sc", "Ɠ", "ƈ", "ƃ", "ƛ", "ɹ", "Ƈ", "ⱳ", "ʐ", "г.loclSRB",
                 "ɽ.sc", "ʈ.sc", "ь.loclBGR", "ю.loclBGR", "ж.loclBGR", "ъ.loclBGR", "в.loclBGR"}  # its own recipe fits the Italic better
TRANSPLANT = set()  # other recipes better transplanted
# where ɗ leaves the italic d for ɓ's top: above the bowl, below where ɓ's
# stem begins to bend into its hook (upright frame)
DHOOK_CUT = 1000
# small caps left to FontForge's drafts of the Italic's capitals (as the
# others), not derive.py's recipes: a capital scaled down (ʛ from Ɠ) is
# heavier than the small caps beside it (ⱳ.sc not: drafted from the
# uncrossed Ⱳ, its narrow diagonals came out light, as w.sc's)
SC_DRAFTED = {"ɑ.sc", "ɂ.sc", "ʒ.sc", "ʊ.sc", "ʋ.sc", "ꞵ.sc", "ƭ.sc", "ƙ.sc",
              "ɲ.sc", "ʝ.sc", "ϗ.sc", "ƴ.sc", "ƈ.sc", "ɠ.sc", "ƥ.sc",
              # ƒ.sc: the Regular's hook recipe takes ȷ's tail, a swash here,
              # scaled to f.sc's stem a crescent under the letter before
              "ƒ.sc"}
# small caps the Italic makes from its own capitals where FontForge's
# draft was faulty, before derive.py's recipes (those made of them follow:
# ǥ.sc, ɢ): g.sc's counter ran straight down its left side into a corner
# (G's is round); ɦ.sc (ITALIC_RECIPES) notched where its hook met the stem
# s.sc n.sc є.sc ϟ.sc: as_capitals could not bring the draft's main stroke
# to its capital's weight (s.sc's spine 0.65 of h.sc against S's 0.99,
# n.sc's diagonal 0.63 against N's 0.84, є.sc 0.83 against Є's 1.07, ϟ.sc's
# bar 0.91; the weighting thickened their bowls and serifs, not that
# stroke): made from the capital, which has it, at the draft's side bearings
ITALIC_SC_RECIPES = [("g.sc", "enlarge", "G", ("O", "o.sc")),
                     ("s.sc", "enlarge", "S", ("O", "o.sc")),
                     ("n.sc", "enlarge", "N", ("O", "o.sc")),
                     ("є.sc", "enlarge", "Є", ("O", "o.sc")),
                     ("ϟ.sc", "enlarge", "Ϟ", ("O", "o.sc")),
                     # ѳ.sc: the draft's counters ran lumpy beside the bar
                     # (the Regular's wave bar's ends, 2026-11-09); Ѳ's are
                     # Old Standard's, round
                     ("ѳ.sc", "enlarge", "Ѳ", ("O", "o.sc"))]
# made in the late pass, after the small caps are drafted: measured
# against the Italic's own o.sc and h.sc, not the Regular's sloped
SC_LATE = {"g.sc", "ɦ.sc", "s.sc", "n.sc", "є.sc", "ϟ.sc", "ѳ.sc"}
# made from their capitals, s.sc's spine and n.sc's diagonal still stood
# light (0.81 and 0.69 of h.sc): enlarge's emboldening thickens strokes by
# their lean (a level stroke by the hairlines' amount), so their thick
# strokes are made heavier (level_gain) until the main stroke stands to
# h.sc's as the capital's to H's: s.sc's up and down (its spine near
# level), n.sc's sideways (its diagonal steep; up and down its top serif
# grew heavy and its vertex dropped)
SC_LEVEL_GAIN = {"s.sc": ("S", True), "n.sc": ("N", False)}
# of those, drafted all the same and remade at the draft's side bearings
# (its spacing and kerning kept), its anchors moved with its ink
SC_DRAFT_SIDES = {"s.sc", "n.sc", "uni0454.sc", "uni03DF.sc", "uni0473.sc"}
# the Italic's own letters already have the shape: Old Standard's g is ɡ,
# its h turned is ɥ (the Regular's is u and a descender, its h's serifs
# would turn)
def retroflex(x0, x1, y, w, r, ball, th, turn=0):
    """attach pieces: a stem w thick from (x0, y) down to (x1, -150), curling
    to the right there through 170 degrees on radii r, ending in a ball."""
    return [("line", ((x0, y), (x1, -150), w), (0, 0), (1, 1, 0, 0)),
            ("curl", {"at": ("pt", x1, -150, w), "dir": 270 + turn, "turn": "ccw", "r": r,
                      "sweep": 170, "ball": ball, "t": (w, th)}, (0, 0), (1, 1, 0, 0))]


def descender(x0, y0, x1, y1, w, d, r, th):
    """attach pieces: a stroke w thick from (x0, y0) to (x1, y1) (running on
    a little into the curl), curling to the left there through 170
    degrees on radii r, the ball as heavy as the stroke."""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    return [("line", ((x0, y0), (x1 + dx / n * 12, y1 + dy / n * 12), w), (0, 0), (1, 1, 0, 0)),
            ("curl", {"at": ("pt", x1, y1, w), "dir": d, "turn": "cw", "r": r, "sweep": 170,
                      "ball": max(36, round(w * 0.48)), "t": (w, th)}, (0, 0), (1, 1, 0, 0))]


# where a recipe's straight piece meets an italic stroke that leans or
# curves (ɰ ɱ ɳ: a leg running on into a descender; ⱳ: the arm into its
# curl), the join faired between these heights (derive.fair_joins): the
# piece is straight in the upright frame, the stroke is not, and the edges
# broke there by 5-20 degrees (seen in print)
ITALIC_JOINS = {"ɰ": (250, 350), "ɧ": (200, 300), "ɱ": (190, 460), "ɳ": (190, 460), "ⱳ": (590, 700)}
# corners rounded off where a descender's straight edge meets the curve of
# the letter it hangs from (round_corner: at that height, a curve tangent to
# both reaching that far either way): җ's descender leans 14 degrees, the
# back of ж's right c it meets rises at 2, a kink with a swelling above it
# (2026-11-08). Not fair_joins: one curve from the descender's
# foot to the c would bend the whole edge (as it thinned ⱳ's arm).
ITALIC_CORNERS = {"җ": (200, 120)}


# an edge run straight between two heights: from the rightmost on-curve
# point at the first (within 6 units) going down, to the second on the
# line below, one curve tangent at both ends (straighten_run). җ's inner
# edge left the crossbar leaning as the descender does, dropped upright down
# the c's lower inside, then leaned again: a kink at the cut in the Italic,
# a swelling above it in the Bold Italic (2026-11-08)
ITALIC_RUNS = {"җ": (417, 50)}


def straighten_run(glyph, y_from, y_to):
    """glyph (in place): see ITALIC_RUNS. Returns whether it changed."""
    import math

    from ufoLib2.objects import Point

    for contour in glyph.contours:
        pts = contour.points
        n = len(pts)
        cand = [i for i, p in enumerate(pts) if p.type and abs(p.y - y_from) <= 6
                and pts[(i + 1) % n].y < p.y - 5]
        if not cand:
            continue
        i = max(cand, key=lambda k: pts[k].x)
        P = (pts[i].x, pts[i].y)
        first = (pts[(i + 1) % n].x, pts[(i + 1) % n].y)
        # down the edge to the line segment that crosses y_to
        j = (i + 1) % n
        while True:
            p = pts[j]
            prev = pts[j - 1]
            if p.type == "line" and prev.type and min(p.y, prev.y) <= y_to <= max(p.y, prev.y):
                break
            j = (j + 1) % n
            if j == i:
                return False
        a, b = pts[j - 1], pts[j]
        t = (y_to - a.y) / (b.y - a.y)
        A = (a.x + (b.x - a.x) * t, y_to)
        u = (first[0] - P[0], first[1] - P[1])
        m = math.hypot(*u) or 1
        u = (u[0] / m, u[1] / m)
        v = (a.x - b.x, a.y - b.y)
        m = math.hypot(*v) or 1
        v = (v[0] / m, v[1] / m)
        k = math.dist(P, A) / 3
        new = [Point(P[0] + u[0] * k, P[1] + u[1] * k), Point(A[0] + v[0] * k, A[1] + v[1] * k),
               Point(*A, "curve", smooth=True), Point(b.x, b.y, "line")]
        if j > i:
            pts[i + 1:j + 1] = new
        else:
            del pts[i + 1:]
            del pts[:j + 1]
            pts.extend(new)
        return True
    return False


def round_corner(glyph, y, reach, turns=(3, 30)):
    """glyph (in place): each join of two segments at height y (within 15
    units; a segment shorter than 20 there taken in) whose directions
    differ by turns degrees, rounded off by a curve from reach back along
    the one to reach along the other (curves split there), tangent to both.
    Returns how many were rounded."""
    import math

    from fontTools.misc.bezierTools import splitCubicAtT
    from ufoLib2.objects import Point

    def segments(contour):
        pts = contour.points
        start = next(i for i, p in enumerate(pts) if p.type)
        order = pts[start + 1:] + pts[:start + 1]
        segs, cur, hs = [], (pts[start].x, pts[start].y), []
        for p in order:
            if p.type is None:
                hs.append((p.x, p.y))
                continue
            end = (p.x, p.y)
            segs.append([cur, *hs, end] if hs else [cur, end])
            cur, hs = end, []
        return segs

    def length(seg):
        return math.dist(seg[0], seg[-1])

    def split(seg, t):
        if len(seg) == 2:
            m = (seg[0][0] + (seg[1][0] - seg[0][0]) * t, seg[0][1] + (seg[1][1] - seg[0][1]) * t)
            return [seg[0], m], [m, seg[1]]
        a, b = splitCubicAtT(*seg, t)
        return list(a), list(b)

    def unit(p, q):
        d = math.dist(p, q) or 1
        return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)

    done = 0
    for contour in glyph.contours:
        segs = segments(contour)
        changed = True
        while changed:
            changed = False
            n = len(segs)
            for k in range(n):
                s0, s1 = segs[k], segs[(k + 1) % n]
                if abs(s0[-1][1] - y) > 15:
                    continue
                # a short segment at the join: taken into the one before it
                if length(s1) < 20 and n > 3:
                    s0 = [s0[0], *s0[1:-1], s1[-1]] if len(s0) == 2 else [*s0[:-1], s1[-1]]
                    s1 = segs[(k + 2) % n]
                    skip = 2
                else:
                    skip = 1
                din = unit(s0[-2], s0[-1])
                dout = unit(s1[0], s1[1])
                ang = abs(math.degrees(math.atan2(din[0] * dout[1] - din[1] * dout[0], din[0] * dout[0] + din[1] * dout[1])))
                if not turns[0] <= ang <= turns[1] or length(s0) < 2 * reach or length(s1) < 2 * reach:
                    continue
                keep0, _ = split(s0, 1 - reach / length(s0))
                _, keep1 = split(s1, reach / length(s1))
                A, B, C = keep0[-1], keep1[0], s0[-1]
                u, v = unit(keep0[-2], A), unit(B, keep1[1])
                ka, kb = 0.55 * math.dist(A, C), 0.55 * math.dist(C, B)
                blend = [A, (A[0] + u[0] * ka, A[1] + u[1] * ka), (B[0] - v[0] * kb, B[1] - v[1] * kb), B]
                idx = [(k + j) % n for j in range(skip + 1)]
                new = [keep0, blend, keep1]
                rest = [segs[i] for i in range(n) if i not in idx]
                pos = min(idx) if max(idx) - min(idx) == skip else 0
                if pos == 0 and max(idx) - min(idx) != skip:  # the join wraps the start
                    rest = [segs[i] for i in range(n) if i not in idx]
                    segs = new + rest
                else:
                    segs = segs[:pos] + new + segs[pos + skip + 1:]
                done += 1
                changed = True
                break
        pts = []
        for seg in segs:
            for h in seg[1:-1]:
                pts.append(Point(*h))
            pts.append(Point(*seg[-1], "curve" if len(seg) == 4 else "line"))
        for p in pts:
            if p.type and abs(p.y - y) <= reach + 5:
                p.smooth = True
        contour.points[:] = pts
    return done


# the curls over the top end in a ball as the case draws them ("ball":
# None, derive.ball_for, 2026-10-27; the Bold Italic draws its own at its
# weight, make_bold.ITALIC_BOLD_RECIPES); tails off a stem (retroflex,
# descender) keep a ball half their stroke, flush with the curl's end;
# Ⱳ keeps its number (its ball 50, the curl run on straight from W's arm)
# ɮ: how far right of l's stem its ʒ stands (ITALIC_RECIPES)
ZH_DX = 150
# the roman's own, sloped, not remade on the italic letter: ʌ turned from the
# italic v rounds its apex and reads as a (2026-11-01)
# Old Standard has it, but derive.py's recipe matches the IPA small capitals
# around it (Old Standard's ʀ stood lower and lighter)
# ɑ is the italic's one-storey a (Old Standard's ɑ is its α), ɒ that turned
OWN_RECIPE = {"ʀ", "ɑ"}
KEPT_SLOPED = {"ʌ", "ɐ", "ᵃ", "a.ipa"}
ITALIC_RECIPES = {"л.loclBGR": ("turn", "v", "x"),  # the rounded form ʌ had
                  # ɴ: n.sc's ink fitted from its vertex, 25 below the line
                  # (21 at ɴ's size), so its feet stand on it (from 0 they
                  # stood 23 above, 2026-11-05)
                  "ɴ": ("enlarge", "n.sc", ("o.sc", "o", -21, 884, "i.sc", "n")),
                  # ȼ.sc: c.sc at its capital's weight (as_capitals) is about
                  # 40 wider; at 0.8 of its box the slash's top met the
                  # terminal in a notch, at 0.78 it stands where it stood
                  "ȼ.sc": ("slash", "c.sc", ("s", "box", 0.25, -90, 0.78, 1130)),
                  "ɡ": ("alias", "g", None), "ɥ": ("turn", "h", "x"),
                  "ɑ": ("alias", "a", None),
                  # ₩: the bars from 20 to 20 past the uncrossed W's
                  # advance (redraw_w), as the Regular's across its W
                  "₩": ("lines", "W", ("c", 64, [(20, 528, 1807, 592), (20, 842, 1807, 906)])),
                  # ⱳ.sc: w.sc (made of v.sc as W of V) with Ⱳ's curl at
                  # the small caps' 0.725, the cut between the middle serif
                  # and the right one (all of it); enlarged from that Ⱳ, its
                  # narrow diagonals thinned by the stem's amount (0.84 of
                  # its kind)
                  "ⱳ.sc": ("curl", "w.sc", ("c", [(940, 834, BIG, BIG)],
                                         {"at": ("y", 834, "last"), "dir": 79, "turn": "cw", "r": (87, 80),
                                          "sweep": 210, "ball": None, "t": (59, 30)})),
                  # ǥ: the single-storey g's bar across its stem below the
                  # baseline, above the hook, as in DejaVu (the roman's
                  # height crossed the tail, easy to miss)
                  "ǥ": ("bar", "g", ("x", -130, "all", (200, 70))),
                  # ɉ: the bar centred on the stem, its length as before
                  # (derive's bar stops at the ink, j's stem on the right:
                  # 169 left, 14 right; "not centred", 2026-11-05)
                  "ɉ": ("bar", "j", ("x", None, "all", (92, 92))),
                  # ₸'s line across the T's top bar, ₫'s under the bowl and
                  # stem (the Regular's numbers run past the narrower italics)
                  "₸": ("lines", "T", ("c", 64, [(118, 1498, 1205, 1562)])),
                  "₫": ("lines", "dcroat", ("x", 64, [(120, -330, 940, -266)])),
                  # f's hook brought down onto the x-height, on a foot serif
                  # (fishhook; as the Regular's, 2026-11-04)
                  "ɾ": ("fishhook", "f", ("r", (213, 0, 493, 50))),
                  # ɦ.sc: Ɦ made small, H's stems brought to h.sc's (by o.sc's
                  # round alone they came out 152 against h.sc's 194)
                  "ɦ.sc": ("enlarge", "uniA7AA", ("O", "o.sc", "H", "h.sc")),
                  "ɸ": ("stem", "o", None),  # o with a stem as heavy as l's through it
                  "ɯ": ("turn", "m", "x"),  # the turned m it is named after
                  # ɯ with its last stem running down into ɥ's descender
                  "ɰ": ("attach", "uni026F", ("x", [(1150, -BIG, BIG, 300), (1300, -BIG, BIG, 600)],
                                              [("uni0265", (700, -BIG, BIG, 300), (0, 0), (1, 1, 459, 0))], 1500)),
                  # the italic r turned (as Charis's), not the roman's drawn ɹ:
                  # its stem as light as the other italic stems
                  "ɹ": ("turn", "r", "x"),
                  # ɹ's stem to ascender height, l's top on it
                  "ɺ": ("attach", "uni0279", ("x", [(-BIG, 850, BIG, BIG)],
                                              [("l", (-BIG, 850, BIG, BIG), (0, 0), (1, 1, 268, 0))])),
                  # the clicks are letters: a sloped bar (the Italic's | is upright)
                  "ǀ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)], [])),
                  "ǁ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)],
                                                [("_clickbar", (-BIG, 0, BIG, BIG), (0, 0), (1, 1, 230, 0))])),
                  "ǂ": ("attach", "_clickbar", ("x", [(-BIG, -BIG, BIG, 0)],
                                                [("rect", (56, 560, 456, 612), (0, 0), (1, 1, 0, 0)),
                                                 ("rect", (56, 820, 456, 872), (0, 0), (1, 1, 0, 0))], 512)),
                  # the rhotic hook rising from the bowl's right side (at that height)
                  "ɚ": ("rhotic", "ə", 500), "ɝ": ("rhotic", "ɜ", 690),
                  # the italic ? (its stroke curls at the foot) turning down
                  # into a stem: ʕ ʡ ʢ follow
                  "ʔ": ("glottal", "question", None),
                  # ɜ closed on the left by the left half of o
                  "ɞ": ("attach", "ɜ", ("x", [(-BIG, 600, 400, BIG), (-BIG, -BIG, 400, 300)],
                                        [("o", (-BIG, -BIG, 440, BIG), (0, 0), (1, 1, -20, 0))])),
                  # c's bottom stroke runs on into a loop, an upright tail
                  # through it; s's turns down at the left and hooks right
                  "ɕ": ("attach", "c", ("x", [(560, -BIG, BIG, 400)],
                                        [("curl", {"at": ("pt", 550, 12, 50), "dir": 10, "turn": "ccw",
                                                   "r": (100, 130), "sweep": 270, "ball": 36, "t": (90, 50)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((433, 150), (433, -200), 90), (0, 0), (1, 1, 0, 0))])),
                  # z's bottom stroke runs on (its rising end cut away), thinning
                  # into a small loop at its end, an upright tail down through
                  # the loop's left side (as the Regular's)
                  "ʑ": ("attach", "z", ("x", [(600, -BIG, BIG, 400)],
                                        [("poly", [(560, -23), (600, -21), ((630, -18), (660, -14), (690, -12)),
                                                   (690, 52), ((660, 62), (630, 84), (600, 106)), (560, 106)],
                                          (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 680, 20, 50), "dir": 3, "turn": "ccw",
                                                   "r": (95, 115), "sweep": 270, "ball": 30, "t": (90, 50), "lead": 10},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((578, 140), (578, -200), 92), (0, 0), (1, 1, 0, 0))])),
                  # z's bottom stroke, where it turns up, turns down instead into a
                  # stem that hooks to the right (as the Regular's and Charis's ʐ),
                  # the stem 110 as tuned (0.85 of the weighted n), run up
                  # into the stroke so the inner corner is the two edges meeting
                  "ʐ": ("attach", "z", ("x", [(600, -BIG, BIG, 400)],
                                        [("curl", {"at": ("pt", 600, 35, 117), "dir": 0, "turn": "cw",
                                                   "r": (90, 90), "sweep": 90, "ball": 30, "t": (110, 117)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((690, -20), (690, -330), 110), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 690, -330, 110), "dir": 270, "turn": "ccw",
                                                   "r": (135, 95), "sweep": 150, "ball": 60, "t": (110, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # s's bottom stroke runs on to the left and hooks down and round
                  "ʂ": ("attach", "s", ("x", [(-BIG, -BIG, 405, 360)],
                                        [("curl", {"at": ("pt", 405, 1.5, 36), "dir": 172, "turn": "ccw",
                                                   "r": (120, 150), "sweep": 188, "ball": 40, "t": (80, 36),
                                                   "lead": 10, "cuts": [(405, -80, BIG, BIG)]}, (0, 0), (1, 1, 0, 0))])),
                  # the stroke across the tail higher, where the tail is
                  "ʝ": ("attach", "j", ("x", [], [("line", ((-20, -400), (580, -110), 50), (0, 0), (1, 1, 0, 0))])),
                  # l on a straight stem to the baseline, Old Standard's ʒ beside
                  # it (as the Regular's): its entry stroke cut, its top bar
                  # run on to the stem, its diagonal and bowl clear of it
                  "ɮ": ("attach", "l", ("x", [(-BIG, -BIG, BIG, 250), (300, -BIG, BIG, 600)],  # l's exit stroke too
                                        [("rect", (163, 0, 304, 260), (0, 0), (1, 1, 0, 0)),
                                         ("uni0292", (250, 0, BIG, BIG), (0, 0), (1, 1, ZH_DX, 0)),
                                         ("uni0292", (-BIG, -BIG, BIG, 0), (0, 0), (1, 1, ZH_DX, 0)),
                                         ("rect", (280, 720, 250 + ZH_DX + 20, 880), (0, 0), (1, 1, 0, 0)),
                                         # filling the notch where ʒ's diagonal meets its bowl
                                         ("line", ((393 + ZH_DX, 307), (452 + ZH_DX, 300), 14), (0, 0), (1, 1, 0, 0)),
                                         ("line", ((390 + ZH_DX, 300), (430 + ZH_DX, 300), 10), (0, 0), (1, 1, 0, 0))],
                                        950 + ZH_DX)),
                  # the stem rising through the top serif and curling over to the left
                  **{ch: ("curl", base, ("c", [(-BIG, 1300, 300, BIG)],
                                         {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                          "sweep": 200, "ball": None, "t": (166, 60)}))
                     for ch, base in (("Ɓ", "B"), ("Ɗ", "D"), ("Ƥ", "P"))},
                  # the arm or stem itself curling over at the top (its serif
                  # cut away), at its own weight
                  # Ƙ Ƴ Ʋ: curls 1.25 times what they were, as large as Ƈ Ɠ's
                  # (their balls growing with them; 2026-11-08)
                  "Ƙ": ("curl", "K", ("c", [(850, 1250, BIG, BIG)],
                                      {"at": ("y", 1250, "last"), "dir": 51, "turn": "cw", "r": (140, 120),
                                       "sweep": 210, "ball": None, "t": (89, 45)})),
                  "Ʋ": ("curl", "U", ("c", [(930, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 90, "turn": "ccw", "r": (175, 150),
                                       "sweep": 200, "ball": None, "t": (64, 40)})),
                  "Ƴ": ("curl", "Y", ("c", [(780, 1200, BIG, BIG)],
                                      {"at": ("y", 1200, "last"), "dir": 62, "turn": "cw", "r": (140, 120),
                                       "sweep": 210, "ball": None, "t": (68, 40)})),
                  "ƴ": ("curl", "y", ("x", [(700, 760, BIG, BIG)],
                                      {"at": ("y", 760, "last"), "dir": 90, "turn": "cw", "r": (100, 90),
                                       "sweep": 200, "ball": None, "t": (116, 40)})),
                  # p's stem (its entry stroke cut away) rising and curling over
                  "ƥ": ("attach", "p", ("x", [(-BIG, 700, 400, BIG), (-BIG, 400, 270, BIG)],
                                        [("rect", (296, 650, 397, 1150), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 346.5, 1150, 101), "dir": 90, "turn": "cw",
                                                   "r": (150, 130), "sweep": 210, "ball": None, "t": (101, 45)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # the bar's left end (its serif cut away) curling down; the curl
                  # leaves the bar where it is as thin as the curl (it flares
                  # toward the serif), so they meet without a ledge
                  # (its ball less than the case's 86: that nearly filled the
                  # curl, its small cap's draft closed to a slit)
                  # the bar run on 220 units left at the curl's weight first: it
                  # stood 197 against the right arm's 648 (the T's own 377;
                  # 2026-11-06: short against the other styles'; at 0.8
                  # of it, as the Regular's 0.85, too long), now about 0.65
                  "Ƭ": ("attach", "T", ("c", [(-BIG, 800, 420, BIG)],
                                        [("line", ((440, 1398), (200, 1398), 62), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 200, 1398, 62), "dir": 180, "turn": "ccw",
                                                   "r": (135, 125), "sweep": 200, "ball": 65, "t": (90, 62),
                                                   "lead": 10, "cuts": [(200, 1300, BIG, BIG)]}, (0, 0), (1, 1, 0, 0))])),
                  # the top hairline rising from where its ball was into a hook
                  # to the right (as Charis and Libertinus)
                  "ƈ": ("attach", "c", ("x", [(540, 450, BIG, BIG), (470, 450, 545, 800)],
                                        [("line", ((515, 858), (560, 1100), 44), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 560, 1100, 44), "dir": 75, "turn": "cw",
                                                   "r": (110, 100), "sweep": 200, "ball": None, "t": (44, 34),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # b's stem without its flag serif, the bar its top run on to
                  # the right
                  "ƃ": ("attach", "b", ("x", [(-BIG, 1300, 173, BIG)],
                                        [("rect", (173, 1379, 720, 1435), (0, 0), (1, 1, 0, 0))])),
                  # λ whole, a bar drawn across its upper stroke (the Regular's,
                  # transplanted, cut the arch off the long stroke)
                  "ƛ": ("attach", "lambda", ("x", [], [("line", ((130, 1010), (610, 1285), 46), (0, 0), (1, 1, 0, 0))])),
                  # C's spur likewise (as Ɠ)
                  "Ƈ": ("attach", "C", ("c", [(1040, 1330, BIG, BIG)],
                                        [("line", ((1090, 1320), (1090, 1500), 36), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1090, 1500, 36), "dir": 90, "turn": "cw",
                                                   "r": (105, 95), "sweep": 210, "ball": None, "t": (36, 30),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # G's spur rising above the cap height into a hook to the right
                  # (as Charis and Libertinus), not curling back over the bowl
                  "Ɠ": ("attach", "G", ("c", [(1080, 1330, BIG, BIG)],
                                        [("line", ((1139, 1320), (1139, 1500), 36), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1139, 1500, 36), "dir": 90, "turn": "cw",
                                                   "r": (105, 95), "sweep": 210, "ball": None, "t": (36, 30),
                                                   "lead": 10}, (0, 0), (1, 1, 0, 0))])),
                  # the stem (its foot serif cut away) running down into the hook
                  "Ɲ":("attach", "N", ("c", [(-BIG, -BIG, 700, 250)],
                                        [("line", ((363, 300), (363, -200), 63), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 363, -200, 63), "dir": 270, "turn": "cw",
                                                   "r": (100, 90), "sweep": 160, "ball": 45, "t": (63, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # (the ball half the stem, flush with the curl's end, as Ɽ's)
                  "Ʈ": ("attach", "T", ("c", [(-BIG, -BIG, BIG, 150)],
                                        retroflex(667.5, 667.5, 200, 165, (150, 125), 82, 50))),
                  # the stem (below its swell, without the exit stroke) going on
                  # below the baseline and curling right, as ɭ ɽ ʈ (the bowl kept
                  # joined)
                  "ɖ": ("attach", "d", ("x", [(700, -BIG, BIG, 200), (820, -BIG, BIG, 450)],
                                        retroflex(733, 733, 210, 114, (110, 100), 57, 40))),
                  "ɭ": ("attach", "l", ("x", [(-BIG, -BIG, BIG, 300), (300, -BIG, BIG, 600)],
                                        retroflex(234, 234, 350, 116, (110, 100), 45, 40))),
                  # the tail on the stem (its foot serif cut away), as ɽ's
                  "Ɽ": ("attach", "R", ("c", [(-BIG, -BIG, 800, 120)],
                                        retroflex(393, 393, 160, 166, (150, 125), 82, 50))),
                  "ɳ": ("attach", "n", ("x", [(700, -BIG, BIG, 200), (900, -BIG, BIG, 450)],
                                        retroflex(795, 795, 210, 112, (110, 100), 56, 40))),
                  "ɽ": ("attach", "r", ("x", [], retroflex(354.5, 354.5, 100, 119, (110, 100), 55, 40))),
                  # ɽ.sc ʈ.sc: the tail on the stem (its foot serif cut away),
                  # as Ɽ's and Ʈ's at the small caps' size: the hook recipe
                  # took the Italic's ȷ, a swash, and ran it out along the baseline
                  "ɽ.sc": ("attach", "r.sc", ("s", [(-BIG, -BIG, 690, 110)],
                                              retroflex(309.5, 309.5, 150, 174, (125, 105), 87, 45))),
                  "ʈ.sc": ("attach", "t.sc", ("s", [(-BIG, -BIG, BIG, 110)],
                                              retroflex(521.5, 521.5, 150, 174, (125, 105), 87, 45))),
                  "ɻ": ("attach", "uni0279", ("x", [(440, -BIG, BIG, 200), (560, 200, BIG, 400)],
                                              retroflex(502, 502, 250, 110, (120, 105), 55, 40))),
                  # the last stem or leg running on below the baseline (the
                  # exit stroke cut away) and curling to the left
                  "ң": ("attach", "uni043D", ("x", [(700, -BIG, BIG, 250), (950, -BIG, BIG, 450)],
                                              descender(802.5, 300, 802.5, -150, 119, 270, (105, 95), 40))),
                  "ҷ": ("attach", "uni0447", ("x", [(680, -BIG, BIG, 250), (950, -BIG, BIG, 450)],
                                              descender(761.5, 300, 761.5, -150, 117, 270, (105, 95), 40))),
                  "қ": ("attach", "uni043A", ("x", [(640, -BIG, BIG, 200), (900, -BIG, BIG, 450)],
                                              descender(730, 250, 735, -150, 125, 270, (105, 95), 40))),
                  # (ж 41 left of Old Standard's: mirror_zhe)
                  "җ": ("attach", "uni0436", ("x", [(959, -BIG, BIG, 200), (1309, -BIG, BIG, 450)],
                                              descender(1047, 210, 1059, -150, 112, 272, (100, 90), 40))),
                  # the capitals as the lowercase: the leg's exit stroke cut
                  # away, a descender in its place (not Ц's tail under it)
                  "Қ": ("attach", "uni041A", ("c", [(895, -BIG, BIG, 200), (1215, -BIG, BIG, 450)],
                                              descender(1001, 250, 1008, -150, 165, 270, (130, 115), 45))),
                  "Җ": ("attach", "uni0416", ("c", [(1480, -BIG, BIG, 200), (1820, -BIG, BIG, 450)],
                                              descender(1596, 250, 1603, -150, 182, 270, (130, 115), 45))),
                  "ҳ": ("attach", "uni0445", ("x", [(560, -BIG, BIG, 150), (900, -BIG, BIG, 350)],
                                              descender(612, 155, 810, -150, 58, 303, (90, 80), 34))),
                  # ȷ's descender on the last stem, as ɲ has it on the first: it
                  # thins as the italic stems do (cut in where the stem is as
                  # wide as ɲ's, below its swell; the exit stroke cleared)
                  # ɧ: ȷ's descender (its stem 144, centred at 405) on ɦ's leg
                  # where it is still whole (152 at 250, centred at 661), the
                  # exit stroke cut away: cut lower, where the leg thins into
                  # its exit, the hook was scaled to that and the leg pinched
                  "ɧ": ("attach", "uni0266", ("x", [(450, -BIG, BIG, 250), (800, -BIG, BIG, 450)],
                                              [("uni0237", (-BIG, -BIG, BIG, 260), (405, 250),
                                                (152 / 144, 1, 661, 250))])),
                  "ɱ": ("hook", "m", ("x", "down-left", "last", 200, 160, 400, [(1360, -BIG, BIG, 450)])),
                  # F's stem (its foot serif cut away) tapering into the hook
                  "Ƒ": ("attach", "F", ("c", [(-BIG, -BIG, BIG, 150)],
                                        [("poly", [(310, 150), (477, 150), (477, -150), (357, -150)], (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 417, -150, 120), "dir": 270, "turn": "cw",
                                                   "r": (130, 110), "sweep": 170, "ball": 58, "t": (120, 45)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # B's stem running on down (its foot serif cut away) to a serif of its own
                  "Ꞵ": ("attach", "B", ("c", [(-BIG, -BIG, 309, 110)],
                                        [("rect", (310, -480, 476, 40), (0, 0), (1, 1, 0, 0)),
                                         ("rect", (170, -480, 616, -428), (0, 0), (1, 1, 0, 0))])),
                  # J's stem straight down into a tail curling left, crossed
                  "Ʝ": ("attach", "J", ("c", [(-BIG, -BIG, BIG, 400), (-BIG, -BIG, 500, 600)],
                                        [("line", ((713, 450), (713, -262), 164), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 713, -250, 164), "dir": 270, "turn": "cw",
                                                   "r": (150, 130), "sweep": 170, "ball": 78, "t": (164, 50)},
                                          (0, 0), (1, 1, 0, 0)),
                                         ("line", ((380, -330), (980, -80), 50), (0, 0), (1, 1, 0, 0))])),
                  # ɟ's stem (its entry stroke cut away) rising and curling over like f's
                  # (its bar centred on the stem)
                  "ʄ": ("attach", "uni025F", ("x", [(-BIG, 600, BIG, BIG), (-BIG, 475, 330, BIG),
                                                    (-BIG, 410, 345, 474), (500, 410, BIG, 474)],
                                              [("rect", (351, 550, 495, 1150), (0, 0), (1, 1, 0, 0)),
                                               ("rect", (173, 414, 673, 470), (0, 0), (1, 1, 0, 0)),
                                               ("curl", {"at": ("pt", 423, 1150, 122), "dir": 90, "turn": "cw",
                                                         "r": (150, 130), "sweep": 210, "ball": None, "t": (122, 45)},
                                                (0, 0), (1, 1, 0, 0))], 760)),
                  # u's last stem curling over to the left at the top
                  "ʋ": ("curl", "u", ("x", [(700, 700, BIG, BIG)],
                                      {"at": ("y", 700, "last"), "dir": 90, "turn": "ccw", "r": (120, 110),
                                       "sweep": 200, "ball": None, "t": (120, 42)})),
                  "ʈ": ("attach", "t", ("x", [(-BIG, -BIG, BIG, 300), (300, -BIG, BIG, 600)],
                                        retroflex(232, 232, 350, 116, (110, 100), 45, 40))),
                  # the left stem curling over to the left, as on Ɓ; W's right arm to the right
                  "Ɦ": ("curl", "H", ("c", [(-BIG, 1300, 700, BIG)],
                                      {"at": ("y", 1300, "first"), "dir": 90, "turn": "ccw", "r": (200, 150),
                                       "sweep": 200, "ball": None, "t": (164, 60)})),
                  # w's hairline arm (its ball cut away) rising straight to the
                  # x-height and curling over (the Regular's curl, carried
                  # across, left slivers beside the diagonal)
                  "ⱳ": ("attach", "w", ("x", [(1000, 645, BIG, BIG)],
                                        [("line", ((1289, 620), (1287, 770), 54), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1287, 770, 54), "dir": 92, "turn": "cw",
                                                   "r": (105, 95), "sweep": 200, "ball": None, "t": (54, 36),
                                                   "lead": 6}, (0, 0), (1, 1, 0, 0))])),
                  # W's last arm cut below its flare into the serif
                  # (redraw_w) and run on straight (its centre 1386.5 at
                  # 900, 1414.5 at 1000; 77 across) to 1150, where the
                  # curl leaves it at its own slant: cut at 1150, the
                  # flare's upright bend stayed under the curl, a bump on
                  # its outer edge (2026-11-03)
                  "Ⱳ": ("attach", "W", ("c", [(1255, 990, BIG, BIG)],
                                        [("line", ((1386.5, 900), (1459.9, 1162), 77), (0, 0), (1, 1, 0, 0)),
                                         ("curl", {"at": ("pt", 1456.5, 1150, 77), "dir": 74.4, "turn": "cw",
                                                   "r": (120, 110), "sweep": 210, "ball": 50, "t": (77, 40)},
                                          (0, 0), (1, 1, 0, 0))])),
                  # v on a stem under its round bottom
                  "ү": ("descend", "v", ("x", "p")),
                  # Serbian and Macedonian italic (locl SRB, MKD; the
                  # Regular's are its plain letters, ITALIC_LOCL): б leaning
                  # back is Old Standard's д, ∂; д is g; ѓ is ī with the
                  # acute over its bar, as Charis and Libertinus stack them
                  # (serbian_gje: the acute added once the letters are
                  # spaced; 2026-11-08)
                  "б.loclSRB": ("alias", "uni0434", None),
                  "д.loclSRB": ("alias", "g", None),
                  "ѓ.loclSRB": ("alias", "imacron", None),
                  # Bulgarian: the italic's own и п т ц ш щ have the shapes
                  # the upright takes from Latin (u n m)
                  "и.loclBGR": ("alias", "uni0438", None),
                  "п.loclBGR": ("alias", "uni043F", None),
                  "т.loclBGR": ("alias", "uni0442", None),
                  "ц.loclBGR": ("alias", "uni0446", None),
                  "ш.loclBGR": ("alias", "uni0448", None),
                  "щ.loclBGR": ("alias", "uni0449", None),
                  "г.loclBGR": ("alias", "uni0433", None),  # the cursive г is ƨ already
                  # ascenders: ь's entry curl and stem top cut where its stem
                  # is as wide as b's (600), b's stem and flag on it (b's
                  # bowl clipped); ю's first and ж's middle stem take l's,
                  # as light as theirs
                  "ь.loclBGR": ("attach", "uni044C", ("x", [(-BIG, 600, BIG, BIG), (-BIG, 520, 200, BIG)],
                                                       [("b", (-BIG, 595, 320, BIG), (0, 0), (1, 1, 107, 0))])),
                  "ю.loclBGR": ("attach", "uni044E", ("x", [(-BIG, 650, 470, BIG), (-BIG, 540, 230, BIG)],
                                                       [("l", (-BIG, 645, BIG, BIG), (0, 0), (1, 1, 122, 0))])),
                  # ж: l's ascender on the stem (ж's own left half is the
                  # right c mirrored, 41 left of Old Standard's: mirror_zhe;
                  # 2026-11-08)
                  "ж.loclBGR": ("attach", "uni0436", ("x", [(639, 800, 939, BIG)],
                                                       [("l", (-BIG, 790, BIG, BIG), (0, 0), (1, 1, 553, 0))])),
                  # в: b with β's loop above, as in the Regular: the loop (its
                  # left side lighter than b's stem) over the stem's top, the
                  # stem cut where the loop's curve rounds it off; the ball on
                  # the stem; β's waist (780) on b's bowl top (860), 0.837 as tall;
                  # below the waist only the ball (not the stroke into β's lower
                  # bowl): one piece, β above 735 less its stem below 1290 and
                  # that stroke (in pieces, the seams kinked the loop); the
                  # notch between stem, ball and b's arch filled; the
                  # counter's floor carried level from the top of the ball
                  # (931) into the loop's right side, where β's waist left a
                  # dip (883 at 508)
                  "в.loclBGR": ("attach", "b", ("x", [(-BIG, 1355, BIG, BIG), (-BIG, 1300, 203, BIG)],
                                                [("beta", ((-BIG, 735, BIG, BIG), (-BIG, 735, 414, 1290),
                                                           (674, 735, BIG, 790)),
                                                  (0, 780), (1, 0.837, -154, 860)),
                                                 ("poly", [(300, 690), (300, 835), (360, 835), (430, 820), (395, 800),
                                                           (375, 780), (360, 760), (345, 740), (335, 720), (325, 700)],
                                                  (0, 0), (1, 1, 0, 0)),
                                                 ("poly", [(354, 915), (354, 931), ((430, 931), (554, 942), (564, 991)),
                                                           (580, 960), (510, 872)],
                                                  (0, 0), (1, 1, 0, 0))])),
                  # ъ (its stem a cursive diagonal): the ь above with ъ's
                  # wave arm raised to the ascender, left of the stem
                  "ъ.loclBGR": ("attach", "ь.loclBGR", ("x", [], [("uni044A", (-BIG, 620, 300, BIG), (300, 884),
                                                                    (1, 1, 270, 1434))])),
                  # г is ī, the bar free above ı as Charis and Libertinus
                  # draw it (2026-11-08; ū's first stem with its
                  # bar, srb_ge, kept too little of the bar to read)
                  "г.loclSRB": ("alias", "imacron", None),
                  # п and т are и and ш with the bar free above them, as
                  # Charis and Libertinus draw them (serbian_bars; Old
                  # Standard's own, afii10831/2, had it fused onto the
                  # stems: 2026-11-08)
                  "п.loclSRB": ("alias", "uni0438", None),
                  "т.loclSRB": ("alias", "uni0448", None)}
# Old Standard's own localized forms taken as they are (none now)
OS_LOCL = {}
# т's bar against п's (ū's macron): Charis 1.85, Libertinus 1.84
SRB_TE_BAR = 1.84
# aliases of a plain letter in the Regular that the Italic makes itself
ITALIC_LOCL = {"uni0433.loclSRB", "uni0434.loclSRB", "uni0453.loclSRB",
               "uni0438.loclBGR", "uni043F.loclBGR", "uni0442.loclBGR", "uni0448.loclBGR"}


def shifted(path, dx):
    from derive import to_path

    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return to_path(None, rec=rec)


def pathops_empty():
    import pathops

    return pathops.Path()


def derive_rect(x0, y0, x1, y1):
    from derive import rect_path

    return rect_path(x0, y0, x1, y1)


def transplant(up, regular, name, source, curl=False):
    """name as the Regular makes it of source: what the Regular adds (a
    hook) and takes away (a serif), moved onto the same stroke of the
    Italic's source, found where the added part meets the letter, and
    scaled about the join as much as that stroke is lighter in the Italic. A part that
    does not touch the letter (the dot of ʘ) is centred as in the Regular."""
    import derive
    from derive import path_op, to_path

    rs, rt = to_path(regular, regular[source]), to_path(regular, regular[name])
    # the Regular's letter as its recipe made it: the side bearings derive.py
    # changes after it (SPACING) are the Regular's, the Italic has its own
    # (ITALIC_SIDEBEARINGS); moved, the letter less its base is no longer the part
    u = regular[name].unicode
    dl, dr = derive.SPACING.get(chr(u), (0, 0)) if u else (0, 0)
    if dl:
        rec = RecordingPen()
        rt.draw(TransformPen(rec, (1, 0, 0, 1, -dl, 0)))
        rt = to_path(None, rec=rec)
    regular_width = regular[name].width - dl - dr
    if rs.bounds == (0, 0, 0, 0):  # drawn from nothing (₪ on space): the Regular's
        g = up[name]
        draw_path(regular, regular[name], g, rt)
        g.width = regular_width
        return
    added, removed = path_op(rt, rs, "DIFFERENCE"), path_op(rs, rt, "DIFFERENCE")
    if added.bounds == (0, 0, 0, 0):
        raise ValueError("nothing added")

    def grown(path, by=4):
        out = path
        for d in (-by, by):
            out = path_op(out, shifted(path, d), "UNION")
            rec = RecordingPen()
            path.draw(TransformPen(rec, (1, 0, 0, 1, 0, d)))
            out = path_op(out, to_path(None, rec=rec), "UNION")
        return out

    def strokes_at(font, glyph_name, y):
        xs = ink_slice(font, glyph_name, y + 0.01)
        return list(zip(xs[::2], xs[1::2]))

    join = path_op(grown(added), rs, "INTERSECTION")
    if join.bounds == (0, 0, 0, 0):
        # apart from the letter: where the Regular has it within the ink
        y = (added.bounds[1] + added.bounds[3]) / 2
        r_xs, i_xs = ink_slice(regular, source, y + 0.01), ink_slice(up, source, y + 0.01)
        if not r_xs or not i_xs:
            raise ValueError("no ink beside the part")
        dx = (i_xs[0] + i_xs[-1]) / 2 - (r_xs[0] + r_xs[-1]) / 2
        ratio = 1
    else:
        jx0, jy0, jx1, jy1 = join.bounds
        ax, ay = (jx0 + jx1) / 2, (jy0 + jy1) / 2
        # at the join, or a little up the stroke (a hook at a stem's foot)
        for y in (ay, (ay + jy1) / 2, jy1 - 1, jy1 + 30, jy1 + 80, jy1 + 150):
            r_runs, i_runs = strokes_at(regular, source, y), strokes_at(up, source, y)
            if r_runs and i_runs:
                break
        else:
            raise ValueError("no stroke where the part joins")
        k = min(range(len(r_runs)), key=lambda n: abs((r_runs[n][0] + r_runs[n][1]) / 2 - ax))
        right = ax > (rs.bounds[0] + rs.bounds[2]) / 2
        # the Italic's stroke where the join falls in proportion to the ink
        # (its letters may cross a height more or fewer times)
        (r0, _, r1, _), (i0, _, i1, _) = rs.bounds, to_path(up, up[source]).bounds
        ix = i0 + ((r_runs[k][0] + r_runs[k][1]) / 2 - r0) * (i1 - i0) / (r1 - r0)
        run = min(i_runs, key=lambda r: abs((r[0] + r[1]) / 2 - ix))
        dx = (run[0] + run[1]) / 2 - (r_runs[k][0] + r_runs[k][1]) / 2
        # as much lighter as the stroke it joins, at most as much as the
        # Italic's stems are (a hairline or terminal: just that much; a bar
        # met at its end, whose run is its length, not its weight (ʐ's
        # foot from z's bar): that much too)
        capital = ink_bounds(regular, source)[3] > (XH + CAP) / 2 and source[:1].isupper()
        # the Italic's stems to the Regular's, weighted
        ref, h = ("H", CAP / 2) if capital else ("n", XH / 2)
        (a0, a1), (b0, b1) = derive.stems_at(up, ref, h)[0], derive.stems_at(regular, ref, h)[0]
        stems = (a1 - a0) / (b1 - b0)
        w_r, w_i = r_runs[k][1] - r_runs[k][0], run[1] - run[0]
        wider = 1.15 * (208 if capital else 164)  # than any stem of its kind in the Regular
        ratio = stems if w_r < 100 or w_r > wider else min(1, max(stems, w_i / w_r))
        if curl and right:
            # a curl from a terminal (Ƈ Ɠ Ƙ Ƴ): the Italic's stroke ends
            # where it ends, with no beak to cut; the curl starts there, as
            # in the Regular it starts where the stroke ends once cut
            band = derive_rect(-10000, jy0 - 150, 10000, jy1 + 150)
            r_ext = path_op(path_op(rs, removed, "DIFFERENCE"), band, "INTERSECTION").bounds
            i_ext = path_op(to_path(up, up[source]), band, "INTERSECTION").bounds
            if r_ext != (0, 0, 0, 0) and i_ext != (0, 0, 0, 0):
                dx = i_ext[2] - r_ext[2] if right else i_ext[0] - r_ext[0]
            removed = pathops_empty()
    if ratio < 0.97:
        # the part scaled about the join, so it is the Italic's weight (and
        # size) with its hairlines in proportion
        rec = RecordingPen()
        added.draw(TransformPen(rec, (ratio, 0, 0, ratio, ax * (1 - ratio), ay * (1 - ratio))))
        added = to_path(None, rec=rec)
    added = shifted(added, dx)
    letter = to_path(up, up[source])
    if join.bounds != (0, 0, 0, 0) and removed.bounds != (0, 0, 0, 0):
        # only what lies beyond the join, where the part takes the letter's
        # place: what the Regular takes off before it (z's beak, for ʐ) is
        # the Regular's own shape, which the Italic's letter does not have
        beyond = derive_rect(jx0 - 10, -10000, 10000, 10000) if right else derive_rect(-10000, -10000, jx1 + 10, 10000)
        removed = path_op(removed, beyond, "INTERSECTION")
    if removed.bounds != (0, 0, 0, 0):
        # what the Regular cuts away (a serif, a terminal), with room: the
        # Italic's is not quite where the Regular's is; the stroke the part
        # joins is kept
        x0, y0, x1, y1 = shifted(removed, dx).bounds
        cut = derive_rect(x0 - 30, y0 - 30, x1 + 30, y1 + 30)
        if join.bounds != (0, 0, 0, 0):
            cut = path_op(cut, derive_rect(run[0], -10000, run[1], 10000), "DIFFERENCE")
        letter = path_op(letter, cut, "DIFFERENCE")
    if join.bounds != (0, 0, 0, 0):
        # where the part and the letter come within a few units of each
        # other, the gap filled (Old Standard's letters do not all stand at
        # 0, its terminals are not the Regular's)
        bridge = path_op(grown(added, 10), grown(letter, 10), "INTERSECTION")
        added = path_op(added, path_op(bridge, grown(shifted(join, dx), 30),
                                       "INTERSECTION"), "UNION")
    out = path_op(letter, added, "UNION")
    g = up[name]
    draw_path(up, up[source], g, out)
    g.width = up[source].width + max(0, regular_width - regular[source].width)
    for a in up[source].anchors:
        g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})


def rhotic(up, source, y):
    """The letter with the rhotic hook (˞) rising from its right side at y:
    the hook's start (its left end) a little inside the stroke."""
    import derive

    ink = ink_bounds(up, "uni02DE")
    sx = ink[0] + 12
    sy = derive.vertical_runs(up, "uni02DE", sx)[0][0]
    tx = derive.stems_at(up, source, y)[-1][1] - 30
    # its end cut (the straight edge from its leftmost point) inside the
    # stroke whole, its far corner 15 units in at its own height: the Bold
    # Italic's wider cut stood out under the hook, a step that left it
    # joined by a neck (ɚ ɝ)
    pts = [(p.x, p.y, p.type) for c in up["uni02DE"].contours for p in c.points]
    i = min(range(len(pts)), key=lambda k: pts[k][0])
    for j in ((i - 1) % len(pts), (i + 1) % len(pts)):
        if (pts[i][2] == "line" and j == (i - 1) % len(pts)) or (pts[j][2] == "line" and j == (i + 1) % len(pts)):
            cx, cy = pts[j][0] - sx + tx, pts[j][1] - sy + y
            edge = derive.stems_at(up, source, cy)[-1][1]
            tx += min(0, edge - 15 - cx)
    out = derive.attach(up, source, [], [("uni02DE", (-BIG, -BIG, BIG, BIG), (sx, sy), (1, 1, tx, y))])
    return out, round(tx + ink[2] - sx + 70)


def glottal(up, source):
    """ʔ from the italic ?: its stroke cut across where it heads down to the
    left, before it curls, and turned down into a stem to the baseline."""
    import derive
    from fontTools.pens.recordingPen import RecordingPen

    px, py, d = 525, 740, math.radians(213)  # on the stroke, its direction
    ux, uy, vx, vy = math.cos(d), math.sin(d), -math.sin(d), math.cos(d)
    far = 5000
    rec = RecordingPen()  # the half-plane ahead of that point
    rec.moveTo((px + vx * far, py + vy * far))
    rec.lineTo((px + (vx + ux) * far, py + (vy + uy) * far))
    rec.lineTo((px + (ux - vx) * far, py + (uy - vy) * far))
    rec.lineTo((px - vx * far, py - vy * far))
    rec.closePath()
    ahead = derive.path_op(derive.to_path(None, rec=rec), derive.rect_path(-BIG, -BIG, BIG, 820), "INTERSECTION")
    top = derive.path_op(derive.to_path(up, up[source]), ahead, "DIFFERENCE")
    top = derive.path_op(top, derive.rect_path(-BIG, 400, BIG, BIG), "INTERSECTION")  # the dot
    stem = derive.attach(up, "space", [],
                         [("curl", {"at": ("pt", px, py, 112), "dir": 213, "turn": "ccw", "r": 200,
                                    "sweep": 57, "ball": 5, "t": (112, 112), "lead": 0}, (0, 0), (1, 1, 0, 0)),
                          ("line", ((434, 590), (434, 0), 112), (0, 0), (1, 1, 0, 0))])
    return derive.path_op(top, stem, "UNION")


def case_weight(font, g):
    """the weight added to a letter of g's case"""
    return CAP_WEIGHT if capital(font, g) else WEIGHT


def weight_of(font, name):
    """The weight added to a glyph's thick strokes: Old Standard's letters'
    as they are taken (WEIGHT, the capitals CAP_WEIGHT), and that of all
    made of them."""
    if name not in font or font[name].lib.get(SOURCE_KEY) not in ("Old Standard", "derived", "small cap draft"):
        return 0
    return case_weight(font, font[name])


def reweight(up, name, w):
    """up[name] (decomposed) with its thick strokes w heavier (weight_thick)"""
    g = up[name]
    rec = DecomposingRecordingPen(up)
    g.draw(rec)
    out = weight_thick(rec, w)
    g.clearContours()
    g.clearComponents()
    out.draw(g.getPen())


def enlarged(font, up, ch, op, source, band, name):
    """A letter scaled to another case (ɩ -> Ɩ with o -> O, Ʊ -> ʊ.sc):
    derive.enlarge brings all its strokes to the new size's weight by one
    amount, which the added weight (WEIGHT on the thick strokes, none on
    the thin) does not scale with: Ɩ's tail thinned to a sliver. So made of
    the glyphs without it, the letter then given the weight of its case."""
    import derive

    refs = {source, *(n for n in band if isinstance(n, str))}
    if derive.ENLARGE_LIKE.get(ch):  # the letter it is scaled like (ʛ as ɢ from g.sc)
        refs.add(derive.ENLARGE_LIKE[ch])
    saved = {n: copy.deepcopy(up[n]) for n in refs if weight_of(font, n) and n in up}
    try:
        for n in saved:
            reweight(up, n, -weight_of(font, n))
        derive.build(up, ch, op, source, band, name)
    finally:
        for n, g in saved.items():
            up.layers.defaultLayer.insertGlyph(g, n, overwrite=True)
    w = case_weight(up, up[name])
    if w:
        reweight(up, name, w)


def exit_face(glyph):
    """((x, y), (dx, dy)): the end face of the italic exit stroke rightmost
    in glyph, the short line dropping to the right at about x-height / 2.5
    (ı u a п: 42 units, from 353 down 12)"""
    best = None
    for c in glyph.contours:
        pts = c.points
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            if not (p.type and q.type == "line"):
                continue
            dx, dy = q.x - p.x, q.y - p.y
            if 20 < math.hypot(dx, dy) < 100 and dx > 0 and -dx < dy < 0 and 0.25 * XH < p.y < 0.6 * XH:
                if best is None or p.x > best[0][0]:
                    best = ((p.x, p.y), (dx, dy))
    if best is None:
        raise ValueError(f"{glyph.name}: no exit face")
    return best


def heavier_stem(up, name, r, foot):
    """up[name]'s stem (f's, lighter than r's: 145 against 159-178) made as
    heavy as r's where its turn begins, its right edge leaning out from the
    foot serif's top (foot) as r's widens into its shoulder; the turn's
    first handle turned with the edge (2026-11-04)"""
    import derive

    pts = up[name].contours[0].points
    right = lambda y: derive.stems_at(up, name, y)[0][1]  # noqa: E731
    edge = [i for i, p in enumerate(pts) if p.type and foot < p.y < 0.6 * XH and abs(p.x - right(p.y)) < 3]
    if not edge:
        raise ValueError(f"{name}: no stem edge")
    top = max(edge, key=lambda i: pts[i].y)
    yt = pts[top].y
    (a, b), (c, d) = derive.stems_at(up, r, yt)[0], derive.stems_at(up, name, yt)[0]
    gain = (b - a) - (d - c)
    if gain <= 0:
        return
    turn = math.atan2(gain, yt - foot)
    for i in edge:
        pts[i].x += gain * (pts[i].y - foot) / (yt - foot)
    n = len(pts)
    for j in ((top + 1) % n, (top - 1) % n):
        h = pts[j]
        if h.type is None and h.y > yt - 1:
            dx, dy = h.x - (pts[top].x - gain), h.y - yt
            co, si = math.cos(-turn), math.sin(-turn)
            h.x, h.y = pts[top].x + dx * co - dy * si, yt + dx * si + dy * co


def fishhook(up, source, band, name):
    """ɾ in up[name] (upright frame): f (source) brought down until its top
    is r's, its crossbar and all under the baseline cut away, on the foot
    serif band gives (r, (x0, y0, x1, y1): the rectangle as placed under
    r's stem), moved under f's stem; the stem as heavy as r's
    (heavier_stem); the slab where it was, the ball as far from the
    advance as r's."""
    import derive

    r, (x0, y0, x1, y1) = band
    pts = lambda g: [p for c in up[g].contours for p in c.points]  # noqa: E731
    dy = max(p.y for p in pts(r)) - max(p.y for p in pts(source))
    # the crossbar: f's level lines about the x-height, beside the stem
    bar = [p.y for p in pts(source) if p.type and 0.85 * XH < p.y < 1.02 * XH]
    b0, b1 = min(bar) - 20, max(bar) + 20
    rec = RecordingPen()
    up[source].draw(TransformPen(rec, (1, 0, 0, 1, 0, dy)))
    out = derive.to_path(None, rec=rec)
    # the crossbar's band cut across, the stem through it drawn again from
    # its edges under and over the band (boxes beside the stem, upright,
    # notched its sloping edges)
    cut = derive.path_op(derive.rect_path(-BIG, -BIG, BIG, 0), derive.rect_path(-BIG, b0 + dy, BIG, b1 + dy), "UNION")
    out = derive.path_op(out, cut, "DIFFERENCE")
    (u0, u1), (v0, v1) = derive.stems_at(up, source, b0)[0], derive.stems_at(up, source, b1)[0]
    stem = RecordingPen()
    stem.moveTo((u0, b0 + dy - 1))
    stem.lineTo((u1, b0 + dy - 1))
    stem.lineTo((v1, b1 + dy + 1))
    stem.lineTo((v0, b1 + dy + 1))
    stem.closePath()
    out = derive.path_op(out, derive.to_path(None, rec=stem), "UNION")
    (r0, r1), (n0, n1) = derive.stems_at(up, r, y1 + 20)[0], derive.stems_at(up, source, y1 + 20 - dy)[0]
    out = derive.path_op(out, derive.rect_path(n0 - (r0 - x0), y0, n1 + (x1 - r1), y1), "UNION")
    g = up[name] if name in up else up.newGlyph(name)
    g.clearContours()
    g.clearComponents()
    g.clearAnchors()
    draw_path(up, up[source], g, out)
    heavier_stem(up, name, r, y1)
    # the slab's left end where the old recipe put it under r
    dx = x0 - (n0 - (r0 - x0))
    g.move((dx, 0))
    # the ball as far from the advance as r's (their tops alike)
    right = lambda gl: max(p.x for c in gl.contours for p in c.points if p.y > 0.6 * XH)  # noqa: E731
    g.width = round(right(g) + up[r].width - right(up[r]))
    for a in up[r].anchors:
        g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})


# Old Standard leans Λ and Δ about 30 and 34 degrees (A 18.5): their right
# leg drawn as an upright stroke slanted, the left one flatter still, a
# right-angled triangle where the references' lean as their A (2026-11-08)
LEAN_AS = {"Lambda": "A", "Deltagreek": "A"}


def axis(font, name):
    """Degrees from upright of the line from the middle of the glyph's foot
    (its lowest 8 %) to the middle of its top (its highest 8 %)."""
    pts = [(p.x, p.y) for c in font[name].contours for p in c.points if p.type]
    ys = [y for _, y in pts]
    y0, y1 = min(ys), max(ys)
    h = y1 - y0
    bot = [x for x, y in pts if y < y0 + 0.08 * h]
    top = [x for x, y in pts if y > y1 - 0.08 * h]
    return math.degrees(math.atan2((min(top) + max(top)) / 2 - (min(bot) + max(bot)) / 2, h))


def lean_as(font, lean=LEAN_AS):
    """Each letter sheared about the baseline until it leans as its model
    (its foot, serifs and base stay; the apex moves; the advance kept).
    A draft until reviewed."""
    for name, model in lean.items():
        if name not in font or model not in font:
            continue
        s = math.tan(math.radians(axis(font, model))) - math.tan(math.radians(axis(font, name)))
        shear(font[name], s, y0=0, extremes=True)
        font[name].lib[SOURCE_KEY] = "derived"
        font[name].lib[DRAFT_KEY] = True


def mirror_zhe(font, name="uni0436"):
    """Old Standard's ж with its left half the right c mirrored about the
    stem's middle (its ball at the top left), not the c turned (its ball at
    the bottom; 2026-11-08). In the upright frame: the stem the
    run through the glyph's middle at 0.68 x-height; left of it cut away and
    the right half mirrored, the stem itself untouched (below); slanted back; moved 41 left and the advance 41 less, as the mirrored
    half reaches less far left (its left side bearing back to the old 28).
    Before anything is made of it (җ, Bulgarian ж follow)."""
    import derive
    from fontTools.pens.transformPen import TransformPen

    if name not in font:
        return
    g = font[name]
    up = ufoLib2.objects.Glyph()
    rec = DecomposingRecordingPen(font)
    g.draw(rec)
    rec.replay(up.getPen())
    shear(up, -SLANT)
    path = derive.to_path(None, rec=(lambda r: (up.draw(r), r)[1])(RecordingPen()))
    b = path.bounds
    middle = (b[0] + b[2]) / 2
    cut = derive.rect_path(-BIG, XH * 0.68 - 0.5, BIG, XH * 0.68 + 0.5)
    runs = sorted((c.bounds[0], c.bounds[2]) for c in derive.path_op(path, cut, "INTERSECTION").contours)
    s0, s1 = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - middle))
    axis = s0 + s1
    # the stem left as it is: cut 6 left of it, the half taken from 3 right
    # of it (from inside, its right edge mirrored bent the left one, and
    # emboldened that bend wobbled); the crossbar's halves overlap by 3
    left = derive.path_op(path, derive.rect_path(-BIG, -BIG, s0 - 6, BIG), "DIFFERENCE")
    right = derive.path_op(path, derive.rect_path(s1 + 3, -BIG, BIG, BIG), "INTERSECTION")
    mirrored = RecordingPen()
    right.draw(TransformPen(mirrored, (-1, 0, 0, 1, axis, 0)))
    out = derive.path_op(left, derive.to_path(None, rec=mirrored), "UNION")
    new = ufoLib2.objects.Glyph()
    out.draw(new.getPen())
    shear(new, SLANT)
    g.clearContours()
    for c in new.contours:
        for p in c.points:
            p.x -= ZHE_SHIFT
        g.contours.append(c)
    for a in g.anchors:
        a.x -= ZHE_SHIFT
    g.width -= ZHE_SHIFT


ZHE_SHIFT = 41


def serbian_bars(font):
    """Serbian and Macedonian italic п and т (loclSRB): и and ш with the bar
    free above, as ū has its macron over u (и is u here): п is ū's parts
    on и; т's bar is the macron stretched SRB_TE_BAR times, standing over
    ш as ū's over u (its ink centre as far right of the letter's)."""
    um = font["umacron"]
    m = next(c for c in um.components if c.baseGlyph == "macron")
    mx, my = m.transformation[4], m.transformation[5]
    mb, ub = font["macron"].getBounds(font), font["u"].getBounds(font)
    shift = (mb.xMin + mb.xMax) / 2 + mx - (ub.xMin + ub.xMax) / 2
    for name, letter, sx in (("uni043F.loclSRB", "uni0438", 1), ("uni0442.loclSRB", "uni0448", SRB_TE_BAR)):
        if name not in font:
            continue
        lb = font[letter].getBounds(font)
        dx = (lb.xMin + lb.xMax) / 2 + shift - sx * (mb.xMin + mb.xMax) / 2
        g = font[name]
        g.clearContours()
        g.clearComponents()
        g.clearAnchors()
        pen = g.getPen()
        pen.addComponent(letter, (1, 0, 0, 1, 0, 0))
        pen.addComponent("macron", (sx, 0, 0, 1, round(dx), round(my)))
        g.width = font[letter].width
        for anchor in font[letter].anchors:
            if anchor.name in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": anchor.name, "x": anchor.x, "y": anchor.y})


def serbian_gje(font):
    """Serbian and Macedonian italic ѓ (uni0453.loclSRB): ī (ı and macron.i,
    as imacron) with the acute over the bar, stacked as ḗ stacks its acute
    over its macron: the step between the two marks ḗ's, the acute moved
    by the difference between the macrons (their ink centres, their tops,
    along the slant). In the final font, its letters spaced."""
    g, im, ref = font["uni0453.loclSRB"], font["imacron"], font["uni1E17"]

    def comp(glyph, name):
        return next(c for c in glyph.components if c.baseGlyph == name)

    mi, rm, ra = comp(im, "macron.i"), comp(ref, "macron"), comp(ref, "acute")
    a, b = font["macron.i"].getBounds(font), font["macron"].getBounds(font)
    lower = a.yMax - b.yMax
    dx = (mi.transformation[4] + ((a.xMin + a.xMax) - (b.xMin + b.xMax)) / 2
          + ra.transformation[4] - rm.transformation[4] + lower * SLANT)
    dy = mi.transformation[5] + lower + ra.transformation[5] - rm.transformation[5]
    g.clearContours()
    g.clearComponents()
    g.clearAnchors()
    pen = g.getPen()
    for c in im.components:
        pen.addComponent(c.baseGlyph, tuple(c.transformation))
    pen.addComponent("acute", (1, 0, 0, 1, round(dx), round(dy)))
    g.width = im.width
    for anchor in im.anchors:
        g.appendAnchor({"name": anchor.name, "x": anchor.x, "y": anchor.y})


def srb_ge(up, source, name):
    """Serbian г (ī) in up[name] (upright frame): ū's first stem from
    up[source] (п.loclSRB) with its bar, the right stem cut away and the
    hairline rising from the bowl ended as the italic exits end (ı u a:
    their end face, dropping to the right, exit_face); the bar
    overhangs the stem as much on the right as on the left. Made of ı, the
    stem leaned as ı's below its cut and as ū's above, bent where they met
    (2026-11-04)."""
    import derive

    runs = lambda y: derive.stems_at(up, source, y)  # noqa: E731
    # between the hairline and the right stem, where both stand apart
    # (and the right stem's exit, the last run), down to below the bowls
    gap = [((r[-3][1] + r[-2][0]) / 2, y) for y in (60, 100, 200, 300, 350) for r in [runs(y)]]
    right = [(gap[0][0], -BIG), *gap, (BIG, gap[-1][1]), (BIG, -BIG)]
    # the exit's end face, the italic's (п's own, ending its right stem's
    # exit: the short line dropping to the right there), put on the
    # hairline's left edge at the face's top
    (fx, fy), face = exit_face(up[source])
    x0 = runs(fy)[1][0]
    k = face[1] / face[0]
    stem = runs(XH * 0.75)[0]
    xl = stem[1] + 20
    top = XH * 0.8
    end = [(xl, fy + k * (xl - x0)), (BIG, fy + k * (BIG - x0)), (BIG, top), (xl, top)]
    # the bar's left end: the first run from the x-height down that is
    # far wider than the stem (the bar lies just under the x-height)
    bar = next(r[0][0] for y in range(XH, round(top), -5) for r in [runs(y)]
               if r and r[0][1] - r[0][0] > 3 * (stem[1] - stem[0]))
    cut = derive.rect_path(stem[1] + (stem[0] - bar), top, BIG, BIG)
    for poly in (right, end):
        rec = RecordingPen()
        rec.moveTo(poly[0])
        for p in poly[1:]:
            rec.lineTo(p)
        rec.closePath()
        cut = derive.path_op(cut, derive.to_path(None, rec=rec), "UNION")
    out = derive.path_op(derive.to_path(up, up[source]), cut, "DIFFERENCE")
    g = up[name] if name in up else up.newGlyph(name)
    g.clearContours()
    g.clearComponents()
    g.clearAnchors()
    draw_path(up, up[source], g, out)
    # as far from the advance as п's own exit, face top to face top
    g.width = round(up[source].width - (fx - x0))
    # the marks over the stem, where ı has them over its own
    (i0, i1), (s0, s1) = derive.stems_at(up, "dotlessi", XH / 2)[0], runs(XH / 2)[0]
    for a in up["dotlessi"].anchors:
        g.appendAnchor({"name": a.name, "x": a.x + (s0 + s1 - i0 - i1) / 2, "y": a.y})


def build_own(up, ch, op, source, band, name, resolve):
    """The Italic's own constructions, which derive.build does not know:
    ɗ, the rhotic ɚ ɝ, the glottal ʔ, made in up[name] (in the upright
    frame) from up's glyphs; so also the Bold Italic's from its own
    (make_bold.rederive). Returns whether ch is one of them."""
    import derive

    if ch == "ɗ":
        # the italic d (its bowl, its exit stroke) with ɓ's top: the
        # f-hook recipe does not fit the italic f, and the Regular's
        # hook transplanted leaves d's flag. ɓ's stem above the cut is
        # scaled across onto d's stem edges, so it runs on without a step
        hooked = resolve("ɓ")
        (a0, a1), (b0, b1) = (derive.stems_at(up, source, DHOOK_CUT)[-1],
                              derive.stems_at(up, hooked, DHOOK_CUT)[0])
        if name in up:
            del up[name]
        derive.build(up, ch, "attach", source, (
            "x", [(-BIG, DHOOK_CUT, BIG, BIG)],
            [(hooked, (-BIG, DHOOK_CUT - 20, BIG, BIG), (b0, 0), ((a1 - a0) / (b1 - b0), 1, a0, 0))]), name)
        return True
    if op == "srb_ge":
        srb_ge(up, source, name)
        return True
    if op == "fishhook":
        fishhook(up, source, band, name)
        return True
    if op not in ("rhotic", "glottal"):
        return False
    if op == "rhotic":
        out, width = rhotic(up, source, band)
    else:
        out, width = glottal(up, source), up[source].width
    g = up[name] if name in up else up.newGlyph(name)
    g.clearContours()
    g.clearComponents()
    g.clearAnchors()
    draw_path(up, up[source], g, out)
    g.width = width
    for a in up[source].anchors:
        g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    return True


def derive_stage(font, regular, late=False, kept=()):
    """derive.py's recipes for the glyphs still sloped roman. Those made
    from a small cap (ɔ.sc from c.sc, ʁ from r.sc) wait for the Italic's
    small caps (smallcaps_stage), late: before it, their sources are the
    Regular's small caps, sloped. Returns what was made, what failed, and
    the names left for the late pass."""
    import derive

    up = upright(font)
    cmap = {u: g.name for g in up for u in g.unicodes}
    _, o_stem, o_hair = derive.strokes(up, "o")

    def resolve(c):
        return derive.resolve(cmap, c)

    # the clicks' bar: upright here, so sloped in the Italic, as heavy
    # against l as the Regular's | against its l
    bar = up.newGlyph("_clickbar")
    bar.width = 512
    def stem(f, name):
        a, b = derive.stems_at(f, name, XH / 2)[0]
        return b - a

    w = stem(regular, "bar") / stem(regular, "l") * stem(up, "l")
    draw_path(up, bar, bar, derive.rect_path(256 - w / 2, -520, 256 + w / 2, CAP))

    made, failed, later = [], [], []
    for ch, op, source, band in ITALIC_SC_RECIPES + derive.RECIPES:
        if ch in SC_DRAFTED:
            continue
        if ch in KEPT_SLOPED:
            continue
        op, source, band = ITALIC_RECIPES.get(ch, (op, source, band))
        name = resolve(ch)
        if name not in font or (font[name].lib.get(SOURCE_KEY) != "sloped roman"
                                and not (late and name in SC_DRAFT_SIDES)):
            continue
        up.lib[derive.STROKE_KEY] = recipe_scale(o_stem, o_hair, case_weight(font, font[name]))
        if len(source) == 1 or (derive.variant(source) and not source[0].isascii()):
            source = resolve(source)
        if (source.endswith(".sc") or ch in SC_LATE) != late:
            if not late:
                later.append(name)
            continue
        if source not in up:
            failed.append(f"{ch}: no {source}")
            continue
        capital = band == "c" or (isinstance(band, tuple) and band[:1] == ("c",))
        old = up[name]
        try:
            if build_own(up, ch, op, source, band, name, resolve):
                pass
            elif op == "stem":
                # through the middle, from the descender to the ascender
                ink = ink_bounds(up, source)
                w = derive.stems_at(up, "l", XH / 2)[0]
                cx, half = (ink[0] + ink[2]) / 2, (w[1] - w[0]) / 2
                out = derive.path_op(derive.to_path(up, up[source]),
                                     derive.rect_path(cx - half, -560, cx + half, 1400), "UNION")
                g = up[name]
                g.clearContours()
                g.clearComponents()
                g.clearAnchors()
                draw_path(up, up[source], g, out)
                g.width = up[source].width
                for a in up[source].anchors:
                    g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
            elif ch in LETTERS:
                g = up[name]
                g.clearContours()
                g.clearComponents()
                x = 0
                for k, c in enumerate(LETTERS[ch]):
                    x -= LETTER_JOIN.get(ch, 0) if k else 0
                    g.getPen().addComponent(cmap[ord(c)], (1, 0, 0, 1, x, 0))
                    x += up[cmap[ord(c)]].width
                g.width = x
            elif ((op in TRANSPLANT_OPS or (op == "hook" and capital) or ch in TRANSPLANT) and ch not in NO_TRANSPLANT
                  and source in regular and name in regular):
                g = up[name]
                g.clearContours()
                g.clearComponents()
                g.clearAnchors()
                try:
                    transplant(up, regular, name, source, curl=op == "curl")
                except (IndexError, ValueError):  # the Regular's is not source plus a part
                    del up[name]
                    derive.build(up, ch, op, source, band, name)
            elif op in ("enlarge", "stretch"):
                del up[name]
                enlarged(font, up, ch, op, source, band, name)
            else:
                del up[name]
                derive.build(up, ch, op, source, band, name)
        except (IndexError, KeyError, ValueError, ZeroDivisionError, AttributeError, TypeError) as e:
            # a recipe the Italic's shapes do not fit
            up.layers.defaultLayer.insertGlyph(old, name, overwrite=True)
            failed.append(f"{ch} ({op}): {e!r}")
            continue
        if name in SC_DRAFT_SIDES:
            # enlarge's emboldening pushes n.sc's crotch under the diagonal
            # past the stem into a loop (the contour crossed itself, the
            # Bold Italic's strokes then measured across it: its stems
            # bulged and notched)
            uncrossed(up, name)
        if name in SC_LEVEL_GAIN:
            level_gain(up, name, *SC_LEVEL_GAIN[name])
        if name in SC_DRAFT_SIDES and old.contours:
            draft_sides(up, name, old)
        if ch in ITALIC_JOINS:
            derive.fair_joins(up[name], *ITALIC_JOINS[ch])
        if ch in ITALIC_RUNS:
            straighten_run(up[name], *ITALIC_RUNS[ch])
        if ch in ITALIC_CORNERS:
            round_corner(up[name], *ITALIC_CORNERS[ch])
        up[name].lib[DRAFT_KEY] = True
        put(font, up, name, "derived")
        made.append(ch)
    return made, failed, later


def weight_thick_level(rec, ay):
    """rec with its thick strokes ay heavier up and down (weight_thick on
    the outline mirrored across the diagonal, mirrored back)"""
    swap = (0, 1, 1, 0, 0, 0)
    mirrored = RecordingPen()
    rec.replay(TransformPen(mirrored, swap))
    out = RecordingPen()
    weight_thick(mirrored, ay).draw(TransformPen(out, swap))
    return out


def uncrossed(up, name, rec=None):
    """up[name] (or rec, drawn into it) with no contour crossing itself or
    another (pathops), its curves split again at their extremes"""
    import derive
    import pathops
    from italic_geometry import EXTREME_PAST

    g = up[name]
    if rec is None:
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
    path = pathops.Path()
    rec.replay(path.getPen())
    clean = RecordingPen()
    pathops.simplify(path, clockwise=False).draw(clean)
    g.clearContours()
    derive.with_extremes(clean, g.getPen(), round_points=False, past=EXTREME_PAST)


def capital_width(up, name, cap):
    """up[name] condensed or widened across (about its ink's left edge)
    until its ink stands to h.sc's as cap's to H's: in the Bold Italic
    level_gain counts the serifs as thick strokes and widens their ends
    (n.sc's ink 1.06 of h.sc's, N's 1.01 of H's)"""
    from smallcaps import ink_bounds

    def wide(n):
        x0, _, x1, _ = ink_bounds(up, n)
        return x1 - x0

    k = wide("h.sc") * wide(cap) / wide("H") / wide(name)
    g = up[name]
    x0, _, x1, _ = ink_bounds(up, name)
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    g.clearContours()
    rec.replay(TransformPen(g.getPen(), (k, 0, 0, 1, x0 * (1 - k), 0)))
    g.width = round(g.width - (x1 - x0) * (1 - k))
    for a in g.anchors:
        a.x = round(x0 + (a.x - x0) * k)


def level_gain(up, name, cap, level):
    """up[name]'s thick strokes made heavier (level: up and down, else
    sideways) until its main stroke stands to h.sc's as cap's to H's (at
    most SC_STROKE_MAX of h.sc's), its side bearings kept"""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
    import derive
    from derived import Outline
    from strokes import main_stroke

    height = up.lib.get("org.myiadidot.smallcapHeight", 1040)

    def weight(n, top):
        return main_stroke(Outline(up, n, (1, 0, 0, 1, 0, 0)), top)[0]

    sc = weight("h.sc", height)
    want = min(weight(cap, CAP) / weight("H", CAP) * sc, SC_STROKE_MAX * sc)
    g = up[name]
    rec = RecordingPen()
    for c in g.contours:
        c.draw(rec)
    x0 = derive.ink_bounds(up, name)[0]
    width = g.width - (derive.ink_bounds(up, name)[2] - x0)
    ys = [p.y for c in g.contours for p in c.points]
    before = (min(ys), max(ys))
    lo, hi = 0.0, 3 * max(0.0, want - weight(name, height))
    for _ in range(8):  # the gain that brings it to want
        ay = (lo + hi) / 2
        g.clearContours()
        heavier = RecordingPen()
        (weight_thick_level(rec, ay) if level else weight_thick(rec, ay)).draw(heavier)
        uncrossed(up, name, heavier)
        lo, hi = (ay, hi) if weight(name, height) < want else (lo, ay)
    if level:
        # the gain up and down took the bottom and top past their overshoots
        # (s.sc's bottom to -35, the capitals'; the small caps' -25): the
        # points past the zones brought back to where they stood before it
        zone_back(g, height, before)
    b = derive.ink_bounds(up, name)
    dx = x0 - b[0]
    for c in g.contours:
        c.move((dx, 0))
    g.width = round(width + b[2] - b[0])


def zone_back(g, height, before):
    """g's points below the baseline and above height scaled toward the
    zone until its lowest and highest stand as in before (ymin, ymax)"""
    ys = [p.y for c in g.contours for p in c.points]
    lo, hi = min(ys), max(ys)
    for c in g.contours:
        for p in c.points:
            if p.y < 0 and lo < before[0] < 0:
                p.y *= before[0] / lo
            elif p.y > height and hi > before[1] > height:
                p.y = height + (p.y - height) * (before[1] - height) / (hi - height)


def draft_sides(up, name, draft):
    """up[name] at the side bearings of draft (upright), its anchors the
    draft's, moved as far as the middle of its ink moved"""
    from smallcaps import ink_bounds

    g = up[name]
    x0, _, x1, _ = ink_bounds(up, name)
    tmp = up.newGlyph("_draft_sides")
    draft.drawPoints(tmp.getPointPen())
    tmp.width = draft.width
    d0, _, d1, _ = ink_bounds(up, "_draft_sides")
    del up["_draft_sides"]
    dx = d0 - x0
    g.move((dx, 0))
    g.width = round(d0 + (x1 - x0) + (draft.width - d1))
    shift = (d0 + d0 + x1 - x0) / 2 - (d0 + d1) / 2
    g.clearAnchors()
    for a in draft.anchors:
        g.appendAnchor({"name": a.name, "x": round(a.x + shift), "y": a.y})


def figures_stage(font, regular):
    """Old-style figures: the lining ones fitted into the band of the
    Regular's, the stems halfway to the lining weight, hairlines kept."""
    import derive
    from smallcaps import ink_bounds

    up = upright(font)
    made = []
    _, stem, hair = derive.strokes(up, "zero")  # the 1 and 4 have no clear hairline
    for d in FIGURES:
        name = d + "oldstyle"
        if name not in font or font[name].lib.get(SOURCE_KEY) != "sloped roman":
            continue
        target, lining = ink_bounds(regular, name), ink_bounds(up, d)
        k = (target[3] - target[1]) / (lining[3] - lining[1])
        # overlaps removed first (Old Standard's 1 and 4 are drawn in parts)
        merged = derive.path_op(derive.to_path(up, up[d]), derive.to_path(up, up[d]), "UNION")
        rec = RecordingPen()
        merged.draw(TransformPen(derive.CubicPen(rec), (k, 0, 0, k, 0, 0)))
        out = embolden(rec, stem * (1 + k) / 2 - k * stem, hair - k * hair)
        x0, y0, x1, _ = out.getBounds()
        dx = (lining[0] + lining[2]) / 2 - (x0 + x1) / 2
        g = up[name]
        g.clearComponents()
        g.clearAnchors()
        g.clearContours()
        out.draw(TransformPen(g.getPen(), (1, 0, 0, 1, dx, target[1] - y0)))
        g.width = up[d].width
        g.lib[DRAFT_KEY] = True
        put(font, up, name, "figure draft")
        made.append(name)
    return made


def smallcaps_stage(font, later=(), redraft=False):
    """Small caps still sloped roman: FontForge's drafts of the Italic's
    capitals (stored: fontforge_inputs.drafts), imported (with their
    anchors) in the upright frame; not those derive_stage makes from them
    afterwards (later). redraft: all drafted anew."""
    import derive
    import smallcaps as sc
    from fontforge_inputs import drafts as fontforge_drafts

    for g in font:
        if (".sc" in g.name and g.lib.get(SOURCE_KEY) == "sloped roman"
                and (g.name not in later or g.name in SC_DRAFT_SIDES)):
            g.lib[SMALLCAP_DRAFT_KEY] = True  # to be replaced
            g.lib.pop("org.myiadidot.derived", None)  # the Regular's ɠ.sc is derived; this one is drafted
    up = upright(font)
    up.features.text = ""  # FontForge only needs the outlines
    height = font.lib.get(sc.HEIGHT_KEY, sc.DEFAULT_HEIGHT)
    lc = derive.stems_at(up, "n", XH / 2)[0]
    uc = derive.stems_at(up, "H", CAP - 300)[0]
    # drafted without the added weight, then given it as a letter: drafted
    # at the weighted stem, FontForge thickens the curves less (c.sc o.sc
    # lighter than their kind)
    lc, uc = lc[1] - lc[0] - WEIGHT, uc[1] - uc[0] - CAP_WEIGHT
    stem = lc + (height - XH) / (CAP - XH) * (uc - lc)
    drafts = fontforge_drafts(up, height, f"{stem:.0f}/{uc:.0f}", redraft=redraft)
    sc.configure(height)
    log = []
    sc.import_drafts(up, drafts, log, redraft=True)
    made = [line.split()[1] for line in log]
    for name in made:
        put(font, up, name, "small cap draft")
        g = font[name]
        rec = RecordingPen()
        for c in g.contours:
            c.draw(rec)
        g.clearContours()
        weight_thick(rec, WEIGHT).draw(g.getPen())
        overshoot_scaled(g, height, sc.SCALE)
    as_capitals(font, made, height)
    return made


# a small cap's main stroke against h.sc's stem may fall this far short of
# its capital's against H's before it is weighted up to it
SC_STROKE_SHORT = 0.02
# a weighting that raises the main stroke by less than this share of what it
# adds is undone
SC_STROKE_REACH = 0.5
# and none heavier than this share of h.sc's stem
SC_STROKE_MAX = 1.10


def as_capitals(font, made, height):
    """FontForge brings the drafts' stems to the small caps' stem but leaves
    their curves and diagonals lighter than their capitals' own proportion
    (o.sc 0.84 of h.sc where O is 1.07 of H, x.sc 0.62 against 0.85, c.sc s.sc
    z.sc n.sc alike; BOXKÄMPFER's "ox" lighter than its "mpfer",
    2026-11-05): each drafted small cap's thick strokes made heavier
    (weight_thick) until its main stroke stands to h.sc's as its capital's
    to H's (strokes.main_stroke, upright, across the stroke)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
    import derive
    import pathops
    from derived import Outline
    from italic_geometry import EXTREME_PAST
    from strokes import main_stroke

    def weight(name, top):
        p = pathops.Path()
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(TransformPen(p.getPen(), (1, 0, -SLANT, 1, 0, 0)))
        return main_stroke(Outline(None, None, path=pathops.simplify(p)), top)[0]

    names = {g.unicode: g.name for g in font if g.unicode is not None}
    stem_uc, stem_sc = weight("H", CAP), weight("h.sc", height)
    for name in made:
        base = font[name.split(".")[0]] if name.split(".")[0] in font else None
        upper = chr(base.unicode).upper() if base is not None and base.unicode else ""
        cap = len(upper) == 1 and names.get(ord(upper))
        if not cap or name == "h.sc":
            continue
        want = weight(cap, CAP)
        if not want:
            continue
        # at most as heavy as the rounds come out (O 1.04-1.07 of H): З's
        # 1.19 made з.sc black beside its neighbours (1.26 in the Bold Italic)
        want = min(want * stem_sc / stem_uc, SC_STROKE_MAX * stem_sc)
        for _ in range(2):
            have = weight(name, height)
            if not have or have >= want * (1 - SC_STROKE_SHORT):
                break
            g = font[name]
            was = copy.deepcopy(g)
            rec = RecordingPen()
            for c in g.contours:
                c.draw(rec)
            g.clearContours()
            ax = want - have
            # its side bearings kept, as make_bold.small_cap_stems keeps them
            # and split again where its curves now run past their points
            # (put() split them so before the weighting moved them)
            heavier = RecordingPen()
            weight_thick(rec, ax).draw(TransformPen(heavier, (1, 0, 0, 1, ax / 2, 0)))
            derive.with_extremes(heavier, g.getPen(), round_points=False, past=EXTREME_PAST)
            for a in g.anchors:
                a.x += ax / 2
            g.width = round(g.width + ax)
            # a main stroke the weighting does not reach (s.sc's spine, near
            # level: its bowls grew 116 units, the spine hardly): as drafted
            if (weight(name, height) or 0) - have < SC_STROKE_REACH * ax:
                g.clearContours()
                for c in was.contours:
                    c.drawPoints(g.getPointPen())
                g.anchors = was.anchors
                g.width = was.width
                break


# a small cap's round past its zone by at most this much is an overshoot
OVERSHOOT_NEAR = 60


def overshoot_scaled(g, height, scale):
    """FontForge's drafts keep the capitals' overshoot in units (39 past 0
    and the small-cap height, 3.7 %; the Italic's capitals 2.7 %): a
    contour whose top or bottom lies within OVERSHOOT_NEAR past its zone
    has the points past it brought nearer by scale, along the slant (the
    glyph is slanted); tails reaching further are left as they are."""
    for c in g.contours:
        ys = [p.y for p in c.points]
        top = max(ys) if height < max(ys) <= height + OVERSHOOT_NEAR else None
        bottom = min(ys) if -OVERSHOOT_NEAR <= min(ys) < 0 else None
        for p in c.points:
            if top is not None and p.y > height:
                y = height + (p.y - height) * scale
            elif bottom is not None and p.y < 0:
                y = p.y * scale
            else:
                continue
            p.x += (y - p.y) * SLANT
            p.y = y


# the Italic's own kerning over the Regular's (measured against italics):
# v w y before round letters less tight (the Regular's -50 left them
# crowded), and f, its top hanging over, closer to the letters with a stem
ITALIC_KERNING = {
    # ƴ: its hook sets its right side; the diagonal under it stood far
    # from a, o, e (kerned until the hook comes near a's terminal)
    ("uni01B4", "public.kern2.a"): -120,
    ("uni01B4", "public.kern2.agrave"): -120,
    ("uni01B4", "public.kern2.c"): -120,
    ("uni01B4", "public.kern2.egrave"): -120,
    ("public.kern1.v", "public.kern2.c"): -10, ("public.kern1.y", "public.kern2.c"): -10,
    ("f", "public.kern2.i"): -60, ("f", "public.kern2.u"): -60, ("f", "m"): -60, ("f", "p"): -60, ("f", "r"): -60,
    # a's exit stroke rises to the right: before v w less kerning than the Regular's -124
    ("public.kern1.a", "public.kern2.v"): -44,
    # Greek (Old Standard's letters) against Greek references, as the
    # Italic's Latin sets them (scripts/quality/greek_pairs.py)
    ("public.kern1.chi", "public.kern2.epsilontonos"): -47,  # χε (the Regular's -158)
    ("public.kern1.eta", "public.kern2.nu"): 86,  # ην
    ("public.kern1.eta", "public.kern2.rho"): 82,  # ηρ
    ("public.kern1.theta", "public.kern2.nu"): 71,  # θν
    ("public.kern1.alpha", "public.kern2.delta"): -70,  # αθ
    ("public.kern1.alpha", "delta"): 0,  # αδ (tight at the cut of 2026-10-21, as in the Bold Italic)
    ("public.kern1.alpha", "public.kern2.xi"): -73,  # αξ
    ("public.kern1.alpha", "public.kern2.zeta"): -79,  # αζ
    ("public.kern1.alpha", "public.kern2.sigma1"): -91,  # ας
    ("public.kern1.tau", "public.kern2.etatonos"): -110,  # τη
    ("public.kern1.sigma", "public.kern2.upsilon"): -120,  # συ
    ("public.kern1.sigma", "public.kern2.etatonos"): -124,  # ση
    ("public.kern1.sigma", "public.kern2.kappa"): -127,  # σκ
    ("public.kern1.Kappa", "public.kern2.alphatonos"): -175,  # Κα
    ("public.kern1.lambda", "public.kern2.epsilontonos"): 15,  # λε (the Regular's -57)
    # where Charis and Libertinus agree against the Italic (tests/test_greek_pairs.py)
    ("public.kern1.sigma", "public.kern2.mugreek"): -21,  # σμ
    ("public.kern1.rho", "public.kern2.gamma"): 32,  # ργ
    # Cyrillic against Cyrillic references, as the Italic's Latin sets them
    # (greek_pairs.py --script cyrillic): the Regular's pairs were made for
    # the upright д л ѵ, the italic's round д and hooked л stood crowded
    ("public.kern1.uni0420", "public.kern2.uni0434"): -94,  # Рд (the Regular's -192)
    ("public.kern1.uni0423", "public.kern2.uni0434"): -130,  # Уд (-352)
    ("public.kern1.uni0490", "public.kern2.uni0434"): -72,  # Ґд (-342)
    ("public.kern1.uni0490", "public.kern2.uni0443"): -168,  # Ґу (-348)
    ("public.kern1.uni0433", "public.kern2.uni043B"): -72,  # гл (-156)
    ("public.kern1.uni0430", "public.kern2.uni0475"): -32,  # аѵ (-124)
}
# the Regular's pairs the Italic does without: tt tf were tightened for the
# roman t (pair review); the italic t's frequent pairs were in range without;
# Cyrillic pairs made for upright forms, in range unkerned in the Italic
# (ду уд уе ул уѫ ъу ѫб оѵ; greek_pairs.py --script cyrillic)
ITALIC_UNKERNED = {("t", "t"), ("t", "f"),
                   ("uni0434", "public.kern2.uni0443"), ("public.kern1.uni0443", "public.kern2.uni0434"),
                   ("public.kern1.uni0443", "public.kern2.uni0435"), ("public.kern1.uni0443", "public.kern2.uni043B"),
                   ("public.kern1.uni0443", "public.kern2.uni046B"), ("public.kern1.uni044A", "public.kern2.uni0443"),
                   ("public.kern1.uni046B", "public.kern2.uni0431"), ("public.kern1.uni043E", "public.kern2.uni0475"),
                   # ΔΥ ΟΥ (and their small caps, copied from them): the
                   # Regular's -206 and -148 made for the upright Δ's open
                   # upper right; the italic Δ's right side is a sloped
                   # stem, Δ ran into Υ (Δ.sc into Υ.sc, the Bold Italic's
                   # overlapping), below every Greek reference; unkerned in
                   # range (greek_pairs refs, capitals and small caps,
                   # samples.pdf review 2026-11-04)
                   ("public.kern1.Deltagreek", "public.kern2.Upsilon"), ("public.kern1.Omicron", "public.kern2.Upsilon")}
# ß's left side looser: with the heavier stems it stood tight against the
# letter before it (measured, scripts/quality/colour.py)
# ʼ ʻ: the Regular's, sloped about half the x-height, stood far right for
# glyphs this high (ʼl touched): as far from l and i as ’ ‘, upright
# the derived letters whose hook, tail or curl set them otherwise beside
# their neighbours than the references set them against their base
# (scripts/quality/derived_spacing.py Italic, to the references' median;
# the Regular's are derive.SPACING): ɠ ʂ ʐ ʃ Ƭ ɻ ҷ қ Ƈ ң Ƴ ƭ ɮ ʄ Ƙ ɳ Ʋ ɱ ɧ Ҳ ʝ ɾ
ITALIC_SIDEBEARINGS = {"germandbls": (25, 0),
                       "uni02BC": (-145, 145), "uni02BB": (-130, 130),
                       "uni0260": (0, -380), "uni0282": (-265, 0), "uni0290": (0, -275), "uni0283": (-215, -135),
                       "uni01AC": (5, 0), "uni027B": (0, -170), "uni04B7": (0, -145), "uni049B": (0, -125),
                       "uni0187": (0, -165), "uni04A3": (0, -145), "uni01B3": (0, -235), "uni01AD": (0, -105),
                       "uni026E": (0, -85), "uni0284": (-130, 0), "uni0198": (0, -180), "uni0273": (0, -130),
                       "uni01B2": (0, -80), "uni0271": (0, -100), "uni0267": (0, -100), "uni04B2": (0, -65),
                       "uni029D": (0, -55), "uni027E": (-90, 0),
                       # ɗ: the hook overhangs, the advance 32 past d's as in the
                       # Regular (Charis 35); set by the hook, ɗa stood 150 looser than da
                       "uni0257": (0, -119),
                       # ɦ.sc (from Ɦ): the least white before its hook as h.sc h.sc's
                       # (107; Ɦ's advance kept, it stood 145, the draft's -19)
                       "uni0266.sc": (-38, 0)}
# the horn's foot sunk into the top of u's stem: set on it, it leaves a
# ledge beside the stem (glyph_lint)
HORN_NUDGE = {"u": (-20, -30), "U": (-20, 0), "u.sc": (-20, 0)}
# the Regular's horn, sloped, was lighter and smaller than every reference
# italic's (ơ: 19 % of o's ink, EB Garamond 22, Libertinus 34, Charis 24):
# scaled about its tip (where it attaches), the Bold Italic's with it
ITALIC_HORN = {"horn": 1.2, "Horn": 1.2}


def swapped_sidebearings(font):
    """Side bearings for the derived letters that are their base turned or
    mirrored (as wide in ink, upright): the base's, swapped, measured
    upright, as the Regular's are. A letter made before its base was
    respaced (Ʊ, turned from Ω before the Greek cut widened it) keeps
    the old spacing otherwise. Returns {glyph: (left, right)} deltas for
    sidebearings()."""
    import derive

    cmap = {u: g.name for g in font for u in g.unicodes}

    def upright_sb(name):
        # (decomposed: shear leaves a component sloped, and Omega, Ʊ's
        # base, is the Ohm sign's composite of Ω)
        g = ufoLib2.objects.Glyph()
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(g.getPen())
        g.width = font[name].width
        shear(g, -SLANT)
        b = g.getBounds(font)
        return (b.xMin, g.width - b.xMax, b.xMax - b.xMin) if b else None

    deltas = {}
    for ch, op, source, band in derive.RECIPES:
        op, source, band = ITALIC_RECIPES.get(ch, (op, source, band))
        if op not in ("turn", "mirror") or len(ch) != 1:
            continue
        name = cmap.get(ord(ch))
        base = cmap.get(ord(source)) if len(source) == 1 else source if source in font else None
        if name is None or base is None or font[name].lib.get(SOURCE_KEY) != "derived":
            continue
        mine, theirs = upright_sb(name), upright_sb(base)
        if mine is None or theirs is None or abs(mine[2] - theirs[2]) > 3:
            continue
        left, right = round(theirs[1] - mine[0]), round(theirs[0] - mine[1])
        if left or right:
            deltas[name] = (left, right)
    return deltas


def horn_stage(font, kept=()):
    """The Horn anchors (draft_vietnamese_marks.py) on the Italic's O U o u,
    their small caps and Ư's bases, found on the upright outlines."""
    from draft_vietnamese_marks import HORN_BASES, horn_anchor

    up = upright(font)
    for base in HORN_BASES:
        if base in kept or base not in font:  # its anchor was set when it was made
            continue
        x, y = horn_anchor(up, base)
        dx, dy = HORN_NUDGE.get(base, (0, 0))
        x, y = x + dx, y + dy
        g = font[base]
        for a in [a for a in g.anchors if a.name == "Horn"]:
            g.anchors.remove(a)
        g.appendAnchor({"name": "Horn", "x": round(x + (y - XH / 2) * SLANT), "y": y})


def os_anchor(osg, name):
    for a in osg.anchors:
        if a.name == name:
            return a.x * KX, ymap(a.y)
    return None


# Myia's anchor names, and Old Standard's to take their place from
ANCHOR_SOURCES = {
    "Top": ["Top"], "Acute": ["Top"], "Grave": ["Top"], "Dotaccent": ["Dotaccent", "Top"],
    "TopCap": ["Top"], "Bottom": ["Bottom"], "DotBelow": ["Bottom"], "Cedilla": ["Bottom"],
    "GreekTop": ["GreekTop", "Top"], "GreekCap": ["GreekCap"], "IotaSubscript": ["Bottom"],
}
# anchors moved a little from there (dx, dy): the cedilla's top corner, from
# Old Standard's Bottom of c, would poke out into the counter
ANCHOR_NUDGE = {("c", "Cedilla"): (0, -4), ("e", "Cedilla"): (0, -10),
                # The Roman t dot rose 59 units after the italic family was
                # reviewed. Retain its recipe anchor for hooked/tailed t;
                # t_dot_anchor sets the plain italic t independently below.
                ("t", "Dotaccent"): (-59 * SLANT, -59)}


def roman_anchor(roman, a, width_it):
    """x of the Regular's anchor a on an italic glyph width_it wide: in
    proportion to the widths, slanted about half the x-height."""
    return a.x * width_it / (roman.width or 1) + (a.y - XH / 2) * SLANT


def missing_anchors(font, regular, marks):
    """The anchors the Regular's glyph has and the Italic's lacks (a turned
    letter takes none from its source, a drafted small cap only its
    capital's), placed as roman_anchor places them; hand-drawn glyphs stay
    as drawn. Returns the names given anchors."""
    given = []
    for g in font:
        if g.name in marks or g.name not in regular or not g.width or g.lib.get(SOURCE_KEY) == "drawn":
            continue
        have = {a.name for a in g.anchors}
        roman = regular[g.name]
        for a in roman.anchors:
            if a.name not in have:
                g.appendAnchor({"name": a.name, "x": round(roman_anchor(roman, a, g.width)), "y": a.y})
                given.append(g.name)
    return sorted(set(given))


def italic_anchors(roman, osg, width_it):
    """Myia's anchors for an Old Standard letter: where Old Standard has the
    anchor (or its stand-in), there, slid along the slant to Myia's height;
    else Myia's, in proportion to the widths and slanted."""
    out = []
    for a in roman.anchors:
        pos = None
        for src in ANCHOR_SOURCES.get(a.name, [a.name]):
            pos = os_anchor(osg, src)
            if pos:
                break
        if pos:
            x = pos[0] + (a.y - pos[1]) * SLANT
        else:
            x = roman_anchor(roman, a, width_it)
        dx, dy = ANCHOR_NUDGE.get((roman.name, a.name), (0, 0))
        out.append((a.name, round(x + dx), a.y + dy))
    return out


def t_dot_anchor(font):
    """Give the tall italic t the same dot clearance as z, along the slant."""
    t, z = font["t"], font["z"]
    ta = next(a for a in t.anchors if a.name == "Dotaccent")
    za = next(a for a in z.anchors if a.name == "Dotaccent")
    dy = round(za.y + t.getBounds(font).yMax - z.getBounds(font).yMax - ta.y)
    ta.x += round(dy * SLANT)
    ta.y += dy


def attach(font, glyph_name, mark, bases):
    """The anchor (name, x in the composite) a mark component sits on: the
    base anchor nearest to the mark's ink (as in make_bold)."""
    from smallcaps import ink_bounds

    ink = ink_bounds(font, mark.baseGlyph)
    if ink is None:
        return None
    mx = mark.transformation[4] + (ink[0] + ink[2]) / 2
    my = mark.transformation[5] + (ink[1] + ink[3]) / 2
    # the anchors this mark attaches to (those of the combining marks made
    # of it, without the underscore); any if none is known
    names = set()
    for g in font:
        if g.width == 0 and len(g.components) == 1 and g.components[0].baseGlyph == mark.baseGlyph:
            names |= {a.name[1:] for a in g.anchors if a.name.startswith("_") and "Mark" not in a.name}
    best = None
    for base, bdx, bdy in bases:
        for a in font[base].anchors:
            if a.name.startswith("_") or (names and a.name not in names):
                continue
            d = abs(a.x + bdx - mx) + abs(a.y + bdy - my)
            if best is None or d < best[0]:
                best = (d, base, a.name)
    return best[1:] if best else None


# the breathings and accents set before a Greek capital (Ἀ Ἔ Ὦ ...), and
# the composite measured for each capital
GREEK_CAP_SAMPLES = {"Alpha": "uni1F08", "Epsilon": "uni1F18", "Eta": "uni1F28", "Iota": "uni1F38",
                     "Omicron": "uni1F48", "Rho": "uni1FEC", "Upsilon": "uni1F59", "Omegagreek": "uni1F68"}


def greek_cap_room(font, regular):
    """Old Standard's GreekCap anchors leave a breathing far from its
    capital (Ἀ about twice the Regular's white): each capital's mark is
    brought as near as it stands in the Regular, judged upright (the
    letter's leftmost ink against the mark's), and the capital moved left
    by as much, in its composites (with what follows it: ᾈ's iota) and in
    the room the GreekCapsafter... lookups make for a combining mark, so
    that the decomposed text sets the same. Returns {capital: shift}."""
    def left(f, c, slant):
        pen = BoundsPen(f)
        f[c.baseGlyph].draw(TransformPen(TransformPen(pen, (1, 0, -slant, 1, 0, 0)), c.transformation))
        return pen.bounds[0]

    def spread(f, name, base, slant):
        comps = f[name].components
        b = next(c for c in comps if c.baseGlyph == base)
        m = next(c for c in comps if c.baseGlyph != base)
        return left(f, b, slant) - left(f, m, slant)

    shift = {}
    for base, sample in GREEK_CAP_SAMPLES.items():
        if sample in font and sample in regular:
            shift[base] = round(spread(font, sample, base, SLANT) - spread(regular, sample, base, 0))
    for base, d in shift.items():
        for a in font[base].anchors:
            if a.name == "GreekCap":
                a.x += d
    for g in font:
        if g.unicode is None or not g.components or g.contours:
            continue
        if not unicodedata.name(chr(g.unicode), "").startswith("GREEK CAPITAL"):
            continue
        caps = [c for c in g.components if c.baseGlyph in shift]
        if len(caps) != 1 or caps[0].transformation[4] <= 0:
            continue  # no room made before the capital
        cap = caps[0]
        x0, d = cap.transformation[4], shift[cap.baseGlyph]
        for c in g.components:
            t = c.transformation
            if t[4] >= x0:
                c.transformation = (t[0], t[1], t[2], t[3], t[4] - d, t[5])
        g.width -= d
    rule = re.compile(r"(lookup GreekCapsafter\w+ \{.*?\} GreekCapsafter\w+;)", re.DOTALL)
    pos = re.compile(r"pos \\(\w+) <(-?\d+) 0 (-?\d+) 0>;")

    def room(m):
        return pos.sub(lambda p: (f"pos \\{p[1]} <{int(p[2]) - shift.get(p[1], 0)} 0 "
                                  f"{int(p[3]) - shift.get(p[1], 0)} 0>;"), m[1])

    font.features.text = rule.sub(room, font.features.text)
    return shift


def move_parts(font, regular, marks, rule_made):
    """The composites the rules do not make keep their parts: their marks
    moved as the base anchor they sit on moved, later letters with the
    first's change of width, the width following the base."""
    for g in font:
        if not g.components or g.contours or g.name in rule_made or g.name in marks:
            continue
        rg = regular[g.name]
        bases = [(c.baseGlyph, c.transformation[4], c.transformation[5])
                 for c in rg.components if c.baseGlyph not in marks]
        if not bases:
            continue
        first = bases[0][0]
        for c, rc in zip(g.components, rg.components, strict=True):
            xx, xy, yx, yy, dx, dy = rc.transformation
            if c.baseGlyph in marks:
                hit = attach(regular, g.name, rc, bases)
                if hit:
                    base, anchor = hit
                    ra = {a.name: (a.x, a.y) for a in regular[base].anchors}.get(anchor)
                    ia = {a.name: a.x for a in font[base].anchors}.get(anchor)
                    if ra is not None and ia is not None:
                        # the base anchor moved; the sloped mark's own anchor
                        # moved by its height along the slant
                        dx = dx + ia - ra[0] - ra[1] * SLANT
            elif dx:
                # a second letter (Ĳ, ...) or room for an accent (Έ): letters
                # after the first move with the first's change of width
                if rg.components[0].baseGlyph != c.baseGlyph and dx >= regular[first].width:
                    dx = dx + font[first].width - regular[first].width
            c.transformation = (xx, xy, yx, yy, round(dx), dy)
        room = [(base, dx) for base, dx, _ in bases if dx > 0]
        if len(bases) == 1 and room and rg.width == regular[room[0][0]].width + room[0][1]:
            g.width = font[room[0][0]].width + room[0][1]
        elif len(bases) == 1:
            g.width = font[first].width + (rg.width - regular[first].width)


# their repairs match their exact points (aleph.py, l_belt.py): slanted
# without splitting their curves at the extremes the slant moves
POINT_REPAIRS = {"uni2135", "uni026C", "uniA7AD"}
# Rounded plainly, not smoothly (make_bold.round_smoothly): the repairs of
# ℵ (aleph.py) and of ɬ Ɬ's belts (l_belt.py) match their exact points;
# ȷ's descender is cut and attached for the Bold Italic ɱ and ɧ, where a
# unit moves the cut; ƹ's smoothed handle takes its top off the x-height
# zone once CFF-hinted (12-15 ppem); the rest gain little or nothing here
# and break joins or extremes in the Bold Italic (ϗ.sc: two findings fewer
# here, five more there).
ROUND_PLAIN = ("uni2135", "uni026C", "uniA7AD", "uni0237", "uni01B9", "eight", "k.sc", "section", "uni023B", "uni03D7.sc")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("italic", nargs="?", default=str(ROOT / "sources/MyiaDidot-Italic.ufo"))
    ap.add_argument("--redraft", action="store_true", help="draft every small cap anew with FontForge")
    args = ap.parse_args()
    regular = ufoLib2.Font.open(args.regular)
    font = ufoLib2.Font.open(args.regular)
    # the Regular as it was spaced before respace.py: the offsets and widths
    # taken from it below were tuned on that; the Italic has its own cut
    undo(regular)
    undo(font)
    kern_clear.undo(font)  # the Regular's loosened pairs: the Italic finds its own
    oldstd = source_font()  # fontforge_inputs: converted once, kept in sources/oldstand
    previous = ufoLib2.Font.open(args.italic) if (Path(args.italic) / "metainfo.plist").exists() else None
    os_cmap = {u: g.name for g in oldstd for u in g.unicodes}

    marks = {g.name for g in regular if mark_like(g)}
    for g in regular:
        if g.width == 0 and len(g.components) == 1 and not g.contours:
            marks.add(g.components[0].baseGlyph)

    # composites the rules make as they are: rebuilt from the Italic's anchors
    builder = Builder(regular)
    rule_made = set()
    for g in regular:
        if not g.components or g.contours or g.unicode is None or g.name in SPECIAL:
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = builder.recipe(g.unicode)
        except ValueError:
            continue
        mine = sorted((c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components)
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) == mine:
            rule_made.add(g.name)

    taken, kept_roman = 0, 0
    for g in font:
        osname = os_cmap.get(g.unicode) if g.unicode is not None else (g.name if g.name in oldstd else None)
        osname = OS_LOCL.get(g.name, osname)
        if g.name in ROMAN_GLYPHS:
            # an alias in the Regular: its outlines, sloped
            rec = DecomposingRecordingPen(regular)
            g.draw(rec)
            g.clearComponents()
            rec.replay(g.getPen())
            shear(g, SLANT, extremes=g.name not in POINT_REPAIRS)
            g.lib[SOURCE_KEY] = "sloped roman"
            kept_roman += 1
            continue
        if g.name in ITALIC_LOCL:
            # made below by its italic recipe, as what Old Standard lacks
            g.clearComponents()
            g.lib[SOURCE_KEY] = "sloped roman"
            continue
        if g.unicode is not None and (keeps_upright(g.unicode) or g.unicode in ROMAN_SIGNS
                                      or chr(g.unicode) in OWN_RECIPE):
            osname = None  # Myia's own, upright or sloped (below)
        if g.name in marks:
            # Myia's accents, sloped about the height they sit at
            t = sloped(0)
            if g.name in ITALIC_HORN:
                k = ITALIC_HORN[g.name]
                t = (k, 0, SLANT * k, k, 440 * (1 - k), 0)  # scaled about (440, 0), then sloped
            if g.contours:
                rec = RecordingPen()
                for c in g.contours:
                    c.draw(rec)
                out = ufoLib2.objects.Glyph()
                rec.replay(TransformPen(out.getPen(), t))
                redraw(g, out)
            for c in g.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, round(dx + dy * SLANT), dy)
            for a in g.anchors:
                a.x = round(a.x + a.y * SLANT)
        elif osname and (not (g.components and not g.contours) or g.name in OS_LOCL):
            # an Old Standard letter, unless Myia makes this glyph of others
            # (an alias, an accented letter rebuilt below)
            osg = oldstd[osname]
            rec = DecomposingRecordingPen(oldstd)
            osg.draw(rec)
            zoned = RecordingPen()
            rec.replay(Zones(zoned))
            out = rezone(embolden(zoned, AX, AY), AY)  # the flat edges kept on the zones
            # the added weight, on the letters (the accents and upright signs
            # are left as they are)
            rec = RecordingPen()
            out.draw(rec)
            out = weight_thick(rec, CAP_WEIGHT if capital(font, g) else WEIGHT)
            anchors = italic_anchors(regular[g.name], osg, osg.width * KX)
            g.clearComponents()
            redraw(g, out)
            g.width = round(osg.width * KX)
            if not g.width and regular[g.name].width:
                # Old Standard's paragraphos ⸏ ⸐ ⸑ hang at zero width; the
                # Regular gives them an advance (fontbakery: base_has_width)
                g.width = regular[g.name].width
            g.clearAnchors()
            for name, x, y in anchors:
                g.appendAnchor({"name": name, "x": x, "y": y})
            g.lib["org.myiadidot.italicSource"] = "Old Standard"
            if g.unicode and (0x2100 <= g.unicode <= 0x214F or 0x1D400 <= g.unicode <= 0x1D7FF):
                # its mathematical letters (𝔐 ℵ) are upright
                shear(g, SLANT, extremes=g.name not in POINT_REPAIRS)
            taken += 1
        elif g.contours:
            # not in Old Standard: Myia's roman, sloped about half the x-height
            shear(g, SLANT, extremes=g.name not in POINT_REPAIRS)
            g.lib["org.myiadidot.italicSource"] = "sloped roman"
            kept_roman += 1

    # Old Standard's W and a, redrawn (before anything is made of them)
    redraw_w(font)
    lighten_a(font)
    mirror_zhe(font)
    lean_as(font)
    # what was reviewed or drawn in the Italic stays
    # (and the Italic's own, reviewed: ʀ.sc, drafted from its Ʀ, is not in the Regular)
    # (drafts made at other weights come back as drafts, drawn ones stay)
    same_settings = previous is not None and previous.lib.get(MADE_WITH_KEY) == MADE_WITH
    kept = [g.name for g in (previous or []) if reviewed(g)
            and (same_settings or g.lib.get(SOURCE_KEY) == "drawn")
            and (g.name in font or g.name.endswith(".sc"))]
    for name in kept:
        font.layers.defaultLayer.insertGlyph(copy.deepcopy(previous[name]), name, overwrite=True)
    from italic_contours import finish_bases

    finish_bases(font, skip=kept)
    from r_hook import round_shoulder

    round_shoulder(font, skip=kept)
    # what Old Standard lacks, made from what it has
    upright_signs = 0
    for g in list(font):
        if g.unicode is not None and g.lib.get(SOURCE_KEY) == "sloped roman" and keeps_upright(g.unicode):
            r = copy.deepcopy(regular[g.name])
            r.lib[SOURCE_KEY] = "roman"
            font.layers.defaultLayer.insertGlyph(r, g.name, overwrite=True)
            upright_signs += 1
    derived, failed, later = derive_stage(font, regular, kept=kept)
    figures = figures_stage(font, regular)
    small_caps = smallcaps_stage(font, later, redraft=args.redraft)
    if "w.sc" in small_caps:
        redraw_w(font, "w.sc", "v.sc")  # as W of V
    # a small cap the Regular lacks (ʀ.sc, drafted from the Italic's own Ʀ):
    # in the glyph order after its letter, a base glyph
    order = list(font.glyphOrder)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    for name in sorted(g.name for g in font if g.name not in order):
        stem = name.split(".")[0]
        order.insert(order.index(stem) + 1 if stem in order else len(order), name)
        cats.setdefault(name, "base")
    font.glyphOrder = order
    derived_late, failed_late, _ = derive_stage(font, regular, late=True, kept=kept)
    derived += derived_late
    failed += failed_late
    horn_stage(font, kept)
    from italic_ligatures import NAMES as LIGATURE_NAMES
    font.kerning.update(ITALIC_KERNING)
    for pair in ITALIC_UNKERNED:
        font.kerning.pop(pair, None)
    still = sorted(g.name for g in font if g.lib.get(SOURCE_KEY) == "sloped roman"
                   and g.name not in LIGATURE_NAMES)

    # aliases (one letter, unmoved: Cyrillic Е is E) show the Italic letter:
    # its width and its anchors, before anything is built from them
    for g in font:
        if (len(g.components) == 1 and not g.contours and g.name not in marks and g.name not in kept
                and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            src = font[g.components[0].baseGlyph]
            g.width = src.width
            # the anchors it shares with the letter, the letter's (sloped);
            # its own besides stay (Ο's GreekCap: kept, it stood upright
            # with the Regular's TopCap and Bottom, 2026-11-08)
            own = [a for a in g.anchors if a.name not in {s.name for s in src.anchors}]
            g.clearAnchors()
            for a in list(src.anchors) + own:
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})

    # letters Old Standard draws with their accent in one outline (Ť): made
    # from base and mark like the decomposed text (not upstream's specials)
    t_dot_anchor(font)
    from y_dot import y_dot_anchor

    y_dot_anchor(font)
    log = []
    stack_anchors(font, log)
    b = Builder(font)
    exceptions = {line.split()[0] for line in (ROOT / "tests/data/nfd-exceptions.txt").read_text().splitlines()
                  if line.startswith("U+")}
    for g in list(font):
        if (g.unicode is None or not g.contours or g.components or g.name in SPECIAL
                or f"U+{g.unicode:04X}" in exceptions or g.lib.get("org.myiadidot.italicSource") != "Old Standard"):
            continue
        if len(unicodedata.normalize("NFD", chr(g.unicode))) < 2:
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = g.name, dict(g.lib)
        del font[g.name]
        b.write(r)
        font[r.name].lib.update(lib)

    # composites: the others first (i, made of ı and a dot, is a base of the
    # rules' ones), then those of the rules rebuilt, then the others again
    move_parts(font, regular, marks, rule_made)
    rebuilt = 0
    for name in sorted(rule_made):
        g = font[name]
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        r.name, lib = name, dict(g.lib)
        del font[name]
        b.write(r)
        font[name].lib.update(lib)
        rebuilt += 1
    move_parts(font, regular, marks, rule_made)
    greek_shift = greek_cap_room(font, regular)  # the breathings nearer their capitals
    info = font.info
    info.styleName = "Italic"
    info.styleMapStyleName = "italic"
    info.italicAngle = -ANGLE
    info.postscriptFontName = "MyiaDidot-Italic"
    info.postscriptFullName = "Myia Didot Italic"
    info.copyright = info.copyright.replace(
        " Copyright 2012", " Copyright 2006-2008 Alexey Kryukov (Old Standard Italic). Copyright 2012", 1)
    # (the italic bit comes from styleMapStyleName; USE_TYPO_METRICS stays)
    font.lib.pop("org.myiadidot.figuresLightened", None)  # the Regular's (lighten_figures.py), not these
    font.lib["org.myiadidot.italicSource"] = "Old Standard Italic, akryukov/oldstand (see sources/oldstand/COMMIT)"
    font.lib[MADE_WITH_KEY] = MADE_WITH
    # Old Standard's outlines crossing themselves at serif tips, crumbs of
    # the cuts (glyph_lint); hand-drawn glyphs stay as drawn
    from glyph_lint import fix

    # no letter is weighted whole any more (its weight came with its base);
    # those kept from the last run were weighted as they were then
    last = previous.lib.get(WHOLE_KEY, {}) if previous else {}
    font.lib[WHOLE_KEY] = dict(sorted((n, why) for n, why in last.items() if n in kept and n in font))
    cleaned = fix(font, [g.name for g in font if g.lib.get(SOURCE_KEY) != "drawn"])
    # the letters spaced tighter (scripts/respace.py), not those kept from the
    # last run, which were (what comes from the Regular has its cut too)
    letter_cut = classifier(font, ITALIC_CUT, ITALIC_CUT_GREEK)
    # what is made only of kept glyphs (their aliases, accented forms) has
    # the cut through them: not cut again; the kept ones not touched at all
    settled = set(kept)
    grew = True
    while grew:
        grew = False
        for g in font:
            if (g.name not in settled and g.components and not g.contours
                    and all(c.baseGlyph in settled or c.baseGlyph in marks for c in g.components)
                    and any(c.baseGlyph in settled for c in g.components)):
                settled.add(g.name)
                grew = True
    respace(font, lambda n: 0 if n in settled else letter_cut(n), [g.name for g in font if g.name not in kept])
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)
    sidebearings(font, swapped_sidebearings(font))
    sidebearings(font, ITALIC_SIDEBEARINGS)
    # an alias a recipe made (Serbian д of g) follows its letter's final width,
    # as derive.py's do in the Regular
    for g in font:
        if (g.lib.get(SOURCE_KEY) == "derived" and g.name not in kept and len(g.components) == 1
                and not g.contours and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            g.width = font[g.components[0].baseGlyph].width
    if "uni0453.loclSRB" not in kept:
        serbian_gje(font)
    if not {"uni043F.loclSRB", "uni0442.loclSRB"} & set(kept):
        serbian_bars(font)
    # the kept ones as they were (the side bearings above, respace carrying
    # composites along, moved them again each run: г.loclSRB -80 a run);
    # an alias still as wide as its letter
    for name in kept:
        g = copy.deepcopy(previous[name])
        if len(g.components) == 1 and not g.contours and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0):
            g.width = font[g.components[0].baseGlyph].width
        font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)
    font.lib[CUT_KEY] ={"cut": ITALIC_CUT, "greekLower": ITALIC_CUT_GREEK}
    anchored = missing_anchors(font, regular, marks)
    case_forms.make(font)  # punctuation raised onto the capitals (case), on the final widths
    # These joined bowls have drawings at each weight, not weighted joins.
    from cyrillic_signs import redraw as redraw_cyrillic_signs
    from italic_contours import finish as finish_contours

    redraw_cyrillic_signs(font)
    finish_contours(font, skip=kept, smooth=False)
    from italic_i import install as install_italic_i

    install_italic_i(font)
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.italic), plain=ROUND_PLAIN)
    # the accented small caps and the smcp/c2sc features, from the new drafts
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts/smallcaps.py"), args.italic], check=True)
    print(f"{args.italic}: {taken} from Old Standard, {len(kept)} kept as reviewed, "
          f"{upright_signs} signs upright, {len(derived)} derived, {len(figures)} figures, "
          f"{len(small_caps)} small caps drafted, {len(LIGATURE_NAMES)} italic ligatures built, {rebuilt} composites rebuilt, "
          f"{len(cleaned)} cleaned, "
          f"{len(anchored)} given the Regular's anchors they lacked; "
          f"{len(still)} still sloped roman (of {kept_roman}); Greek capitals' marks nearer: "
          + " ".join(f"{n} {d}" for n, d in greek_shift.items()))
    for line in failed:
        print("  recipe failed:", line)
    print("  still sloped roman:", " ".join(still))


if __name__ == "__main__":
    main()
