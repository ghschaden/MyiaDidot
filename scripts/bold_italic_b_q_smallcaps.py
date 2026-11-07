"""Local counter and stem repairs for Bold Italic b.sc/d.sc/q.sc; --out reviews."""

import argparse
import copy
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
from built_from import fingerprint
from drawn import KEY as DRAWN_KEY
from italic_geometry import SLANT, shear
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("b.sc", "d.sc", "q.sc")


def bounds(font, contour):
    pen = BoundsPen(font)
    contour.draw(pen)
    return pen.bounds


def round_b(font):
    glyph = copy.deepcopy(font["b.sc"])
    shear(glyph, -SLANT)
    lower, upper = glyph.contours[1:]
    lx0, ly0, lx1, ly1 = bounds(font, lower)
    ux0, uy0, ux1, uy1 = bounds(font, upper)
    sx, sy = (ux1 - ux0) / (lx1 - lx0), (uy1 - uy0) / (ly1 - ly0)
    lp, up = lower.points, upper.points
    a = next(i for i, p in enumerate(lp) if p.type == "line" and p.y == ly0)
    b = next(i for i, p in enumerate(lp) if p.type == "curve" and p.y == ly1)
    c = next(i for i, p in enumerate(up)
             if p.type == "line" and p.y == uy0 and up[i - 1].y == uy0)
    d = next(i for i, p in enumerate(up) if p.type == "curve" and p.y == uy1)
    up[c:d + 1] = [Point(ux0 + (p.x - lx0) * sx, uy0 + (p.y - ly0) * sy,
                         p.type, p.smooth) for p in lp[a:b + 1]]
    install_counter(font, glyph, 2)


def round_q(font):
    glyph, reference = copy.deepcopy(font["q.sc"]), copy.deepcopy(font["o.sc"])
    for g in (glyph, reference):
        shear(g, -SLANT)
    qp, op = glyph.contours[1].points, reference.contours[1].points
    # Keep the entire tail and the lower part of its main counter. Borrow
    # the approved o.sc's upper oval from right side through top to left.
    a = next(i for i, p in enumerate(qp) if p.type == "curve" and p.y == 608)
    b = next(i for i, p in enumerate(qp) if p.type == "curve" and p.y == 1000)
    c = next(i for i, p in enumerate(qp) if p.type == "curve" and p.y == 379)
    ra = next(i for i, p in enumerate(op) if p.type == "curve" and p.y == 733)
    rb = next(i for i, p in enumerate(op) if p.type == "curve" and p.y == 1000)
    rc = next(i for i, p in enumerate(op) if p.type == "curve" and p.y == 648)

    sx = (qp[a].x - qp[b].x) / (op[ra].x - op[rb].x)
    sy = (qp[a].y - qp[b].y) / (op[ra].y - op[rb].y)
    right = [Point(qp[b].x + (p.x - op[rb].x) * sx,
                   qp[b].y + (p.y - op[rb].y) * sy, p.type, p.smooth)
             for p in op[ra + 1:rb + 1]]
    # Same top, independent left-side fit because Q's tail makes its two
    # preserved side endpoints stand at different heights.
    sx = (qp[c].x - qp[b].x) / (op[rc].x - op[rb].x)
    sy = (qp[c].y - qp[b].y) / (op[rc].y - op[rb].y)
    left = [Point(qp[b].x + (p.x - op[rb].x) * sx,
                  qp[b].y + (p.y - op[rb].y) * sy, p.type, p.smooth)
            for p in op[rb + 1:rc + 1]]
    # The new arc enters the unchanged lower sides along their tangents.
    right[0].x = qp[a].x + ((right[0].y - qp[a].y)
                          * (qp[a].x - qp[a - 1].x) / (qp[a].y - qp[a - 1].y))
    left[-2].x = qp[c].x + ((left[-2].y - qp[c].y)
                          * (qp[c + 1].x - qp[c].x) / (qp[c + 1].y - qp[c].y))
    qp[a + 1:c + 1] = right + left
    install_counter(font, glyph, 1)


def install_counter(font, glyph, index):
    shear(glyph, SLANT, extremes=True)
    contour = glyph.contours[index]
    round_smoothly(contour.points)
    font[glyph.name].contours[index].points[:] = copy.deepcopy(contour.points)


