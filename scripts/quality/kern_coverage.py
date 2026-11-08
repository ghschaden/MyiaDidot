"""Kerning coverage: letters left out of the kerning their shape calls for.

    python scripts/quality/kern_coverage.py UFO [--out FILE]

Read from the UFO (groups are a source decision, not a build result):

1. Accented letters outside their base letter's kerning group, side by
   side (NFD base, or the base component of a mark composite). For each,
   the kerning it would take is set against the letters it would meet:
   the closest horizontal gap between the inks (within 20 units of height)
   over all the group's negative pairs, and the base's own gap in the
   same pair. "ok": no closer than the base, or at least MIN_GAP;
   "tight"/"collides": an accent comes too near, or into, the other letter
   (T ï): such a letter stays out, or takes exceptions.
2. Small caps: small caps with no pair against punctuation where their
   capital has one. (A capital before a small cap is mostly left unkerned,
   as in most references: scripts/quality/capsc_pairs.py measures it.)
3. Letter sides in no group and no pair whose shape is alike a group's
   with kerning on that side (to be judged by eye); those reviewed and
   left out (KEPT_OUT) are counted, not listed.

Writes the full report to build/quality/kern-coverage-STYLE.txt and prints
counts.
"""

import argparse
import collections
import sys
import unicodedata
from pathlib import Path

import numpy as np
import ufoLib2
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen

ROOT = Path(__file__).resolve().parent.parent.parent
STEP = 10
YS = np.arange(-800, 2600, STEP) + STEP / 2
WINDOW = 2  # steps either way: inks closer than this vertically count as meeting
MIN_GAP = 40
ALIKE = 40  # shape score (units) under which an ungrouped side is reported
SCRIPTS = ("LATIN", "GREEK", "CYRILLIC")
# Letter sides (glyph, kern side) reviewed and left out of the group their
# shape is alike, measured 2026-10-19: each pair the group kerns, set
# unkerned and as if joined, against the references (greek_pairs.py's gap
# and Latin offset) in all four styles.
KEPT_OUT = {
    # N's kerning is for its open lower right; these, serifed or straight,
    # set inside the references' range unkerned
    "straight sides": [(n, 1) for n in (
        "H", "Hbar", "I", "M", "uni018E", "uni0197", "uni01C0", "uni01C1", "uni01C2",
        "uni2C6D", "uniA78D", "uniA7AA", "uniA7AE", "uni0406", "uni0418", "uni041B",
        "uni041C", "uni041D", "uni041F", "uni0427", "uni0428", "uni042B", "uni042F")]
    + [(n, 2) for n in ("IJ", "M", "Mu", "N", "Nu", "uni041C")],
    "inside the range unkerned": [("m", 1), ("n", 1), ("uni1D6F", 1), ("uni1D70", 1),
                                  ("uni0187", 2), ("uni0193", 2), ("uni03F5", 2)],
    # their model's group kerns only another script's letters
    "model of another script": [(n, 2) for n in (
        "m", "r", "uni024D", "uni027E", "uni1D6F", "uni1D70", "uni1D72", "uni0251",
        "uni025B")]
    + [(n, 1) for n in ("oslash", "uni0252", "uni0258", "uniA7B7")],
    # joining brings more pairs out of the range than into it (ɛ ø as c
    # only in the italics)
    "worse joined": [(n, 2) for n in (
        "uni028E", "uni028A", "uni0250", "uni0269", "uni0268", "uni044A", "oslash")],
    # rare letters, the measure with one reference only
    "unmeasured": [("uni1D72", 1), ("uni1D73", 1)],
    # Greek signs, not letters in a word: ʹ follows its letter, ι is set apart
    "signs": [("uni0374", 1), ("uni1FBE", 2)],
}
KEPT = {item for items in KEPT_OUT.values() for item in items}


class FlattenPen(BasePen):
    """Contours as polygons (curves sampled), for scanlines."""

    def __init__(self, glyphSet=None):
        super().__init__(glyphSet)
        self.edges = []
        self.start = None

    def _moveTo(self, p):
        self.start = p

    def _lineTo(self, p):
        self.edges.append((*self._getCurrentPoint(), *p))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        prev = p0
        for i in range(1, 9):
            t = i / 8
            u = 1 - t
            q = tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                      for a, b, c, d in zip(p0, p1, p2, p3))
            self.edges.append((*prev, *q))
            prev = q

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        c1 = tuple(p0[k] + 2 / 3 * (p1[k] - p0[k]) for k in (0, 1))
        c2 = tuple(p2[k] + 2 / 3 * (p1[k] - p2[k]) for k in (0, 1))
        self._curveToOne(c1, c2, p2)

    def _closePath(self):
        cur = self._getCurrentPoint()
        if self.start and cur != self.start:
            self.edges.append((*cur, *self.start))


