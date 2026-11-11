"""What the Bold gains over the Regular, beside what the references gain (F4, phase 7).

    python scripts/quality/bold_measures.py [--italic] [--range] [--chars TEXT]
        [--out build/quality/bold-measures.md] [--json build/quality/bold-measures.json]

Each pair is a regular and its bold: Myia's from the UFOs (sources/, the
master, no build needed), the references' from build/refs/ (fetch_refs.py).
By default the pairs are Myia and Old Standard (Kryukov's own emboldening,
phase 7's calibrated reference); --range adds Bodoni Moda 11 and Libre
Bodoni, so the gains read as a range, not a target. --italic measures the
Italic against the Bold Italic for phase 8 (Old Standard has no bold italic
in build/refs, so the range is the reference there).

Outlines are deslanted by the font's italic angle and scaled to a 1000 em.
The measures, per character:

  advance, ink    the advance width and the ink's width
  stem            the first straight stem's width (stems())
  white           the area of all counters together
  counters        how many; where the weights differ, no counter is compared
  counterN        each counter's area, width and aperture, counters ordered
                  top to bottom, left to right. A counter is white that sees
                  ink in at least ENCLOSED of eight directions (rows, columns,
                  diagonals), larger than MIN_COUNTER of the zone squared and
                  MIN_WIDTH of the zone wide:
                  counters see it in 7-8, the slots beside serifs and the
                  white under r's arm in 4-5 (surveyed 2026-11-11 on Myia, Old
                  Standard and Bodoni Moda, upright and italic). Its width is
                  the widest disc inside it; its aperture the widest that
                  passes from it to the outside (0 for a closed counter): o's
                  is 0, c's the gap at its mouth, n's the gap between its feet
  join            where an arch or a bowl leaves a stem (JOINS): the ink's
                  height in a column JOIN_OFFSET stems beside the stem's edge,
                  the highest run (top), the lowest (bottom) or the one
                  nearest half the zone (mid)
  ball            a ball terminal's diameter: the widest disc of ink whose
                  centre lies in the terminal's region (BALLS, fractions of
                  the ink's box)

Then per family the median gain (bold over regular) of each measure, Myia's
beside each reference's, and Myia's gain over the reference's: above 1 the
Bold gains more than the reference does. The tools find candidates; the
designer's eye decides what the Bold should change.

Known limits: a few letters keep a hollow beside their counters (b f h, some
italic exits), and where the two weights count different counters only the
counts are shown, nothing compared by place (b, f, h in Myia's upright pair,
2026-11-11). A join is the column through the stem's
side; on a sloped arch it reads thicker than across the stroke, the same in
every font. Balls are found by region: a g whose ear is a flag gets its
flag's width.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np
import pathops
import skia
import ufoLib2
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, REFDIR, ROOT, SETS

EM = 1000
PX = 2  # units of the 1000 em per pixel for counters, apertures and balls
MIN_COUNTER = 0.02  # of the zone squared
MIN_WIDTH = 0.105  # of the zone: the pockets in serifs' brackets are 0.09-0.10 wide, P's bowl 0.13
ENCLOSED = 6  # of eight directions in which a counter's white sees ink (counters())
JOIN_OFFSET = 0.5  # stems beside the stem's edge
STEM_ROWS = range(4, 13)  # of 20: 20 % to 60 % of the zone
STEM_AT = (10, 8, 6, 12)  # of 20: where a stem is looked for
STEM_STRAIGHT = 0.015  # of the zone

CORE = (SETS["latin-lc"][:26] + SETS["latin-uc"][:26] + SETS["figures"] + SETS["greek-lc"] + SETS["greek-uc"]
        + SETS["cyr-lc"][:33] + SETS["cyr-uc"][:33])

# char: [(stem index among the straight stems, left to right; side; where)]
JOINS = {
    "n": [(0, "R", "top")], "m": [(0, "R", "top"), (1, "R", "top")], "h": [(0, "R", "top")],
    "r": [(0, "R", "top")], "u": [(-1, "L", "bottom")],
    "b": [(0, "R", "top"), (0, "R", "bottom")], "p": [(0, "R", "top"), (0, "R", "bottom")],
    "d": [(-1, "L", "top"), (-1, "L", "bottom")], "q": [(-1, "L", "top"), (-1, "L", "bottom")],
    "a": [(-1, "L", "top"), (-1, "L", "mid"), (-1, "L", "bottom")],
    "B": [(0, "R", "top"), (0, "R", "mid"), (0, "R", "bottom")], "D": [(0, "R", "top"), (0, "R", "bottom")],
    "P": [(0, "R", "top"), (0, "R", "mid")], "R": [(0, "R", "top"), (0, "R", "mid")],
    "п": [(0, "R", "top")], "р": [(0, "R", "top"), (0, "R", "bottom")], "η": [(0, "R", "top")],
    "μ": [(-1, "L", "bottom")],
}
# char: (x0, x1, y0, y1) of the ink's box where the ball's centre lies
BALLS = {
    "a": (0.0, 0.5, 0.55, 1.0), "c": (0.55, 1.0, 0.5, 1.0), "f": (0.55, 1.0, 0.75, 1.0),
    "r": (0.55, 1.0, 0.5, 1.0), "y": (0.0, 0.45, 0.0, 0.3), "j": (0.0, 0.5, 0.0, 0.3),
    "g": (0.65, 1.0, 0.75, 1.0), "J": (0.0, 0.5, 0.0, 0.35),
    "с": (0.55, 1.0, 0.5, 1.0), "у": (0.0, 0.45, 0.0, 0.3), "ς": (0.55, 1.0, 0.55, 1.0),
}
FAMILIES = {
    "arches": "nmhru", "bowls": "bdpq", "rounds": "oce", "apertures": "ceas", "balls": "acfryjg",
    "straights": "il", "diagonals": "vwxyzk", "two-storey": "ag",
    "capital rounds": "OCGQ", "capital straights": "HINU", "capital bowls": "BDPR",
    "figures": "0123456789",
    "greek": SETS["greek-lc"], "cyrillic": SETS["cyr-lc"][:33],
}
PAIRS = {
    False: [("Myia", "sources/MyiaDidot-Regular.ufo", "sources/MyiaDidot-Bold.ufo"),
            ("Old Standard", "OldStandard-Regular", "OldStandard-Bold"),
            ("Bodoni Moda", "BodoniModa-11-Regular", "BodoniModa-11-Bold"),
            ("Libre Bodoni", "LibreBodoni-Regular", "LibreBodoni-Bold")],
    True: [("Myia", "sources/MyiaDidot-Italic.ufo", "sources/MyiaDidot-BoldItalic.ufo"),
           ("Bodoni Moda", "BodoniModa-11-Italic", "BodoniModa-11-BoldItalic"),
           ("Libre Bodoni", "LibreBodoni-Italic", "LibreBodoni-BoldItalic")],
}


class _SkiaPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.path = skia.Path()

    def _moveTo(self, p):
        self.path.moveTo(*p)

    def _lineTo(self, p):
        self.path.lineTo(*p)

    def _curveToOne(self, a, b, c):
        self.path.cubicTo(*a, *b, *c)

    def _qCurveToOne(self, a, b):
        self.path.quadTo(*a, *b)

    def _closePath(self):
        self.path.close()


class _Segments(BasePen):
    """Explicit cubic segments for pathops: quadratics raised to cubics, or
    pathops gives them back as TrueType contours of off-curve points only
    (qCurveTo ending in None), which derived.Outline cannot read."""

    def __init__(self, pen, glyph_set=None):
        super().__init__(glyph_set)  # components drawn through it
        self.pen = pen

    def _moveTo(self, p):
        self.pen.moveTo(p)

    def _lineTo(self, p):
        self.pen.lineTo(p)

    def _curveToOne(self, a, b, c):
        self.pen.curveTo(a, b, c)

    def _qCurveToOne(self, a, b):
        p0 = self._getCurrentPoint()
        self.pen.curveTo(tuple(p0[k] + 2 / 3 * (a[k] - p0[k]) for k in (0, 1)),
                         tuple(b[k] + 2 / 3 * (a[k] - b[k]) for k in (0, 1)), b)

    def _closePath(self):
        self.pen.closePath()


class Rows(BasePen):
    """A path as polygons (BasePen reads any contour pathops gives, quadratic
    ones of off-curve points only included), cut into ink runs at a height;
    swap=True cuts it into columns instead."""

    def __init__(self, path, swap=False, steps=12):
        super().__init__(None)
        self.swap, self.steps, self.polys, self.cur = swap, steps, [], []
        path.draw(self)

    def _pt(self, p):
        self.cur.append((p[1], p[0]) if self.swap else tuple(p))

    def _moveTo(self, p):
        self.cur = []
        self._pt(p)

    def _lineTo(self, p):
        self._pt(p)

    def _curveToOne(self, a, b, c):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self._pt(tuple(u ** 3 * p0[k] + 3 * u * u * t * a[k] + 3 * u * t * t * b[k] + t ** 3 * c[k]
                           for k in (0, 1)))

    def _qCurveToOne(self, a, b):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self._pt(tuple(u * u * p0[k] + 2 * u * t * a[k] + t * t * b[k] for k in (0, 1)))

    def _closePath(self):
        if self.cur:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath

    def spans(self, y):
        xs = []
        for poly in self.polys:
            for i in range(len(poly)):
                (x0, y0), (x1, y1) = poly[i - 1], poly[i]
                if (y0 <= y) != (y1 <= y):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        return list(zip(xs[::2], xs[1::2]))


class Source:
    """A font's outlines by character: merged, deslanted, at a 1000 em."""

    def __init__(self, path):
        self.file = str(path)
        if self.file.endswith(".ufo"):
            self.font = ufoLib2.Font.open(self.file)
            self.gs = self.font
            self.cmap = {u: g.name for g in self.font for u in g.unicodes}
            angle, upm = self.font.info.italicAngle or 0, self.font.info.unitsPerEm
            self._width = lambda n: self.font[n].width
        else:
            f = TTFont(self.file)
            self.gs = f.getGlyphSet()
            self.cmap = f.getBestCmap()
            angle, upm = f["post"].italicAngle, f["head"].unitsPerEm
            self._width = lambda n: self.gs[n].width
        self.scale = EM / upm
        self.slant = -math.tan(math.radians(angle))
        self._p = {}
        self.xh = self.path("x").bounds[3]
        self.cap = self.path("H").bounds[3]

    def has(self, ch):
        return ord(ch) in self.cmap

    def path(self, ch):
        if ch not in self._p:
            p = pathops.Path()
            s = self.scale
            gs = None if isinstance(self.gs, ufoLib2.Font) else self.gs
            pen = TransformPen(_Segments(p.getPen(), gs), (s, 0, -self.slant * s, s, 0, 0))
            name = self.cmap[ord(ch)]
            if isinstance(self.gs, ufoLib2.Font):
                r = DecomposingRecordingPen(self.gs)
                self.gs[name].draw(r)
                r.replay(pen)
            else:
                self.gs[name].draw(pen)
            self._p[ch] = pathops.simplify(p)
        return self._p[ch]

    def advance(self, ch):
        return self._width(self.cmap[ord(ch)]) * self.scale

    def zone(self, ch):
        return self.cap if ch.isupper() or ch.isdigit() else self.xh


