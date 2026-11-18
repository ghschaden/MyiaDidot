#!/usr/bin/env python3
"""Phase 6, step B's loose end: the Italic's round small caps o.sc and q.sc
on the widened O and Q (docs/claude/italic.md, "What followed").

    python scripts/italic_round_sc.py SRC.ufo OUT.ufo [--install --date D --why TEXT]

They were drawn on 2026-11-12 from the narrow O and Q and kept as saved, so
the widening of step B left them narrower than c.sc and d.sc (o.sc 1060
against c.sc 1148; the Regular's o.sc is the wider of the two). FontForge's
draft of the widened O came out square inside (the weighting thickens its
curves unevenly), and italic_bowls.py's widening of o.sc itself pushed the
extra width into a straight right side. So each is made as the small caps'
own recipe makes a small cap of a capital (derive.enlarge: ("q.sc", "enlarge",
"Q", ("O", "o.sc"))), the capital being the widened one and the strokes
measured on the o.sc as it stands in SRC: an oval like O's, stems and
hairlines as the old o.sc's (205 and 59). both are built before either replaces o.sc, since o.sc
is the measure.

Without --install, OUT.ufo is SRC with the two glyphs replaced. With it SRC
is written and both marked drawn (their italicSource stays "small cap draft":
the recipes read a small cap draft's measures without its added weight, as
they did the old o.sc's; "drawn" would change every small cap made against
them, n.sc 1202 -> 1191).
"""

import argparse
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))

import derive  # noqa: E402
import make_italic as MI  # noqa: E402

PAIRS = (("o.sc", "O"), ("q.sc", "Q"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--why")
    a = ap.parse_args()
    if a.install and not (a.date and a.why):
        ap.error("--install needs --date and --why")
    f = ufoLib2.Font.open(a.src)
    up = MI.upright(f)
    _, o_stem, o_hair = derive.strokes(up, "o")
    up.lib[derive.STROKE_KEY] = MI.recipe_scale(o_stem, o_hair, MI.case_weight(f, f["o.sc"]))
    # the old o.sc's top and bottom: the zones the hinting and the recipes read
    # (enlarge's scale gives 1068 for 1067, and cff_hint_zones counts the unit)
    y0, y1 = derive.ink_bounds(up, "o.sc")[1::2]
    box0, stem0, hair0 = derive.strokes(up, "o.sc")
    lsb0, rsb0 = box0[0], up["o.sc"].width - box0[2]
    delta = None
    for name, cap in PAIRS:
        MI.enlarged(f, up, name, "enlarge", cap, ("O", "o.sc"), "_" + name)
        g = up["_" + name]
        if delta is None:
            # the recipes measure o.sc's stem: the thick strokes brought to the old
            # one's (the weighting after the scaling falls short of it by a unit or two)
            delta = stem0 - derive.strokes(up, "_" + name)[1]
            print(f"stem {stem0:.2f}: {name} came at {stem0 - delta:.2f}, weighted by {delta:+.2f}")
        MI.reweight(up, "_" + name, delta)
        top = max(p.y for c in g.contours for p in c.points)
        k = (y1 - y0) / (top - y0)
        for c in g.contours:
            for p in c.points:
                p.y = y0 + (p.y - y0) * k
        for an in g.anchors:
            an.y = y0 + (an.y - y0) * k
    for name, _ in PAIRS:
        up.layers.defaultLayer.renameGlyph(name, "_old" + name)
        up.layers.defaultLayer.renameGlyph("_" + name, name)
        up[name].anchors = list(up["_old" + name].anchors)
        up[name].unicodes = list(up["_old" + name].unicodes)
        MI.put(f, up, name, "small cap draft")
        del up["_old" + name]
    # what the recipes read of o.sc (its side bearings, stem), as the old one's, to
    # what the saved glyph allows (whole units): the slant and the rounding of the
    # first put leave a unit and a half in the stem and a unit in the left side
    for _ in range(3):
        box, stem, hair = derive.strokes(MI.upright(f), "o.sc")
        d_stem, d_lsb = stem0 - stem, lsb0 - box[0]
        if abs(d_stem) < 0.05 and abs(d_lsb) < 0.3:
            break
        for name, _ in PAIRS:
            g = up[name]
            if abs(d_stem) >= 0.05:
                MI.reweight(up, name, d_stem)
            for c in g.contours:
                for p in c.points:
                    p.x += d_lsb
            for an in g.anchors:
                an.x += d_lsb
            g.width = round(derive.ink_bounds(up, name)[2] + rsb0)
            MI.put(f, up, name, "small cap draft")
    for name, _ in PAIRS:
        print(f"{name:<5}stem {derive.strokes(MI.upright(f), name)[1]:.2f} (old o.sc {stem0:.2f}) advance {f[name].width}")
    if a.install:
        from drawn import mark
        for name, _ in PAIRS:
            mark(f, name, a.date, a.why)
            f[name].lib[MI.SOURCE_KEY] = "small cap draft"
    f.save(None if a.install else a.out, overwrite=True)


if __name__ == "__main__":
    main()
