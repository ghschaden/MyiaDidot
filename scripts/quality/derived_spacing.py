"""Derived letters' spacing against their base letter's, in Myia and in the
references.

    python scripts/quality/derived_spacing.py STYLE [--font OTF] [--tolerance T]
        [--json OUT]

A letter derive.py makes by adding to a base (a hook, tail, curl, attached
piece: ɗ from d, ƴ from y, Ɓ from B) should sit beside its neighbours about
as the references set it, measured from the base: ɗ a against d a. For each
side and neighbour (n o a, capitals H O) the optical gap of the pair (as
greek_pairs.gap, over the x-height or for capitals the cap height, shaped
with kerning, in n n gaps) less the base's is taken in Myia and in every
reference that has both letters (Charis, Libertinus, EB Garamond, the
Didots). A side whose median difference lies outside the references' range
by more than the tolerance (0.15 of the n n gap) is flagged, with the
sidebearing change that brings it to the references' median, in font units
(these are construction faults, not tuned pairs: derive.SPACING).

Hooks that overhang their advance can collide with a tall neighbour that
the optical gap does not see (ɗ l, H Ɓ): every pair with a tall neighbour
(l h k b d ! ? ) ], capitals H T l) whose least white over the whole height
is under CLEAR units and under the base's is listed (clear), for kerning
(scripts/kern_clear.py PAIRS).
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

import uharfbuzz as hb

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import derive
from common import MYIA, REFS, Face, runs
from greek_pairs import SYSTEM_REFS

OPS = ("hook", "curl", "attach", "graft", "tail", "descend", "lower", "unserif", "ezh", "esh")
NEIGHBOURS = {False: "noa", True: "HO"}
TALL = {False: ("lhkbd!?)]", "lhkbdf([!"), True: ("HTl!?)]", "HTl([")}  # (after it, before it)
CLEAR = 40
DEPTH = 0.2


class Font:
    def __init__(self, path):
        self.face = Face(path)
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.name = self.face.name
        self.nn = None
        self.nn = self.gap("nn", self.face.xh)

    def shaped(self, pair):
        buf = hb.Buffer()
        buf.add_str(pair)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True})
        pos = buf.glyph_positions
        return pos[0].x_advance + pos[1].x_offset if len(pos) == 2 else None

    def rows(self, pair, ys):
        off = self.shaped(pair)
        if off is None:
            return []
        pa, pb = self.face.path(pair[0]), self.face.path(pair[1])
        out = []
        for y in ys:
            ra, rb = runs(pa, y), runs(pb, y)
            out.append(off + rb[0][0] - ra[-1][1] if ra and rb else None)
        return out

    def gap(self, pair, h, steps=30):
        """Mean white across 0..h, deep white clipped at DEPTH x h beyond the
        nearest; in units (n n's gap: self.nn)."""
        vals = self.rows(pair, [h * (i + 0.5) / steps for i in range(steps)])
        real = [v for v in vals if v is not None]
        if not real:
            return None
        near = min(real)
        cap = near + DEPTH * h
        return sum(min(v, cap) if v is not None else cap for v in vals) / steps

    def clearance(self, pair, step=8):
        """The least white between the two letters over their whole height."""
        lo, hi = -self.face.xh, 2 * self.face.cap
        real = [v for v in self.rows(pair, range(int(lo), int(hi), step)) if v is not None]
        return min(real) if real else None

    def has(self, s):
        return all(self.face.has(c) for c in s)


def letters(cmap):
    """(letter, base) for derive.py's additive recipes on encoded letters."""
    names = {v: chr(k) for k, v in cmap.items()}
    out = []
    for name, op, base, *_ in derive.RECIPES:
        if op not in OPS or len(name) != 1 or not name.isalpha():
            continue
        b = base if len(base) == 1 else names.get(base)
        if b and b.isalpha():
            out.append((name, b))
    return out


def pair(c, n, side):
    return c + n if side == "R" else n + c


def diff(f, ch, base, side):
    """The median over the neighbours of ch's gap less base's, in n n gaps."""
    cap = ch.isupper()
    h = f.face.cap if cap else f.face.xh
    ds = []
    for n in NEIGHBOURS[cap]:
        g1, g0 = f.gap(pair(ch, n, side), h), f.gap(pair(base, n, side), h)
        if g1 is not None and g0 is not None:
            ds.append((g1 - g0) / f.nn)
    return statistics.median(ds) if ds else None


def measure(style, font=None, tolerance=0.15):
    myia = Font(str(font or MYIA.format(style)))
    paths = REFS[style] + [str(Path(p).expanduser()) for p in SYSTEM_REFS[style]
                           if Path(p).expanduser().exists()]
    refs = [Font(p) for p in paths]
    rows, clear = [], []
    for ch, base in letters(myia.face.cmap):
        if not myia.has(ch + base):
            continue
        cap = ch.isupper()
        for side in "LR":
            m = diff(myia, ch, base, side)
            others = {r.name: d for r in refs
                      if r.has(ch + base) and (d := diff(r, ch, base, side)) is not None}
            if m is None or len(others) < 2:
                continue
            lo, hi = min(others.values()), max(others.values())
            off = (m - hi) if m > hi else (m - lo) if m < lo else 0.0
            med = statistics.median(others.values())
            change = round((med - m) * myia.nn) if abs(off) > tolerance else 0
            rows.append({"letter": ch, "base": base, "side": side, "myia": round(m, 3),
                         "lo": round(lo, 3), "hi": round(hi, 3), "median": round(med, 3), "off": round(off, 3),
                         "sidebearing": change, "refs": {k: round(v, 3) for k, v in others.items()}})
            for n in TALL[cap][0 if side == "R" else 1]:
                if not myia.has(n):
                    continue
                c1, c0 = myia.clearance(pair(ch, n, side)), myia.clearance(pair(base, n, side))
                # (no c0: the base pair is a ligature, f l)
                if c1 is not None and c0 is not None and c1 < min(CLEAR, c0):
                    clear.append({"pair": pair(ch, n, side), "white": round(c1), "base": round(c0)})
    return rows, clear, myia


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style")
    ap.add_argument("--font")
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--json")
    args = ap.parse_args()
    rows, clear, myia = measure(args.style, args.font, args.tolerance)
    flagged = [r for r in rows if r["sidebearing"]]
    print(f"{args.style}: {len(rows)} sides of derived letters measured against their base "
          f"(n n gap {myia.nn:.0f} units); {len(flagged)} outside the references' range by more than "
          f"{args.tolerance}; {len(clear)} pairs with a tall neighbour under {CLEAR} units of white")
    for r in sorted(rows, key=lambda r: -abs(r["off"])):
        flag = f"  sidebearing {r['sidebearing']:+d}" if r["sidebearing"] else ""
        print(f"  {r['letter']} {r['side']} (from {r['base']})  myia {r['myia']:+.2f}  "
              f"refs {r['lo']:+.2f}..{r['hi']:+.2f} ({len(r['refs'])}){flag}")
    if clear:
        print("clear:")
        for c in clear:
            print(f"  {c['pair']}  {c['white']} (base {c['base']})")
    if args.json:
        Path(args.json).write_text(json.dumps({"sides": rows, "clear": clear}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
