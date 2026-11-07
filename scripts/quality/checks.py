"""Quality checks on a UFO, fast enough for the test suite.

    python scripts/quality/checks.py UFO [--kind KIND ...]

Each finding is (glyph, kind, where, detail). The kinds (criteria 7-11, 14,
17, 18 of build/proofs/quality-evaluation.md):

  smooth   a node marked smooth whose tangent breaks by more than 2 degrees
           (both handles at least 10 units long: a shorter one has no angle
           worth the name once rounded)
  kink     a corner not marked smooth that turns only 1-8 degrees, between
           segments at least 20 units long: meant smooth, drawn broken
  extreme  a curve bulging more than 5 units past its end points without a
           point at the extreme
  step     a short straight edge (STEP_LEN units at most) jogging aside
           between two edges that run on in the same direction (within
           STEP_SAME degrees), turning at least STEP_JOG from both: a piece
           set beside its stroke (a tail narrower than its stem, a hook's
           end cut standing out of the letter)
  wobble   (the Bold, the Bold Italic) a curve bending back the other way
           for a short stretch (WOBBLE_TURN degrees or more, at most
           WOBBLE_LEN units, between bends the first way) more often than
           in the glyph it is generated from (the Regular's, the Italic's):
           a bulge and shoulder the emboldening put in (ψ's terminal, г's
           inner curves, o's inner side)
  grid     a point, anchor or component offset off whole units
  zone     a letter's flat top or bottom near an alignment zone (baseline,
           x-height, small-cap and cap height, ascender, descender) but
           neither on it (2 units) nor at the font's overshoot (6)
  weight   a straight stem more than 12 % off its case's (n, H, h.sc)
  slant    (italics) a glyph's straight stems leaning more than 2 degrees
           off the italic angle
  accent   a mark above or below a letter more than 25 units further or
           nearer than that mark's usual gap on its kind of letter, counted
           from the flat zone a round edge overshoots (marks beside a
           capital or inside a descender are left out)
  width    (the Bold) an advance off the Bold's usual ratio to the Regular's
           by more than 10 %
  base, stem, advance, style
           a derived letter against the letter its recipe makes it from
           (derive.py): too little of the base kept, its stem heavier or
           lighter, its advance off, an italic one made from the roman
           (scripts/quality/derived.py)
  stroke   a letter's or figure's main stroke more than 10 % heavier or
           lighter than its kind's (n/o, H/O, h.sc/o.sc): darker or
           lighter than the text around it (scripts/quality/strokes.py;
           --sheet draws them for review)

tests/test_quality.py holds each style to its list of known findings
(tests/data/quality.txt, quality-Italic.txt ...); the list only shrinks.
After an intended change: scripts/update_test_data.py --quality.
"""

import collections
import math
import statistics
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from case_reference import reference_top

KINDS = ("smooth", "kink", "extreme", "step", "wobble", "grid", "zone", "weight", "slant", "accent", "width",
         "base", "stem", "advance", "style", "stroke")
DERIVED = ("base", "stem", "advance", "style")


