#!/usr/bin/env python3
"""Phase 6, step C: the Italic's long stems weighted to n's stem, its
ascenders raised, its overshoots set to the Regular's, one construction a
glyph (docs/claude/italic.md, "The designer's round", 2026-11-17, 4 to 6).

    python scripts/italic_long.py SRC.ufo OUT.ufo [GLYPH ...]            candidates
    python scripts/italic_long.py SRC.ufo OUT.ufo [GLYPH ...] --install --date D --review DOC

Three changes, made together so that no glyph is installed twice for
what is one reason, each by the outline's own points:

- weight (STEMS): the stem where it leaves the x-height (b d h k: above
  it; p q þ ц щ џ: below; f ß ƒ ф ђ ћ д б: both; l t ſ: the whole stem)
  thickened to n's stem (derive.embolden with a weight per node: the
  nodes on a straight stem edge inside the band, faded at the band's
  ends; the amount measured on the glyph, so that the stem reads n's
  thickness where italic_measures.py reads it). A serif, a hook, a
  crossbar and a bowl are not stems and keep their thickness.
- raise (ASCENDERS): the points above the x-height ramped up by ASC
  units (the ascender 4 % of the cap height over the capitals, the
  Regular's: 1496 over 1434), along the italic angle.
- overshoot: the points below the baseline's flat edges moved up and the
  capitals' above the cap line down so that the round's overshoot is
  the Regular's: lowercase -16 (the Italic -23), capitals -28 and 1462
  (the Italic -35 and 1473). Only the points within OVER_BAND of an
  extreme move, so a flat foot (0, 1434) and a descender's end stay.

The drawn f-ligatures (LIGATURES) are given by glyph name and made as f;
in them only the stems light at their middle are weighted (fi's i is not).

Then, as italic_harmonise.py: redrawn onto clean nodes (redraw.py) and
gated against the construction, into OUT.ufo; with --install into SRC.ufo
marked drawn, lib org.myiadidot.redrawn "harmonise": "long". Run again on
a changed glyph, it changes it again: install once.
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
import glyph_lint as L  # noqa: E402
import italic_bowls as B  # noqa: E402
import italic_harmonise as H  # noqa: E402
import italic_measures as im  # noqa: E402
import redraw as R  # noqa: E402

# the stems, by where they leave the x-height: asc (above it), desc (below
# the baseline), both, all (a stem with no x-height part of its own)
STEMS = {
    **dict.fromkeys("bdhk", "asc"), **dict.fromkeys("pq", "desc"), "þ": "both",
    **dict.fromkeys("ltſfß", "all"), "ƒ": "all",
}
# held back, 2026-11-18: the Cyrillic stems (б д ф ђ ћ ц щ џ) barely moved, their rows
# read bowls and hooks: a pass of their own
HELD = set("бдфђћцщџ")
# the ascenders raised: units, the Regular's 4 % over the capitals
ASC = 61
ASCENDERS = {**dict.fromkeys("bdhklþfſßƒλħđłϐ", ASC), "ð": 45, **dict.fromkeys("βδξꞵ", 22)}
RAMP = (0.0, 0.40)  # of the x-height over it: the raise's ease, from nothing to whole
OVER = 8  # units: the lowercase and the capitals' overshoot below, -23/-35 to -16/-28
OVER_TOP = 11  # units: the capitals' above, 1473 to 1462
OVER_BAND = (-2, -14)  # the baseline's flat edge stays: the move eased in from here to here
OVER_FAR = (-45, -90)  # and eased out again below: a descender's end stays
STEM_AT = (0.5, 1.45)  # a stem edge's thickness across, over n's: the nodes weighted
CASE_TOP = 1440  # a capital's overshoot above begins here (the cap line is 1434)
# the drawn f-ligatures, named by glyph, made as the letter given (2026-11-21:
# step C left them, and ſ, at Old Standard's height and stem; italic_ligatures
# builds f_b ... and the ſ-ligatures from them). In a ligature only the stems
# lighter than LIGHT of n's are weighted: fi's i stands at n's already.
LIGATURES = dict.fromkeys(("fi", "fl", "ff", "ffi", "ffl", "f_j", "f_f_j"), "f")
LIGHT = 0.95


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def n_stem(path):
    """n's stem in font units, as italic_measures reads it a third up"""
    src = bm.Source(path)
    return im.stem(im.cut(src, "n")) / src.scale


