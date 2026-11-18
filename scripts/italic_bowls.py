#!/usr/bin/env python3
"""Phase 6, step B: the Italic's bowls wider, n o d p q (and what shares
them: b a g h m u) and O, by about a tenth of the counter
(docs/claude/italic.md, "The designer's round", 2026-11-17).

    python scripts/italic_bowls.py SRC.ufo OUT.ufo [GLYPH ...]            candidates
    python scripts/italic_bowls.py SRC.ufo OUT.ufo [GLYPH ...] --install --date D --review DOC

The operation: each counter is found on the row through the middle of the
zone (deslanted), the white between two ink runs; the outline is cut
there and everything right of the counter's middle moved out by
WIDEN units, the move eased in over the counter's middle part (BAND:
smoothstep, so that no curve crossing it gains a corner). The stems and
the thick sides lie outside the band and move whole or not at all; what
crosses the band is the bowl's top and bottom, the arch, a hook's tail:
hairlines run near horizontal there and keep their thickness. m has two
counters, both widened. Anchors move with the outline; the advance grows
by what the glyph grew, so both sidebearings stay.

Then, as italic_harmonise.py: the construction redrawn onto clean nodes
(redraw.py, the spec's points moved by the same map) and gated against
the construction (at TOL, then closer, TOLS, where the gate finds an
extreme left without its node: b), into OUT.ufo; with --install into SRC.ufo marked drawn,
lib org.myiadidot.redrawn "harmonise": "bowls". Run again on a changed
glyph, it widens it again: install once.

WIDEN is calibrated so that italic_measures.py's relations land inside
the three Didones' range (read from build/quality/italic-measures.json,
printed after each run): the counters of n o d p q b and O's width,
with the widths n o a, a-z, A-Z and the hairlines o n checked to stay
inside. The letters with no measure take their leader's units (KIN),
so a family stays one size. C G Q D are not run by default: whether
they follow O is the designer's, on the sheet (name them to see them).
"""

import argparse
import copy
import json
import sys
from pathlib import Path

import ufoLib2
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))

import bold_measures as bm  # noqa: E402
import glyph_lint as L  # noqa: E402
import italic_harmonise as H  # noqa: E402
import italic_measures as im  # noqa: E402
import redraw as R  # noqa: E402

# units the counter grows by, per counter (m: each of its two)
WIDEN = {"n": 34, "o": 42, "d": 40, "p": 40, "q": 40, "O": 140}
# the letters without a measure of their own take their leader's units
KIN = {"h": "n", "m": "n", "u": "n", "b": "p", "a": "d", "g": "q",
       "Q": "O", "C": "O", "G": "O", "D": "O"}
BAND = 0.20  # of the counter's width at either side: the ease runs over the middle 60 %
ROW = 0.5  # of the zone: where the counters are found
MIN_GAP = 0.12  # of the zone: white narrower than this is no counter (a serif's slot)
NAMES = "nodpqbaghmuO"
TOLS = (R.TOL, 1.5, 1.0)  # the redraw's tolerances, tried in turn until the gate (and glyph_lint's notch) passes
MEASURES = ["counter n / x-height", "counter o / x-height", "counter d / x-height",
            "counter p / x-height", "counter q / x-height", "counter b / x-height",
            "width O / cap height", "width n / x-height", "width o / x-height",
            "width a / x-height", "width a-z / x-height", "width A-Z / cap height",
            "hairline o top / stem", "hairline o bottom / stem", "hairline n arch / stem"]
REPORT = im.ROOT / "build/quality/italic-measures.json"


def widen_of(name):
    return WIDEN[KIN.get(name, name)]


