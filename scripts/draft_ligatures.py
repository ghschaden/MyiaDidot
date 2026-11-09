"""Draft the discretionary ligatures ct st sp Qu Th th tt (feature dlig), the
f-ligatures fb fh fk ft ffb ffh ffk fft (liga) and the long-s ligatures
ſb ſh ſk ſt ſi ſl ſſ ſſi ſſl (liga, own lookup).

    python scripts/draft_ligatures.py UFO [--redraft]

Each is the first letter whole (its top terminal kept, standing free to
the right of the arch's foot), the t at its usual distance without the
wedge above its crossbar, and an arch from the first letter's top stroke
up and over into the t's stem: half an
ellipse, a hairline where it leaves the first letter and across the
top, swelling to the t's stem width as it comes down into it. Glyphs are marked
as drafts; existing glyphs are kept unless they are unreviewed drafts and
--redraft is given. The dlig rules are in features.fea.

The f-ligatures are fl (ffl) with the l below its top cut away and the
letter put in its place, stem on the l's stem (b h k are cut above 1250,
where fl's stem takes over; the t loses its wedge, its stem rises into
fl's, and the two crossbars are joined). The long-s ligatures are the
f-ligatures without the f's crossbars, as ſ is f without its crossbar.
sp is st's arch landing on the p's stem: the p's top serif cut away, its
stem running up into the arch's right leg (sp_ligature). Qu is O and u
with a drawn tail (qu_ligature): in the upright styles (QU_TAIL) the lower
part of a 2 hanging from the centre of the O's bottom, down its neck to a
sharp point, back up nearly along it and away under the Q and the u as a
gently waving swash; in the italics (QU_TAIL_LOOP) the 2's head loops in
the O first.

In the Bold, finish() and finish_f() (finalization passes) make Th th tt Qu
and the f- and long-s ligatures (ff fi fl ffi ffl fj ffj too) again from
its own final letters.
"""

import argparse
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive import BIG, draw_path, path_op, rect_path, stems_at, to_path
from draft_symbols import KAPPA

DRAFT_KEY = "org.myiadidot.draft"


def ellipse(cx, cy, rx, ry):
    rec = RecordingPen()
    kx, ky = KAPPA * rx, KAPPA * ry
    rec.moveTo((cx + rx, cy))
    rec.curveTo((cx + rx, cy + ky), (cx + kx, cy + ry), (cx, cy + ry))
    rec.curveTo((cx - kx, cy + ry), (cx - rx, cy + ky), (cx - rx, cy))
    rec.curveTo((cx - rx, cy - ky), (cx - kx, cy - ry), (cx, cy - ry))
    rec.curveTo((cx + kx, cy - ry), (cx + rx, cy - ky), (cx + rx, cy))
    rec.closePath()
    return to_path(None, rec=rec)


def arch(left, right, base, peak, t_left, t_right, t_top, clip):
    """Upper half of an elliptical ring from x=left to x=right (outer),
    springing at y=base and reaching peak; legs t_left/t_right thick, the
    top t_top; cut off below clip."""
    cx, rx, ry = (left + right) / 2, (right - left) / 2, peak - base
    outer = ellipse(cx, base, rx, ry)
    inner = ellipse(cx + (t_left - t_right) / 2, base, rx - (t_left + t_right) / 2, ry - t_top)
    ring = path_op(outer, inner, "DIFFERENCE")
    return path_op(ring, rect_path(-BIG, clip, BIG, BIG), "INTERSECTION")


# name, first letter, a box cut away from it (None: kept whole), arch: left
# foot x, base, peak, left leg, top, foot clip; the t moves this much closer
LIGATURES = [
    ("c_t", "c", None, 400, 800, 1380, 50, 40, 850, 50),
    ("s_t", "s", None, 400, 800, 1380, 50, 40, 850, 50),
]


