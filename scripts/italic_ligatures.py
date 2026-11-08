"""Accepted italic ligatures, built from the final same-style letters."""

import math
from copy import deepcopy

from derive import BIG, draw_path, path_op, rect_path, stems_at, to_path
from draft_ligatures import arch, th_ligature
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from italic_geometry import SLANT, XH, shear, upright
from ufoLib2.objects import Glyph
from upright_aleph import add_extrema, fair_joins


def shift(path, dx):
    rec = RecordingPen()
    path.draw(TransformPen(rec, (1, 0, 0, 1, dx, 0)))
    return to_path(None, rec=rec)


F_LIGATURES = tuple(f"{prefix}_{letter}" for prefix in ("f", "f_f") for letter in ("b", "h", "k", "t"))
LONGS = (
    ("longs_b", "f_b"),
    ("longs_h", "f_h"),
    ("longs_k", "f_k"),
    ("longs_t", "f_t"),
    ("longs_i", "fi"),
    ("longs_l", "fl"),
    ("longs_longs", "ff"),
    ("longs_longs_i", "ffi"),
    ("longs_longs_l", "ffl"),
)
NAMES = (*F_LIGATURES, *(name for name, _ in LONGS), "c_t", "s_t", "T_h", "t_h")


ITALIC_TH_CLOSER = 100  # th: the h this much nearer than after t (chosen 2026-11-08 from 140 100 60)
TH_PEAK = 1600  # th: the arch's top, above the ascender (1434) and below the accents


