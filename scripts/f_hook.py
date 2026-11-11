"""The Italic's f with a hook below: its stem run into ȷ's descender.

    python scripts/f_hook.py SRC.ufo OUT.ufo                     candidates, for the sheet
    python scripts/f_hook.py SRC.ufo OUT.ufo --install --date D --review DOC

Old Standard's italic f ends in a flat cut below the baseline (-461). Asked
for and approved on proofs/italic-f-hook-2026-11-11.pdf (2026-11-11): the
hook other italic fs have, in f and in the f-ligatures; ſ stays as it is.

Each f foot (two line nodes on one level below -400, a stem's width apart,
the stem's edges running up from them) is replaced by the descender of
uni0237 from where its stem ends (its right edge's last node, its left
edge's first), moved so that its two ends lie on the f's edges. The result
is then redrawn onto clean nodes (redraw.py) and, with --install, put into
SRC.ufo marked drawn, as redraw.py --install does; lib
org.myiadidot.redrawn says "hook": the outline replaced was the flat-footed
one. The ligatures made from fl and ffl (f_b f_h f_k f_t ...) and ᵮ follow
by themselves; the long-s ligatures clear the hook away
(italic_ligatures.py).

Run on a glyph that has the hook already it finds no foot and leaves it.
"""

import argparse
import copy
import sys
from pathlib import Path

import ufoLib2
from ufoLib2.objects import Contour, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))

import redraw as R  # noqa: E402

NAMES = ("f", "ff", "fi", "fl", "ffi", "ffl", "f_j", "f_f_j")
MODEL = "uni0237"
FOOT_BELOW = -400   # a foot's level lies under this
STEM = (120, 260)   # a foot's width, from the Italic's to the Bold Italic's
RIGHT_END, LEFT_END = (331, -89), (201, -41)  # where ȷ's stem ends: its tail starts and stops there


def tail_of(model):
    """ȷ's descender: the points from its stem's right edge round the hook
    to its left edge, and the two ends"""
    (c,) = model.contours
    pts = list(c.points)

    def nearest(xy):
        return min((i for i, p in enumerate(pts) if p.type), key=lambda i: abs(pts[i].x - xy[0]) + abs(pts[i].y - xy[1]))

    a, b = nearest(RIGHT_END), nearest(LEFT_END)
    if abs(pts[a].y - RIGHT_END[1]) > 40 or abs(pts[b].y - LEFT_END[1]) > 40 or pts[a].type != "line":
        raise ValueError(f"{MODEL}'s stem ends are not where they were: look at RIGHT_END, LEFT_END")
    return pts[a:] + pts[: b + 1]


def x_on(p, q, y):
    return p.x + (q.x - p.x) * (y - p.y) / (q.y - p.y)


def hooked(glyph, model):
    """a copy of glyph with every f foot replaced by the hook; the number of feet"""
    tail = tail_of(model)
    new = copy.deepcopy(glyph)
    feet = 0
    for ci, c in enumerate(new.contours):
        pts = list(c.points)
        while True:
            ons = [i for i, p in enumerate(pts) if p.type]
            for k, i in enumerate(ons):
                j, h, m = ons[(k + 1) % len(ons)], ons[k - 1], ons[(k + 2) % len(ons)]
                r, left, up_r, up_l = pts[i], pts[j], pts[h], pts[m]
                if not (r.y == left.y < FOOT_BELOW and STEM[0] <= r.x - left.x <= STEM[1]
                        and r.type == left.type == up_l.type == "line" and (j - i) % len(pts) == 1
                        and (i - h) % len(pts) == 1 and (m - j) % len(pts) == 1
                        and up_r.y > 0 and up_l.y > 0):
                    continue
                # the tail's ends onto the stem's edges, both as near as one shift allows
                dx = round((x_on(up_r, r, tail[0].y) - tail[0].x + x_on(left, up_l, tail[-1].y) - tail[-1].x) / 2)
                piece = [Point(p.x + dx, p.y, p.type, p.smooth) for p in tail]
                piece[0].smooth = piece[-1].smooth = False
                lo, hi = sorted((i, j))
                pts = pts[:lo] + piece + pts[hi + 1:] if j - i == 1 else piece + pts[lo + 1: hi]
                feet += 1
                break
            else:
                break
        new.contours[ci] = Contour(pts)
    return new, feet


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--review")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review")
    font = ufoLib2.Font.open(a.src)
    out = ufoLib2.Font.open(a.src)
    spec = R.spec_for(a.src, None)
    failed = 0
    for name in NAMES:
        raw, feet = hooked(font[name], font[MODEL])
        if not feet:
            print(f"{name:<8} no flat foot: left as it is")
            continue
        new, rep = R.redraw(raw, R.TOL, spec.get(name))
        fail, look = R.gate(rep, None)
        print(f"{name:<8}{feet} hook(s) {rep['nodes_before']:>3} ->{rep['nodes_after']:>3} nodes  {rep['dev']:.1f} from the construction  "
              + ("FAIL: " + "; ".join(fail) if fail else "candidate") + ("  [look: " + "; ".join(look) + "]" if look else ""))
        failed += bool(fail)
        g = out[name]
        g.clearContours()
        for c in new.contours:
            g.appendContour(c)
        if a.install and not fail:
            R.install(font, name, new, a.date, a.review, rep)
            font[name].lib[R.KEY]["hook"] = True
    out.save(a.out, overwrite=True)
    if a.install:
        font.save()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