def build(font, name, first, cut, left, base, peak, t_left, t_top, clip, closer):
    w1 = font[first].width - closer
    a = to_path(font, font[first])
    if cut:
        a = path_op(a, rect_path(*cut), "DIFFERENCE")
    # the t without the wedge above its crossbar
    t = path_op(to_path(font, font["t"]), rect_path(-BIG, 884, BIG, BIG), "DIFFERENCE")
    rec = RecordingPen()
    t.draw(TransformPen(rec, (1, 0, 0, 1, w1, 0)))
    t = to_path(None, rec=rec)
    sa, sb = stems_at(font, "t", 600)[0]
    bow = arch(left, w1 + sb, base, peak, t_left, sb - sa, t_top, clip)
    out = path_op(path_op(a, t, "UNION"), bow, "UNION")
    return out, w1 + font["t"].width


SP_JOIN = 850  # sp: where the arch meets the p's stem (st's arch is cut there)
SP_CLOSER = 30  # sp: the p's stem as far from the s as st's t stem (st: 50; t's stem 210, p's 190)


def sp_ligature(font, closer=SP_CLOSER):
    """sp: the s whole, the p without its top serif and the top of its stem
    (cut at SP_JOIN), and st's arch from the s's top over into the p's
    stem, its right leg the stem's width there (measured above the bowl's
    crotch: lower the stem widens into it). The arch springs at SP_JOIN, so
    its legs leave the s and the stem upright (st's springs 50 lower and is
    cut there, 3 degrees off upright, hidden in the t's stem)."""
    w1 = font["s"].width - closer
    sa, sb = stems_at(font, "p", 800)[0]
    foot = min(p.y for c in font["p"].contours for p in c.points if p.x < sa - 20 and p.y > 600)
    p = path_op(to_path(font, font["p"]), rect_path(-BIG, foot - 6, sa, BIG), "DIFFERENCE")
    p = path_op(p, rect_path(-BIG, SP_JOIN, sb + 20, BIG), "DIFFERENCE")
    bow = arch(400, w1 + sb, SP_JOIN, 1380, 50, sb - sa, 40, SP_JOIN)
    out = path_op(path_op(to_path(font, font["s"]), shifted(p, w1), "UNION"), bow, "UNION")
    return out, w1 + font["p"].width


F_BAR = (84 - 230, 836, 610 - 230, 884)  # the f's crossbar, from its stem
F_STEM = (230, 394)
L_STEM = 220  # left of the l's stem, and of b h k


def f_ligature(font, base, letter, bar=None):
    """base (fl or ffl) with letter in place of the l. bar: the f's
    crossbar as measured (f_bar; the Bold), the letter then set by its own
    stem and the cut kept off the crossbar; None: the Regular's F_BAR and
    L_STEM."""
    lx = stems_at(font, base, 300)[-1][0]
    fx = stems_at(font, base, 300)[-2][0]
    dx = lx - (L_STEM if bar is None else stems_at(font, letter, 1100)[0][0])
    bar = bar or F_BAR
    if letter == "t":
        dx = lx - stems_at(font, "t", 300)[0][0]
        keep = path_op(to_path(font, font[base]), rect_path(lx - 160, -BIG, BIG, bar[3]), "DIFFERENCE")
        part = path_op(to_path(font, font["t"]), rect_path(-BIG, bar[3], BIG, BIG), "DIFFERENCE")
        # the f's crossbar (ending 610 after its last stem) runs on into the t's
        keep = path_op(keep, rect_path(fx + bar[2] - 20, bar[1], dx + 100, bar[3]), "UNION")
    else:
        # the l's stem and foot cut away below 1250, not the f's crossbar
        cut = path_op(rect_path(lx - 160, -BIG, BIG, bar[1] - 1),
                      rect_path(max(lx - 160, fx + bar[2] + 1), bar[1] - 2, BIG, 1250), "UNION")
        keep = path_op(to_path(font, font[base]), cut, "DIFFERENCE")
        part = path_op(to_path(font, font[letter]), rect_path(-BIG, 1300, BIG, BIG), "DIFFERENCE")
    rec = RecordingPen()
    part.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return path_op(keep, to_path(None, rec=rec), "UNION"), dx + font[letter].width


