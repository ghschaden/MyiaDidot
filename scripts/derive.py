"""Draft new characters from existing glyphs: same shape, turned, mirrored.

    python scripts/derive.py UFO [--redraft] [CHARS...]

Each recipe below makes one encoded glyph from a source glyph (a glyph name,
or an earlier recipe's character):

    alias     a component of the source (Ɪ = I, ɩ = ι); follows
              any later change to the source (its width on a run)
    turn      outlines turned 180° about the middle of the band given
              (x: x-height, c: cap height, s: small-cap height)
    mirror    outlines mirrored left-right
    flip      outlines mirrored top-bottom about the middle of the band
    nodot     the source without its lowest contour, the stem run down to
              the baseline (? -> ʔ)
    double    two copies side by side (| -> ǁ)
    bar       a horizontal bar merged into the outlines (Ɨ ʉ Ө): across the
              stems the ink crosses at that height, stretching OVER past
              them but not past the letter's ink (ħ, Đ, Ŧ have 168/220)
    slash     a diagonal stroke merged in: corner to corner like Ø (Ⱥ ȼ),
              or short through one stem like ł (ƛ)
    midtilde  a tilde across the letter at mid height (ɫ ᵬ)
    unserif   the outer arm of the last stem's top serif cut away, the
              stem's right edge run up to the top: the base of Ư (U.horn),
              whose horn grows out of the stem (its Horn anchor there)

A recipe for "U.horn" makes the unencoded U.horn (a Latin letter's
variant, only for the suffixes in ASCII_VARIANTS). A recipe for "ɔ.sc"
makes the small cap uni0254.sc (unencoded, reached through smcp/c2sc once
smallcaps.py has run); it is marked as a small-cap draft and reviewed with
the other small caps.

Transformed glyphs get plain outlines, not components, since they are
meant to be redrawn (a turned serif sits on the wrong side). Every glyph
is marked as a draft (lib DRAFT_KEY) and appears under "Other drafts" in
the small-caps review sheet. Existing glyphs are never touched, except
unreviewed drafts with --redraft. CHARS limits the run to those characters.
Each glyph drawn records the glyphs its recipe read, as they are saved
(lib org.myiadidot.builtFrom, scripts/built_from.py), so that a base edited
later is noticed; existing ones without the record get it on a run.
"""

import argparse
import itertools
import math
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_regular import (
    BIG,
    ENLARGE_LIKE,
    F_HOOK,  # noqa: F401  (read as derive.F_HOOK elsewhere)
    F_TOP,  # noqa: F401  (read as derive.F_TOP elsewhere)
    J_TAIL,  # noqa: F401  (read as derive.J_TAIL elsewhere)
    NARROW,
    RECIPES,
    SMOOTH_CURVES,
    SPACING,
)
from smallcaps import DEFAULT_HEIGHT, HEIGHT_KEY, ink_bounds, ink_slice
from smallcaps import DRAFT_KEY as SMALLCAP_DRAFT_KEY

DRAFT_KEY = "org.myiadidot.draft"
DERIVED_KEY = "org.myiadidot.derived"
# font lib: (stems, hairlines) of the font against the style the recipes'
# drawn thicknesses are for (make_bold.rederive sets it for the Bold's)
STROKE_KEY = "org.myiadidot.strokeScale"


# suffixes that make an ASCII letter's recipe a variant (an ASCII name
# with any other is a glyph name: g.sc)
ASCII_VARIANTS = (".horn", ".sc.horn", ".ipa")





def narrowed(path, x0, factor):
    """path with every point left of x0 moved towards it by factor (an
    affine map on that side, so curves keep their smoothness where their
    points all lie on it)"""
    rec = RecordingPen()
    path.draw(rec)
    pen = RecordingPen()

    def f(pt):
        x, y = pt
        return (x0 - (x0 - x) * factor if x < x0 else x, y)

    for op, args in rec.value:
        getattr(pen, op)(*(f(pt) for pt in args))
    return to_path(None, rec=pen)


# anchors that keep their meaning when the shape is mirrored left-right
# within the same vertical band
KEEP_ANCHORS = ("Top", "Acute", "Grave", "Dotaccent", "TopCap", "Bottom", "DotBelow")


def variant(ch):
    """A recipe's variant of a character, its suffix: "ɔ.sc" (the small
    cap), "б.loclSRB" (a localized form, unencoded), "U.horn" (a base drawn
    for a mark); "" for the character."""
    if len(ch) > 2 and ch[1] == "." and (not ch[0].isascii() or ch[1:] in ASCII_VARIANTS):
        return ch[1:]
    return ch[1:] if ch.endswith(".sc") and len(ch) == 4 else ""


def glyph_name(ch):
    if variant(ch):
        return glyph_name(ch[0]) + variant(ch)
    return f"uni{ord(ch):04X}" if ord(ch) <= 0xFFFF else f"u{ord(ch):05X}"


def resolve(cmap, c):
    """Glyph name of a recipe's character or variant ("ƒ.sc" -> florin.sc,
    "б.loclSRB" -> uni0431.loclSRB) by the font's cmap; a glyph name as it is."""
    if variant(c):
        return cmap.get(ord(c[0]), glyph_name(c[0])) + variant(c)
    return cmap.get(ord(c), glyph_name(c)) if len(c) == 1 else c


def band_middle(font, band):
    return {
        "x": font.info.xHeight,
        "c": font.info.capHeight,
        "s": font.lib.get(HEIGHT_KEY, DEFAULT_HEIGHT),
    }[band] / 2


def draw_transformed(font, src, dst, transform, reverse):
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    pen = dst.getPen()
    if reverse:
        pen = ReverseContourPen(pen)
    rec.replay(TransformPen(pen, transform))


def with_extremes(rec, out, round_points=True, past=None):
    """Replay a recording into the pen out with each cubic split where it
    turns in x or y (a sheared bowl's extremes move off its points); given
    past, only where it runs more than past units beyond its end points; points
    rounded to whole units unless the caller will round smoothly."""
    from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT

    def turns(a, b, c, d):
        # roots of the derivative of one coordinate, inside the curve
        return [t for t in solveQuadratic(3 * (-a + 3 * b - 3 * c + d), 6 * (a - 2 * b + c), 3 * (b - a))
                if 0.02 < t < 0.98 and (past is None or beyond(a, b, c, d, t) > past)]

    def beyond(a, b, c, d, t):
        v = (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d
        return max(v - max(a, d), min(a, d) - v)

    def r(pt):
        return (round(pt[0]), round(pt[1])) if round_points else pt

    current = None
    for op, args in rec.value:
        if op == "curveTo" and len(args) == 3:
            p0, (p1, p2, p3) = current, args
            ts = sorted(set(turns(p0[0], p1[0], p2[0], p3[0]) + turns(p0[1], p1[1], p2[1], p3[1])))
            for seg in splitCubicAtT(p0, p1, p2, p3, *ts) if ts else [(p0, p1, p2, p3)]:
                out.curveTo(r(seg[1]), r(seg[2]), r(seg[3]))
            current = p3
        else:
            getattr(out, op)(*[r(a) for a in args])
            current = args[-1] if args else current


# bar thickness and how far a bar runs past the stems, as in ħ ŧ / Đ Ŧ
BARS = {"x": (56, 168), "c": (64, 220), "s": (60, 190)}
# the y a bar sits at for each band; capitals as in Đ Ŧ (714-778)
BAR_Y = {"x": 442, "c": 746}
SLASH = {"x": 55, "c": 77, "s": 66}  # perpendicular thickness of Ø ø


def bar_y(font, band, y):
    if y is not None:
        return y
    return BAR_Y.get(band) or band_middle(font, band)


def stems_at(font, name, y):
    """The ink intervals at height y, as (x0, x1) pairs."""
    xs = ink_slice(font, name, y + 0.01)  # off the nodes at the extremes
    return list(zip(xs[::2], xs[1::2]))


def rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def stroke(pen, p0, p1, t):
    """A straight stroke of perpendicular thickness t, ends cut square."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * t / 2, dx / n * t / 2
    pen.moveTo((p0[0] + ox, p0[1] + oy))
    pen.lineTo((p1[0] + ox, p1[1] + oy))
    pen.lineTo((p1[0] - ox, p1[1] - oy))
    pen.lineTo((p0[0] - ox, p0[1] - oy))
    pen.closePath()


def bar_shape(font, source, band, arg):
    """Pen commands for the bar: arg is (y or None, which stems, overhang or
    None, thickness or None); which is 'all', 'first', 'last' or 'inside'
    (Ө: the counter only). An overhang (left, right) is taken as given, past
    the letter's ink if so (ǥ: a bar standing out of the loop it crosses,
    not a ledge on it); a thickness, a heavier style's own bar (the Bold
    Italic's ʉ, rebuilt on its u)."""
    y, which, over, own = (arg + (None, None, None, None))[:4]
    t, default_over = BARS[band]
    t = own or t
    over = default_over if over is None else over
    if isinstance(over, tuple):
        stems = stems_at(font, source, bar_y(font, band, y))
        if which == "first":
            stems = stems[:1]
        elif which == "last":
            stems = stems[-1:]
        y = bar_y(font, band, y)
        rec = RecordingPen()
        rect(rec, stems[0][0] - over[0], y - t / 2, stems[-1][1] + over[1], y + t / 2)
        return rec
    y = bar_y(font, band, y)
    stems = stems_at(font, source, y)
    if which == "first":
        stems = stems[:1]
    elif which == "last":
        stems = stems[-1:]
    x0, x1 = stems[0][0], stems[-1][1]
    if which == "inside":
        x0, x1 = stems[0][1] - 20, stems[-1][0] + 20
    else:
        ink = ink_bounds(font, source)
        x0, x1 = max(x0 - over, min(ink[0], x0)), min(x1 + over, max(ink[2], x1))
    rec = RecordingPen()
    rect(rec, x0, y - t / 2, x1, y + t / 2)
    return rec


def slash_shape(font, source, band, arg):
    """arg ('box', fx0, y0, fx1, y1[, thickness]): from (x0 + fx0*w, y0) to
    (x0 + fx1*w, y1) in the ink box, like Ø, a heavier style's own
    thickness if given (the Bold Italic's Ⱦ ⱦ.sc); or ('short', y, length,
    angle, which): a stroke of that length centred on a stem at height y,
    like ł."""
    t = SLASH[band]
    rec = RecordingPen()
    if arg[0] == "box":
        _, fx0, y0, fx1, y1, *own = arg
        t = own[0] if own else t
        x0, _, x1, _ = ink_bounds(font, source)
        w = x1 - x0
        p0, p1 = (x0 + fx0 * w, y0), (x0 + fx1 * w, y1)
        if not own:
            stroke(rec, p0, p1, t)
            return rec
        # a heavier style's own slash ends level at y1, flush in the top
        # line (its square end stood a corner over it): run on, cut level,
        # its corners in stroke's order (so it winds as stroke draws it)
        n = math.dist(p0, p1)
        ux, uy = (p1[0] - p0[0]) / n, (p1[1] - p0[1]) / n
        q = (p1[0] + ux * t, p1[1] + uy * t)
        ox, oy = -uy * t / 2, ux * t / 2
        corners = [(p0[0] + ox, p0[1] + oy), (q[0] + ox, q[1] + oy), (q[0] - ox, q[1] - oy), (p0[0] - ox, p0[1] - oy)]
        kept = []
        for a, b in zip(corners, corners[1:] + corners[:1]):
            if a[1] <= y1:
                kept.append(a)
            if (a[1] - y1) * (b[1] - y1) < 0:
                k = (y1 - a[1]) / (b[1] - a[1])
                kept.append((a[0] + k * (b[0] - a[0]), y1))
        rec.moveTo(kept[0])
        for pt in kept[1:]:
            rec.lineTo(pt)
        rec.closePath()
    else:
        _, y, length, angle, which = arg
        stems = stems_at(font, source, y)
        s = stems[0] if which == "first" else stems[-1]
        cx = (s[0] + s[1]) / 2
        dx, dy = math.cos(math.radians(angle)) * length / 2, math.sin(math.radians(angle)) * length / 2
        stroke(rec, (cx - dx, y - dy), (cx + dx, y + dy), t)
    return rec