class Profiles:
    """Each glyph's leftmost and rightmost ink per scanline."""

    def __init__(self, font):
        self.font = font
        self._p = {}

    def __getitem__(self, name):
        if name not in self._p:
            rec = DecomposingRecordingPen(self.font)
            self.font[name].draw(rec)
            pen = FlattenPen()
            rec.replay(pen)
            left = np.full(len(YS), np.inf)
            right = np.full(len(YS), -np.inf)
            if pen.edges:
                e = np.array(pen.edges)
                x0, y0, x1, y1 = e[:, 0:1], e[:, 1:2], e[:, 2:3], e[:, 3:4]
                ys = YS[None, :]
                hit = ((y0 <= ys) & (ys < y1)) | ((y1 <= ys) & (ys < y0))
                with np.errstate(divide="ignore", invalid="ignore"):
                    x = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
                left = np.where(hit, x, np.inf).min(axis=0)
                right = np.where(hit, x, -np.inf).max(axis=0)
            # widened by the window: ink within WINDOW steps above or below
            lw, rw = left.copy(), right.copy()
            for k in range(1, WINDOW + 1):
                lw[k:] = np.minimum(lw[k:], left[:-k])
                lw[:-k] = np.minimum(lw[:-k], left[k:])
                rw[k:] = np.maximum(rw[k:], right[:-k])
                rw[:-k] = np.maximum(rw[:-k], right[k:])
            self._p[name] = (left, right, lw, rw)
        return self._p[name]

    def gap(self, a, b, kern):
        """The closest horizontal white between a's ink and b's set after it."""
        _, ra, _, raw = self[a]
        lb, _, lbw, _ = self[b]
        shift = self.font[a].width + kern
        g = np.minimum(lb + shift - raw, lbw + shift - ra)
        g = g[np.isfinite(g)]
        return float(g.min()) if len(g) else None


def membership(font):
    side = {1: {}, 2: {}}
    for gname, members in font.groups.items():
        for s in (1, 2):
            if gname.startswith(f"public.kern{s}."):
                for m in members:
                    side[s][m] = gname
    return side


def script_of(font, name):
    g = font[name]
    if g.unicodes:
        return unicodedata.name(chr(g.unicodes[0]), "?").split()[0]
    return "small caps" if ".sc" in name else "other"


def is_mark(font, name):
    g = font[name]
    if g.unicodes and unicodedata.category(chr(g.unicodes[0])).startswith("M"):
        return True
    return any(a.name and a.name.startswith("_") for a in g.anchors)


def base_of(font, cmap, name):
    """The letter an accented one is made of: its NFD base, or the base
    component of a composite whose other components are marks."""
    g = font[name]
    if g.unicodes:
        d = unicodedata.normalize("NFD", chr(g.unicodes[0]))
        if len(d) > 1 and ord(d[0]) in cmap and all(unicodedata.combining(c) for c in d[1:]):
            return cmap[ord(d[0])]
    comps = [c.baseGlyph for c in g.components]
    if len(comps) > 1 and comps[0] in font and all(c in font and is_mark(font, c) for c in comps[1:]):
        return comps[0]
    return None


def pairs_of(font, item, s):
    """Kerning pairs with item on side s, the other side expanded to glyphs."""
    out = []
    for (l, r), v in font.kerning.items():
        mine, other = (l, r) if s == 1 else (r, l)
        if mine != item or v >= 0:
            continue
        for o in font.groups.get(other, [other]):
            if o in font:
                out.append((o, v))
    return out


def group_gaps(font, prof, side, cmap, lines):
    counts = collections.Counter()
    lines.append("1. Accented letters outside their base's group\n")
    for s in (1, 2):
        what = "right side (kern1, the letter before)" if s == 1 else "left side (kern2, the letter after)"
        lines.append(f"  {what}")
        for g in font:
            name = g.name
            if name in side[s] or name.endswith(".sc") or ".sc." in name:
                continue
            base = base_of(font, cmap, name)
            if base is None or base not in side[s]:
                continue
            group = side[s][base]
            worst = None
            for other, v in pairs_of(font, group, s):
                a, b = (name, other) if s == 1 else (other, name)
                ba, bb = (base, other) if s == 1 else (other, base)
                gap, bgap = prof.gap(a, b, v), prof.gap(ba, bb, v)
                if gap is None:
                    continue
                if worst is None or gap - min(bgap if bgap is not None else gap, MIN_GAP) < worst[0]:
                    worst = (gap - min(bgap if bgap is not None else gap, MIN_GAP), other, v, gap, bgap)
            if worst is None:
                verdict, detail = "ok", "no negative pair"
            else:
                _, other, v, gap, bgap = worst
                verdict = "ok" if worst[0] >= 0 else ("collides" if gap < 0 else "tight")
                detail = f"closest {other} ({v}): gap {gap:.0f}, base {bgap:.0f}" if bgap is not None \
                    else f"closest {other} ({v}): gap {gap:.0f}"
            ch = chr(g.unicodes[0]) if g.unicodes else ""
            counts[(s, script_of(font, name), verdict)] += 1
            lines.append(f"    {verdict:8} {ch:2} {name:24} -> {group:28} {detail}")
        lines.append("")
    return counts


