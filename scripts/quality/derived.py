"""Derived glyphs against the letters they are made from.

    python scripts/quality/derived.py UFO [GLYPH ...] [--all]

derive.py's recipes name each derived letter's base and what is done to it
(a hook replacing a stem's end, a bar across, a tail added, the letter
turned or mirrored). What the recipe does not touch must be the base's ink
as it is. The glyph and its base (turned or mirrored as the recipe says)
are sliced into rows, upright (an italic deslanted), and every ink span of
the base is looked for in the glyph, the base shifted by the offset most
rows agree on:

  exact      both edges within TOL of a span of the glyph
  covered    inside a wider span (a bar or slash running through it)
  lost       neither: the glyph differs there

The findings (kinds for checks.py):

  base     less than KEPT of the base's ink kept (exact or covered): the
           glyph is not (or no longer) its base with something done to it
  stem     the base's widest span at mid height (its stem, a bowl's side)
           heavier or lighter in the glyph by more than STEM_OFF
  advance  an advance off whole units
  style    (italics) closer to the Regular's glyph than to its own base, by
           STYLE_MARGIN of overlap: made from the roman, not the italic.
           Multi-input attachments also compare their same-style recipe.

Only glyphs that are still the recipe's work are checked: in the Italic
and Bold Italic those whose org.myiadidot.italicSource is "derived".

--json PATH writes the measures and findings for other tools, each glyph
and base with a hash of its outline, so that a stale report can be told.
The recipe is the one the check reads: derive.py's, or the Italic's; the
Bold Italic's own (ITALIC_BOLD_RECIPES) are not among them.
"""

import collections
import hashlib
import json
import math
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TOL = 6  # units an edge may move and still be the base's
KEPT = 0.6  # least share of the base's ink a derived glyph keeps
STEM_OFF = (8, 0.06)  # a stem off by more than this many units and this share
STYLE_MARGIN = 0.1
STEP = 10  # row spacing
# ops whose glyph keeps the base's outline, but for what they add or cut
KEEPS = {"hook", "tail", "bar", "slash", "midtilde", "lines", "attach", "graft", "curl",
         "descend", "twin", "nodot", "stem", "unserif"}
TRANSFORMS = {"turn", "mirror", "flip"}
SOURCE_KEY = "org.myiadidot.italicSource"


def _flatten(rec, steps=12):
    """Polygons from a recording (cubic and quadratic curves cut into lines)."""
    polys, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op in ("curveTo", "qCurveTo"):
            p0 = cur[-1]
            if op == "curveTo" and len(args) == 3:
                p1, p2, p3 = args
                for i in range(1, steps + 1):
                    t = i / steps
                    u = 1 - t
                    cur.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k]
                                     + t ** 3 * p3[k] for k in (0, 1)))
            else:  # pathops gives single quadratics, if any
                p1, p2 = args[-2], args[-1]
                for i in range(1, steps + 1):
                    t = i / steps
                    u = 1 - t
                    cur.append(tuple(u * u * p0[k] + 2 * u * t * p1[k] + t * t * p2[k] for k in (0, 1)))
        elif op in ("closePath", "endPath"):
            if cur:
                polys.append(cur)
            cur = []
    return polys


class Outline:
    """A glyph's ink, merged, as polygons: sliced into rows on demand."""

    def __init__(self, font, name, transform=(1, 0, 0, 1, 0, 0), path=None):
        p = pathops.Path()
        if path is None:
            r = DecomposingRecordingPen(font)
            font[name].draw(r)
            r.replay(TransformPen(p.getPen(), transform))
        else:  # a pathops.Path given instead of a glyph
            path.draw(TransformPen(p.getPen(), transform))
        p = pathops.simplify(p)
        rec = RecordingPen()
        p.draw(rec)
        self.polys = _flatten(rec)
        self.bounds = None if not self.polys else p.bounds
        self.area = abs(p.area) if self.polys else 0

    def spans(self, y):
        xs = []
        for poly in self.polys:
            n = len(poly)
            for i in range(n):
                (x0, y0), (x1, y1) = poly[i - 1], poly[i]
                if (y0 <= y) != (y1 <= y):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        return list(zip(xs[::2], xs[1::2]))


