#!/usr/bin/env python3
"""Where the Bold stands in the references' range, family by family (F4, phase 7).

Reads what bold_measures.py --range wrote (build/quality/bold-measures-range.json;
--italic: bold-measures-italic.json) and puts every measure on the font's own
scale, so that fonts of different x-height and weight compare: lengths over the
style's stem (the median straight stem of the lowercase, of the capitals for
capitals and figures) or over the zone (x-height, cap height), areas over the
zone squared. Per family and measure: where Myia's Regular and Bold lie against
the references' range (0: inside; +6: 6 % above the highest; -9: 9 % below the
lowest), the gain bold over regular beside each reference's, and the letters
whose Bold lies outside by 3 % or more.

A Bold outside where the Regular is inside is the emboldening's doing; outside
in both is the design's. The range is a calibrated range, not a target.

    .venv/bin/python -I scripts/quality/bold_targets.py [--italic] [--chars nmhu]
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "quality"
OUTSIDE = 0.03
FAMILIES = {
    "arches": "nmhu", "r": "r", "bowls": "bdpq", "rounds": "oce", "s": "s", "a": "a", "g": "g",
    "balls": "acfryj", "straights": "il", "diagonals": "vwxyzk", "t f": "tf",
    "capital rounds": "OCGQ", "capital straights": "HINUEFLT", "capital bowls": "BDPR",
    "capital diagonals": "AVWXYZKM", "capital S J": "SJ", "figures": "0123456789",
}


def style_stem(chars, lower):
    stems = [m["stem"] for c, m in chars.items()
             if m.get("stem") and c.isascii() and c.isalpha() and c.islower() == lower]
    return statistics.median(stems) if stems else None


def ratios(style, c):
    """One character's measures on the style's own scale."""
    m = style["chars"].get(c)
    if not m:
        return {}
    lower = c.islower()
    zone = style["xHeight"] if lower else style["capHeight"]
    stem = style_stem(style["chars"], lower)
    r = {"advance/zone": m["advance"] / zone, "stem/zone": stem / zone,
         "advance/stem": m["advance"] / stem, "ink/stem": m["ink"] / stem}
    counters = m.get("counters") or []
    if counters:
        big = max(counters, key=lambda k: k["area"])
        r["counter width/stem"] = big["width"] / stem
        r["counter area/zone²"] = big["area"] / zone / zone
        r["white/zone²"] = m["white"] / zone / zone
        if big["aperture"] > 0:
            r["aperture/stem"] = big["aperture"] / stem
            r["aperture/counter width"] = big["aperture"] / big["width"]
        elif len(counters) == 1:
            r["round stroke/stem"] = (m["ink"] - big["width"]) / 2 / stem
    if "ball" in m:
        r["ball/stem"] = m["ball"] / stem
        r["ball/zone"] = m["ball"] / zone
    for name, v in (m.get("joins") or {}).items():
        r["join/stem " + name.split()[-1]] = v / stem
    return r


def position(value, refs):
    lo, hi = min(refs), max(refs)
    if lo <= value <= hi:
        return 0.0
    return value / lo - 1 if value < lo else value / hi - 1


def table(data, families):
    fonts = list(data)
    mine, refs = fonts[0], fonts[1:]
    lines = []
    for family, chars in families.items():
        rows = {}
        for c in chars:
            v = {(f, w): ratios(data[f][w], c) for f in fonts for w in ("regular", "bold")}
            for k in v[(mine, "bold")]:
                if any(k not in v[(f, w)] for f in fonts for w in ("regular", "bold")):
                    continue
                rb = [v[(f, "bold")][k] for f in refs]
                rr = [v[(f, "regular")][k] for f in refs]
                mb, mr = v[(mine, "bold")][k], v[(mine, "regular")][k]
                rows.setdefault(k, []).append(
                    (c, position(mr, rr), position(mb, rb), mb / mr, [b / r for b, r in zip(rb, rr)]))
        if not rows:
            continue
        lines += ["", f"## {family} ({chars})", "",
                  "| measure | Regular | Bold | gain | " + " | ".join(refs) + " | Bold outside |",
                  "|---|---|---|---|" + "---|" * len(refs) + "---|"]
        med = statistics.median
        for k, got in rows.items():
            outside = " ".join(f"{c} {b * 100:+.0f}" for c, _, b, _, _ in got if abs(b) >= OUTSIDE)
            gains = " | ".join(f"{med(g[4][i] for g in got):.2f}" for i in range(len(refs)))
            lines.append(f"| {k} | {med(g[1] for g in got) * 100:+.0f} | {med(g[2] for g in got) * 100:+.0f} "
                         f"| {med(g[3] for g in got):.2f} | {gains} | {outside} |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--italic", action="store_true", help="the Bold Italic over the Italic")
    ap.add_argument("--chars", help="one family of these characters only")
    args = ap.parse_args()
    stem = "bold-measures-italic" if args.italic else "bold-measures-range"
    src = OUT / f"{stem}.json"
    if not src.exists():
        sys.exit(f"{src} is missing: run scripts/quality/bold_measures.py "
                 + ("--italic" if args.italic else "--range"))
    data = json.loads(src.read_text())["measures"]
    families = {"chosen": args.chars} if args.chars else FAMILIES
    fonts = list(data)
    head = ["# Where the Bold stands in the references' range", "",
            f"{fonts[0]} against {', '.join(fonts[1:])}; from {src.relative_to(ROOT)}.",
            ("Regular, Bold: the family's median position against the references' range, in % "
             "(0 inside, + above the highest, - below the lowest). Gain: bold over regular, "
             "Myia's and each reference's. Bold outside: letters 3 % or more outside.")]
    out = OUT / ("bold-targets-italic.md" if args.italic else "bold-targets.md")
    out.write_text("\n".join(head + table(data, families)) + "\n")
    print(out, file=sys.stderr)


if __name__ == "__main__":
    main()
