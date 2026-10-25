"""Find outlines gone wrong: specks, pinholes, slivers, notches, steps.

    python scripts/glyph_lint.py UFO [GLYPH ...] [--kind KIND ...] [--fix]

Prints one line per finding: "glyph  kind  where  detail". What it looks for
(units are font units; the ink is the glyph decomposed, overlaps merged):

  speck    a separate piece of ink too small to be meant (a leftover of a cut)
  twist    an outline crossing itself in a loop of no area (harmless to see,
           but a fault in the outline: merging the overlaps leaves a crumb)
  pinhole  a counter too small to be meant (a slit left inside a join)
  sliver   a separate piece much thinner than any hairline
  notch    a narrow slit cut into the ink from outside, where two parts meet
           without blending (found by closing the ink: what a few units of
           growing and shrinking fill in, beyond what a sharp corner gives)
  step     a tiny jog in an outline: a very short segment between two corners
  ledge    a short straight segment between two corners that turn opposite
           ways: where a curl, bar or tail was joined on at another width
           or height than the stroke it joins (or a cusp emboldening made)

--fix cleans the specks, twists, pinholes, steps and ledges in place (the
outline merged as it renders, the crumbs dropped, each step or ledge shrunk
to a point, so the strokes on either side meet there) in
glyphs drawn as outlines; then make
normalize. Glyphs a script generates are better fixed there (make_italic.py
and derive.py clean what they make).

tests/test_glyph_lint.py holds each style to its list of known findings
(tests/data/glyph-lint.txt, glyph-lint-Italic.txt ...); the list only
shrinks.
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pathops
import ufoLib2
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from freetype.ft_errors import FT_Exception

sys.path.insert(0, str(Path(__file__).resolve().parent))

SPECK_AREA = 1500  # a dot of ~44 units across; the smallest real dots are far larger
SPECK_SIZE = 12  # or a piece nowhere this wide
PINHOLE_AREA = 300  # the smallest counter (e, a in small caps) is far larger
SLIVER_WIDTH = 10  # mean width of a piece (2 * area / perimeter); hairlines are 25+
SCALE = 0.5  # raster: pixels per unit
CLOSE = 3  # notch: closing radius, pixels (6 units)
NOTCH_PIXELS = 30  # notch: filled pixels in one place (120 square units)
STEP = 3  # step: a segment shorter than this between two corners
CORNER = 25  # step: degrees the outline turns at each end
LEDGE = 32  # ledge: a straight segment shorter than this ...
LEDGE_TURN = 40  # ... the outline turning this much at each end, opposite ways
# ledges meant: bars ending in a stub just past the stroke they cross (ɉ ₲),
# and the roman ℵ's drawn serif/diagonal joins (draft_letterlike.alef).
LEDGE_KEEP = {"uni0249", "uni0249.sc", "uni20B2", "uni2135"}

TWIST_AREA = 2  # a piece this small is a self-crossing of the outline, not ink
KINDS = ("speck", "twist", "pinhole", "sliver", "notch", "step", "ledge")


def ink(font, glyph):
    """The glyph's ink as one pathops Path, overlaps merged."""
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    path = pathops.Path()
    rec.replay(path.getPen())
    return pathops.simplify(path, clockwise=False)


def contour_stats(contour):
    """(signed area, perimeter, bounds) of a pathops contour."""
    area = AreaPen()
    contour.draw(area)
    per = PerimeterPen()
    contour.draw(per)
    return area.value, per.value, contour.bounds


def vector_findings(path):
    out = []
    stats = [contour_stats(c) for c in path.contours]
    if not stats:
        return out
    # outer contours wind like the largest one, counters the other way
    sign = math.copysign(1, max((s[0] for s in stats), key=abs))
    for area, per, (x0, y0, x1, y1) in stats:
        where = f"{round((x0 + x1) / 2)},{round((y0 + y1) / 2)}"
        a = abs(area)
        if area * sign > 0:
            if a < TWIST_AREA:
                out.append(("twist", where, f"area {a:.1f}"))
            elif a < SPECK_AREA or min(x1 - x0, y1 - y0) < SPECK_SIZE:
                out.append(("speck", where, f"area {round(a)}"))
            elif per and 2 * a / per < SLIVER_WIDTH:
                out.append(("sliver", where, f"mean width {2 * a / per:.1f}"))
        elif a < TWIST_AREA:
            out.append(("twist", where, f"area {a:.1f}"))
        elif a < PINHOLE_AREA:
            out.append(("pinhole", where, f"area {round(a)}"))
    return out


