"""curvature.py UFO [GLYPH ...] [--sheet PDF]: where a smooth outline turns
unevenly (2026-11-27).

Every check before this one reads directions: a kink is a corner, a smooth
node one whose handles do not line up. None reads how evenly a curve turns,
and the Bold Italic's T came out of the stroker with the arm's underside as
a tight turn at the stem and a long, nearly straight sweep to the serif (the
designer saw it on Ʈ: "very unround"); its tangents are continuous, so
nothing flagged it.

Three measures:

- runs (a generated style against its source: the Bold against the
  Regular, the Bold Italic against the Italic). The outline is cut into
  runs that turn one way without a corner (lines inside a run count, an
  inflection ends it); each run is read as the arc length it spends per
  WINDOW degrees of turning, i.e. its mean radius at each direction. The
  same directions of the source's run in the same place are read alike,
  and per window q = log((r + R0) / (r_source * sx + R0)), sx the advances'
  ratio. Emboldening adds about the same to every radius and contrast
  changes it slowly along the run, so q follows a straight trend over the
  run's directions; a window off that trend by LIMIT or more is a place
  where the style turns at another rate than its source does there (R0
  keeps a small corner round, 8 against 40 units, from counting as a
  fivefold change). The ends of a common stretch are left out: there the
  run meets a straight, and where the turn starts is not the shape.
- joins: the curvature at either side of a smooth node, JUMP times apart.
- flats: a curve that turns one way but is FLAT times flatter inside than at
  both ends.

For a generated style joins and flats list only what its source has nothing
like near; for the Regular and the Italic (no source to read) only joins
and flats are read. Candidates for the designer's eye, not a gate: `--sheet`
draws the strongest runs finds, source beside style, the run in red and
the window ringed. The runs finds of the Bold and the Bold Italic are
baselines (tests/test_curvature.py, data/curvature-Bold.txt ...: all
accepted by the designer from the sheets, 2026-11-27); a new one fails,
and a mended one's line goes (scripts/update_test_data.py --curvature).

    python -I scripts/quality/curvature.py sources/MyiaDidot-BoldItalic.ufo T
    python -I scripts/quality/curvature.py sources/MyiaDidot-BoldItalic.ufo --sheet build/quality/curvature-BoldItalic.pdf
"""

import argparse
import itertools
import math
import subprocess
from pathlib import Path

import ufoLib2
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

SMOOTH = 3  # degrees: tangents this close make a smooth join
JUMP = 3.0  # curvature ratio across a smooth join reported
MIN_LEG = 4  # units: a shorter handle leaves the curvature undefined
NEAR = 80  # units: the source's node counted as the same place
SOURCE = {"BoldItalic": "Italic", "Bold": "Regular"}

WINDOW = 10  # degrees of turning read as one radius
MIN_RUN = 15  # degrees: a run turning less has no roundness to compare
SAMPLES_RUN = 48  # points per curve along a run
CLIP = (8, 2000)  # units: radii outside are a corner, or straight
R0 = 100  # units added to both radii: a small corner rounder by the offset is no change
LIMIT = 0.7  # off the run's trend: e^0.7, about twice the expected radius (plus R0)
MATCH = 250  # units: the mean distance at which the source's run is still the same place
MIN_WINDOWS = 3  # common windows inside the ends, fewer read no trend


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


# -- runs ---------------------------------------------------------------------


class _Segments(BasePen):
    """contours as [[(kind, points from the previous on-curve)]], components
    drawn through the glyph set"""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours, self._cur, self._start = [], None, None

    def _moveTo(self, p):
        self._cur, self._start = [], p
        self._last = p

    def _lineTo(self, p):
        if math.dist(self._last, p) > 0.5:
            self._cur.append(("line", [self._last, p]))
        self._last = p

    def _curveToOne(self, p1, p2, p3):
        self._cur.append(("curve", [self._last, p1, p2, p3]))
        self._last = p3

    def _closePath(self):
        if math.dist(self._last, self._start) > 0.5:
            self._cur.append(("line", [self._last, self._start]))
        if self._cur:
            self.contours.append(self._cur)
        self._cur = None

    _endPath = _closePath