def counters(glyph, font):
    """[(left, right)] of the counters on the middle row, deslanted units"""
    sl = H.slant_of(font)
    zone = font.info.capHeight if glyph.name[0].isupper() else font.info.xHeight
    y = ROW * zone
    rec = RecordingPen()
    glyph.draw(rec)
    flat = ufoLib2.objects.Glyph()
    rec.replay(flat.getPen())
    xs = []
    for (ax, ay), (bx, by) in H.derive_segments(flat):
        if (ay <= y < by) or (by <= y < ay):
            x = ax + (y - ay) * (bx - ax) / (by - ay)
            xs.append(x - sl * y)
    xs.sort()
    runs = list(zip(xs[0::2], xs[1::2]))  # ink runs (clean contours, no overlaps)
    gaps = [(a[1], b[0]) for a, b in zip(runs, runs[1:])]
    gaps = [g for g in gaps if g[1] - g[0] >= MIN_GAP * zone]
    if not gaps and len(runs) == 1:
        # open on the right (C G): from the left side's inside to the ink's right edge
        right = max(p.x - sl * p.y for c in glyph.contours for p in c.points)
        if right - runs[0][1] >= MIN_GAP * zone:
            gaps = [(runs[0][1], right)]
    return gaps


def mapping(glyph, font):
    """fn(x, y) -> (x, y), the widening, and the units the glyph grows by"""
    sl = H.slant_of(font)
    gaps = counters(glyph, font)
    if not gaps:
        raise ValueError(f"{glyph.name}: no counter found on the row at {ROW:g} of the zone")
    d = widen_of(glyph.name)
    bands = [(l + BAND * (r - l), r - BAND * (r - l)) for l, r in gaps]

    def shift(x):
        s = 0.0
        for lo, hi in bands:
            t = min(1.0, max(0.0, (x - lo) / (hi - lo)))
            s += d * t * t * (3 - 2 * t)
        return s

    def fn(px, py):
        dx = px - sl * py
        return px + shift(dx), py

    return fn, d * len(gaps), gaps, bands, shift


def quartered_in(rec, bands, sl):
    """rec with each curve that reaches into a band split in four; the
    rest only translated by the map, so left whole (a short curve at a
    stem's foot, quartered, falls under the redraw's shortest span and
    takes the stem's edge with it)"""
    from fontTools.misc.bezierTools import splitCubicAtT

    out, cur = RecordingPen(), None
    for op, args in rec.value:
        if op == "curveTo":
            xs = [x - sl * y for x, y in (cur, *args)]
            if any(min(xs) < hi and max(xs) > lo for lo, hi in bands):
                for seg in splitCubicAtT(cur, *args, 0.25, 0.5, 0.75):
                    out.curveTo(*seg[1:])
            else:
                out.curveTo(*args)
        else:
            getattr(out, op)(*args)
        cur = args[-1] if args else cur
    return out


def bowls(font, glyph):
    """the construction: glyph widened, its curves in the ease quartered
    first so that it bends them where it runs (the redraw takes the nodes
    back out).

    n's left stem comes out 1.5 units thinner at half the x-height (191 to
    189.5, h and m 1 unit): its inner edge and its arch are one curve,
    which the redraw cannot keep on the stem once the arch is wider.
    Neither cutting the curves exactly at the band's edges nor a closer
    tolerance kept it; a narrower ease (BAND 0.3) did, at the cost of
    nodes in o p m O and a failed b (2026-11-17). It cannot be taken as
    it is: the small caps' drafting stem is n's there, rounded, and moved
    from 181 to 180, every small cap drafted again (the Bold Italic's
    ψ.sc lost an arm). The installed n was mended by hand after
    (docs/claude/italic.md, "What followed"); install n again and mend it
    again."""
    fn, grow, gaps, bands, _shift = mapping(glyph, font)
    rec = RecordingPen()
    glyph.draw(rec)
    rec = quartered_in(rec, bands, H.slant_of(font))
    new = copy.deepcopy(glyph)
    new.clearContours()
    rec.replay(new.getPen())
    for c in new.contours:
        for p in c.points:
            p.x, p.y = fn(p.x, p.y)
    for a in new.anchors:
        a.x, a.y = (round(v) for v in fn(a.x, a.y))
    new.width = glyph.width + round(grow)
    return new, fn, gaps


