"""An italic's Latin kerning computed from the white its own shapes leave.

    python scripts/italic_kerning.py UPRIGHT.ufo ITALIC.ufo [--out FILE] [--pairs "To Av ..."]

A prototype (TODO.md F2, phase 3): it reads both UFOs and writes a table,
nothing in sources/. The rule it tries, in docs/claude/spacing.md:

    an upright pair's kerning says how much white the pair is to have
    against the style's plain rhythm (n n, H H); the italic of the same
    weight gets the kerning that gives its own shapes that share of its
    own rhythm.

    white(a b)  the mean white between a's right and b's left edge over the
                rows where the two face each other (both have ink between
                their lowest and highest point), each row counted no
                further than DEPTH x-heights past the pair's near white;
                the near white is the row at QUANTILE, not the nearest: an
                entry or exit hairline counts by the rows it fills
    share       (white(a b) + kerning) / white of the pair's plain rhythm:
                n n, H H, H n or n H by the two letters' case
    italic's    share * the italic's rhythm - the italic's white(a b)

with three limits:
- no tighter than the upright's own value (TIGHTEN, below);
- the inks come no nearer than the upright's pair has them (its nearest
  white, by the same scale: j's dot under T's bar is in too few rows to
  count in the mean) or, where that is less, than the italic's own n n
  or H H has them;
- a kerning keeps its sign or goes (the upright's k v stays open after
  its kerning because k is; the italic k is not, and is not opened to
  match).
Values under DROP are no pair.

Not computed, the upright's value kept (the table says which):
- pairs whose letters do not face each other (’ before s: no row in
  common), "no rows";
- Greek and Cyrillic (measured against their references per style,
  greek_pairs.py) and small caps (smallcaps.py makes theirs).
"""

import argparse
import copy
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
import ufoLib2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
sys.path.insert(0, str(ROOT / "scripts"))
from kern_coverage import YS, Profiles  # noqa: E402

DEPTH = 0.2  # of the x-height: how far past the near white a row counts
QUANTILE = 0.2  # the near white: this share of the facing rows are nearer
MIN_ROWS = 8  # facing rows (of 10 units) under which a pair is not measured
DROP = 8  # a computed value under this is no pair
# how much of a tightening past the upright's value is taken (1: all).
# The italic leans away from what follows it at the baseline (V Y P F T
# before comma, J, a), and the rule would close that fully (V, -320 to
# -467); the reference italics leave such pairs looser than their romans.
# Measured 2026-11-11 against five reference italics, pairs outside their
# range, Italic / Bold Italic: today 81 / 59; at 1.0 60 / 41; at 0.5
# 45 / 33; at 0: 40 / 29. So none is taken, unless the review says otherwise.
TIGHTEN = 0.0


def representative(font, key):
    """The glyph that stands for a kerning key: itself, or its group's
    name-giver (public.kern1.A: A), or the group's first glyph."""
    if not key.startswith("public.kern"):
        return key if key in font else None
    members = [m for m in font.groups.get(key, []) if m in font]
    name = key.split(".", 2)[2]
    return name if name in members else (members[0] if members else None)


def kind(font, name):
    """"lower", "upper" (capitals, figures, punctuation: what stands with
    capitals), or None for what is not computed."""
    if ".sc" in name:
        return None
    g = font[name]
    if not g.unicodes:
        return "upper"
    ch = chr(g.unicodes[0])
    script = unicodedata.name(ch, "?").split()[0]
    if script in ("GREEK", "CYRILLIC", "COPTIC"):
        return None
    return "lower" if unicodedata.category(ch) == "Ll" else "upper"


