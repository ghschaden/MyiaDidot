"""The Italic's ⱳ: its arm one thickness into the hook, nearer the middle stem, a larger ball.

    python scripts/w_hook.py SRC.ufo OUT.ufo                     the candidate, for the sheet
    python scripts/w_hook.py SRC.ufo OUT.ufo --install --date D --review DOC

The recipe's ⱳ (make_italic: w's arm cut at 645, a straight piece and a
curl; the join faired by derive.fair_joins) had its arm's outer edge
refitted as one curve from the curl down to w's node at 1129,117, on w's
handles: the arm ran 38 units wide at mid height where w's own is 58-60
and swelled to 69 in the hook ("a thickening in the final hook", on the
sheet of 2026-11-11). Asked for and approved there, version H
(proofs/italic-w-hook-arm-2026-11-11.pdf):

- the arm in w's own form but nearer the middle stem: its x drawn towards
  X0 so that its top stands SHIFT units further left, the hook moved with it;
- the inner edge one curve from w's at YI into the hook;
- the outer edge drawn anew from the bowl's lowest point: THICK across
  the stroke from YC up into the hook, thickening below it in the bowl's
  turn (46 at the bottom);
- the hook's own side of the arm moved out to that thickness;
- the ball BALL times as large, about a point left of where it meets the
  ring's inner edge, so that it grows right and down and the hook's eye
  stays open; the advance follows the hook's right side.

The construction reads the recipe's outline by its nodes; on a glyph that
has not got them (made already, or the recipe changed) it stops. The
result is redrawn onto clean nodes (redraw.py) and, with --install, put
into SRC.ufo marked drawn, as redraw.py --install does; lib
org.myiadidot.redrawn says "hook". The Bold Italic's ⱳ is drawn by itself
(2026-11-08) and does not follow.
"""

import argparse
import copy
import math
import sys
from pathlib import Path

import numpy as np
import ufoLib2
from ufoLib2.objects import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))

import redraw as R  # noqa: E402

NAME = "uni2C73"
SHIFT = 50.0   # units the arm's top and the hook stand nearer the middle stem
X0 = 830.0     # the arm is drawn in from here (the second bowl's lowest point)
BALL = 1.5     # the ball's size against the recipe's
BALL_AT = (1476.0, 830.0)  # about this point: 49 units left of where the ball meets the ring
THICK = 74.0   # across the arm, from YC up into the hook
WAS = 68.2     # across the hook's stroke where the arm runs into it, as the recipe gives it
YI = 554.0     # the inner edge leaves w's own here
YC = 260.0     # the arm is THICK from here up
BOTTOM = 46.0  # across the bowl at its lowest point
# the recipe's nodes the construction stands on (w's arm, the hook's two ends, the ball)
ARM_IN = [(843, 23), (1106, 23), (1291, 421), (1291, 601)]   # w's inner edge, going up
HOOK_IN, HOOK_OUT = (1327, 773), (1395, 773)                 # where the ring's two edges begin
HOOK_DIR = (18.0, 65.0)                                      # the way the ring's edges leave the arm
STUBS = [(1326, 770), (1326, 771), (1327, 772),              # the bits of 3-8 units the recipe left
         (1395, 772), (1394, 771), (1394, 770), (1394, 769), (1393, 767), (1394, 765)]  # between arm and ring
OUTER_FROM, OUTER_TO = (1339, 547), (820, -23)               # the outer edge's first handle; the bowl's lowest point
BALL_FROM, BALL_TO = (1623, 839), (1485, 845)                # the handle before the ball; the ring's inner top
RING_SIDE = (1406, 813)                                      # the ring's inner edge from here down is the arm's side


def bez(p, t):
    p = np.array(p, float)
    t = np.atleast_1d(t)[:, None]
    m = 1 - t
    return m**3 * p[0] + 3 * m * m * t * p[1] + 3 * m * t * t * p[2] + t**3 * p[3]


