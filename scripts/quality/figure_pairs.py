"""figure_pairs.py STYLE [--osf] [--font PATH]: the figures' spacing against
the references, as pairs and as sides.

Each pair (figure-figure, figure against . , : ; – / ( ) % $) is shaped
with proportional figures and kerning, lining (or old-style with --osf),
and its optical gap measured as pairs.py does (white between the two
shapes over the band where both have ink, deep white clipped at 0.2 of
the cap height), relative to H H (n n with --osf) and then to the font's
own median figure-figure gap, so that the figures' rhythm and the pairs
within it are judged apart. The side changes that bring Myia's pairs to
the references' median are fitted by least squares over the 100 figure
pairs (each pair = the left figure's right side + the right figure's
left side, their sum held at 0); what the sides cannot explain is left
for kerning. The basis of data_regular.FIGURE_SIDES (2026-11-14).

A second fit, absolute: each pair's gap over the cap height against the
references' median (the rhythm included; not over H H, which a style's
loose capitals would pass on to its figures), over the figure pairs and the figures on
both sides of H O n o, without the sum held. Only it sees where a figure
stands in its advance (a figure-figure pair has one figure's right side
with the other's left, so a shift of all of them cancels): in the
italics the figures stood right of where the letters stand, 0 o and 1 H
tight, H 1 loose (2026-11-14). The basis of data_italic's and
data_bold_italic's figure tables.

Output: build/quality/figure-pairs-STYLE[-osf].txt; a summary on stdout.
"""
import argparse
import collections
import statistics
import sys
from pathlib import Path

import numpy as np
import pathops
import uharfbuzz as hb
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, OUT, REFDIR, REFS, Face, band  # noqa: E402

FIG = "0123456789"
LETTERS = "HOno"  # the absolute fit's anchors beside the figures
OSF_REFS = {"Regular": ["BodoniModa-11-Regular.ttf", "EBGaramond-Regular.ttf", "GFSDidot-Regular.ttf",
                        "LibertinusSerif-Regular.otf"]}


def gpath(face, gid, cache):
    if gid not in cache:
        p = pathops.Path()
        face.gs[face.f.getGlyphOrder()[gid]].draw(
            TransformPen(p.getPen(glyphSet=face.gs), (1, 0, -face.slant, 1, 0, 0)))
        cache[gid] = pathops.simplify(p)
    return cache[gid]


def runs(path, y):
    q = band(path, y - 0.5, y + 0.5)
    return sorted((c.bounds[0], c.bounds[2]) for c in q.contours)


