"""The bold styles' small caps on their lines, their serifs' brackets, the
Bold's k.sc join drawn and the Bold Italic's x.sc brackets as fillets.

The pointed feet overshoot by 18 to 35 units. Heavier they end
flat and broad, and a flat foot that deep hangs under its neighbours (ZWÖLF,
BOXKÄMPFER, the person, 2026-11-01): 6 units, the same for each foot. w's
and v's serifs stood 9 units over the height of their neighbours, and w
looked the larger for it.

A stroke emboldened past its serif leaves the bracket's handle on the serif
behind where the curve starts, and the curve turns back: a wobble at the foot
(ä.sc). That handle goes halfway along the bracket. Only on the top of a foot
serif: on a round's extreme a handle may stand so, and the bowl needs it.
"""

import math

DEPTH = 6
HEIGHT = 1040
SERIF_TOP = range(65, 80)
# a fillet's handles this far towards the corner it rounds
FILLET = 0.55
# a stroke this long (or longer) is the arm or leg a bracket runs into
DIAGONAL = 200
def brackets(glyph):
    for contour in glyph.contours:
        P, n = contour.points, len(contour.points)
        for i, p3 in enumerate(P):
            if p3.type != "curve":
                continue
            p0, h1, h2 = P[(i - 3) % n], P[(i - 2) % n], P[(i - 1) % n]
            if h1.type or h2.type:
                continue
            for flat, inner, near in ((h2, p3, p0), (h1, p0, p3)):
                if (flat.y == inner.y and inner.y in SERIF_TOP and near.y > inner.y
                        and (flat.x - near.x) * (inner.x - near.x) < 0):
                    flat.x = round((near.x + inner.x) / 2)


def k_sc(font):
    """The arm and leg run straight into the stem: their ends bent there."""
    points = font["k.sc"].contours[0].points
    keys = [(p.x, p.y) for p in points]
    if (500, 585) not in keys or (475, 522) not in keys:
        raise ValueError("Bold k.sc changed; review its join")
    for key, to in (((468, 571), (468, 548)), ((468, 519), (468, 531))):
        points[keys.index(key)].x, points[keys.index(key)].y = to
    for key in ((500, 585), (475, 522)):
        del points[[(p.x, p.y) for p in points].index(key)]


def fillets(glyph):
    """Each bracket between a serif's flat and a long straight stroke (the
    arm or leg) as one curve, tangent to both: the stroke run on meets the
    serif's line at a corner; the curve leaves the flat and joins the stroke
    as far from it as the bracket's farther end was, its handles FILLET of
    the way to the corner. By its strokes the Bold Italic's x.sc had two or
    three curves there that bent back: a knee where each arm and leg ran
    into its serif (the person, 2026-11-01 and 2026-11-05; the Italic's are
    one curve)."""
    from ufoLib2.objects.point import Point

    for contour in glyph.contours:
        P = contour.points
        ons = [i for i, p in enumerate(P) if p.type]
        n = len(ons)
        # start after a line segment, so no run of curves wraps around
        start = next((k for k in range(n) if P[ons[k]].type == "line"), None)
        if n < 4 or start is None:
            continue
        order = [ons[(start + j) % n] for j in range(n)]
        seq = [P[i] for i in order]
        # (index in seq, its new position) for the on-curves a fillet moves,
        # and the runs of curves it replaces: {first index: (h1, h2, end)}
        moved, runs = {}, {}
        j = 0
        while j < n:
            if seq[j].type != "curve":
                j += 1
                continue
            m = j
            while m < n and seq[m].type == "curve":
                m += 1
            if m - j >= 2 and seq[j - 1].type == "line" and seq[m % n].type == "line":
                got = _fillet(seq[j - 2], seq[j - 1], seq[m - 1], seq[m % n])
                if got:
                    t0, h1, h2, t3 = got
                    moved[(j - 1) % n], moved[m - 1] = t0, t3
                    runs[j] = (h1, h2, m)
            j = m
        if not runs:
            continue
        new, j = [], 0
        while j < n:
            if j in runs:
                h1, h2, m = runs[j]
                new += [Point(*h1), Point(*h2), Point(*moved[m - 1], type="curve")]
                j = m
                continue
            pts = _segment(P, order[j])
            if j in moved:
                pts[-1] = Point(*moved[j], type=pts[-1].type)
            new += pts
            j += 1
        contour.points[:] = new
    # the fillets' turns in x (an acute bracket's lies past both its ends)
    # given points, as the generators split extremes
    import derive
    from fontTools.pens.recordingPen import RecordingPen
    from italic_geometry import EXTREME_PAST

    rec = RecordingPen()
    glyph.draw(rec)
    glyph.clearContours()
    derive.with_extremes(rec, glyph.getPen(), past=EXTREME_PAST)