def midtilde_shape(font, source, band, arg):
    """The spacing tilde squeezed to 85% height, centred at the bar height
    and stretched across the ink there plus a bit (arg: (y or None, which,
    right, left): right and left move its ends outward, in units)."""
    y, which, right, left = (arg + (None, None, None, None))[:4]
    y = bar_y(font, band, y)
    stems = stems_at(font, source, y)
    if which == "first":
        stems = stems[:1]
    over = BARS[band][1] * 0.8
    x0, x1 = stems[0][0] - over - (left or 0), stems[-1][1] + over + (right or 0)
    tx0, ty0, tx1, ty1 = ink_bounds(font, "tilde")
    sx = (x1 - x0) / (tx1 - tx0)
    sy = 0.85 * (1 if band != "s" else 0.9)
    own = RecordingPen()
    font["tilde"].draw(own)
    own = tapered_ends(own, MIDTILDE_TAPER)
    rec = RecordingPen()
    tp = TransformPen(rec, (sx, 0, 0, sy, x0 - tx0 * sx, y - (ty0 + ty1) / 2 * sy))
    own.replay(tp)
    # stretched across two stems (1.7-1.9 times) its ends flatten: the
    # stretch spread unevenly, less at the ends, more in the middle (chosen
    # 2026-11-09, "more": ᵭ's ends 1.20, its middle 2.52); a tilde stretched
    # 1.2 times or less (ɫ ᵮ ᵲ ᵵ) as it was
    c = -min(0.4, 1 - 1.2 / sx) if sx > 1.2 else 0
    if c:
        width = x1 - x0

        def warp(x):
            u = (x - x0) / width
            return x0 + width * (u + c * math.sin(2 * math.pi * u) / (2 * math.pi))

        rec.value = [(op, tuple((warp(px), py) for px, py in args)) for op, args in rec.value]
    return rec


# the middle tilde's end faces narrowed to this share of the spacing tilde's,
# about their middles, the curves into them following: the ends taper to
# their tips (asked 2026-11-09, chosen 0.4 for all styles; 1: the
# tilde's own ends)
MIDTILDE_TAPER = 0.4


def tapered_ends(rec, share):
    """The tilde's end faces (its two lines) narrowed to share of their length
    about their middles; the handles next to them move half as far."""
    if share == 1:
        return rec
    value = [(op, list(args)) for op, args in rec.value]
    start = 0
    for end, (op, _) in enumerate(value):
        if op not in ("closePath", "endPath"):
            continue
        segs = list(range(start, end))  # moveTo, then the segments
        faces = [(i - 1, i) for i in segs[1:] if value[i][0] == "lineTo"]
        if value[segs[-1]][1][-1] != value[segs[0]][1][0]:
            faces.append((segs[-1], segs[0]))  # the closing line
        for a, b in faces:
            (ax, ay), (bx, by) = value[a][1][-1], value[b][1][-1]
            mx, my = (ax + bx) / 2, (ay + by) / 2
            da = ((mx - ax) * (1 - share), (my - ay) * (1 - share))
            db = ((mx - bx) * (1 - share), (my - by) * (1 - share))
            value[a][1][-1] = (ax + da[0], ay + da[1])
            value[b][1][-1] = (bx + db[0], by + db[1])
            if value[a][0] == "curveTo":  # the handle into the face
                hx, hy = value[a][1][1]
                value[a][1][1] = (hx + da[0] / 2, hy + da[1] / 2)
            after = b + 1 if b + 1 < end else start + 1
            if value[after][0] == "curveTo":  # the handle out of it
                hx, hy = value[after][1][0]
                value[after][1][0] = (hx + db[0] / 2, hy + db[1] / 2)
        start = end + 1
    out = RecordingPen()
    out.value = [(op, tuple(args)) for op, args in value]
    return out


def merged(font, src, extra):
    """The source outlines and the extra shape merged into one outline."""
    path = pathops.Path()
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    rec.replay(path.getPen())
    extra.replay(path.getPen())
    out = RecordingPen()
    pathops.union([path], out)
    return out


def orientation(rec):
    """Sign of the largest contour's area."""
    best = 0
    for op, args in rec.value:
        if op == "moveTo":
            pen = AreaPen()
        getattr(pen, op)(*args)
        if op in ("closePath", "endPath"):
            best = max(best, pen.value, key=abs)
    return best > 0


def draw_merged(font, src, dst, extra):
    out = merged(font, src, extra)
    rec = DecomposingRecordingPen(font)
    src.draw(rec)
    pen = RoundingPen(dst.getPen())
    if orientation(out) != orientation(rec):
        pen = ReverseContourPen(pen)
    out.replay(pen)


def lines_shape(font, source, band, arg):
    """Straight strokes given by hand, arg (t, items): ((x0, y0), (x1, y1))
    segments of thickness t, or (x0, y0, x1, y1) boxes (₦ ₩ ₱ ₲ ₡ ...)."""
    t, items = arg
    rec = RecordingPen()
    for it in items:
        if len(it) == 4:
            rect(rec, *it)
        else:
            stroke(rec, it[0], it[1], t)
    return rec


SHAPES = {"bar": bar_shape, "slash": slash_shape, "midtilde": midtilde_shape,
          "lines": lines_shape}

# the descender of Ц ц (and the small cap) is the model for Қ Ң Җ Ҳ Ҷ
TAIL = {"c": "uni0426", "x": "uni0446", "s": "uni0446.sc"}
TAIL_Y = 300  # straight stem in all three


def to_path(font, glyph=None, rec=None):
    path = pathops.Path()
    if glyph is not None:
        rec = DecomposingRecordingPen(font)
        glyph.draw(rec)
    rec.replay(path.getPen())
    return path


def counters(font, glyph):
    """The glyph's counters, each a path: its contours that wind against
    the largest."""
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    contours, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            contours.append(cur)
            cur = []

    def area(contour):
        pts = [pt for _, args in contour for pt in args]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in contours]
    outer = max(areas, key=abs, default=1) > 0
    found = []
    for contour, a in zip(contours, areas, strict=True):
        if a and (a > 0) != outer:
            one = RecordingPen()
            one.value = contour
            found.append(to_path(None, rec=one))
    return found


def rect_path(x0, y0, x1, y1):
    rec = RecordingPen()
    rect(rec, x0, y0, x1, y1)
    return to_path(None, rec=rec)


def path_op(a, b, op):
    return pathops.op(a, b, getattr(pathops.PathOp, op))


def shifted(path, dx, dy=0):
    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, dy)))
    return to_path(None, rec=rec)


def foot_top(font, name, stem):
    """Height of the foot serif under a stem (x0, x1): the lowest y where the
    ink there is no wider than the stem."""
    for y in range(2, 200, 2):
        s = [iv for iv in stems_at(font, name, y) if iv[0] <= stem[1] and iv[1] >= stem[0]]
        if s and s[0][1] - s[0][0] <= stem[1] - stem[0] + 2:
            return y - 2
    return 0


def serif_foot(font, name):
    """(y, y_stem, x): the height where the last stem's top serif has given
    way (the slab's underside: the width falls below 0.6 of it; the
    italics' slab tapers), where its bracket has (the width within 1.15 of
    the stem's at half the height), and the stem's right edge there."""
    def width(y):
        x0, x1 = stems_at(font, name, y)[-1]
        return x1 - x0

    _, bottom, _, top = ink_bounds(font, name)
    serif, stem = width(top - 5), width((bottom + top) / 2)
    y = top - 5
    while width(y) > 0.6 * serif:
        y -= 2
        if y < top - 400:
            raise ValueError(f"{name}: no top serif on the last stem")
    y_stem = y
    while width(y_stem) > 1.15 * stem and y_stem > y - 300:
        y_stem -= 2
    return y, y_stem, stems_at(font, name, y_stem)[-1][1]


def unserif_cut(font, source):
    """What unserif cuts away: the outer arm of the last stem's top serif
    and the bracket under it (the italics'), so that the stem's right edge
    runs straight up to the slab."""
    _, y, x = serif_foot(font, source)
    return rect_path(x, y, BIG, BIG)


def unserif_path(font, source):
    """The letter without the outer arm of its last stem's top serif."""
    return path_op(to_path(font, font[source]), unserif_cut(font, source), "DIFFERENCE")


def stem_horn_anchor(font, name, inside=24):
    """Where a horn's tail goes on a stem without its serif's outer arm
    (unserif): on the stem's right edge, 25 below the serif's foot,
    inside units into the ink."""
    y = serif_foot(font, name)[0] - 25
    return round(stems_at(font, name, y)[-1][1] - inside), round(y)


def tail_path(font, source, band, mode):
    """The letter with the descender of Ц: 'stem' replaces the foot of the
    right stem (Ң Ҷ); 'foot' hangs it under the right foot serif (Қ Җ Ҳ)."""
    tsrc = TAIL[band]
    sa, sb = stems_at(font, tsrc, TAIL_Y)[-1]
    letter = to_path(font, font[source])
    if mode == "stem":
        ta, tb = stems_at(font, source, TAIL_Y)[-1]
        # a little above the serif's top, so no hairline of it is left (the tail covers it)
        letter = path_op(letter, rect_path(ta, -BIG, BIG, foot_top(font, source, (ta, tb)) + 6), "DIFFERENCE")
        keep = rect_path(sa, -BIG, BIG, TAIL_Y)
        dx = ta - sa
    else:
        fb = stems_at(font, source, 10)[-1][1]
        keep = rect_path(sa, -BIG, BIG, 30)
        dx = fb - sb - (sb - sa) / 2
    keep = path_op(keep, rect_path(-BIG, -BIG, BIG, 0), "UNION")
    piece = shifted(path_op(to_path(font, font[tsrc]), keep, "INTERSECTION"), dx)
    out = path_op(letter, piece, "UNION")
    if mode == "foot":
        out = path_op(out, tail_step(letter, piece, 30), "UNION")
    rsb = font[tsrc].width - ink_bounds(font, tsrc)[2]
    return out, piece.bounds[2] + rsb


def tail_step(letter, piece, top):
    """Where the tail's top (cut flat at top) runs on past a foot serif
    whose end drops steeply (the italics' Ҳ Қ Җ: a step of 15 units), the
    step filled: a straight edge from the serif's top corner to the tail's
    top corner. Nothing where the serif's end slopes into it (the Regular)."""
    def right(path, y):
        cut = path_op(path, rect_path(-BIG, y - 0.5, BIG, y + 0.5), "INTERSECTION")
        return cut.bounds[2] if list(cut.contours) else None

    # the tail's top at its right corner: the cut, or below it where the
    # tail's model starts lower (the Italic's Ц: 25)
    xr = piece.bounds[2]
    top = min(top, round(path_op(piece, rect_path(xr - 10, -BIG, BIG, BIG), "INTERSECTION").bounds[3]))
    xs, xt = right(letter, top + 1), right(piece, top - 1)
    if xs is None or xt is None or xt - xs < 5:
        return pathops.Path()
    # up the serif's end to its top corner, where the right edge turns back
    # (onto a flat top, or one sloping as the Italic's)
    y, x = top + 1, xs
    while True:
        nx = right(letter, y + 2)
        if nx is None or nx < x - 8:
            break
        y, x = y + 2, nx
    if y - top < 4 or x - xs > y - top:  # no step, or the end slopes into the tail
        return pathops.Path()
    rec = RecordingPen()
    rec.moveTo((x - 1, y))
    rec.lineTo((xt, top))
    rec.lineTo((xt - 12, top - 2))  # inside the tail, which runs in below its corner
    rec.lineTo((xs - 1, top - 2))
    rec.closePath()
    return to_path(None, rec=rec)


def vertical_runs(font, name, x):
    """(y0, y1) of the ink crossed by a vertical line at x, bottom to top."""
    cut = path_op(to_path(font, font[name]), rect_path(x - 0.5, -BIG, x + 0.5, BIG), "INTERSECTION")
    runs = []
    for contour in cut.contours:
        b = contour.bounds
        runs.append((b[1], b[3]))
    return sorted(runs)


def strokes(font, name):
    """(ink box, round stem at mid height, top hairline) of an o-like glyph."""
    b = ink_bounds(font, name)
    s = stems_at(font, name, (b[1] + b[3]) / 2)[0]
    top = vertical_runs(font, name, (b[0] + b[2]) / 2)[-1]
    return b, s[1] - s[0], top[1] - top[0]


def straight_stem(font, name):
    """The width of the first stem a third of the way up: an italic's stem
    swells towards the branch at mid height."""
    b = ink_bounds(font, name)
    x0, x1 = stems_at(font, name, b[1] + (b[3] - b[1]) / 3)[0]
    return x1 - x0