def split(p, t):
    p = [np.array(q, float) for q in p]
    a, b, c = p[0] + (p[1] - p[0]) * t, p[1] + (p[2] - p[1]) * t, p[2] + (p[3] - p[2]) * t
    d, e = a + (b - a) * t, b + (c - b) * t
    m = d + (e - d) * t
    return [p[0], a, d, m], [m, e, c, p[3]]


def t_at_y(p, y):
    """where a curve running up reaches height y"""
    lo, hi = 0.0, 1.0
    for _ in range(50):
        t = (lo + hi) / 2
        if bez(p, t)[0][1] < y:
            lo = t
        else:
            hi = t
    return t


def unit(v):
    return v / np.linalg.norm(v)


def offset(curve, ts):
    """a curve's points, its normals to the right of the way up, its directions"""
    p = bez(curve, ts)
    d = bez(curve, np.clip(ts + 1e-3, 0, 1)) - bez(curve, np.clip(ts - 1e-3, 0, 1))
    d /= np.hypot(*d.T)[:, None]
    return p, np.c_[d[:, 1], -d[:, 0]], d


def fit(a0, d0, a1, d1, target):
    """one curve from a0 (leaving along d0) to a1 (arriving along d1), its
    handle lengths those that keep it nearest the target points; with how
    far it stays from them"""
    span = np.linalg.norm(a1 - a0)
    best = None
    for a in np.arange(0.08, 0.7, 0.02):
        for b in np.arange(0.08, 0.7, 0.02):
            c = [a0, a0 + d0 * span * a, a1 - d1 * span * b, a1]
            pts = bez(c, np.linspace(0, 1, 60))
            e = max(np.min(np.hypot(*(pts - q).T)) for q in target[::3])
            if best is None or e < best[0]:
                best = (e, c)
    return best


