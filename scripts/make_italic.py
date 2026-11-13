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

Each glyph's lib key org.myiadidot.italicSource says where it came from
(provenance: how a glyph is finished, never whether it is kept). A rerun
keeps exactly the glyphs marked drawn (org.myiadidot.drawn, set with
scripts/drawn.py after editing a glyph: docs/claude/drawn.md); a draft's
cleared flag is review status only and keeps nothing. When the weights or
cuts (MADE_WITH) changed, the kept glyphs are listed to be looked at again.
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
import derive
import kern_clear
from composites import SPECIAL, Builder, stack_anchors
from data_italic import (
    ANCHOR_NUDGE,
    ANCHOR_SOURCES,
    AX,
    AY,
    CAP_WEIGHT,
    GREEK_CAP_SAMPLES,
    HORN_NUDGE,
    ITALIC_CORNERS,
    ITALIC_CUT,
    ITALIC_CUT_GREEK,
    ITALIC_HORN,
    ITALIC_JOINS,
    ITALIC_JOINS_THROUGH,
    ITALIC_KERNING,
    ITALIC_LOCL,
    ITALIC_MARK_SCALE,
    ITALIC_RECIPES,
    ITALIC_RUNS,
    ITALIC_SC_RECIPES,
    ITALIC_SIDEBEARINGS,
    ITALIC_UNKERNED,
    KEPT_SLOPED,
    KX,
    LEAN_AS,
    LETTER_JOIN,
    LETTERS,
    MADE_WITH,
    MATH_SIGNS,
    NO_TRANSPLANT,
    OS_LOCL,
    OWN_RECIPE,
    POINT_REPAIRS,
    ROMAN_GLYPHS,
    ROMAN_SIGNS,
    ROUND_PLAIN,
    SC_DRAFT_SIDES,
    SC_DRAFTED,
    SC_LEVEL_GAIN,
    TRANSPLANT,
    TUNED_AX,
    TUNED_AY,
    WEIGHT,
    ZH_DX,  # noqa: F401  (read as make_italic.ZH_DX elsewhere)
    descender,  # noqa: F401  (read as make_italic.descender elsewhere)
    retroflex,  # noqa: F401  (read as make_italic.retroflex elsewhere)
)
from derive import BIG, draw_path, embolden, rezone
from drawn import is_drawn
from fontforge_inputs import source_font
from italic_geometry import ANGLE, CAP, SLANT, XH, shear, upright
from make_bold import WHOLE_KEY, mark_like, redraw, write
from respace import CUT_KEY, classifier, respace, sidebearings, undo
from smallcaps import ink_bounds, ink_slice
from space_figures import space as space_figures

ROOT = Path(__file__).resolve().parent.parent
OS_XH, OS_CAP = 456, 712


def recipe_scale(stem, hair, weight=WEIGHT):
    """derive.STROKE_KEY for the Italic's recipes: an o's stem (WEIGHT
    added) and top hairline as they are, against what the numbers were
    tuned at (Old Standard's, thinned by TUNED_AX, TUNED_AY): a drawn
    stroke comes at the stem with the weight of the letter it is drawn on
    (weight: CAP_WEIGHT on a capital's tail)."""
    return (stem - WEIGHT + weight) / (stem - WEIGHT - AX + TUNED_AX), hair / (hair - AY + TUNED_AY)
# the weights and cuts the Italic was made with (font lib): a rerun with
# others still keeps the drawn glyphs (they are neither weighted nor
# respaced again) and lists them to be looked at again
MADE_WITH_KEY = "org.myiadidot.italicMadeWith"
SOURCE_KEY = "org.myiadidot.italicSource"
REDRAWN_KEY = "org.myiadidot.redrawn"  # redraw.py's record: date, review, from, source, tol
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


def origin(g):
    """Where a glyph's outline came from: its source mark; for a letter
    redrawn onto new nodes (redraw.py: marked drawn, its shape and weight
    kept) the mark it had before."""
    src = g.lib.get(SOURCE_KEY)
    if src == "drawn":
        return g.lib.get(REDRAWN_KEY, {}).get("source") or src
    return src




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
# where ɗ leaves the italic d for ɓ's top: above the bowl, below where ɓ's
# stem begins to bend into its hook (upright frame)
DHOOK_CUT = 1000
def sc_late(source, band):
    """Made in the late pass, after the small caps are drafted: a recipe
    built from a small cap or measured against one (o.sc, h.sc in its
    band), so against the Italic's own, not the Regular's sloped. Listed
    by hand until 2026-11-12, ɛ.sc ɩ.sc ꞷ.sc ɤ.sc ә.sc were left out and
    measured a stand-in o.sc (1230 wide, hairline 45 for the draft's 59);
    it showed when o.sc was kept and stood there early."""
    return source.endswith(".sc") or (isinstance(band, tuple) and any(
        isinstance(n, str) and n.endswith(".sc") for n in band))








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


# т's bar against п's (ū's macron): Charis 1.85, Libertinus 1.84
SRB_TE_BAR = 1.84


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
    if name not in font or origin(font[name]) not in ("Old Standard", "derived", "small cap draft"):
        return 0
    return case_weight(font, font[name])


