"""Smooth the Italic ƥ hook-to-stem join locally (2026-11-06).

Use --source BEFORE.ufo --out CANDIDATE.ufo to review, or --install to
write only uni01A5 to the production Italic, marked drawn.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint
from derive import with_extremes
from drawn import KEY as DRAWN_KEY
from drawn import mark_by_script
from italic_geometry import SLANT, shear
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/MyiaDidot-Italic.ufo"


def repair(font):
    glyph = copy.deepcopy(font["uni01A5"])
    shear(glyph, -SLANT)
    pts = glyph.contours[0].points
    left = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 1143)
    root = next(i for i in range(left + 1, len(pts)) if pts[i].type and pts[i].y == 1150)
    low = next(pts[i] for i in range(left - 1, -1, -1) if pts[i].type)
    slope = (pts[left].x - low.x) / (pts[left].y - low.y)
    x = low.x + slope * (1150 - low.y)
    pts[left:root + 1] = [Point(x, 1150, "line", True)]
    pts[left + 1].x = x + slope * (pts[left + 1].y - 1150)

    right = max(i for i, p in enumerate(pts)
                if i > left + 1 and p.type == "curve" and p.y == 1150)
    low_index = next(i for i in range(right + 1, len(pts))
                     if pts[i].type == "line" and pts[i].y == 700)
    high = next(pts[i] for i in range(low_index - 1, right, -1) if pts[i].type)
    low = pts[low_index]
    slope = (high.x - low.x) / (high.y - low.y)
    x = low.x + slope * (1150 - low.y)
    pts[right].x, pts[right].smooth = x, True
    pts[right - 1].x = x + slope * (pts[right - 1].y - 1150)
    del pts[right + 1:low_index]
    shear(glyph, SLANT, extremes=True)
    for contour in glyph.contours:
        round_smoothly(contour.points)
    # Preserve the bowl's counter exactly, and replace only the outer path.
    font["uni01A5"].contours[0].points[:] = copy.deepcopy(glyph.contours[0].points)
    mark_by_script(font, "uni01A5", "scripts/p_hook_join.py")
    font["uni01A5"].lib.pop("org.myiadidot.accepted", None)


def finish_bold_italic(before):
    """Finish the generated dependent without changing its established spacing."""
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
    source = ufoLib2.Font.open(SOURCE)
    old = ufoLib2.Font.open(before)
    glyph = font["uni01A5"]
    for contour in glyph.contours:
        pts = contour.points
        for i, p in enumerate(pts):
            if p.type != "line" or not 600 <= p.y <= 640:
                continue
            handle = pts[(i + 1) % len(pts)]
            if handle.type is not None:
                continue
            prev = next(pts[k] for k in range(i - 1, -1, -1) if pts[k].type)
            handle.x = p.x + (p.x - prev.x) / (p.y - prev.y) * (handle.y - p.y)
            p.smooth = True
    rec = RecordingPen()
    glyph.draw(rec)
    made = ufoLib2.objects.Glyph("uni01A5")
    with_extremes(rec, made.getPen(), round_points=False, past=5)
    for contour in made.contours:
        round_smoothly(contour.points)
    glyph.clearContours()
    for contour in made.contours:
        contour.drawPoints(glyph.getPointPen())
    dx = round(old["uni01A5"].getBounds(old).xMin - glyph.getBounds(font).xMin)
    glyph.move((dx, 0))
    glyph.width = old["uni01A5"].width
    glyph.anchors = copy.deepcopy(old["uni01A5"].anchors)
    glyph.lib[DRAWN_KEY] = {
        "date": "2026-11-06",
        "why": "Finished Italic hook join propagated; local tangent/extrema finishing and spacing retained",
        "source": fingerprint(source, "uni01A5"),
    }
    font.save()


def strengthen_bold_hook(font):
    """Match ƥ's rising hook to its stem, without the former shoulder."""
    glyph = copy.deepcopy(font["uni01A5"])
    shear(glyph, -SLANT)
    pts = glyph.contours[0].points
    low = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 620)
    high = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 1128)
    # Continue the p stem straight into the heavier hook, deleting the
    # short outward shoulder below it. Preserve the existing slight taper.
    x = pts[low].x + 3
    pts[high].x = x
    pts[high + 1].x = x + 1
    del pts[low + 1:high]
    inner = next(i for i, p in enumerate(pts) if p.type == "curve" and p.y == 1146)
    pts[inner].x += 24
    pts[inner - 1].x += 24
    pts[inner - 2].x += 12
    pts[inner + 1].x += 24
    pts[inner + 2].x += 17
    pts[inner + 3].x += 8
    shear(glyph, SLANT, extremes=True)
    for contour in glyph.contours:
        round_smoothly(contour.points)
    font["uni01A5"].contours[0].points[:] = copy.deepcopy(glyph.contours[0].points)
    font["uni01A5"].lib.pop("org.myiadidot.accepted", None)
    font["uni01A5"].lib[DRAWN_KEY]["why"] = (
        "Hook rising stroke strengthened to match p stem; smooth join, spacing and anchors retained"
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    target.add_argument("--finish-bold-italic", action="store_true")
    target.add_argument("--strengthen-bold-hook", action="store_true")
    parser.add_argument("--bold-before", type=Path)
    args = parser.parse_args()
    if args.strengthen_bold_hook:
        font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
        strengthen_bold_hook(font)
        font.save()
        return
    if args.finish_bold_italic:
        if args.bold_before is None:
            parser.error("--finish-bold-italic requires --bold-before")
        finish_bold_italic(args.bold_before)
        return
    font = ufoLib2.Font.open(args.source)
    repair(font)
    if args.install:
        current = ufoLib2.Font.open(SOURCE)
        current.layers.defaultLayer.insertGlyph(font["uni01A5"], "uni01A5", overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