def runs_at(segs, y):
    """the ink's runs on the row y, from the flattened outline"""
    xs = []
    for (ax, ay), (bx, by) in segs:
        if (ay <= y < by) or (by <= y < ay):
            xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2], strict=False))


def stem_at(segs, y, xh, lean, lightest=None):
    """the widest run under 0.45 of the x-height on row y, across (its
    lean taken out), or None; with lightest (a ligature: n's stem) the
    narrowest run that is still a stem"""
    k = math.hypot(1, lean)
    runs = [(r[1] - r[0]) / k for r in runs_at(segs, y) if 0 < r[1] - r[0] < 0.45 * xh]
    if lightest:
        runs = [t for t in runs if t >= STEM_AT[0] * lightest]
        return min(runs) if runs else None
    return max(runs) if runs else None


def bands(kind, xh, top, bottom):
    """the heights the stem is weighted at: [(lo, hi)], and the rows it is measured on"""
    asc, desc = (xh * 0.95, top + 1), (bottom - 1, -0.05 * xh)
    whole = (bottom - 1, top + 1)
    return {"asc": [asc], "desc": [desc], "both": [asc, desc], "all": [whole]}[kind]


def stem_nodes(glyph, segs, spans, stem, sl, upper=STEM_AT[1]):
    """the end nodes of the stem's straight edges, {(x, y)} rounded: the
    long edges running along the italic angle, a stem thick across, that
    lie in a band by a third of their length or are collinear with one that
    does (b's stem right of the bowl continues the edge above it). A
    straight edge moves whole, so the stem keeps one thickness from end to
    end and keeps its slant (make_italic.weight_thick does the same)."""
    edges = []
    for c in glyph.contours:
        P = c.points
        for i, p in enumerate(P):
            if p.type != "line":
                continue
            q = P[i - 1]
            dx, dy = p.x - q.x, p.y - q.y
            ln = math.hypot(dx, dy)
            if ln < 100 or abs(dx - sl * dy) > 0.36 * ln:  # within 20 degrees of the stem's lean
                continue
            ok = heavy = False
            for u in (0.2, 0.5, 0.8):  # the edge is a stem where it stands alone: not at every height (q's joins its bowl)
                mx, my = q.x + u * dx, q.y + u * dy
                runs = [r for r in runs_at(segs, my) if r[0] - 3 <= mx <= r[1] + 3]
                t = (runs[0][1] - runs[0][0]) / math.hypot(1, sl) if runs else 0
                ok |= STEM_AT[0] * stem <= t <= upper * stem
                heavy |= u == 0.5 and t > upper * stem
            # a ligature's stem is light at its middle: fi's i stands at n's
            # there and thins towards its top; fl's l is light but thick at
            # its head, so the ends do not decide
            if not ok or (heavy and upper < STEM_AT[1]):
                continue
            lo, hi = sorted((p.y, q.y))
            inside = sum(max(0.0, min(hi, b) - max(lo, a)) for a, b in spans) / max(hi - lo, 1.0)
            edges.append((q, p, inside))
    chosen = [e for e in edges if e[2] >= 0.3 or e[2] * abs(e[1].y - e[0].y) >= 100]
    out = set()
    for q, p, _ in edges:
        for a, b, _ in chosen:
            ex, ey = b.x - a.x, b.y - a.y
            d = math.hypot(ex, ey)
            if all(abs((pt.x - a.x) * ey - (pt.y - a.y) * ex) / d < 3 for pt in (p, q)):
                out |= {(round(p.x, 1), round(p.y, 1)), (round(q.x, 1), round(q.y, 1))}
                break
    return out