class Raster:
    """A glyph rasterised at PX units a pixel, with its distance fields: of
    each white pixel to the ink (white) and of each ink pixel to the white
    (ink), in units, to the pixel's centre less half a pixel."""

    def __init__(self, path):
        x0, y0, x1, y1 = path.bounds
        margin = 2 * PX
        self.x0, self.y1 = x0 - margin, y1 + margin
        self.w = int((x1 - x0 + 2 * margin) / PX) + 2
        self.h = int((y1 - y0 + 2 * margin) / PX) + 2
        pen = _SkiaPen()
        path.draw(pen)
        surface = skia.Surface(self.w, self.h)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorTRANSPARENT)
        canvas.scale(1 / PX, -1 / PX)
        canvas.translate(-self.x0, -self.y1)
        canvas.drawPath(pen.path, skia.Paint(AntiAlias=False, Color=skia.ColorBLACK))
        self.ink = surface.makeImageSnapshot().toarray()[:, :, 3] > 127
        self.white_d = np.maximum(edt(self.ink) - 0.5, 0) * PX
        self.ink_d = np.maximum(edt(~self.ink) - 0.5, 0) * PX

    def xy(self, col, row):
        return self.x0 + col * PX, self.y1 - row * PX

    def cell(self, x, y):
        return int((x - self.x0) / PX), int((self.y1 - y) / PX)


