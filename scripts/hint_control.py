"""hint_control.py UNHINTED.ttf HINTED.ttf [--control FILE]: ttfautohint with
a control file made for the font.

ttfautohint hints the vertical direction from the horizontal segments it
finds.  What it gets wrong in a Didot, mended here:

- Tips: where a stroke ends under a flat edge at the same height (M's and N's
  thick diagonal under the left serif, 1382; m.sc's at 996) it ends in a point
  or a flat of a few units that ttfautohint does not see as a segment, so it
  is interpolated and, when the serif is rounded to a whole pixel, pokes out
  above the cap height.  Such a tip is given the direction of the edge at its
  height (control `left`/`right`), so it joins that edge and moves with it.
- Ascenders: ttfautohint's Cyrillic has no ascender zone, so the Bulgarian
  forms with ascenders (ж ъ ь ю .loclBGR) would end between rows or above l's;
  Cyrillic letters reaching l's height are hinted as Latin (`latn dflt @`).
  The rest of the Cyrillic is better with its own zones.
- Greek: ttfautohint's Greek x-height is the mean of α ε ι ο π σ τ ω's tops;
  in the italics π σ τ rise above the x-height (Old Standard's), so the Greek
  zone rounds a row above the Latin one and ε ο ρ stand above x.  Myia's
  Greek is drawn to the Latin zones, so it may be hinted with them: both are
  tried and the one with fewer contours off the zones kept (the italics take
  the Latin zones, the uprights their own).
- Zones: outer contours whose flat top or bottom is on a zone but which end a whole
  pixel off the zone's row once hinted (quality/hint_zones.py: A's apex at
  1462 snapped to the ascender zone instead of O's) are moved onto it by
  `touch` deltas, at the sizes where both FreeType interpreters ask for the
  same shift.  Round extremes (one point) and contours ttfautohint leaves
  between rows are not moved: a delta would dent the one, and only shift the
  other's blur.
  Counter holes are excluded: a coincident height inside a bowl is not an
  alignment zone and must not trigger a touch delta.

ttfautohint drops what does not fit in a control line silently, so glyph
lists are cut into lines of ASSIGN names.

The first passes hint with the tips and style assignments only and measure; the second adds the
deltas, and what is still off the zones is printed.
"""
import argparse
import sys
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

from fontTools.ttLib import TTFont
from ttfautohint import ttfautohint
from ttfautohint.options import stem_width_mode

sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
from hint_zones import INTERPRETERS, letters, measure, summary  # noqa: E402

# ttfautohint-py (the library, pinned in uv.lock): grayscale natural, ClearType
# strong, blue zones for the win metrics, unassigned glyphs (brackets, bars,
# daggers) hinted as Latin rather than only scaled.
TTFAUTOHINT = dict(no_info=True, windows_compatibility=True, fallback_script="latn",
                   **stem_width_mode("nss"))
SHORT = 24  # a tip's flat is shorter than this
LONG = 40   # an edge's flat at least this long
ASSIGN = 8  # glyph names per style assignment line


def runs(points):
    """Runs of consecutive points (cyclic) at one height: [(first, last)] as
    positions in points, last may wrap past the end."""
    n = len(points)
    start = next((i for i in range(n) if points[i][1] != points[i - 1][1]), None)
    if start is None:
        return []
    out, i = [], start
    while i < start + n:
        j = i
        while j + 1 < start + n and points[(j + 1) % n][1] == points[i % n][1]:
            j += 1
        out.append((i, j))
        i = j + 1
    return out