def _direction(kind, p, end):
    if kind == "line":
        a, b = p[0], p[-1]
    elif end == 0:
        a, b = p[0], next((q for q in p[1:] if math.dist(q, p[0]) > 1e-6), p[-1])
    else:
        a, b = next((q for q in reversed(p[:-1]) if math.dist(q, p[-1]) > 1e-6), p[0]), p[-1]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _chains(glyph, glyphset):
    """[(contour index, [segment])]: segments joined within SMOOTH degrees"""
    pen = _Segments(glyphset)
    glyph.draw(pen)
    out = []
    for ci, segs in enumerate(pen.contours):
        n = len(segs)
        smooth = [abs(math.degrees(_wrap(_direction(*segs[(k + 1) % n], 0) - _direction(*segs[k], 1)))) <= SMOOTH
                  for k in range(n)]
        if all(smooth):
            out.append((ci, segs))
            continue
        start = smooth.index(False) + 1
        cur = []
        for m in range(n):
            k = (start + m) % n
            cur.append(segs[k])
            if not smooth[k]:
                out.append((ci, cur))
                cur = []
    return out


def _bezier(p, t):
    u = 1 - t
    return tuple(u**3 * p[0][i] + 3 * u * u * t * p[1][i] + 3 * u * t * t * p[2][i] + t**3 * p[3][i] for i in (0, 1))


def runs(glyph, glyphset=None):
    """[{contour, sign, pts: [(x, y, direction unwrapped, arc length)]}]:
    the outline's runs turning one way, MIN_RUN degrees at least"""
    out = []
    for ci, segs in _chains(glyph, glyphset):
        samples = []
        for kind, p in segs:
            if kind == "curve":
                samples += [_bezier(p, j / SAMPLES_RUN) for j in range(SAMPLES_RUN + 1)]
            else:
                samples += [p[0], p[-1]]
        steps = [(b, math.atan2(b[1] - a[1], b[0] - a[0]), math.dist(a, b))
                 for a, b in itertools.pairwise(samples) if math.dist(a, b) > 1e-6]
        if len(steps) < 2:
            continue
        th, s, sign, prev = steps[0][1], 0.0, 0, steps[0][1]
        cur = [(*samples[0], th, 0.0)]
        for b, ang, d in steps:
            dth = _wrap(ang - prev)
            sg = (dth > 1e-3) - (dth < -1e-3)
            if sg and sign and sg != sign:
                out.append({"contour": ci, "sign": sign, "pts": cur})
                cur, s = [(*cur[-1][:2], th, 0.0)], 0.0
            if sg:
                sign = sg
            th, prev, s = th + dth, ang, s + d
            cur.append((*b, th, s))
        out.append({"contour": ci, "sign": sign, "pts": cur})
    return [r for r in out if r["sign"] and abs(r["pts"][-1][2] - r["pts"][0][2]) > math.radians(MIN_RUN)]


def _at(run, th):
    """(arc length, point) where the run's direction reaches th"""
    pts, sg = run["pts"], run["sign"]
    prev = pts[0]
    for q in pts[1:]:
        if (q[2] - th) * sg >= 0:
            d = q[2] - prev[2]
            f = (th - prev[2]) / d if abs(d) > 1e-12 else 1
            return prev[3] + f * (q[3] - prev[3]), (prev[0] + f * (q[0] - prev[0]), prev[1] + f * (q[1] - prev[1]))
        prev = q
    return pts[-1][3], pts[-1][:2]


def windows(run):
    """{window: (radius, point, order)}: the run's mean radius in each whole
    WINDOW of absolute direction it covers"""
    w = math.radians(WINDOW)
    a, b = run["pts"][0][2], run["pts"][-1][2]
    out = {}
    for k in range(math.ceil(min(a, b) / w), math.floor(max(a, b) / w)):
        (s0, p0), (s1, p1) = _at(run, k * w), _at(run, (k + 1) * w)
        r = min(max(abs(s1 - s0) / w, CLIP[0]), CLIP[1])
        out[k % round(360 / WINDOW)] = (r, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), k * run["sign"])
    return out