def keep_brackets(P, ons, old, new, sign):
    """Brackets the emboldening overran: a concave curve (sign: the
    contour's winding, as embolden's) between a stroke that grew
    and a straight edge running on from it (G's jaw stem into its bar, the
    bar a hairline that only grows in y), whose node on that edge now lies
    less than half as far from where the two tangents meet as before (or
    past it: the handles, as long as before, curl back into a hook). That
    node slides along its edge (no further than half of it) until the
    bracket is as long as before; the handles keep their share of it.
    Moves the nodes in new; returns {segment's first node: its handles}
    and the nodes whose handles must run on from their neighbour (each
    slid node, along its edge, and the bracket's other end, along the
    stroke it leaves), as (node, the neighbour, the node's handle, how
    far the neighbour must stay for its direction to count)."""
    n, L = len(P), len(ons)

    def unit(dx, dy):
        d = math.hypot(dx, dy)
        return (dx / d, dy / d) if d > 1e-9 else None

    def meet(a, ta, b, tb):
        """s, t with a + s ta = b - t tb (None if parallel)"""
        det = ta[0] * tb[1] - ta[1] * tb[0]  # s ta + t tb = b - a
        if abs(det) < 0.2:  # tangents nearly parallel: no bracket
            return None
        rx, ry = b[0] - a[0], b[1] - a[1]
        return (rx * tb[1] - ry * tb[0]) / det, (ta[0] * ry - ta[1] * rx) / det

    out, slid = {}, []
    for idx, i in enumerate(ons):
        j = ons[(idx + 1) % L]
        if (j - i) % n != 3:
            continue
        h1, h2 = (i + 1) % n, (i + 2) % n
        ta = unit(old[h1][0] - old[i][0], old[h1][1] - old[i][1])
        tb = unit(old[j][0] - old[h2][0], old[j][1] - old[h2][1])
        if not ta or not tb:
            continue
        if (ta[0] * tb[1] - ta[1] * tb[0]) * sign >= 0:  # a tip rounded (Ɛ's beak), not a bracket
            continue
        was = meet(old[i], ta, old[j], tb)
        if not was or min(was) <= 0:
            continue
        now = meet(new[i], ta, new[j], tb)
        if not now:
            continue
        s, t = now
        # the edge before i, arriving along ta; the one after j, leaving along tb
        before = ons[(idx - 1) % L]
        after = ons[(idx + 2) % L]
        for end, (wanted, got) in (("i", (was[0], s)), ("j", (was[1], t))):
            if got >= 0.5 * wanted:
                continue
            q, far = (i, before) if end == "i" else (j, after)
            straight = P[q].type == "line" if end == "i" else P[far].type == "line"
            if not straight:
                continue
            edge = unit(old[q][0] - old[far][0], old[q][1] - old[far][1]) if end == "i" else \
                unit(old[far][0] - old[q][0], old[far][1] - old[q][1])
            tn = ta if end == "i" else tb
            if not edge or edge[0] * tn[0] + edge[1] * tn[1] < 0.999:
                continue
            # the other end runs on smoothly into the stroke that grew (not
            # a tip: Ɛ's beak, whose underside is concave too)
            o, nb = (j, (j + 1) % n) if end == "i" else (i, (i - 1) % n)
            on = unit(old[nb][0] - old[o][0], old[nb][1] - old[o][1]) if end == "i" else \
                unit(old[o][0] - old[nb][0], old[o][1] - old[nb][1])
            to = tb if end == "i" else ta
            if not on or on[0] * to[0] + on[1] * to[1] < 0.99:
                continue
            slide = min(wanted - got, 0.5 * math.dist(new[q], new[far]))
            sgn = -1 if end == "i" else 1
            new[q] = (new[q][0] + sgn * tn[0] * slide, new[q][1] + sgn * tn[1] * slide)
            slid.append((q, far, h1 if end == "i" else h2, 0))
            # and the other end: there the bracket runs on from the stroke
            # (the source's slight corner, on handles too short to show it,
            # would show on the longer ones); not from a tip's few units,
            # whose direction is noise
            if math.dist(old[o], old[nb]) >= 20:
                slid.append((o, nb, h2 if end == "i" else h1, 20))
            if end == "i":
                s += slide
            else:
                t += slide
        if (s, t) != now:
            la = math.dist(old[i], old[h1]) * max(s, 0) / was[0]
            lb = math.dist(old[h2], old[j]) * max(t, 0) / was[1]
            out[i] = ((new[i][0] + ta[0] * la, new[i][1] + ta[1] * la),
                      (new[j][0] - tb[0] * lb, new[j][1] - tb[1] * lb))
    return out, slid


def embolden(rec, ax, ay, factor=None, slid=None, keep_bends=False):
    """Thicken vertical strokes by ax and horizontal ones by ay (negative:
    thinner). Each node moves out along its outline's normal (at a corner,
    along the bisector, as far as both edges move: a mitre, limited); its
    handles move with it and grow as their segment grows, so smooth nodes
    stay smooth and a circle stays a circle. factor(x, y, inward) -> 0..1, if
    given, scales ax at each node (make_italic: the thick strokes only).
    slid, a list if given, gets the bracket nodes keep_brackets slid, as
    (contour, node, far node, handle). keep_bends: a fitted curve that
    bends both ways where the source curve bent one way only has its
    handles moved with its nodes instead (a wobble the fit put in).
    """
    glyph = ufoLib2.objects.Glyph()
    rec.replay(glyph.getPen())

    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    def unit(dx, dy):
        n = math.hypot(dx, dy)
        return (dx / n, dy / n) if n > 1e-9 else None

    # outlines wind like the largest contour, counters the other way: an
    # outline grows outward, a counter shrinks (its boundary moves into it),
    # so the ink around a counter thickens too
    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    for contour, a in zip(glyph.contours, areas, strict=True):
        P = contour.points
        n = len(P)
        sign = 1 if a > 0 else -1
        if (a > 0) != outer:
            sign = -sign
        ons = [i for i, p in enumerate(P) if p.type]
        if not ons or n < 3:
            continue
        old = [(p.x, p.y) for p in P]
        move, ks = {}, {}
        for i in ons:
            x, y = old[i]
            # the nearest distinct points before and after: the tangents
            b = next((old[(i - k) % n] for k in range(1, n) if old[(i - k) % n] != (x, y)), None)
            f = next((old[(i + k) % n] for k in range(1, n) if old[(i + k) % n] != (x, y)), None)
            t_in, t_out = unit(x - b[0], y - b[1]), unit(f[0] - x, f[1] - y)
            if not t_in or not t_out:
                move[i] = (0.0, 0.0)
                continue
            # right-hand normals of the edges, and their bisector
            n_in, n_out = (t_in[1], -t_in[0]), (t_out[1], -t_out[0])
            m = unit(n_in[0] + n_out[0], n_in[1] + n_out[1]) or n_in
            # the mitre: as far as both edges move; at a convex corner limited
            # (no spike), at a concave one (a crotch) whole, or a slit is left
            turn = t_in[0] * t_out[1] - t_in[1] * t_out[0]
            convex = turn * sign < 0
            half = max(0.5 if convex else 0.1, math.hypot(n_in[0] + n_out[0], n_in[1] + n_out[1]) / 2)
            k = factor(x, y, (-sign * m[0], -sign * m[1])) if factor else 1.0
            ks[i] = k
            move[i] = (sign * m[0] / half * ax * k / 2, sign * m[1] / half * ay / 2)
        new = list(old)
        for i in ons:
            new[i] = (old[i][0] + move[i][0], old[i][1] + move[i][1])
        brackets, moved = keep_brackets(P, ons, old, new, sign)
        if slid is not None:
            slid += [(glyph.contours.index(contour), *m) for m in moved]
        # handles: along their old directions (so smooth nodes stay smooth),
        # their lengths fitted (least squares) to the curve's points offset
        # along their own normals, as far as the nodes are; a tight curve
        # keeps its shape
        def offset_fit(i, j, h1, h2, old=old, new=new, ks=ks, sign=sign):
            P0, P1, P2, P3 = old[i], old[h1], old[h2], old[j]
            A, B = new[i], new[j]
            ta = unit(P1[0] - P0[0], P1[1] - P0[1])
            tb = unit(P3[0] - P2[0], P3[1] - P2[1])
            if not ta or not tb:
                return None
            ka, kb = ks.get(i, 1.0), ks.get(j, 1.0)
            rows, rhs = [], []
            for step in range(1, 12):
                t = step / 12
                u = 1 - t
                pt = [u ** 3 * P0[q] + 3 * u * u * t * P1[q] + 3 * u * t * t * P2[q] + t ** 3 * P3[q] for q in (0, 1)]
                d = [3 * u * u * (P1[q] - P0[q]) + 6 * u * t * (P2[q] - P1[q]) + 3 * t * t * (P3[q] - P2[q])
                     for q in (0, 1)]
                tn = unit(*d)
                if not tn:
                    continue
                k = ka + (kb - ka) * t
                target = (pt[0] + sign * tn[1] * ax * k / 2, pt[1] - sign * tn[0] * ay / 2)
                b0, b1, b2, b3 = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
                base = [(b0 + b1) * A[q] + (b2 + b3) * B[q] for q in (0, 1)]
                for q in (0, 1):
                    rows.append((b1 * ta[q], -b2 * tb[q]))
                    rhs.append(target[q] - base[q])
            s11 = sum(r[0] * r[0] for r in rows)
            s12 = sum(r[0] * r[1] for r in rows)
            s22 = sum(r[1] * r[1] for r in rows)
            r1 = sum(r[0] * v for r, v in zip(rows, rhs, strict=True))
            r2 = sum(r[1] * v for r, v in zip(rows, rhs, strict=True))
            det = s11 * s22 - s12 * s12
            if abs(det) < 1e-9:
                return None
            la, lb = (r1 * s22 - r2 * s12) / det, (s11 * r2 - s12 * r1) / det
            # never shorter than a tenth of the old handles, nor turned round
            la = max(la, 0.1 * math.dist(P0, P1))
            lb = max(lb, 0.1 * math.dist(P2, P3))
            return (A[0] + ta[0] * la, A[1] + ta[1] * la), (B[0] - tb[0] * lb, B[1] - tb[1] * lb)

        for idx, i in enumerate(ons):
            j = ons[(idx + 1) % len(ons)]
            offs = [(i + k) % n for k in range(1, (j - i) % n or n)]
            if not offs:
                continue
            if i in brackets:
                new[offs[0]], new[offs[1]] = brackets[i]
                continue
            fitted = offset_fit(i, j, offs[0], offs[1]) if len(offs) == 2 else None
            # other segments: the handles with their nodes, scaled as the chord
            c0, c1 = math.dist(old[i], old[j]), math.dist(new[i], new[j])
            r = c1 / c0 if c0 > 1e-6 else 1.0
            plain = []
            for k, h in enumerate(offs):
                own = i if k < len(offs) / 2 else j
                ox, oy = old[own]
                nx, ny = new[own]
                plain.append((nx + (old[h][0] - ox) * r, ny + (old[h][1] - oy) * r))
            if fitted and keep_bends and inflects((new[i], *fitted, new[j])) and not inflects(
                    tuple(old[q] for q in (i, offs[0], offs[1], j))):
                # only as far toward the plain handles as takes the wobble out
                # (none does: the fit kept, as a terminal's plain handles loop)
                for w in (0.25, 0.5, 0.75, 1.0):
                    blend = tuple(tuple(f + (p_ - f) * w for f, p_ in zip(fh, ph, strict=True))
                                  for fh, ph in zip(fitted, plain, strict=True))
                    if not inflects((new[i], *blend, new[j])):
                        fitted = blend
                        break
            if fitted:
                new[offs[0]], new[offs[1]] = fitted
                continue
            for h, q in zip(offs, plain, strict=True):
                new[h] = q
        for p, (x, y) in zip(P, new, strict=True):
            p.x, p.y = x, y
    return glyph


def inflects(pts):
    """Whether a cubic bends both ways (its curvature changes sign inside)."""
    signs = set()
    for s in range(1, 20):
        t = s / 20
        u = 1 - t
        d1 = [3 * u * u * (pts[1][q] - pts[0][q]) + 6 * u * t * (pts[2][q] - pts[1][q])
              + 3 * t * t * (pts[3][q] - pts[2][q]) for q in (0, 1)]
        d2 = [6 * u * (pts[2][q] - 2 * pts[1][q] + pts[0][q]) + 6 * t * (pts[3][q] - 2 * pts[2][q] + pts[1][q])
              for q in (0, 1)]
        c = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(c) > 1e-6 * (d1[0] ** 2 + d1[1] ** 2) ** 1.5:
            signs.add(c > 0)
    return len(signs) > 1


# the alignment edges (flat tops and bottoms) of the Regular, which
# emboldening by ay moves by ay / 2: bottoms (descender, baseline), tops
ZONE_BOTTOMS = (-612, 0)
ZONE_TOPS = (884, 1040, 1434, 1496)


def rezone(glyph, ay):
    """Undo what emboldening by ay does to the alignment: the flat edges it
    moved by ay / 2 (bottoms down, tops up) put back on the zones, the
    heights between mapped linearly (by under 1 % of a zone)."""
    if not ay:
        return glyph
    moved = sorted([(z - ay / 2, z) for z in ZONE_BOTTOMS] + [(z + ay / 2, z) for z in ZONE_TOPS])

    def f(y):
        if y <= moved[0][0]:
            return y + moved[0][1] - moved[0][0]
        if y >= moved[-1][0]:
            return y + moved[-1][1] - moved[-1][0]
        for (y0, z0), (y1, z1) in itertools.pairwise(moved):
            if y0 <= y <= y1:
                return z0 + (y - y0) * (z1 - z0) / (y1 - y0)
        return y

    for c in glyph.contours:
        for p in c.points:
            p.y = f(p.y)
    return glyph


def merged_glyph(rec):
    """rec's outline with overlaps removed (pathops), as a ufoLib2 Glyph,
    cubic, winding as rec's does (pathops turns contours round)."""
    def winding(g):
        best = 0.0
        for c in g.contours:
            pen = AreaPen()
            c.draw(pen)
            if abs(pen.value) > abs(best):
                best = pen.value
        return best

    source = ufoLib2.objects.Glyph()
    rec.replay(source.getPen())
    merged = pathops.Path()
    rec.replay(merged.getPen())
    merged = pathops.simplify(merged)
    glyph = ufoLib2.objects.Glyph()
    merged.draw(CubicPen(glyph.getPen()))
    if winding(glyph) * winding(source) < 0:
        turned = ufoLib2.objects.Glyph()
        glyph.draw(ReverseContourPen(turned.getPen()))
        glyph = turned
    return glyph


