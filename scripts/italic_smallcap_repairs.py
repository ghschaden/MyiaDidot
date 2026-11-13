"""Local drawings for Italic Ʀ, Ɓ and Ɗ small caps (2026-11-06).

Use --source BEFORE.ufo --out CANDIDATE.ufo to review; --install writes
only the three repaired glyphs, marked drawn, into the production Italic.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from built_from import fingerprint
from drawn import KEY as DRAWN_KEY
from drawn import mark_by_script
from italic_geometry import SLANT, redraw, shear, upright
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/MyiaDidot-Italic.ufo"
NAMES = ("uni0280.sc", "uni0253.sc", "uni0257.sc")


def smooth_hook_stem(glyph):
    """Remove the old serif's tiny reversals on both upper stem edges."""
    pts = glyph.contours[0].points
    i = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 931)
    j = next(j for j in range(i + 1, len(pts)) if pts[j].type and pts[j].y == 943)
    prev = next(pts[k] for k in range(i - 1, -1, -1) if pts[k].type)
    slope = (pts[i].x - prev.x) / (pts[i].y - prev.y)
    x = pts[i].x + slope * (943 - pts[i].y)
    pts[i:j + 1] = [Point(x, 943, "line", True)]
    # The hook's first handle continues the straight stem's direction.
    pts[i + 1].x = x + slope * (pts[i + 1].y - 943)
    for contour in glyph.contours[1:]:
        pts = contour.points
        if max(p.y for p in pts) != 972:
            continue
        j = next(j for j, p in enumerate(pts)
                 if p.type == "line" and p.y == 972 and p.x < 500)
        first, end = pts[0], pts[-1]
        slope = (first.x - end.x) / (first.y - end.y)
        h1, h2 = pts[j + 1], pts[j + 2]
        # One bracket joins the counter's straight side tangentially;
        # the short reversing curve left by the serif cut is removed.
        pts[j + 1:] = [Point(h1.x, h1.y),
                        Point(end.x + slope * (h2.y - end.y), h2.y),
                        Point(end.x, end.y, "curve", True)]


def repair(font):
    up = upright(font)
    # Cut within the actual stem, not the crossbar/bowl run at y=500.
    # The overlap keeps the lowered bowl joined to the retained stem.
    stem_right = min(derive.stems_at(up, "r.sc", y)[0][1] for y in (300, 900))
    cut = stem_right - 8
    foot_right = derive.stems_at(up, "r.sc", 10)[0][1]
    whole = derive.to_path(up, up["r.sc"])
    region = derive.path_op(derive.rect_path(cut, 80, derive.BIG, derive.BIG),
                            derive.rect_path(foot_right, -derive.BIG, derive.BIG, 80), "UNION")
    moved = derive.shifted(derive.path_op(whole, region, "INTERSECTION"), 0, -145)
    # The overlap strip must not make a second little descender under
    # the stem: only the leg, beyond the foot serif, descends.
    moved = derive.path_op(moved, derive.rect_path(-derive.BIG, -derive.BIG, foot_right, 0),
                           "DIFFERENCE")
    lowered = derive.path_op(derive.path_op(whole, region, "DIFFERENCE"), moved, "UNION")
    paths = {"uni0280.sc": ("r.sc", lowered)}

    # Compact upright curls as on the capitals, aligned to the left edge
    # of each small-cap stem. A round end touches both ring edges, avoiding
    # the dent where a separate ball intersects a short, tight curl.
    for name, base in (("uni0253.sc", "b.sc"), ("uni0257.sc", "d.sc")):
        left, _ = derive.stems_at(up, base, 943)[0]
        path = derive.curl(up, base, [(-derive.BIG, 943, left + 14, derive.BIG)],
                           at=("pt", left + 75, 943, 150), dir=90, turn="ccw",
                           r=(155, 109), sweep=190, ball="end", t=(150, 44))
        paths[name] = base, path

    for name, (base, path) in paths.items():
        made = ufoLib2.objects.Glyph(name)
        derive.draw_path(up, up[base], made, path)
        if name != "uni0280.sc":
            smooth_hook_stem(made)
        shear(made, SLANT, extremes=True)
        for contour in made.contours:
            round_smoothly(contour.points)
        redraw(font[name], made)
        mark_by_script(font, name, "scripts/italic_smallcap_repairs.py")
        for key in ("org.myiadidot.accepted", "org.myiadidot.derived", "org.myiadidot.builtFrom"):
            font[name].lib.pop(key, None)


def finish_bold_italic(before_path):
    """Record true extremes and retain the three letters' previous metrics."""
    path = ROOT / "sources/MyiaDidot-BoldItalic.ufo"
    font = ufoLib2.Font.open(path)
    source = ufoLib2.Font.open(SOURCE)
    before = ufoLib2.Font.open(before_path)
    for name in NAMES:
        if name != "uni0280.sc":
            made = copy.deepcopy(font[name])
            shear(made, -SLANT)
            smooth_bold_hook_stem(made)
            shear(made, SLANT, extremes=True)
            redraw(font[name], made)
        rec = RecordingPen()
        font[name].draw(rec)
        made = ufoLib2.objects.Glyph(name)
        derive.with_extremes(rec, made.getPen(), round_points=False, past=5)
        for contour in made.contours:
            round_smoothly(contour.points)
        redraw(font[name], made)
        # Keep the body at its prior horizontal position. The hooks'
        # reduced overhang should not respace the whole small-cap letter.
        dx = round(before[name].getBounds(before).xMax - font[name].getBounds(font).xMax)
        font[name].move((dx, 0))
        font[name].width = before[name].width
        font[name].lib[DRAWN_KEY] = {
            "date": "2026-11-06",
            "why": "Local small-cap repair: true extremes recorded and existing spacing retained",
            "source": fingerprint(source, name),
        }
    font.save()