def tips(glyf, name):
    """[(direction, point indices)]: tips that should join the edge at their
    height in the same contour.  A tip turns sharply (both neighbours steeper
    than 45 degrees): a counter's top tilted by a unit in the italic (Ѫ) is an
    edge ttfautohint already sees, and a one-point segment would break it."""
    g = glyf[name]
    if not g.numberOfContours or g.isComposite():
        return []
    coords, ends, flags = g.getCoordinates(glyf)
    out = []
    start = 0
    for end in ends:
        pts = [(coords[i][0], coords[i][1], flags[i] & 1, i) for i in range(start, end + 1)]
        n = len(pts)
        edges = defaultdict(list)  # y -> [(direction, xmin, xmax)]
        cands = []
        for a, b in runs(pts):
            run = [pts[k % n] for k in range(a, b + 1)]
            on = [p for p in run if p[2]]
            if not on:
                continue
            y = run[0][1]
            xs = [p[0] for p in run]
            if max(xs) - min(xs) >= LONG and len(on) >= 2:
                edges[y].append(("left" if on[-1][0] < on[0][0] else "right", min(xs), max(xs)))
            elif max(xs) - min(xs) < SHORT:
                before, after = pts[(a - 1) % n], pts[(b + 1) % n]
                steep = all(abs(q[1] - y) > abs(q[0] - p[0])
                            for q, p in ((before, run[0]), (after, run[-1])))
                if (before[1] - y) * (after[1] - y) > 0 and steep:
                    cands.append((y, min(xs), max(xs), [p[3] for p in on]))
        for y, x0, x1, idx in cands:
            if edges.get(y):
                near = min(edges[y], key=lambda e: max(e[1] - x1, x0 - e[2], 0))
                out.append((near[0], sorted(idx)))
        start = end + 1
    return out


def ppem_list(ppems):
    ppems = sorted(ppems)
    out, i = [], 0
    while i < len(ppems):
        j = i
        while j + 1 < len(ppems) and ppems[j + 1] == ppems[j] + 1:
            j += 1
        out.append(str(ppems[i]) if i == j else f"{ppems[i]}-{ppems[j]}")
        i = j + 1
    return ", ".join(out)


def tip_lines(tt):
    glyf = tt["glyf"]
    return [f"{name} {direction} {', '.join(map(str, idx))}"
            for name in tt.getGlyphOrder() for direction, idx in tips(glyf, name)]


def script_letters(tt, script):
    """Letters of a script (by their character's name), small caps left out:
    ttfautohint hints those in its smcp/c2sc styles, with their own zones."""
    by_name = {}
    for code, name in tt.getBestCmap().items():
        by_name.setdefault(name, code)
    out = []
    for name in sorted(letters(tt)):
        code = by_name.get(name.split(".")[0])
        if ".sc" not in name and code is not None \
                and unicodedata.name(chr(code), "").startswith(script):
            out.append(name)
    return out


def assign(names):
    return [f"latn dflt @ {', '.join(names[i:i + ASSIGN])}" for i in range(0, len(names), ASSIGN)]


def ascender_names(tt):
    """Cyrillic letters with a contour at l's height, to be hinted as Latin."""
    glyf = tt["glyf"]
    if "l" not in tt.getGlyphOrder():
        return []
    height = glyf["l"].yMax
    return [n for n in script_letters(tt, "CYRILLIC")
            if glyf[n].numberOfContours > 0 and glyf[n].yMax == height]


def off_zone(path):
    return sum(sum(summary(measure(path, interpreter=v)).values()) for v in INTERPRETERS)


def smallcap_tip_lines(tt):
    """Approved Italic tip adjustment, discovering indices from the outline."""
    if tt["name"].getDebugName(2) != "Italic":
        return []
    glyf = tt["glyf"]
    lines = []
    for name in ("v.sc", "w.sc", "uni0475.sc", "uni2C73.sc"):
        coords, _, flags = glyf[name].getCoordinates(glyf)
        indices = [i for i, (_, y) in enumerate(coords) if y == glyf["O"].yMin and flags[i] & 1]
        if not indices:
            raise ValueError(f"{name}: approved small-cap tip no longer meets O's bottom zone")
        lines.append(f"{name} touch {', '.join(map(str, indices))} yshift 0.5 @ 30, 32")
    return lines