def _angle(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _turn(d0, d1):
    return abs(math.degrees((d1 - d0 + math.pi) % (2 * math.pi) - math.pi))


def _bez(p, t):
    u = 1 - t
    return tuple(u ** 3 * p[0][q] + 3 * u * u * t * p[1][q] + 3 * u * t * t * p[2][q] + t ** 3 * p[3][q] for q in (0, 1))


STEP_LEN, STEP_SAME, STEP_JOG = 70, 35, 40  # units; degrees (step)


def construction(glyph):
    """smooth, kink, extreme, step, grid findings of one glyph's contours."""
    out = []
    for c in glyph.contours:
        P = list(c.points)
        n = len(P)
        if n < 3:
            continue
        for i, p in enumerate(P):
            if p.type is None:
                continue
            prev, nxt = P[i - 1], P[(i + 1) % n]
            a, h, b = (prev.x, prev.y), (p.x, p.y), (nxt.x, nxt.y)
            la, lb = math.dist(a, h), math.dist(h, b)
            if not la or not lb:
                continue
            t = _turn(_angle(a, h), _angle(h, b))
            if p.smooth and t > 2 and la >= 10 and lb >= 10 and (prev.type is None or nxt.type is None):
                out.append(("smooth", f"{round(p.x)},{round(p.y)}", f"{t:.1f} degrees"))
            if not p.smooth and 1 < t < 8 and la >= 20 and lb >= 20:
                out.append(("kink", f"{round(p.x)},{round(p.y)}", f"{t:.1f} degrees"))
            # a step: the line from p to nxt, between the edge into p and
            # the one out of nxt (each toward its nearest point)
            after = P[(i + 2) % n]
            if nxt.type == "line" and 0 < lb <= STEP_LEN and (after.x, after.y) != b:
                d_in, d_step, d_out = _angle(a, h), _angle(h, b), _angle(b, (after.x, after.y))
                if (_turn(d_in, d_out) <= STEP_SAME and _turn(d_in, d_step) >= STEP_JOG
                        and _turn(d_step, d_out) >= STEP_JOG):
                    out.append(("step", f"{round(p.x)},{round(p.y)}", f"{lb:.0f} units aside"))
        # curves: their extremes
        ons = [k for k, p in enumerate(P) if p.type]
        for k, i in enumerate(ons):
            j = ons[(k + 1) % len(ons)]
            offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
            if len(offs) != 2:
                continue
            pts = [(P[x].x, P[x].y) for x in (i, offs[0], offs[1], j)]
            samples = [_bez(pts, s / 20) for s in range(21)]
            for q in (0, 1):
                lo, hi = min(s[q] for s in samples), max(s[q] for s in samples)
                e0, e1 = sorted((pts[0][q], pts[3][q]))
                over = max(e0 - lo, hi - e1)
                if over > 5:
                    out.append(("extreme", f"{round(pts[0][0])},{round(pts[0][1])}", f"{over:.0f} units past"))
                    break
    grid = [p for c in glyph.contours for p in c.points if p.x != round(p.x) or p.y != round(p.y)]
    grid += [a for a in glyph.anchors if a.x != round(a.x) or a.y != round(a.y)]
    grid += [c for c in glyph.components if any(v != round(v) for v in c.transformation[4:])]
    if grid:
        out.append(("grid", "", f"{len(grid)} off whole units"))
    return out


class Shapes:
    """Merged, deslanted outlines of a font's glyphs, measured on demand."""

    def __init__(self, font):
        self.font = font
        self.slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
        self._p, self._u = {}, {}

    def path(self, name, deslant=False):
        key = (name, deslant)
        if key not in self._p:
            p = pathops.Path()
            r = DecomposingRecordingPen(self.font)
            self.font[name].draw(r)
            t = (1, 0, -self.slant if deslant else 0, 1, 0, 0)
            r.replay(TransformPen(p.getPen(), t))
            self._p[key] = pathops.simplify(p)
        return self._p[key]

    def bounds(self, name):
        b = self.path(name).bounds
        return None if b == (0, 0, 0, 0) else b

    def runs(self, name, y, deslant=True):
        r = pathops.Path()
        pen = r.getPen()
        pen.moveTo((-9000, y - 0.5))
        pen.lineTo((9000, y - 0.5))
        pen.lineTo((9000, y + 0.5))
        pen.lineTo((-9000, y + 0.5))
        pen.closePath()
        q = pathops.op(self.path(name, deslant), r, pathops.PathOp.INTERSECTION)
        return sorted((c.bounds[0], c.bounds[2]) for c in q.contours)


def _cmap(font):
    return {u: g.name for g in font for u in g.unicodes}


def _letter(font, g):
    u = g.unicodes[0] if g.unicodes else None
    if g.name.endswith(".sc"):
        return "sc"
    if u is None:
        return None
    cat = unicodedata.category(chr(u))
    return {"Ll": "lc", "Lu": "uc", "Lt": "uc"}.get(cat)


def zones(font, shapes):
    """zone findings: flat edges near a zone but neither on it nor at the
    overshoot."""
    cm = _cmap(font)

    def edge(ch, i):
        name = cm.get(ord(ch)) if len(ch) == 1 else ch
        b = shapes.bounds(name) if name in font else None
        return b[i] if b else None

    flat_over = {
        "lc": [(edge("x", 1), edge("o", 1)), (edge("x", 3), edge("o", 3)), (edge("l", 3), None), (edge("p", 1), None)],
        "uc": [(edge("H", 1), edge("O", 1)), (edge("H", 3), edge("O", 3))],
        "sc": [(edge("h.sc", 1), edge("o.sc", 1)), (edge("h.sc", 3), edge("o.sc", 3))],
    }
    # the overshoot of the zones without a round letter of their own: o's
    over = abs(edge("o", 1) or 0)
    out = []
    for g in font:
        kind = _letter(font, g)
        if kind not in flat_over:
            continue
        # outlines and aliases only: an accented letter's top is its accent's
        if not g.contours and len(g.components) != 1:
            continue
        b = shapes.bounds(g.name)
        if not b:
            continue
        for y, which in ((b[1], "bottom"), (b[3], "top")):
            levels = flat_over[kind]
            if kind == "sc" and which == "top":
                inherited_top = reference_top(font, g)
                if inherited_top is not None:
                    levels = [(f, inherited_top) if f == font.lib.get("org.myiadidot.smallcapHeight", 1040)
                              else (f, o) for f, o in levels]
            near = [(abs(y - f), f, o) for f, o in levels if f is not None]
            d, f, o = min(near)
            if d > 30:
                continue
            on = d <= 2 or (o is not None and abs(y - o) <= 6) or (o is None and abs(d - over) <= 6)
            if not on:
                out.append((g.name, "zone", which, f"{round(y - f):+} from {round(f)}"))
    return out


# letters whose first stem is a thick straight one (not M N: their uprights are thin)
STEM_LETTERS = {"lc": ("n", "bdhiklmnpqru"), "uc": ("H", "BDEFHIKLPRT"), "sc": ("h.sc", "")}


def weights(font, shapes):
    """weight findings: straight stems off their case's."""
    cm = _cmap(font)
    xh = shapes.bounds(cm[ord("x")])[3]
    cap = shapes.bounds(cm[ord("H")])[3]
    out = []
    for case, (ref, chars) in STEM_LETTERS.items():
        names = [cm[ord(c)] for c in chars if ord(c) in cm]
        if case == "sc":
            names = [n + ".sc" for n in ("b", "d", "h", "i", "k", "l", "p", "r", "u") if n + ".sc" in font]
        refname = cm.get(ord(ref)) if len(ref) == 1 else ref
        if refname not in font:
            continue
        h = {"lc": xh * 0.5, "uc": cap * 0.4, "sc": 1040 * 0.4}[case]
        rr = shapes.runs(refname, h)
        if not rr:
            continue
        stem = rr[0][1] - rr[0][0]
        for name in names:
            rn = shapes.runs(name, h)
            if not rn:
                continue
            w = rn[0][1] - rn[0][0]
            if abs(w / stem - 1) > 0.12:
                out.append((name, "weight", f"at {round(h)}", f"stem {round(w)} against {round(stem)}"))
    return out


def slant(font):
    """slant findings (an italic): straight stems leaning off the angle."""
    target = -(font.info.italicAngle or 0)
    if not target:
        return []
    out = []
    for g in font:
        if not g.contours or _letter(font, g) is None and not (g.unicodes and chr(g.unicodes[0]).isdigit()):
            continue
        angs = []
        for c in g.contours:
            P = list(c.points)
            for i, p in enumerate(P):
                q = P[(i + 1) % len(P)]
                if p.type is None or q.type != "line":
                    continue
                dx, dy = q.x - p.x, q.y - p.y
                L = math.hypot(dx, dy)
                if L < 250 or abs(dy) < 0.9 * L:
                    continue
                a = math.degrees(math.atan2(dx, dy)) if dy > 0 else math.degrees(math.atan2(-dx, -dy))
                if abs(a - target) < 10:
                    angs.append((L, a))
        if angs:
            a = sum(L * x for L, x in angs) / sum(L for L, _ in angs)
            if abs(a - target) > 2:
                out.append((g.name, "slant", "", f"{a:.1f} degrees, not {target}"))
    return out


def accents(font, shapes):
    """accent findings: a mark's gap off its usual one on its kind of letter."""
    from make_bold import mark_like

    marks = {g.name for g in font if mark_like(g)}
    # marks are set at one height whatever the letter's overshoot (as in
    # Libertinus and Charis: Ḍ Ọ, Ả Ẻ alike), so a round or pointed edge
    # counts from the flat zone it overshoots
    flat = [b[i] for n in ("H", "x", "h.sc") if n in font and (b := shapes.bounds(n)) for i in (1, 3)]
    over = max((abs(shapes.bounds(n)[1]) for n in ("O", "o") if n in font and shapes.bounds(n)), default=0) + 6

    def unshoot(y, top):
        for f in flat:
            if 0 < (y - f if top else f - y) <= over:
                return f
        return y

    rows = collections.defaultdict(list)
    for g in font:
        if not g.components or g.contours or len(g.components) != 2:
            continue
        base, mark = g.components
        if base.baseGlyph in marks or mark.baseGlyph not in marks:
            continue
        bb, mb = shapes.bounds(base.baseGlyph), shapes.bounds(mark.baseGlyph)
        if not bb or not mb:
            continue
        dy = mark.transformation[5] - base.transformation[5]
        top = mb[1] + dy > (bb[1] + bb[3]) / 2
        gap = (mb[1] + dy - unshoot(bb[3], True)) if top else (unshoot(bb[1], False) - (mb[3] + dy))
        if gap < -200:
            # beside the letter, not above (Greek capitals' breathings and
            # tonos) or inside a descender (ỵ's dot under the fork): set at
            # one height, so the gap only tells the letter's overshoot
            continue
        kind = ("cap" if bb[3] > 1200 and not g.name.endswith(".sc") else "sc" if g.name.endswith(".sc") else "lc")
        rows[(mark.baseGlyph, kind, top)].append((gap, g.name))
    out = []
    for (mark, _kind, top), items in rows.items():
        if len(items) < 4:
            continue
        med = statistics.median(v for v, _ in items)
        for v, name in items:
            if abs(v - med) > 25:
                out.append((name, "accent", "above" if top else "below", f"{mark} gap {round(v)}, usually {round(med)}"))
    return out


WOBBLE_TURN, WOBBLE_LEN, WOBBLE_STEP = 3, 160, 4  # degrees; units; units between samples


def _directions(contour):
    """(x, y, direction, on a curve) every WOBBLE_STEP units along a contour"""
    P = list(contour.points)
    n = len(P)
    ons = [i for i, p in enumerate(P) if p.type]
    out = []
    for k, i in enumerate(ons):
        j = ons[(k + 1) % len(ons)]
        offs = [(i + m) % n for m in range(1, (j - i) % n or n)]
        pts = [(P[x].x, P[x].y) for x in (i, *offs, j)]
        if len(pts) == 2:
            m = max(1, int(math.dist(*pts) / WOBBLE_STEP))
            a = _angle(*pts)
            out += [(pts[0][0] + (pts[1][0] - pts[0][0]) * s / m, pts[0][1] + (pts[1][1] - pts[0][1]) * s / m, a, False)
                    for s in range(m)]
        elif len(pts) == 4:
            m = max(2, int(sum(math.dist(pts[q], pts[q + 1]) for q in range(3)) / WOBBLE_STEP))
            for s in range(m):
                t = s / m
                u = 1 - t
                dx, dy = (3 * u * u * (pts[1][q] - pts[0][q]) + 6 * u * t * (pts[2][q] - pts[1][q])
                          + 3 * t * t * (pts[3][q] - pts[2][q]) for q in (0, 1))
                if dx or dy:
                    x, y = _bez(pts, t)
                    out.append((x, y, math.atan2(dy, dx), True))
    return out


def reversals(glyph):
    """[(x, y, degrees)]: where a curve bends back the other way for a short
    stretch between two bends the first way (corners and straight edges
    break the run)"""
    out = []
    for c in glyph.contours:
        s = _directions(c)
        n = len(s)
        if n < 6:
            continue
        lobes = []  # [sign, degrees, first sample, samples]
        for i in range(n):
            t = math.degrees((s[(i + 1) % n][2] - s[i][2] + math.pi) % (2 * math.pi) - math.pi)
            if abs(t) > 30 or not s[i][3]:
                lobes.append([0, 0, i, 1])
                continue
            sign = 1 if t > 0.01 else -1 if t < -0.01 else 0
            if not sign:
                continue
            if lobes and lobes[-1][0] == sign:
                lobes[-1][1] += t
                lobes[-1][3] += 1
            else:
                lobes.append([sign, t, i, 1])
        for a, b, d in zip(lobes, lobes[1:], lobes[2:]):
            if (a[0] and b[0] and a[0] == d[0] != b[0] and b[3] * WOBBLE_STEP <= WOBBLE_LEN
                    and min(abs(a[1]), abs(b[1]), abs(d[1])) > WOBBLE_TURN):
                x, y = s[b[2] + b[3] // 2][:2]
                out.append((round(x), round(y), abs(b[1])))
    return out


def wobbles(font, source):
    """wobble findings (a generated style): reversals beyond its source's."""
    out = []
    for g in font:
        if not g.contours or g.name not in source:
            continue
        mine, theirs = reversals(g), reversals(source[g.name])
        if len(mine) > len(theirs):
            where = "; ".join(f"{x},{y} {d:.0f} degrees" for x, y, d in mine)
            out.append((g.name, "wobble", "", f"{len(mine)} against {len(theirs)}: {where}"))
    return out


def widths(font, regular):
    """width findings (the Bold): advances off its usual ratio to the Regular's."""
    ratios = {g.name: g.width / regular[g.name].width for g in font
              if g.name in regular and g.width and regular[g.name].width and g.contours}
    if not ratios:
        return []
    med = statistics.median(ratios.values())
    return [(n, "width", "", f"{r:.2f} of the Regular's, usually {med:.2f}")
            for n, r in ratios.items() if abs(r / med - 1) > 0.10]


def check(font, path=None, kinds=KINDS):
    """{glyph: [(kind, where, detail), ...]} for the glyphs with findings."""
    found = collections.defaultdict(list)
    if {"smooth", "kink", "extreme", "step", "grid"} & set(kinds):
        for g in font:
            for k, where, detail in construction(g):
                if k in kinds:
                    found[g.name].append((k, where, detail))
    shapes = Shapes(font)
    rest = []
    if "zone" in kinds:
        rest += zones(font, shapes)
    if "weight" in kinds:
        rest += weights(font, shapes)
    if "slant" in kinds:
        rest += slant(font)
    if "accent" in kinds:
        rest += accents(font, shapes)
    if "wobble" in kinds and path and Path(path).name.endswith(("-Bold.ufo", "-BoldItalic.ufo")):
        source = str(path).replace("-BoldItalic.ufo", "-Italic.ufo").replace("-Bold.ufo", "-Regular.ufo")
        rest += wobbles(font, ufoLib2.Font.open(source))
    if "width" in kinds and path and Path(path).name.endswith("-Bold.ufo"):
        regular = ufoLib2.Font.open(str(path).replace("-Bold.ufo", "-Regular.ufo"))
        rest += widths(font, regular)
    if "stroke" in kinds:
        from strokes import strokes

        rest += strokes(font)[0]
    if set(DERIVED) & set(kinds):
        from derived import derived

        rest += [f for f in derived(font, path)[0] if f[1] in kinds]
    for name, k, where, detail in rest:
        found[name].append((k, where, detail))
    return dict(found)


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--kind", action="append", choices=KINDS)
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    found = check(font, args.ufo, tuple(args.kind or KINDS))
    counts = collections.Counter()
    for name, items in sorted(found.items()):
        for k, where, detail in items:
            counts[k] += 1
            print(f"{name:20} {k:8} {where:>12}  {detail}")
    print(f"{Path(args.ufo).name}: " + ", ".join(f"{k} {v}" for k, v in counts.most_common()), file=sys.stderr)


if __name__ == "__main__":
    main()