def gap(face, hbfont, text, feat, cache, zone=None, steps=30, depth=0.2):
    """Mean white between the two glyphs of text, in font units."""
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(hbfont, buf, feat)
    if len(buf.glyph_infos) != 2:
        return None
    pa, pb = (gpath(face, i.codepoint, cache) for i in buf.glyph_infos)
    off = buf.glyph_positions[0].x_advance
    if not pa.bounds or not pb.bounds:
        return None
    y0, y1 = zone or (max(pa.bounds[1], pb.bounds[1], 0), min(pa.bounds[3], pb.bounds[3]))
    if y1 - y0 < 20:
        return None
    vals = []
    for i in range(steps):
        y = y0 + (y1 - y0) * (i + 0.5) / steps
        ra, rb = runs(pa, y), runs(pb, y)
        vals.append(None if not ra or not rb else off + rb[0][0] - ra[-1][1])
    real = [v for v in vals if v is not None]
    if not real:
        return None
    near, lim = min(real), depth * face.cap
    return sum(min(v, near + lim) if v is not None else near + lim for v in vals) / steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("style")
    ap.add_argument("--osf", action="store_true")
    ap.add_argument("--font", help="Myia's font to measure (default fonts/otf)")
    a = ap.parse_args()
    feat = {"kern": True, "pnum": True, ("onum" if a.osf else "lnum"): True}
    if a.osf:
        refs = [str(REFDIR / n) for n in OSF_REFS.get(a.style, [])]
    else:
        extra = [REFDIR / f"CharisSIL-{a.style}.ttf", REFDIR / f"LibertinusSerif-{a.style}.otf"]
        refs = REFS[a.style] + [str(p) for p in extra if p.exists()]
    fonts = [a.font or MYIA.format(a.style)] + refs
    pairs = [x + y for x in FIG for y in FIG]
    pairs += [x + p for x in FIG for p in ".,:;–/)%"] + [p + x for x in FIG for p in ".,–/($"]
    pairs += [x + c for x in FIG for c in LETTERS] + [c + x for x in FIG for c in LETTERS]

    res, cal, caps, names = {}, {}, {}, []
    for path in fonts:
        face = Face(path)
        hf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        cache = {}
        name = face.name if path != fonts[0] else "Myia"
        names.append(name)
        caps[name] = face.cap
        cal[name] = gap(face, hf, "nn" if a.osf else "HH", feat, cache,
                        zone=(0, face.xh if a.osf else face.cap))
        for p in pairs:
            if all(face.has(c) for c in p):
                g = gap(face, hf, p, feat, cache)
                if g is not None:
                    res.setdefault(p, {})[name] = g / cal[name]
    fm = {n: statistics.median(res[p][n] for p in res if p[0] in FIG and p[1] in FIG and n in res[p])
          for n in names}
    unit = fm["Myia"] * cal["Myia"]
    rows = []
    for p, v in res.items():
        refs_v = [v[n] / fm[n] for n in names[1:] if n in v]
        if "Myia" in v and len(refs_v) >= min(4, len(names) - 1):
            m, med = v["Myia"] / fm["Myia"], statistics.median(refs_v)
            rows.append((p, m, med, min(refs_v), max(refs_v), round((med - m) * unit)))
    ff = [r for r in rows if r[0][0] in FIG and r[0][1] in FIG]
    col = {("R", c): i for i, c in enumerate(FIG)} | {("L", c): 10 + i for i, c in enumerate(FIG)}
    A, y = np.zeros((len(ff) + 1, 20)), np.zeros(len(ff) + 1)
    for k, r in enumerate(ff):
        A[k, col["R", r[0][0]]] = A[k, col["L", r[0][1]]] = 1
        y[k] = r[5]
    A[-1, :] = 1
    x = np.linalg.lstsq(A, y, rcond=None)[0]
    side = {k: x[i] for k, i in col.items()}

    kind = "old-style (onum)" if a.osf else "lining"
    cal_name = "n n" if a.osf else "H H"
    lines = [f"{a.style}, {kind} proportional figures; Myia: {fonts[0]}",
             f"figure rhythm (median figure-figure gap / {cal_name}): Myia {fm['Myia']:.2f}, references "
             + ", ".join(f"{n} {fm[n]:.2f}" for n in names[1:])
             + f" (median {statistics.median(fm[n] for n in names[1:]):.2f})",
             "", "side changes to the references' median (units, + = more space):"]
    lines += [f"  {c}: left {side['L', c]:+5.0f}   right {side['R', c]:+5.0f}" for c in FIG]
    resid = sorted((r[5] - side["R", r[0][0]] - side["L", r[0][1]], r[0]) for r in ff)
    rms0 = np.sqrt(np.mean(y[:-1] ** 2))
    rms1 = np.sqrt(np.mean([d ** 2 for d, _ in resid]))
    lines += [f"rms off the median: {rms0:.0f} as set, {rms1:.0f} after the side changes",
              "figure pairs the sides leave beyond 40 units: "
              + " ".join(f"{p}{d:+.0f}" for d, p in resid if abs(d) > 40), "",
              "punctuation pairs after the side changes (units to add):"]
    by = collections.defaultdict(list)
    for p, *_, k in rows:
        if p[0] in LETTERS or p[1] in LETTERS:
            continue
        if p[0] in FIG and p[1] not in FIG:
            by[f"{p[1]} after"].append((p, round(k - side["R", p[0]])))
        elif p[1] in FIG and p[0] not in FIG:
            by[f"{p[0]} before"].append((p, round(k - side["L", p[1]])))
    for key, lst in sorted(by.items()):
        lst.sort(key=lambda t: t[1])
        lines.append(f"  {key}: median {statistics.median(v for _, v in lst):+.0f}   "
                     + " ".join(f"{p}{v:+d}" for p, v in lst))
    # the absolute fit: gaps over H H, no sum held
    ab = []
    for p, v in res.items():
        refs_v = [v[n] for n in names[1:] if n in v]
        if "Myia" in v and len(refs_v) >= min(4, len(names) - 1) and (
                (p[0] in FIG and p[1] in FIG) or (p[0] in FIG and p[1] in LETTERS) or (p[0] in LETTERS and p[1] in FIG)):
            # over the cap height: a style whose own H H is loose (the Bold
            # Italic's, 0.32 of it against the references' 0.22-0.25) would
            # loosen its figures with it
            refs_c = [v[n] * cal[n] / caps[n] for n in names[1:] if n in v]
            ab.append((p, round((statistics.median(refs_c) - v["Myia"] * cal["Myia"] / caps["Myia"]) * caps["Myia"])))
    A, y = np.zeros((len(ab), 20)), np.zeros(len(ab))
    for k, (p, d) in enumerate(ab):
        if p[0] in FIG:
            A[k, col["R", p[0]]] = 1
        if p[1] in FIG:
            A[k, col["L", p[1]]] = 1
        y[k] = d
    x = np.linalg.lstsq(A, y, rcond=None)[0]
    absolute = {k: x[i] for k, i in col.items()}
    left = sorted((d - sum(absolute.get((s, c), 0) for s, c in (("R", p[0]), ("L", p[1]))), p) for p, d in ab)
    lines += ["", (f"absolute fit (gaps over the cap height to the references' median, figures and {' '.join(LETTERS)} "
                   "beside them; units, + = more space):")]
    lines += [f"  {c}: left {absolute['L', c]:+5.0f}   right {absolute['R', c]:+5.0f}" for c in FIG]
    lines += [(f"rms off the median: {np.sqrt(np.mean(y ** 2)):.0f} as set, "
               f"{np.sqrt(np.mean([d ** 2 for d, _ in left])):.0f} after the side changes"),
              "pairs the sides leave beyond 40 units: " + " ".join(f"{p}{d:+.0f}" for d, p in left if abs(d) > 40)]
    lines += ["", "pair\tMyia\tref median\tmin\tmax\tunits to median (gaps / the font's figure median)"]
    lines += [f"{p}\t{m:.2f}\t{med:.2f}\t{lo:.2f}\t{hi:.2f}\t{k:+d}" for p, m, med, lo, hi, k in
              sorted(rows, key=lambda r: -abs(r[5]))]
    out = OUT / f"figure-pairs-{a.style}{'-osf' if a.osf else ''}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:lines.index("punctuation pairs after the side changes (units to add):")]))
    i = next(k for k, t in enumerate(lines) if t.startswith("absolute fit"))
    print("\n".join(lines[i:i + 13]))
    print(f"full report: {out}")


if __name__ == "__main__":
    main()
