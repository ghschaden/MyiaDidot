"""Florin/P-hook proposals from final same-style drawn references.

The lowercase florin supplies the descending gesture, and the accepted hooked
B small cap supplies the P's head. --out draws a scratch candidate; --install
installs only the approved hooks from --source and records their acceptance.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from italic_geometry import SLANT, redraw, shear, upright
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
REVIEW = "docs/hook-reference-reset-review-2026-11-07.md"


def align_inherited_handle(glyph, y):
    """Correct a one-unit short-handle rounding error in the new drawing."""
    for contour in glyph.contours:
        points = contour.points
        for i, point in enumerate(points):
            if point.type == "line" and point.smooth and point.y == y:
                previous, handle = points[i - 1], points[(i + 1) % len(points)]
                if previous.type and handle.type is None:
                    x = round(point.x + (handle.y - point.y)
                              * (point.x - previous.x) / (point.y - previous.y))
                    assert abs(x - handle.x) <= 1
                    handle.x = x


def finish(font, name, made):
    shear(made, SLANT, extremes=True)
    for contour in made.contours:
        round_smoothly(contour.points)
    redraw(font[name], made)
    for key in ("org.myiadidot.accepted", "org.myiadidot.derived",
                "org.myiadidot.builtFrom", "org.myiadidot.drawn"):
        font[name].lib.pop(key, None)
    font[name].lib["org.myiadidot.italicSource"] = "drawn"


def florin(font, up, name, base, depth):
    # Translate the lowercase's complete tail vertically, retaining its curve
    # proportions and contrast. Match horizontal scale to this F's own stem.
    join = 250
    dy = depth - up["florin"].getBounds(up).yMin
    source_left, source_right = derive.stems_at(up, "florin", join - dy)[0]
    left, right = derive.stems_at(up, base, join)[0]
    sx = (right - left) / (source_right - source_left)
    dx = left - sx * source_left
    terminal = copy.deepcopy(up["florin"])
    points = terminal.contours[0].points
    # The lowercase's terminal is oversized at a capital stem's weight.
    # Reduce only the terminal about its return into the inner trough;
    # keep the full descending stroke and the two trough extrema intact.
    pivot = points[15]
    px, py = pivot.x, pivot.y
    for point in points[:15] + [points[-1]]:
        point.x = px + 0.78 * (point.x - px)
        point.y = py + 0.78 * (point.y - py)
    points[-2].x = px + 0.78 * (points[-2].x - px)
    rec = RecordingPen()
    terminal.draw(TransformPen(rec, (sx, 0, 0, 1, dx, dy)))
    tail = derive.path_op(derive.to_path(None, rec=rec),
                         derive.rect_path(-derive.BIG, -derive.BIG, derive.BIG, join),
                         "INTERSECTION")
    body = derive.path_op(derive.to_path(up, up[base]),
                         derive.rect_path(-derive.BIG, join, derive.BIG, derive.BIG),
                         "INTERSECTION")
    path = derive.path_op(body, tail, "UNION")
    old_stem = derive.stems_at(up, name, 600)[0]
    base_stem = derive.stems_at(up, base, 600)[0]
    shift = (sum(old_stem) - sum(base_stem)) / 2
    made = ufoLib2.objects.Glyph(name)
    derive.draw_path(up, up[base], made, derive.shifted(path, shift))
    # Remove the clipping seam: extend each F edge down to the existing
    # tail curve and align its first handle. This avoids a line-line jog
    # where the lowercase's almost-upright stem differs slightly from F.
    for contour in made.contours:
        points = contour.points
        for i in range(len(points) - 1, -1, -1):
            point = points[i]
            if point.type != "line" or abs(point.y - join) > 0.01:
                continue
            previous, following = points[i - 1], points[(i + 1) % len(points)]
            if not (previous.type and following.type):
                continue
            body_point, tail_point = (previous, following) if previous.y > join else (following, previous)
            slope = (body_point.x - point.x) / (body_point.y - point.y)
            tail_point.x = point.x + slope * (tail_point.y - join)
            handle = points[(i + 2) % len(points)] if previous.y > join else points[i - 2]
            assert handle.type is None
            handle.x = tail_point.x + slope * (handle.y - tail_point.y)
            tail_point.smooth = True
            del points[i]
    finish(font, name, made)
    if name == "florin.sc" and font.info.styleName == "Italic":
        align_inherited_handle(font[name], 931)
    if name == "uni0191" and font.info.styleName.replace(" ", "") == "BoldItalic":
        fair_tail_join(font[name])


def fair_tail_join(glyph):
    """Merge the short clipping remnant into its tail arc, within 3 units."""
    import numpy as np
    from stroke_bold import bez, fit_cubic, unit

    for contour in glyph.contours:
        pts = contour.points
        for i in range(3, len(pts) - 4):
            if not (pts[i - 3].type and pts[i].type == "curve"
                    and pts[i + 3].type == "curve" and pts[i + 4].type == "line"
                    and all(pts[j].type is None for j in (i - 2, i - 1, i + 1, i + 2))
                    and 0 < pts[i].y < 200):
                continue
            a = np.array([(p.x, p.y) for p in pts[i - 3:i + 1]], float)
            b = np.array([(p.x, p.y) for p in pts[i:i + 4]], float)
            end = np.array((pts[i + 4].x, pts[i + 4].y), float)
            if np.linalg.norm(b[3] - b[0]) > 80 or np.linalg.norm(end - b[3]) < 500:
                continue
            samples = np.concatenate((bez(a, np.linspace(0, 1, 100)),
                                      bez(b, np.linspace(0, 1, 40))[1:]))
            fitted, distances = fit_cubic(samples, unit(a[1] - a[0]), unit(end - b[3]))
            if fitted is None or max(distances) > 3:
                raise ValueError("Florin tail finishing exceeds its three-unit bound")
            pts[i - 2:i + 4] = [Point(round(fitted[1][0]), round(fitted[1][1])),
                                Point(round(fitted[2][0]), round(fitted[2][1])),
                                Point(round(fitted[3][0]), round(fitted[3][1]), "curve", True)]
            round_smoothly(pts)
            break


def p_hook(font, up):
    name, base, reference = "uni01A5.sc", "p.sc", "uni0253.sc"
    made = copy.deepcopy(up[base])
    pts = made.contours[0].points
    ref = up[reference].contours[0].points
    # Approved B's entire upper-left gesture: straight stem, open eye, compact
    # terminal, and smooth fall onto the head. P's own counter stays intact.
    start = next(i for i, p in enumerate(ref) if p.type == "line" and p.y == 939)
    end = next(i for i in range(start + 1, len(ref))
               if ref[i].type and ref[i].y == 1040)
    a = next(i for i, p in enumerate(pts) if p.type == "line" and p.y == 922)
    b = next(i for i in range(a + 1, len(pts))
             if pts[i].type == "line" and pts[i].y == 1040)
    pl, pr = derive.stems_at(up, base, 700)[0]
    rl, rr = derive.stems_at(up, reference, 700)[0]
    sx = (pr - pl) / (rr - rl)
    slope = (pts[a].x - pts[a - 1].x) / (pts[a].y - pts[a - 1].y)
    x = pts[a].x + slope * (ref[start].y - pts[a].y)
    graft = copy.deepcopy(ref[start:end + 1])
    for point in graft:
        point.x = x + (point.x - ref[start].x) * sx
    pts[a:b + 1] = graft
    old_left = derive.stems_at(up, name, 700)[0][0]
    made.move((old_left - pl, 0))
    finish(font, name, made)
    align_inherited_handle(font[name], 105)


def install(source, bold):
    """Install reviewed same-style hooks, retaining every other production glyph."""
    from accepted import DRAFT_KEYS, stamp
    from built_from import fingerprint
    from drawn import KEY as DRAWN_KEY
    from smallcaps import SMALLCAP_KERNING

    style = "BoldItalic" if bold else "Italic"
    proposed = ufoLib2.Font.open(source)
    assert proposed.info.styleName.replace(" ", "") == style
    font = ufoLib2.Font.open(ROOT / "sources" / ("MyiaDidot-" + style + ".ufo"))
    italic = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo") if bold else None
    names = ("uni0191", "florin.sc", "uni01A5.sc") if bold else ("uni0191", "florin.sc")
    for name in names:
        glyph = copy.deepcopy(proposed[name])
        if name == "florin.sc" and not bold:
            align_inherited_handle(glyph, 931)
        if name == "uni01A5.sc":
            align_inherited_handle(glyph, 105)
        if name == "uni0191" and bold:
            fair_tail_join(glyph)
        for key in (*DRAFT_KEYS, "org.myiadidot.accepted", "org.myiadidot.derived",
                    "org.myiadidot.builtFrom", DRAWN_KEY):
            glyph.lib.pop(key, None)
        if bold:
            glyph.lib[DRAWN_KEY] = {
                "date": "2026-11-07",
                "why": "Approved local Florin/P-hook drawing from final same-style references",
                "source": fingerprint(italic, name),
            }
        else:
            glyph.lib["org.myiadidot.italicSource"] = "drawn"
        font.layers.defaultLayer.insertGlyph(glyph, name, overwrite=True)
        stamp(font, name, "2026-11-07", REVIEW)
    font.kerning.update(SMALLCAP_KERNING[style])
    font.save()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    parser.add_argument("--bold", action="store_true")
    args = parser.parse_args()
    if args.install:
        install(args.source, args.bold)
        return
    if not args.out.resolve().is_relative_to(ROOT / "build"):
        parser.error("candidate UFO must remain under build/")
    font = ufoLib2.Font.open(args.source)
    up = upright(font)
    florin(font, up, "uni0191", "F", -292)
    florin(font, up, "florin.sc", "f.sc", -224)
    if args.bold:
        p_hook(font, up)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    font.save(args.out)


if __name__ == "__main__":
    main()
