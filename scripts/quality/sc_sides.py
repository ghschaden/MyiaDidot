"""Each small cap's sides against references with small caps: the optical
gap (capsc_pairs.Font.gap) of the letter after and before h.sc (straight)
and o.sc (round), relative to h.sc h.sc, set by smcp from lowercase text.

    python scripts/quality/sc_sides.py STYLE [--myia OTF] [--letters abc...]
        [--tolerance T] [--caps]

Prints per letter and side Myia's value, the references' range and median,
marking those outside it by more than the tolerance (0.10 of h.sc h.sc).
A side is "L" (the letter's left: h X, o X) or "R" (X h, X o). The value
in units (--units) is how far Myia's side would move to reach the nearer
end of the range, measured against h.sc h.sc's gap.
"""

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capsc_pairs import Font, refs
from common import MYIA

LETTERS = "abcdefghijklmnopqrstuvwxyz"


CAPS = False


def pair(font, text):
    if CAPS:
        text = text.upper()
    if not all(ord(c) in font.cmap for c in text):
        return None
    names, adv = font.shape(text)
    if len(names) != 2 or (not CAPS and any(n == font.cmap[ord(c)] for n, c in zip(names, text))):
        return None
    return names, adv


def measure(font, letters):
    hh = pair(font, "hh")
    if not hh:
        return None
    h = font.top(hh[0][0])
    norm = font.gap(hh[0], hh[1][0], h)
    out = {}
    for x in letters:
        for side, texts in (("L", ("h" + x, "o" + x)), ("R", (x + "h", x + "o"))):
            for nb, t in zip("ho", texts):
                got = pair(font, t)
                if got:
                    g = font.gap(got[0], got[1][0], h)
                    if g is not None:
                        out[(x, side, nb)] = g / norm
    return out, norm


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style")
    ap.add_argument("--myia")
    ap.add_argument("--letters", default=LETTERS)
    ap.add_argument("--tolerance", type=float, default=0.10)
    ap.add_argument("--all", action="store_true", help="print every row, not only those outside")
    ap.add_argument("--caps", action="store_true", help="the capitals instead, beside H and O (no smcp)")
    args = ap.parse_args()
    global CAPS
    CAPS = args.caps
    myia = Font(str(args.myia or MYIA.format(args.style)))
    mine, norm = measure(myia, args.letters)
    others = {}
    for p in refs(args.style):
        f = Font(p)
        got = measure(f, args.letters)
        if got:
            others[f.name] = got[0]
    print(f"{args.style}: h.sc h.sc gap {norm:.0f} units; references: {', '.join(others)}")
    print(f"{'':6}{'myia':>6} {'lo':>6} {'med':>6} {'hi':>6}  units  refs")
    n_out = 0
    for key in sorted(mine, key=lambda k: (k[0], k[1], k[2])):
        vals = [v[key] for v in others.values() if key in v]
        if len(vals) < 2:
            continue
        m, lo, hi, med = mine[key], min(vals), max(vals), statistics.median(vals)
        off = m < lo - args.tolerance or m > hi + args.tolerance
        n_out += off
        if off or args.all:
            edge = lo if m < lo else hi if m > hi else m
            x, side, nb = key
            label = f"{nb}{x}" if side == "L" else f"{x}{nb}"
            print(f"{x} {side} {label:3}{m:6.2f} {lo:6.2f} {med:6.2f} {hi:6.2f} {round((edge - m) * norm):+6d}  "
                  f"{len(vals)}{'  <' if m < lo else '  >' if m > hi else ''}")
    print(f"{n_out} sides outside the references' range by more than {args.tolerance}")


if __name__ == "__main__":
    sys.exit(main())
