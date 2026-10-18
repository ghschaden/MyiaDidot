"""Greek letter pairs against Greek references: the optical gap of each
frequent pair, shaped with kerning, relative to n n (as pairs.py does for the
mixed corpus, which has too little Greek).

    python scripts/quality/greek_pairs.py STYLE [--top N] [--tolerance T] [--json OUT]

The pairs: the most frequent letter pairs of the Greek UDHR texts
(build/udhr/, monotonic and polytonic; `make udhr` fetches them), accents
taken off (ά ἀ ᾶ are α), lowercase pairs and a capital before a lowercase.
The references with Greek: GFS Didot, EB Garamond (build/refs/), Libertinus
Serif and Charis SIL (installed fonts). Each pair's gap is printed against
the references' median and range, shifted by the style's own offset from
the same references on Latin (the English UDHR's frequent pairs): these
text faces set tighter or looser than a Didot overall, and Greek is to sit
as Myia's Latin does. A pair outside that range by more than the tolerance
(0.15 of the n n gap, as pairs.py) is flagged, with the kerning that would
bring it just inside, in font units.
"""

import argparse
import collections
import itertools
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

import uharfbuzz as hb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, REFDIR, ROOT, Face, runs

SYSTEM_REFS = {
    "Regular": ["/usr/share/fonts/libertinus/LibertinusSerif-Regular.otf",
                "~/texlive/2026/texmf-dist/fonts/truetype/SIL/charissil/CharisSIL-Regular.ttf"],
    "Italic": ["/usr/share/fonts/libertinus/LibertinusSerif-Italic.otf",
               "~/texlive/2026/texmf-dist/fonts/truetype/SIL/charissil/CharisSIL-Italic.ttf"],
    "Bold": ["/usr/share/fonts/libertinus/LibertinusSerif-Bold.otf",
             "~/texlive/2026/texmf-dist/fonts/truetype/SIL/charissil/CharisSIL-Bold.ttf"],
    "BoldItalic": ["/usr/share/fonts/libertinus/LibertinusSerif-BoldItalic.otf",
                   "~/texlive/2026/texmf-dist/fonts/truetype/SIL/charissil/CharisSIL-BoldItalic.ttf"],
}
PINNED = {"Regular": ["GFSDidot-Regular", "EBGaramond-Regular"], "Italic": ["EBGaramond-Italic"],
          "Bold": ["EBGaramond-Bold"], "BoldItalic": ["EBGaramond-BoldItalic"]}


def refs(style):
    paths = [str(REFDIR / f"{n}.ttf") for n in PINNED[style] if (REFDIR / f"{n}.ttf").exists()]
    paths += [str(Path(p).expanduser()) for p in SYSTEM_REFS[style] if Path(p).expanduser().exists()]
    return paths


def corpus():
    text = ""
    for name in ("udhr_ell_monotonic.xml", "udhr_ell_polytonic.xml"):
        path = ROOT / "build" / "udhr" / name
        if path.exists():
            text += " " + re.sub(r"<[^>]+>", " ", path.read_text())
    if not text.strip():
        sys.exit("no Greek UDHR text: make udhr")
    return text


def base(ch):
    """The letter without its accents (ά ἀ ᾶ -> α; ς stays)."""
    return unicodedata.normalize("NFD", ch)[0]


def greek(ch):
    return "Ͱ" <= ch <= "Ͽ" and ch.isalpha()


def frequent_pairs(top, text=None, keep=None):
    counts = collections.Counter()
    keep = keep or (lambda a, b: greek(a) and greek(b) and b.islower())
    for word in (text or corpus()).split():
        letters = [base(c) for c in word if c.isalpha()]
        for a, b in itertools.pairwise(letters):
            if keep(a, b):
                counts[a + b] += 1
    return [p for p, _ in counts.most_common(top)]


def gap(face, hbfont, pair, steps=30, depth=0.2):
    """The mean white between the two letters across the x-height (deep
    white clipped at depth), over the x-height."""
    buf = hb.Buffer()
    buf.add_str(pair)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True})
    pos = buf.glyph_positions
    if len(pos) != 2:
        return None
    pa, pb = face.path(pair[0]), face.path(pair[1])
    off, h = pos[0].x_advance + pos[1].x_offset, face.xh
    vals = []
    for i in range(steps):
        y = h * (i + 0.5) / steps
        ra, rb = runs(pa, y), runs(pb, y)
        vals.append(off + rb[0][0] - ra[-1][1] if ra and rb else None)
    real = [v for v in vals if v is not None]
    if not real:
        return None
    near = min(real)
    return sum(min(v, near + depth * h) if v is not None else near + depth * h for v in vals) / steps / h


def latin_offset(style, top=150):
    """The median of Myia's gaps less the references' on frequent English
    pairs: how much tighter (negative) or looser Myia's Latin sets than
    these references."""
    text = re.sub(r"<[^>]+>", " ", (ROOT / "build" / "udhr" / "udhr_eng.xml").read_text())
    pairs = frequent_pairs(top, text, lambda a, b: a.isascii() and b.isascii() and b.islower())
    res, myia, _ = measure(style, top, pairs)
    return statistics.median(v[myia] - statistics.median(x for k, x in v.items() if k != myia)
                             for v in res.values() if myia in v and len(v) >= 3)


def measure(style, top, pairs=None):
    fonts = [MYIA.format(style)] + refs(style)
    pairs = pairs or frequent_pairs(top)
    out, nn_units = {}, None
    for path in fonts:
        face = Face(path)
        hf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        nn = gap(face, hf, "nn")
        if path == fonts[0]:
            nn_units = nn * face.xh
        for p in pairs:
            if all(face.has(c) for c in p):
                g = gap(face, hf, p)
                if g is not None:
                    out.setdefault(p, {})[face.name] = g / nn
    return out, Face(fonts[0]).name, nn_units


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style")
    ap.add_argument("--top", type=int, default=150)
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--json")
    args = ap.parse_args()
    res, myia, nn_units = measure(args.style, args.top)
    shift = latin_offset(args.style)
    rows = []
    for p, v in res.items():
        if myia not in v or len(v) < 3:  # Myia and at least two references
            continue
        others = [x for k, x in v.items() if k != myia]
        lo, hi, med = (min(others) + shift, max(others) + shift, statistics.median(others) + shift)
        m = v[myia]
        off = (m - hi) if m > hi else (m - lo) if m < lo else 0.0
        # kerning that brings it inside by a little (0.05 of n n), in units
        kern = 0
        if abs(off) > args.tolerance:
            target = hi - 0.05 if m > hi else lo + 0.05
            kern = round((target - m) * nn_units)
        rows.append({"pair": p, "myia": round(m, 3), "median": round(med, 3), "lo": round(lo, 3),
                     "hi": round(hi, 3), "off": round(off, 3), "kern": kern})
    rows.sort(key=lambda r: r["off"])
    print(f"{args.style}: {len(rows)} frequent Greek pairs measured (n n gap {nn_units:.0f} units; "
          f"references shifted by the Latin's {shift:+.3f}); "
          f"{sum(1 for r in rows if r['kern'])} outside the references' range by more than {args.tolerance}")
    for r in rows:
        flag = f"  kern {r['kern']:+d}" if r["kern"] else ""
        print(f"  {r['pair']}  myia {r['myia']:.2f}  refs {r['median']:.2f} ({r['lo']:.2f}..{r['hi']:.2f}){flag}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
