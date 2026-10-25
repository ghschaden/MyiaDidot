"""Accepted italic ligatures, built from the final same-style letters."""

import math
from copy import deepcopy

from derive import BIG, draw_path, path_op, rect_path, stems_at, to_path
from draft_ligatures import arch
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from make_italic import SLANT, XH, shear, upright
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
NAMES = (*F_LIGATURES, *(name for name, _ in LONGS), "c_t", "s_t")


def make(font):
    """Rebuild new ligatures from final bases at this italic weight."""
    if not font.info.italicAngle:
        return []
    up = upright(font)
    made = []

    def put(name, path, width, carets=()):
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
            region = rect_path(a - 220, -BIG, b + 230, cut)
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
    return made
