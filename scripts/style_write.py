"""Finishing and saving a generated style: make_italic and make_bold both
write through here (T5b, 2026-11-27: moved out of make_bold, so that
make_italic need not import make_bold and make_bold may import
make_italic at the top). make_bold re-exports the names read through it
(WHOLE_KEY, mark_like, redraw, round_smoothly, separate_breve_grave_stacks,
write), so make_bold.NAME goes on working for them.

write(font, path): finalize (rounded, cleaned, the finishing passes of
finalization.py, stacks and horns refitted), the acceptances carried
over, the drawn glyphs put back, wound as the Regular, saved.
"""

import math
import unicodedata
from pathlib import Path

import ufoLib2
from built_from import KEY as BUILT_KEY
from composites import STACK_GAP_LC
from glyph_lint import fix

# lib: derived letters left emboldened whole, with why (follow_bases);
# tests/test_emboldened.py holds them to a list that only shrinks
WHOLE_KEY = "org.myiadidot.emboldenedWhole"


def mark_like(g):
    """Accents and combining marks: zero width, the spacing modifier
    symbols (´ ˆ ΄ ᾿ ..., whatever their width) and the unencoded 880-wide
    spacing accents (Acute ...), not a small cap that width (the Italic's
    ґ.sc, 880 wide, emboldened as an accent)."""
    if g.width == 0:
        return True
    if g.unicode is not None:
        return unicodedata.category(chr(g.unicode)) in ("Sk", "Mn")
    return g.width == 880 and not g.name.endswith(".sc")


def redraw(g, glyph):
    """Replace g's contours with those of glyph (an emboldened ufoLib2 Glyph);
    quadratic segments (pathops' results may hold some) made cubic."""
    g.clearContours()
    if any(p.type == "qcurve" for c in glyph.contours for p in c.points):
        from derive import CubicPen

        for c in glyph.contours:
            c.draw(CubicPen(g.getPen()))
        return
    pen = g.getPointPen()
    for c in glyph.contours:
        c.drawPoints(pen)


def refit_horns(font):
    """The letters with a horn composed again on the outlines as saved:
    composites.py fits the horn to its base and keeps the marks above
    clear of it by their ink, which rounding and cleaning still move."""
    from composites import Builder

    builder = Builder(font)
    for g in [g for g in font if g.unicode is not None and g.components]:
        if (len(unicodedata.normalize("NFD", chr(g.unicode))) < 2
                or not any(c.baseGlyph in ("horn", "Horn") for c in g.components)):
            continue
        r = builder.recipe(g.unicode)
        if [(c.glyph, c.dx, c.dy) for c in r.components] != [(c.baseGlyph, *c.transformation[4:]) for c in g.components]:
            r.name, lib = g.name, dict(g.lib)
            del font[g.name]
            builder.write(r)
            font[r.name].lib.update(lib)