def construct(font, glyph, stem, ch, ligature=False):
    """glyph as the three changes make it (a new glyph, outline only); a
    ligature is made as its letter ch, its light stems alone weighted"""
    sl, xh = H.slant_of(font), font.info.xHeight
    ys = [p.y for c in glyph.contours for p in c.points if p.type]
    top, bottom = max(ys), min(ys)
    up = ASCENDERS.get(ch, 0)
    cap = ch.isupper() or ch in ("Θ",)

    def dy(y):
        d = up * smooth((y - xh * (1 + RAMP[0])) / ((RAMP[1] - RAMP[0]) * xh)) if up else 0.0
        if y <= OVER_BAND[0]:
            d += OVER * smooth((OVER_BAND[0] - y) / (OVER_BAND[0] - OVER_BAND[1])) \
                * (1 - smooth((OVER_FAR[0] - y) / (OVER_FAR[0] - OVER_FAR[1])))
        if cap and y > CASE_TOP:
            d -= OVER_TOP * smooth((y - CASE_TOP) / 32)
        return d

    def fn(px, py):
        ny = py + dy(py)
        return px + sl * (ny - py), ny

    new = H.moved(glyph, fn)
    for an in new.anchors:
        # across only: the anchors' heights are the Regular's (the spacing
        # marks of the precomposed forms stand at fixed heights, NFD agrees
        # with them only so); moved with the overshoots (2026-11-18) they broke it
        an.x = fn(an.x, an.y)[0]
    kind = STEMS.get(ch)
    if not kind:
        return new, None, fn
    # weight: measured on the moved outline, where the stem stands now
    flat = ufoLib2.objects.Glyph()
    rec = RecordingPen()
    new.draw(rec)
    rec.replay(flat.getPen())
    segs = H.derive_segments(flat)
    spans = bands(kind, xh, top + up, bottom)
    rows = []
    for lo, hi in spans:
        for t in (0.35, 0.5, 0.65):
            rows.append(max(lo, bottom + 1) + t * (min(hi, top + up) - max(lo, bottom + 1)))
    if kind == "all":
        rows = [xh / 3, xh / 2]
    got = [t for y in rows if (t := stem_at(segs, y, xh, sl, stem if ligature else None)) is not None]
    if not got:
        return new, None, fn
    now = sum(got) / len(got)
    amount = stem - now
    if amount <= 0.5:
        return new, {"now": now, "amount": 0.0}, fn

    fixed = stem_nodes(new, segs, spans, stem, sl, LIGHT if ligature else STEM_AT[1])

    def factor(x, y, inward):
        return 1.0 if (round(x, 1), round(y, 1)) in fixed else 0.0

    out = derive.embolden(rec, amount, 0, factor)
    made = copy.deepcopy(new)
    made.clearContours()
    out.draw(made.getPen())
    return made, {"now": now, "amount": amount}, fn


def stem_after(font, glyph, ch, ligature=False, stem=None):
    """the stem as construct reads it, on a finished glyph: the same rows"""
    sl, xh = H.slant_of(font), font.info.xHeight
    ys = [p.y for c in glyph.contours for p in c.points if p.type]
    top, bottom = max(ys), min(ys)
    flat = ufoLib2.objects.Glyph()
    rec = RecordingPen()
    glyph.draw(rec)
    rec.replay(flat.getPen())
    segs = H.derive_segments(flat)
    spans = bands(STEMS[ch], xh, top, bottom)
    rows = []
    for lo, hi in spans:
        lo, hi = max(lo, bottom + 1), min(hi, top)
        rows += [lo + t * (hi - lo) for t in (0.35, 0.5, 0.65)]
    if STEMS[ch] == "all":
        rows = [xh / 3, xh / 2]
    got = [t for y in rows if (t := stem_at(segs, y, xh, sl, stem if ligature else None)) is not None]
    return sum(got) / len(got) if got else None