def without_crossbars(font, path, stems, bar=None):
    """ſ from f: each f's crossbar removed, its stem kept. bar: as
    f_ligature's."""
    stem = F_STEM[1] - F_STEM[0] if bar is None else bar[4]
    bar = bar or F_BAR
    for sx in stems:
        cut = rect_path(sx + bar[0], bar[1], sx + bar[2], bar[3])
        cut = path_op(cut, rect_path(sx, -BIG, sx + stem, BIG), "DIFFERENCE")
        path = path_op(path, cut, "DIFFERENCE")
    return path


# Qu: the tail drawn as one outline in the Regular's units (2026-11-09,
# after the designer's sketch Bildschirmfoto_20261109_120154 and review):
# the "2" out of the O (from a root in the bowl's lower-left stroke, a
# hairline lift over a hairline apex, one full stroke through the bowl's
# bottom down its neck), a sharp point at the bottom left, back up nearly
# along the neck from a crotch and away as a swash waving like a flattened
# tilde, to a sharp point under the u's right stem. (start, [(h1, h2, end)])
# The italics' (QU_TAIL_LOOP); the upright styles take QU_TAIL below.
QU_TAIL_LOOP = ((505, 118), [
    ((600, 178), (745, 214), (880, 214)),        # head top: from the root in the bowl's stroke to the apex
    ((1015, 214), (1135, 170), (1135, 85)),      # over the right shoulder, to its extreme
    ((1135, 0), (1040, -175), (930, -285)),      # the outer edge, one stroke through the bowl's bottom, full to the crotch
    ((1060, -235), (1240, -205), (1440, -205)),  # the swash's top edge (a corner at the crotch), to its crest
    ((1640, -205), (1840, -327), (2040, -327)),  # down into the trough
    ((2215, -327), (2375, -275), (2445, -150)),  # rising to the point
    ((2395, -275), (2130, -432), (1880, -432)),  # the bottom edge back (a point at the end), under the trough
    ((1660, -432), (1420, -320), (1170, -322)),  # rising under the crest
    ((960, -325), (790, -398), (690, -460)),     # down to the sharp point at the bottom left
    ((800, -300), (1000, 30), (1000, 128)),      # the inner edge, one stroke up through the bowl, arriving upright
    ((1000, 165), (950, 178), (850, 178)),       # under the head: the 2's hook
    ((720, 178), (610, 120), (525, 72)),         # back to the root
])
# the upright styles' (chosen 2026-11-09 over the loop): only the 2's lower
# part, its neck hanging from the centre of the O's bottom (the loop's
# neck and hairpin 207 to the left, the swash stretched to keep its end)
QU_TAIL = ((744, 8), [
    ((794, 8), (842, 8), (892, 8)),              # the neck's top, inside the bowl's bottom stroke
    ((892, -90), (828, -195), (723, -285)),      # the outer edge, down to the crotch
    ((871, -235), (1075, -205), (1303, -205)),   # the swash's top edge (a corner at the crotch), to its crest
    ((1530, -205), (1757, -327), (1985, -327)),  # down into the trough
    ((2184, -327), (2365, -275), (2445, -150)),  # rising to the point
    ((2388, -275), (2087, -432), (1803, -432)),  # the bottom edge back (a point at the end), under the trough
    ((1553, -432), (1280, -320), (996, -322)),   # rising under the crest
    ((757, -325), (583, -398), (483, -460)),     # down to the sharp point at the bottom left
    ((578, -330), (735, -110), (744, 8)),        # the neck's inner edge, up into the bowl
])
# the Regular's measures QU_TAIL was drawn at: O's ink, its round stem and
# hairline, the centre of u's right stem; the end's offset from that centre
QU_DRAWN = {"o_ink": (126, 1502), "o_width": 1578, "stem": 184, "hair": 48, "u_stem": 835, "end": 2445}