def white(font, prof, a, b):
    """The unkerned white of a b (see the module's text), or None where
    the two do not face each other."""
    _, ra, _, _ = prof[a]
    lb, _, _, _ = prof[b]
    ina, inb = np.isfinite(ra), np.isfinite(lb)
    if not ina.any() or not inb.any():
        return None
    lo = max(YS[ina].min(), YS[inb].min())
    hi = min(YS[ina].max(), YS[inb].max())
    band = (YS >= lo) & (YS <= hi)
    facing = band & ina & inb
    if facing.sum() < MIN_ROWS:
        return None
    d = (lb + font[a].width - ra)[facing]
    limit = float(np.quantile(d, QUANTILE)) + DEPTH * font.info.xHeight
    # rows of the band where one letter has no ink (between i and its dot) are open
    return float((np.minimum(d, limit).sum() + limit * (band.sum() - facing.sum())) / band.sum())


RHYTHM = {("lower", "lower"): ("n", "n"), ("upper", "upper"): ("H", "H"),
          ("upper", "lower"): ("H", "n"), ("lower", "upper"): ("n", "H")}


def rhythm(font, prof):
    return {k: white(font, prof, *pair) for k, pair in RHYTHM.items()}


def upright_kerning(font):
    """The upright's kerning before kern_clear loosened it for its own
    outlines (as the generators start from it)."""
    import kern_clear

    f = copy.copy(font)
    f.kerning = dict(font.kerning)
    f.lib = copy.deepcopy(dict(font.lib))
    kern_clear.undo(f)
    return f.kerning


def compute(upright, italic, only=None):
    """{(left, right): row} for the upright's Latin pairs; row: a, b (the
    glyphs measured), upright (its kerning), value (the italic's, None
    where not computed), note."""
    pu, pi = Profiles(upright), Profiles(italic)
    ru, ri = rhythm(upright, pu), rhythm(italic, pi)
    out = {}
    for (left, right), k in sorted(upright_kerning(upright).items()):
        a, b = representative(upright, left), representative(upright, right)
        if a is None or b is None or a not in italic or b not in italic:
            continue
        if only is not None and (a, b) not in only:
            continue
        ka, kb = kind(upright, a), kind(upright, b)
        if ka is None or kb is None:
            continue
        row = {"a": a, "b": b, "upright": k, "value": None, "note": ""}
        out[(left, right)] = row
        wu, wi = white(upright, pu, a, b), white(italic, pi, a, b)
        if wu is None or wi is None:
            row["note"] = "no rows"
            continue
        scale = ri[(ka, kb)] / ru[(ka, kb)]
        v = round(scale * (wu + k) - wi)
        # the inks no nearer than the upright's pair has them, or than
        # the italic's own rhythm has them anyway (its exits and entries)
        short = min(scale * pu.gap(a, b, k), pi.gap(*RHYTHM[(ka, kb)], 0)) - pi.gap(a, b, v)
        if short > 0:
            v += math.ceil(short)
            row["note"] = "nearest"
        # a kerning keeps its sign or goes: the italic is not opened
        # where the upright closed, nor closed where it opened
        if v * k < 0:
            v, row["note"] = 0, "sign"
        if v < k < 0:
            v = round(k + TIGHTEN * (v - k))
        row["value"] = 0 if abs(v) < DROP else v
        row["share"] = round((wu + k) / ru[(ka, kb)], 3)
        row["white"], row["rhythm"] = wi, ri[(ka, kb)]
    return out