def clean(path, ledges=True):
    """path merged (an outline crossing itself resolved as it renders), with
    its specks, twists and pinholes dropped and its steps (and ledges) taken
    out. Give it the outline as drawn: a crumb pinched off at a point comes
    apart in the first merge only."""
    path = pathops.simplify(path, clockwise=False)
    stats = [(c, contour_stats(c)) for c in path.contours]
    if not stats:
        return path
    sign = math.copysign(1, max((s[0] for _, s in stats), key=abs))
    out = pathops.Path()
    pen = out.getPen()
    for c, (area, _, (x0, y0, x1, y1)) in stats:
        a = abs(area)
        if area * sign > 0 and (a < SPECK_AREA or min(x1 - x0, y1 - y0) < SPECK_SIZE):
            continue
        if area * sign < 0 and a < PINHOLE_AREA:
            continue
        c.draw(pen)
    return unstep(out, ledges)


class _Corners(BasePen):
    """Segments of an outline as (start, end, direction in, direction out)."""

    def __init__(self):
        super().__init__(None)
        self.contours, self.segs, self.start, self.cur = [], [], None, None

    def _moveTo(self, pt):
        self.start = self.cur = pt
        self.segs = []

    def _add(self, pts):
        self.segs.append((self.cur, pts[-1], pts[0], pts[-2] if len(pts) > 1 else self.cur))
        self.cur = pts[-1]

    def _lineTo(self, pt):
        self._add([pt])

    def _curveToOne(self, p1, p2, p3):
        self._add([p1, p2, p3])

    def _qCurveToOne(self, p1, p2):
        self._add([p1, p2])

    def _closePath(self):
        if self.cur != self.start:
            self._add([self.start])
        self.contours.append(self.segs)

    _endPath = _closePath