def _weighted(rec, k_stem, k_hair, thin=32):
    """the tail at another weight: each node (with its handles) moved out
    by half what its stroke gains there, the stroke's thickness at the node
    measured inward along its normal: a hairline thin units thick at k_hair,
    the rest at k_stem (points, nearly nothing thick, stay sharp)"""
    import math

    if k_stem == 1 and k_hair == 1:
        return rec
    path = to_path(None, rec=rec)
    start = rec.value[0][1][0]
    segs = [pts for op, pts in rec.value[1:] if op == "curveTo"]
    nodes = [start] + [s[2] for s in segs]
    n = len(segs)
    moves = []
    for i in range(n):
        p = nodes[i]
        before = segs[i - 1][1] if i else segs[-1][1]  # the handle into p
        after = segs[i][0]  # the handle out of p
        tx, ty = after[0] - before[0], after[1] - before[1]
        length = math.hypot(tx, ty) or 1
        nx, ny = -ty / length, tx / length
        if path.contains((p[0] + 2 * nx, p[1] + 2 * ny)):
            nx, ny = -nx, -ny  # (nx, ny) points out of the stroke
        t = next((s for s in range(1, 400) if not path.contains((p[0] - s * nx, p[1] - s * ny))), 0)
        gain = (min(t, thin) * (k_hair - 1) + max(t - thin, 0) * (k_stem - 1)) / 2
        moves.append((nx * gain, ny * gain))
    out = RecordingPen()
    dx, dy = moves[0]
    out.moveTo((start[0] + dx, start[1] + dy))
    for i, (h1, h2, end) in enumerate(segs):
        a, b = moves[i], moves[(i + 1) % n]
        out.curveTo((h1[0] + a[0], h1[1] + a[1]), (h2[0] + b[0], h2[1] + b[1]), (end[0] + b[0], end[1] + b[1]))
    out.closePath()
    return out


def qu_ligature(font, tail=None):
    """Qu: O, the drawn tail (QU_TAIL) and u set after O as after Q, in this
    style: the tail's x mapped onto its O and to its u's right stem, its
    weight moved to its stem and hairline (the Regular's are QU_DRAWN)."""
    import derive
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.reverseContourPen import ReverseContourPen
    from italic_geometry import EXTREME_PAST

    o_width = font["O"].width
    ox0, ox1 = (round(v) for v in derive.ink_bounds(font, "O")[::2])
    runs = derive.stems_at(font, "u", 300)
    u_stem = max(runs[1:], key=lambda r: r[1] - r[0])
    (dx0, dx1), end_was = QU_DRAWN["o_ink"], QU_DRAWN["end"]
    end_is = o_width + round((u_stem[0] + u_stem[1]) / 2) + end_was - QU_DRAWN["o_width"] - QU_DRAWN["u_stem"]

    def mapped(pt):
        x, y = pt
        if x <= dx1:
            return (ox0 + (x - dx0) * (ox1 - ox0) / (dx1 - dx0), y)
        return (ox1 + (x - dx1) * (end_is - ox1) / (end_was - dx1), y)

    start, segs = tail or QU_TAIL
    rec = RecordingPen()
    rec.moveTo(mapped(start))
    for seg in segs:
        rec.curveTo(*(mapped(pt) for pt in seg))
    rec.closePath()
    # (to three places: the Regular measures 183.9998 and 48.0004)
    _, stem, hair = derive.strokes(font, "o")
    rec = _weighted(rec, round(stem / QU_DRAWN["stem"], 3), round(hair / QU_DRAWN["hair"], 3))
    area = AreaPen()
    rec.replay(area)
    if area.value > 0:  # wound as the O's outer contour
        flipped = RecordingPen()
        rec.replay(ReverseContourPen(flipped))
        rec = flipped
    out = to_path(font, font["O"])
    for part in (to_path(None, rec=rec), shifted(to_path(font, font["u"]), o_width)):
        out = path_op(out, part, "UNION")
    # nodes at the extremes
    rec = RecordingPen()
    out.draw(rec)
    split = RecordingPen()
    derive.with_extremes(rec, split, past=EXTREME_PAST)
    return to_path(None, rec=split), o_width + font["u"].width