def smooth_bold_hook_stem(glyph):
    """Keep the fitter from bending back at the head and foot of the stem."""
    pts = glyph.contours[0].points
    i = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 939)
    j = next(j for j in range(i + 1, len(pts)) if pts[j].type and pts[j].y == 1022)
    prev = next(pts[k] for k in range(i - 1, -1, -1) if pts[k].type)
    slope = (pts[i].x - prev.x) / (pts[i].y - prev.y)
    start, end, h2 = pts[i], pts[j], pts[j - 1]
    hy = start.y + 0.6 * (end.y - start.y)
    pts[i].smooth = True
    pts[i + 1:j + 1] = [Point(start.x + slope * (hy - start.y), hy),
                        Point(h2.x, end.y), Point(end.x, end.y, "curve", True)]
    for contour in glyph.contours[1:]:
        pts = contour.points
        if max(p.y for p in pts) != 962:
            continue
        j = next(j for j, p in enumerate(pts)
                 if p.type == "line" and p.y == 962 and p.x < 600)
        first, end = pts[0], pts[-1]
        height = 962 - end.y
        slope = (first.x - end.x) / (first.y - end.y)
        # Start beyond the straight side, so the bracket travels left
        # out of its horizontal head, then down onto the stem edge.
        pts[j] = Point(end.x + 0.8 * height, 962, "line", True)
        hy = end.y + 0.55 * height
        pts[j + 1:] = [Point(end.x, 962),
                        Point(end.x + slope * (hy - end.y), hy),
                        Point(end.x, end.y, "curve", True)]
    smooth_bold_hook_foot(glyph)


def smooth_bold_hook_foot(glyph):
    """One rounded bracket on each side of the stem, without reverse turns."""
    k = 0.5523
    pts = glyph.contours[0].points
    i = next(i for i, p in enumerate(pts)
             if p.type == "line" and p.y == 69 and pts[i - 1].type == "line"
             and pts[i - 1].y == 69)
    above = next(j for j in range(i + 1, len(pts))
                 if pts[j].type == "line" and pts[j].y > 200)
    j = next(j for j in range(above - 1, i, -1) if pts[j].type)
    end, high = pts[j], pts[above]
    height = end.y - 69
    assert 25 < height < 45
    slope = (high.x - end.x) / (high.y - end.y)
    sx = end.x - height
    hy = end.y - k * height
    pts[i:j + 1] = [Point(sx, 69, "line", True),
                    Point(sx + k * height, 69),
                    Point(end.x + slope * (hy - end.y), hy),
                    Point(end.x, end.y, "curve", True)]
    for contour in glyph.contours[1:]:
        pts = contour.points
        if not (pts[0].type == "line" and 95 <= pts[0].y <= 110):
            continue
        j = next(j for j, p in enumerate(pts) if p.type and p.y == 69)
        start, prev = pts[0], pts[-1]
        height = start.y - 69
        slope = (start.x - prev.x) / (start.y - prev.y)
        hy = start.y - k * height
        ex = start.x + height
        pts[0].smooth = True
        pts[1:j + 1] = [Point(start.x + slope * (hy - start.y), hy),
                        Point(ex - k * height, 69), Point(ex, 69, "curve", True)]


def round_bold_b_counter(font):
    """Use the lower counter's round side for the upper counter, fitted to its box."""
    glyph = copy.deepcopy(font["uni0253.sc"])
    shear(glyph, -SLANT)
    lower, upper = glyph.contours[1:]

    def bounds(contour):
        pen = BoundsPen(font)
        contour.draw(pen)
        return pen.bounds

    lx0, ly0, lx1, ly1 = bounds(lower)
    ux0, uy0, ux1, uy1 = bounds(upper)
    sx, sy = (ux1 - ux0) / (lx1 - lx0), (uy1 - uy0) / (ly1 - ly0)
    lp, up = lower.points, upper.points
    a = next(i for i, p in enumerate(lp) if p.type == "line" and p.y == ly0)
    b = next(i for i, p in enumerate(lp) if p.type == "curve" and p.y == ly1)
    c = next(i for i, p in enumerate(up)
             if p.type == "line" and p.y == uy0 and up[i - 1].y == uy0)
    d = next(i for i, p in enumerate(up) if p.type == "curve" and p.y == uy1)
    up[c:d + 1] = [Point(ux0 + (p.x - lx0) * sx, uy0 + (p.y - ly0) * sy,
                         p.type, p.smooth) for p in lp[a:b + 1]]
    # The upper counter's left stem edge and both head/foot joins stay
    # untouched; only its round side and the horizontal runs change.
    shear(glyph, SLANT, extremes=True)
    for contour in glyph.contours:
        round_smoothly(contour.points)
    font["uni0253.sc"].contours[2].points[:] = copy.deepcopy(glyph.contours[2].points)
    font["uni0253.sc"].lib[DRAWN_KEY]["why"] = (
        "Upper counter rounded from the lower counter; smooth stem brackets and spacing retained")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    target.add_argument("--finish-bold-italic", action="store_true")
    target.add_argument("--round-b-counter", action="store_true")
    parser.add_argument("--bold-before", type=Path,
                        help="before Bold Italic UFO, required for --finish-bold-italic")
    args = parser.parse_args()
    if args.round_b_counter:
        font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
        round_bold_b_counter(font)
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
        for name in NAMES:
            current.layers.defaultLayer.insertGlyph(font[name], name, overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