def straighten_stem(font, name):
    glyph = copy.deepcopy(font[name])
    shear(glyph, -SLANT)
    outer, lower = [c.points for c in glyph.contours[:2]]
    upper = glyph.contours[2].points if name == "b.sc" else lower
    foot = next(p for p in outer if p.type == "curve" and p.y == 102)
    head = next(p for p in outer if p.type == "line" and p.y == 927)
    slope = (head.x - foot.x) / (head.y - foot.y)
    width = 310 if name == "b.sc" else 307  # existing main-stem weights
    k = 0.5523

    def left(y):
        return foot.x + slope * (y - foot.y)

    def right(y):
        return left(y) + width

    # Outside foot: the old serif started inside the stroke and pinched
    # it before the straight side. One bracket now widens into the serif.
    a = next(i for i, p in enumerate(outer) if p.type == "line" and p.y == 69)
    b = next(i for i, p in enumerate(outer) if p.type == "curve" and p.y == 102)
    height = 102 - 69
    x = left(102) - height
    hy = 102 - k * height
    outer[a:b + 1] = [Point(x, 69, "line", True), Point(x + k * height, 69),
                      Point(left(hy), hy), Point(left(102), 102, "curve", True)]
    # Outside head: continue the same straight edge to its head bracket.
    a = next(i for i, p in enumerate(outer) if p.type == "line" and p.y == 927)
    b = next(i for i, p in enumerate(outer) if p.type == "line" and p.y == 963)
    height = 963 - 927
    x = left(927) - height
    hy = 927 + k * height
    outer[a:b] = [Point(left(927), 927, "line", True), Point(left(hy), hy),
                   Point(x + k * height, 963), Point(x, 963, "curve", True)]

    # The counter sides form the other edge of the same straight stem.
    foot_y, head_y = lower[0].y, upper[-1].y
    a = next(i for i, p in enumerate(lower) if p.type == "line" and p.y == 69)
    height = foot_y - 69
    x = right(foot_y) + height
    hy = foot_y - k * height
    lower[:a] = [Point(right(foot_y), foot_y, "line", True), Point(right(hy), hy),
                 Point(x - k * height, 69), Point(x, 69, "curve", True)]
    lower[-1].x = right(lower[-1].y)
    upper[0].x = right(upper[0].y)
    a = next(i for i, p in enumerate(upper) if p.type == "line" and p.y == 962)
    height = 962 - head_y
    x = right(head_y) + height
    hy = head_y + k * height
    upper[a:] = [Point(x, 962, "line", True), Point(x - k * height, 962),
                 Point(right(hy), hy), Point(right(head_y), head_y, "curve", True)]
    shear(glyph, SLANT, extremes=True)
    for contour in glyph.contours:
        round_smoothly(contour.points)
    for i, contour in enumerate(glyph.contours):
        font[name].contours[i].points[:] = copy.deepcopy(contour.points)


def finish_barred_d(font, italic):
    """Finish the bar recipe's rounding on the final same-style D base."""
    glyph = font["uniA7C8.sc"]
    for contour in glyph.contours:
        pts = contour.points
        for i in range(len(pts) - 2, 0, -1):
            a, p, b = pts[i - 1:i + 2]
            if (a.type == p.type == b.type == "line" and 1000 < p.y < 1040
                    and abs((p.x - a.x) * (b.y - a.y) - (p.y - a.y) * (b.x - a.x))
                    / math.hypot(b.x - a.x, b.y - a.y) < 0.5):
                del pts[i]
        for i, p in enumerate(pts):
            a, b = pts[i - 1], pts[(i + 1) % len(pts)]
            if p.type == "line" and p.smooth and a.type and b.type is None and abs(p.y - a.y) > 100:
                b.x = round(p.x + (b.y - p.y) * (p.x - a.x) / (p.y - a.y))
            if p.type != "curve" or not p.smooth or a.type or b.type:
                continue
            ax, ay, bx, by = p.x - a.x, p.y - a.y, b.x - p.x, b.y - p.y
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if min(la, lb) < 10:
                continue
            turn = abs(math.degrees(math.atan2(ax * by - ay * bx, ax * bx + ay * by)))
            if 1 < turn < 3:
                dx, dy = ax / la + bx / lb, ay / la + by / lb
                length = math.hypot(dx, dy)
                dx, dy = dx / length, dy / length
                a.x, a.y = p.x - la * dx, p.y - la * dy
                b.x, b.y = p.x + lb * dx, p.y + lb * dy
        round_smoothly(pts)
    glyph.lib[DRAWN_KEY] = {
        "date": "2026-11-07", "why": "Local rounding finish of the bar on the final d.sc",
        "source": fingerprint(italic, glyph.name),
        "bases": {"d.sc": fingerprint(font, "d.sc")},
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    target.add_argument("--finish-barred-d", action="store_true")
    args = parser.parse_args()
    font = ufoLib2.Font.open(args.source)
    italic = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    if args.finish_barred_d:
        finish_barred_d(font, italic)
        current = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
        current.layers.defaultLayer.insertGlyph(font["uniA7C8.sc"], "uniA7C8.sc", overwrite=True)
        current.save()
        return
    round_b(font)
    for name in ("b.sc", "d.sc"):
        straighten_stem(font, name)
    round_q(font)
    for name in NAMES:
        font[name].lib.pop("org.myiadidot.accepted", None)
        font[name].lib[DRAWN_KEY] = {
            "date": "2026-11-06", "why": "Local small-cap counter and stem repairs",
            "source": fingerprint(italic, name),
        }
    if args.install:
        current = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo")
        for name in NAMES:
            current.layers.defaultLayer.insertGlyph(font[name], name, overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