def edt(feature):
    """Each pixel's Euclidean distance in pixels to the nearest feature pixel
    (exact: the distance down its column first, then the nearest over its row)."""
    h, w = feature.shape
    big = h + w
    idx = np.arange(h)[:, None]
    above = np.maximum.accumulate(np.where(feature, idx, -big), 0)
    below = np.minimum.accumulate(np.where(feature, idx, 2 * big)[::-1], 0)[::-1]
    g2 = np.minimum(idx - above, below - idx).astype(np.float32) ** 2
    j = np.arange(w, dtype=np.float32)
    dj2 = (j[:, None] - j[None, :]) ** 2
    out = np.empty((h, w), np.float32)
    step = max(1, 4_000_000 // (w * w))
    for r in range(0, h, step):
        out[r:r + step] = (g2[r:r + step, None, :] + dj2[None]).min(axis=2)
    return np.sqrt(out)


def _label(mask):
    """mask's 4-connected components as an int array (0: not in mask), by
    runs: each row's runs joined to the overlapping runs of the row above."""
    h, w = mask.shape
    parent = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    runs, prev = [], []
    for r in range(h):
        edges = np.flatnonzero(np.diff(np.concatenate(([0], mask[r].view(np.int8), [0]))))
        here = []
        for s0, s1 in zip(edges[::2], edges[1::2]):
            i = len(parent)
            parent.append(i)
            for p0, p1, j in prev:
                if p0 < s1 and s0 < p1:
                    a, b = find(i), find(j)
                    if a != b:
                        parent[max(a, b)] = min(a, b)
            here.append((s0, s1, i))
            runs.append((r, s0, s1, i))
        prev = here
    out = np.zeros((h, w), np.int32)
    for r, s0, s1, i in runs:
        out[r, s0:s1] = find(i) + 1
    return out


def _escapes(ras, mask, r):
    """Whether a disc of radius r passes from mask to the outside."""
    room = np.pad(ras.white_d >= r, 1, constant_values=True)  # beyond the raster all is open
    labels = _label(room)
    return bool((labels[1:-1, 1:-1][mask] == labels[0, 0]).any())


def _rays(ink):
    """For each pixel, in how many of eight directions (rows, columns and
    both diagonals, either way) ink lies."""
    h, w = ink.shape
    rows, cols = np.indices((h, w))

    def both(arr, axis):
        fwd = np.maximum.accumulate(arr, axis)
        back = np.flip(np.maximum.accumulate(np.flip(arr, axis), axis), axis)
        return fwd.astype(np.int8) + back

    count = both(ink, 0) + both(ink, 1)
    for j in (cols - rows + h - 1, cols + rows):  # the diagonals as columns of a skewed array
        skew = np.zeros((h, w + h - 1), bool)
        skew[rows, j] = ink
        count += both(skew, 0)[rows, j]
    return count


def counters(src, ch, ras):
    """[{area, width, aperture, x, y}] top to bottom, left to right.

    A counter is white that sees ink in at least ENCLOSED of eight
    directions (its median pixel does): an italic n's, open below, sees it
    in seven; the slot beside a serif, a v's crotch, the white under r's
    arm in five. Its width is the widest disc inside it, its aperture the
    widest that passes from it to the outside (0: closed)."""
    zone, ink = src.zone(ch), ras.ink
    seen = _rays(ink)
    inner = ~ink & (seen >= ENCLOSED)
    out = []
    labels = _label(inner)
    for k in np.unique(labels[labels > 0]):
        mask = labels == k
        if mask.sum() * PX * PX < MIN_COUNTER * zone * zone:
            continue
        width = 2 * float((np.maximum(edt(~mask) - 0.5, 0) * PX)[mask].max())
        if width < MIN_WIDTH * zone:
            continue
        aperture = 0.0
        if _escapes(ras, mask, 0):
            lo, hi = 0.0, float(ras.white_d[mask].max()) + PX
            while hi - lo > 0.25:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if _escapes(ras, mask, mid) else (lo, mid)
            aperture = 2 * lo
        rows, cols = np.nonzero(mask)
        x, y = ras.xy(cols.mean(), rows.mean())
        out.append({"area": round(float(mask.sum()) * PX * PX), "width": round(width, 1),
                    "aperture": round(aperture, 1), "x": round(x), "y": round(y),
                    "seen": float(np.median(seen[mask]))})
    out.sort(key=lambda c: (-round(c["y"] / (0.1 * zone)), c["x"]))
    return out


def stems(src, ch):
    """[(x0, x1)] of the straight stems, left to right: a run at one of
    STEM_AT whose edges stay within STEM_STRAIGHT of it, both a row (5 % of
    the zone) above and below, one of them over STEM_ROWS (the other may run
    into a bowl or a crotch there). Its width is taken at the first of
    STEM_AT that finds it."""
    rows = Rows(src.path(ch))
    zone = src.zone(ch)
    tol = STEM_STRAIGHT * zone
    out = []
    for at in STEM_AT:
        for a, b in rows.spans(zone * at / 20 + 0.37):
            if b - a > 0.45 * zone or any(a < d and c < b for c, d in out):
                continue
            left = right = True
            for k in STEM_ROWS:
                near = [r for r in rows.spans(zone * k / 20 + 0.37) if r[0] < b and r[1] > a]
                if len(near) != 1:
                    left = right = False
                    break
                ok_l, ok_r = abs(near[0][0] - a) <= tol, abs(near[0][1] - b) <= tol
                if abs(k - at) <= 1 and not (ok_l and ok_r):
                    left = right = False
                    break
                left, right = left and ok_l, right and ok_r
            if left or right:
                out.append((a, b))
    return sorted(out)


def joins(src, ch, found_stems):
    """{"0R top": height} for the char's joins (JOINS)."""
    cols = Rows(src.path(ch), swap=True)
    zone, out = src.zone(ch), {}
    for index, side, where in JOINS.get(ch, ()):
        if not found_stems or (index >= 0 and index >= len(found_stems)):
            continue
        a, b = found_stems[index]
        x = b + JOIN_OFFSET * (b - a) if side == "R" else a - JOIN_OFFSET * (b - a)
        runs = cols.spans(x + 0.37)
        runs = [r for r in runs if -0.1 * zone < (r[0] + r[1]) / 2 < 1.1 * zone]
        if not runs:
            continue
        if where == "top":
            r = max(runs, key=lambda r: r[1])
        elif where == "bottom":
            r = min(runs, key=lambda r: r[0])
        else:
            r = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - zone / 2))
        out[f"{index}{side} {where}"] = round(r[1] - r[0], 1)
    return out


