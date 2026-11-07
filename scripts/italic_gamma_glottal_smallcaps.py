"""Approved paired gamma and glottal small-cap construction; scratch output only."""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from built_from import fingerprint
from case_reference import KEY as CASE_REFERENCE_KEY
from drawn import KEY as DRAWN_KEY
from italic_geometry import SLANT, redraw, shear, upright
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("uni0263.sc", "uni0242.sc")


def gamma(font, up):
    from derived import Outline
    from strokes import main_stroke

    name = "uni0263.sc"
    old_box = font[name].getBounds(font)
    rec = DecomposingRecordingPen(up)
    up["uni0194"].draw(rec)
    scaled = RecordingPen()
    scale = 1040 / 1434
    rec.replay(TransformPen(scaled, (scale, 0, 0, scale, 0, 0)))

    def weight(glyph_name, height):
        return main_stroke(Outline(up, glyph_name, (1, 0, 0, 1, 0, 0)), height)[0]

    # Same relative stroke weight as Ɣ/H, rather than the draft's weight
    # of a full stem. The capital's descending loop keeps its position.
    target = weight("uni0194", 1434) / weight("H", 1434) * weight("h.sc", 1040)
    low, high = 0.0, target / 2
    for _ in range(9):
        gain = (low + high) / 2
        made = derive.embolden(scaled, gain, gain * 0.1)
        up.layers.defaultLayer.insertGlyph(made, name, overwrite=True)
        if weight(name, 1040) < target:
            low = gain
        else:
            high = gain
    shear(made, SLANT, extremes=True)
    for contour in made.contours:
        round_smoothly(contour.points)
    redraw(font[name], made)
    new_box = font[name].getBounds(font)
    growth = (new_box.xMax - new_box.xMin) - (old_box.xMax - old_box.xMin)
    dx = round(old_box.xMin - new_box.xMin)
    for contour in font[name].contours:
        contour.move((dx, 0))
    font[name].width += round(growth)
    for anchor in font[name].anchors:
        anchor.x += round(growth / 2)
    font[name].lib[CASE_REFERENCE_KEY] = "uni0194"


def glottal(font, up):
    name = "uni0242.sc"
    glyph = copy.deepcopy(up[name])
    points = glyph.contours[0].points
    # The inner run follows the stem's last baseline point and precedes
    # the terminal ball. Identify its bottom, top and ball-side endpoint.
    last_baseline = max(i for i, p in enumerate(points) if p.type and p.y == 0)
    nodes = [i for i in range(last_baseline + 1, len(points)) if points[i].type == "curve"]
    bottom = min(nodes[:4], key=lambda i: points[i].y)
    top = max(nodes, key=lambda i: points[i].y)
    end = next(i for i in nodes if i > top)
    B, T, E = points[bottom], points[top], points[end]

    capital = ufoLib2.objects.Glyph()
    rec = DecomposingRecordingPen(up)
    up["uni0241"].draw(rec)
    rec.replay(capital.getPen())
    cp = capital.contours[0].points
    on = [i for i, p in enumerate(cp) if p.type]
    peak = next(j for j in range(1, len(on) - 1)
                if cp[on[j]].y > cp[on[j - 1]].y and cp[on[j]].y > cp[on[j + 1]].y
                and cp[on[j]].y > 1000)
    a, b, c = on[peak - 1:peak + 2]
    stem = derive.stems_at(up, "i.sc", 300)[0]
    mid_y = B.y + 0.52 * (T.y - B.y)
    mid_x = derive.stems_at(up, name, mid_y)[-1][1] - 0.62 * (stem[1] - stem[0])
    R = Point(mid_x, mid_y, "curve", True)

    def fitted(start, source_start, source_end):
        sx = (start.x - T.x) / (cp[source_start].x - cp[b].x)
        sy = (start.y - T.y) / (cp[source_start].y - cp[b].y)
        return [Point(T.x + (p.x - cp[b].x) * sx, T.y + (p.y - cp[b].y) * sy,
                      p.type, p.smooth) for p in cp[source_start + 1:source_end + 1]]

    right = fitted(R, a, b)
    sx, sy = (E.x - T.x) / (cp[c].x - cp[b].x), (E.y - T.y) / (cp[c].y - cp[b].y)
    left = [Point(T.x + (p.x - cp[b].x) * sx, T.y + (p.y - cp[b].y) * sy,
                  p.type, p.smooth) for p in cp[b + 1:c + 1]]
    points[bottom + 1:end + 1] = [
        Point(B.x + 0.7 * (R.x - B.x), B.y),
        Point(R.x - 0.45 * (right[0].x - R.x), R.y - 0.45 * (right[0].y - R.y)),
        R, *right, *left,
    ]
    shear(glyph, SLANT, extremes=True)
    for contour in glyph.contours:
        round_smoothly(contour.points)
    redraw(font[name], glyph)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--italic-reference", type=Path)
    args = parser.parse_args()
    if not args.out.resolve().is_relative_to(ROOT / "build"):
        parser.error("review output must remain under build/")
    sys.path.insert(0, str(ROOT / "scripts/quality"))
    font = ufoLib2.Font.open(args.source)
    up = upright(font)
    glottal(font, up)
    gamma(font, up)
    italic = ufoLib2.Font.open(args.italic_reference) if args.italic_reference else None
    for name in NAMES:
        for key in ("org.myiadidot.accepted", "org.myiadidot.derived", "org.myiadidot.builtFrom"):
            font[name].lib.pop(key, None)
        if italic is None:
            font[name].lib["org.myiadidot.italicSource"] = "drawn"
        else:
            font[name].lib[DRAWN_KEY] = {
                "date": "2026-11-06", "why": "Paired gamma and glottal small-cap repairs",
                "source": fingerprint(italic, name),
            }
    font.save(args.out)


if __name__ == "__main__":
    main()