def snapped(spec, glyph, reach=45):
    """the spec's points put on the nearest node of the construction (the weight
    moves an edge's nodes by more than the fit's NEAR)"""
    pts = [(p.x, p.y) for c in glyph.contours for p in c.points if p.type]

    def near(xy):
        best = min(pts, key=lambda q: math.dist(q, xy))
        return [best[0], best[1]] if math.dist(best, xy) <= reach else xy

    def go(v):
        if isinstance(v, list) and len(v) == 2 and all(isinstance(t, (int, float)) for t in v):
            return near(v)
        if isinstance(v, list):
            return [go(t) for t in v]
        if isinstance(v, dict):
            return {k: go(t) for k, t in v.items()}
        return v

    return go(spec) if spec is not None else None


def affected(font, name):
    """the glyphs the changes touch: a stem, an ascender, a round's overshoot"""
    g = font[name]
    ch = chr(g.unicode) if g.unicode else ""
    if ch in HELD:
        return False
    if ch in STEMS or ch in ASCENDERS:
        return True
    ys = [p.y for c in g.contours for p in c.points if p.type]
    if not ys:
        return False
    over_lo = -45 < min(ys) < -14
    over_hi = ch.isupper() and max(ys) > CASE_TOP + 20
    return ch.isalpha() and (over_lo or over_hi)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("glyphs", nargs="*", help="characters, or the ligatures of LIGATURES by name")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--review")
    ap.add_argument("--all", action="store_true", help="every glyph the changes touch")
    a = ap.parse_args()
    if a.install and not (a.date and a.review):
        ap.error("--install needs --date and --review")
    font = ufoLib2.Font.open(a.src)
    out = ufoLib2.Font.open(a.src)
    stem = n_stem(a.src)
    spec = R.spec_for(a.src, None)
    cmap = {chr(g.unicode): g.name for g in font if g.unicode and not g.components}
    chars = list(a.glyphs[0]) if len(a.glyphs) == 1 and len(a.glyphs[0]) > 1 and a.glyphs[0] not in cmap.values() \
        and a.glyphs[0] not in LIGATURES \
        else a.glyphs
    if a.all:
        chars = [c for c, n in cmap.items() if any("drawn" in k for k in font[n].lib) and affected(font, n)]
    print(f"n's stem {stem:.1f}")
    failed = 0
    for ch in chars:
        lig = ch in LIGATURES
        name, ch = (ch, LIGATURES[ch]) if lig else (cmap[ch], ch)
        g = font[name]
        raw, info, fn = construct(font, g, stem, ch, lig)
        for c in raw.contours:
            for pt in c.points:
                pt.x, pt.y = round(pt.x), round(pt.y)
        for an in raw.anchors:
            an.x, an.y = round(an.x), round(an.y)
        had = {f[1] for f in L.notch_findings(font, raw, raw.getBounds(font))}
        for tol in B.TOLS:
            new, rep = R.redraw(raw, tol, snapped(B.moved_spec(spec.get(name), fn), raw))
            fail, look = R.gate(rep, None)
            fail += [f"notch at {f[1]} ({f[2]})" for f in L.notch_findings(font, new, new.getBounds(font))
                     if f[1] not in had]
            if not fail:
                break
        after = stem_after(font, new, ch, lig, stem) if ch in STEMS else None
        note = f"stem {info['now']:.0f} -> {after:.0f}" if info and after else ""
        print(f"{ch} {name:<10}{rep['nodes_before']:>3} ->{rep['nodes_after']:>3} nodes  "
              f"tol {tol:g}  {rep['dev']:.1f} from the construction  {note}  "
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
        if a.install and not fail:
            R.install(font, name, new, a.date, a.review, rep)
            font[name].clearAnchors()
            for an in raw.anchors:
                font[name].appendAnchor(copy.deepcopy(an))
            font[name].lib[R.KEY]["harmonise"] = "long"
    out.save(a.out, overwrite=True)
    if a.install:
        font.save()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