def ball(src, ch, ras):
    """The ball's diameter: the widest disc of ink centred in its region."""
    if ch not in BALLS:
        return None
    x0, y0, x1, y1 = src.path(ch).bounds
    fx0, fx1, fy0, fy1 = BALLS[ch]
    c0, r0 = ras.cell(x0 + fx0 * (x1 - x0), y0 + fy1 * (y1 - y0))
    c1, r1 = ras.cell(x0 + fx1 * (x1 - x0), y0 + fy0 * (y1 - y0))
    region = ras.ink_d[r0:r1 + 1, c0:c1 + 1]
    return round(2 * float(region.max()), 1) if region.size and region.max() > 0 else None


def measure(src, ch):
    path = src.path(ch)
    if not path.bounds or path.bounds[2] <= path.bounds[0]:
        return None
    found = stems(src, ch)
    ras = Raster(path)
    cs = counters(src, ch, ras)
    m = {"advance": round(src.advance(ch)), "ink": round(path.bounds[2] - path.bounds[0]),
         "white": sum(c["area"] for c in cs), "counters": cs}
    if found:
        m["stem"] = round(found[0][1] - found[0][0], 1)
    if j := joins(src, ch, found):
        m["joins"] = j
    if (b := ball(src, ch, ras)) is not None:
        m["ball"] = b
    return m