def run_finds(glyph, source, glyphset=None, source_glyphset=None, limit=LIMIT):
    """[{q, at, r, r_source, run, source_run}]: the windows of glyph's runs
    off their trend against the source's run by limit or more, the worst
    per run"""
    sx = glyph.width / source.width if source.width else 1
    theirs = [(r, windows(r)) for r in runs(source, source_glyphset)]
    same_contours = len(glyph.contours) == len(source.contours)
    out = []
    for run in runs(glyph, glyphset):
        mine = windows(run)
        best = None
        for other, wo in theirs:
            if other["sign"] != run["sign"] or same_contours and other["contour"] != run["contour"]:
                continue
            common = [k for k in mine if k in wo]
            if len(common) < MIN_WINDOWS + 2:
                continue
            d = sum(math.dist(mine[k][1], (wo[k][1][0] * sx, wo[k][1][1])) for k in common) / len(common)
            if best is None or d < best[0]:
                best = (d, other, wo, common)
        if best is None or best[0] > MATCH:
            continue
        _, other, wo, common = best
        inner = sorted(common, key=lambda k: mine[k][2])[1:-1]
        y = [math.log((mine[k][0] + R0) / (wo[k][0] * sx + R0)) for k in inner]
        x = range(len(inner))
        mx, my = (len(inner) - 1) / 2, sum(y) / len(y)
        slope = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True)) / sum((a - mx) ** 2 for a in x)
        off = [b - my - slope * (a - mx) for a, b in zip(x, y, strict=True)]
        i = max(x, key=lambda j: abs(off[j]))
        if abs(off[i]) >= limit:
            k = inner[i]
            out.append({"q": off[i], "at": mine[k][1], "r": mine[k][0], "r_source": wo[k][0],
                        "run": run, "source_run": other})
    return out


def run_keys(font, source, limit=LIMIT):
    """{"glyph runs count": where}: the runs finds per glyph, as the
    baselines tests/data/curvature-Bold.txt and -BoldItalic.txt list them"""
    keys = {}
    for g in font:
        if g.name not in source or not (g.contours or g.components):
            continue
        got = sorted(run_finds(g, source[g.name], font, source, limit), key=lambda f: -abs(f["q"]))
        if got:
            keys[f"{g.name} runs {len(got)}"] = " ; ".join(
                f"{f['q']:+.2f} at {f['at'][0]:.0f},{f['at'][1]:.0f} r {f['r']:.0f}/{f['r_source']:.0f}" for f in got)
    return keys


def source_of(path):
    """the source style's UFO beside a generated style's, or None"""
    path = Path(path)
    style = path.stem.split("-")[-1]
    return path.with_name(path.name.replace(style, SOURCE[style])) if style in SOURCE else None


# -- joins and flats ----------------------------------------------------------


def end_curvature(p0, p1, p2):
    """signed curvature of a cubic at p0, p1 its handle, p2 the next one"""
    d1, d2 = _sub(p1, p0), _sub(p2, p1)
    n = math.hypot(*d1)
    if n < MIN_LEG:
        return None
    return 2 / 3 * _cross(d1, d2) / n**3


def joins(glyph):
    """[(x, y, k_before, k_after)] at each smooth join of two curves"""
    out = []
    for contour in glyph.contours:
        pts = [(p.x, p.y, p.type) for p in contour.points]
        n = len(pts)
        for i, (x, y, t) in enumerate(pts):
            if t != "curve" or pts[(i + 1) % n][2] is not None or pts[(i - 1) % n][2] is not None:
                continue
            # the curve after starts at i: its handles i+1, i+2
            if pts[(i + 3) % n][2] != "curve":
                continue
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
            ta, tb = _sub((x, y), a[:2]), _sub(b[:2], (x, y))
            if min(math.hypot(*ta), math.hypot(*tb)) < MIN_LEG:
                continue
            turn = math.degrees(math.atan2(_cross(ta, tb), ta[0] * tb[0] + ta[1] * tb[1]))
            if abs(turn) > SMOOTH:
                continue
            # curvature at the end of the curve before: reversed, from (x, y)
            kb = end_curvature((x, y), a[:2], pts[(i - 2) % n][:2])
            ka = end_curvature((x, y), b[:2], pts[(i + 2) % n][:2])
            if kb is None or ka is None:
                continue
            out.append((x, y, -kb, ka))  # (the reversed curve turns the other way)
    return out


def jumps(glyph):
    """[(x, y, ratio, kb, ka)] the joins whose curvature jumps by JUMP or more"""
    out = []
    for x, y, kb, ka in joins(glyph):
        lo, hi = sorted((abs(kb), abs(ka)))
        same_side = kb * ka > 0
        ratio = hi / lo if lo > 1e-9 else math.inf
        if same_side and ratio >= JUMP:
            out.append((x, y, ratio, kb, ka))
    return out


FLAT = 3.0  # a curve this much flatter inside than at both its ends: a flat spot
SAMPLES = 16
MIN_LENGTH = 60  # units: a shorter curve's flat spot does not show
MIN_TURN = 20  # degrees the curve turns in all: a nearly straight one has no roundness to lose
MAX_RADIUS = 1000  # units: ends flatter than this are no rounder than the middle to the eye


