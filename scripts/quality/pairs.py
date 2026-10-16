"""pairs.py STYLE: the optical gap (white between the two letters across the
x-height, deep white clipped) of frequent letter pairs, shaped with kerning,
relative to n n; Myia against the references' median for the same pair."""
import collections
import itertools
import statistics
import sys
from pathlib import Path

import uharfbuzz as hb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, REFS, ROOT, TEXTS, Face, runs

style = sys.argv[1]
corpus = " ".join(TEXTS.values()) + " " + (ROOT / "proofs" / "textpages.tex").read_text()
big = collections.Counter()
for w in corpus.split():
    w = "".join(c for c in w if c.isalpha())
    for a, b in itertools.pairwise(w):
        big[a + b] += 1
pairs = [p for p, _ in big.most_common(300)]


def gap(face, hbfont, pair, steps=30, depth=0.2):
    buf = hb.Buffer(); buf.add_str(pair); buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True})
    pos = buf.glyph_positions
    if len(pos) != 2:
        return None
    a, b = pair
    pa, pb = face.path(a), face.path(b)
    off = pos[0].x_advance
    h = face.xh
    vals = []
    for i in range(steps):
        y = h * (i + 0.5) / steps
        ra, rb = runs(pa, y), runs(pb, y)
        if not ra or not rb:
            vals.append(None); continue
        vals.append(off + rb[0][0] - ra[-1][1])
    real = [v for v in vals if v is not None]
    if not real:
        return None
    near = min(real)
    return sum(min(v, near + depth * h) if v is not None else near + depth * h for v in vals) / steps / h


fonts = [MYIA.format(style)] + REFS[style]
res = {}
for path in fonts:
    face = Face(path)
    hf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    if not face.has("n"):
        continue
    nn = gap(face, hf, "nn")
    for p in pairs:
        if all(face.has(c) for c in p):
            g = gap(face, hf, p)
            if g is not None:
                res.setdefault(p, {})[face.name] = g / nn
myia = Face(fonts[0]).name
rows = []
for p, v in res.items():
    if myia in v and len(v) >= 4:
        refs = [x for k, x in v.items() if k != myia]
        rows.append((v[myia] - statistics.median(refs), p, v[myia], statistics.median(refs), min(refs), max(refs)))
rows.sort()
spread = statistics.pstdev([r[0] for r in rows])
print(f"{style}: {len(rows)} frequent pairs; Myia's gap relative to n n minus the references' median: sd {spread:.2f}")
print("  tightest against the references:", "  ".join(f"{p} {d:+.2f}" for d, p, *_ in rows[:15]))
print("  loosest:", "  ".join(f"{p} {d:+.2f}" for d, p, *_ in rows[-15:]))
out = [r for r in rows if r[2] < r[4] - 0.15 or r[2] > r[5] + 0.15]
print(f"  outside the references' range by more than 0.15 n-gaps: {len(out)}:", " ".join(r[1] for r in out))