def flat(m):
    """{measure name: value} of a character's measures, counters by place."""
    if not m:
        return {}
    out = {k: m[k] for k in ("advance", "ink", "stem", "white", "ball") if k in m}
    out["counters"] = len(m["counters"])
    for i, c in enumerate(m["counters"], 1):
        out[f"counter{i} area"] = c["area"]
        out[f"counter{i} width"] = c["width"]
        if c["aperture"]:
            out[f"counter{i} aperture"] = c["aperture"]
    for k, v in m.get("joins", {}).items():
        out[f"join {k}"] = v
    return out


def run(pairs, chars):
    """{pair name: {"regular"/"bold": {char: measures}}} for the pairs found."""
    data = {}
    for name, regular, bold in pairs:
        paths = []
        for p in (regular, bold):
            path = ROOT / p if p.endswith(".ufo") else REFDIR / f"{p}.ttf"
            paths.append(path if path.exists() else None)
        if None in paths:
            print(f"{name}: {regular} or {bold} missing (fetch_refs.py), left out", file=sys.stderr)
            continue
        entry = {}
        for weight, path in zip(("regular", "bold"), paths):
            src = Source(path)
            entry[weight] = {"file": str(path.relative_to(ROOT)), "xHeight": round(src.xh),
                             "capHeight": round(src.cap),
                             "chars": {c: measure(src, c) for c in chars if src.has(c)}}
        data[name] = entry
    return data