def italic_th(up, closer=ITALIC_TH_CLOSER, peak=TH_PEAK):
    """The italics' th in the upright frame: (path, width)."""
    bar = sorted({p.y for c in up["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900})
    hair = (bar[-1] - bar[0]) * 0.7
    top = max(p.y for c in up["t"].contours for p in c.points)
    dx = up["t"].width - closer
    ta, tb = stems_at(up, "t", 1000)[0]
    xe = tb - hair  # the hairline's left edge, on the t's top
    y_l = top - 0.6 * (tb - ta)
    scoop = RecordingPen()
    scoop.moveTo((ta - 40, y_l))
    scoop.lineTo((ta, y_l))
    scoop.curveTo((ta + 0.55 * (xe - ta), y_l), (xe, top - 0.55 * (top - y_l)), (xe, top))
    scoop.lineTo((xe, top + 40))
    scoop.lineTo((ta - 40, top + 40))
    scoop.closePath()
    tee = path_op(to_path(up, up["t"]), to_path(None, rec=scoop), "DIFFERENCE")
    # the h below its serif; the arch's leg on its stem as measured there
    h = path_op(to_path(up, up["h"]), rect_path(-BIG, top - 80, BIG, BIG), "DIFFERENCE")
    ja, jb = stems_at(up, "h", top - 60)[0]
    bow = arch(xe, dx + jb, top - 81, peak, hair, jb - ja, hair, top - 82)
    out = path_op(path_op(tee, shift(h, dx), "UNION"), bow, "UNION")
    return out, dx + up["h"].width


def make(font):
    """Rebuild new ligatures from final bases at this italic weight."""
    if not font.info.italicAngle:
        return []
    up = upright(font)
    made = []

    def put(name, path, width, carets=()):
        # what the glyph made before carries over: its code points (ſt st:
        # U+FB05 U+FB06) and its acceptance (accepted.py compares outlines)
        before = font[name] if name in font else None
        g = Glyph(name=name)
        g.width = round(width)
        draw_path(up, up["f"], g, path)
        add_extrema(g)
        fair_joins(g)
        up.layers.defaultLayer.insertGlyph(g, name, overwrite=True)
        shear(g, SLANT, XH / 2)
        final = deepcopy(g)
        cleaned = Glyph(name=name)
        draw_path(None, final, cleaned, to_path(None, final))
        final = cleaned
        add_extrema(final)
        fair_joins(final)
        cleaned = Glyph(name=name)
        draw_path(None, final, cleaned, to_path(None, final))
        final = cleaned
        fair_joins(final)
        # Remove the artificial splice node on an otherwise straight stem.
        for contour in final.contours:
            points = contour.points
            for i in range(len(points) - 1, -1, -1):
                a, p, b = points[i - 1], points[i], points[(i + 1) % len(points)]
                if p.type and a.type and b.type:
                    turn = abs(
                        (math.degrees(math.atan2(p.y - a.y, p.x - a.x) - math.atan2(b.y - p.y, b.x - p.x)) + 180) % 360
                        - 180
                    )
                    if turn < 8:
                        del points[i]
        fair_joins(final)
        final.width = round(width)
        final.lib["org.myiadidot.italicSource"] = "ligature"
        if before is not None:
            final.unicodes = list(before.unicodes)
            if "org.myiadidot.accepted" in before.lib:
                final.lib["org.myiadidot.accepted"] = before.lib["org.myiadidot.accepted"]
        for i, x in enumerate(carets, 1):
            final.appendAnchor({"name": f"caret_{i}", "x": round(x), "y": 0})
        font.layers.defaultLayer.insertGlyph(final, name, overwrite=True)
        font.lib.setdefault("public.openTypeCategories", {})[name] = "ligature"
        if name not in font.glyphOrder:
            font.glyphOrder = [*font.glyphOrder, name]
        ending = name.split("_")[-1]
        group = {"b": "public.kern1.b", "k": "public.kern1.k"}.get(ending)
        if group and name not in font.groups.get(group, []):
            font.groups[group] = [*font.groups.get(group, []), name]
        # restore the upright glyph for dependent ligatures
        shear(g, -SLANT, XH / 2)
        made.append(name)

    for prefix, base in (("f", "fl"), ("f_f", "ffl")):
        lx = stems_at(up, base, 1000)[-1][0]
        for letter in ("b", "h", "k", "t"):
            cut = 1200
            dx = lx - stems_at(up, letter, 1000)[0][0]
            keep = path_op(to_path(up, up[base]), rect_path(lx - 100, -BIG, BIG, cut), "DIFFERENCE")
            part = path_op(to_path(up, up[letter]), rect_path(-BIG, cut, BIG, BIG), "DIFFERENCE")
            out = path_op(keep, shift(part, dx), "UNION")
            if letter == "t":
                fx = stems_at(up, base, 700)[-2][0]
                ys = sorted({p.y for c in up["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900})
                out = path_op(out, rect_path(fx, ys[0], dx + stems_at(up, "t", 700)[0][1], ys[-1]), "UNION")
            put(
                f"{prefix}_{letter}",
                out,
                dx + up[letter].width,
                [a.x for a in font[base].anchors if a.name.startswith("caret_")],
            )
    # Replace the crossbar region with the same-style long s; keep joined heads.
    for name, base in LONGS:
        path = to_path(up, up[base])
        count = 2 if "longs_longs" in name else 1
        stem_pairs = stems_at(up, base, 700)[:count]
        for i, (a, b) in enumerate(stem_pairs):
            cut = 1000
            ca, cb = stems_at(up, base, cut)[i]
            la, lb = stems_at(up, "longs", cut)[0]
            dx = (ca + cb - la - lb) / 2
            right = b + 230
            if name == "longs_t":
                # not into t's own crossbar arm (where f_t set t: lx - t's
                # stem): the Bold Italic's wider f stem cut it to a stub
                t_dx = stems_at(up, "fl", 1000)[-1][0] - stems_at(up, "t", 1000)[0][0]
                arm = min(p.x for c in up["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900)
                right = min(right, t_dx + arm)
            region = rect_path(a - 220, -BIG, right, cut)
            path = path_op(path, region, "DIFFERENCE")
            stem = path_op(to_path(up, up["longs"]), rect_path(-BIG, cut, BIG, BIG), "DIFFERENCE")
            path = path_op(path, shift(stem, dx), "UNION")
        put(name, path, up[base].width, [a.x for a in font[base].anchors if a.name.startswith("caret_")])
    for first in ("c", "s"):
        dx = up[first].width - 70
        tx0, tx1 = stems_at(up, "t", 700)[0]
        part = path_op(to_path(up, up["t"]), rect_path(-BIG, 884, BIG, BIG), "DIFFERENCE")
        a = to_path(up, up[first])
        bar_heights = sorted({p.y for c in up["t"].contours for p in c.points if p.type == "line" and 780 < p.y < 900})
        hair = (bar_heights[-1] - bar_heights[0]) * 0.7
        bow = arch(300, dx + tx1, 790, 1434, hair, tx1 - tx0, hair, 810)
        out = path_op(path_op(a, shift(part, dx), "UNION"), bow, "UNION")
        put(f"{first}_t", out, dx + up["t"].width, [dx])
    # Th as the Regular's (draft_ligatures.th_ligature), on this style's T and h
    # the italic T's arm is short: the h 0.8 of a T stem further out
    # (chosen 2026-11-08 from 0, 0.5, 1)
    ta, tb = stems_at(up, "T", 700)[0]
    out, width = th_ligature(up, reach=0.8 * (tb - ta))
    put("T_h", out, width, [width - up["h"].width + stems_at(up, "h", 700)[0][0]])
    # th (accepted 2026-11-08): an arch from the t's top to the h's, as the
    # ct st arches: a hairline rising from the t's top, its stem's top a
    # concave scoop as the Regular t's (leaving the stem's left edge level,
    # arriving upright at the hairline), over the top as a hairline and down
    # into the h's stem at its full width; the h's sloped top serif cut
    # away, the h ITALIC_TH_CLOSER nearer than set after t
    put("t_h", *italic_th(up), [up["t"].width - ITALIC_TH_CLOSER])
    return made
