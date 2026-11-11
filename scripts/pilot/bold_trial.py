#!/usr/bin/env python3
"""F4's trial (docs/claude/bold.md): the upright Bold made into build/ with
another widening (B2: KX) and with the gaps between facing serifs keeping
their share of the counter (B1), make_bold itself and sources/ untouched.

    .venv/bin/python -I scripts/pilot/bold_trial.py OUT.ufo [--kx 1.0] [--gaps]

OUT.ufo starts as a copy of sources/MyiaDidot-Bold.ufo (for the glyphs kept
as drawn) and is then written by make_bold.main() from the Regular. --gaps
replaces make_bold.part_serifs for the run by gap_serifs below: where two
serif tips face each other (part_serifs' own pairs), the Bold's gap is to be
at least GAP_SHARE of the share the source's gap has of the white between
the strokes, measured GAP_AT units from the serifs' edge into the letter;
both tips are shortened in the source in steps, as part_serifs does, until
it is. Parting what would merge (part_serifs' present work) runs first.
Printed: the glyphs whose serifs were shortened, with gap before and after.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import make_bold as mb  # noqa: E402
import pathops  # noqa: E402
import ufoLib2  # noqa: E402
from fontTools.pens.recordingPen import RecordingPen  # noqa: E402

GAP_SHARE = 0.9  # of the source's gap over white: the references keep 0.89 to 0.91 (n m h)
GAP_AT = 221  # units into the letter from the serifs' edge: a quarter of the x-height
GAP_MIN_WHITE = 120  # a white narrower than this between the strokes is no counter
REACH = 900
LOG = []


def to_path(glyph):
    p = pathops.Path()
    for c in glyph.contours:
        c.draw(p.getPen())
    return pathops.simplify(p)


def white(path, x, y):
    """The white run through (x, y) across: its width, 0 where there is ink
    or no ink on one of the sides."""
    strip = pathops.Path()
    pen = strip.getPen()
    pen.moveTo((x - REACH, y - 1))
    pen.lineTo((x + REACH, y - 1))
    pen.lineTo((x + REACH, y + 1))
    pen.lineTo((x - REACH, y + 1))
    pen.closePath()
    cut = pathops.op(path, strip, pathops.PathOp.INTERSECTION)
    left, right = None, None
    for c in cut.contours:
        x0, _, x1, _ = c.bounds
        if x0 <= x <= x1:
            return 0
        if x1 < x and (left is None or x1 > left):
            left = x1
        if x0 > x and (right is None or x0 < right):
            right = x0
    return right - left if left is not None and right is not None else 0


def facing_tips(src):
    """part_serifs' pairs: [(tips a, tips b, mid x, gap, y of the edge, shortest edge)]"""
    edges = []
    for ci, c in enumerate(src.contours):
        pts = c.points
        n = len(pts)
        for i in range(n):
            p0, p1 = pts[i], pts[(i + 1) % n]
            if p0.type and p1.type == "line" and p0.y == p1.y and abs(p1.x - p0.x) >= 30:
                edges.append((ci, i, (i + 1) % n, p0.y, min(p0.x, p1.x), max(p0.x, p1.x)))
    pairs = []
    for a in edges:
        for b in edges:
            if a[3] != b[3] or not 0 < b[4] - a[5] < mb.PART_GAP:
                continue
            pa, pb = src.contours[a[0]].points, src.contours[b[0]].points
            ia = a[1] if pa[a[1]].x == a[5] else a[2]
            ib = b[1] if pb[b[1]].x == b[4] else b[2]
            tips = []
            for ci, i, step, pts in ((a[0], ia, 1 if ia == a[2] else -1, pa), (b[0], ib, 1 if ib == b[2] else -1, pb)):
                j = (i + step) % len(pts)
                q = pts[j]
                tips.append([(ci, i), (ci, j)] if q.type == "line" and 10 <= abs(q.y - pts[i].y) <= 150 else [(ci, i)])
            pairs.append((tips[0], tips[1], (a[5] + b[4]) / 2, b[4] - a[5], a[3],
                          min(a[5] - a[4], b[5] - b[4])))
    return pairs


