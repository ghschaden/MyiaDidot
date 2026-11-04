"""Curves running into a straight stem kept on their side of its edge (Bold).

Emboldened by weight, a curve that runs into a vertical stem (an arch's
inner side into n m h's stem, u's bowl into its stem at the foot, a hook
into j J ʃ, Œ's counter into E's stem) gets a handle past the stem's edge:
the curve crosses the edge and comes back, a dent in the straight stem
(Bold n 24 units past, m 32; the Regular has none; 2026-11-04). r's
return is faired its own way first (r_hook.fair_bold_stem).

For each such curve, its handle on the stem's node is put back on the
edge (the tangent there the stem's), its handle on the far node shortened
along its own direction until it reaches the edge (the curve leaves the
junction as before). Found on unrounded points too: make_bold runs it
before the derived letters are made of their bases, and again once
rounded (finalization).
"""

import sys

import ufoLib2

PAST = 1.0  # units: a handle further past the edge is moved
STEM = 40  # units: the shortest straight run that is a stem's edge
AWAY = 4  # units: the far node at least this far from the edge (not a curve along the stem; m's arch joins 9.8 off before rounding)


def faults(glyph):
    """[(contour index, edge node index, far node index, handle indices)]:
    each curve into a stem edge with a handle past it."""
    out = []
    for ci, contour in enumerate(glyph.contours):
        P = contour.points
        n = len(P)
        on = [i for i, p in enumerate(P) if p.type]
        if len(on) < 3:
            continue
        for k, i in enumerate(on):
            j = on[(k + 1) % len(on)]
            if P[j].type != "curve":
                continue
            offs = [m % n for m in range(i + 1, j if j > i else j + n)]
            if len(offs) != 2:
                continue
            # the stem's edge after the curve's end, or before its start
            for edge, far, beyond, line in ((j, i, on[(k + 2) % len(on)], P[on[(k + 2) % len(on)]].type == "line"),
                                           (i, j, on[k - 1], P[i].type == "line")):
                e, f, b = P[edge], P[far], P[beyond]
                if not line or abs(b.x - e.x) > 0.5 or abs(b.y - e.y) < STEM or abs(f.x - e.x) < AWAY:
                    continue
                side = 1 if f.x > e.x else -1
                past = [m for m in offs if (e.x - P[m].x) * side > PAST]
                if past:
                    out.append((ci, edge, far, offs, past))
    return out


def fair(font, names=None, bold=None):
    """font's glyphs (names, or all) faired so in place; their names.
    bold: the font is the Bold (make_bold, before it is named so)."""
    if not (font.info.styleName == "Bold" if bold is None else bold):
        return []
    changed = []
    for name in names or sorted(font.keys()):
        g = font[name]
        if not g.contours:
            continue
        for _ in range(4):
            found = faults(g)
            if not found:
                break
            for ci, edge, far, offs, past in found:
                P = g.contours[ci].points
                e, f = P[edge], P[far]
                for m in past:
                    h = P[m]
                    # the handle's own node: the one next to it on the curve
                    near_edge = (offs.index(m) == 1) == (edge == (offs[-1] + 1) % len(P))
                    if near_edge:
                        h.x = e.x
                    else:
                        t = (f.x - e.x) / (f.x - h.x)
                        h.x, h.y = e.x, f.y + t * (h.y - f.y)
            if name not in changed:
                changed.append(name)
    return changed


def finish(font):
    fair(font)


def main():
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("glyphs", nargs="*")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    for name in args.glyphs or sorted(font.keys()):
        for ci, edge, far, _offs, past in faults(font[name]):
            P = font[name].contours[ci].points
            print(f"{name:16} node {P[edge].x},{P[edge].y} from {P[far].x},{P[far].y}: "
                  + ", ".join(f"{P[m].x},{P[m].y}" for m in past))


if __name__ == "__main__":
    sys.exit(main())