def halved(rec):
    """rec with each curve split at its middle"""
    from fontTools.misc.bezierTools import splitCubicAtT

    out, cur = RecordingPen(), None
    for op, args in rec.value:
        if op == "curveTo":
            for seg in splitCubicAtT(cur, *args, 0.5):
                out.curveTo(*seg[1:])
        else:
            getattr(out, op)(*args)
        cur = args[-1] if args else cur
    return out


def reweight(up, name, w, fine=False):
    """up[name] (decomposed) with its thick strokes w heavier (weight_thick).
    fine: its curves halved first. weight_thick moves nodes, a round
    between them follows: o redrawn onto its extremes lost 8.2 of its 10
    at mid height where Old Standard's nodes lost 9.6 (stem 164.8 against
    162.9, Ꞷ 1 % narrower for it); halved, 163.3 and 162.6."""
    g = up[name]
    rec = DecomposingRecordingPen(up)
    g.draw(rec)
    out = weight_thick(halved(rec) if fine else rec, w)
    g.clearContours()
    g.clearComponents()
    out.draw(g.getPen())


def enlarged(font, up, ch, op, source, band, name):
    """A letter scaled to another case (ɩ -> Ɩ with o -> O, Ʊ -> ʊ.sc):
    derive.enlarge brings all its strokes to the new size's weight by one
    amount, which the added weight (WEIGHT on the thick strokes, none on
    the thin) does not scale with: Ɩ's tail thinned to a sliver. So made of
    the glyphs without it, the letter then given the weight of its case."""

    refs = {source, *(n for n in band if isinstance(n, str))}
    if derive.ENLARGE_LIKE.get(ch):  # the letter it is scaled like (ʛ as ɢ from g.sc)
        refs.add(derive.ENLARGE_LIKE[ch])
    saved = {n: copy.deepcopy(up[n]) for n in refs if weight_of(font, n) and n in up}
    try:
        for n in saved:
            # a redrawn letter read for its measures only: see reweight
            reweight(up, n, -weight_of(font, n), fine=n != source and REDRAWN_KEY in font[n].lib)
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
        if sc_late(source, band) != late:
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
            derive.fair_joins(up[name], *ITALIC_JOINS[ch], min_turn=0 if ch in ITALIC_JOINS_THROUGH else 1)
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


def smallcaps_stage(font, later=(), redraft=False, keep=False):
    """Small caps still sloped roman: FontForge's drafts of the Italic's
    capitals (stored: fontforge_inputs.drafts), imported (with their
    anchors) in the upright frame; not those derive_stage makes from them
    afterwards (later). redraft: all drafted anew."""
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
    drafts = fontforge_drafts(up, height, f"{stem:.0f}/{uc:.0f}", redraft=redraft, keep=keep)
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




def swapped_sidebearings(font):
    """Side bearings for the derived letters that are their base turned or
    mirrored (as wide in ink, upright): the base's, swapped, measured
    upright, as the Regular's are. A letter made before its base was
    respaced (Ʊ, turned from Ω before the Greek cut widened it) keeps
    the old spacing otherwise. Returns {glyph: (left, right)} deltas for
    sidebearings()."""

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




def roman_anchor(roman, a, width_it):
    """x of the Regular's anchor a on an italic glyph width_it wide: in
    proportion to the widths, slanted about half the x-height."""
    return a.x * width_it / (roman.width or 1) + (a.y - XH / 2) * SLANT


def kept_names(previous, font):
    """the glyphs of the last run a rerun keeps as saved: those marked drawn
    (drawn.py) that font still makes, and the Italic's own small caps"""
    return [g.name for g in (previous or []) if is_drawn(g)
            and (g.name in font or g.name.endswith(".sc"))]