def hooked(glyph):
    """A copy of the recipe's ⱳ with the arm, hook and ball as described
    above, and what it measures; None if the recipe's nodes are not there."""
    g = copy.deepcopy(glyph)
    if len(g.contours) != 1:
        return None, {}
    c = g.contours[0]
    have = {(p.x, p.y) for p in c.points}
    needed = [*ARM_IN, HOOK_IN, HOOK_OUT, *STUBS, OUTER_FROM, OUTER_TO, BALL_FROM, BALL_TO, RING_SIDE, (1036, 22), (917, -23)]
    if any(xy not in have for xy in needed):
        return None, {}

    def idx(xy):
        return next(k for k, p in enumerate(c.points) if (p.x, p.y) == tuple(xy))

    def rounded(q):
        return tuple(int(round(v)) for v in q)

    for xy in STUBS:
        del c.points[idx(xy)]
    k = (ARM_IN[3][0] - SHIFT - X0) / (ARM_IN[3][0] - X0)

    def sx(x):
        return X0 + (x - X0) * k

    right_was = max(p.x for p in c.points if p.type)
    # the ball
    b0, b1 = idx(BALL_FROM), idx(BALL_TO)
    for p in c.points[b0:b1]:
        p.x = BALL_AT[0] + (p.x - BALL_AT[0]) * BALL
        p.y = BALL_AT[1] + (p.y - BALL_AT[1]) * BALL
    # the ring's inner edge runs level into its top: the handles before it stay under it
    for p in c.points[b1 - 2:b1]:
        p.y = min(p.y, BALL_TO[1])
    # the hook: its arm's side out to the arm's thickness, all of it nearer the stem
    i_in, i_out = idx(HOOK_IN), idx(HOOK_OUT)
    slope = HOOK_DIR[0] / HOOK_DIR[1]
    gain = (THICK - WAS) / math.cos(math.atan(slope))
    for p in c.points[idx(RING_SIDE):i_out + 1]:
        p.x += gain
    for p in c.points[i_in:i_out + 1]:
        p.x -= SHIFT
    # the inner edge: w's, narrowed, up to YI; one curve from there into the hook
    t = np.linspace(0, 1, 200)
    arm = [(sx(x), y) for x, y in ARM_IN]
    low, _ = split(arm, t_at_y(arm, YI))
    q, dq = low[3], unit(low[3] - low[2])
    end, d_end = np.array((HOOK_IN[0] - SHIFT, float(HOOK_IN[1]))), unit(np.array(HOOK_DIR))
    span = np.linalg.norm(end - q)
    top = [q, q + dq * span / 3, end - d_end * span / 3, end]
    inner = np.vstack([bez(low, t), bez(top, t)])
    # the outer edge above YC: THICK from the inner edge, one curve down from the hook
    t0 = t_at_y(low, YC)
    p_low, n_low, d_low = offset(low, np.linspace(t0, 1, 30))
    p_top, n_top, d_top = offset(top, np.linspace(0, 1, 40))
    target = np.vstack([p_low + n_low * THICK, p_top + n_top * THICK])
    p2, d2 = target[0], d_low[0]
    a = np.array((HOOK_OUT[0] + gain - SHIFT, float(HOOK_OUT[1])))
    e_up, upper = fit(a, -d_end, p2, -d2, target)
    # and below it: from YC down into the bowl's lowest point, level there, thinning steadily
    p_bowl, n_bowl, _ = offset(low, np.linspace(0, t0, 40))
    grow = BOTTOM + (THICK - BOTTOM) * np.linspace(0, 1, 40)
    e_low, lower = fit(p2, -d2, np.array(OUTER_TO, float), np.array((-1.0, 0.0)), (p_bowl + n_bowl * grow[:, None])[5:])
    j, j1 = idx(OUTER_FROM), idx(OUTER_TO)
    c.points[j:j1] = [Point(*rounded(upper[1])), Point(*rounded(upper[2])), Point(*rounded(p2), type="curve", smooth=True),
                      Point(*rounded(lower[1])), Point(*rounded(lower[2]))]
    i = idx(ARM_IN[1])
    c.points[i:i + 5] = [Point(*rounded(low[1])), Point(*rounded(low[2])), Point(*rounded(q), type="curve", smooth=True),
                         Point(*rounded(top[1])), Point(*rounded(top[2]))]
    for p in c.points:
        p.x, p.y = round(p.x), round(p.y)
    # the advance: the right side bearing kept
    moved = int(round(max(p.x for p in c.points if p.type) - right_was))
    g.width += moved
    outer = np.vstack([bez(lower, t)[::-1], bez(upper, t)[::-1]])
    across = np.array([np.min(np.hypot(*(inner - p).T)) for p in outer])
    above = across[outer[:, 1] >= YC]
    return g, {"across": (float(above.min()), float(above.max())), "fit": (e_up, e_low), "advance": moved}


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
    raw, says = hooked(font[NAME])
    if raw is None:
        print(f"{NAME}: not the recipe's outline (made already, or the recipe changed): left as it is")
        sys.exit(0)
    new, rep = R.redraw(raw, R.TOL, R.spec_for(a.src, None).get(NAME))
    fail, look = R.gate(rep, None)
    print(f"{NAME}  arm {says['across'][0]:.0f}-{says['across'][1]:.0f} across from y {YC:.0f} up, advance {says['advance']:+d}  "
          f"{rep['nodes_before']} -> {rep['nodes_after']} nodes  {rep['dev']:.1f} from the construction  "
          + ("FAIL: " + "; ".join(fail) if fail else "candidate") + ("  [look: " + "; ".join(look) + "]" if look else ""))
    g = out[NAME]
    g.clearContours()
    for c in new.contours:
        g.appendContour(c)
    g.width = raw.width
    if a.install and not fail:
        R.install(font, NAME, new, a.date, a.review, rep)
        font[NAME].width = raw.width
        font[NAME].lib[R.KEY]["hook"] = True
        font.save()
    out.save(a.out, overwrite=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