def gap_serifs(wide, bold, make, original=mb.part_serifs):
    bold, n = original(wide, bold, make)
    src = ufoLib2.objects.Glyph()
    wide.replay(src.getPen())
    sp, bp = to_path(src), to_path(bold)
    todo = []
    for ta, tb, mid, gap, y, shortest in facing_tips(src):
        for side in (1, -1):  # the letter's inside is above the edge (feet) or below it (tops)
            w_src, w_bold = white(sp, mid, y + side * GAP_AT), white(bp, mid, y + side * GAP_AT)
            g_bold = white(bp, mid, y + side * 6)
            if w_src >= max(GAP_MIN_WHITE, gap) and w_bold >= GAP_MIN_WHITE and g_bold:
                want = GAP_SHARE * gap / w_src * w_bold
                if g_bold < want - 2:
                    todo.append((ta, tb, mid, y + side * 6, y + side * GAP_AT, gap / w_src, g_bold, shortest))
                break
    if not todo:
        return bold, n
    best = None
    for s in range(4, int(min(t[7] for t in todo)) - 20, 4):
        moved = ufoLib2.objects.Glyph()
        wide.replay(moved.getPen())
        for ta, tb, *_ in todo:
            for tips, dx in ((ta, -s), (tb, s)):
                for ci, i in tips:
                    pts = moved.contours[ci].points
                    near = {i} | {(i + st) % len(pts) for st in (-1, 1) if pts[(i + st) % len(pts)].type is None}
                    for j in near:
                        pts[j].x += dx
        rec = RecordingPen()
        moved.draw(rec)
        out = make(rec)
        op = to_path(out)
        got = [(white(op, mid, yg), share * GAP_SHARE * white(op, mid, yw)) for _, _, mid, yg, yw, share, _, _ in todo]
        if all(g >= want - 2 for g, want in got):
            best = (out, s, got)
            break
    if best is None:  # not reached within the serifs' length: left as it is
        return bold, n
    out, s, got = best
    LOG.append((s, [round(t[6]) for t in todo], [round(g) for g, _ in got], [round(w) for _, w in got]))
    return out, n + len(todo)


BALL_OF_STEM = 1.04  # B4: r's ball over the stem, the references' lowest share
ROUNDS = ("O", "C", "G", "Q")


def tolerant_finish(font):
    """finalization.finish_glyphs for another KX: the passes that mend a glyph
    at fixed coordinates refuse the changed outline (k.sc, numero); the
    trial skips them and says so."""
    from importlib import import_module

    import finalization
    for stage in finalization.PASSES:
        if font.info.styleName in stage.styles:
            try:
                getattr(import_module(stage.module), stage.entry)(font)
            except ValueError as e:
                print(f"trial: pass {stage.module}.{stage.entry} skipped ({e})")


def grow_ball(font):
    """B4: r's ball (the terminal's nodes, the top's on-curve to the neck's
    inner one) scaled from the neck's inner edge and the top until its
    diameter is BALL_OF_STEM of n's stem; the advance follows the ink."""
    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import bold_measures as bm
    src = bm.Source(font.path)
    k = BALL_OF_STEM * bm.measure(src, "n")["stem"] / bm.measure(src, "r")["ball"]
    g = font["r"]
    pts = max(g.contours, key=len).points
    if len(pts) != 39:
        sys.exit("r's outline is not the one the trial knows")
    x0, y0 = pts[20].x, pts[11].y
    right = max(p.x for p in pts)
    for p in pts[11:21]:
        p.x, p.y = round(x0 + (p.x - x0) * k), round(y0 + (p.y - y0) * k)
    g.width += max(p.x for p in pts) - right
    print(f"r's ball times {k:.3f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("--kx", type=float, default=mb.KX)
    ap.add_argument("--gaps", action="store_true")
    ap.add_argument("--base", help="an earlier trial's UFO to start from instead of running make_bold")
    ap.add_argument("--ball", action="store_true", help="B4: r's ball at the stem's weight")
    ap.add_argument("--rounds", help="B3: O C G Q taken from this trial UFO (made with a KX "
                    "that keeps the Regular's advance, about 0.943)")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if ROOT / "sources" in out.parents:
        sys.exit("a trial is not written into sources/")
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(args.base or ROOT / "sources" / "MyiaDidot-Bold.ufo", out)
    if not args.base:
        if args.kx != mb.KX:
            import finalization
            finalization.finish_glyphs = tolerant_finish
        mb.KX = args.kx
        if args.gaps:
            mb.part_serifs = gap_serifs
        sys.argv = ["make_bold.py", str(ROOT / "sources" / "MyiaDidot-Regular.ufo"), str(out)]
        mb.main()
        for s, before, after, want in LOG:
            print(f"gaps: serifs -{s}: {before} > {after} (wanted {want})")
        print(f"{out}: KX {args.kx}, gaps {'kept' if args.gaps else 'as today'}, {len(LOG)} glyphs' serifs shortened")
    if args.ball or args.rounds:
        font = ufoLib2.Font.open(out)
        if args.rounds:
            other = ufoLib2.Font.open(args.rounds)
            for name in ROUNDS:
                font[name].clearContours()
                other[name].draw(font[name].getPen())
                font[name].width = other[name].width
        if args.ball:
            grow_ball(font)
        font.save()


if __name__ == "__main__":
    main()
