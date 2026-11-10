"""A straight stem into its serif: found where it steps in, and mended.

The rule (the designer, 2026-11-10; docs/claude/quality.md): a straight
stem is one thickness from top to bottom and never steps in where it
meets its serif; a bracket may only widen it. Where a letter is brought
to weight by moving its stem's edge (derive.embolden, enlarge,
make_bold.small_cap_stems, the strokes) the bracket's nodes stay behind:
the edge then stands outside the bracket, and the outline goes into the
ink for a few units before it runs out along the serif (the Bold Italic's
small-cap D at the x-height, uni1D05: 22 units at both feet).

    retreats(glyph)  the joins where that happens
    mend(glyph)      each of them redrawn as one fillet (sc_feet.fillets):
                     the stem's edge run on straight to the serif's flat,
                     the bracket one curve tangent to both, outside the edge

A join is a run of curves between a serif's flat (a level line) and a
stem's edge (a steep line, STEM units long or more). It retreats when a
point of the run lies more than MIN units on the ink's side of the edge
run on. The measure is the furthest such point.
"""

import math

import sc_feet

STEM = 200   # units: a steep line this long is a stem's edge
MIN = 2.0    # units into the ink before a join counts as a retreat
RUN = 4      # curves at most in a bracket
SPAN = 160   # units: a bracket's ends no further apart


def _area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _segments(contour):
    """[(kind, [points])] of a closed contour: each segment's points from
    its start to its end, 2 for a line, 4 for a curve; None if it has
    another kind of segment"""
    P = [(p.x, p.y, p.type) for p in contour.points]
    ons = [i for i, p in enumerate(P) if p[2]]
    if len(ons) < 3:
        return None
    segs = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        between = [P[q % len(P)][:2] for q in range(i + 1, i + 1 + (j - i - 1) % len(P))]
        kind = P[j][2]
        if (kind == "line" and between) or (kind == "curve" and len(between) != 2) or kind not in ("line", "curve"):
            return None
        segs.append((kind, [P[i][:2], *between, P[j][:2]]))
    return segs


def retreats(glyph):
    """[(x, y, units)]: the stem's end at each join of glyph where the
    outline steps into the ink between a stem's edge and its serif's flat,
    and how far"""
    contours = [s for s in (_segments(c) for c in glyph.contours) if s]
    if not contours:
        return []
    outer = max(contours, key=lambda s: abs(_area([seg[1][0] for seg in s])))
    sign = 1 if _area([seg[1][0] for seg in outer]) > 0 else -1  # counter-clockwise outside: the ink on the left
    out = []
    for segs in contours:
        n = len(segs)
        for i, (kind, pts) in enumerate(segs):
            if kind != "line":
                continue
            (ax, ay), (bx, by) = pts
            length = math.hypot(bx - ax, by - ay)
            if length < STEM or abs(by - ay) < 2 * abs(bx - ax):
                continue
            nx, ny = -(by - ay) / length * sign, (bx - ax) / length * sign  # towards the ink
            for step, end in ((1, (bx, by)), (-1, (ax, ay))):
                # the curves after (before) the edge, up to a level line
                run, k = [], i + step
                while len(run) <= RUN and segs[k % n][0] == "curve":
                    run.append(segs[k % n][1])
                    k += step
                flat = segs[k % n]
                if not run or len(run) > RUN or flat[0] != "line" or abs(flat[1][0][1] - flat[1][1][1]) > 1:
                    continue
                far = run[-1][-1] if step == 1 else run[-1][0]
                if math.dist(end, far) > SPAN:
                    continue
                # the serif runs out from the stem: its far end outside the edge
                tip = flat[1][1] if step == 1 else flat[1][0]
                if (tip[0] - end[0]) * nx + (tip[1] - end[1]) * ny > -MIN:
                    continue
                worst = max(((q[0] - end[0]) * nx + (q[1] - end[1]) * ny
                             for c in run for q in (_bezier(*c, t / 8) for t in range(9))), default=0.0)
                if worst > MIN:
                    out.append((round(end[0]), round(end[1]), round(worst, 1)))
    return out


def mend(glyph, reach=0):
    """glyph (in place) with every retreating join a fillet; returns the
    joins mended [(x, y, units)]. A join the fillet does not take (its
    corner not past the stem's end) stays and is found again."""
    done = []
    for _ in range(12):
        found = [f for f in retreats(glyph) if f not in done]
        if not found:
            break
        x, y, units = found[0]
        sc_feet.fillets(glyph, near=(x, y, 6), reach=reach)
        done.append((x, y, units))
    left = {(x, y) for x, y, _ in retreats(glyph)}
    return [f for f in done if (f[0], f[1]) not in left]


def finish(font):
    """finalization, last: every stem of the generated style into its
    serif without a step. Glyphs drawn by hand are left (the Italic's
    marked drawn; the bold styles' drawn.py puts its own back after the
    passes): those are mended where they are drawn."""
    mended = {}
    for glyph in font:
        if (not glyph.contours or glyph.lib.get("org.myiadidot.italicSource") == "drawn"
                or "org.myiadidot.drawn" in glyph.lib):
            continue
        done = mend(glyph)
        if done:
            mended[glyph.name] = done
    return mended
