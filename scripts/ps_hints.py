"""ps_hints.py OTF...: PostScript hints for the CFF fonts, in place.

The Private dict's alignment zones and standard stems are measured from each
style's own glyphs (the UFOs carry the Regular's, imported from upstream, in
every style: the Bold's StdVW was the Regular's 52), then otfautohint (afdko)
adds the stem hints, which the fonts had none of.

Zones, from reference glyphs, as the TrueType hinting has them
(quality/hint_zones.py): the baseline (O's and o's overshoot below 0), x-height
(x, o), small caps (h.sc, o.sc), capitals (H, O), ascenders (l, and b d h k
above it); below, the descenders (p, and g j q y below it).  Zones that would
overlap or touch are merged.  Stems are measured across reference strokes:
vertical ones in n l H h.sc (a quarter up, below H's bar) and o's sides,
horizontal ones in H's bar and H's and n's serifs (runs under MIN_STEM, where
the column only grazes an italic serif, left out).  BlueScale is kept below
1 / (the tallest zone), as the format requires.
"""
import subprocess
import sys
from pathlib import Path

import freetype
import numpy as np
from fontTools.ttLib import TTFont

OTFAUTOHINT = Path(sys.executable).parent / "otfautohint"  # afdko, in the same environment
TOPS = (("x", "o"), ("h.sc", "o.sc"), ("H", "O"), ("l", "b", "d", "h", "k"))
BOTTOM = ("O", "o", "H")  # the baseline zone: from 0 down to the deepest
DESCENDERS = ("p", "q", "g", "j", "y")
FUZZ = 1  # BlueFuzz
MIN_STEM = 24


class Glyphs:
    """Unhinted bitmaps at one pixel per unit."""

    def __init__(self, path, tt):
        self.face = freetype.Face(str(path))
        upm = tt["head"].unitsPerEm
        self.face.set_pixel_sizes(0, upm)
        self.cmap = {name: code for code, name in tt.getBestCmap().items()}
        self.order = set(tt.getGlyphOrder())

    def __contains__(self, name):
        return name in self.order

    def bitmap(self, name):
        """(ink mask, x of its left column, y of its top row) in font units."""
        f = self.face
        f.load_glyph(f.get_name_index(name.encode()), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = f.glyph
        bm = g.bitmap
        a = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.width) > 127
        return a, g.bitmap_left, g.bitmap_top

    def extent(self, name):
        a, _, top = self.bitmap(name)
        rows = np.nonzero(a.any(axis=1))[0]
        return int(top - rows[-1] - 1), int(top - rows[0])  # bottom, top

    def runs_h(self, name, y):
        """Widths of the ink runs along the row at height y."""
        a, _, top = self.bitmap(name)
        return runs(a[top - y]) if 0 <= top - y < a.shape[0] else []

    def runs_v(self, name, x):
        """Heights of the ink runs along the column at x (from the left
        edge of the advance)."""
        a, left, _ = self.bitmap(name)
        return runs(a[:, x - left]) if 0 <= x - left < a.shape[1] else []


def runs(line):
    out, n = [], 0
    for v in line:
        if v:
            n += 1
        elif n:
            out.append(n)
            n = 0
    if n:
        out.append(n)
    return out


def zones(gl):
    """(BlueValues, OtherBlues)."""
    base = min(gl.extent(n)[0] for n in BOTTOM if n in gl)
    blues = [(min(base, 0), 0)]
    for names in TOPS:
        names = [n for n in names if n in gl]
        if not names:
            continue
        flat = gl.extent(names[0])[1]
        blues.append((flat, max(flat, *(gl.extent(n)[1] for n in names))))
    descs = [n for n in DESCENDERS if n in gl]
    flat = gl.extent(descs[0])[0]
    others = [(min(flat, *(gl.extent(n)[0] for n in descs)), flat)]
    return merge(blues), merge(others)


def merge(zs):
    out = []
    for lo, hi in sorted(zs):
        if out and lo <= out[-1][1] + 2 * FUZZ + 1:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def stems(gl, blues):
    """(vertical stems, horizontal stems), most important first."""
    v, h = [], []
    for name in ("n", "l", "H", "h.sc", "o"):
        if name not in gl:
            continue
        lo, hi = gl.extent(name)
        # a quarter up: below H's bar, through n's and o's sides
        r = gl.runs_h(name, lo + (hi - lo) // (2 if name == "o" else 4))
        v += [max(r)] if name == "o" and r else r[:1]
    for name, at in (("H", "middle"), ("H", "edge"), ("n", "edge")):
        if name not in gl:
            continue
        a, left, _ = gl.bitmap(name)
        cols = np.nonzero(a.any(axis=0))[0]
        # through H's bar; through the serifs, just inside the left edge
        x = left + ((cols[0] + cols[-1]) // 2 if at == "middle" else cols[0] + 4)
        h += sorted(r for r in gl.runs_v(name, x) if r >= MIN_STEM)
    return snap(v), snap(h)


def snap(widths, near=4):
    """Distinct widths (those within near units of an earlier one dropped),
    in order of importance, at most 12."""
    out = []
    for w in widths:
        if w > 0 and all(abs(w - o) > near for o in out):
            out.append(int(w))
    return out[:12]


def flat(zs):
    return [int(v) for z in zs for v in z]


def set_private(path):
    tt = TTFont(path)
    gl = Glyphs(path, tt)
    blues, others = zones(gl)
    v, h = stems(gl, blues)
    top = tt["CFF "].cff.topDictIndex[0]
    p = top.Private
    p.BlueValues = flat(blues)
    p.OtherBlues = flat(others)
    p.BlueFuzz = FUZZ
    tallest = max(hi - lo for lo, hi in blues + others)
    p.BlueScale = min(getattr(p, "BlueScale", 0.039625), round(0.99 / max(tallest, 1), 6))
    p.StdVW, p.StdHW = v[0], h[0]
    p.StemSnapV, p.StemSnapH = sorted(v), sorted(h)
    tt.save(path)
    return p


def main():
    for path in sys.argv[1:]:
        p = set_private(path)
        subprocess.run([str(OTFAUTOHINT), path], check=True, stdout=subprocess.DEVNULL)
        print(f"{Path(path).name}: BlueValues {p.BlueValues} OtherBlues {p.OtherBlues} "
              f"StdVW {p.StdVW} StemSnapV {p.StemSnapV} StdHW {p.StdHW} StemSnapH {p.StemSnapH} "
              f"BlueScale {p.BlueScale}")


if __name__ == "__main__":
    main()
