"""Letters and figures meeting the signs beside them: the collision sweep.

    python scripts/quality/collisions.py UFO [--out TXT] [--sheet PDF] [--show N] [--exact]
    make collisions        # four styles: build/quality/collisions-STYLE.{txt,pdf}

Every letter and figure is set before the closing signs (? ! ) ] } ” “ ’
* : ;) and the superiors, after the opening ones (( [ { „ “ ‘ ¿ ¡), and
the capitals beside the case forms as `case` sets them, each pair at the
kerning it takes; listed are those with less white across than
kern_clear.clearance asks (CLEAR, or a sign's own: openers 100, ! ? 60,
the other closers 40). One measure with kern_clear (its Ink): a pair
listed is one kern_clear would loosen if it were among its entries, and
a pair it has cleared is not listed. Specification: docs/claude/collisions.md.

The sets are taken from the font (respace.classifier's letters, the
figures by name), so a new letter is swept the day it is added. Reads the
UFO, writes nothing into it. Output, one line a pair, worst first:

    f question -34  f?  loosen 54   public.kern1.f question (12 of 14)

the two glyphs, the white (negative: ink in common), the pair as text,
the loosening that gives that clearance, and the most general kerning key pair of
which at least half the pairs swept are listed ("-": only this one).
The list in tests/data/collisions*.txt is held by tests/test_collisions.py.
"""

import argparse
import collections
import subprocess
import sys
import unicodedata
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kern_clear
import kern_coverage
from kern_coverage import Profiles
from kern_touch import draw, label

ROOT = Path(__file__).resolve().parent.parent.parent
# rows this far apart (two rows of kern_coverage either way) may miss ink
# between them; pairs whose rows come nearer than CLEAR + MARGIN are intersected
MARGIN = 2 * kern_coverage.STEP
sets = kern_clear.sets


def swept_pairs(font, s=None):
    """The glyph pairs swept, (left, right), in a set."""
    s = s or sets(font)
    words = s["LETTERS"] + s["FIGURES"]
    pairs = {(a, c) for a in words for c in s["CLOSERS"] + s["SUPERIORS"]}
    pairs |= {(o, b) for o in s["OPENERS"] for b in words}
    for c in s["CLOSERS"]:
        if c + ".case" in font:
            pairs |= {(a, c + ".case") for a in s["CAPITALS"]}
    for o in s["OPENERS"]:
        if o + ".case" in font:
            pairs |= {(o + ".case", b) for b in s["CAPITALS"]}
    return pairs


def white(ink, a, b, kern, clear=kern_clear.CLEAR):
    """How far b, set after a at kern, can still move left before the inks
    meet, in steps of kern_clear.STEP up to clear (clear: clear enough);
    negative where they overlap: how far it must move right to come free."""
    if not ink.touch(a, b, kern, clear=clear):
        return clear
    w = clear - kern_clear.STEP
    while w > 0 and ink.touch(a, b, kern, clear=w):
        w -= kern_clear.STEP
    if w > 0:
        return w
    while ink.touch(a, b, kern, clear=w):
        w -= kern_clear.STEP
        if -w > kern_clear.LIMIT:
            raise SystemExit(f"collisions: {a} {b} still overlap {kern_clear.LIMIT} units loosened")
    return w


def sweep(font, exact=False, pairs=None):
    """[(a, b, kern, white)] for the swept pairs with less white than
    kern_clear.clearance asks of them (CLEAR, or a sign's own), worst
    first, and the number swept. exact: every pair intersected (no row
    filter)."""
    pairs = swept_pairs(font) if pairs is None else pairs
    _, entry = kern_clear.kern_lookup(font)
    ink = kern_clear.Ink(font)
    prof = Profiles(font)
    found = []
    for a, b in pairs:
        e = entry(a, b)
        kern = font.kerning[e] if e else 0
        c = kern_clear.clearance(a, b)
        if not exact:
            g = prof.gap(a, b, kern)
            if g is None or g >= c + MARGIN:
                continue
        w = white(ink, a, b, kern, clear=c)
        if w < c:
            found.append((a, b, kern, w))
    found.sort(key=lambda f: (f[3], f[0], f[1]))
    return found, len(pairs)