def stroke_gauge(glyph):
    """across(px, py, ux, uy): the distance from (px, py) along (ux, uy) to
    the other side of the ink, over the glyph's outline as straight pieces
    (curves in tenths): the thickness of the stroke a point is on, measured
    inward from its edge."""
    import numpy as np

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
        return lambda px, py, ux, uy: 0.0
    a = np.array([s[0] for s in segs], float)
    d = np.array([s[1] for s in segs], float) - a

    def across(px, py, ux, uy):
        den = d[:, 0] * uy - d[:, 1] * ux
        ok = np.abs(den) > 1e-9
        wx, wy = a[:, 0] - px, a[:, 1] - py
        t = np.where(ok, (d[:, 0] * wy - d[:, 1] * wx) / np.where(ok, den, 1), -1)  # along the ray
        s = np.where(ok, (ux * wy - uy * wx) / np.where(ok, den, 1), -1)  # along the segment
        hit = ok & (t > 3) & (s >= 0) & (s <= 1)
        return float(t[hit].min()) if hit.any() else 0.0

    return across


def embolden_by_weight(rec, ax, ay, thin=60, thick=160, runs_on=False, keep_bends=False):
    """Thicken the thick strokes by ax across, in whatever direction they
    run, and every edge by ay vertically (the hairlines' gain): the contrast
    of a Didot bold, where emboldening every vertical by ax made the
    Bold's upright hairlines a stem's weight heavier (N's 64 -> 157) and left
    its thick diagonals light (N's +37: a crotch moved into the diagonal).

    embolden() with a weight per node (none below thin, all of ax above
    thick, by the stroke's thickness across; a wide band, so a tapering
    stroke's weight changes gradually): a node on a long straight edge
    takes the heavier of its edges', each measured at its middle (so an
    edge moves whole and keeps its slant); both nodes of a short edge (a
    serif's end, under SHORT) the heavier of the edges beside it (so the end
    moves whole, no spur); a node on a curve its own, averaged with the
    outline's a little way on either side; a node on both, the heavier
    (a junction belongs to its thick stroke). Then each corner
    between two straight edges goes where its two moved edges meet: a
    convex one no further than twice their move (no spike), a crotch (N's
    diagonal meeting its hairline stem) up to three times their move and
    0.8 of the shorter edge (by the bisector it moved into the diagonal).
    Overlaps are removed first: the weight is the union's. runs_on: a short
    edge also takes the weight of a curve it runs on into (RUNS_ON).
    """
    SHORT = 60
    RUNS_ON = 10  # degrees: a short edge this close to a curve's direction is part of its stroke
    glyph = merged_glyph(rec)  # overlaps removed: Θ's bar, Ø's slash weigh as the union does
    across = stroke_gauge(glyph)

    def k_of(w):
        return min(1.0, max(0.0, (w - thin) / (thick - thin)))

    def unit(dx, dy):
        n = math.hypot(dx, dy)
        return (dx / n, dy / n) if n > 1e-9 else None

    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    signs = []
    fixed = {}  # (x, y) -> weight, for nodes on straight edges
    corners = []  # (contour, index, in edge, out edge, weights): corners between two straight edges
    for ci, (contour, ar) in enumerate(zip(glyph.contours, areas, strict=True)):
        sign = 1 if ar > 0 else -1
        if (ar > 0) != outer:
            sign = -sign
        signs.append(sign)
        P = contour.points
        ons = [i for i, p in enumerate(P) if p.type]
        if len(ons) < 2:
            continue
        edges = []  # (i, j, straight, length, weight)
        for idx, i in enumerate(ons):
            j = ons[(idx + 1) % len(ons)]
            straight = P[j].type == "line"
            ln = math.dist((P[i].x, P[i].y), (P[j].x, P[j].y))
            k = None
            if straight and ln >= SHORT:
                t = unit(P[j].x - P[i].x, P[j].y - P[i].y)
                nx, ny = t[1], -t[0]
                k = k_of(across((P[i].x + P[j].x) / 2, (P[i].y + P[j].y) / 2, -sign * nx, -sign * ny))
            edges.append([i, j, straight, ln, k])
        m = len(edges)
        def curve_end(a, b, q, P=P, sign=sign):
            """k of a curve at its node q, running from point a to b there"""
            t = unit(P[b].x - P[a].x, P[b].y - P[a].y)
            if not t:
                return None
            return k_of(across(P[q].x, P[q].y, -sign * t[1], sign * t[0]))

        for e_i, e in enumerate(edges):
            if e[2] and e[3] < SHORT:  # a short straight edge: the heavier beside it
                # or the curve it runs on into, beside a long straight edge:
                # ƒ's stem edge begins under the bar with a short line,
                # weighed as the hairline bar alone it notched the stem
                prev, nxt = edges[(e_i - 1) % m], edges[(e_i + 1) % m]
                ks = [v for v in (prev[4], nxt[4]) if v is not None]
                d = unit(P[e[1]].x - P[e[0]].x, P[e[1]].y - P[e[0]].y)
                for side, other, (a, b, q) in ((prev, nxt, ((e[0] - 1) % len(P), e[0], e[0])),
                                               (nxt, prev, (e[1], (e[1] + 1) % len(P), e[1]))):
                    c = unit(P[b].x - P[a].x, P[b].y - P[a].y)
                    if (runs_on and not side[2] and other[2] and other[3] >= SHORT and c and d
                            and c[0] * d[0] + c[1] * d[1] > math.cos(math.radians(RUNS_ON))):
                        k = curve_end(a, b, q)
                        if k is not None:
                            ks.append(k)
                if ks:
                    e[4] = max(ks)
        for e in edges:
            if e[4] is None:
                continue
            for q in (e[0], e[1]):
                key = (P[q].x, P[q].y)
                fixed[key] = max(fixed.get(key, 0.0), e[4])
        for e_i, e in enumerate(edges):
            prev = edges[(e_i - 1) % m]
            if prev[2] and e[2] and prev[3] >= 1 and e[3] >= 1:
                corners.append((ci, e[0], prev, e))

    # the other nodes (on curves): their stroke's thickness, averaged with
    # the thickness a little way along the outline on either side (REACH), so
    # the weight changes gradually where a stem meets an arch's hairline (else
    # the arch's edge waves: n) and along a tapering stroke (t's top), while
    # a round's side, thick for a long way, keeps its own (o)
    REACH = 40

    def point_on(P, i, j, offs, t):
        """the point and unit tangent at t along the segment i -> j"""
        if len(offs) == 2:
            P0, P1, P2, P3 = ((P[q].x, P[q].y) for q in (i, offs[0], offs[1], j))
            u = 1 - t
            pt = tuple(u ** 3 * P0[q] + 3 * u * u * t * P1[q] + 3 * u * t * t * P2[q] + t ** 3 * P3[q] for q in (0, 1))
            d = tuple(3 * u * u * (P1[q] - P0[q]) + 6 * u * t * (P2[q] - P1[q]) + 3 * t * t * (P3[q] - P2[q])
                      for q in (0, 1))
        else:
            pt = (P[i].x + (P[j].x - P[i].x) * t, P[i].y + (P[j].y - P[i].y) * t)
            d = (P[j].x - P[i].x, P[j].y - P[i].y)
        return pt, unit(*d)

    smooth = {}
    for ci, contour in enumerate(glyph.contours):
        P = contour.points
        n = len(P)
        ons = [i for i, p in enumerate(P) if p.type]
        if len(ons) < 2:
            continue
        sg = signs[ci]
        L = len(ons)
        for idx, i in enumerate(ons):
            samples = []
            for d, (a0, a1) in ((-1, (ons[(idx - 1) % L], i)), (1, (i, ons[(idx + 1) % L]))):
                offs = [(a0 + k) % n for k in range(1, (a1 - a0) % n or n)]
                ln = math.dist((P[a0].x, P[a0].y), (P[a1].x, P[a1].y)) or 1
                for frac in (0.0, min(0.5, REACH / ln)):
                    t = frac if d == 1 else 1 - frac
                    pt, tn = point_on(P, a0, a1, offs, t)
                    if tn:
                        samples.append(across(pt[0], pt[1], -sg * tn[1], sg * tn[0]))
            if samples:
                smooth[(P[i].x, P[i].y)] = k_of(sum(samples) / len(samples))

    def factor(x, y, inward):
        # a junction (e's bar ending in its bowl) is of the heavier stroke
        ks = [d[(x, y)] for d in (fixed, smooth) if (x, y) in d]
        return max(ks) if ks else k_of(across(x, y, *inward))

    rec2 = RecordingPen()
    glyph.draw(rec2)
    slid = []
    out = embolden(rec2, ax, ay, factor, slid, keep_bends=keep_bends)
    # corners between straight edges: where the moved edges meet
    for ci, i, e_in, e_out in corners:
        P = glyph.contours[ci].points
        Q = out.contours[ci].points
        sign = signs[ci]
        x, y = P[i].x, P[i].y
        a0, b0 = P[e_in[0]], P[e_out[1]]
        t_in, t_out = unit(x - a0.x, y - a0.y), unit(b0.x - x, b0.y - y)
        if not t_in or not t_out:
            continue
        cross = t_in[0] * t_out[1] - t_in[1] * t_out[0]
        if abs(cross) < 0.03:
            continue
        k_in = e_in[4] if e_in[4] is not None else 0.0
        k_out = e_out[4] if e_out[4] is not None else 0.0
        n_in, n_out = (t_in[1], -t_in[0]), (t_out[1], -t_out[0])
        d_in = (k_in * abs(n_in[0]) * ax + abs(n_in[1]) * ay) / 2
        d_out = (k_out * abs(n_out[0]) * ax + abs(n_out[1]) * ay) / 2
        ax_, ay_ = sign * n_in[0] * d_in, sign * n_in[1] * d_in
        bx_, by_ = sign * n_out[0] * d_out, sign * n_out[1] * d_out
        wx, wy = bx_ - ax_, by_ - ay_
        u = (wx * t_out[1] - wy * t_out[0]) / cross
        mvx, mvy = ax_ + u * t_in[0], ay_ + u * t_in[1]
        convex = cross * sign < 0
        reach = math.hypot(mvx, mvy)
        if convex:
            cap = 2 * max(d_in, d_out)
        else:
            cap = min(3 * max(d_in, d_out), 0.8 * min(e_in[3], e_out[3]))
        if reach > cap > 0:
            mvx, mvy = mvx * cap / reach, mvy * cap / reach
        Q[i].x, Q[i].y = x + mvx, y + mvy
    # a bracket's slid node: its handle along its edge as the corners left
    # it (the serif's tip moved after the slide: a kink of a few degrees);
    # its other end's along the stroke it leaves
    # (a node between two brackets, each aimed along the other: both
    # handles on the tangent between them)
    aimed = {(ci, h) for ci, _, _, h, _ in slid}
    for ci, q, far, h, reach in slid:
        if not reach or (ci, far) not in aimed or h > far:
            continue
        Q = out.contours[ci].points
        ta, tb = unit(Q[h].x - Q[q].x, Q[h].y - Q[q].y), unit(Q[q].x - Q[far].x, Q[q].y - Q[far].y)
        t = ta and tb and unit(ta[0] + tb[0], ta[1] + tb[1])
        if not t:
            continue
        for k, sgn in ((h, 1), (far, -1)):
            ln = math.dist((Q[q].x, Q[q].y), (Q[k].x, Q[k].y))
            Q[k].x, Q[k].y = Q[q].x + sgn * t[0] * ln, Q[q].y + sgn * t[1] * ln
    for ci, q, far, h, reach in slid:
        Q = out.contours[ci].points
        d = unit(Q[q].x - Q[far].x, Q[q].y - Q[far].y)
        if not d or math.dist((Q[q].x, Q[q].y), (Q[far].x, Q[far].y)) < reach or (reach and (ci, far) in aimed):
            continue
        # the curve runs on from the edge past the node, whichever end it is
        ln = math.dist((Q[q].x, Q[q].y), (Q[h].x, Q[h].y))
        Q[h].x, Q[h].y = Q[q].x + d[0] * ln, Q[q].y + d[1] * ln
    return out


SMOOTH_TURN = 3  # degrees: a node whose handles turn less runs on smoothly (checks.py's smooth)