def moved_spec(spec, fn):
    """the spec's points through fn (a spec names nodes by where they are)"""
    if spec is None:
        return None
    if isinstance(spec, list) and len(spec) == 2 and all(isinstance(v, (int, float)) for v in spec):
        return [round(v, 1) for v in fn(*spec)]
    if isinstance(spec, list):
        return [moved_spec(s, fn) for s in spec]
    if isinstance(spec, dict):
        return {k: moved_spec(v, fn) for k, v in spec.items()}
    return spec


def ranges():
    """{measure: (lo, hi)} of the three Didones' relations, italic_measures' last run"""
    if not REPORT.exists():
        sys.exit(f"{REPORT} missing: run scripts/quality/italic_measures.py first")
    out = {}
    for v in json.loads(REPORT.read_text())["verdicts"]:
        if v["name"] in MEASURES and v.get("refs"):
            out[v["name"]] = (min(v["refs"].values()), max(v["refs"].values()), v["myia"])
    return out


def measure(ufo):
    """Myia's relation (Italic over Regular) on MEASURES, the Italic at ufo"""
    r = im.measure(bm.Source(im.ROOT / "sources/MyiaDidot-Regular.ufo"))
    i = im.measure(bm.Source(ufo))
    return {k: i[k][0] / r[k][0] for k in MEASURES if k in r and k in i and r[k][0] and i[k][0]}


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
    names = a.glyphs or list(NAMES)
    font = ufoLib2.Font.open(a.src)
    out = ufoLib2.Font.open(a.src)
    spec = R.spec_for(a.src, None)
    failed = 0
    for name in names:
        g = font[name]
        try:
            raw, fn, gaps = bowls(font, g)
            # the eased curves meet the stems' edges: where one span at
            # TOL leaves an extreme without its node (b), or opens a crotch
            # into a slit the construction has not (u's, glyph_lint's
            # notch: 30 px at 2 and 1.5, none at 1), a closer fit keeps it
            had = {f[1] for f in L.notch_findings(font, raw, raw.getBounds(font))}
            for tol in TOLS:
                new, rep = R.redraw(raw, tol, moved_spec(spec.get(name), fn))
                fail, look = R.gate(rep, None)
                new.width = raw.width
                fail += [f"notch at {f[1]} ({f[2]})" for f in L.notch_findings(font, new, new.getBounds(font))
                         if f[1] not in had]
                if not fail:
                    break
        except ValueError as e:
            print(f"{name:<3}refused: {e}")
            failed += 1
            continue
        where = ", ".join(f"{l:.0f}-{r:.0f}" for l, r in gaps)
        print(f"{name:<3}+{widen_of(name)} x {len(gaps)} (counter {where}) tol {tol:g}{rep['nodes_before']:>4} ->"
              f"{rep['nodes_after']:>3} nodes  {rep['dev']:.1f} from the construction  advance {g.width} -> {raw.width}  "
              + ("FAIL: " + "; ".join(fail) if fail else "candidate")
              + ("  [look: " + "; ".join(look) + "]" if look else ""))
        failed += bool(fail)
        o = out[name]
        o.clearContours()
        for c in new.contours:
            o.appendContour(c)
        o.clearAnchors()
        for an in raw.anchors:
            o.appendAnchor(copy.deepcopy(an))
        o.width = raw.width
        if a.install and not fail:
            R.install(font, name, new, a.date, a.review, rep)
            f = font[name]
            f.width = raw.width
            f.clearAnchors()
            for an in raw.anchors:
                f.appendAnchor(copy.deepcopy(an))
            f.lib[R.KEY]["harmonise"] = "bowls"
    out.save(a.out, overwrite=True)
    rng = ranges()
    for k, v in measure(a.out).items():
        lo, hi, was = rng[k]
        print(f"  {k:<26}{was:.3f} -> {v:.3f}  the Didones {lo:.3f} to {hi:.3f}  "
              + ("inside" if lo <= v <= hi else "OUTSIDE"))
    if a.install:
        font.save()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
