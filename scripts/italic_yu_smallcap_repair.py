"""Review a local Italic Ю.sc built from the approved i.sc and o.sc.

Use --out for a complete scratch UFO or --install for the production glyph.
"""

import argparse
import copy
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from built_from import fingerprint
from drawn import KEY as DRAWN_KEY
from italic_geometry import SLANT, redraw, shear
from make_bold import round_smoothly


def smooth_oval(glyph):
    """Make the two side joins tangent-continuous, retaining all endpoints."""
    for contour in glyph.contours:
        points = contour.points
        for i, point in enumerate(points):
            if point.type != "curve" or point.smooth:
                continue
            before, after = points[i - 1], points[(i + 1) % len(points)]
            if before.type is not None or after.type is not None:
                continue
            ax, ay = point.x - before.x, point.y - before.y
            bx, by = after.x - point.x, after.y - point.y
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            assert la > 10 and lb > 10
            dx, dy = ax / la + bx / lb, ay / la + by / lb
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            before.x, before.y = point.x - la * dx, point.y - la * dy
            after.x, after.y = point.x + lb * dx, point.y + lb * dy
            point.smooth = True


def repair(font):
    old = font["uni044E.sc"]
    stem, bowl = copy.deepcopy(font["i.sc"]), copy.deepcopy(font["o.sc"])
    smooth_oval(bowl)
    # Keep the bowl at the current right edge; use the final same-style
    # bases' stroke weights, with no weighting of the combined outline.
    shift = old.getBounds(font).xMax - bowl.getBounds(font).xMax
    bowl.move((shift, 0))
    for glyph in (stem, bowl):
        shear(glyph, -SLANT)
    stem_path = derive.to_path(None, rec=_record(stem))
    bowl_path = derive.to_path(None, rec=_record(bowl))
    path = derive.path_op(stem_path, bowl_path, "UNION")
    path = derive.path_op(path, derive.rect_path(300, 487, 600, 549), "UNION")
    made = ufoLib2.objects.Glyph("uni044E.sc")
    derive.draw_path(font, old, made, path)
    shear(made, SLANT, extremes=True)
    for contour in made.contours:
        round_smoothly(contour.points)
        # The approved i.sc has a one-unit rounding error at this short
        # head bracket. Align its handle locally in the new combined glyph.
        points = contour.points
        for i, point in enumerate(points):
            if point.type == "line" and point.smooth and point.y == 931:
                previous, handle = points[i - 1], points[(i + 1) % len(points)]
                handle.x = round(point.x + (handle.y - point.y)
                                 * (point.x - previous.x) / (point.y - previous.y))
    redraw(old, made)
    old.lib["org.myiadidot.italicSource"] = "drawn"
    for key in ("org.myiadidot.accepted", "org.myiadidot.derived",
                "org.myiadidot.builtFrom"):
        old.lib.pop(key, None)


def _record(glyph):
    rec = RecordingPen()
    glyph.draw(rec)
    return rec


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    target.add_argument("--finish-bold-italic", type=Path, metavar="BEFORE.ufo")
    args = parser.parse_args()
    if args.finish_bold_italic:
        path = Path(__file__).resolve().parents[1] / "sources/MyiaDidot-BoldItalic.ufo"
        current = ufoLib2.Font.open(path)
        before = ufoLib2.Font.open(args.finish_bold_italic)
        source = ufoLib2.Font.open(args.source)
        name = "uni044E.sc"
        if current[name].width != before[name].width:
            current[name].width = before[name].width
            current[name].lib[DRAWN_KEY] = {
                "date": "2026-11-06",
                "why": "Retain spacing after the approved Italic Yu small-cap repair",
                "source": fingerprint(source, name),
            }
        current.save()
        return
    font = ufoLib2.Font.open(args.source)
    repair(font)
    if args.install:
        path = Path(__file__).resolve().parents[1] / "sources/MyiaDidot-Italic.ufo"
        current = ufoLib2.Font.open(path)
        current.layers.defaultLayer.insertGlyph(font["uni044E.sc"], "uni044E.sc", overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
