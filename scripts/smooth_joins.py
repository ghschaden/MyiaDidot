"""The Bold Italic's joins smoothed where the Italic's are smooth, named one
by one (finalization, last).

Emboldened by its strokes, the Bold Italic keeps some joins the Italic has
smooth as slight corners, 11-33 degrees (scripts/quality/corners.py; the
designer's list from build/corners/bolditalic-letters.pdf, 2026-11-09):

- a straight edge running into a curve whose first handle stands off the
  line's direction (m's middle stem into its second arch), or two curves
  whose handles do not line up: JOINS. Crumbs at the node (segments under
  CRUMB units: ƴ had a zero-length curve and line stacked there) are dropped,
  the next segment starting from the node before; then the curve's handle
  takes the line's direction (between two curves, both the mean of theirs),
  at least a third of its curve's chord long (1-2 unit handles rounded back
  where they were).
- a serif's bracket collapsed into a short curve or two bending back (ψ.sc's
  feet and top, я.sc's top): FILLETS, redrawn as one curve tangent to the
  serif's flat and the stroke (sc_feet.fillets, as the Bold Italic's x.sc),
  reaching at least as far as the Italic's brackets there.

Each entry names a node by its position in the finished glyph; an entry
that finds none fails (the generator moved it: look again). Glyphs kept as
drawn (drawn.py) are put back after finishing and are fixed in place
instead; ℵ's join is put in line in aleph.py, whose repairs the tests rerun.
"""

import math

import sc_feet

CRUMB = 12

# glyph: nodes (x, y) whose handles are put in line
JOINS = {
    "dotlessi": [(343, 688)],
    "uni028B": [(697, 889)],
    "m": [(770, 598)],
    "uni0442": [(770, 598)],
    "uni026F": [(900, 286)],
    "uni0496": [(1016, -314), (926, -237), (1776, 307), (1447, 268)],
    "u1D510": [(1838, 92)],
    "uni01B4": [(1181, 759), (810, 752)],
    "ordfeminine": [(649, 865)],
    "uni044F.sc": [(465, 195)],
}
# glyph: (x, y, reach) of the brackets redrawn as fillets
FILLETS = {
    "psi.sc": [(973, 928, 30), (745, 90, 35)],
    "uni044F.sc": [(1199, 927, 30)],
    "uni0274": [(134, 138, 0)],
    # eng.sc: the stem into its foot serif by a short upright curve and the
    # bracket, the handles at odds (aligned, the join bent back)
    "eng.sc": [(263, 170, 0)],
    "eth.sc": [(88, 101, 35), (613, 928, 30)],
}


def _ons(contour):
    return [i for i, p in enumerate(contour.points) if p.type]


def crumbs(glyph, x, y, r=CRUMB):
    """segments under r units, ending within r of (x, y), dropped"""
    for c in glyph.contours:
        while len(_ons(c)) > 4:
            P, n, hit = c.points, len(c.points), None
            ons = _ons(c)
            for k, i in enumerate(ons):
                j = ons[k - 1]
                seg = [P[(j + m) % n] for m in range(1, (i - j) % n + 1)]
                if (all(math.dist((q.x, q.y), (P[j].x, P[j].y)) < r for q in seg)
                        and math.dist((P[i].x, P[i].y), (x, y)) < r):
                    hit = [(j + m) % n for m in range(1, (i - j) % n + 1)]
                    break
            if not hit:
                break
            for idx in sorted(hit, reverse=True):
                del c.points[idx]


def _far(P, i, step):
    """the on-curve at the other end of the segment leaving P[i] (step 1 or -1)"""
    k = (i + step) % len(P)
    while P[k].type is None:
        k = (k + step) % len(P)
    return P[k]


def align(glyph, x, y, r=CRUMB):
    """the node nearest (x, y), crumbs dropped, its handles put in line"""
    crumbs(glyph, x, y, r)
    best = None
    for c in glyph.contours:
        for i, p in enumerate(c.points):
            d = math.dist((p.x, p.y), (x, y))
            if p.type and d < r and (best is None or d < best[0]):
                best = (d, c, i)
    if best is None:
        raise ValueError(f"smooth_joins: {glyph.name} has no node near {x},{y}")
    _, c, i = best
    P = c.points
    p, a, b = P[i], P[i - 1], P[(i + 1) % len(P)]
    if a.type and b.type:
        raise ValueError(f"smooth_joins: {glyph.name} {x},{y} joins two lines")

    def unit(dx, dy):
        n = math.hypot(dx, dy)
        return (dx / n, dy / n) if n else None

    ua, ub = unit(p.x - a.x, p.y - a.y), unit(b.x - p.x, b.y - p.y)
    if a.type:
        u = ua
    elif b.type:
        u = ub
    else:
        ua, ub = ua or ub, ub or ua
        u = unit(ua[0] + ub[0], ua[1] + ub[1])
    for h, step in ((a, -1), (b, 1)):
        if h.type:
            continue
        far = _far(P, i, step)
        length = max(math.dist((h.x, h.y), (p.x, p.y)), math.dist((far.x, far.y), (p.x, p.y)) / 3)
        h.x, h.y = round(p.x + step * u[0] * length), round(p.y + step * u[1] * length)


def fillet(glyph, x, y, reach=0, near=60):
    """sc_feet's fillets, on the brackets near (x, y) only, a single curve
    too, reaching at least reach along serif and stroke"""
    sc_feet.fillets(glyph, near=(x, y, near), reach=reach)


def finish(font):
    for name, spots in FILLETS.items():
        for x, y, reach in spots:
            fillet(font[name], x, y, reach)
    for name, spots in JOINS.items():
        for x, y in spots:
            align(font[name], x, y)
