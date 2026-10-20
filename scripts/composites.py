"""Build accented composite glyphs from Unicode decompositions and anchors.

    python scripts/composites.py UFO --check            # rebuild existing, compare
    python scripts/composites.py UFO --anchors          # complete missing anchors
    python scripts/composites.py UFO --carry-anchors    # composites keep their base's free anchors
    python scripts/composites.py UFO --add U+1EA0 ...   # add composites
    python scripts/composites.py UFO --add-missing FONT # all 'compose' chars of
                                                        # the coverage target

The rules follow the conventions of the upstream Theano Didot source:

* combining marks are spacing accents (880 wide, centred on x=440) shifted by
  -880; composites reference the spacing accent, not the combining mark;
* lowercase bases carry Top/Acute/Grave/Dotaccent anchors (Acute and Grave
  20 units below Top, Dotaccent 20 above), Bottom and DotBelow below;
* capitals carry a single TopCap anchor and take the flatter ".cap" accents;
* i and j take dotless bases and the narrow ".i" accents, Cyrillic lowercase
  takes the ".cyrl" breve, Cyrillic capitals the ".cyrcap" breve;
* a second top mark stacks on the first through TopMark/_TopMark.
* a horn takes the base drawn for it where there is one (U.horn); the
  marks above move left where they come nearer it than HORN_GAP.
"""

import argparse
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import ufoLib2
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))

TOP_MARK_ANCHORS = ("_Acute", "_Grave", "_Dotaccent", "_Top", "_TopCap")
BOTTOM_MARK_ANCHORS = ("_DotBelow", "_Bottom")
SIDE_MARK_ANCHORS = ("_Cedilla", "_Ogonek", "_Horn")
# Base anchors that can stand in for a missing one, with a y correction.
FALLBACK = {
    "Acute": [("Top", -20)],
    "Grave": [("Top", -20)],
    "Dotaccent": [("Top", 20)],
    "Top": [("Acute", 20), ("Grave", 20), ("Dotaccent", -20)],
    "DotBelow": [("Bottom", -20)],
    "Bottom": [("DotBelow", 20)],
    "Cedilla": [("Bottom", 0)],
}
SOFT_DOTTED = {"i": "dotlessi", "j": "uni0237", "uni0456": "dotlessi", "uni0458": "uni0237"}
# Vertical gap between the ink of two stacked top marks (font units).
STACK_GAP_LC = 90
STACK_GAP_UC = 60
# least white between a horn and a mark above (ỡ: the tilde's end ran into
# the horn's ball); the marks above move left as far as it takes
HORN_GAP = 50
# how far a horn may move off its anchor so that it joins its base cleanly
# (the tail hooks left: it stood out of ư.sc's narrow stem in the italics,
# and its outer edge met u's top corner, a ledge of 4 units)
HORN_FIT = 24


@dataclass
class Placed:
    glyph: str  # glyph used as component
    dx: int
    dy: int
    anchor: str | None = None  # base anchor the mark was attached to


@dataclass
class Recipe:
    name: str
    unicode: int
    base: str
    width: int
    components: list = field(default_factory=list)
    anchors: list = field(default_factory=list)