def _fillet(a, p0, p3, b):
    """For a bracket from p0 to p3 between the lines a-p0 and p3-b, one a
    serif's flat and the other a stroke DIAGONAL long or more: (new p0, h1,
    h2, new p3), rounded, or None"""
    if a.y == p0.y and b.y != p3.y and math.dist((b.x, b.y), (p3.x, p3.y)) >= DIAGONAL:
        flat_far, flat_y, stroke_end, stroke_far, flat_first = a, p0.y, p3, b, True
    elif b.y == p3.y and a.y != p0.y and math.dist((a.x, a.y), (p0.x, p0.y)) >= DIAGONAL:
        flat_far, flat_y, stroke_end, stroke_far, flat_first = b, p3.y, p0, a, False
    else:
        return None
    flat_end = p0 if flat_first else p3
    t = (flat_y - stroke_end.y) / (stroke_far.y - stroke_end.y)
    cx = stroke_end.x + t * (stroke_far.x - stroke_end.x)
    if t > 0:  # the corner must lie past the stroke's end, not along it
        return None
    side = 1 if flat_far.x > cx else -1
    us = ((stroke_far.x - cx), (stroke_far.y - flat_y))
    ls = math.hypot(*us)
    us = (us[0] / ls, us[1] / ls)
    r = math.dist((cx, flat_y), (stroke_end.x, stroke_end.y))
    if (flat_end.x - cx) * side > 0:
        r = max(r, abs(flat_end.x - cx))
    r = min(r, 0.8 * abs(flat_far.x - cx), 0.8 * ls)
    tf = (cx + side * r, flat_y)
    ts = (cx + r * us[0], flat_y + r * us[1])
    hf = (tf[0] + FILLET * (cx - tf[0]), flat_y)
    hs = (ts[0] + FILLET * (cx - ts[0]), ts[1] + FILLET * (flat_y - ts[1]))
    tf, ts, hf, hs = (tuple(round(v) for v in q) for q in (tf, ts, hf, hs))
    return (tf, hf, hs, ts) if flat_first else (ts, hs, hf, tf)


def _segment(P, i):
    """the points of the segment ending at on-curve P[i]: its off-curves, then it"""
    k, offs = (i - 1) % len(P), []
    while P[k].type is None:
        offs.append(P[k])
        k = (k - 1) % len(P)
    return offs[::-1] + [P[i]]


def finish(font):
    # the Bold Italic's x.sc was drawn here (2026-11-01, its arm and leg
    # into their serifs) until the italic small caps took their capitals'
    # weight (make_italic.as_capitals, 2026-11-05): by its strokes, its
    # brackets made fillets (the person, 2026-11-05: the knees removed)
    if font.info.styleName == "Bold":
        k_sc(font)
    else:
        fillets(font["x.sc"])
    for name in ("m.sc", "v.sc", "w.sc"):
        points = [p for c in font[name].contours for p in c.points]
        for p in points:
            p.y = min(p.y, HEIGHT)
        low = min(p.y for p in points)
        if low < -DEPTH:
            for p in points:
                if p.y < 0:
                    p.y = round(p.y * DEPTH / -low)
    if font.info.styleName == "Bold Italic":
        for glyph in font:
            if glyph.name.endswith(".sc") and glyph.contours:
                brackets(glyph)