def round_smoothly(P):
    """P's points rounded to whole units, a join that ran on (nearly)
    smoothly, under 3 degrees, not broken further: where rounding leaves
    it turning by more than a degree and more than it did, its handles
    moved a unit each, together, to bring it more in line (a 15-unit
    handle rounded turns up to 4 degrees, one moved alone in steps of 3-4),
    a level or upright one (at an extreme) kept so. Handles under 10 units are left as rounded: theirs
    is no angle worth the name (checks.py)."""
    def turn(a, h, b):
        t = math.atan2(h[1] - a[1], h[0] - a[0]) - math.atan2(b[1] - h[1], b[0] - h[0])
        return abs(math.degrees((t + math.pi) % (2 * math.pi) - math.pi))

    def overshoot(k, q):
        """how far the curve through handle k, put at q, bulges past its ends"""
        h = [(P[(k + d) % n].x, P[(k + d) % n].y) for d in (-2, -1, 0, 1, 2)]
        seg = h[1:5] if P[(k - 1) % n].type else h[0:4]
        seg = [q if pt == (P[k].x, P[k].y) else pt for pt in seg]
        most = 0.0
        for step in range(1, 32):
            t = step / 32
            u = 1 - t
            pt = [u ** 3 * seg[0][c] + 3 * u * u * t * seg[1][c] + 3 * u * t * t * seg[2][c] + t ** 3 * seg[3][c]
                  for c in (0, 1)]
            for c in (0, 1):
                lo, hi = sorted((seg[0][c], seg[3][c]))
                most = max(most, lo - pt[c], pt[c] - hi)
        return most

    n = len(P)
    raw = [(p.x, p.y) for p in P]
    for p in P:
        p.x, p.y = round(p.x), round(p.y)
    if n < 3:
        return
    for i, p in enumerate(P):
        if not p.type:
            continue
        a, b = (i - 1) % n, (i + 1) % n
        if min(math.dist(raw[a], raw[i]), math.dist(raw[i], raw[b])) < 1 or turn(raw[a], raw[i], raw[b]) > 3:
            continue
        node = (p.x, p.y)
        ends = [(P[a].x, P[a].y), (P[b].x, P[b].y)]
        least = turn(ends[0], node, ends[1])
        # only what the rounding broke (an outline in whole units, a drawn
        # glyph kept, stays as it is)
        if least <= max(1, turn(raw[a], raw[i], raw[b]) + 0.25) or min(math.dist(e, node) for e in ends) < 10:
            continue
        # each handle's places a unit around it (an on-curve neighbour, a
        # line's end, stays), tried together: one alone, 15-20 units long,
        # turns in steps of 3-4 degrees
        options = []
        for k in (a, b):
            places = [(P[k].x, P[k].y)]
            if not P[k].type:
                bulge = overshoot(k, (P[k].x, P[k].y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (P[k].x + dx, P[k].y + dy)
                        # an extreme's handle stays level or upright
                        if (dx or dy) and math.dist(q, node) >= 10 and not (P[k].x == p.x and q[0] != p.x) \
                                and not (P[k].y == p.y and q[1] != p.y) and overshoot(k, q) <= max(bulge, 2):
                            places.append(q)  # (nor bulging further past its ends: an extreme lost)
            options.append(places)
        best = None
        for qa in options[0]:
            for qb in options[1]:
                t = turn(qa, node, qb)
                moved = abs(qa[0] - P[a].x) + abs(qa[1] - P[a].y) + abs(qb[0] - P[b].x) + abs(qb[1] - P[b].y)
                if t < least - 1e-9 or (best and abs(t - least) < 1e-9 and moved < best[2]):
                    best, least = (qa, qb, moved), t
        if best:
            (P[a].x, P[a].y), (P[b].x, P[b].y) = best[0], best[1]


def separate_breve_grave_stacks(font):
    """Keep the inherited grave/breathing pairs clear of the Greek breve.

    These legacy mark ligatures use fixed component offsets rather than
    Builder's stacking anchors. Weighting makes the grave touch the breve.
    Move the complete upper pair, preserving its internal arrangement and
    the stack's attachment anchor, with the usual lowercase mark gap.
    """
    from smallcaps import ink_bounds

    for breathing in ("0313", "0314"):
        if f"brevecmb_uni{breathing}_gravecomb.grek" not in font:  # (--only: what is read)
            continue
        glyph = font[f"brevecmb_uni{breathing}_gravecomb.grek"]
        upper, breve = glyph.components
        upper_bounds = ink_bounds(font, upper.baseGlyph)
        breve_bounds = ink_bounds(font, breve.baseGlyph)
        gap = upper_bounds[1] + upper.transformation.dy - (breve_bounds[3] + breve.transformation.dy)
        if gap < STACK_GAP_LC:
            xx, xy, yx, yy, dx, dy = upper.transformation
            upper.transformation = (xx, xy, yx, yy, dx, dy + math.ceil(STACK_GAP_LC - gap))


def finalize(font, smooth=True, separate_stacks=False, plain=()):
    """Finish a generated style before persistence. Its
    points, anchors and component offsets are rounded to whole units first,
    and what that leaves cleaned (glyph_lint). The Regular's record of what
    its derived glyphs were built from (built_from.py) is left behind: a
    generated style is checked by being generated again.
    smooth: joins the rounding would break kept smooth (round_smoothly).
    plain: glyphs rounded plainly all the same.
    separate_stacks: fit legacy Greek breve/grave stacks after rounding;
    enabled for the bold styles, not for the Italic's shared writer."""
    for g in font:
        g.lib.pop(BUILT_KEY, None)
        for c in g.contours:
            if smooth and g.name not in plain:
                round_smoothly(c.points)
            else:
                for p in c.points:
                    p.x, p.y = round(p.x), round(p.y)
        for a in g.anchors:
            a.x, a.y = round(a.x), round(a.y)
        for c in g.components:
            xx, xy, yx, yy, dx, dy = c.transformation
            c.transformation = (xx, xy, yx, yy, round(dx), round(dy))
    fix(font)  # what rounding left (a unit's step)
    from finalization import finish_glyphs

    finish_glyphs(font)
    if separate_stacks:
        separate_breve_grave_stacks(font)
    refit_horns(font)
    from degenerate import mend_font

    mend_font(font)  # zero segments, lined-up corners the rounding left (degenerate.py)
    # aliases as wide as their glyph after the finishing passes set it
    # (the Bold Italic's ff, made again by italic_ligatures and fitted after,
    # left ff.short at the Italic's width)
    for g in font:
        if (not g.contours and len(g.components) == 1 and g.components[0].baseGlyph in font
                and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            g.width = font[g.components[0].baseGlyph].width


def write(font, path, smooth=True, separate_stacks=False, plain=(), kept=None):
    """font finalized and saved to path, the acceptances of the
    style saved there before carried over (accepted.py), and the glyphs
    kept as drawn (drawn.py: kept, as saved) put back as they were.
    Every glyph is then wound as the Regular is (winding.orient: pathops
    and a mirrored letter wind the other way), the drawn ones too: a
    contour's direction is no part of the drawing."""
    from accepted import acceptances, carry
    from drawn import restore
    from ufo_io import save_font
    from winding import orient

    finalize(font, smooth=smooth, separate_stacks=separate_stacks, plain=plain)
    carry(acceptances(ufoLib2.Font.open(path)) if Path(path).exists() else {}, font)
    restore(kept or {}, font)
    _, left = orient(font)
    if left:
        print("  contour direction undecided (overlapping contours wound both ways):", " ".join(sorted(left)))
    save_font(font, path)