class Builder:
    def __init__(self, font):
        self.font = font
        self.cmap = {}
        for g in font:
            for u in g.unicodes:
                self.cmap.setdefault(u, g.name)

    # -- helpers -----------------------------------------------------------

    def anchors(self, name):
        return {a.name: (a.x, a.y) for a in self.font[name].anchors}

    def base_anchor(self, base, name):
        anchors = self.anchors(base)
        if name in anchors:
            return anchors[name]
        for alt, dy in FALLBACK.get(name, ()):
            if alt in anchors:
                x, y = anchors[alt]
                return x, y + dy
        return None

    def is_upper(self, glyph):
        u = self.font[glyph].unicode
        if u is None and "." in glyph:
            # an unencoded variant (U.horn) takes its base letter's case
            stem = glyph.split(".", 1)[0]
            if stem in self.font:
                u = self.font[stem].unicode
        return u is not None and unicodedata.category(chr(u)) == "Lu"

    def script(self, glyph):
        u = self.font[glyph].unicode
        if u is None and "." in glyph:
            # an unencoded variant (a.sc, ...) takes its base letter's script
            stem = glyph.split(".", 1)[0]
            if stem in self.font:
                u = self.font[stem].unicode
        if u is None:
            return None
        n = unicodedata.name(chr(u), "")
        return "cyrl" if "CYRILLIC" in n else "grek" if "GREEK" in n else "latn"

    def mark_variant(self, mark, base, stacked, upper=None):
        """Pick the contextual form of a combining mark for this base."""
        candidates = []
        sc = self.script(base)
        if upper if upper is not None else self.is_upper(base):
            if sc == "cyrl":
                candidates.append(mark + ".cyrcap")
            candidates.append(mark + ".cap")
        else:
            if sc == "cyrl":
                candidates.append(mark + ".cyrl")
            if base in SOFT_DOTTED.values() and not stacked:
                candidates.append(mark + ".i")
        for c in candidates:
            if c in self.font:
                return c
        return mark

    def mark_side(self, mark):
        names = set(self.anchors(mark))
        if names & set(TOP_MARK_ANCHORS):
            return "top"
        if names & set(BOTTOM_MARK_ANCHORS):
            return "bottom"
        if names & set(SIDE_MARK_ANCHORS):
            return "side"
        return None

    def spacing_form(self, mark):
        """(glyph, dx, dy) to reference instead of the combining mark itself."""
        g = self.font[mark]
        if len(g.components) == 1 and not g.contours:
            c = g.components[0]
            t = c.transformation
            if tuple(t[:4]) == (1, 0, 0, 1):
                return c.baseGlyph, t[4], t[5]
        return mark, 0, 0

    def vietnamese_tones(self, marks):
        """Circumflex + acute/grave/hook above as one mark, the tone beside
        the circumflex (Vietnamese habit; ccmpVietnameseToneMarks in the
        features does the same for decomposed text)."""
        out, i = [], 0
        while i < len(marks):
            pair = f"{marks[i]}_{marks[i + 1]}" if i + 1 < len(marks) else None
            if marks[i] == "circumflexcmb" and pair in self.font:
                out.append(pair)
                i += 2
            else:
                out.append(marks[i])
                i += 1
        return out

    # -- recipe ------------------------------------------------------------

    def recipe(self, cp):
        """The composite for code point cp, from its canonical decomposition."""
        nfd = unicodedata.normalize("NFD", chr(cp))
        if len(nfd) < 2:
            raise ValueError(f"U+{cp:04X} has no decomposition")
        base = self.cmap.get(ord(nfd[0]))
        if base is None:
            raise ValueError(f"U+{cp:04X}: base {nfd[0]!r} missing")
        marks = []
        for m in nfd[1:]:
            if ord(m) not in self.cmap:
                raise ValueError(f"U+{cp:04X}: mark U+{ord(m):04X} missing")
            marks.append(self.cmap[ord(m)])
        return self.compose(f"uni{cp:04X}", cp, base, marks, label=f"U+{cp:04X}")

    def compose(self, name, cp, base, marks, label=None, upper=None):
        """A composite of base glyph + combining mark glyphs (any base, encoded or not).

        upper forces the capital (True) or lowercase (False) accent forms;
        by default they follow the base's case.
        """
        cp_label = label or name
        marks = self.vietnamese_tones(marks)
        sides = [self.mark_side(m) for m in marks]
        if None in sides:
            raise ValueError(f"{cp_label}: mark without attachment anchors in {marks}")
        if "top" in sides and base in SOFT_DOTTED:
            base = SOFT_DOTTED[base]
        # a base drawn for the horn (U.horn: the serif's outer arm left out,
        # the horn growing out of the stem; derive.py)
        if any("_Horn" in self.anchors(m) for m in marks) and f"{base}.horn" in self.font:
            base = f"{base}.horn"

        r = Recipe(name, cp, base, self.font[base].width)
        r.components.append(Placed(base, 0, 0))
        last = {"top": None, "bottom": None}  # (mark glyph, dx, dy) of the stack top
        for m, side in zip(marks, sides, strict=True):
            prev = last.get(side)
            mv = self.mark_variant(m, base, stacked=prev is not None, upper=upper)
            manchors = self.anchors(mv)
            if prev is not None:
                pg, pdx, pdy = prev
                pa = self.anchors(pg).get("TopMark" if side == "top" else "BottomMark")
                ma = manchors.get("_TopMark" if side == "top" else "_BottomMark")
                if pa is None or ma is None:
                    raise ValueError(f"{cp_label}: cannot stack {mv} on {pg}")
                dx, dy = pa[0] + pdx - ma[0], pa[1] + pdy - ma[1]
            else:
                order = {
                    "top": TOP_MARK_ANCHORS,
                    "bottom": BOTTOM_MARK_ANCHORS,
                    "side": SIDE_MARK_ANCHORS,
                }[side]
                for an in order:
                    if an not in manchors:
                        continue
                    ba = self.base_anchor(base, an[1:])
                    if ba is not None:
                        break
                else:
                    raise ValueError(f"{cp_label}: {base} has no anchor for {mv}")
                ma = manchors[an]
                dx, dy = ba[0] - ma[0], ba[1] - ma[1]
            sg, sdx, sdy = self.spacing_form(mv)
            attached = an[1:] if prev is None else None
            r.components.append(Placed(sg, round(dx + sdx), round(dy + sdy), attached))
            last[side] = (mv, dx, dy)

        self.fit_horn(r, sides)
        self.clear_horn(r, sides)
        used = {s for s in sides}
        for a in self.font[base].anchors:
            if a.name.startswith("_"):
                continue
            if "top" in used and a.name in ("Top", "Acute", "Grave", "Dotaccent", "TopCap"):
                continue
            if "bottom" in used and a.name in ("Bottom", "DotBelow"):
                continue
            r.anchors.append((a.name, a.x, a.y))
        return r

    def outline_points(self, glyph, dx, dy):
        pen = _Points(self.font)
        self.font[glyph].draw(TransformPen(pen, (1, 0, 0, 1, dx, dy)))
        return pen.points

    def fit_horn(self, r, sides):
        """The horn moved the least (up to HORN_FIT) that leaves its join with
        the base without the faults glyph_lint finds (steps, ledges, slivers)."""
        from glyph_lint import ink, ledge_findings, step_findings, vector_findings

        horns = [c for c, s in zip(r.components[1:], sides, strict=True)
                 if s == "side" and c.anchor == "Horn"]
        if not horns:
            return
        horn, base = horns[0], r.components[0]

        def faults(dx, dy):
            g = ufoLib2.objects.Glyph()
            pen = g.getPointPen()
            pen.addComponent(base.glyph, (1, 0, 0, 1, base.dx, base.dy))
            pen.addComponent(horn.glyph, (1, 0, 0, 1, horn.dx + dx, horn.dy + dy))
            path = ink(self.font, g)
            return vector_findings(path) + step_findings(path) + ledge_findings(path)

        if not faults(0, 0):
            return
        shifts = sorted(((dx, dy) for dx in range(-HORN_FIT, HORN_FIT + 1, 2)
                         for dy in range(-HORN_FIT, HORN_FIT + 1, 2)),
                        key=lambda s: (s[0] ** 2 + s[1] ** 2, s))
        for dx, dy in shifts[1:]:
            if dx * dx + dy * dy <= HORN_FIT ** 2 and not faults(dx, dy):
                horn.dx += dx
                horn.dy += dy
                return

    def clear_horn(self, r, sides):
        """The marks above moved left, all alike, until HORN_GAP of white
        parts them from the horn (by their outlines, sampled)."""
        horns = [c for c, s in zip(r.components[1:], sides, strict=True)
                 if s == "side" and c.anchor == "Horn"]
        tops = [c for c, s in zip(r.components[1:], sides, strict=True) if s == "top"]
        if not horns or not tops:
            return
        horn = self.outline_points(horns[0].glyph, horns[0].dx, horns[0].dy)
        marks = [pt for c in tops for pt in self.outline_points(c.glyph, c.dx, c.dy)]
        shift = 0
        while shift < 400 and min((hx - mx + shift) ** 2 + (hy - my) ** 2
                                  for hx, hy in horn for mx, my in marks) < HORN_GAP ** 2:
            shift += 2
        for c in tops:
            c.dx -= shift

    def write(self, r, overwrite=False):
        if r.name in self.font and not overwrite:
            raise ValueError(f"{r.name} exists")
        if r.unicode is not None and r.unicode in self.cmap and self.cmap[r.unicode] != r.name:
            raise ValueError(f"U+{r.unicode:04X} already encoded as {self.cmap[r.unicode]}")
        g = self.font.newGlyph(r.name)
        g.unicodes = [r.unicode] if r.unicode is not None else []
        g.width = r.width
        pen = g.getPointPen()
        for c in r.components:
            pen.addComponent(c.glyph, (1, 0, 0, 1, c.dx, c.dy))
        for name, x, y in r.anchors:
            g.appendAnchor({"name": name, "x": x, "y": y})
        if r.unicode is not None:
            self.cmap[r.unicode] = r.name
        if r.name not in self.font.glyphOrder:
            self.font.glyphOrder = [*self.font.glyphOrder, r.name]
        cats = self.font.lib.setdefault("public.openTypeCategories", {})
        cats[r.name] = "base"