def gains(data):
    """{pair: {char: {measure: (regular, bold, gain)}}}; a counter's measures
    only where both weights have as many counters."""
    out = {}
    for pair, entry in data.items():
        out[pair] = {}
        reg, bold = entry["regular"]["chars"], entry["bold"]["chars"]
        for ch in reg:
            if ch not in bold or not reg[ch] or not bold[ch]:
                continue
            same = len(reg[ch]["counters"]) == len(bold[ch]["counters"])
            r, b = flat(reg[ch]), flat(bold[ch])
            row = {}
            for k in r:
                if k not in b:
                    continue
                if k == "counters":
                    row[k] = (r[k], b[k], None)
                elif same or not (k.startswith("counter") or k == "white"):
                    row[k] = (r[k], b[k], round(b[k] / r[k], 3) if r[k] else None)
            out[pair][ch] = row
    return out


def family_summary(g):
    """{family: {measure kind: {pair: median gain}}}."""
    out = {}
    for family, chars in FAMILIES.items():
        rows = {}
        for pair, by_char in g.items():
            kinds = {}
            for ch in chars:
                for k, (_, _, gain) in by_char.get(ch, {}).items():
                    if gain is None:
                        continue
                    kind = ("counter " + k.split()[1]) if k.startswith("counter") \
                        else "join" if k.startswith("join") else k
                    kinds.setdefault(kind, []).append(gain)
            for kind, vals in kinds.items():
                rows.setdefault(kind, {})[pair] = (round(statistics.median(vals), 3), len(vals))
        out[family] = rows
    return out


