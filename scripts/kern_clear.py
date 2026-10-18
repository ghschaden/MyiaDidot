"""Kerning that keeps letters apart: pairs whose inks would touch or run
into each other are loosened just enough to leave CLEAR units between them.

    python scripts/kern_clear.py UFO [--dry-run]

Run on the Regular; make_italic.py and make_bold.py apply it to the styles
they make (after their own kerning), and smallcaps.py again after the small
caps' kerning, so the values follow each style's outlines. Only the entries in PAIRS are touched (reviewed collisions):
an entry already in the kerning is only ever loosened; one that is not
(a letter's exception to its group's pair) is added where its letters
would come too close at the kerning they take now, and left out where
they would not. What it changed is recorded in the lib (KEY: the
entries and the values they had, "added" where it added one); undo() puts
those back, so a style made from another (the Bold from the Regular)
starts from the kerning before it and finds its own. Idempotent.
"""

import argparse
import sys

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

CLEAR = 20  # units of white the inks keep, measured across
STEP = 2
LIMIT = 600  # no pair needs more: a sign that something else is wrong
KEY = "org.myiadidot.kernCleared"

OGONEK = ("aogonek", "eogonek", "iogonek", "uogonek", "uni01EB", "uni01ED",
          "Aogonek", "Eogonek", "Iogonek", "Uogonek", "uni01EA", "uni01EC")
HORN = ("uni01AF", "uni1EE8", "uni1EEA", "uni1EEC", "uni1EEE", "uni1EF0")  # Ư Ứ Ừ Ử Ữ Ự
# (left, right): glyph or group names, as kerning keys
PAIRS = [
    # the ogonek runs into j's ball (Lithuanian įj ųj, Polish ąj)
    *((o, "public.kern2.j") for o in OGONEK),
    # the Bold Italic's foot serifs meet (A's right, Y's left)
    ("public.kern1.A", "public.kern2.Y"),
    ("A", "Y"),
    ("Aogonek", "Y"),
    # the horn reaches over a small cap's accent (the Bold Italic's Ư ỗ.sc)
    *((h, "public.kern2.O.sc") for h in HORN),
]


def kern_lookup(font):
    m1, m2 = {}, {}
    for gname, members in font.groups.items():
        for m in members:
            if gname.startswith("public.kern1."):
                m1[m] = gname
            elif gname.startswith("public.kern2."):
                m2[m] = gname

    def keys(a, b):
        """The kerning keys for glyphs a b, most specific first (the UFO's order)."""
        return [(a, b), (a, m2.get(b)), (m1.get(a), b), (m1.get(a), m2.get(b))]

    def entry(a, b):
        return next((k for k in keys(a, b) if k in font.kerning), None)

    return keys, entry


def members(font, item):
    return [m for m in font.groups.get(item, [item]) if m in font]


class Ink:
    def __init__(self, font):
        self.font = font
        self._rec = {}

    def path(self, name, dx):
        if name not in self._rec:
            rec = DecomposingRecordingPen(self.font)
            self.font[name].draw(rec)
            self._rec[name] = rec
        p = pathops.Path()
        self._rec[name].replay(TransformPen(p.getPen(), (1, 0, 0, 1, dx, 0)))
        return p

    def touch(self, a, b, kern):
        """Do a's ink and b's, set after it with kern, come within CLEAR?"""
        dx = self.font[a].width + kern - CLEAR
        both = pathops.op(self.path(a, 0), self.path(b, dx), pathops.PathOp.INTERSECTION)
        return abs(both.area) > 1


def needed(ink, pairs, kern):
    """The kerning, from kern up, at which no pair touches (None: kern does)."""
    v = kern
    while any(ink.touch(a, b, v) for a, b in pairs):
        v += STEP
        if v - kern > LIMIT:
            raise SystemExit(f"kern_clear: {pairs[0]} still touch at {v}")
    return None if v == kern else v


def undo(font):
    """Put back the entries clear() changed, as they were before it."""
    for key, was in font.lib.pop(KEY, {}).items():
        pair = tuple(key.split(" "))
        if was == "added":
            font.kerning.pop(pair, None)
        else:
            font.kerning[pair] = was


def clear(font, log=None):
    """Loosen PAIRS where they touch (after undoing a previous run)."""
    undo(font)
    keys, entry = kern_lookup(font)
    ink = Ink(font)
    record = {}
    for left, right in PAIRS:
        if left not in font.groups and left not in font or right not in font.groups and right not in font:
            continue
        # the glyph pairs this entry decides: those with no entry as specific
        pairs = []
        for a in members(font, left):
            for b in members(font, right):
                k = keys(a, b)
                if (left, right) in k and not any(x in font.kerning for x in k[:k.index((left, right))]):
                    pairs.append((a, b))
        was = font.kerning.get((left, right))
        if was is None:
            # an exception to the group's pair: from the kerning the letters take now
            now = {font.kerning[entry(a, b)] if entry(a, b) else 0 for a, b in pairs}
            if len(now) > 1:
                raise SystemExit(f"kern_clear: {left} {right} take {sorted(now)}")
            kern = now.pop() if now else 0
        else:
            kern = was
        v = needed(ink, pairs, kern) if pairs else None
        if v is not None:
            font.kerning[(left, right)] = v
            record[f"{left} {right}"] = "added" if was is None else was
            if log is not None:
                log.append(f"kern_clear: {left} {right} {kern} -> {v}")
    if record:
        font.lib[KEY] = record
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ufo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    font = ufoLib2.Font.open(a.ufo)
    log = []
    before = (dict(font.kerning), font.lib.get(KEY))
    clear(font, log)
    print("\n".join(log) or "kern_clear: nothing to loosen")
    if (dict(font.kerning), font.lib.get(KEY)) != before and not a.dry_run:
        font.save()


if __name__ == "__main__":
    sys.exit(main())
