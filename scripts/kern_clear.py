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
starts from the kerning before it and finds its own.

Letters kern_groups.py put in a group though its kerning would bring their
accent too near (lib GUARD_KEY: Ά Ǎ ǐ Ľ ...; and their small caps) are
guarded: each of the group's pairs that would leave less than GUARD units
of white between their ink and the other letter's (kern_coverage's gap)
gets an exception for that letter, as tight as GUARD allows (looser than
unkerned where even that is too near). Idempotent.
"""

import argparse
import math
import sys
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
from kern_coverage import MIN_GAP, Profiles

CLEAR = 20  # units of white the inks keep, measured across
STEP = 2
LIMIT = 600  # no pair needs more: a sign that something else is wrong
KEY = "org.myiadidot.kernCleared"
GUARD_KEY = "org.myiadidot.kernGuarded"  # {letter: [side, ...]}, by kern_groups.py
GUARD = MIN_GAP  # units of white a guarded letter keeps (kern_groups' measure)

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
    # hooks and tails that overhang their advance (derive.SPACING; found by
    # scripts/quality/derived_spacing.py): ɗ ɠ ʄ over a tall letter, ʐ's
    # tail under ) ], the descenders' tails at a foot serif, the opening
    # bracket over a hook below
    *((a, b) for a in ("uni0257", "uni0260", "uni0284", "uni0290", "uni01AD")
      for b in ("l", "h", "k", "b", "exclam", "question", "parenright", "bracketright")),
    *((a, b) for a in ("uni049B", "uni0497", "uni04B3") for b in ("l", "h", "k", "b")),
    *((a, b) for a in ("uni049A", "uni0496", "uni04B2", "uni0198") for b in ("l", "H")),
    *((a, b) for a in ("parenleft", "bracketleft") for b in ("uni0272", "uni0191", "uni0283")),
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
    # the guarded letters have exceptions of their own (guard()): they do
    # not loosen their group's pairs
    held = {s: {n for n, side, _ in guarded(font) if side == s} for s in (1, 2)}
    for left, right in PAIRS:
        if left not in font.groups and left not in font or right not in font.groups and right not in font:
            continue
        # the glyph pairs this entry decides: those with no entry as specific
        pairs = []
        for a in members(font, left):
            for b in members(font, right):
                if (a in held[1] and left != a) or (b in held[2] and right != b):
                    continue
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
    guard(font, record, log)
    if record:
        font.lib[KEY] = record
    return record


def guarded(font):
    """(letter, side, its group) for the guarded letters and their small caps."""
    side = {1: {}, 2: {}}
    for gname, names in font.groups.items():
        for s in (1, 2):
            if gname.startswith(f"public.kern{s}."):
                for m in names:
                    side[s][m] = gname
    for name, sides in sorted(font.lib.get(GUARD_KEY, {}).items()):
        for s in sides:
            for n in (name, name + ".sc"):
                if n in side[s]:
                    yield n, s, side[s][n]


def guard(font, record, log=None):
    """Exceptions for the guarded letters where their group's pairs bring
    them nearer than GUARD (added to record)."""
    _, entry = kern_lookup(font)
    prof = Profiles(font)
    added = {}
    for name, s, group in guarded(font):
        for (left, right), v in list(font.kerning.items()):
            mine, other = (left, right) if s == 1 else (right, left)
            if mine != group or v >= 0:
                continue
            key = (name, other) if s == 1 else (other, name)
            if key in font.kerning or key in added:
                continue
            need = None
            for o in members(font, other):
                a, b = (name, o) if s == 1 else (o, name)
                if entry(a, b) != (left, right):
                    continue  # decided by a more specific entry
                gap = prof.gap(a, b, v)
                if gap is not None and gap < GUARD:
                    need = max(need or v, v + math.ceil(GUARD - gap))
            if need is not None:
                # loosened past unkerned where even that is too near (the
                # italics' Ľ's apostrophe in V's arm)
                added[key] = need
                if log is not None:
                    log.append(f"kern_clear: guard {key[0]} {key[1]} {v} -> {need}")
        # on the right side, (letter, group) would override the group's own
        # exceptions for single letters of that group: carried over as they are
        if s == 1:
            for left, right in list(added):
                if left != name or right not in font.groups:
                    continue
                for o in members(font, right):
                    if (group, o) in font.kerning and (name, o) not in added and (name, o) not in font.kerning:
                        added[(name, o)] = font.kerning[(group, o)]
    for key, v in added.items():
        font.kerning[key] = v
        record[f"{key[0]} {key[1]}"] = "added"


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