def _angle(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _turn(d0, d1):
    t = abs(math.degrees(d1 - d0)) % 360
    return min(t, 360 - t)


def _curved(seg):
    """A _Corners segment that is a curve (a line's handles are its ends)."""
    p0, p1, c_in, c_out = seg
    return (c_in, c_out) != (p1, p0)


def step_findings(path, crumbs=False):
    """Very short segments with a corner at both ends; with crumbs, also
    curves as short with a corner at one end only, beside a curve (unstep
    folds them in: what cleaning takes, not what lint reports)."""
    pen = _Corners()
    path.draw(pen)
    out = []
    for segs in pen.contours:
        n = len(segs)
        if n < 3:
            continue
        for i, (p0, p1, c_in, c_out) in enumerate(segs):
            if math.dist(p0, p1) >= STEP or p0 == p1:
                continue
            prev, nxt = segs[i - 1], segs[(i + 1) % n]
            here_in = _angle(p0, c_in if c_in != p0 else p1)
            here_out = _angle(c_out if c_out != p1 else p0, p1)
            # from the nearest distinct points, as unstep (a handle may sit
            # on its node: then the other handle gives the direction)
            before = _angle(next(q for q in (prev[3], prev[2], prev[0]) if q != prev[1]), prev[1])
            after = _angle(nxt[0], next(q for q in (nxt[2], nxt[3], nxt[1]) if q != nxt[0]))
            corner0, corner1 = _turn(before, here_in) > CORNER, _turn(here_out, after) > CORNER
            keep = nxt if corner0 else prev
            crumb = crumbs and corner0 != corner1 and _curved(segs[i]) and _curved(keep)
            if (corner0 and corner1) or crumb:
                out.append(("step", f"{round(p0[0])},{round(p0[1])}", f"{math.dist(p0, p1):.1f} units"))
    return out


def _signed(d0, d1):
    return math.degrees((d1 - d0 + math.pi) % (2 * math.pi) - math.pi)


def _is_ledge(before, d, after, length, straight):
    if not (straight and STEP <= length < LEDGE):
        return False
    t0, t1 = _signed(before, d), _signed(d, after)
    return abs(t0) > LEDGE_TURN and abs(t1) > LEDGE_TURN and t0 * t1 < 0


def ledge_findings(path):
    """Short straight segments between corners turning opposite ways."""
    pen = _Corners()
    path.draw(pen)
    out = []
    for segs in pen.contours:
        n = len(segs)
        if n < 3:
            continue
        for i, (p0, p1, c_in, _c_out) in enumerate(segs):
            if p0 == p1:
                continue
            prev, nxt = segs[i - 1], segs[(i + 1) % n]
            before = _angle(prev[3] if prev[3] != prev[1] else prev[0], prev[1])
            after = _angle(nxt[0], nxt[2] if nxt[2] != nxt[0] else nxt[1])
            if _is_ledge(before, _angle(p0, p1), after, math.dist(p0, p1), c_in == p1):
                out.append(("ledge", f"{round(p0[0])},{round(p0[1])}", f"{math.dist(p0, p1):.0f} units"))
    return out


def unstep(path, ledges=False):
    """path with its steps taken out: each very short segment between two
    corners shrunk to a point (at its middle, on whole units), so the
    strokes on either side meet there, and each as short with a corner at
    one end only (a crumb of a curve) folded into the curve beside it; with
    ledges, the ledges too."""
    rec = RecordingPen()
    path.draw(rec)
    contours, cur = [], None
    for op, pts in rec.value:
        if op == "moveTo":
            cur = [pts[0], []]
            contours.append(cur)
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            cur[1].append([op, list(pts)])
    out = pathops.Path()
    pen = out.getPen()
    for start, segs in contours:
        if segs and segs[-1][1][-1] != start:
            segs.append(["lineTo", [start]])
        while True:
            ends = [s[1][-1] for s in segs]
            n = len(segs)
            if n < 3:
                break
            for i in range(n):
                p0, p1 = ends[i - 1], ends[i]
                if p0 == p1 or math.dist(p0, p1) >= (LEDGE if ledges else STEP):
                    continue
                prev, here, nxt = segs[i - 1], segs[i], segs[(i + 1) % n]
                # directions from the nearest distinct points (a control
                # point may sit on its node)
                c_in = next((q for q in here[1] if q != p0), p1)
                c_out = next((q for q in [*reversed(here[1][:-1]), p0] if q != p1), p0)
                b = next((q for q in [*reversed(prev[1][:-1]), ends[i - 2]] if q != p0), ends[i - 2])
                a = next((q for q in nxt[1] if q != p1), nxt[1][-1])
                before, after = _angle(b, p0), _angle(p1, a)
                if math.dist(p0, p1) >= STEP:
                    hit = _is_ledge(before, _angle(p0, p1), after, math.dist(p0, p1), here[0] == "lineTo")
                else:
                    corner0 = _turn(before, _angle(p0, c_in)) > CORNER
                    corner1 = _turn(_angle(c_out, p1), after) > CORNER
                    hit = corner0 and corner1
                    # a crumb: a curve's last units split off at an extreme
                    # beside a corner (pathops splits curves there), turning
                    # the corner sharper (emboldened, it grew a spur: the
                    # Bold Italic ₲'s beak); folded into the curve it ends
                    keep = nxt if corner0 else prev
                    if corner0 != corner1 and here[0] == keep[0] == "curveTo":
                        d = (p1[0] - p0[0], p1[1] - p0[1]) if corner1 else (p0[0] - p1[0], p0[1] - p1[1])
                        if corner1:
                            prev[1][-2] = (prev[1][-2][0] + d[0], prev[1][-2][1] + d[1])
                            prev[1][-1] = p1
                        else:
                            nxt[1][0] = (nxt[1][0][0] + d[0], nxt[1][0][1] + d[1])
                        del segs[i]
                        break
                if hit:
                    m = (round((p0[0] + p1[0]) / 2), round((p0[1] + p1[1]) / 2))
                    prev[1][-1] = m
                    if nxt[1] and len(nxt[1]) > 1 and nxt[1][0] == p1:
                        nxt[1][0] = m
                    del segs[i]
                    break
            else:
                break
        ends = [s[1][-1] for s in segs]
        pen.moveTo(ends[-1])
        for op, pts in segs:
            getattr(pen, op)(*pts)
        pen.closePath()
    return out


def _grow(mask, r):
    """Binary dilation by a disc of radius r pixels."""
    out = mask.copy()
    h, w = mask.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r or (dx == 0 and dy == 0):
                continue
            src = mask[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
            out[max(0, dy):h - max(0, -dy), max(0, dx):w - max(0, -dx)] |= src
    return out


def _components(mask):
    """Connected regions of a boolean array: lists of (y, x)."""
    seen = np.zeros_like(mask)
    regions = []
    for y, x in zip(*np.nonzero(mask), strict=True):
        if seen[y, x]:
            continue
        stack, region = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            region.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        regions.append(region)
    return regions


def notch_findings(font, glyph, bounds):
    """What closing the ink fills in, beyond what corners give."""
    x0, y0, x1, y1 = bounds
    if x1 <= x0 or y1 <= y0:
        return []
    # the pixel grid on whole pixels of the glyph's own coordinates, so a
    # composite measures its base as the base does (a mark below would move it)
    x0, y0 = math.floor(x0 * SCALE) / SCALE, math.floor(y0 * SCALE) / SCALE
    pad = CLOSE + 2
    w = int((x1 - x0) * SCALE) + 2 * pad
    h = int((y1 - y0) * SCALE) + 2 * pad
    # the glyph as drawn (the rasteriser fills overlaps); pathops' merged
    # outline can overflow FreeType
    pen = FreeTypePen(None)
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    rec.replay(pen)
    # a crotch fills a few pixels more or less with where the grid falls on
    # it, and a slit can split in two at one phase: the lower median of four
    # half-pixel phases
    results = []
    for phase in ((0, 0), (0.5, 0), (0, 0.5), (0.5, 0.5)):
        tx, ty = pad - x0 * SCALE + phase[0], pad - y0 * SCALE + phase[1]
        found = _notches(pen, w, h, tx, ty)
        if found is not None:
            results.append(found)
    if not results:
        return [("notch", "-", "not rasterised")]
    results.sort(key=lambda found: (max((size for _, size in found), default=0), len(found)))
    return [("notch", at, f"{size} px") for at, size in results[(len(results) - 1) // 2]]


def _notches(pen, w, h, tx, ty):
    """(centre, pixels) of each notch in the glyph rasterised at this offset; None if it cannot be."""
    # FreeType's rasteriser overflows on some exact positions and scales (the sloped +)
    for nudge, k in ((0, 1), (0.13, 1), (0.29, 1), (0, 0.9), (0.2, 0.9), (0, 0.8), (0.3, 0.7)):
        try:
            raster = pen.array(width=w, height=h,
                               transform=(SCALE * k, 0, 0, SCALE * k, tx + nudge, ty + nudge), contain=False)
            break
        except FT_Exception:
            continue
    else:
        return None
    mask = raster > 0.5
    closed = ~_grow(~_grow(mask, CLOSE), CLOSE)
    filled = closed & ~mask
    if not filled.any():
        return []
    # a corner fills a little wedge at its tip; a notch fills a region that
    # stays after shrinking the fill by one more pixel
    core = filled & ~_grow(~filled, 1)
    out = []
    for region in _components(core):
        if len(region) < NOTCH_PIXELS:
            continue
        ys, xs = zip(*region, strict=True)
        # array rows run top down
        cx = (sum(xs) / len(xs) - tx) / SCALE
        cy = ((h - sum(ys) / len(ys)) - ty) / SCALE
        out.append((f"{round(cx)},{round(cy)}", len(region)))
    return out


def lint_glyph(font, glyph, kinds=KINDS):
    path = ink(font, glyph)
    if not path.contours:
        return []
    out = []
    if {"speck", "twist", "pinhole", "sliver"} & set(kinds):
        out += [f for f in vector_findings(path) if f[0] in kinds]
    if "step" in kinds:
        out += step_findings(path)
    if "ledge" in kinds:
        out += ledge_findings(path)
    if "notch" in kinds:
        out += notch_findings(font, glyph, path.bounds)
    return out


def lint(font, names=None, kinds=KINDS):
    """{glyph name: [(kind, where, detail), ...]} for the glyphs with findings."""
    found = {}
    for name in names or sorted(font.keys()):
        f = lint_glyph(font, font[name], kinds)
        if f:
            found[name] = f
    return found


FIXED = ("speck", "twist", "pinhole", "step", "ledge")


def fix(font, names=None):
    """Clean the specks, twists, pinholes, steps and ledges of the outline
    glyphs (not the ledges of LEDGE_KEEP); the names of the glyphs changed."""
    import copy

    from derive import draw_path

    changed = []
    for name in names or sorted(font.keys()):
        g = font[name]
        for _ in range(3):  # again if rounding to whole units crossed the outline anew
            if not g.contours or g.components:
                break
            path = ink(font, g)
            found = vector_findings(path) + step_findings(path, crumbs=True)
            if name not in LEDGE_KEEP:
                found += ledge_findings(path)
            if not any(k in FIXED for k, *_ in found):
                break
            before = copy.deepcopy(g)
            g.clearContours()
            # the outline as drawn: merged once, a pinched-off crumb comes
            # apart (merged again, it would rejoin)
            raw = pathops.Path()
            rec = DecomposingRecordingPen(font)
            before.draw(rec)
            rec.replay(raw.getPen())
            draw_path(font, before, g, raw)
            if name not in changed:
                changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--kind", action="append", choices=KINDS, help="only these kinds (repeatable)")
    ap.add_argument("--fix", action="store_true", help="clean specks, twists, pinholes, steps and ledges in place")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    if args.fix:
        changed = fix(font, args.glyphs or None)
        font.save()
        print(f"{Path(args.ufo).name}: cleaned {len(changed)} glyphs: {' '.join(changed)}", file=sys.stderr)
    found = lint(font, args.glyphs or None, tuple(args.kind or KINDS))
    for name, items in found.items():
        for kind, where, detail in items:
            print(f"{name:20} {kind:8} {where:>12}  {detail}")
    counts = {}
    for items in found.values():
        for kind, *_ in items:
            counts[kind] = counts.get(kind, 0) + 1
    print(f"{Path(args.ufo).name}: {sum(counts.values())} findings in {len(found)} glyphs "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), file=sys.stderr)


if __name__ == "__main__":
    main()