def report(data, g, summary):
    pairs = list(g)
    refs = [p for p in pairs if p != "Myia"]
    lines = ["# What the Bold gains over the Regular", "",
             ("Units of a 1000 em, outlines deslanted. Gain: bold over regular. "
              "Myia/ref: Myia's gain over the reference's (above 1: Myia's Bold gains more)."), ""]
    for pair, entry in data.items():
        lines.append(f"- {pair}: {entry['regular']['file']} | {entry['bold']['file']} "
                     f"(x-height {entry['regular']['xHeight']} | {entry['bold']['xHeight']})")
    lines += ["", "## By family (median gain, n)", ""]
    head = "| family | measure | " + " | ".join(pairs) + "".join(f" | Myia/{r}" for r in refs) + " |"
    lines += [head, "|" + "---|" * (2 + len(pairs) + len(refs))]
    for family, rows in summary.items():
        for kind, by_pair in rows.items():
            cells = [f"{by_pair[p][0]:.3f} ({by_pair[p][1]})" if p in by_pair else "" for p in pairs]
            rel = []
            for r in refs:
                if "Myia" in by_pair and r in by_pair and by_pair[r][0]:
                    rel.append(f"{by_pair['Myia'][0] / by_pair[r][0]:.3f}")
                else:
                    rel.append("")
            lines.append(f"| {family} | {kind} | " + " | ".join(cells + rel) + " |")
    lines += ["", "## By character", ""]
    head = "| char | measure | " + " | ".join(f"{p} R | {p} B | {p} gain" for p in pairs) + " |"
    lines += [head, "|" + "---|" * (2 + 3 * len(pairs))]
    chars = list(g.get("Myia", {})) or list(next(iter(g.values()), {}))
    for ch in chars:
        kinds = list(g["Myia"].get(ch, {})) if "Myia" in g else []
        for p in refs:
            kinds += [k for k in g[p].get(ch, {}) if k not in kinds]
        for k in kinds:
            cells = []
            for p in pairs:
                v = g[p].get(ch, {}).get(k)
                cells += [f"{v[0]:g}", f"{v[1]:g}", f"{v[2]:.3f}" if v[2] is not None else ""] if v else ["", "", ""]
            lines.append(f"| {ch} | {k} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--italic", action="store_true", help="the Italic and Bold Italic (phase 8)")
    ap.add_argument("--range", action="store_true", help="Bodoni Moda and Libre Bodoni beside Old Standard")
    ap.add_argument("--chars", help="the characters to measure (default: the core set's letters and figures)")
    ap.add_argument("--out", help="the Markdown table (default build/quality/bold-measures[-italic].md)")
    ap.add_argument("--json", help="every measure (default beside --out, .json)")
    args = ap.parse_args()
    pairs = PAIRS[args.italic]
    if not args.italic and not args.range:
        pairs = pairs[:2]
    chars = args.chars or CORE
    stem = "bold-measures-italic" if args.italic else "bold-measures"
    out = Path(args.out) if args.out else OUT / f"{stem}.md"
    js = Path(args.json) if args.json else out.with_suffix(".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = run(pairs, chars)
    g = gains(data)
    summary = family_summary(g)
    js.write_text(json.dumps({"measures": data, "summary": summary}, ensure_ascii=False, indent=1) + "\n")
    out.write_text(report(data, g, summary))
    print(f"{out}\n{js}", file=sys.stderr)


if __name__ == "__main__":
    main()