def embolden_simple(rec, ax, ay, weighted=False, thin=60, thick=160, keep_smooth=False):
    """The earlier emboldening: each point (handles too) moved along the
    normal of the chord between its neighbours. Rounder at corners (it does
    not mitre), but smooth nodes come out a little broken; make_bold.py
    falls back on it where embolden() would close a gap to a slit.
    weighted: ax scaled at each point by the weight of its stroke (none
    below thin, all above thick: embolden_by_weight's contrast), overlaps
    removed first. keep_smooth: a smooth node's handles move with it.
    """
    glyph = ufoLib2.objects.Glyph()
    if weighted:
        glyph = merged_glyph(rec)
        across = stroke_gauge(glyph)
    else:
        rec.replay(glyph.getPen())

    def area(contour):
        pts = [(p.x, p.y) for p in contour.points]
        return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True))

    areas = [area(c) for c in glyph.contours]
    outer = max(areas, key=abs, default=1) > 0
    for contour, a in zip(glyph.contours, areas, strict=True):
        pts = [(p.x, p.y) for p in contour.points]
        sign = 1 if a > 0 else -1
        if (a > 0) != outer:
            sign = -sign
        n = len(pts)
        moved = []
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i - 1], pts[(i + 1) % n]
            length = math.hypot(x1 - x0, y1 - y0) or 1.0
            nx, ny = (y1 - y0) / length, -(x1 - x0) / length
            k = 1.0
            if weighted:
                k = min(1.0, max(0.0, (across(*pts[i], -sign * nx, -sign * ny) - thin) / (thick - thin)))
            moved.append((pts[i][0] + sign * nx * ax * k / 2, pts[i][1] + sign * ny * ay / 2))
        # keep_smooth: a smooth node's handles move with it (handles in line,
        # SMOOTH_TURN; the merge drops the flags): each weighed on its own,
        # off the stroke, they moved less than the node and broke the join
        # (φ's bowl pointed at its extremes)
        P = contour.points
        for i, p in enumerate(P):
            b, f = (i - 1) % n, (i + 1) % n
            if not keep_smooth or not p.type or P[b].type or P[f].type:
                continue
            t_in = math.atan2(pts[i][1] - pts[b][1], pts[i][0] - pts[b][0])
            t_out = math.atan2(pts[f][1] - pts[i][1], pts[f][0] - pts[i][0])
            if abs(math.degrees((t_out - t_in + math.pi) % (2 * math.pi) - math.pi)) > SMOOTH_TURN:
                continue
            dx, dy = moved[i][0] - pts[i][0], moved[i][1] - pts[i][1]
            for h in (b, f):
                moved[h] = (pts[h][0] + dx, pts[h][1] + dy)
        for p, (x, y) in zip(contour.points, moved, strict=True):
            p.x, p.y = x, y
    return glyph


def enlarge(font, source, src_ref, dst_ref, fit=None, stretch=False, stems=None, like=None):
    """The source scaled so that src_ref's strokes and height become
    dst_ref's (ə -> Ә with o -> O): scaled uniformly, then the stems and
    hairlines brought to dst_ref's weight; sidebearings of dst_ref. With
    fit (y0, y1) the source's ink is scaled into that band instead (γ with
    its loop on the baseline for Ɣ). With stems (two letters with a straight
    stem) the first's stem becomes the second's, in place of the round ones.
    With like, the scale and the band are like's (the source like it with a
    part beyond it), its ink's bottom on fit's."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, src_ref), strokes(font, dst_ref)
    if stems:
        s0, s1 = (straight_stem(font, name) for name in stems)
    k = ((b1[3] - b1[1]) - h1) / ((b0[3] - b0[1]) - h0)
    # a capital made a small cap: scaled about the baseline from the cap height
    # to the small caps' (its flat edges on 0 and that height, not on O's
    # overshoots)
    on_baseline = src_ref == "O" and dst_ref.endswith(".sc")
    if on_baseline:
        k = font.lib.get("org.myiadidot.smallcapHeight", 1040) / (font.info.capHeight or 1434)
    if fit:
        sb = ink_bounds(font, like or source)
        k = (fit[1] - fit[0]) / (sb[3] - sb[1])
        if stems:  # the finished letter in the band, hairlines brought to weight
            k = (fit[1] - fit[0] - h1) / (sb[3] - sb[1] - h0)
        b1 = (b1[0], fit[0], b1[2], fit[1])
    rec = DecomposingRecordingPen(font)
    if stretch:
        # stretch: across by the stem ratio, up by the height ratio, so
        # only the hairlines need bringing to weight (thinning the stems of
        # a uniform enlargement leaves slivers where thin strokes slant: Ꞷ)
        kx = s1 / s0
        font[source].draw(TransformPen(rec, (kx, 0, 0, k, 0, 0)))
        glyph = embolden(rec, 0, h1 - k * h0)
    else:
        font[source].draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
        glyph = embolden(rec, s1 - k * s0, h1 - k * h0)
        if on_baseline:  # its flat edges back on the zones
            glyph = rezone(glyph, h1 - k * h0)
    out = RecordingPen()
    glyph.draw(out)
    bp = BoundsPen(None)
    out.replay(bp)
    x0, y0, x1, _ = bp.bounds
    lsb, rsb = b1[0], font[dst_ref].width - b1[2]
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, lsb - x0, 0 if on_baseline else b1[1] - y0)))
    return moved, round(lsb + (x1 - x0) + rsb)


class CubicPen(BasePen):
    """Passes outlines on with quadratic segments made cubic."""

    def __init__(self, out):
        super().__init__(None)
        self.out = out

    def _moveTo(self, p):
        self.out.moveTo(p)

    def _lineTo(self, p):
        self.out.lineTo(p)

    def _curveToOne(self, p1, p2, p3):
        self.out.curveTo(p1, p2, p3)

    def _closePath(self):
        self.out.closePath()

    def _endPath(self):
        self.out.endPath()


def draw_path(font, src, dst, out):
    """Draw a merged outline (a pathops Path or a recording) into dst,
    rounded and in the source's contour direction."""
    from glyph_lint import LEDGE_KEEP, clean

    if isinstance(out, pathops.Path):  # no crumbs of the cuts and merges (glyph_lint)
        out = clean(out, ledges=dst.name not in LEDGE_KEEP)
    rec = RecordingPen()
    # pathops can return a quadratic segment; the font is cubic
    cubic = CubicPen(rec)
    out.draw(cubic) if hasattr(out, "draw") else out.replay(cubic)
    ref = DecomposingRecordingPen(font)
    src.draw(ref)
    pen = RoundingPen(dst.getPen())
    if orientation(rec) != orientation(ref):
        pen = ReverseContourPen(pen)
    rec.replay(pen)


# hooks are taken from the font: the top of f (up), the descender of ȷ (down)
HOOK_SRC = {"up": ("f", 1512), "down": ("uni0237", -628)}
# top or bottom the hook reaches, per band (up) and for descenders (down)
HOOK_TOP = {"x": 1512, "c": 1462, "s": 1062}
HOOK_BOTTOM = {"x": -628, "c": -628, "s": -500}
# retroflex hooks (turning right: ɖ ɭ ɳ ɽ ɻ ʈ) stop short of the descender,
# as in Charis and Libertinus; the left-turning ones (ɲ ɱ ɡ) go all the way
HOOK_BOTTOM_RETROFLEX = {"x": -420, "c": -420, "s": -360}


def smooth_curves(glyph, y0, y1, max_turn=10, tiny=16):
    """glyph (in place) with the shallow kinks between two curves made
    smooth between heights y0 and y1, where fair_joins (corners between
    on-curve points) sees none: a curve shorter than tiny is merged into
    the one after it (the first's handle out, the second's in), then each
    on-curve point there between two curves that turns by at most max_turn
    degrees gets both handles on the bisecting direction, their lengths
    kept (Ƭ: the ring's inner edge split into two curves 3 degrees apart
    where it leaves the bar). Returns how many points changed."""
    changed = 0
    for contour in glyph.contours:
        pts = contour.points
        # merge the short curves: a curve's end P (on-curve) and the next
        # curve's end Q, P within tiny of the curve's start: drop P and its
        # two handles nearest it
        k = 0
        while k < len(pts):
            p = pts[k]
            n = len(pts)
            if (p.type == "curve" and y0 <= p.y <= y1 and pts[(k + 3) % n].type == "curve"
                    and pts[(k - 1) % n].type is None and pts[(k + 1) % n].type is None):
                start = next(pts[(k - j) % n] for j in range(1, 4) if pts[(k - j) % n].type)
                if math.dist((start.x, start.y), (p.x, p.y)) < tiny:
                    # the merged curve leaves start in its handle's direction,
                    # a third of its span out (the short curve's own handle
                    # was a few units long)
                    h, q = pts[(k - 2) % n], pts[(k + 3) % n]
                    d = math.dist((start.x, start.y), (h.x, h.y)) or 1
                    reach = math.dist((start.x, start.y), (q.x, q.y)) / 3
                    h.x = round(start.x + (h.x - start.x) / d * reach)
                    h.y = round(start.y + (h.y - start.y) / d * reach)
                    for i in sorted({(k - 1) % n, k, (k + 1) % n}, reverse=True):
                        del pts[i]
                    changed += 1
                    k = 0
                    continue
            k += 1
        n = len(pts)
        for k, p in enumerate(pts):
            a, b = pts[(k - 1) % n], pts[(k + 1) % n]
            if p.type != "curve" or a.type is not None or b.type is not None or not y0 <= p.y <= y1:
                continue
            ain = math.atan2(p.y - a.y, p.x - a.x)
            aout = math.atan2(b.y - p.y, b.x - p.x)
            turn = (math.degrees(aout - ain) + 180) % 360 - 180
            if not 0 < abs(turn) <= max_turn:
                continue
            mid = ain + math.radians(turn) / 2
            la, lb = math.dist((a.x, a.y), (p.x, p.y)), math.dist((b.x, b.y), (p.x, p.y))
            a.x, a.y = round(p.x - la * math.cos(mid)), round(p.y - la * math.sin(mid))
            b.x, b.y = round(p.x + lb * math.cos(mid)), round(p.y + lb * math.sin(mid))
            p.smooth = True
            changed += 1
    return changed




def fair_joins(glyph, y0, y1, max_turn=25, tiny=16, min_turn=1):
    """glyph (in place) with the shallow corners between y0 and y1 faired:
    where an added piece meets a stroke that runs on at another angle (an
    italic leg leaning into a straight descender, a cut's stub left in
    between), each run of on-curve points there that turn by 1 to max_turn
    degrees is replaced by one curve from the point before to the point
    after, tangent to the outline at both. A side that was a curve keeps its
    handle, a straight one gets a third of the span. Bits shorter than tiny
    (a cut's stubs) go first; corners turning further (serifs, crotches) stay.
    With min_turn 0 a smooth node in the band belongs to the run as well, so
    the curve runs on through it to the next node outside the band.
    Returns how many runs were faired."""

    def turn(a, p, b):
        t = math.degrees(math.atan2(b[1] - p[1], b[0] - p[0]) - math.atan2(p[1] - a[1], p[0] - a[0]))
        return (t + 180) % 360 - 180

    def inside(pt):
        return y0 <= pt[1] <= y1

    def unit(a, b):
        d = math.dist(a, b) or 1
        return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)

    def into(segs, k):
        """the point the outline comes to segs[k]'s end from"""
        end, hs, _ = segs[k]
        frm = hs[-1] if hs else segs[k - 1][0]
        return frm if frm != end else (hs[0] if hs else segs[k - 1][0])

    def out_of(segs, k):
        """the point the outline leaves segs[k]'s end towards"""
        nxt = segs[(k + 1) % len(segs)]
        return nxt[1][0] if nxt[1] else nxt[0]

    faired = 0
    contours = []
    ends = set()  # where the new curves begin and end
    for contour in glyph.contours:
        # as segments [on-curve end, handles (None: a line), smooth], closed
        pts = list(contour.points)
        start = next(i for i, p in enumerate(pts) if p.type)
        segs, handles = [], []
        for p in pts[start + 1:] + pts[:start + 1]:
            if p.type:
                segs.append([(p.x, p.y), handles if p.type == "curve" else None, p.smooth])
                handles = []
            else:
                handles.append((p.x, p.y))
        # bits in the band too short to give a direction (a cut's stubs)
        k = 0
        while k < len(segs) and len(segs) > 3:
            if inside(segs[k][0]) and math.dist(segs[k - 1][0], segs[k][0]) < tiny:
                segs[k - 1][0] = segs[k][0]  # the segment before ends here instead
                del segs[k]
                continue
            k += 1
        n = len(segs)
        bad = [inside(segs[k][0]) and min_turn <= abs(turn(into(segs, k), segs[k][0], out_of(segs, k))) <= max_turn
               for k in range(n)]
        if any(bad) and not all(bad):
            first = next(k for k in range(n) if not bad[k])
            order = [(first + i) % n for i in range(n)]
            out, k = [], 0
            while k < n:
                if not bad[order[k]]:
                    out.append(segs[order[k]])
                    k += 1
                    continue
                run = []
                while k < n and bad[order[k]]:
                    run.append(order[k])
                    k += 1
                # (the first of order is good, so the run ends before it comes round)
                entry = segs[(run[0] - 1) % n][0]
                exit_k = order[k % n]
                lead, trail = segs[run[0]], segs[exit_k]
                exit_ = trail[0]
                span = math.dist(entry, exit_)
                if lead[1]:
                    h1 = lead[1][0]
                else:
                    u = unit(entry, lead[0])
                    h1 = (entry[0] + u[0] * span / 3, entry[1] + u[1] * span / 3)
                if trail[1]:
                    h2 = trail[1][-1]
                else:
                    u = unit(segs[run[-1]][0], exit_)
                    h2 = (exit_[0] - u[0] * span / 3, exit_[1] - u[1] * span / 3)
                faired += 1
                ends.update((entry, exit_))
                if k < n:
                    out.append([exit_, [h1, h2], trail[2]])
                    k += 1
                else:
                    out[0] = [exit_, [h1, h2], trail[2]]
            segs = out
        contours.append(segs)
    if faired:
        glyph.clearContours()
        pen = glyph.getPointPen()
        for segs in contours:
            # a new curve's ends smooth where the outline runs on through them
            # (emboldening keeps a smooth node smooth, a corner a corner)
            for k, seg in enumerate(segs):
                if seg[0] in ends and not seg[2]:
                    seg[2] = abs(turn(into(segs, k), seg[0], out_of(segs, k))) < 1
            pen.beginPath()
            for end, hs, smooth in segs:
                for h in hs or ():
                    pen.addPoint(tuple(round(v) for v in h))
                pen.addPoint(tuple(round(v) for v in end), "curve" if hs else "line", smooth)
            pen.endPath()
    return faired


