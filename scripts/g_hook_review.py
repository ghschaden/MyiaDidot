"""Local Bold Italic G-hook drawings, proposed 2026-11-06.

Run with --out UFO to make a review copy; --install writes the three
drawings and marks them drawn so the style generator preserves them.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive
from built_from import fingerprint
from drawn import KEY
from italic_geometry import SLANT, redraw, shear, upright
from make_bold import round_smoothly

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/MyiaDidot-BoldItalic.ufo"
NAMES = ("uni0193", "uni0260", "uni0260.sc")


def revise(font):
    old_sc = copy.deepcopy(font["uni0260.sc"])
    up = upright(font)
    # Keep the final same-style bowls. A wider rising stroke meets the
    # terminal's right edge, replacing the old hairline and its ledge.
    for name, base, x, y0, top, thick, radii, ball, hair, cut in (
        ("uni0193", "G", 1190, 1280, 1500, 110, (185, 165), 95, 70,
         (1090, 1330, 10000, 10000)),
        ("uni0260.sc", "g.sc", 929, 930, 1090, 108, (145, 125), 75, 55,
         (750, 980, 10000, 10000)),
    ):
        pieces = [
            ("line", ((x, y0), (x, top), thick), (0, 0), (1, 1, 0, 0)),
            ("curl", {"at": ("pt", x, top, thick), "dir": 90,
                      "turn": "cw", "r": radii, "sweep": 200,
                      "ball": ball, "t": (thick, hair), "lead": 10},
             (0, 0), (1, 1, 0, 0)),
        ]
        path = derive.attach(up, base, [cut], pieces)
        made = ufoLib2.objects.Glyph(name)
        derive.draw_path(up, up[base], made, path)
        if name == "uni0260.sc":
            # Replace the rectangular cut's ledge by a rounded shoulder
            # into the hook. The bowl's preceding curve remains untouched.
            pts = made.contours[0].points
            i = next(i for i, p in enumerate(pts)
                     if p.type == "line" and p.y == 980)
            assert pts[i + 1].y == 980 and pts[i + 2].y == top
            start, end = pts[i - 1], pts[i + 2]
            pts[i:i + 3] = [Point(start.x + 60, start.y - 25),
                            Point(end.x, top - 110),
                            Point(end.x, top, "curve", True)]
        shear(made, SLANT, extremes=True)
        # The rising stroke and the terminal's right edge meet at a
        # shallow angle after union. Run that edge straight between its
        # retained ends instead of retaining the cut's intermediate node.
        pts = made.contours[0].points
        joins = [i for i, p in enumerate(pts)
                 if p.type == "line" and pts[(i + 1) % len(pts)].type == "line"
                 and cut[1] - 30 <= p.y <= cut[1] + 1 and p.x > x]
        assert len(joins) == 1
        del pts[joins[0]]
        # Keep the bowl at its existing horizontal position and the advance.
        dx = round(font[name].getBounds(font).xMin - made.getBounds(up).xMin)
        made.move((dx, 0))
        redraw(font[name], made)

    # The inner edge below the counter used two short bends, then another
    # in the descender. One cubic runs from the counter to the existing
    # tail, tangent to the retained curve at each end.
    g = copy.deepcopy(up["uni0260"])
    pts = g.contours[0].points
    assert len(pts) == 142 and pts[91].type == pts[100].type == "curve"
    pts[92:101] = [Point(665, 90), Point(648, -218),
                   Point(605, -320, "curve", True)]
    shear(g, SLANT, extremes=True)
    redraw(font["uni0260"], g)
    for name in NAMES:
        for contour in font[name].contours:
            round_smoothly(contour.points)
    # Preserve the existing small cap's lower bowl and bar exactly. The
    # boolean union otherwise subdivides its short curves differently.
    pts = font["uni0260.sc"].contours[0].points
    a = next(i for i, p in enumerate(pts) if p.type and p.y == 1068)
    b = next(i for i, p in enumerate(pts) if p.type and p.y == 1001)
    assert old_sc.contours[0].points[19].y == 1068
    assert old_sc.contours[0].points[59].y == 1001
    pts[:] = (copy.deepcopy(old_sc.contours[0].points[:20])
              + pts[a + 1:b] + copy.deepcopy(old_sc.contours[0].points[59:]))


def main():
    parser = argparse.ArgumentParser(__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--install", action="store_true")
    parser.add_argument("--source", type=Path, default=SOURCE,
                        help="unmodified before UFO (required for repeat trials)")
    args = parser.parse_args()
    font = ufoLib2.Font.open(args.source)
    revise(font)
    source = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    reasons = (
        "Ɠ: thicker upright hook joined to G's terminal without the ledge",
        "ɠ: continuous inner downstroke from the counter into the tail",
        "ɠ.sc: rising hook as the capital and Italic, on the final g.sc",
    )
    for name, why in zip(NAMES, reasons):
        font[name].lib.pop("org.myiadidot.accepted", None)
        font[name].lib[KEY] = {"date": "2026-11-06", "why": why,
                              "source": fingerprint(source, name)}
    if args.install:
        current = ufoLib2.Font.open(SOURCE)
        for name in NAMES:
            current.layers.defaultLayer.insertGlyph(font[name], name, overwrite=True)
        current.save()
    else:
        font.save(args.out)


if __name__ == "__main__":
    main()
