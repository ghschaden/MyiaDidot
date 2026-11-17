#!/usr/bin/env python3
"""Phase 6, step A: the Italic's r c balls, v w thin strokes, o O overshoots
brought to what the Regular has (docs/claude/italic.md, "The designer's
round", 2026-11-17).

    python scripts/italic_harmonise.py SRC.ufo OUT.ufo [GLYPH ...]            candidates
    python scripts/italic_harmonise.py SRC.ufo OUT.ufo [GLYPH ...] --install --date D --review DOC

Each change is a construction made of the glyph itself, then redrawn onto
clean nodes (redraw.py) and gated against the construction, into OUT.ufo;
with --install put into SRC.ufo marked drawn (redraw.install), lib
org.myiadidot.redrawn saying which change ("harmonise"). Run again on a
changed glyph, it changes it again: install once.

- ball (r c): the ball shrunk by BALL[name] about the top of its disc
  (where it hangs from its stroke), the neck blended back to the stroke
  over a disc of NECK radii; the disc found as italic_measures finds it.
  The advance loses what the glyph's right edge lost, so the white after
  the ball stays as it was.
- thin (v w): the rising thin strokes thinned by THIN[name] units across
  (derive.embolden with a weight per node: the nodes between THIN_BAND of
  the x-height, right of THIN_FROM of the ink's width, on a stroke under
  THIN_MAX thick, faded over THIN_FADE at the band's ends). y has no such
  stroke (its right stroke is its stem): not changed.
- overshoot (o O): the outline moved along the italic angle so that the
  round's overshoot above and below is the Regular's (OVERSHOOT, units);
  every point by its height, the far side fixed (o: its top, at the
  italic's one lowercase line, is no overshoot: italic.md, "Scale").

The numbers are calibrated so that italic_measures.py's relation lands
inside the three Didones' range with a margin (TARGETS, printed after
each run from OUT.ufo).
"""

import argparse
import copy
import math
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))

import bold_measures as bm  # noqa: E402
import derive  # noqa: E402
import italic_measures as im  # noqa: E402
import redraw as R  # noqa: E402

# the ball's scale; target relation (Italic over Regular, ball over stem)
BALL = {"r": 0.81, "c": 0.885}
NECK = 2.3  # the blend back to the stroke ends this many radii from the centre
# units across taken off the thin strokes
THIN = {"v": 10, "w": 10}
THIN_BAND = (0.10, 0.72)  # of the x-height
THIN_FADE = 0.08  # of the x-height, at both ends of the band
THIN_FROM = {"v": 0.40, "w": 0.22}  # of the ink's width (deslanted), from its left
THIN_MAX = 100  # units: a stroke thicker than this is a stem, left
# the Regular's overshoots, units (o below, O above and below)
OVERSHOOT = {"o": {"bottom": 16}, "O": {"top": 28, "bottom": 28}}
TARGETS = {"ball r / stem": (0.92, 1.10), "ball c / stem": (0.93, 0.96),
           "hairline v thin / stem": (0.92, 1.12),
           "overshoot o bottom % x-height": (0.0, 0.1), "overshoot O top % cap height": (-0.4, 0.0),
           "overshoot O bottom % cap height": (-0.2, 0.2)}
NAMES = ("r", "c", "v", "w", "o", "O")


def slant_of(font):
    return math.tan(math.radians(-(font.info.italicAngle or 0)))


def moved(glyph, fn):
    """a copy of glyph with every point (x, y) -> fn(x, y)"""
    new = copy.deepcopy(glyph)
    for c in new.contours:
        for p in c.points:
            p.x, p.y = fn(p.x, p.y)
    return new


def ball(font, glyph, src):
    """r's or c's ball shrunk about the top of its disc (font units)"""
    from italic_sheet import ball_disc

    ch = glyph.name
    x, y, r = ball_disc(src, ch)  # 1000-em, deslanted
    k, sl = 1 / src.scale, slant_of(font)
    cx, cy, rad = x * k, y * k, r * k
    ax, ay = cx, cy + rad  # the anchor: the disc's top, deslanted
    s = BALL[ch]

    def fn(px, py):
        dx = px - sl * py  # deslanted
        d = math.hypot(dx - cx, py - cy)
        t = 1.0 if d <= 1.05 * rad else 0.0 if d >= NECK * rad else 1 - (d - 1.05 * rad) / ((NECK - 1.05) * rad)
        w = t * t * (3 - 2 * t)  # smoothstep
        f = 1 + w * (s - 1)
        nx, ny = ax + f * (dx - ax), ay + f * (py - ay)
        return nx + sl * ny, ny

    return moved(glyph, fn)


def thin(font, glyph, src):
    """v's or w's rising thin strokes thinned by THIN units across"""
    ch = glyph.name
    xh, sl = font.info.xHeight, slant_of(font)
    lo, hi = THIN_BAND[0] * xh, THIN_BAND[1] * xh
    fade = THIN_FADE * xh
    xs = [p.x - sl * p.y for c in glyph.contours for p in c.points]
    x0, x1 = min(xs), max(xs)
    left = x0 + THIN_FROM[ch] * (x1 - x0)
    rec = RecordingPen()
    glyph.draw(rec)
    # the curves quartered first, so that the band moves where it is
    # measured and not only at the stroke's far nodes (make_italic.reweight's
    # fine); the redraw takes the nodes back out
    rec = halved(halved(rec))
    flat = ufoLib2.objects.Glyph()
    rec.replay(flat.getPen())
    segs = derive_segments(flat)

    def factor(x, y, inward):
        if not (lo <= y <= hi) or x - sl * y < left:
            return 0.0
        if across(segs, x, y, *inward) > THIN_MAX:
            return 0.0
        return min(1.0, (y - lo) / fade, (hi - y) / fade)

    out = derive.embolden(rec, -THIN[ch], 0, factor)
    new = copy.deepcopy(glyph)
    new.clearContours()
    out.draw(new.getPen())
    return new


