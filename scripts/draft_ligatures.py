"""Draft the discretionary ligatures ct and st (feature dlig).

    python scripts/draft_ligatures.py UFO [--redraft]

Each is the first letter without its top terminal, the t at its usual
distance without the wedge above its crossbar, and an arch from the
first letter's top stroke up and over into the t's stem: half an
ellipse, a hairline where it leaves the first letter and across the
top, swelling to the t's stem width as it comes down into it. Glyphs are marked
as drafts; existing glyphs are kept unless they are unreviewed drafts and
--redraft is given. The dlig rules are in features.fea.
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


# name, first letter, its terminal cut away, arch: left foot x, base, peak,
# left leg, top, foot clip; the t moves this much closer
LIGATURES = [
    ("c_t", "c", (600, 500, BIG, BIG), 560, 800, 1380, 50, 40, 850, 50),
    ("s_t", "s", (600, 600, BIG, BIG), 560, 800, 1380, 50, 40, 850, 50),
]


def build(font, name, first, cut, left, base, peak, t_left, t_top, clip, closer):
    w1 = font[first].width - closer
    a = path_op(to_path(font, font[first]), rect_path(*cut), "DIFFERENCE")
    # the t without the wedge above its crossbar
    t = path_op(to_path(font, font["t"]), rect_path(-BIG, 884, BIG, BIG), "DIFFERENCE")
    rec = RecordingPen()
    t.draw(TransformPen(rec, (1, 0, 0, 1, w1, 0)))
    t = to_path(None, rec=rec)
    sa, sb = stems_at(font, "t", 600)[0]
    bow = arch(left, w1 + sb, base, peak, t_left, sb - sa, t_top, clip)
    out = path_op(path_op(a, t, "UNION"), bow, "UNION")
    return out, w1 + font["t"].width


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--redraft", action="store_true")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    cats = font.lib.setdefault("public.openTypeCategories", {})
    made = []
    for name, first, cut, left, base, peak, t_left, t_top, clip, closer in LIGATURES:
        if name in font:
            if not (args.redraft and font[name].lib.get(DRAFT_KEY)):
                continue
            del font[name]
        out, width = build(font, name, first, cut, left, base, peak, t_left, t_top, clip, closer)
        g = font.newGlyph(name)
        g.width = round(width)
        draw_path(font, font["t"], g, out)
        g.lib[DRAFT_KEY] = True
        cats[name] = "ligature"
        if name not in font.glyphOrder:
            font.glyphOrder = [*font.glyphOrder, name]
        made.append(name)
    font.save()
    print("drafted:", " ".join(made) or "nothing")


if __name__ == "__main__":
    main()