TH_FLOW = 0.33  # Th: the T's right bracket at this size flowing into the h's stem (chosen 2026-11-08 from 1, 0.5, 0.33)
TH_CLOSER = 110  # th: t's width (730) - TH_SHIFT: the h this much nearer than set after t
TH_SHIFT = 620  # th: the h this far from the t (590 chosen 2026-11-08 from 620 560 520; "a bit tight", 620 chosen 2026-11-09 from 620 650)
TT_CLOSER = 140  # tt: the second t as near as th's h was (590 after the t), kept so 2026-11-09


def shifted(path, dx):
    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return to_path(None, rec=rec)


def th_ligature(font, s=TH_FLOW, reach=0):
    """Th: the T's crossbar runs on to the h's stem, standing where the
    T's right arm ended; the arm's bracket (the curve from the bar's
    underside into its serif), scaled by s about the arm's end, flows from
    the bar into the stem. The T's foot serif whole, the h cut at the bar's
    underside (no top serif). Measured on the font's own T and h (the
    italics: italic_ligatures.py, upright frame). reach: the h this much
    further right than the arm's end, the crossbar run on to it (the
    italics' T has a short arm: under it the h's stem stood tight against
    the T's, 2026-11-08)."""
    T = font["T"]
    top = max(p.y for c in T.contours for p in c.points)
    stem = stems_at(font, "T", 700)[0][1]
    under = max(p.y for c in T.contours for p in c.points if p.type and p.x > stem + 50 and p.y < top)
    arm = rect_path(stem + 1, under / 2, BIG, under)  # below the bar, above the foot serif
    tee = to_path(font, T)
    core = path_op(tee, arm, "DIFFERENCE")
    bracket = path_op(tee, arm, "INTERSECTION")
    x0, y0, x1, _ = bracket.bounds
    foot_in = min(x for c in to_glif(bracket) for x, y in c if y < y0 + 20)
    sa, sb = stems_at(font, "h", 700)[0]
    dx = x1 - sb + reach
    rec = RecordingPen()
    # about (x1, under), then its inner foot 8 units into the stem
    move = x1 * (1 - s) + (sa + dx - (x1 - (x1 - foot_in) * s)) + 8
    bracket.draw(TransformPen(rec, (s, 0, 0, s, move, under * (1 - s))))
    h = path_op(to_path(font, font["h"]), rect_path(-BIG, under, BIG, BIG), "DIFFERENCE")
    out = path_op(path_op(core, shifted(h, dx), "UNION"), to_path(None, rec=rec), "UNION")
    # the bar out to the h's stem as it is just below it (the Bold's widens
    # toward its top: run to its mid-height edge, the stem's corner stood
    # 46 units out under the bar's end)
    top_b = max(sb, stems_at(font, "h", under - 60)[0][1])
    out = path_op(out, rect_path(stem, under, top_b + dx, top), "UNION")
    return out, dx + font["h"].width


def to_glif(path):
    """The on-curve points of a path, per contour."""
    rec = RecordingPen()
    path.draw(rec)
    out, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]
            out.append(cur)
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            cur.append(args[-1])
    return out