class _Points(BasePen):
    """Points along an outline, about every 10 units on curves."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.points = []

    def _moveTo(self, pt):
        self.start = pt
        self.points.append(pt)

    def _closePath(self):
        if self._getCurrentPoint() != self.start:
            self._lineTo(self.start)

    def _lineTo(self, pt):
        (x0, y0), (x1, y1) = self._getCurrentPoint(), pt
        n = max(1, int(abs(x1 - x0) + abs(y1 - y0)) // 10)
        self.points += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(1, n + 1)]

    def _curveToOne(self, p1, p2, p3):
        x0, y0 = self._getCurrentPoint()
        n = max(1, int(abs(p3[0] - x0) + abs(p3[1] - y0)) // 10)
        for i in range(1, n + 1):
            t = i / n
            u = 1 - t
            self.points.append((u ** 3 * x0 + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                                u ** 3 * y0 + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))


# -- anchor completion ------------------------------------------------------


def complete_anchors(font, log):
    b = Builder(font)

    # 1. Specific top anchors on lowercase bases that only have Top.
    for g in font:
        names = {a.name for a in g.anchors}
        if "Top" not in names or g.unicode is None:
            continue
        x, y = b.anchors(g.name)["Top"]
        for n, dy in (("Acute", -20), ("Grave", -20), ("Dotaccent", 20)):
            if n not in names:
                g.appendAnchor({"name": n, "x": x, "y": y + dy})
                log.append(f"{g.name}: +{n}")

    # 2. Cedilla anchors, recovered from upstream's hand-placed composites.
    cedillas = {"cedilla": "uni0327", "Cedilla": "uni0327.cap"}
    for g in font:
        comps = {c.baseGlyph: c.transformation for c in g.components}
        ced = [n for n in comps if n in cedillas]
        others = [n for n in comps if n not in cedillas]
        if len(ced) != 1 or len(others) != 1:
            continue
        base = others[0]
        if tuple(comps[base]) != (1, 0, 0, 1, 0, 0):
            continue
        dx = comps[ced[0]][4]
        if "Cedilla" not in b.anchors(base):
            font[base].appendAnchor({"name": "Cedilla", "x": dx + 440, "y": 0})
            log.append(f"{base}: +Cedilla at {dx + 440} (from {g.name})")
    for mark in cedillas.values():
        if mark in font and "_Cedilla" not in b.anchors(mark):
            font[mark].appendAnchor({"name": "_Cedilla", "x": -440, "y": 0})
            log.append(f"{mark}: +_Cedilla")



def ink_bounds(font, name):
    pen = ControlBoundsPen(font)
    font[name].draw(pen)
    return pen.bounds


def carry_anchors(font, log):
    """The base's anchors no mark of it took (Á keeps A's Bottom and
    DotBelow, for a mark added below), as Builder.recipe carries them, onto
    the composites made by the rules that lack them (upstream's were made
    without): only anchors missing, none moved."""
    b = Builder(font)
    for g in font:
        if g.unicode is None or g.name in SPECIAL or g.contours or not g.components:
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        mine = sorted((c.baseGlyph, round(c.transformation[4]), round(c.transformation[5])) for c in g.components)
        if sorted((p.glyph, p.dx, p.dy) for p in r.components) != mine:
            continue
        have = {a.name for a in g.anchors}
        for name, x, y in r.anchors:
            if name not in have:
                g.appendAnchor({"name": name, "x": x, "y": y})
                log.append(f"{g.name}: {name} carried from its base")


def stack_anchors(font, log, gap_lc=STACK_GAP_LC, gap_uc=STACK_GAP_UC):
    """Set TopMark/_TopMark on every top combining mark from its ink.

    _TopMark sits half a gap below the ink, TopMark half a gap above it, so
    any two stacked marks are separated by exactly one gap.
    """
    b = Builder(font)
    for g in font:
        a = b.anchors(g.name)
        ref = next((a[n] for n in ("_TopCap", "_Top", "_Acute", "_Grave", "_Dotaccent") if n in a),
                   None)
        if ref is None or g.width != 0:
            continue
        bounds = ink_bounds(font, g.name)
        if bounds is None:
            continue
        gap = gap_uc if "_TopCap" in a else gap_lc
        x = a.get("_TopMark", ref)[0]
        for anchor in list(g.anchors):
            if anchor.name in ("TopMark", "_TopMark"):
                g.anchors.remove(anchor)
        g.appendAnchor({"name": "_TopMark", "x": x, "y": round(bounds[1] - gap / 2)})
        g.appendAnchor({"name": "TopMark", "x": x, "y": round(bounds[3] + gap / 2)})
        log.append(f"{g.name}: stack anchors at {round(bounds[1] - gap / 2)}/{round(bounds[3] + gap / 2)}")


# -- check against existing composites --------------------------------------

# Hand-designed upstream composites that deliberately deviate from the
# anchor rules (vertical caron on ascenders, ring + acute stack).
SPECIAL = {
    "dcaron", "lcaron", "tcaron", "Lcaron", "aringacute", "Aringacute",
    # Latvian letters: Unicode says cedilla, the design uses a comma below
    "Gcommaaccent", "gcommaaccent", "Kcommaaccent", "kcommaaccent",
    "Lcommaaccent", "lcommaaccent", "Ncommaaccent", "ncommaaccent",
    "Rcommaaccent", "rcommaaccent",
}


def single_mark_deltas(font, b):
    """(base, anchor) -> set of (dx, dy) by which upstream composites differ."""
    deltas = {}
    for g in font:
        if g.name in SPECIAL or g.unicode is None or len(g.components) != 2 or g.contours:
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError:
            continue
        have = {c.baseGlyph: c.transformation for c in g.components}
        mark = r.components[1]
        if mark.glyph not in have or r.components[0].glyph not in have:
            continue
        t = have[mark.glyph]
        deltas.setdefault((r.base, mark.anchor), set()).add(
            (round(t[4]) - mark.dx, round(t[5]) - mark.dy)
        )
    return deltas


def sync_anchors(font, log):
    """Move base anchors to where upstream's composites place the accents."""
    b = Builder(font)
    for (base, anchor), ds in sorted(single_mark_deltas(font, b).items()):
        if len(ds) != 1:
            log.append(f"{base}.{anchor}: inconsistent composites {sorted(ds)}, left alone")
            continue
        (dx, dy), = ds
        if (dx, dy) == (0, 0):
            continue
        x, y = b.base_anchor(base, anchor)
        g = font[base]
        for a in list(g.anchors):
            if a.name == anchor:
                g.anchors.remove(a)
        g.appendAnchor({"name": anchor, "x": x + dx, "y": y + dy})
        log.append(f"{base}.{anchor}: moved by ({dx}, {dy})")