def smallcap_gaps(font, side, lines):
    sc = {gname[:-3]: gname for gname in font.groups if gname.endswith(".sc")}
    caps = set(sc)
    lines.append("2. Small caps")
    punct = [(l, r, v) for (l, r), v in font.kerning.items()
             if l in caps and not r.startswith("public.") and r in font
             and font[r].unicodes and unicodedata.category(chr(font[r].unicodes[0])).startswith("P")
             and (sc[l], r) not in font.kerning]
    punct += [(l, r, v) for (l, r), v in font.kerning.items()
              if r in caps and not l.startswith("public.") and l in font
              and font[l].unicodes and unicodedata.category(chr(font[l].unicodes[0])).startswith("P")
              and (l, sc[r]) not in font.kerning]
    lines.append(f"  capital-punctuation pairs with no small-cap pair: {len(punct)}")
    for l, r, v in punct:
        lines.append(f"    {l} {r}: {v}")
    lines.append("")
    return len(punct)


def ungrouped(font, prof, side, cmap, lines):
    """Letter sides in no group (accented letters aside: their base speaks
    for them) whose shape is most alike that of a group with kerning on
    that side: the profile from the sidebearing line, its offset taken out,
    rows inked in one only counting against."""
    lines.append(f"3. Letter sides in no group, alike a kerned group (score under {ALIKE})")
    counts = collections.Counter()
    kept = 0
    kerned = {s: collections.Counter() for s in (1, 2)}
    for pair in font.kerning:
        kerned[1][pair[0]] += 1
        kerned[2][pair[1]] += 1

    def shape(name, s):
        left, right, _, _ = prof[name]
        return left if s == 2 else font[name].width - right

    reps = {s: {} for s in (1, 2)}
    for s in (1, 2):
        for m, gname in side[s].items():
            if m in font and not m.endswith(".sc") and kerned[s][gname]:
                reps[s].setdefault(gname, m)
    for g in font:
        name = g.name
        if not g.unicodes or not unicodedata.category(chr(g.unicodes[0])).startswith("L"):
            continue
        scr = script_of(font, name)
        if scr not in SCRIPTS or base_of(font, cmap, name):
            continue
        for s in (1, 2):
            if name in side[s] or kerned[s][name]:
                continue
            a = shape(name, s)
            best = None
            for gname, rep in reps[s].items():
                b = shape(rep, s)
                both = np.isfinite(a) & np.isfinite(b)
                if both.sum() < 10:
                    continue
                d = a[both] - b[both]
                score = float(np.abs(d - np.median(d)).mean()) + \
                    int((np.isfinite(a) ^ np.isfinite(b)).sum()) * STEP * 0.5
                if best is None or score < best[0]:
                    best = (score, gname)
            if best and best[0] < ALIKE and (name, s) in KEPT:
                kept += 1
            elif best and best[0] < ALIKE:
                counts[(scr, s)] += 1
                lines.append(f"    kern{s} {scr:8} {chr(g.unicodes[0])} {name:20} like "
                             f"{best[1]} ({best[0]:.0f}, {kerned[s][best[1]]} pairs)")
    lines.append(f"    and {kept} sides reviewed and left out (KEPT_OUT)")
    lines.append("")
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--out")
    a = ap.parse_args()
    font = ufoLib2.Font.open(a.ufo)
    style = Path(a.ufo).stem.split("-")[-1]
    out = Path(a.out) if a.out else ROOT / "build" / "quality" / f"kern-coverage-{style}.txt"
    cmap = {u: g.name for g in font for u in g.unicodes}
    side = membership(font)
    prof = Profiles(font)
    lines = [f"Kerning coverage, {style}\n"]
    counts = group_gaps(font, prof, side, cmap, lines)
    npunct = smallcap_gaps(font, side, lines)
    free = ungrouped(font, prof, side, cmap, lines)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"{style}: {out}")
    for s in (1, 2):
        row = collections.Counter()
        for (s2, scr, verdict), n in counts.items():
            if s2 == s:
                row[(scr, verdict)] += n
        print(f"  outside base group, kern{s}: " +
              ", ".join(f"{scr} {v} {n}" for (scr, v), n in sorted(row.items())))
    print(f"  small caps: {npunct} punctuation pairs missing")
    print("  ungrouped sides alike a kerned group: " +
          ", ".join(f"{scr} kern{s} {n}" for (scr, s), n in sorted(free.items())))


if __name__ == "__main__":
    sys.exit(main())
