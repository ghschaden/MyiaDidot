"""The two pair measures taken apart: which choice makes them disagree.

    python scripts/quality/pair_measures.py STYLE [--pairs "Rv Wv ..."] [--out FILE]

docs/claude/spacing.md, "One measure for Latin kerning": quality/pairs.py's
gap and italic_kerning's share differ in three choices of construction and
in the verdict. Here one measure is computed with each choice switched
alone, on the built font and the references, so that a pair's
disagreement can be laid to one of them:

    over   the pair's white over n n ("nn"), or over its cases' own
           rhythm: n n, H H, H n, n H ("case")
    rows   baseline to x-height ("xh"), or the rows where the two inks
           face each other ("facing")
    near   the near white the depth is cut from: the nearest row ("min"),
           or the row at italic_kerning's QUANTILE ("q")

    gap      nn, xh, min        (pairs.py's choices, on the profiles' rows)
    +over    case, xh, min
    +rows    nn, facing, min
    +near    nn, xh, q
    share    case, facing, q    (checked against Built.share)

Each against the range of the share's five references (off: how far past
the range, in per cent of the nearer edge; 0 inside), and the gap once
more as pairs.py judges it: its own references, 0.15 n-gaps of margin.
First the confirmation the "over" row asks for: H n and H H over n n in
the gap's measure, per font.
"""

import argparse
import sys
import unicodedata
from pathlib import Path

import numpy as np
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
sys.path.insert(0, str(ROOT / "scripts"))
from common import MYIA, REFS  # noqa: E402
from italic_kerning import DEPTH, MIN_ROWS, QUANTILE, RHYTHM, Built, references  # noqa: E402
from kern_coverage import YS  # noqa: E402

VARIANTS = {"gap": ("nn", "xh", "min"), "+over": ("case", "xh", "min"),
            "+rows": ("nn", "facing", "min"), "+near": ("nn", "xh", "q"),
            "share": ("case", "facing", "q")}
DEFAULT = {"Regular": "Rv Rw Ry Wv Ww RO RQ 7. 1. A“ A\" Tu Tp Tz Tm Tn Tr",
           "Bold": "Rv Rw Ry Wv Ww RO RQ 7. 1. A“ A\" Tu Tp Tz Tm Tn Tr",
           "Italic": "fr Rv Wv RO Tu", "BoldItalic": "fr Rv Wv RO Tu"}
MARGIN = 0.15  # pairs.py's: n-gaps past its references' range


def white(font, text, rows, near):
    """The pair's white as set (kerning on) by the two choices, or None."""
    if any(ord(c) not in font.cmap for c in text):
        return None
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font.hb, buf, {"kern": True, "liga": False})
    if len(buf.glyph_infos) != 2:
        return None
    order = font.tt.getGlyphOrder()
    a, b = (order[i.codepoint] for i in buf.glyph_infos)
    pos = buf.glyph_positions
    ra, lb = font.prof[a][1], font.prof[b][0]
    ina, inb = np.isfinite(ra), np.isfinite(lb)
    if rows == "xh":
        band = (YS > 0) & (YS < font.info.xHeight)
    else:
        if not ina.any() or not inb.any():
            return None
        band = (YS >= max(YS[ina].min(), YS[inb].min())) & (YS <= min(YS[ina].max(), YS[inb].max()))
    facing = band & ina & inb
    if facing.sum() < (1 if rows == "xh" else MIN_ROWS):
        return None
    d = (lb + (pos[0].x_advance + pos[1].x_offset) * font.scale - ra)[facing]
    first = float(d.min()) if near == "min" else float(np.quantile(d, QUANTILE))
    limit = first + DEPTH * font.info.xHeight
    return float((np.minimum(d, limit).sum() + limit * (band.sum() - facing.sum())) / band.sum())


def value(font, text, variant):
    over, rows, near = VARIANTS[variant]
    cases = tuple("lower" if unicodedata.category(c) == "Ll" else "upper" for c in text)
    base = "nn" if over == "nn" else "".join(RHYTHM[cases])
    w, r = white(font, text, rows, near), white(font, base, rows, near)
    return None if w is None or not r else w / r


def off(v, got, margin=0.0):
    """Past the range in per cent of its nearer edge (with a margin: in
    the measure's own unit); 0 inside."""
    lo, hi = min(got) - margin, max(got) + margin
    if lo <= v <= hi:
        return 0.0
    edge = hi if v > hi else lo
    return (v - edge) if margin else 100 * (v - edge) / abs(edge)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("style")
    ap.add_argument("--pairs")
    ap.add_argument("--out")
    a = ap.parse_args()
    pairs = (a.pairs or DEFAULT[a.style]).split()
    myia = Built(MYIA.format(a.style))
    five = {Path(p).stem: Built(str(p)) for p in references(a.style)}
    own = {Path(p).stem: five.get(Path(p).stem) or Built(p) for p in REFS[a.style]}
    lines = [f"# Pair measures taken apart: {a.style}", "",
             "The capitals' rhythm over n n in the gap's measure (nn, xh, min):", "",
             "| font | H n | H H |", "|---|---|---|"]
    for name, f in [("Myia", myia), *sorted({**five, **own}.items())]:
        lines.append(f"| {name} | {value(f, 'Hn', 'gap'):.3f} | {value(f, 'HH', 'gap'):.3f} |")
    lines += ["", ("Per pair and variant: Myia's value, the five references' range, off in per cent "
              "(+ looser than the range, - tighter, 0 inside; n: references that have the pair)."), "",
              "| pair | " + " | ".join(VARIANTS) + f" | gap as pairs.py (±{MARGIN}) |",
              "|---|" + "---|" * (len(VARIANTS) + 1)]
    for text in pairs:
        cells = []
        for variant in VARIANTS:
            v = value(myia, text, variant)
            got = [x for x in (value(f, text, variant) for f in five.values()) if x is not None]
            if variant == "share":
                s = myia.share(text)
                assert (v is None) == (s is None) and (v is None or abs(v - s) < 1e-9), (text, v, s)
            if v is None or len(got) < 3:
                cells.append("none" if v is None else f"{v:.2f} (n {len(got)})")
                continue
            cells.append(f"{v:.2f} [{min(got):.2f}, {max(got):.2f}] **{off(v, got):+.0f}**")
        v = value(myia, text, "gap")
        got = [x for x in (value(f, text, "gap") for f in own.values()) if x is not None]
        if v is None or len(got) < 3:  # pairs.py: four fonts with Myia
            cells.append("none")
        else:
            cells.append(f"{v:.2f} [{min(got):.2f}, {max(got):.2f}] **{off(v, got, MARGIN):+.2f}**")
        lines.append(f"| {text} | " + " | ".join(cells) + " |")
    out = Path(a.out) if a.out else ROOT / "build" / "quality" / f"pair-measures-{a.style}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(out)


if __name__ == "__main__":
    sys.exit(main())
