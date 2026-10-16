"""evenness.py STYLE: grey value along lines of text. Each line is shaped
(HarfBuzz, kerning on), rendered at UPEM/40 px per unit... smoothed with a
window of an average letter, and the darkness profile's coefficient of
variation measured (lower: more even). Then each letter's mean deviation:
the darkness where it stands, against the line's mean."""
import statistics
import sys
from pathlib import Path

import numpy as np
import uharfbuzz as hb
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import MYIA, REFS, TEXTS

SCALE = 0.05  # px per unit
style = sys.argv[1]
fonts = [MYIA.format(style)] + REFS[style]


def line_profile(path, text):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    upem = tt["head"].unitsPerEm
    s = SCALE * 2048 / upem
    x = 0
    spans, placed = [], []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = order[info.codepoint]
        placed.append((g, x + pos.x_offset, pos.y_offset))
        spans.append((info.cluster, x, x + pos.x_advance))
        x += pos.x_advance
    xh = 0.43 * upem  # the band measured: baseline to about the x-height
    W = int(x * s) + 4
    H = int(upem * 1.0 * s)
    img = np.zeros((H, W))
    margin = int(0.6 * upem * s)
    for g, gx, gy in placed:
        pen = FreeTypePen(gs)
        gs[g].draw(pen)
        x0 = int(gx * s) - margin
        w = int(gs[g].width * s) + 2 * margin
        a = pen.array(width=w, height=H, transform=(s, 0, 0, s, gx * s - x0, (0.25 * upem + gy) * s), contain=False)
        lo, hi = max(0, x0), min(W, x0 + w)
        if hi > lo:
            img[:, lo:hi] = np.maximum(img[:, lo:hi], a[:, lo - x0:hi - x0])
    # darkness per column in the x-height band (rows: from top)
    band = img[int(H - (0.25 * upem + xh) * s):int(H - 0.25 * upem * s), :]
    col = band.mean(axis=0)
    win = max(3, int(0.5 * upem * s))  # about a letter
    k = np.ones(win) / win
    sm = np.convolve(col, k, mode="same")
    inner = sm[win:-win]
    cv = inner.std() / inner.mean()
    # per letter: smoothed darkness at its centre relative to the line's mean
    dev = {}
    m = inner.mean()
    for cl, x0, x1 in spans:
        c = int((x0 + x1) / 2 * s)
        if win <= c < len(sm) - win and cl < len(text) and text[cl] != " ":
            dev.setdefault(text[cl], []).append(sm[c] / m - 1)
    return cv, dev


print(f"{style}: coefficient of variation of the grey along a line (lower is more even)")
results = {}
for path in fonts:
    name = path.split("/")[-1].rsplit(".", 1)[0][:22]
    row, devs = [], {}
    tt = TTFont(path)
    cmap = tt.getBestCmap()
    for text in TEXTS.values():
        if not all(ord(c) in cmap for c in text if c != " "):
            row.append(None)
            continue
        cv, dev = line_profile(path, text)
        row.append(cv)
        for ch, v in dev.items():
            devs.setdefault(ch, []).extend(v)
    results[name] = (row, devs)
    print(f"  {name:22} " + "  ".join(f"{l} {v:.3f}" if v is not None else f"{l}  -   " for l, v in zip(TEXTS, row)))
# letters that sit darkest/lightest in Myia's lines, against how they sit in the references
myia = next(iter(results))
md = {ch: statistics.mean(v) for ch, v in results[myia][1].items() if len(v) >= 3}
rd = {}
for name, (_, devs) in list(results.items())[1:]:
    for ch, v in devs.items():
        if len(v) >= 3:
            rd.setdefault(ch, []).append(statistics.mean(v))
diffs = sorted(((md[ch] - statistics.median(rd[ch]), ch) for ch in md if ch in rd and len(rd[ch]) >= 3), reverse=True)
print("  darker than in the references (letter: Myia's local darkness minus the references' median):")
print("   ", "  ".join(f"{ch} {d:+.2f}" for d, ch in diffs[:12]))
print("  lighter:")
print("   ", "  ".join(f"{ch} {d:+.2f}" for d, ch in diffs[-12:]))