def t_h_ligature(font):
    """th: the t's crossbar run on into the h's stem."""
    bar = sorted({p.y for c in font["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900})
    shift = font["t"].width - TH_CLOSER  # TH_SHIFT in the Regular
    h = shifted(to_path(font, font["h"]), shift)
    t = to_path(font, font["t"])
    t_bar_end = max(p.x for c in font["t"].contours for p in c.points if p.type and p.y == bar[-1])
    h_stem = stems_at(font, "h", 700)[0][0] + shift
    out = path_op(path_op(t, h, "UNION"), rect_path(t_bar_end - 10, bar[0], h_stem + 10, bar[-1]), "UNION")
    return out, shift + font["h"].width


def t_t_ligature(font, closer=TT_CLOSER):
    """tt: two t's on one crossbar, the second as near as th's h."""
    bar = sorted({p.y for c in font["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900})
    xs = [p.x for c in font["t"].contours for p in c.points if p.type and bar[0] <= p.y <= bar[-1]]
    shift = font["t"].width - closer
    t = to_path(font, font["t"])
    out = path_op(t, shifted(t, shift), "UNION")
    out = path_op(out, rect_path(max(xs) - 10, bar[0], min(xs) + shift + 10, bar[-1]), "UNION")
    return out, shift + font["t"].width


def finish(font):
    """The Bold's Th th tt Qu made again from its own final letters
    (finalization): emboldened whole from the Regular's, the T's and the h's
    foot serifs grew into each other, Qu's tail stayed light. Their review
    records are kept."""
    for name, make in (("T_h", th_ligature), ("t_h", t_h_ligature), ("t_t", t_t_ligature), ("Q_u", qu_ligature)):
        if name not in font:
            continue
        out, width = make(font)
        g = font[name]
        g.clearContours()
        g.clearComponents()
        draw_path(font, font["t"], g, out)
        g.width = round(width)


# The Bold's fl: from the f's top (its outer apex, and the inner one) the
# arch over into the l's straight stem, as the Regular's fl emboldened
# (2026-11-09) but for its stem, which leaned: offsets from the l's stem
# (left edge), heights absolute.
FL_ARCH = {
    "out_h1": 99,  # the outer curve's first handle, after the f's apex
    "out_h2": (42, 1462),
    "meet": (71, 1428),  # where the outer curve meets the wedge up to the stem's top
    "wedge": 148,  # the wedge's top
    "in_foot": 1168,  # where the stem's inner edge stops being straight
    "in_h": 1321,
}


def f_bar(font):
    """The f's crossbar from its stem's left: (left, bottom, right, top,
    stem width)."""
    f = font["f"]
    sa, sb = stems_at(font, "f", 300)[0]
    pts = [p for c in f.contours for p in c.points if p.type]
    low = min(p.y for p in pts if 700 < p.y < 1000)
    top = min(p.y for p in pts if low < p.y < 1000)
    xs = [p.x for p in pts if p.y == low]
    return (min(xs) - sa, low, max(xs) - sa, top, sb - sa)


def fl_shape(font, dx):
    """fl: the f's contour with its ball replaced, from its outer apex to
    its inner one, by FL_ARCH over into the l's straight stem (at dx),
    spliced in so that both apexes stay smooth; the l below 1110."""
    from fontTools.pens.pointPen import PointToSegmentPen

    (contour,) = font["f"].contours
    pts = [(p.x, p.y, p.type) for p in contour.points]
    on = [i for i, p in enumerate(pts) if p[2]]
    top = max(pts[i][1] for i in on)
    apex = next(i for i in on if pts[i][1] == top)  # the outer apex
    inner = max((i for i in on if pts[i][1] < top - 20 and pts[i][0] < pts[apex][0]), key=lambda i: pts[i][1])
    ax, iy = pts[apex][0], pts[inner][1]
    sl, sr = (x + dx for x in stems_at(font, "l", 300)[0])
    a = FL_ARCH
    arch = [(ax + a["out_h1"], top, None), (sl + a["out_h2"][0], a["out_h2"][1], None),
            (sl + a["meet"][0], a["meet"][1], "curve"), (sl + a["wedge"], top, "line"), (sr, top, "line"),
            (sr, 1100, "line"), (sl, 1100, "line"), (sl, a["in_foot"], "line"),
            (sl, a["in_h"], None), (sl, iy, None)]
    spliced = pts[:apex + 1] + arch + pts[inner:]
    rec = RecordingPen()
    pen = PointToSegmentPen(rec)
    pen.beginPath()
    for x, y, t in spliced:
        pen.addPoint((x, y), segmentType=t)
    pen.endPath()
    l = path_op(to_path(font, font["l"]), rect_path(-BIG, 1110, BIG, BIG), "DIFFERENCE")
    return path_op(to_path(None, rec=rec), shifted(l, dx), "UNION")


def bar_join(font, end, letter, dx, bar):
    """The f's crossbar (ending at end) run on into the top serif of
    letter (ı ȷ, set at dx), as the old emboldened fi fj had it (their
    gap, 58 in the Regular, closed): from 20 inside the bar to 20 inside
    the serif, its top sloping to the serif's if they differ by a unit."""
    pts = [p for c in font[letter].contours for p in c.points if p.type and bar[1] - 20 < p.y < bar[3] + 20]
    left = min(p.x for p in pts)
    top = max(p.y for p in pts if p.x == left)
    low = min(p.y for p in pts if p.x == left)
    rec = RecordingPen()
    rec.moveTo((end - 20, bar[1]))
    rec.lineTo((end - 20, bar[3]))
    rec.lineTo((left + dx + 20, top))
    rec.lineTo((left + dx + 20, low))
    rec.closePath()
    return to_path(None, rec=rec)


def offset(font, lig, k, letter):
    """Where lig's k-th stem (at 300) puts letter."""
    return stems_at(font, lig, 300)[k][0] - stems_at(font, letter, 300)[0][0]


def finish_f(font):
    """The Bold's f-ligatures made again from its own final f
    (finalization; decided 2026-11-09): emboldened whole from the
    Regular's, their fs came out badly drawn over the crossbar, fl's
    stem leaning, ﬀh's shoulder kinked. ff fi fj: the f beside the f, ı, ȷ;
    fl: fl_shape; ffi ffl ffj: the f beside those; before b h k t:
    f_ligature on fl ffl; the long-s ones: without_crossbars. Each keeps
    its stems where the emboldened one had them and its advance width
    (the Bold's spacing), and is marked a draft for review."""
    if "f" not in font or "ff" not in font:
        return
    f = to_path(font, font["f"])
    bar = f_bar(font)
    shapes = {}
    dff = offset(font, "ff", 1, "f")
    shapes["ff"] = path_op(f, shifted(f, dff), "UNION")
    unjoined = {}  # fi fj ffi ffj before the crossbar's join: their long-s forms
    fx = stems_at(font, "f", 300)[0][0]
    for name, letter in (("fi", "dotlessi"), ("f_j", "uni0237")):
        if name in font:
            dx = offset(font, name, 1, letter)
            unjoined[name] = path_op(f, shifted(to_path(font, font[letter]), dx), "UNION")
            shapes[name] = path_op(unjoined[name], bar_join(font, fx + bar[2], letter, dx, bar), "UNION")
    shapes["fl"] = fl_shape(font, offset(font, "fl", 1, "l"))
    for name, two in (("ffi", "fi"), ("ffl", "fl"), ("f_f_j", "f_j")):
        if name in font and two in shapes:
            shapes[name] = path_op(f, shifted(shapes[two], dff), "UNION")
            if two in unjoined:
                unjoined[name] = path_op(f, shifted(unjoined[two], dff), "UNION")

    def put(name, out):
        g = font[name]
        width = g.width
        g.clearContours()
        g.clearComponents()
        draw_path(font, font["f"], g, out)
        g.width = width
        g.lib[DRAFT_KEY] = True

    for name, out in shapes.items():
        put(name, out)
    for name, base, letter in F_LIGATURES:
        if name in font:
            put(name, f_ligature(font, base, letter, bar)[0])
    for name, src in LONGS_LIGATURES:
        if name in font and src in font:
            n_f = src.count("f") if "_" not in src else src.split("_").count("f")
            stems = [a for a, _ in stems_at(font, src, 300)][:n_f]
            path = unjoined.get(src) or to_path(font, font[src])
            put(name, without_crossbars(font, path, stems, bar))


# name, the fl it is built on, the letter; long-s ones: name, f-ligature
F_LIGATURES = [
    ("f_b", "fl", "b"), ("f_h", "fl", "h"), ("f_k", "fl", "k"), ("f_t", "fl", "t"),
    ("f_f_b", "ffl", "b"), ("f_f_h", "ffl", "h"), ("f_f_k", "ffl", "k"), ("f_f_t", "ffl", "t"),
]
LONGS_LIGATURES = [
    ("longs_b", "f_b"), ("longs_h", "f_h"), ("longs_k", "f_k"), ("longs_t", "f_t"),
    ("longs_i", "fi"), ("longs_l", "fl"), ("longs_longs", "ff"),
    ("longs_longs_i", "ffi"), ("longs_longs_l", "ffl"),
    # completing the set (2026-11-08): ſſ before b h k t, ſj ſſj
    ("longs_longs_b", "f_f_b"), ("longs_longs_h", "f_f_h"), ("longs_longs_k", "f_f_k"),
    ("longs_longs_t", "f_f_t"), ("longs_j", "f_j"), ("longs_longs_j", "f_f_j"),
]
# the encoded ligature characters (Alphabetic Presentation Forms) for
# shapes the font has: ſt st
ENCODED = {"longs_t": 0xFB05, "s_t": 0xFB06}
# right-side kerning of the ligature = that of its last letter
KERN1 = {"b": "public.kern1.b", "k": "public.kern1.k"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    made = []

    def wanted(name):
        if name in font:
            # an accepted ligature is not redrafted (acceptance does not
            # clear the draft flag: docs/claude/quality.md)
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)) or "org.myiadidot.accepted" in font[name].lib:
                return False
            del font[name]
        return True

    def put(name, out, width):
        g = font.newGlyph(name)
        g.width = round(width)
        draw_path(font, font["t"], g, out)
        g.lib[DRAFT_KEY] = True
        cats[name] = "ligature"
        if name not in font.glyphOrder:
            font.glyphOrder = [*font.glyphOrder, name]
        group = KERN1.get(name.split("_")[-1])
        if group and name not in font.groups[group]:
            font.groups[group] = [*font.groups[group], name]
        # on its left, the ligature kerns as its first letter (Qu: as O, Q's group)
        first = name.split("_")[0]
        left = next((g for g, m in font.groups.items() if g.startswith("public.kern2.") and first in m), None)
        if left and name not in font.groups[left]:
            font.groups[left] = [*font.groups[left], name]
        made.append(name)

    for name, first, cut, left, base, peak, t_left, t_top, clip, closer in LIGATURES:
        if wanted(name):
            put(name, *build(font, name, first, cut, left, base, peak, t_left, t_top, clip, closer))
    for name, make in (("s_p", sp_ligature), ("Q_u", qu_ligature), ("T_h", th_ligature),
                       ("t_h", t_h_ligature), ("t_t", t_t_ligature)):
        if wanted(name):
            put(name, *make(font))
    for name, base, letter in F_LIGATURES:
        if wanted(name):
            put(name, *f_ligature(font, base, letter))
    for name, src in LONGS_LIGATURES:
        if wanted(name):
            n_f = src.count("f") if "_" not in src else src.split("_").count("f")
            stems = [a for a, _ in stems_at(font, src, 300)][:n_f]
            put(name, without_crossbars(font, to_path(font, font[src]), stems), font[src].width)
    for name, code in ENCODED.items():
        if name in font and code not in font[name].unicodes:
            font[name].unicodes = [*font[name].unicodes, code]
            made.append(f"{name}=U+{code:04X}")
    font.save()
    print("drafted:", " ".join(made) or "nothing")


if __name__ == "__main__":
    main()