def delta_lines(path):
    """touch deltas for the contours off their zone, where both interpreters
    want the same shift of the contour's flat; and what is left unmended."""
    shifts = {}
    for version in INTERPRETERS:
        for ppem, items in measure(path, interpreter=version).items():
            for n, _side, _z, _v, row, flat, idx in items:
                if len(idx) < 2:
                    continue
                shift = round((row - flat) * 8) / 8
                shifts.setdefault((n, tuple(idx), ppem), {})[version] = shift
    grouped = defaultdict(list)
    left = []
    for (n, idx, ppem), by in shifts.items():
        s = set(by.values())
        if len(by) == len(INTERPRETERS) and len(s) == 1 and abs(next(iter(s))) == 1:
            grouped[(n, idx, next(iter(s)))].append(ppem)
        else:
            left.append(f"{n} {ppem}px {by}")
    lines = [f"{n} touch {', '.join(map(str, idx))} yshift {s:g} @ {ppem_list(p)}"
             for (n, idx, s), p in sorted(grouped.items())]
    return lines, left


def autohint(src, dst, control):
    ttfautohint(in_file=str(src), out_file=str(dst), control_file=str(control), **TTFAUTOHINT)


def hint(unhinted, hinted, control=None):
    """Hint unhinted into hinted (control file kept at control if given);
    returns what was done, for the report."""
    tt = TTFont(unhinted)
    with tempfile.TemporaryDirectory() as tmp:
        control = Path(control) if control else Path(tmp) / "control.txt"
        control.parent.mkdir(parents=True, exist_ok=True)
        tiplines = tip_lines(tt)
        ascenders = ascender_names(tt)
        tried = {}
        for greek in (False, True):
            names = ascenders + (script_letters(tt, "GREEK") if greek else [])
            head = ("# tips\n" + "".join(f"{x}\n" for x in tiplines)
                    + "# hinted with the Latin zones\n" + "".join(f"{x}\n" for x in assign(names)))
            control.write_text(head)
            first = Path(tmp) / f"first-{greek}.ttf"
            autohint(unhinted, first, control)
            tried[greek] = off_zone(first)
            if not greek or tried[True] < tried[False]:
                chosen = (greek, head, first)
        greek, head, first = chosen
        deltas, left = delta_lines(first)
        overrides = ""
        if tt["name"].getDebugName(2) == "Regular" and "uni1FBE" in tt.getGlyphOrder():
            # Approved 2026-10-26: the serifed adscript aligns with x in
            # Latin zones. Append after other assignments, as in the proof.
            overrides = "# prosgegrammeni: Latin x-height\nlatn dflt @ uni1FBE\n"
        tip_adjustments = smallcap_tip_lines(tt)
        if tip_adjustments:
            overrides += "# approved small-cap bottom tips\n" + "\n".join(tip_adjustments) + "\n"
        control.write_text(head + "# zones\n" + "".join(f"{x}\n" for x in deltas) + overrides)
        autohint(unhinted, hinted, control)
    return dict(tips=len(tiplines), greek_latin=greek, tried=tried, deltas=len(deltas), left=len(left))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("unhinted")
    ap.add_argument("hinted")
    ap.add_argument("--control", help="keep the control file here")
    args = ap.parse_args()
    r = hint(args.unhinted, args.hinted, args.control)
    print(f"{Path(args.hinted).name}: {r['tips']} tips, Greek with {'Latin' if r['greek_latin'] else 'its own'} "
          f"zones (off-zone {r['tried'][False]} with its own, {r['tried'][True]} with Latin), "
          f"{r['deltas']} deltas; not mended by deltas: {r['left']}")
    for version in INTERPRETERS:
        per = summary(measure(args.hinted, interpreter=version))
        print(f"  v{version} still off-zone: {sum(per.values())} in {len(per)} contours: "
              + " ".join(f"{k}({c})" for k, c in per.most_common(12)))


if __name__ == "__main__":
    main()