def hook_path(font, source, band, kind, pick, cut, left, right, cuts=()):
    """The letter with a stem's end replaced by a hook from the font: kind
    'up-right' (ɓ: the top of f), 'up-left' (Ɓ: f mirrored), 'down-left'
    (ɲ: the descender of ȷ) or 'down-right' (ʈ: ȷ mirrored). The stem
    (first/last at mid height) loses its ink beyond cut, from left of it to
    right of it; the hook is scaled by the stem ratio to reach the band's
    top (or the descender). cuts: boxes also taken from the letter (an
    italic's exit stroke above the cut)."""
    up = kind.startswith("up")
    mirror = kind in ("up-left", "down-right")  # f hooks right, ȷ left
    hsrc, hend = HOOK_SRC["up" if up else "down"]
    probe = 300 if not up else max(cut - 150, 400)
    stems = stems_at(font, source, probe)
    # not the end of a stroke the probe grazes (an italic's exit stroke)
    stems = [s for s in stems if s[1] - s[0] >= 0.5 * max(t[1] - t[0] for t in stems)]
    ta, tb = stems[0] if pick == "first" else stems[-1]
    # f: stem first, ball to the right; ȷ: stem last, ball to the left
    hs = stems_at(font, hsrc, 900)[0] if up else stems_at(font, hsrc, -200)[-1]
    k = (tb - ta) / (hs[1] - hs[0])
    if up:
        # start the hook where f's stem is still straight (below 1000)
        cut = min(cut, HOOK_TOP[band] - (hend - 1000) * k)
        reach = HOOK_TOP[band] - cut
        # never below 900: f's crossbar ends at 884 (the hook is then shorter)
        s0, s1 = max(hend - reach / k, 900), BIG
    else:
        reach = cut - (HOOK_BOTTOM_RETROFLEX if kind == "down-right" else HOOK_BOTTOM)[band]
        s0, s1 = -BIG, hend + reach / k
    piece = path_op(to_path(font, font[hsrc]), rect_path(-BIG, s0, BIG, s1), "INTERSECTION")
    # the hook's stem where it meets the letter, and the letter's stem at
    # the cut: the hook is scaled across to that width exactly and put on
    # its edges, so the stroke runs on without a step
    js = stems_at(font, hsrc, s0 + 2)[0] if up else stems_at(font, hsrc, s1 - 2)[-1]
    # only ink over the stem counts (above a letter's x-height the cut may
    # meet nothing but a bowl's overshoot: ƥ); none there, the stem itself
    at_cut = [s for s in stems_at(font, source, cut - 2 if up else cut + 2) if s[1] > ta and s[0] < tb]
    ca, cb = (min(at_cut, key=lambda s: abs((s[0] + s[1]) / 2 - (ta + tb) / 2)) if at_cut
              else (ta, tb))
    sx = (cb - ca) / (js[1] - js[0])
    if mirror:
        sx, tx = -sx, ca + sx * js[1]
    else:
        tx = ca - sx * js[0]
    ty = cut - k * (s0 if up else s1)
    rec = RecordingPen()
    piece.draw(TransformPen(rec, (sx, 0, 0, k, tx, ty)))
    piece = to_path(None, rec=rec)
    if mirror:
        piece = path_op(piece, piece, "UNION")  # fix the reversed winding
    cut_box = (rect_path(ta - left, cut, tb + right, BIG) if up
               else rect_path(ta - left, -BIG, tb + right, cut))
    letter = path_op(to_path(font, font[source]), cut_box, "DIFFERENCE")
    for box in cuts:
        letter = path_op(letter, rect_path(*box), "DIFFERENCE")
    return path_op(letter, piece, "UNION"), piece.bounds


def ezh(font, source, band, ym, bottom, right):
    """Ʒ ʒ: the top bar and diagonal of Z/z down to ym, and the lower bowl
    of the figure 3 from its middle tongue hung on the end of the diagonal,
    scaled to reach down to bottom and across to right (as wide as the bar,
    as in Charis), its strokes brought back to the figure's weight."""
    top = path_op(to_path(font, font[source]), rect_path(-BIG, ym, BIG, BIG), "INTERSECTION")
    tongue_y = 760
    tx0 = stems_at(font, "three", tongue_y)[0][0]
    bowl = path_op(to_path(font, font["three"]), rect_path(-BIG, -BIG, BIG, tongue_y + 30),
                   "INTERSECTION")
    b = ink_bounds(font, "three")
    dx = stems_at(font, source, ym)[-1][0]
    kx = (right - dx) / (b[2] - tx0)
    ky = (ym - bottom) / (tongue_y - b[1])
    stem = max(e - a for a, e in stems_at(font, "three", 350))  # its upright side
    hair = vertical_runs(font, "three", 530)[0]
    hair = hair[1] - hair[0]  # its foot
    rec = RecordingPen()
    bowl.draw(TransformPen(rec, (kx, 0, 0, ky, dx - kx * tx0, ym - ky * tongue_y)))
    out = RecordingPen()
    embolden(rec, stem * (1 - kx), hair * (1 - ky)).draw(out)
    joined = path_op(top, to_path(None, rec=out), "UNION")
    # cut flat across the 3's waist, the bowl's top stands as a shelf beside
    # the diagonal: cut away above a line from where the diagonal's edge
    # meets it down to where the bowl's own top edge falls away, so the
    # diagonal meets the bowl in a crotch
    def top_at(x):
        """the top of the ink at x, looked at up to just above the cut"""
        cut = path_op(joined, rect_path(x - 0.5, -BIG, x + 0.5, ym + 120), "INTERSECTION")
        tops = [c.bounds[3] for c in cut.contours if c.bounds[1] < ym]
        return max(tops) if tops else None

    def right_at(y):
        return max(e for _, e in stems_at(font, source, y))

    x = right_at(ym + 1) + 2
    while x < right and (top_at(x) or 0) >= ym + 119:  # still under the diagonal
        x += 2
    shelf = top_at(x)
    while x < right and (top_at(x) or 0) > shelf - 4:  # along the shelf (and the stub on it)
        x += 2
    bx, by = x + 6, top_at(x + 6)
    if by is None or x >= right:
        return joined
    ay = shelf
    ax = right_at(ay - 1)
    h = 60  # the shelf and the stub of the 3's upper bowl on it
    if right_at(ay + h) >= bx:
        return joined
    cut = RecordingPen()
    cut.moveTo((ax, ay))
    cut.lineTo((bx, by))
    cut.lineTo((bx, ay + h))
    cut.lineTo((right_at(ay + h), ay + h))
    cut.closePath()
    return path_op(joined, to_path(None, rec=cut), "DIFFERENCE")


def esh(font, source, band, bottom_model):
    """ʃ: the top of f (no crossbar), its stem run down, and the descender
    of ȷ at the bottom."""
    top = path_op(to_path(font, font[source]), rect_path(-BIG, 900, BIG, BIG), "INTERSECTION")
    fa, fb = stems_at(font, source, 920)[0]
    ja, _ = stems_at(font, bottom_model, -100)[-1]
    tail = path_op(to_path(font, font[bottom_model]), rect_path(-BIG, -BIG, BIG, -80), "INTERSECTION")
    tail = shifted(tail, fa - ja)
    stem = rect_path(fa, -100, fb, 920)
    out = path_op(path_op(top, stem, "UNION"), tail, "UNION")
    return shifted(out, 40 - out.bounds[0])


def superior(font, source, ref="zerosuperior"):
    """A modifier letter (ʰ ⁿ ᵃ): the letter at the size and weight of the
    superior figures (0 -> ⁰ gives the scale and the stroke changes), on
    their baseline; with ref "zeroinferior" a subscript (₊)."""
    (b0, s0, h0), (b1, s1, h1) = strokes(font, "zero"), strokes(font, ref)
    k = ((b1[3] - b1[1]) - h1) / ((b0[3] - b0[1]) - h0)
    ax, ay = s1 - k * s0, h1 - k * h0
    rec = DecomposingRecordingPen(font)
    font[source].draw(TransformPen(rec, (k, 0, 0, k, 0, 0)))
    out = RecordingPen()
    embolden(rec, ax, ay).draw(out)
    moved = RecordingPen()
    out.replay(TransformPen(moved, (1, 0, 0, 1, ax / 2, b1[1] - (k * b0[1] - ay / 2))))
    return moved, round(k * font[source].width + ax)


def attach(font, source, cuts, pieces):
    """The letter minus the boxes in cuts, merged with pieces: each a part
    of a glyph (name, clip box, or boxes: the first less the others) whose
    point (px, py) goes to (x, y),
    scaled (sx, sy) and optionally turned (degrees, a fifth value); a negative
    sx mirrors. For hooks that need placing by hand (Ɲ, ₪, Ϗ); "rect" pieces
    are boxes, "line" pieces straight strokes, "poly" pieces polygons (with
    curves), "curl" pieces drawn hooks; a "counter" piece (a box) clears
    the letter's own counters within it of the pieces before it."""
    stems, hairs = font.lib.get(STROKE_KEY, (1, 1))

    def thick(v):
        """A drawn thickness in this font's weight: a stem's (100 and up) or a hairline's."""
        return v * (stems if v >= 100 else hairs)

    out = to_path(font, font[source])
    for box in cuts:
        out = path_op(out, rect_path(*box), "DIFFERENCE")
    for name, clip, (px, py), (sx, sy, x, y, *turn) in pieces:
        if name == "rect":  # a plain box
            part = rect_path(*clip)
        elif name == "line":  # a straight stroke: ((x0, y0), (x1, y1), thickness)
            rec = RecordingPen()
            stroke(rec, clip[0], clip[1], thick(clip[2]))
            part = to_path(None, rec=rec)
        elif name == "counter":  # the letter's own counters within the box,
            # cleared again of what the pieces before brought into them
            own = counters(font, font[source])
            for c in own:
                out = path_op(out, path_op(c, rect_path(*clip), "INTERSECTION"), "DIFFERENCE")
            # one come out whole is drawn as the letter draws it (the merges
            # split its curves where the pieces crossed it: kinks, crumbs)
            redrawn = pathops.Path()
            for contour in out.contours:
                same = next((c for c in own if all(abs(u - v) < 1 for u, v in zip(c.bounds, contour.bounds))
                             and abs(abs(c.area) - abs(contour.area)) < 0.001 * abs(c.area)), None)
                if same is not None:
                    turn = same.clockwise != contour.clockwise
                    contour = pathops.Path()
                    same.draw(contour.getPen())
                    if turn:  # as the result winds it
                        contour.reverse()
                redrawn.addPath(contour)
            out = redrawn
            continue
        elif name == "poly":  # a filled polygon: its points (a stroke tapering);
            # a triple of points is a curve to the last (two handles)
            rec = RecordingPen()
            rec.moveTo(clip[0])
            for pt in clip[1:]:
                rec.curveTo(*pt) if isinstance(pt[0], (tuple, list)) else rec.lineTo(pt)
            rec.closePath()
            part = to_path(None, rec=rec)
        elif name == "curl":  # a drawn hook ending in a ball: curl's arguments,
            # and optionally "cuts", boxes taken from it (so the ring's lead
            # does not stand out past the stroke it leaves)
            args = dict(clip)
            boxes = args.pop("cuts", ())
            if (stems, hairs) != (1, 1):
                if args.get("t"):
                    args["t"] = tuple(thick(v) for v in args["t"])
                if args.get("at", ("",))[0] == "pt" and len(args["at"]) > 3:
                    args["at"] = (*args["at"][:3], thick(args["at"][3]), *args["at"][4:])
                if args.get("ball") not in (None, "end"):
                    args["ball"] = args["ball"] * stems
            if args.get("ball") is None:  # a terminal ball as the letter's case draws them
                r = args["r"]
                args["ball"] = min(ball_for(font, source), BALL_OF_RADIUS * (min(r) if isinstance(r, (tuple, list)) else r))
            part = curl(font, "space", [], **args)
            for box in boxes:
                part = path_op(part, rect_path(*box), "DIFFERENCE")
        else:
            # a box, or boxes: the first kept, the others cut out of it (one
            # piece whose outline is the glyph's own, no seam to join)
            keep, *holes = clip if isinstance(clip[0], (tuple, list)) else (clip,)
            part = path_op(to_path(font, font[name]), rect_path(*keep), "INTERSECTION")
            for box in holes:
                part = path_op(part, rect_path(*box), "DIFFERENCE")
        rec = RecordingPen()
        # scaled, then turned by turn[0] degrees (counter-clockwise) about (px, py)
        t = Transform().translate(x, y).rotate(math.radians(turn[0] if turn else 0))
        part.draw(TransformPen(rec, t.scale(sx, sy).translate(-px, -py)))
        if turn and turn[0]:  # turned, its curves' extremes move off their points (Ϗ's tail)
            rec, turned = RecordingPen(), rec
            with_extremes(turned, rec, round_points=False)
        out = path_op(out, path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG),
                                   "INTERSECTION"), "UNION")
    return out