def check(font):
    b = Builder(font)
    ok, bad, skipped = 0, [], 0
    for g in font:
        if g.unicode is None or not g.components or g.contours or g.name in SPECIAL:
            continue
        nfd = unicodedata.normalize("NFD", chr(g.unicode))
        if len(nfd) < 2 or "GREEK" in unicodedata.name(chr(g.unicode), ""):
            continue
        try:
            r = b.recipe(g.unicode)
        except ValueError as e:
            skipped += 1
            bad.append((g.name, f"skip: {e}"))
            continue
        have = sorted((c.baseGlyph, round(c.transformation[4]), round(c.transformation[5]))
                      for c in g.components)
        want = sorted((c.glyph, c.dx, c.dy) for c in r.components)
        if have == want and g.width == r.width:
            ok += 1
        else:
            bad.append((g.name, f"upstream {have} w={g.width}\n{'':14}rules    {want} w={r.width}"))
    print(f"{ok} composites reproduced exactly, {len(bad) - skipped} differ, {skipped} skipped")
    for name, msg in bad:
        print(f"  {name:12} {msg}")


def parse_cp(s):
    s = s.upper().removeprefix("U+")
    return int(s, 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ufo")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--anchors", action="store_true")
    ap.add_argument("--sync-anchors", action="store_true")
    ap.add_argument("--stack-anchors", action="store_true")
    ap.add_argument("--carry-anchors", action="store_true",
                    help="give rule-made composites the base anchors no mark took")
    ap.add_argument("--rebuild-stacked", action="store_true",
                    help="regenerate composites with two or more top marks")
    ap.add_argument("--add", nargs="*", default=[])
    ap.add_argument("--add-missing", metavar="FONT")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    font = ufoLib2.Font.open(args.ufo)
    changed = False
    if args.anchors:
        log = []
        complete_anchors(font, log)
        print("\n".join(log))
        print(f"{len(log)} anchors added")
        changed = bool(log)
    if args.sync_anchors:
        log = []
        sync_anchors(font, log)
        print("\n".join(log))
        changed = changed or any("moved" in m for m in log)
    if args.stack_anchors:
        log = []
        stack_anchors(font, log)
        print("\n".join(log))
        changed = changed or bool(log)
    if args.carry_anchors:
        log = []
        carry_anchors(font, log)
        print(f"{len(log)} anchors carried onto composites")
        changed = changed or bool(log)
    if args.rebuild_stacked:
        b = Builder(font)
        n = 0
        for g in list(font):
            if g.unicode is None or g.name in SPECIAL or g.contours or not g.components:
                continue
            nfd = unicodedata.normalize("NFD", chr(g.unicode))
            if len(nfd) < 3 or "GREEK" in unicodedata.name(chr(g.unicode), ""):
                continue
            try:
                r = b.recipe(g.unicode)
            except ValueError:
                continue
            if r.name != g.name:
                r.name = g.name
            del font[g.name]
            b.write(r)
            n += 1
        print(f"{n} stacked composites rebuilt")
        changed = changed or bool(n)
    if args.check:
        check(font)

    cps = [parse_cp(s) for s in args.add]
    if args.add_missing:
        import glyphsets
        from fontTools.ttLib import TTFont

        sys.path.insert(0, "scripts")
        from coverage import TARGET, classify

        have = set(TTFont(args.add_missing).getBestCmap())
        for gs in TARGET:
            for u in glyphsets.unicodes_per_glyphset(gs):
                if u not in have and u not in cps and classify(u, have)[0] == "compose":
                    cps.append(u)
    if cps:
        b = Builder(font)
        added, failed = [], []
        for cp in cps:
            try:
                r = b.recipe(cp)
                if not args.dry_run:
                    b.write(r)
                added.append(r)
            except ValueError as e:
                failed.append(str(e))
        for r in added:
            comps = " + ".join(f"{c.glyph}@{c.dx},{c.dy}" for c in r.components)
            print(f"  {r.name} {chr(r.unicode)}  {comps}")
        print(f"{len(added)} composites {'planned' if args.dry_run else 'added'}, "
              f"{len(failed)} failed")
        for e in failed:
            print("  FAIL", e)
        changed = changed or (bool(added) and not args.dry_run)
    if changed and not args.dry_run:
        font.save()


if __name__ == "__main__":
    main()