class Built:
    """A built font (Myia's or a reference) as Profiles and white() read a
    UFO: glyphs by name, drawn at 2048 units to the em."""

    class _Glyph:
        def __init__(self, glyph, scale):
            self._g, self._s = glyph, scale
            self.width = glyph.width * scale

        def draw(self, pen):
            from fontTools.pens.transformPen import TransformPen

            self._g.draw(TransformPen(pen, (self._s, 0, 0, self._s, 0, 0)))

    class _Info:
        pass

    def __init__(self, path):
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont

        self.tt = TTFont(path)
        self.scale = 2048 / self.tt["head"].unitsPerEm
        self._gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.info = self._Info()
        prof = Profiles(self)
        top = prof[self.cmap[ord("x")]][1]
        self.info.xHeight = float(YS[np.isfinite(top)].max())
        self.prof = prof

    def __getitem__(self, name):
        return self._Glyph(self._gs[name], self.scale)

    def __contains__(self, name):
        return name in self._gs

    def keys(self):  # a glyph set, for DecomposingRecordingPen
        return self._gs.keys()

    def share(self, text):
        """The pair's white as set (kerning on), over its plain rhythm;
        None where the font lacks a letter or the two do not face."""
        import uharfbuzz as hb

        def set_white(pair):
            if any(ord(c) not in self.cmap for c in pair):
                return None
            buf = hb.Buffer()
            buf.add_str(pair)
            buf.guess_segment_properties()
            hb.shape(self.hb, buf, {"kern": True, "liga": False})
            order = self.tt.getGlyphOrder()
            if len(buf.glyph_infos) != 2:
                return None
            a, b = (order[i.codepoint] for i in buf.glyph_infos)
            w = white(self, self.prof, a, b)
            if w is None:
                return None
            pos = buf.glyph_positions
            return w + (pos[0].x_advance + pos[1].x_offset) * self.scale - self[a].width

        cases = tuple("lower" if unicodedata.category(c) == "Ll" else "upper" for c in text)
        w, r = set_white(text), set_white("".join(RHYTHM[cases]))
        return None if w is None or not r else w / r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("upright")
    ap.add_argument("italic")
    ap.add_argument("--out")
    ap.add_argument("--pairs", help="only these glyph-name pairs, 'T:o A:v'")
    ap.add_argument("--refs", nargs="*", default=[],
                    help="reference italics (built fonts): their shares' range in the table")
    a = ap.parse_args()
    upright, italic = ufoLib2.Font.open(a.upright), ufoLib2.Font.open(a.italic)
    only = {tuple(p.split(":")) for p in a.pairs.split()} if a.pairs else None
    rows = compute(upright, italic, only)
    style = Path(a.italic).stem.split("-")[-1]
    out = Path(a.out) if a.out else ROOT / "build" / "quality" / f"italic-kerning-{style}.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    refs = [Built(p) for p in a.refs]
    lines = [("left\tright\ta\tb\tupright\ttoday\tcomputed\tchange\tshare\tshare today\tshare computed"
              "\trefs low\trefs high\tnote")]
    changes = []
    for (left, right), r in rows.items():
        today = italic.kerning.get((left, right), 0)
        v = r["value"]
        change = "" if v is None else v - today
        if v is not None:
            changes.append(abs(change))
        shares = ["", "", "", ""]
        if v is not None:
            shares[:2] = [f"{(r['white'] + x) / r['rhythm']:.3f}" for x in (today, v)]
            ua, ub = upright[r["a"]].unicodes, upright[r["b"]].unicodes
            if refs and ua and ub:
                got = [x for x in (f.share(chr(ua[0]) + chr(ub[0])) for f in refs) if x is not None]
                if len(got) >= 2:
                    shares[2:] = [f"{min(got):.3f}", f"{max(got):.3f}"]
        lines.append(f"{left}\t{right}\t{r['a']}\t{r['b']}\t{r['upright']}\t{today}\t"
                     f"{'' if v is None else v}\t{change}\t{r.get('share', '')}\t"
                     + "\t".join(shares) + f"\t{r['note']}")
    out.write_text("\n".join(lines) + "\n")
    c = np.array(changes or [0])
    print(f"{style}: {len(rows)} Latin pairs, {len(changes)} computed, "
          f"{sum(1 for r in rows.values() if r['note'] == 'no rows')} with no facing rows, "
          f"{sum(1 for r in rows.values() if r['note'] == 'nearest')} held by the nearest white, "
          f"{sum(1 for r in rows.values() if r['note'] == 'sign')} gone with their sign; "
          f"against today's: median {np.median(c):.0f}, over 30 units {int((c > 30).sum())}, "
          f"over 60 {int((c > 60).sum())}: {out}")


if __name__ == "__main__":
    sys.exit(main())