def _run_at(font, name, y, pick):
    runs = stems_at(font, name, y)
    return runs[0] if pick == "first" else runs[-1] if pick == "last" else runs[pick]


def _perpendicular(font, name, y, pick, dy=20):
    """Width of a stroke across its direction, from horizontal runs at y."""
    a, b = _run_at(font, name, y, pick)
    a2, b2 = _run_at(font, name, y + dy, pick)
    slope = ((a2 + b2) - (a + b)) / 2 / dy
    return (b - a) / math.hypot(1, slope)


def graft(font, source, cuts, piece, py, junction, clip=None, mirror=False, pick="first"):
    """The letter minus cuts, with a hook from another glyph (piece, its ink
    above py, within clip) scaled so its stroke at py is as thick, across
    the stroke, as the letter's where they meet. junction is ('y', y, pick):
    the piece's run at py goes onto the letter's run at y, edge on edge (a
    stem or arm running on: ʋ ƴ Ƴ), or ('x', x): its middle onto the middle
    of the letter's topmost ink at x (a hook rising from an arc: Ƈ ƈ Ɠ)."""
    pp = _perpendicular(font, piece, py, pick)
    if junction[0] == "y":
        _, ly, lpick = junction
        lp = _perpendicular(font, source, ly - 20, lpick)
    else:
        jx = junction[1]
        r0, r1 = vertical_runs(font, source, jx)[-1]
        q0, q1 = vertical_runs(font, source, jx + 20)[-1]
        lp = (r1 - r0) / math.hypot(1, ((q0 + q1) - (r0 + r1)) / 40)
    k = lp / pp
    box = clip or (-BIG, py, BIG, BIG)
    part = path_op(to_path(font, font[piece]),
                   rect_path(box[0], max(box[1], py - 2 / k), box[2], box[3]), "INTERSECTION")
    pa, pb = _run_at(font, piece, py, pick)
    sx = -k if mirror else k
    if junction[0] == "y":
        la, _ = _run_at(font, source, ly, lpick)
        tx = la - sx * (pb if mirror else pa)
        ty = ly - k * py
    else:
        tx = jx - sx * (pa + pb) / 2
        ty = (r0 + r1) / 2 - k * py
    rec = RecordingPen()
    part.draw(TransformPen(rec, (sx, 0, 0, k, tx, ty)))
    part = to_path(None, rec=rec)
    part = path_op(part, rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")  # winding
    out = to_path(font, font[source])
    for b in cuts:
        out = path_op(out, rect_path(*b), "DIFFERENCE")
    return path_op(out, part, "UNION")


def _ellipse(cx, cy, rx, ry):
    k = 0.5523
    rec = RecordingPen()
    rec.moveTo((cx + rx, cy))
    rec.curveTo((cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry))
    rec.curveTo((cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy))
    rec.curveTo((cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry))
    rec.curveTo((cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy))
    rec.closePath()
    return to_path(None, rec=rec)


# a terminal ball's radius against its case's stem (l, I, l.sc), as the
# drawn letters have them: c a y 0.53, J 0.51, j.sc 0.49 (2026-10-27)
BALL_OF_STEM = 0.52
# and no more than this of the curl's smallest radius: the recipes keep the
# Regular's radii, a Bold ball at its stem's size ran into the stroke it
# hangs from (Ƙ ʐ: lint faults); the Regular's largest is Ʈ's 0.77
BALL_OF_RADIUS = 0.77


def ball_for(font, source):
    """The radius of a terminal ball on the letter source, at this font's
    weight: BALL_OF_STEM of its case's stem."""
    g = font[source] if source in font else None
    if source.endswith(".sc"):
        ref = "l.sc"
    elif g is not None and g.unicode and unicodedata.category(chr(g.unicode)) == "Lu":
        ref = "I"
    else:
        ref = "l"
    return BALL_OF_STEM * strokes(font, ref)[1]


def curl(font, source, cuts, at, dir, turn, r, sweep, ball, t=None, lead=3):
    """The letter minus cuts, with a hook drawn as part of an elliptical
    ring ending in a ball: it leaves the letter's stroke at `at` (('y', y,
    pick): the run at height y; ('x', x) / ('xb', x): the topmost /
    bottommost ink at x; ('pt', x, y, width)) going in
    direction dir (degrees; 90 = up), turning cw or ccw through sweep
    degrees on a centre line of radii r (one number: a circle). The ring is
    t thick: (across vertical parts, across horizontal parts), by default
    the stroke's own width where it meets the letter, so the stroke runs on
    at its weight; the ball (radius) sits inside the end, flush with the
    outer edge, as on f; None: as the letter's case draws them (ball_for);
    "end": a round cap touching both the ring's edges, the outer at the
    end, the ring cut between where it touches (ƴ: a ball a few units
    wider than the end stood into the counter in a dent; one across the
    end from the centre crossed its edges, wobbling)."""
    a, b = (r, r) if not isinstance(r, (tuple, list)) else r
    if ball is None:
        ball = min(ball_for(font, source), BALL_OF_RADIUS * min(a, b))
    if at[0] == "y":
        _, y, pick = at
        ra, rb_ = _run_at(font, source, y, pick)
        px, py = (ra + rb_) / 2, y
        width = _perpendicular(font, source, y - 20, pick)
    elif at[0] == "pt":  # a given point and stroke width (˞)
        _, px, py, width = at
    else:  # 'x': the topmost ink at x, 'xb': the bottommost
        x = at[1]
        i = 0 if at[0] == "xb" else -1
        r0, r1 = vertical_runs(font, source, x)[i]
        q0, q1 = vertical_runs(font, source, x + 20)[i]
        px, py = x, (r0 + r1) / 2
        width = (r1 - r0) / math.hypot(1, ((q0 + q1) - (r0 + r1)) / 40)
    tv, th = t if t else (width, width)
    if at[0] == "y" and dir == 90:
        tv = rb_ - ra if not t else tv  # a vertical stem: its full width
    sign = -1 if turn == "cw" else 1
    # the centre lies to the side the curl turns to, across the direction
    d = math.radians(dir)
    nx, ny = -math.sin(d) * sign, math.cos(d) * sign
    start = math.degrees(math.atan2(-ny, -nx))  # from the centre to the start
    sa = math.radians(start)
    cx, cy = px - a * math.cos(sa), py - b * math.sin(sa)
    ring = path_op(_ellipse(cx, cy, a + tv / 2, b + th / 2),
                   _ellipse(cx, cy, a - tv / 2, b - th / 2), "DIFFERENCE")
    # the part swept, from just before the start (into the letter's stroke)
    # lead: degrees the ring starts back inside the letter's stroke, so a
    # stroke cut across at an angle to the ring still flows into it (Ϗ)
    past = 30 if ball == "end" else 0  # (cut again where the end's cap touches, below)
    angles = [start - sign * lead + sign * (sweep + lead + past) * i / 24 for i in range(25)]
    pts = [(cx, cy)] + [(cx + 4 * (a + tv) * math.cos(math.radians(g)),
                         cy + 4 * (b + th) * math.sin(math.radians(g))) for g in angles]
    rec = RecordingPen()
    rec.moveTo(pts[0])
    for q in pts[1:]:
        rec.lineTo(q)
    rec.closePath()
    wedge = path_op(to_path(None, rec=rec), rect_path(-BIG, -BIG, BIG, BIG), "INTERSECTION")
    hook = path_op(ring, wedge, "INTERSECTION")
    end = math.radians(start + sign * sweep)
    if ball == "end":
        # a cap touching both edges: tangent to the outer edge at the end,
        # its radius where it touches the inner edge too (along the outer
        # edge's normal); the ring cut between the two touching points
        A, B = a + tv / 2, b + th / 2
        ox, oy = cx + A * math.cos(end), cy + B * math.sin(end)
        nx, ny = -math.cos(end) / A, -math.sin(end) / B
        nl = math.hypot(nx, ny)
        nx, ny = nx / nl, ny / nl
        inner = [(cx + (a - tv / 2) * math.cos(end + math.radians(d / 20)),
                  cy + (b - th / 2) * math.sin(end + math.radians(d / 20))) for d in range(-1800, 1801)]

        def gap(r):
            x, y = ox + r * nx, oy + r * ny
            return min(math.hypot(x - qx, y - qy) for qx, qy in inner) - r
        lo, hi = 0.0, max(tv, th)
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if gap(mid) > 0 else (lo, mid)
        ball = (lo + hi) / 2
        bx, by = ox + ball * nx, oy + ball * ny
        tx, ty = min(inner, key=lambda q: math.hypot(q[0] - bx, q[1] - by))
        # (the half-plane past the chord, on the far side from the ring
        # before the end, within the end's reach)
        ux, uy = tx - ox, ty - oy
        ul = math.hypot(ux, uy)
        ux, uy = ux / ul, uy / ul
        back = end - sign * math.radians(20)
        px, py = cx + a * math.cos(back), cy + b * math.sin(back)
        mx, my = -uy, ux
        if (px - ox) * mx + (py - oy) * my > 0:
            mx, my = -mx, -my
        reach = 2 * max(tv, th)
        rec = RecordingPen()
        rec.moveTo((ox - ux * reach, oy - uy * reach))
        rec.lineTo((tx + ux * reach, ty + uy * reach))
        rec.lineTo((tx + ux * reach + mx * reach, ty + uy * reach + my * reach))
        rec.lineTo((ox - ux * reach + mx * reach, oy - uy * reach + my * reach))
        rec.closePath()
        near = RecordingPen()  # (and about the end only: it crossed the ring's start)
        near.moveTo((cx, cy))
        for i in range(13):
            g = end + sign * math.radians(-25 + (past + 30) * i / 12)
            near.lineTo((cx + 4 * (a + tv) * math.cos(g), cy + 4 * (b + th) * math.sin(g)))
        near.closePath()
        cut = path_op(to_path(None, rec=rec), path_op(to_path(None, rec=near), rect_path(-BIG, -BIG, BIG, BIG),
                                                       "INTERSECTION"), "INTERSECTION")
        hook = path_op(hook, cut, "DIFFERENCE")
    else:
        bx = cx + (a + tv / 2 - ball) * math.cos(end)
        by = cy + (b + th / 2 - ball) * math.sin(end)
    hook = path_op(hook, _ellipse(bx, by, ball, ball), "UNION")
    out = to_path(font, font[source])
    for box in cuts:
        out = path_op(out, rect_path(*box), "DIFFERENCE")
    return path_op(out, hook, "UNION")


def lower(font, source, depth):
    """The letter right of its first stem (a bowl, a leg) moved down by
    depth, the stem and its foot serif staying: Ʀ from R."""
    _, b = stems_at(font, source, 500)[0]
    # the foot serif: as far right as the first run reaches at the baseline,
    # as high as that run is wider than the stem
    x1 = stems_at(font, source, 10)[0][1]
    top = 10
    while top < 300 and stems_at(font, source, top)[0][1] > b + 2:
        top += 2
    whole = to_path(font, font[source])
    region = path_op(rect_path(b, top, BIG, BIG), rect_path(x1, -BIG, BIG, top), "UNION")
    moved = shifted(path_op(whole, region, "INTERSECTION"), 0, -depth)
    return path_op(path_op(whole, region, "DIFFERENCE"), moved, "UNION")


def descend(font, source, band, model, pick=None):
    """A v with a stem down to the descender (ү): the stem and foot serif
    of the model's descender (p) under the vertex; with pick (first/last)
    under that stem instead (ɰ)."""
    if pick:
        stems = stems_at(font, source, 300)
        vx = sum(stems[0] if pick == "first" else stems[-1]) / 2
    else:
        runs = stems_at(font, source, 26)  # a rounded bottom (the Italic's v) is cut twice
        vx = (runs[0][0] + runs[-1][1]) / 2
    ma, mb = stems_at(font, model, -200)[0]
    piece = path_op(to_path(font, font[model]), rect_path(-BIG, -BIG, BIG, -60), "INTERSECTION")
    # up into the vertex, not into the counter above a rounded bottom; with
    # pick, up to where the stem was measured
    top = 300 if pick else 120
    while not pick and top > 0 and len(stems_at(font, source, top)) > 1:
        top -= 10
    stem = rect_path(ma, -80, mb, top)
    piece = shifted(path_op(piece, stem, "UNION"), vx - (ma + mb) / 2)
    return path_op(to_path(font, font[source]), piece, "UNION")


def mirrored_anchors(src, dst, width):
    for a in src.anchors:
        if a.name in KEEP_ANCHORS:
            dst.appendAnchor({"name": a.name, "x": width - a.x, "y": a.y})


def build(font, ch, op, source, band, name=None):
    src = font[source]
    small_cap = variant(ch) == ".sc"
    g = font.newGlyph(name or glyph_name(ch))
    if not variant(ch):
        g.unicodes = [ord(ch)]
    w = src.width
    if op == "alias":
        g.width = w
        g.getPen().addComponent(source, (1, 0, 0, 1, 0, 0))
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "turn":
        g.width = w
        cy = band_middle(font, band)
        draw_transformed(font, src, g, (-1, 0, 0, -1, w, 2 * cy), reverse=False)
        if band != "x" or source not in ("h", "y"):  # ascender <-> descender: no anchor fits
            mirrored_anchors(src, g, w)
    elif op == "mirror":
        g.width = w
        draw_transformed(font, src, g, (-1, 0, 0, 1, w, 0), reverse=True)
        mirrored_anchors(src, g, w)
    elif op == "upright":
        # a sloped outline (∂) set upright about half the x-height, between
        # the sidebearings of the model letter (band: angle, model)
        angle, model = band
        s = math.tan(math.radians(angle))
        rec, sheared = DecomposingRecordingPen(font), RecordingPen()
        src.draw(rec)
        rec.replay(TransformPen(sheared, (1, 0, -s, 1, s * font.info.xHeight / 2, 0)))
        with_extremes(sheared, g.getPen())
        x0, _, x1, _ = ink_bounds(font, g.name)
        m0, _, m1, _ = ink_bounds(font, model)
        dx = round(m0 - x0)
        for c in g.contours:
            for pt in c.points:
                pt.x += dx
        g.width = round(x1 + dx + font[model].width - m1)
    elif op == "flip":
        g.width = w
        cy = band_middle(font, band)
        draw_transformed(font, src, g, (1, 0, 0, -1, 0, 2 * cy), reverse=True)
    elif op == "nodot":
        g.width = w
        rec = DecomposingRecordingPen(font)
        src.draw(rec)
        tmp = ufoLib2.objects.Glyph()
        rec.replay(tmp.getPen())
        lowest = min(tmp.contours, key=lambda c: min(p.y for p in c.points))
        rest = [c for c in tmp.contours if c is not lowest]
        # the stem stopped above the dot: run its foot down to the baseline
        foot = min(p.y for c in rest for p in c.points)
        for c in rest:
            for pt in c.points:
                if pt.y == foot:
                    pt.y = 0
            c.drawPoints(g.getPointPen())
    elif op == "twin":
        # ɯ Ɯ from u U: a second copy whose first stem lies on the first's
        # last stem; the first loses what is right of that stem (its foot
        # spur, the right half of its serif), the copy brings its own
        # band: the height to find the stems at, or (height, glyph of the
        # copy): ɰ is u and ɥ
        y, other = band if isinstance(band, tuple) else (band, source)
        stems = stems_at(font, source, y)
        dx = stems[-1][1] - stems[0][1]
        first = path_op(to_path(font, src), rect_path(stems[-1][1], -BIG, BIG, BIG), "DIFFERENCE")
        out = path_op(first, shifted(to_path(font, font[other]), dx), "UNION")
        w = font[other].width
        g.width = round(w + dx)
        draw_path(font, src, g, out)
    elif op == "double":
        dx = w + (band or 0)  # band: the second one nearer by that much
        g.width = w + dx
        pen = g.getPen()
        pen.addComponent(source, (1, 0, 0, 1, 0, 0))
        pen.addComponent(source, (1, 0, 0, 1, dx, 0))
    elif op in SHAPES:
        g.width = w
        sband, *rest = band
        draw_merged(font, src, g, SHAPES[op](font, source, sband, tuple(rest)))
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "tail":
        sband, mode = band
        out, right = tail_path(font, source, sband, mode)
        g.width = max(w, round(right))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "hook":
        sband, kind, pick, cut, left, right, *cuts = band
        out, (_, _, x1, _) = hook_path(font, source, sband, kind, pick, cut, left, right, *cuts)
        rsb = w - ink_bounds(font, source)[2]
        g.width = max(w, round(x1 + rsb))
        draw_path(font, src, g, out)
        for a in src.anchors:
            g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "lower":
        _band, depth = band
        g.width = w
        draw_path(font, src, g, lower(font, source, depth))
        for a in src.anchors:
            if a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "unserif":
        g.width = w
        draw_path(font, src, g, unserif_path(font, source))
        for a in src.anchors:
            if a.name != "Horn":
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
        x, y = stem_horn_anchor(font, g.name)
        g.appendAnchor({"name": "Horn", "x": x, "y": y})
    elif op == "descend":
        sband, model, *pick = band
        g.width = w
        draw_path(font, src, g, descend(font, source, sband, model, *pick))
        for a in src.anchors:
            if a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op in ("attach", "graft", "curl"):
        _band, cuts, pieces, *width = band
        if op == "graft":
            out = graft(font, source, cuts, **pieces)
        elif op == "curl":
            out = curl(font, source, cuts, **pieces)
        else:
            out = attach(font, source, cuts, pieces)
        if width:
            g.width = width[0]
        else:
            g.width = max(w, round(out.bounds[2] + w - ink_bounds(font, source)[2]))
        anchors = [(a.name, a.x, a.y) for a in src.anchors]
        if ch in NARROW:
            factor, above = NARROW[ch]
            x0 = stems_at(font, source, band_middle(font, _band))[-1][0]
            left = out.bounds[0]
            out = narrowed(out, x0, factor)
            dx = left - out.bounds[0]
            out = shifted(out, dx)
            g.width += round(dx)
            tops = ("Top", "Acute", "Grave", "Dotaccent")
            anchors = ([(a.name, a.x, a.y) for a in font[above].anchors if a.name in tops]
                       + [a for a in anchors if a[0] not in tops])
            anchors = [(n, round((x0 - (x0 - x) * factor if x < x0 else x) + dx), y) for n, x, y in anchors]
        draw_path(font, src, g, out)
        for n, x, y in anchors:
            g.appendAnchor({"name": n, "x": x, "y": y})
    elif op in ("ezh", "esh"):
        out = (ezh(font, source, *band) if op == "ezh" else esh(font, source, *band))
        rsb = w - ink_bounds(font, source)[2]
        g.width = max(w, round(out.bounds[2] + rsb)) if op == "ezh" else round(out.bounds[2] + 40)
        draw_path(font, src, g, out)
        for a in src.anchors:
            if op == "ezh" and a.name not in ("Bottom", "DotBelow", "Cedilla"):
                g.appendAnchor({"name": a.name, "x": a.x, "y": a.y})
    elif op == "superior":
        out, g.width = superior(font, source, *([band] if band else []))
        draw_path(font, src, g, out)
    elif op in ("enlarge", "stretch"):
        src_ref, dst_ref, *rest = band
        fit = tuple(v for v in rest if not isinstance(v, str)) or None
        stems = tuple(v for v in rest if isinstance(v, str)) or None
        out, g.width = enlarge(font, source, src_ref, dst_ref, fit,
                               stretch=op == "stretch", stems=stems, like=ENLARGE_LIKE.get(ch))
        draw_path(font, src, g, out)
        ref = font[dst_ref]
        # a letter taller than dst_ref (ʒ.sc on the baseline, from Ʒ with its
        # tail below) takes its accents as far above its own top
        rise = ink_bounds(font, g.name)[3] - ink_bounds(font, dst_ref)[3]
        rise = rise if rise > 40 else 0
        for a in ref.anchors:
            g.appendAnchor({"name": a.name, "x": round(a.x * g.width / ref.width),
                            "y": a.y + (rise if a.y > 0 else 0)})
    else:
        raise ValueError(op)
    if ch in SMOOTH_CURVES:
        smooth_curves(g, *SMOOTH_CURVES[ch])
    if small_cap:
        # reviewed with the small caps; smallcaps.py never redrafts it
        g.lib[SMALLCAP_DRAFT_KEY] = True
        g.lib[DERIVED_KEY] = True
    else:
        g.lib[DRAFT_KEY] = True
    font.lib.setdefault("public.openTypeCategories", {})[g.name] = "base"
    if g.name not in font.glyphOrder:
        order = list(font.glyphOrder)
        # a localized form after its letter (and the letter's other variants)
        stem = g.name.split(".")[0] if variant(ch) and not small_cap else None
        if stem in order:
            at = order.index(stem) + 1
            while at < len(order) and order[at].split(".")[0] == stem:
                at += 1
            order.insert(at, g.name)
        else:
            order.append(g.name)
        font.glyphOrder = order
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("chars", nargs="*")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    # characters, and small caps given whole ("ɔ.sc")
    only = set()
    for arg in args.chars:
        if variant(arg):
            only.add(arg)
        else:
            only.update(arg)

    font = ufoLib2.Font.open(args.ufo)
    from built_from import KEY as BUILT_KEY
    from built_from import Tracker, stamp

    # built on the spacing the recipes were tuned on, then cut again
    # (scripts/respace.py): scaled letters (small caps) keep the cut whole
    from respace import CUT_KEY, classifier, respace, sidebearings, undo

    done = font.lib.get(CUT_KEY)
    undo(font)
    cmap = {u: g.name for g in font for u in g.unicodes}
    made, kept, built = [], [], []
    bases = {}  # glyph: the glyphs its recipe read (built_from.py)
    aliases = []  # kept aliases: (glyph, source)

    def probe(ch, op, source, band, name):
        """What the recipe of an existing glyph reads, built aside and dropped."""
        tmp, order = f"_probe.{name}", font.glyphOrder
        categories = dict(font.lib.get("public.openTypeCategories", {}))
        tracker = Tracker(font)
        try:
            build(tracker, ch, op, source, band, tmp)
            return tracker.read - {tmp}
        except Exception:  # noqa: BLE001 (a recipe that no longer runs on it: no stamp)
            return None
        finally:
            if tmp in font:
                del font[tmp]
            font.glyphOrder = order
            font.lib["public.openTypeCategories"] = categories

    for ch, op, source, band in RECIPES:
        if only and ch not in only:
            continue
        if len(source) == 1 or (variant(source) and not source[0].isascii()):
            source = resolve(cmap, source)  # an earlier recipe's character
        if source not in font:
            sys.exit(f"{ch}: source {source} missing")
        name = resolve(cmap, ch)
        if name in font:
            lib = font[name].lib
            # unreviewed: a draft, or a derived small cap still marked a draft
            draft = lib.get(DRAFT_KEY) or (lib.get(DERIVED_KEY) and lib.get(SMALLCAP_DRAFT_KEY))
            if not (args.redraft and draft):
                kept.append(ch)
                if op == "alias":
                    aliases.append((name, source))
                # made before bases were recorded: recorded now, as they are
                if BUILT_KEY not in lib and not font[name].components:
                    read = probe(ch, op, source, band, name)
                    if read:
                        bases[name] = read
                continue
            del font[name]
        tracker = Tracker(font)
        try:
            g = build(tracker, ch, op, source, band, name)
        except (IndexError, KeyError, ValueError) as e:
            sys.exit(f"{ch}: {e!r}")
        if ch in SPACING:
            sidebearings(font, {g.name: SPACING[ch]})
        if not g.components:  # an alias follows its source itself
            bases[g.name] = tracker.read
        if op == "alias":
            aliases.append((g.name, source))
        if not variant(ch):
            cmap[ord(ch)] = g.name
        made.append(ch)
        built.append(g.name)
    # what a recipe drew without merging (enlarged, turned) cleaned too
    from glyph_lint import fix

    fix(font, built)
    if done:
        respace(font, classifier(font, done["cut"], done["greekLower"]))
        font.lib[CUT_KEY] = done
    # an alias follows its source's outline, and its width too where the
    # cut moved neither (ʛ kept the width ɠ.sc had before it was redrafted)
    for name, source in aliases:
        g = font[name]
        if (len(g.components) == 1 and not g.contours
                and tuple(g.components[0].transformation) == (1, 0, 0, 1, 0, 0)):
            g.width = font[source].width
    # the bases as they are saved, cut again
    for name, read in bases.items():
        stamp(font, name, read)
    font.save()
    print(f"drafted {len(made)}: {''.join(made)}")
    if kept:
        print(f"kept {len(kept)} existing: {''.join(kept)}")


if __name__ == "__main__":
    main()
