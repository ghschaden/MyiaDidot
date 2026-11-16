"""The Italic against the Regular, beside the references' own pairs (phase 6).

    python scripts/quality/italic_measures.py [--out build/quality/italic-targets.md]
        [--json build/quality/italic-measures.json] [--marks DIR]

docs/claude/italic.md is the specification: where does the Italic read as
another typeface beside the Regular? Each pair is a roman and its italic:
Myia's from the UFOs (sources/, no build needed), the references' from
build/refs/ (fetch_refs.py). Outlines are deslanted by the font's italic
angle and scaled to a 1000 em (bold_measures.Source); every value is then
put on the style's own scale: a thickness over its stem (the lowercase's
or the capitals', taken a third of the way up), a size (a width, a
counter, a serif's or a hook's reach) over its zone, the ball over the
stem it is read against. The x-height is x's top: in a roman the flat
letters' height, in an italic the height all its lowercase shares (x z o
n u v reach one line there), so the rounds' overshoot above is no measure
of an italic; "x-height I / R" says where that line lies against the
roman's flat letters.

  relation   both styles have the feature: the Italic's own-scale value
             over the Regular's. Myia's against the range of the three
             Didones' relations (Old Standard, Bodoni Moda, Libre Bodoni).
  own        the Regular has no counterpart (hooks): the Italic's value
             against the three Didone italics' directly.
  diff       a difference Italic less Regular, in the measure's own unit
             (degrees of stress, per cent of the zone for overshoots).

The gate (GATE below, italic.md): outside the range by OUTSIDE or more is
a candidate; a candidate with Libertinus and Charis both on the range's
side of Myia, or one outside by FAR or more, reads as another typeface. A
measure whose three references spread by more than SPREAD of their median
does not discriminate and is shown only. The capitals' contrast is kept
(declined twice) and never on the change list.

A stroke's thickness is taken across it: the ink's run in a column (or a
row), times the cosine of the stroke's lean there, the lean read from the
run's middle a little to either side (across()). --marks writes one PNG
per font and style with every measured place drawn on the letters: to be
looked at before a number is believed.

The tools find candidates; the designer's eye decides.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bold_measures as bm  # noqa: E402
from common import OUT, REFDIR, ROOT  # noqa: E402

OUTSIDE = 0.03  # past the range: a candidate
FAR = 0.10  # past the range: another typeface, whatever the second voice says
SPREAD = 0.30  # the three references' range over their median: beyond it shown only
STRESS = 5.0  # degrees past the range
OVERSHOOT = 0.5  # per cent of the zone past the range
KEPT = "kept: declined 2026-10-21 and 2026-11-02"

# name, roman, italic, part: "range" (the Didones), "voice" (the second
# voice), "shown"
PAIRS = [
    ("Myia", "sources/MyiaDidot-Regular.ufo", "sources/MyiaDidot-Italic.ufo", "myia"),
    ("Old Standard", "OldStandard-Regular.ttf", "OldStandard-Italic.ttf", "range"),
    ("Bodoni Moda", "BodoniModa-11-Regular.ttf", "BodoniModa-11-Italic.ttf", "range"),
    ("Libre Bodoni", "LibreBodoni-Regular.ttf", "LibreBodoni-Italic.ttf", "range"),
    ("Libertinus", "LibertinusSerif-Regular.otf", "LibertinusSerif-Italic.otf", "voice"),
    ("Charis", "CharisSIL-Regular.ttf", "CharisSIL-Italic.ttf", "voice"),
    ("EB Garamond", "EBGaramond-Regular.ttf", "EBGaramond-Italic.ttf", "shown"),
]
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
STEMS = {"lc": "ilnmhu", "uc": "HIEL"}
# the stems that leave the x-height, each over the x-height letters' stem
# (an italic's may be drawn lighter: Old Standard's are, the Bodonis' not)
LONG = "lbdhkftpq"
# a and g are not among the balls: single-storey in an italic, their
# regions (bold_measures.BALLS) hold a bowl's top or a stem there
BALLS = "cfryj"
# the letters drawn by --marks
SHOWN = "nioecvfryjgpqlubdhktHIELOAxz"


class Cut:
    """A character's outline cut into rows and columns, with the places
    measured on it (marks: segments in the outline's units)."""

    def __init__(self, src, ch):
        self.path = src.path(ch)
        self.rows = bm.Rows(self.path, steps=24)
        self.cols = bm.Rows(self.path, swap=True, steps=24)
        self.x0, self.y0, self.x1, self.y1 = self.path.bounds
        self.zone = src.zone(ch)
        self.marks = []

    def row(self, y):
        return self.rows.spans(y + 0.37)

    def col(self, x):
        return self.cols.spans(x + 0.37)

    def mark(self, x0, y0, x1, y1):
        self.marks.append((x0, y0, x1, y1))


def cut(src, ch):
    cache = src.__dict__.setdefault("_cuts", {})
    if ch not in cache:
        cache[ch] = Cut(src, ch) if src.has(ch) and src.path(ch).bounds else None
    return cache[ch]


def _near(spans, run):
    """The span whose middle lies nearest run's, if it overlaps it."""
    mid = (run[0] + run[1]) / 2
    got = [s for s in spans if s[0] < run[1] and s[1] > run[0]]
    return min(got, key=lambda s: abs((s[0] + s[1]) / 2 - mid)) if got else None


def across(spans_at, at, pick, d=2.0, strict=False):
    """(thickness, run) of the stroke pick() chooses among the spans at
    `at`: the run's length times the cosine of the stroke's lean, read from
    the run's middle d to either side. spans_at: Cut.row or Cut.col.
    Where the run to one side is another stroke (half as long again, or
    half as short: the arch running into its stem, a step) there is no
    lean to read: the run as cut, or with strict nothing."""
    here = pick(spans_at(at))
    if here is None:
        return None, None
    lo, hi = _near(spans_at(at - d), here), _near(spans_at(at + d), here)
    size = here[1] - here[0]
    if lo is None or hi is None or any(abs((r[1] - r[0]) - size) > 0.5 * size for r in (lo, hi)):
        return (None, None) if strict else (size, here)
    lean = ((hi[0] + hi[1]) - (lo[0] + lo[1])) / 2 / (2 * d)
    return (here[1] - here[0]) / math.hypot(1, lean), here


def stem_runs(c):
    """The stems' runs a third of the way up the zone, left to right: the
    runs at least 0.6 of the widest (a hook's or a serif's hairline is
    not one)."""
    runs = [r for r in c.row(c.zone / 3) if r[1] - r[0] < 0.45 * c.zone]
    if not runs:
        return []
    widest = max(b - a for a, b in runs)
    return [r for r in runs if r[1] - r[0] >= 0.6 * widest]


def stem(c, index=0):
    """A stem's thickness a third of the way up."""
    runs = stem_runs(c)
    if not runs:
        return None
    t, run = across(c.row, c.zone / 3, lambda s: _near(s, runs[index]))
    if t is not None:
        c.mark(run[0], c.zone / 3, run[1], c.zone / 3)
    return t


def long_stem(c):
    """The stem of a letter with an ascender or a descender, where it
    stands alone: halfway between the x-height and the letter's top (b d
    h k), halfway down the descender (p q); the widest run there. A letter
    whose stem is free a third of the way up (l t f) is measured by stem."""
    y = (c.zone + c.y1) / 2 if c.y1 - c.zone > -c.y0 else c.y0 / 2
    runs = [r for r in c.row(y) if r[1] - r[0] < 0.45 * c.zone]
    if not runs:
        return None
    widest = max(runs, key=lambda r: r[1] - r[0])
    t, run = across(c.row, y, lambda s: _near(s, widest), strict=True)
    if t is not None:
        c.mark(run[0], y, run[1], y)
    return t


def _thinnest(c, places, spans_at, pick, cols=True):
    """The least thickness across a stroke over places, and where its thin
    part lies: the mean of the places within a tenth of the least."""
    got = []
    for at in places:
        t, run = across(spans_at, at, pick, strict=True)
        if t is not None:
            got.append((t, at, run))
    if not got:
        return None, None
    least = min(g[0] for g in got)
    thin = [g for g in got if g[0] <= 1.1 * least]
    at = statistics.mean(g[1] for g in thin)
    mid = statistics.mean((g[2][0] + g[2][1]) / 2 for g in thin)
    t, at0, run = min(got)
    if cols:
        c.mark(at0, run[0], at0, run[1])
    else:
        c.mark(run[0], at0, run[1], at0)
    return least, ((at, mid) if cols else (mid, at))


def ring(c):
    """{top, bottom, stress} of a round letter: its stroke where thinnest
    above and below, and the angle from the vertical of the line through
    the two thin places (positive: the upper one to the right)."""
    w = c.x1 - c.x0
    xs = np.linspace(c.x0 + 0.25 * w, c.x1 - 0.25 * w, 41)
    top, where_t = _thinnest(c, xs, c.col, lambda s: s[-1] if len(s) >= 2 else None)
    bottom, where_b = _thinnest(c, xs, c.col, lambda s: s[0] if len(s) >= 2 else None)
    if top is None or bottom is None:
        return {}
    stress = math.degrees(math.atan2(where_t[0] - where_b[0], where_t[1] - where_b[1]))
    return {"top": top, "bottom": bottom, "stress": stress}


def e_bar(c):
    """e's bar: the middle one of three runs, where thinnest."""
    w = c.x1 - c.x0
    xs = np.linspace(c.x0 + 0.35 * w, c.x1 - 0.35 * w, 15)
    return _thinnest(c, xs, c.col, lambda s: s[1] if len(s) == 3 else None)[0]


def arch(c):
    """n's arch where thinnest between its stems."""
    runs = stem_runs(c)
    if len(runs) < 2:
        return None
    a, b = runs[0][1], runs[-1][0]
    xs = np.linspace(a + 6, a + 0.6 * (b - a), 25)

    def upper(spans):
        return spans[-1] if spans and (spans[-1][0] + spans[-1][1]) / 2 > 0.3 * c.zone else None

    return _thinnest(c, xs, c.col, upper)[0]


def thin_stroke(c, at):
    """The thinner of two strokes in the row at `at` of the zone (v, A)."""
    def thinner(spans):
        return min(spans, key=lambda s: s[1] - s[0]) if len(spans) == 2 else None

    t, run = across(c.row, at * c.zone, thinner)
    if t is not None:
        c.mark(run[0], at * c.zone, run[1], at * c.zone)
    return t


def bar(c):
    """H's bar, in the column midway between its stems."""
    runs = stem_runs(c)
    if len(runs) < 2:
        return None
    x = (runs[0][1] + runs[-1][0]) / 2
    t, run = across(c.col, x, lambda s: min(s, key=lambda r: abs((r[0] + r[1]) / 2 - c.zone / 2)) if s else None)
    if t is not None:
        c.mark(x, run[0], x, run[1])
    return t


def colour(c, src, ch):
    """Ink between the baseline and the x-height over advance x x-height."""
    n = 60
    ink = sum(b - a for i in range(n) for a, b in c.row(src.xh * (i + 0.5) / n)) * src.xh / n
    return ink / (src.advance(ch) * src.xh)


def foot(c, index=0):
    """{L, R, tip, half} of the serif at a stem's lower end: its reach past
    the stem's edges in the row just above the glyph's lowest point; its
    thickness (the ink's run up from there) near the left tip and at half
    the left reach."""
    runs = stem_runs(c)
    if not runs:
        return {}
    s = runs[index]
    base = min((r[0] for x in (s[0] + 1, (s[0] + s[1]) / 2, s[1] - 1) for r in c.col(x)), default=None)
    if base is None:
        return {}
    span = _near(c.row(base + 2), s)
    if span is None:
        return {}
    out = {"L": s[0] - span[0], "R": span[1] - s[1]}
    c.mark(span[0], base + 2, span[1], base + 2)
    if out["L"] > 6:
        for name, x in (("tip", span[0] + max(3, 0.1 * out["L"])), ("half", s[0] - out["L"] / 2)):
            low = [r for r in c.col(x) if r[0] < base + 4]
            if low:
                out[name] = low[0][1] - low[0][0]
                c.mark(x, low[0][0], x, low[0][1])
    return out


def head(c):
    """l's head: how far the ink reaches left of the stem in the top fifth."""
    runs = stem_runs(c)
    if not runs:
        return None
    ys = np.linspace(c.y1 - 0.2 * (c.y1 - c.y0), c.y1 - 1, 20)
    got = [(s[0][0], y) for y in ys if (s := c.row(y))]
    if not got:
        return None
    x, y = min(got)
    c.mark(x, y, runs[0][0], y)
    return runs[0][0] - x


def hook(c, end):
    """{reach, thin} of an entry ("entry": top left of the first stem) or
    exit ("exit": bottom right of the last): how far the ink reaches past
    the stem's edge, and the hook's stroke where thinnest."""
    runs = stem_runs(c)
    if not runs:
        return {}
    if end == "entry":
        edge = runs[0][0]
        ys = np.linspace(0.7 * c.zone, min(c.y1, 1.1 * c.zone) - 1, 20)
        got = [(s[0][0], y) for y in ys if (s := c.row(y))]
        if not got:
            return {}
        x, y = min(got)
        reach, lo, hi = edge - x, x, edge
    else:
        edge = runs[-1][1]
        ys = np.linspace(max(c.y0, -0.05 * c.zone) + 1, 0.45 * c.zone, 20)
        got = [(s[-1][1], y) for y in ys if (s := c.row(y))]
        if not got:
            return {}
        x, y = max(got)
        reach, lo, hi = x - edge, edge, x
    c.mark(min(x, edge), y, max(x, edge), y)
    out = {"reach": reach}
    if reach > 8:
        def strip(spans):
            side = [r for r in spans if ((r[0] + r[1]) / 2 > 0.5 * c.zone) == (end == "entry")]
            return (side[-1] if end == "entry" else side[0]) if side else None

        xs = np.linspace(lo + 0.15 * reach, hi - 0.15 * reach, 15)
        thin = _thinnest(c, xs, c.col, strip)[0]
        if thin is not None:
            out["thin"] = thin
    return out


def lean(c):
    """What lean the first stem keeps after deslanting, in degrees."""
    runs = stem_runs(c)
    if not runs:
        return None
    lo, hi = _near(c.row(0.25 * c.zone), runs[0]), _near(c.row(0.6 * c.zone), runs[0])
    if lo is None or hi is None:
        return None
    return math.degrees(math.atan2((hi[0] + hi[1]) / 2 - (lo[0] + lo[1]) / 2, 0.35 * c.zone))


def measure(src):
    """{name: (value on the style's own scale, raw)} for one style."""
    m = {}

    def put(name, raw, over):
        if raw is not None and over:
            m[name] = (raw / over, round(raw, 2))

    def C(ch):
        return cut(src, ch)

    xh, cap = src.xh, src.cap
    widths = {k: [w for ch in chars if C(ch) and (w := stem(C(ch))) is not None] for k, chars in STEMS.items()}
    lc = statistics.median(widths["lc"]) if widths["lc"] else None
    uc = statistics.median(widths["uc"]) if widths["uc"] else None
    put("stem lc / x-height", lc, xh)
    put("stem uc / cap height", uc, cap)

    for ch in LONG:
        if C(ch):
            put(f"long stem {ch} / stem", stem(C(ch)) if ch in "ltf" else long_stem(C(ch)), lc)

    o, O = (ring(C(ch)) if C(ch) else {} for ch in "oO")
    hair = o.get("top")
    put("hairline o top / stem", o.get("top"), lc)
    put("hairline o bottom / stem", o.get("bottom"), lc)
    put("hairline e bar / stem", C("e") and e_bar(C("e")), lc)
    put("hairline n arch / stem", C("n") and arch(C("n")), lc)
    put("hairline v thin / stem", C("v") and thin_stroke(C("v"), 0.5), lc)
    hbar = C("H") and bar(C("H"))
    put("capital hairline H bar / stem", hbar, uc)
    put("capital hairline O top / stem", O.get("top"), uc)
    put("capital hairline A thin / stem", C("A") and thin_stroke(C("A"), 0.65), uc)

    each = {ch: colour(C(ch), src, ch) for ch in LOWER if C(ch)}
    if each:
        ink = sum(v * src.advance(ch) for ch, v in each.items())
        m["colour a-z"] = (ink / sum(src.advance(ch) for ch in each), None)
        for ch, v in each.items():
            m[f"colour {ch}"] = (v, None)
    put("width a-z / x-height", sum(src.advance(ch) for ch in LOWER if src.has(ch)) / 26, xh)
    for ch in "noea":
        put(f"width {ch} / x-height", src.advance(ch), xh)
    put("width A-Z / cap height", sum(src.advance(ch) for ch in UPPER if src.has(ch)) / 26, cap)
    for ch in "HO":
        put(f"width {ch} / cap height", src.advance(ch), cap)

    for ch in "noebdpq" + BALLS:
        if not C(ch):
            continue
        ras = bm.Raster(src.path(ch))
        if ch in "noebdpq":
            found = bm.counters(src, ch, ras)
            if found:
                put(f"counter {ch} / x-height", max(found, key=lambda k: k["area"])["width"], xh)
        else:
            put(f"ball {ch} / stem", bm.ball(src, ch, ras), lc)

    for ch, sides in (("H", "LR"), ("I", "LR"), ("E", "L"), ("L", "L")):
        f = foot(C(ch)) if C(ch) else {}
        for side in sides:
            put(f"serif {ch} reach {side} / cap height", f.get(side), cap)
        if ch in "HI":
            put(f"serif {ch} tip / hairline", f.get("tip"), hbar)
            put(f"serif {ch} half / hairline", f.get("half"), hbar)
    for ch, index in (("p", 0), ("q", -1)):
        f = foot(C(ch), index) if C(ch) else {}
        for side in "LR":
            put(f"foot {ch} reach {side} / x-height", f.get(side), xh)
        put(f"foot {ch} tip / hairline", f.get("tip"), hair)
    put("head l reach / x-height", C("l") and head(C("l")), xh)

    for ch, ends in (("n", ("entry", "exit")), ("i", ("entry", "exit")), ("u", ("exit",))):
        for end in ends:
            h = hook(C(ch), end) if C(ch) else {}
            put(f"hook {ch} {end} reach / x-height", h.get("reach"), xh)
            put(f"hook {ch} {end} thin / stem", h.get("thin"), lc)

    m["x-height I / R"] = (xh, None)  # judge() puts the Italic's over the Regular's
    if C("o"):
        m["overshoot o bottom % x-height"] = (100 * -C("o").y0 / xh, None)
    if C("O"):
        m["overshoot O top % cap height"] = (100 * (C("O").y1 - cap) / cap, None)
        m["overshoot O bottom % cap height"] = (100 * -C("O").y0 / cap, None)
    for ch in "bdl":
        if C(ch):
            put(f"ascender {ch} / cap height", C(ch).y1, cap)
    for ch, r in (("o", o), ("O", O)):
        if "stress" in r:
            m[f"stress {ch} degrees"] = (r["stress"], None)
    m["italic angle degrees"] = (math.degrees(math.atan(src.slant)), None)
    for ch in "nHl":
        if C(ch) and (v := lean(C(ch))) is not None:
            m[f"lean left after deslanting {ch} degrees"] = (v, None)
    return m


def kind(name):
    if name.startswith(("hook", "head")):
        return "own"
    if name.startswith(("stress", "overshoot")):
        return "diff"
    if name.startswith(("italic angle", "lean")):
        return "shown"
    return "relation"


def run(pairs=PAIRS, marks=None):
    data = {}
    for name, roman, italic, part in pairs:
        paths = [ROOT / p if p.endswith(".ufo") else REFDIR / p for p in (roman, italic)]
        if missing := [p.name for p in paths if not p.exists()]:
            print(f"{name}: {', '.join(missing)} missing (fetch_refs.py), left out", file=sys.stderr)
            continue
        entry = {"part": part}
        for style, path in zip(("regular", "italic"), paths):
            src = bm.Source(path)
            entry[style] = {k: v for k, v in measure(src).items()}
            if marks:
                draw_marks(src, Path(marks) / f"{name.replace(' ', '')}-{style}.png")
        data[name] = entry
    return data


def draw_marks(src, out):
    """The letters measured, deslanted, with every measured place in red."""
    import skia

    chars = [ch for ch in SHOWN if cut(src, ch)]
    cell, per_row, k = 420, 7, 0.3
    rows = -(-len(chars) // per_row)
    surface = skia.Surface(cell * per_row, cell * rows)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorWHITE)
    grey = skia.Paint(AntiAlias=True, Color=skia.Color(150, 150, 150))
    red = skia.Paint(AntiAlias=True, Color=skia.Color(220, 0, 0), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
    for i, ch in enumerate(chars):
        c = cut(src, ch)
        canvas.save()
        canvas.translate(cell * (i % per_row) + 80, cell * (i // per_row) + 300)
        canvas.scale(k, -k)
        pen = bm._SkiaPen()
        c.path.draw(pen)
        canvas.drawPath(pen.path, grey)
        for x0, y0, x1, y1 in c.marks:
            canvas.drawLine(x0, y0, x1, y1, red)
        canvas.restore()
    out.parent.mkdir(parents=True, exist_ok=True)
    surface.makeImageSnapshot().save(str(out), skia.kPNG)


def position(value, refs):
    """bold_targets': 0 inside, +0.06 six per cent above the highest."""
    lo, hi = min(refs), max(refs)
    if lo <= value <= hi or lo <= 0:
        return 0.0
    return value / lo - 1 if value < lo else value / hi - 1


def past(value, refs):
    """How far past the range, in the measure's own unit (diff)."""
    lo, hi = min(refs), max(refs)
    return 0.0 if lo <= value <= hi else value - (lo if value < lo else hi)


def judge(data):
    """[{name, kind, myia, refs, voice, shown, pos, spread, verdict, ...}]
    for every measure all three Didones and Myia have."""
    fonts = {part: [n for n, e in data.items() if e["part"] == part] for part in ("myia", "range", "voice", "shown")}
    mine = fonts["myia"][0]
    rows = []
    for name in data[mine]["italic"]:
        k = kind(name)

        def value(font, name=name, k=k):
            e = data[font]
            if name not in e["italic"] or (k != "own" and name not in e["regular"]):
                return None
            it = e["italic"][name][0]
            if k in ("own", "shown"):
                return it
            reg = e["regular"][name][0]
            if k == "diff":
                return it - reg
            return it / reg if reg else None

        v = value(mine)
        refs = [value(f) for f in fonts["range"]]
        if v is None or None in refs or len(refs) < 3:
            continue
        voice = [value(f) for f in fonts["voice"]]
        row = {"name": name, "kind": k, "myia": v, "refs": dict(zip(fonts["range"], refs)),
               "voice": dict(zip(fonts["voice"], voice)),
               "shown": {f: value(f) for f in fonts["shown"]},
               "own": {f: (data[f]["regular"].get(name, (None,))[0], data[f]["italic"][name][0])
                       for f in (mine, fonts["range"][0])}}
        if k == "shown":
            row.update(pos=0.0, spread=None, verdict="shown")
        elif k == "diff":
            limit = STRESS if name.startswith("stress") else OVERSHOOT
            row["pos"] = past(v, refs)
            row["spread"] = None
            row["verdict"] = "another typeface" if abs(row["pos"]) >= limit else "inside"
        else:
            row["pos"] = position(v, refs)
            med = statistics.median(refs)
            row["spread"] = (max(refs) - min(refs)) / abs(med) if med else None
            away = abs(row["pos"])
            sided = len(voice) == 2 and None not in voice and (
                all(x < v for x in voice) if row["pos"] > 0 else all(x > v for x in voice))
            if row["spread"] is None or row["spread"] > SPREAD:
                row["verdict"] = "shown: the references spread"
            elif away < OUTSIDE:
                row["verdict"] = "inside"
            elif away >= FAR or sided:
                row["verdict"] = "another typeface"
            else:
                row["verdict"] = "candidate"
        if name.startswith("capital hairline"):
            row["verdict"] = KEPT
        rows.append(row)
    return rows


def report(data, rows):
    def f(x, k):
        return "" if x is None else f"{x:+.1f}" if k == "diff" else f"{x:.3f}"

    order = {"another typeface": 0, "candidate": 1, KEPT: 2, "inside": 3, "shown: the references spread": 4,
             "shown": 5}
    lines = ["# The Italic against the Regular", "",
             ("From scripts/quality/italic_measures.py (docs/claude/italic.md). Relation: the Italic's "
             "own-scale value over the Regular's; own: the Italic's value itself; diff: Italic less "
             "Regular. pos: Myia past the three Didones' range, in per cent (diff: in the measure's "
             "unit); spread: the Didones' range over their median, per cent. R/OS, I/OS: Myia's Regular "
             "and Italic over Old Standard's, own scale, per cent."), ""]
    refs = list(rows[0]["refs"]) if rows else []
    voice = list(rows[0]["voice"]) if rows else []
    shown = list(rows[0]["shown"]) if rows else []
    lines += ["| measure | kind | Myia R | Myia I | Myia | " + " | ".join(refs) + " | pos | spread | "
              + " | ".join(voice + shown) + " | R/OS | I/OS | verdict |",
              "|---|---|---|---|---|" + "---|" * (len(refs) + 2 + len(voice) + len(shown) + 3)]
    letters = []
    for r in sorted(rows, key=lambda r: order[r["verdict"]]):
        if r["name"].startswith("colour ") and r["name"] != "colour a-z":
            letters.append(r)
            continue
        k = r["kind"]
        (mr, mi), (osr, osi) = r["own"].values()
        pos = "" if k == "shown" else f"{r['pos']:+.1f}" if k == "diff" else f"{100 * r['pos']:+.0f}"
        rel = [f"{100 * (a / b - 1):+.0f}" if a is not None and b and k in ("relation", "own") else ""
               for a, b in ((mr, osr), (mi, osi))]
        lines.append(
            f"| {r['name']} | {k} | {f(mr, 'r')} | {f(mi, 'r')} | {f(r['myia'], k)} | "
            + " | ".join(f(r["refs"][x], k) for x in refs)
            + f" | {pos} | {'' if r['spread'] is None else round(100 * r['spread'])} | "
            + " | ".join(f({**r["voice"], **r["shown"]}[x], k) for x in voice + shown)
            + f" | {rel[0]} | {rel[1]} | {r['verdict']} |")
    out = [r for r in letters if r["verdict"] in ("candidate", "another typeface")]
    lines += ["", "Colour letter by letter, those outside (relation, pos in per cent): "
              + (", ".join(f"{r['name'][-1]} {r['myia']:.2f} ({100 * r['pos']:+.0f})" for r in out) or "none") + "."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", help="the table (default build/quality/italic-targets.md)")
    ap.add_argument("--json", help="every measure (default build/quality/italic-measures.json)")
    ap.add_argument("--marks", help="a directory for the letters with the measured places drawn")
    args = ap.parse_args()
    out = Path(args.out) if args.out else OUT / "italic-targets.md"
    js = Path(args.json) if args.json else OUT / "italic-measures.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = run(marks=args.marks)
    rows = judge(data)
    js.write_text(json.dumps({"measures": data, "verdicts": rows}, ensure_ascii=False, indent=1) + "\n")
    out.write_text(report(data, rows))
    print(f"{out}\n{js}", file=sys.stderr)


if __name__ == "__main__":
    main()