def _rows(base, glyph):
    y0, y1 = base.bounds[1], base.bounds[3]
    ys = [y0 + 3 + i * STEP for i in range(int((y1 - y0 - 6) // STEP) + 1)]
    return [(y, base.spans(y + 0.37), glyph.spans(y + 0.37)) for y in ys]


def _shift(rows):
    """The x offset most base edges find a glyph edge at."""
    votes = collections.Counter()
    for _, bs, gs in rows:
        for a, b in bs:
            for c, d in gs:
                votes[round((c - a) / 2) * 2] += 1
                votes[round((d - b) / 2) * 2] += 1
    if not votes:
        return 0
    best = max(votes.values())
    return min((dx for dx, v in votes.items() if v >= 0.9 * best), key=abs)


def compare(base, glyph):
    """{exact, covered, lost} shares of the base's spans (by length), the
    shift, and the rows."""
    rows = _rows(base, glyph)
    dx = _shift(rows)
    tally = collections.Counter()
    for _, bs, gs in rows:
        for a, b in bs:
            a, b = a + dx, b + dx
            L = b - a
            if any(abs(c - a) <= TOL and abs(d - b) <= TOL for c, d in gs):
                tally["exact"] += L
            elif any(c <= a + TOL and d >= b - TOL for c, d in gs):
                tally["covered"] += L
            else:
                tally["lost"] += L
    total = sum(tally.values()) or 1
    return {k: tally[k] / total for k in ("exact", "covered", "lost")}, dx, rows


def _stem(base, glyph, dx, y):
    """The base's widest span at y against the glyph's span at the same
    place: (base width, glyph width), or None."""
    bs = base.spans(y + 0.37)
    gs = glyph.spans(y + 0.37)
    if not bs or not gs:
        return None
    a, b = max(bs, key=lambda s: s[1] - s[0])
    a, b = a + dx, b + dx
    hits = [(c, d) for c, d in gs if c < b and d > a]
    if len(hits) != 1:
        return None
    c, d = hits[0]
    # only a span that is the stem's own (both edges near): a bar through it is not
    if abs(c - a) > 25 or abs(d - b) > 25:
        return None
    return b - a, d - c


def _iou(p, q, dx):
    """Intersection over union of two outlines' rows, q shifted by dx."""
    inter = union = 0
    lo = min(p.bounds[1], q.bounds[1])
    hi = max(p.bounds[3], q.bounds[3])
    y = lo + 3
    while y < hi:
        ps = p.spans(y + 0.37)
        qs = [(a + dx, b + dx) for a, b in q.spans(y + 0.37)]
        both = sum(max(0, min(b, d) - max(a, c)) for a, b in ps for c, d in qs)
        inter += both
        union += sum(b - a for a, b in ps) + sum(b - a for a, b in qs) - both
        y += STEP
    return inter / union if union else 0


def _best_iou(p, q):
    dx = _shift([(y, q.spans(y + 0.37), p.spans(y + 0.37))
                 for y in range(int(q.bounds[1]) + 3, int(q.bounds[3]), STEP * 3)])
    return _iou(p, q, dx)


def recipes(italic):
    """(char, op, source, band) as the style's glyphs were made."""
    import derive

    if not italic:
        return list(derive.RECIPES)
    import make_italic

    out = []
    for ch, op, source, band in derive.RECIPES:
        op, source, band = make_italic.ITALIC_RECIPES.get(ch, (op, source, band))
        if ch == "ɗ":  # the italic d with ɓ's top (make_italic.derive_stage)
            op = "attach"
        out.append((ch, op, source, band))
    return out


def attachment_reference(font, source, band, slant):
    """An attachment's same-style inputs, rather than its primary base alone.

    A letter such as ɮ contains l and ʒ. Comparing its whole silhouette
    with l alone can mistake that deliberate construction for roman ink.
    Rebuild the declared attachment in the recipe's upright frame. Keep
    the independent base-retention and stem checks on the primary base.
    """
    import derive

    _, cuts, pieces, *_ = band
    inputs = {piece[0] for piece in pieces if piece[0] in font}
    if not inputs:
        return None
    upright = ufoLib2.Font()
    transform = (1, 0, -slant, 1, slant * (font.info.xHeight or 884) / 2, 0)
    for name in inputs | {source, "space"}:
        glyph = upright.newGlyph(name)
        rec = DecomposingRecordingPen(font)
        font[name].draw(rec)
        rec.replay(TransformPen(glyph.getPen(), transform))
        glyph.width = font[name].width
    return Outline(None, None, path=derive.attach(upright, source, cuts, pieces))


def derived(font, path=None, only=None, regular=None):
    """[(glyph, kind, where, detail), ...] and {glyph: metrics} for the
    derived glyphs of font."""
    import derive

    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    italic = bool(slant)
    deslant = (1, 0, -slant, 1, 0, 0)
    cmap = {u: g.name for g in font for u in g.unicodes}

    def resolve(c):
        return derive.resolve(cmap, c)

    if italic and regular is None and path is not None:
        rpath = Path(path).parent / "MyiaDidot-Regular.ufo"
        regular = ufoLib2.Font.open(rpath) if rpath.exists() else None

    out, metrics = [], {}
    outlines = {}

    def outline(name, t=deslant):
        key = (name, t)
        if key not in outlines:
            outlines[key] = Outline(font, name, t)
        return outlines[key]

    for ch, op, source, band in recipes(italic):
        name, source = resolve(ch), resolve(source)
        if only and name not in only:
            continue
        if name not in font or source not in font or source == "space":
            continue
        g = font[name]
        if italic and g.lib.get(SOURCE_KEY) != "derived":
            continue
        if g.width != int(g.width):
            out.append((name, "advance", "", f"{g.width} not whole units"))
        if op not in KEEPS | TRANSFORMS:
            continue
        glyph = outline(name)
        if glyph.bounds is None:
            continue
        if op in TRANSFORMS:
            w = font[source].width
            sb = band if isinstance(band, str) else band[0] if isinstance(band, tuple) else "x"
            cy = derive.band_middle(font, sb) if op != "mirror" else 0
            m = {"turn": (-1, 0, 0, -1, w, 2 * cy), "mirror": (-1, 0, 0, 1, w, 0),
                 "flip": (1, 0, 0, -1, 0, 2 * cy)}[op]
            # deslanted, then turned: the recipes work in the upright frame
            a, _, _, d, e, f = m
            base = outline(source, (a, 0, -a * slant, d, e, f))
        elif ch in derive.NARROW and not italic:
            # the base with its bowl narrowed as the recipe narrows it
            factor, _ = derive.NARROW[ch]
            sb = band[0] if isinstance(band, tuple) else "x"
            x0 = derive.stems_at(font, source, derive.band_middle(font, sb))[-1][0]
            base = Outline(font, None, path=derive.narrowed(derive.to_path(font, font[source]), x0, factor))
        else:
            base = outline(source)
        if base.bounds is None:
            continue
        shares, dx, _ = compare(base, glyph)
        m = {"op": op, "source": source, "dx": dx, **shares}
        # the main stem at a quarter, half and three quarters of the band
        # (the base's own straight part); the middle difference of the
        # three, so that a bar or tilde through one of them does not count
        y0, y1 = base.bounds[1], base.bounds[3]
        probes = [(y, _stem(base, glyph, dx, y)) for y in (y0 + k * (y1 - y0) for k in (0.25, 0.5, 0.75))]
        probes = sorted(((y, s) for y, s in probes if s), key=lambda p: p[1][1] - p[1][0])
        mid, st = probes[len(probes) // 2] if probes else (None, None)
        m["stem"] = st
        kept = shares["exact"] + shares["covered"]
        if kept < KEPT:
            out.append((name, "base", "", f"{kept:.0%} of {source} kept ({op})"))
        if st and abs(st[1] - st[0]) > max(STEM_OFF[0], STEM_OFF[1] * st[0]):
            out.append((name, "stem", f"at {round(mid)}", f"{round(st[1])} against {source}'s {round(st[0])}"))
        # (a twin is its base twice: no overlap to compare)
        if italic and regular is not None and name in regular and source in regular and op != "twin":
            mine = _best_iou(glyph, base)
            roman = _best_iou(glyph, Outline(regular, name))
            m["iou_base"], m["iou_roman"] = mine, roman
            reference = source
            if op == "attach" and roman > mine + STYLE_MARGIN:
                attached = attachment_reference(font, source, band, slant)
                if attached is not None:
                    m["iou_recipe"] = _best_iou(glyph, attached)
                    if m["iou_recipe"] > mine:
                        mine = m["iou_recipe"]
                        reference = "its same-style attachment recipe"
            if roman > mine + STYLE_MARGIN:
                detail = f"closer to the Regular's {name} ({roman:.2f}) than to {reference} ({mine:.2f})"
                out.append((name, "style", "", detail))
        metrics[name] = m
    return out, metrics


def outline_hash(font, name):
    """A glyph's advance and decomposed outline, hashed."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    return hashlib.sha256(json.dumps([font[name].width, rec.value]).encode()).hexdigest()


def report(font, path, found, metrics):
    """The findings and measures as plain data: the same sources give the
    same report."""
    from build_support import content_hash

    def plain(v):
        if isinstance(v, (tuple, list)):
            return [plain(x) for x in v]
        return round(v, 4) if isinstance(v, float) else v

    glyphs = {n: {**{k: plain(v) for k, v in m.items()}, "glyph_sha256": outline_hash(font, n),
                  "source_sha256": outline_hash(font, m["source"])}
              for n, m in metrics.items()}
    return {"format": "myiadidot-derived-v1", "ufo": Path(path).name, "ufo_sha256": content_hash(path),
            "limits": {"tol": TOL, "kept": KEPT, "stem_off": list(STEM_OFF), "step": STEP},
            "glyphs": glyphs,
            "findings": [dict(zip(("glyph", "kind", "where", "detail"), f)) for f in found]}


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    ap.add_argument("--all", action="store_true", help="print every glyph's measures")
    ap.add_argument("--json", type=Path, help="write the measures and findings here")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    found, metrics = derived(font, args.ufo, set(args.glyphs) or None)
    if args.json:
        args.json.write_text(json.dumps(report(font, args.ufo, found, metrics), indent=1,
                                        sort_keys=True, ensure_ascii=False) + "\n")
    if args.all:
        for n, m in sorted(metrics.items(), key=lambda kv: kv[1]["exact"]):
            st = m["stem"]
            sts = f"stem {st[0]:.0f}->{st[1]:.0f}" if st else ""
            extra = f" iou {m['iou_base']:.2f}/{m['iou_roman']:.2f}" if "iou_base" in m else ""
            print(f"{n:14} {m['op']:9} {m['source']:10} dx {m['dx']:5} exact {m['exact']:.2f} "
                  f"covered {m['covered']:.2f} lost {m['lost']:.2f} {sts}{extra}")
    for name, k, where, detail in found:
        print(f"{name:20} {k:8} {where:>12}  {detail}")


if __name__ == "__main__":
    main()