def missing_anchors(font, regular, marks):
    """The anchors the Regular's glyph has and the Italic's lacks (a turned
    letter takes none from its source, a drafted small cap only its
    capital's), placed as roman_anchor places them; hand-drawn glyphs stay
    as drawn. Returns the names given anchors."""
    given = []
    for g in font:
        if g.name in marks or g.name not in regular or not g.width or is_drawn(g):
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




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("regular", nargs="?", default=str(ROOT / "sources/MyiaDidot-Regular.ufo"))
    ap.add_argument("italic", nargs="?", default=str(ROOT / "sources/MyiaDidot-Italic.ufo"))
    ap.add_argument("--redraft", action="store_true", help="draft every small cap anew with FontForge")
    ap.add_argument("--keep-drafts", action="store_true",
                    help="keep the stored small-cap drafts though their capitals changed "
                         "(after capitals were redrawn onto new nodes: fontforge_inputs.drafts)")
    ap.add_argument("--out", metavar="UFO", help="the whole run into a copy of ITALIC, which stays as it is "
                    "(scratch_out.py; smallcaps.py runs on the copy)")
    args = ap.parse_args()
    if args.out:
        from scratch_out import prepare

        args.italic = str(prepare(args.italic, args.out))
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
            if g.name in ITALIC_MARK_SCALE:
                k = ITALIC_MARK_SCALE[g.name]
                (x0, y0), (x1, y1) = ((min(p.x for c in g.contours for p in c.points), min(p.y for c in g.contours for p in c.points)),
                                      (max(p.x for c in g.contours for p in c.points), max(p.y for c in g.contours for p in c.points)))
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                # scaled about its centre, then sloped
                t = (k, 0, SLANT * k, k, cx * (1 - k) + SLANT * cy * (1 - k), cy * (1 - k))
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
    # what was drawn in the Italic stays (drawn.py), whatever the settings
    # (and the Italic's own: ʀ.sc, drafted from its Ʀ, is not in the Regular)
    kept = kept_names(previous, font)
    if previous is not None and kept and previous.lib.get(MADE_WITH_KEY) != MADE_WITH:
        print(f"{args.italic}: kept though the weights or cuts changed, look again: {' '.join(kept)}")
    for name in kept:
        font.layers.defaultLayer.insertGlyph(copy.deepcopy(previous[name]), name, overwrite=True)
    # a kept glyph is saved as spaced (the cut taken), everything else here
    # stands uncut until respace below: the kept ones too until then, so
    # that what is built on one is cut once with the rest (ɲ ʂ ɠ ɸ came 2
    # cuts narrow when n s g o were first marked drawn, 2026-11-10). They
    # are put back as saved after it.
    kept_cut = classifier(font, ITALIC_CUT, ITALIC_CUT_GREEK)
    respace(font, lambda n: -kept_cut(n) if n in kept else 0, kept)
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
    small_caps = smallcaps_stage(font, later, redraft=args.redraft, keep=args.keep_drafts)
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
    still =sorted(g.name for g in font if g.lib.get(SOURCE_KEY) == "sloped roman"
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

    # a kept y has its dot's anchor as saved: placed here on it uncut, it
    # came a unit off (912 for the saved 897 + 16), ỵ was built on that and
    # y then put back as saved (the redrawn y, 2026-11-11)
    if "y" not in kept:
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
    cleaned = fix(font, [g.name for g in font if not is_drawn(g)])
    # the letters spaced tighter (scripts/respace.py), not those kept from the
    # last run, which were (what comes from the Regular has its cut too)
    letter_cut = classifier(font, ITALIC_CUT, ITALIC_CUT_GREEK)
    # the kept ones stand uncut (above) and are put back as saved below:
    # counted as cut here, so that their composites' parts move with them
    respace(font, letter_cut, [g.name for g in font if g.name not in kept])
    space_figures(font)  # the old-style figures spaced by their shapes (their .tf, the .pf rebuilt)

    def restore_kept():
        # as saved; an alias still as wide as its letter
        for name in kept:
            g = copy.deepcopy(previous[name])
            if (len(g.components) == 1 and not g.contours
                    and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
                g.width = font[g.components[0].baseGlyph].width
            font.layers.defaultLayer.insertGlyph(g, name, overwrite=True)

    # the kept ones as saved, cut: ɘ takes its sides from e's below
    restore_kept()
    sidebearings(font, swapped_sidebearings(font))
    sidebearings(font, ITALIC_SIDEBEARINGS)
    # and again (the side bearings above, carrying composites along, moved
    # them again each run: г.loclSRB -80 a run)
    restore_kept()
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
    # the Latin pairs from the white the finished italic shapes leave
    # (italic_kerning.py, docs/claude/spacing.md), then the reviewed exceptions
    from italic_kerning import apply as italic_kerning

    # against the Regular as saved (the one above has respace undone)
    kerned = italic_kerning(ufoLib2.Font.open(args.regular), font)
    font.kerning.update(ITALIC_KERNING)
    for pair in ITALIC_UNKERNED:
        font.kerning.pop(pair, None)
    kern_clear.clear(font)  # pairs whose inks would meet, loosened (on the final outlines)
    write(font, Path(args.italic), plain=ROUND_PLAIN)
    # the accented small caps and the smcp/c2sc features, from the new drafts
    subprocess.run([sys.executable, "-I", str(ROOT / "scripts/smallcaps.py"), args.italic], check=True)
    print(f"{args.italic}: {taken} from Old Standard, {len(kept)} kept as drawn, "
          f"{upright_signs} signs upright, {len(derived)} derived, {len(figures)} figures, "
          f"{len(small_caps)} small caps drafted, {len(LIGATURE_NAMES)} italic ligatures built, {rebuilt} composites rebuilt, "
          f"{len(cleaned)} cleaned, {kerned[0]} Latin pairs computed ({kerned[1]} set plain, at 0), "
          f"{len(anchored)} given the Regular's anchors they lacked; "
          f"{len(still)} still sloped roman (of {kept_roman}); Greek capitals' marks nearer: "
          + " ".join(f"{n} {d}" for n, d in greek_shift.items()))
    for line in failed:
        print("  recipe failed:", line)
    print("  still sloped roman:", " ".join(still))


if __name__ == "__main__":
    main()