def _point_curvature(seg, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg
    u = 1 - t
    d1 = (3 * (u * u * (x1 - x0) + 2 * u * t * (x2 - x1) + t * t * (x3 - x2)),
          3 * (u * u * (y1 - y0) + 2 * u * t * (y2 - y1) + t * t * (y3 - y2)))
    d2 = (6 * (u * (x2 - 2 * x1 + x0) + t * (x3 - 2 * x2 + x1)), 6 * (u * (y2 - 2 * y1 + y0) + t * (y3 - 2 * y2 + y1)))
    pt = (u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
          u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3)
    n = math.hypot(*d1)
    return pt, (_cross(d1, d2) / n**3 if n > 1e-6 else None)


def flats(glyph):
    """[(x, y, ratio, k_min, k_ends)] curves that turn one way throughout but
    go FLAT times flatter inside than at both ends"""
    out = []
    for contour in glyph.contours:
        pts = [(p.x, p.y, p.type) for p in contour.points]
        n = len(pts)
        for i, (_, _, t) in enumerate(pts):
            if t is None or pts[(i + 1) % n][2] is not None or pts[(i + 3) % n][2] != "curve":
                continue
            seg = [pts[(i + k) % n][:2] for k in range(4)]
            ks = [_point_curvature(seg, j / SAMPLES) for j in range(SAMPLES + 1)]
            if any(k is None for _, k in ks):
                continue
            vals = [k for _, k in ks]
            if not (all(v > 0 for v in vals) or all(v < 0 for v in vals)):
                continue
            ends = min(abs(vals[0]), abs(vals[-1]))
            length = sum(math.dist(ks[m][0], ks[m + 1][0]) for m in range(SAMPLES))
            a0 = _sub(seg[1], seg[0]) if math.dist(seg[0], seg[1]) > 1e-6 else _sub(seg[2], seg[0])
            a1 = _sub(seg[3], seg[2]) if math.dist(seg[2], seg[3]) > 1e-6 else _sub(seg[3], seg[1])
            turn = abs(math.degrees(math.atan2(_cross(a0, a1), a0[0] * a1[0] + a0[1] * a1[1])))
            if length < MIN_LENGTH or turn < MIN_TURN or ends < 1 / MAX_RADIUS:
                continue
            j = min(range(1, SAMPLES), key=lambda m: abs(vals[m]))
            if abs(vals[j]) > 1e-9 and ends / abs(vals[j]) >= FLAT:
                (px, py), _ = ks[j]
                out.append((px, py, ends / abs(vals[j]), abs(vals[j]), ends))
    return out


def own(glyph, source_glyph):
    """the joins and flats of glyph its source glyph has nothing like near"""
    sx = glyph.width / source_glyph.width if source_glyph.width else 1
    out = []
    for measure in (jumps, flats):
        theirs = measure(source_glyph)
        out += [j for j in measure(glyph)
                if not any(math.dist((j[0], j[1]), (s[0] * sx, s[1])) < NEAR and s[2] >= j[2] / 2 for s in theirs)]
    return out


# -- the sheet ----------------------------------------------------------------


def _families(found):
    """the runs finds grouped where glyphs share the shape (one radius pair
    at nearly one place: T Ʈ Ⱦ, the f-ligatures), strongest first"""
    groups = {}
    for name, f in found:
        key = (round(f["q"], 1), round(f["r"] / 5), round(f["r_source"] / 5))
        groups.setdefault(key, []).append((name, f))
    return sorted(groups.values(), key=lambda g: -abs(g[0][1]["q"]))


def _label(font, name):
    g = font[name]
    return f"{name} {chr(g.unicode)}" if g.unicode and g.unicode > 32 else name


def sheet(out, font, source, found, top=24, style="", source_style=""):
    """the top run finds as a PDF: per find the source glyph, then the
    style's, filled, the run in red, the window ringed"""
    cell_w, cell_h, cols, pad = 520, 300, 2, 24
    groups = _families(found)[:top]
    rows = math.ceil(len(groups) / cols)
    W, H = pad * 2 + cols * cell_w, 60 + rows * cell_h
    title = (f'<text x="{pad}" y="28" font-family="DejaVu Sans" font-size="15" font-weight="bold">'
             f"{style}: runs that turn at another rate than the {source_style}'s ({len(found)} finds, "
             f"{len(groups)} shown)</text>")
    key = (f'<text x="{pad}" y="46" font-family="DejaVu Sans" font-size="10" fill="#555">'
           f"each pair: {source_style} left, {style} right; red the run, the ring the window off its trend; "
           "r its radius against the source's there (units), q how far off (log, LIMIT "
           f"{LIMIT})</text>")
    body = [title, key]
    for n, group in enumerate(groups):
        name, f = group[0]
        x0, y0 = pad + (n % cols) * cell_w, 60 + (n // cols) * cell_h
        g, s = font[name], source[name]
        boxes = []
        for gl, fo in ((s, source), (g, font)):
            bp = BoundsPen(fo)
            gl.draw(bp)
            boxes.append(bp.bounds or (0, 0, gl.width, 1000))
        ymin, ymax = min(b[1] for b in boxes), max(b[3] for b in boxes)
        widths = [max(b[2], gl.width) - min(b[0], 0) for b, gl in zip(boxes, (s, g), strict=True)]
        scale = min((cell_h - 60) / (ymax - ymin), (cell_w / 2 - 20) / max(widths))
        others = ", ".join(_label(font, m) for m, _ in group[1:6]) + (" ..." if len(group) > 6 else "")
        body.append(f'<text x="{x0}" y="{y0 + 14}" font-family="DejaVu Sans" font-size="12" font-weight="bold">'
                    f'{_label(font, name)}</text><text x="{x0}" y="{y0 + 28}" font-family="DejaVu Sans" '
                    f'font-size="9" fill="#555">q {f["q"]:+.2f} at {f["at"][0]:.0f},{f["at"][1]:.0f}: '
                    f'r {f["r"]:.0f} against {f["r_source"]:.0f}'
                    + (f"; also {others}" if others else "") + "</text>")
        for j, (gl, fo, box, run, ring) in enumerate((
                (s, source, boxes[0], f["source_run"], None), (g, font, boxes[1], f["run"], f["at"]))):
            ox = x0 + j * cell_w / 2 - min(box[0], 0) * scale
            base = y0 + 40 + ymax * scale
            tr = (scale, 0, 0, -scale, ox, base)
            pen = SVGPathPen(fo)
            gl.draw(TransformPen(pen, tr))
            body.append(f'<path d="{pen.getCommands()}" fill="#9a9a9a"/>')
            pts = " ".join(f"{ox + p[0] * scale:.1f},{base - p[1] * scale:.1f}" for p in run["pts"])
            body.append(f'<polyline points="{pts}" fill="none" stroke="#d00" stroke-width="2.2"/>')
            if ring:
                body.append(f'<circle cx="{ox + ring[0] * scale:.1f}" cy="{base - ring[1] * scale:.1f}" r="11" '
                            'fill="none" stroke="#06c" stroke-width="2"/>')
    svg_doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
               '<rect width="100%" height="100%" fill="#fff"/>' + "".join(body) + "</svg>")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    svg = out.with_suffix(".svg")
    svg.write_text(svg_doc, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(out), str(svg)], check=True)
    svg.unlink()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--sheet", help="PDF of the strongest runs finds (generated styles)")
    ap.add_argument("--top", type=int, default=24, help="groups on the sheet")
    ap.add_argument("--limit", type=float, default=LIMIT)
    a = ap.parse_args()
    path = Path(a.ufo)
    font = ufoLib2.Font.open(path)
    style = path.stem.split("-")[-1]
    source = ufoLib2.Font.open(source_of(path)) if source_of(path) else None
    found_runs, found_points = [], {}
    for g in font:
        if a.glyphs and g.name not in a.glyphs or not (g.contours or g.components):
            continue
        if source is not None and g.name in source:
            found_runs += [(g.name, f) for f in run_finds(g, source[g.name], font, source, a.limit)]
            got = own(g, source[g.name])
        else:
            got = jumps(g) + flats(g)
        if got:
            found_points[g.name] = got
    if source is not None:
        print(f"{style} runs against the {SOURCE[style]}: {len(found_runs)} in {len({n for n, _ in found_runs})} glyphs")
        for name, f in sorted(found_runs, key=lambda nf: -abs(nf[1]["q"])):
            print(f"   {name:14} {f['q']:+.2f} at {f['at'][0]:.0f},{f['at'][1]:.0f}"
                  f"  r {f['r']:.0f} against {f['r_source']:.0f}")
    print(f"{style} joins and flats{' of its own' if source is not None else ''}: {len(found_points)} glyphs")
    for name, got in sorted(found_points.items(), key=lambda kv: -max(j[2] for j in kv[1])):
        print(f"   {name:14}", "  ".join(f"{x:.0f},{y:.0f}: {r:.1f}x" for x, y, r, *_ in sorted(got, key=lambda j: -j[2])[:4]))
    if a.sheet:
        if source is None:
            ap.error("--sheet reads runs, which need a generated style")
        print(sheet(a.sheet, font, source, found_runs, a.top, style, SOURCE[style]))


if __name__ == "__main__":
    main()
