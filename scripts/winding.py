"""Contour direction: every glyph winds as the Regular does.

The Regular winds its outer contours clockwise and its counters
counter-clockwise. Old Standard's CFF outlines, pathops' results (simplify
and op return counter-clockwise outers by default) and a mirrored or
flipped letter (make_bold's TRANSFORMS) wind the other way; a glyph that
mixes the two loses ink where one of its pieces is merged across another
(derive.merged, one path, nonzero winding: ʢ's bar across ʔ's stem,
2026-11-24).

A contour's direction is set by its depth: one inside an even number of
the glyph's other contours is an outside and winds clockwise, one inside an
odd number a counter and winds counter-clockwise. A contour wound against
its depth is turned on its own (Bold ʝ: the body from pathops, the dot as
drawn). Contours that overlap (no contour wholly inside or outside
another) leave the depth undecided; such a glyph is only turned as a
whole, when every decided contour winds against its depth, and otherwise
reported. A contour of no area (a stray point) is passed over.

orient(font) turns the glyphs that wind the other way (each contour
reversed with its points kept, ReverseContourPointPen); the generators
call it before saving (make_italic, make_bold, smallcaps). As a script it
is the check:

    .venv/bin/python -I scripts/winding.py sources/*.ufo

lists the glyphs winding against the rule and those it cannot decide, and
exits 1 when any winds against it.
"""

import sys

import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.pointPen import ReverseContourPointPen
from fontTools.pens.recordingPen import RecordingPointPen

CLOCKWISE = True  # the Regular's outer contours


def _area(contour):
    pen = AreaPen()
    contour.draw(pen)
    return pen.value  # positive: counter-clockwise


def _path(contour):
    p = pathops.Path()
    contour.draw(p.getPen())
    return p


def _inside(a, b):
    """a wholly inside b (their overlap is all of a)"""
    try:
        common = pathops.op(a, b, pathops.PathOp.INTERSECTION)
    except pathops.PathOpsError:
        return None
    aa = abs(a.area)
    if aa == 0:
        return False
    share = abs(common.area) / aa
    if share > 0.999:
        return True
    if share < 0.001:
        return False
    return None  # overlapping: undecided


def wanted(glyph):
    """per contour: True when it should wind clockwise, False
    counter-clockwise, None undecided (overlaps)"""
    paths = [_path(c) for c in glyph.contours]
    # pathops winds by itself: compare areas, not directions
    for p in paths:
        if p.area and not p.clockwise:
            p.reverse()
    out = []
    for i, a in enumerate(paths):
        depth, sure = 0, True
        for j, b in enumerate(paths):
            if i == j or abs(b.area) < abs(a.area):
                continue
            inside = _inside(a, b)
            if inside is None:
                sure = False
            elif inside:
                depth += 1
        out.append((depth % 2 == 0) == CLOCKWISE if sure else None)
    return out


def against(glyph):
    """the indices of glyph's contours that wind against their depth, or
    None when it cannot be told contour by contour: some winding against
    and some with it while others overlap (undecided). A contour of no
    area (a stray point) has no direction and is passed over."""
    want = wanted(glyph)
    have = [_area(c) for c in glyph.contours]
    decided = [(i, w == (h < 0)) for i, (w, h) in enumerate(zip(want, have)) if h and w is not None]
    wrong = [i for i, ok in decided if not ok]
    # overlapping contours are pieces of the outside (a stroke laid
    # across another), clockwise all of them
    undecided = [h < 0 for w, h in zip(want, have) if h and w is None]
    if not undecided:
        return wrong
    if not wrong and all(undecided):
        return []
    if len(wrong) == len(decided) and not any(undecided):
        return [i for i, h in enumerate(have) if h]  # all of it flipped
    return None


def judge(glyph):
    """'ok', 'turn' (the whole glyph wound the other way), 'mixed' (some
    contours each way, each decided: turned one by one) or 'undecided'
    (overlapping contours wound both ways: left)"""
    if not glyph.contours:
        return "ok"
    wrong = against(glyph)
    if wrong is None:
        return "undecided"
    if not wrong:
        return "ok"
    real = [i for i, c in enumerate(glyph.contours) if _area(c)]
    return "turn" if wrong == real else "mixed"


def reverse(glyph, which=None):
    """glyph's contours (or those at the indices which) reversed, their
    points and the points' names kept"""
    contours = []
    for i, c in enumerate(glyph.contours):
        rec = RecordingPointPen()
        c.drawPoints(ReverseContourPointPen(rec) if which is None or i in which else rec)
        contours.append(rec)
    components = list(glyph.components)
    glyph.clearContours()
    pen = glyph.getPointPen()
    for rec in contours:
        rec.replay(pen)
    assert list(glyph.components) == components


def orient(font, names=None):
    """the glyphs of font (or those named) that wind against the Regular
    turned; returns (turned, left), left the names it could not turn
    (mixed or undecided), with their verdict"""
    turned, left = [], {}
    for name in names if names is not None else list(font.keys()):
        g = font[name]
        if not g.contours:
            continue
        wrong = against(g)
        if wrong is None:
            left[name] = "undecided"
        elif wrong:
            reverse(g, set(wrong))
            turned.append(name)
    return turned, left


def main(paths):
    import ufoLib2

    bad = False
    for path in paths:
        font = ufoLib2.Font.open(path)
        verdicts = {}
        for g in font:
            v = judge(g)
            if v != "ok":
                verdicts.setdefault(v, []).append(g.name)
        print(f"{path}: " + (", ".join(f"{v} {len(n)}" for v, n in sorted(verdicts.items())) or "all wound as the Regular"))
        for v, names in sorted(verdicts.items()):
            print(f"  {v}: " + " ".join(sorted(names)))
        bad |= bool(verdicts)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
