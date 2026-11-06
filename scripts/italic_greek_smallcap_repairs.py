"""Local Italic delta/lambda slant and theta counter repairs.

Read --source BEFORE.ufo and write --out CANDIDATE.ufo for review.
--install replaces only these three glyphs in the production Italic.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from built_from import fingerprint
from drawn import KEY as DRAWN_KEY
from italic_geometry import redraw
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/MyiaDidot-Italic.ufo"
NAMES = ("delta.sc", "lambda.sc", "theta.sc")


def diagonal_slopes(font, name):
    """The two long outside flanks, measured as dx/dy in the slanted frame."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    edges = []
    previous = None
    for op, args in rec.value:
        if op == "lineTo" and previous is not None:
            x, y = args[0]
            dx, dy = x - previous[0], y - previous[1]
            if abs(dy) > 600:
                edges.append((abs(dy), dx / dy))
        if args:
            previous = args[-1]
        elif op in ("closePath", "endPath"):
            previous = None
    # The counter has shorter sides; the two longest belong to the outside.
    return sorted(slope for _, slope in sorted(edges, reverse=True)[:2])


def repair(font):
    for name, capital in (("delta.sc", "Delta"), ("lambda.sc", "Lambda")):
        right, left = diagonal_slopes(font, name)
        cap_right, cap_left = diagonal_slopes(font, capital)
        # x' = scale*x + shear*y: map both diagonal directions exactly,
        # leaving all vertical positions and the existing advance intact.
        scale = (cap_left - cap_right) / (left - right)
        shear = cap_right - scale * right
        glyph = font[name]
        x0 = glyph.getBounds(font).xMin
        for contour in glyph.contours:
            for point in contour.points:
                point.x = x0 + scale * (point.x - x0) + shear * point.y
        for anchor in glyph.anchors:
            anchor.x = round(x0 + scale * (anchor.x - x0) + shear * anchor.y)

    # theta.sc's old counter pinches and bends near the crossbar. Use
    # the approved o.sc's continuous oval, split only by the existing bar.
    theta = font["theta.sc"]
    oval = derive.counters(font, font["o.sc"])
    assert len(oval) == 1
    outer = copy.deepcopy(theta.contours[0])
    rec = RecordingPen()
    outer.draw(rec)
    outside = derive.to_path(None, rec=rec)
    # The outer theta bowl stands eight units right of o.sc at both ends.
    counter = derive.shifted(oval[0], 8)
    counter = derive.path_op(counter, derive.rect_path(-derive.BIG, 486,
                                                     derive.BIG, 548), "DIFFERENCE")
    outline = derive.path_op(outside, counter, "DIFFERENCE")
    made = ufoLib2.objects.Glyph("theta.sc")
    derive.draw_path(font, theta, made, outline)
    # Keep the outside's original control points, rather than pathops'
    # equivalent reparameterization.
    made.contours[0].points[:] = copy.deepcopy(outer.points)
    redraw(theta, made)

    for name in NAMES:
        glyph = font[name]
        for contour in glyph.contours:
            round_smoothly(contour.points)
        glyph.lib["org.myiadidot.italicSource"] = "drawn"
        for key in ("org.myiadidot.accepted", "org.myiadidot.derived",
                    "org.myiadidot.builtFrom"):
            glyph.lib.pop(key, None)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    target.add_argument("--finish-bold-italic", type=Path, metavar="BEFORE.ufo",
                        help="retain the regenerated Bold Italic's previous advances")
    args = parser.parse_args()
    if args.finish_bold_italic:
        path = ROOT / "sources/MyiaDidot-BoldItalic.ufo"
        current = ufoLib2.Font.open(path)
        before = ufoLib2.Font.open(args.finish_bold_italic)
        source = ufoLib2.Font.open(SOURCE)
        for name in NAMES:
            if current[name].width != before[name].width:
                current[name].width = before[name].width
                current[name].lib[DRAWN_KEY] = {
                    "date": "2026-11-06",
                    "why": "Retain spacing after the approved Italic Greek small-cap slant repair",
                    "source": fingerprint(source, name),
                }
        current.save()
        return
    font = ufoLib2.Font.open(args.source)
    repair(font)
    if args.install:
        current = ufoLib2.Font.open(SOURCE)
        for name in NAMES:
            current.layers.defaultLayer.insertGlyph(font[name], name, overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
