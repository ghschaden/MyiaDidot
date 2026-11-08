"""Draft the discretionary ligatures ct st Th th (feature dlig), the
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


F_BAR = (84 - 230, 836, 610 - 230, 884)  # the f's crossbar, from its stem
F_STEM = (230, 394)
L_STEM = 220  # left of the l's stem, and of b h k


def f_ligature(font, base, letter):
    """base (fl or ffl) with letter in place of the l."""
    lx = stems_at(font, base, 300)[-1][0]
    dx = lx - L_STEM
    if letter == "t":
        dx = lx - stems_at(font, "t", 300)[0][0]
        keep = path_op(to_path(font, font[base]), rect_path(lx - 160, -BIG, BIG, 884), "DIFFERENCE")
        part = path_op(to_path(font, font["t"]), rect_path(-BIG, 884, BIG, BIG), "DIFFERENCE")
        # the f's crossbar (ending 610 after its last stem) runs on into the t's
        fx = stems_at(font, base, 300)[-2][0]
        keep = path_op(keep, rect_path(fx + F_BAR[2] - 20, 836, dx + 100, 884), "UNION")
    else:
        keep = path_op(to_path(font, font[base]), rect_path(lx - 160, -BIG, BIG, 1250), "DIFFERENCE")
        part = path_op(to_path(font, font[letter]), rect_path(-BIG, 1300, BIG, BIG), "DIFFERENCE")
    rec = RecordingPen()
    part.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return path_op(keep, to_path(None, rec=rec), "UNION"), dx + font[letter].width


def without_crossbars(font, path, stems):
    """ſ from f: each f's crossbar removed, its stem kept."""
    for sx in stems:
        bar = rect_path(sx + F_BAR[0], F_BAR[1], sx + F_BAR[2], F_BAR[3])
        bar = path_op(bar, rect_path(sx, -BIG, sx + F_STEM[1] - F_STEM[0], BIG), "DIFFERENCE")
        path = path_op(path, bar, "DIFFERENCE")
    return path


TH_FLOW = 0.33  # Th: the T's right bracket at this size flowing into the h's stem (chosen 2026-11-08 from 1, 0.5, 0.33)
TH_CLOSER = 140  # th: t's width (730) - TH_SHIFT: the h this much nearer than set after t
TH_SHIFT = 590  # th: the h this far from the t (its foot serif 44 clear of t's tail; chosen 2026-11-08 from 620 560 520)


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


def finish(font):
    """The Bold's Th th made again from its own final T t h (finalization):
    emboldened whole from the Regular's, the T's and the h's foot serifs
    grew into each other. Their review records are kept."""
    for name, make in (("T_h", th_ligature), ("t_h", t_h_ligature)):
        if name not in font:
            continue
        out, width = make(font)
        g = font[name]
        g.clearContours()
        g.clearComponents()
        draw_path(font, font["t"], g, out)
        g.width = round(width)


# name, the fl it is built on, the letter; long-s ones: name, f-ligature
F_LIGATURES = [
    ("f_b", "fl", "b"), ("f_h", "fl", "h"), ("f_k", "fl", "k"), ("f_t", "fl", "t"),
    ("f_f_b", "ffl", "b"), ("f_f_h", "ffl", "h"), ("f_f_k", "ffl", "k"), ("f_f_t", "ffl", "t"),
]
LONGS_LIGATURES = [
    ("longs_b", "f_b"), ("longs_h", "f_h"), ("longs_k", "f_k"), ("longs_t", "f_t"),
    ("longs_i", "fi"), ("longs_l", "fl"), ("longs_longs", "ff"),
    ("longs_longs_i", "ffi"), ("longs_longs_l", "ffl"),
]
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
        made.append(name)

    for name, first, cut, left, base, peak, t_left, t_top, clip, closer in LIGATURES:
        if wanted(name):
            put(name, *build(font, name, first, cut, left, base, peak, t_left, t_top, clip, closer))
    for name, make in (("T_h", th_ligature), ("t_h", t_h_ligature)):
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
    font.save()
    print("drafted:", " ".join(made) or "nothing")


if __name__ == "__main__":
    main()
