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
- a gap closed to a slit (ʊ's between its flags: Ʊ made small and brought
  to the lowercase's weight, 2026-11-09): GAPS, cut open again to a width,
  a channel upright in the unslanted letter.
- a serif's bracket collapsed into a short curve or two bending back (ψ.sc's
  feet and top, я.sc's top): FILLETS, redrawn as one curve tangent to the
  serif's flat and the stroke (sc_feet.fillets, as the Bold Italic's x.sc),
  reaching at least as far as the Italic's brackets there.

Each entry names a node by its position in the finished glyph; an entry
that finds none fails (the generator moved it: look again). Glyphs kept as
drawn (drawn.py) are put back after finishing and are fixed in place
instead; ℵ's join is put in line in aleph.py, whose repairs the tests rerun.
The Italic has a few of its own (ITALIC_JOINS), put in line the same way;
the Bold Italic made from it takes them with its letters.
"""

import math

import sc_feet
from derive import path_op, rect_path, to_path
from finalization import absent
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from italic_geometry import SLANT, XH

CRUMB = 12

# glyph: nodes (x, y) whose handles are put in line
JOINS = {
    "uni028B": [(697, 889), (888, 168)],  # (the second: the one-way foot, below)
    "m": [(770, 598)],
    "uni0442": [(770, 598)],
    "uni026F": [(900, 286), (1354, 194)],  # (the second: the one-way foot, below)
    "uni0496": [(1016, -314), (926, -237), (1774, 285), (1447, 268)],
    "u1D510": [(1838, 92)],
    "uni01B4": [(1181, 759), (810, 752)],
    "ordfeminine": [(649, 865)],
    "uni044F.sc": [(465, 195)],
    # ⱦ: the slash's lower edge into the stem's inner curve, a 4-unit crumb
    # there (2026-11-09, its slash drawn at this weight)
    # was (278, 167): the rebuilt ⱦ and ƭ (2026-11-20) have it at (294, 164)
    "uni2C66": [(294, 164)], "uni01AD": [(294, 164)],
    # the entry strokes and feet kept turning one way (stroke_bold.one_way,
    # 2026-11-09): fair_arcs' split or the cleaning leaves a short handle
    # or a crumb at their node, rounded off its course (11-26 degrees;
    # ʋ ɯ's above);
    # ı's entry, here before, has no corner left
    "n": [(316, 690)],
    "uni043F": [(316, 690)],
    "uni1D6F": [(316, 690)],
    "uni0289": [(888, 168)],
    "uni1D43": [(422, 1046)],
    "uni1DA4": [(387, 615)],
}
# the Italic's, the same way (its node made smooth too): ɱ's hook, its
# inner edge running into m's leg, a zero-length line stacked on the node
# there since ȷ was redrawn (a spike of two nodes on one point, 0.3 degrees
# between the curves; 2026-11-11)
ITALIC_JOINS = {
    "uni0271": [(1137, 45)],  # m 68 wider (phase 6 step B, 2026-11-17)
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
    # 2026-11-09, the second list: Ѫ's inner right leg's feet, ꞵ.sc's stem
    # (under its top serif the bracket turned the wrong way, a notch)
    "uni046A": [(1835, 121, 35), (1570, 110, 0)],
    "uniA7B5.sc": [(390, 101, 35), (316, 945, 30)],
}


# glyph: (centre x and bottom y of the channel in the unslanted letter, width)
GAPS = {
    # ʊ: 19 units between the flags, the Italic's 97 (90 chosen 2026-11-09
    # from 60, 90); the bowl's top at 625
    "uni028A": (554, 625, 90),
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
        near = sorted((round(math.dist((p.x, p.y), (x, y))), round(p.x), round(p.y)) for c in glyph.contours
                      for p in c.points if p.type and math.dist((p.x, p.y), (x, y)) < 6 * r)[:4]
        raise ValueError(f"smooth_joins: {glyph.name} has no node near {x},{y} (nearest on-curve nodes: distance, x, y: {near})")
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


def gap(glyph, cx, y0, width):
    """a channel width wide, upright in the unslanted letter, cut from y0 up"""
    channel = rect_path(cx - width / 2, y0, cx + width / 2, 4000)
    rec = RecordingPen()
    channel.draw(TransformPen(rec, (1, 0, SLANT, 1, -SLANT * XH / 2, 0)))
    out = path_op(to_path(None, glyph), to_path(None, rec=rec), "DIFFERENCE")
    glyph.clearContours()
    pen = glyph.getPen()
    rounded = RecordingPen()
    out.draw(rounded)
    for op, pts in rounded.value:
        getattr(pen, op)(*[(round(x), round(y)) for x, y in pts])


def finish(font):
    if font.info.styleName == "Italic":
        for name, spots in ITALIC_JOINS.items():
            if absent(font, name):
                continue
            for x, y in spots:
                align(font[name], x, y)
                node = min((p for c in font[name].contours for p in c.points if p.type),
                           key=lambda p: math.dist((p.x, p.y), (x, y)))
                node.smooth = True
        return
    for name, (cx, y0, width) in GAPS.items():
        if absent(font, name):
            continue
        gap(font[name], cx, y0, width)
    for name, spots in FILLETS.items():
        if absent(font, name):
            continue
        for x, y, reach in spots:
            fillet(font[name], x, y, reach)
    for name, spots in JOINS.items():
        if absent(font, name):
            continue
        for x, y in spots:
            align(font[name], x, y)
    for name in FF_HOOKS:
        if absent(font, name):
            continue
        while hook_ball(font[name]):
            pass


# the ff-ligatures' lower hooks (2026-11-20, the designer: "a strange lower
# hook" in ffi): the stroker leaves the ball's leftmost node out and joins
# its two curves in a corner a bend of this many degrees or more, the curve
# after it running on to the left past the node (a lobe)
FF_HOOKS = ("ff", "ffi", "ffl", "f_f_j")
BALL_BEND = 30


def hook_ball(glyph):
    """Mend one such corner (below the baseline, between two curves): the
    two curves through it are fitted again with a node at the ball's
    leftmost point, upright there. Returns whether one was mended."""
    import numpy as np
    from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT
    from redraw import fit_cubic
    from ufoLib2.objects import Point

    for c in glyph.contours:
        P = c.points
        n = len(P)
        for i, p in enumerate(P):
            if not (p.type == "curve" and not p.smooth and p.y < -20):
                continue
            a, b = P[i - 1], P[(i + 1) % n]
            if a.type or b.type:
                continue
            u = (p.x - a.x, p.y - a.y)
            v = (b.x - p.x, b.y - p.y)
            bend = abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))
            if bend < BALL_BEND:
                continue
            if not 3 <= i <= n - 4 or P[i - 3].type != "curve" or P[i + 3].type != "curve":
                raise ValueError(f"hook_ball: {glyph.name} {p.x},{p.y}: the corner's curves are not whole in the contour")
            A, C, D = P[i - 3], p, P[i + 3]
            s1 = [(A.x, A.y), (P[i - 2].x, P[i - 2].y), (a.x, a.y), (C.x, C.y)]
            s2 = [(C.x, C.y), (b.x, b.y), (P[i + 2].x, P[i + 2].y), (D.x, D.y)]
            xs = [q[0] for q in s2]
            ts = [t for t in solveQuadratic(3 * (-xs[0] + 3 * xs[1] - 3 * xs[2] + xs[3]),
                                            6 * (xs[0] - 2 * xs[1] + xs[2]), 3 * (xs[1] - xs[0]))
                  if 0.02 < t < 0.98]
            if not ts:
                raise ValueError(f"hook_ball: {glyph.name} {p.x},{p.y}: no leftmost point after the corner")
            t = ts[0]
            first, second = splitCubicAtT(*s2, t)
            E = np.array(first[3], float)

            def sample(seg, m=24):
                s = np.linspace(0, 1, m)[:, None]
                q = np.array(seg, float)
                return ((1 - s) ** 3) * q[0] + 3 * ((1 - s) ** 2) * s * q[1] + 3 * (1 - s) * s * s * q[2] + s ** 3 * q[3]

            up = np.array([0.0, 1.0 if second[1][1] >= second[0][1] else -1.0])
            tA = np.array([s1[1][0] - s1[0][0], s1[1][1] - s1[0][1]], float)
            tA /= np.linalg.norm(tA)
            tD = np.array([s2[3][0] - s2[2][0], s2[3][1] - s2[2][1]], float)
            tD /= np.linalg.norm(tD)
            lower = fit_cubic(np.vstack([sample(s1), sample(first)[1:]]), np.array(s1[0], float), tA, E, up)
            upper = fit_cubic(sample(second), E, up, np.array(s2[3], float), tD)
            new = [Point(round(q[0]), round(q[1]), kind, smooth=kind == "curve")
                   for q, kind in ((lower[1], None), (lower[2], None), (E, "curve"), (upper[1], None), (upper[2], None))]
            P[i - 2:i + 3] = new
            return True
    return False