def families(font, found, pairs):
    """{(a, b): (key pair, listed, swept)} for each listed pair whose most
    general kerning key pair (group, group first) has at least half its
    swept member pairs listed; the rest not in the dict."""
    keys, _ = kern_clear.kern_lookup(font)
    listed = {(a, b) for a, b, _, _ in found}
    out, seen = {}, {}
    for a, b, _, _ in found:
        for left, right in reversed(keys(a, b)[1:]):
            if left is None or right is None:
                continue
            if (left, right) not in seen:
                inside = [(x, y) for x in kern_clear.members(font, left) for y in kern_clear.members(font, right)
                          if (x, y) in pairs]
                seen[(left, right)] = (sum(p in listed for p in inside), len(inside))
            n, total = seen[(left, right)]
            if total > 1 and 2 * n >= total:
                out[(a, b)] = ((left, right), n, total)
                break
    return out


def text(font, a, b):
    return unicodedata.normalize("NFC", label(font, a) + label(font, b))


def lines(font, found, pairs):
    fam = families(font, found, pairs)
    out = []
    for a, b, _, w in found:
        if (a, b) in fam:
            (left, right), n, total = fam[(a, b)]
            key = f"{left} {right} ({n} of {total})"
        else:
            key = "-"
        out.append(f"{a} {b} {w}  {text(font, a, b)}  loosen {kern_clear.clearance(a, b) - w}   {key}")
    return out


def sheet(font, found, out, show):
    """Per sign a block, its pairs worst first: each as set (red: ink in
    common, orange: nearer than CLEAR) and beside it at the loosened value."""
    s = sets(font)
    words = set(s["LETTERS"] + s["FIGURES"])
    blocks = collections.defaultdict(list)
    for a, b, kern, w in found:
        sign = b if a in words else a
        blocks[sign].append((a, b, kern, w))
    ink = kern_clear.Ink(font)
    per_row, cell_gap, row_h = 6, 500, 2700
    parts, y, width = [], 700, 9000
    parts.append(f'<text x="100" y="400" font-size="260" font-family="sans-serif">{Path(out).stem}: '
                 f'each pair as set (red: ink in common, orange: nearer than {kern_clear.CLEAR}) | '
                 f'loosened to its clearance (kern_clear.clearance)</text>')
    order = sorted(blocks, key=lambda k: (k.endswith(".case"), min(f[3] for f in blocks[k]), k))
    for sign in order:
        items = blocks[sign]
        caption = f"{label(font, sign)} ({sign}): {len(items)} pairs"
        if len(items) > show:
            caption += f", {show} shown, {len(items) - show} more in the list"
        caption = caption.replace("&", "&amp;").replace("<", "&lt;")
        parts.append(f'<text x="100" y="{y + 300}" font-size="260" font-family="sans-serif" '
                     f'font-weight="bold">{caption}</text>')
        y += 400
        for i in range(0, min(len(items), show), per_row):
            x = 100
            base = y + 1900
            for a, b, kern, w in items[i:i + per_row]:
                x0 = x
                x += draw(font, ink, a, b, kern, x, base, parts) + 200
                c = kern_clear.clearance(a, b)
                x += draw(font, ink, a, b, kern + c - w, x, base, parts)
                parts.append(f'<text x="{x0}" y="{base + 550}" font-size="200" font-family="sans-serif">'
                             f'{w} of {c} → +{c - w}</text>')
                x += cell_gap
            width = max(width, x)
            y += row_h
        y += 200
    h = max(y, row_h)
    svg = Path(out).with_suffix(".svg")
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" '
                   f'viewBox="0 0 {width} {h}"><rect width="{width}" height="{h}" fill="white"/>'
                   f'{"".join(parts)}</svg>')
    subprocess.run(["rsvg-convert", "-f", "pdf", "-w", "1000", "-o", str(out), str(svg)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--out", help="the list, also printed")
    ap.add_argument("--sheet", help="a PDF of the pairs, by sign")
    ap.add_argument("--show", type=int, default=40, help="pairs drawn a sign (default 40)")
    ap.add_argument("--exact", action="store_true", help="intersect every pair, no row filter (slow)")
    args = ap.parse_args()
    font = ufoLib2.Font.open(args.ufo)
    pairs = swept_pairs(font)
    found, n = sweep(font, exact=args.exact, pairs=pairs)
    out = lines(font, found, pairs)
    print("\n".join(out))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("\n".join(out) + "\n" if out else "")
    if args.sheet:
        sheet(font, found, args.sheet, args.show)
    touching = sum(w <= 0 for *_, w in found)
    print(f"{Path(args.ufo).name}: {len(found)} pairs within their clearance ({touching} touching), "
          f"{n} swept", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