def halved(rec):
    """rec with each curve split at its middle"""
    from fontTools.misc.bezierTools import splitCubicAtT

    out, cur = RecordingPen(), None
    for op, args in rec.value:
        if op == "curveTo":
            for seg in splitCubicAtT(cur, *args, 0.5):
                out.curveTo(*seg[1:])
        else:
            getattr(out, op)(*args)
        cur = args[-1] if args else cur
    return out


def derive_segments(glyph):
    """the outline as straight pieces, for measuring across"""
    from fontTools.pens.basePen import BasePen

    segs = []

    class Flat(BasePen):
        def _moveTo(self, p):
            self.start = self.cur = p

        def _lineTo(self, p):
            segs.append((self.cur, p))
            self.cur = p

        def _curveToOne(self, a, b, c):
            p0 = self.cur
            prev = p0
            for k in range(1, 13):
                t = k / 12
                q = tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * a[i] + 3 * (1 - t) * t * t * b[i]
                          + t ** 3 * c[i] for i in range(2))
                segs.append((prev, q))
                prev = q
            self.cur = c

        def _closePath(self):
            if self.cur != self.start:
                segs.append((self.cur, self.start))

    glyph.draw(Flat(None))
    return segs


def across(segs, px, py, ux, uy):
    """distance from (px, py) along (ux, uy) to the outline's other side"""
    best = math.inf
    for (ax, ay), (bx, by) in segs:
        dx, dy = bx - ax, by - ay
        den = dx * uy - dy * ux
        if abs(den) < 1e-9:
            continue
        wx, wy = ax - px, ay - py
        t = (dx * wy - dy * wx) / den
        s = (ux * wy - uy * wx) / den
        if t > 3 and 0 <= s <= 1:
            best = min(best, t)
    return best


def overshoot(font, glyph, src):
    """o's or O's overshoots set to the Regular's, the outline moved along
    the italic angle by height"""
    ch = glyph.name
    sl = slant_of(font)
    zone = font.info.capHeight if ch.isupper() else font.info.xHeight
    ys = [p.y for c in glyph.contours for p in c.points if p.type]
    top, bottom = max(ys), min(ys)
    want = OVERSHOOT[ch]
    new_top = zone + want["top"] if "top" in want else top
    new_bottom = -want["bottom"] if "bottom" in want else bottom
    k = (new_top - new_bottom) / (top - bottom)

    def fn(px, py):
        ny = new_bottom + (py - bottom) * k
        return px + sl * (ny - py), ny

    return moved(glyph, fn)


CHANGE = {"r": ball, "c": ball, "v": thin, "w": thin, "o": overshoot, "O": overshoot}


def measure(ufo):
    """italic_measures' values for the changed measures, Myia's relation"""
    reg = bm.Source(im.ROOT / "sources/MyiaDidot-Regular.ufo")
    it = bm.Source(ufo)
    r, i = im.measure(reg), im.measure(it)
    out = {}
    for name in TARGETS:
        if name in r and name in i:
            out[name] = i[name][0] - r[name][0] if name.startswith("overshoot") else i[name][0] / r[name][0]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--review")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review")
    names = a.glyphs or NAMES
    font = ufoLib2.Font.open(a.src)
    out = ufoLib2.Font.open(a.src)
    src = bm.Source(a.src)
    spec = R.spec_for(a.src, None)
    failed = 0
    for name in names:
        g = font[name]
        raw = CHANGE[name](font, g, src)
        new, rep = R.redraw(raw, R.TOL, spec.get(name))
        fail, look = R.gate(rep, None)
        xs_old = [p.x for c in g.contours for p in c.points if p.type]
        xs_new = [p.x for c in new.contours for p in c.points if p.type]
        width = g.width
        if CHANGE[name] is ball:
            width = g.width - round(max(xs_old) - max(xs_new))
        print(f"{name:<3}{CHANGE[name].__name__:<10}{rep['nodes_before']:>3} ->{rep['nodes_after']:>3} nodes  "
              f"{rep['dev']:.1f} from the construction  advance {g.width} -> {width}  "
              + ("FAIL: " + "; ".join(fail) if fail else "candidate")
              + ("  [look: " + "; ".join(look) + "]" if look else ""))
        failed += bool(fail)
        o = out[name]
        o.clearContours()
        for c in new.contours:
            o.appendContour(c)
        o.width = width
        if a.install and not fail:
            R.install(font, name, new, a.date, a.review, rep)
            font[name].width = width
            font[name].lib[R.KEY]["harmonise"] = CHANGE[name].__name__
    out.save(a.out, overwrite=True)
    for k, v in measure(a.out).items():
        lo, hi = TARGETS[k]
        print(f"  {k:<34}{v:+.3f}  the Didones {lo} to {hi}  " + ("inside" if lo <= v <= hi else "OUTSIDE"))
    if a.install:
        font.save()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
