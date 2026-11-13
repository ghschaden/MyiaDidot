"""Kerning that keeps letters apart: pairs whose inks would touch or run
into each other are loosened just enough to leave CLEAR units between them.

    python scripts/kern_clear.py UFO [--dry-run]

Run on the Regular; make_italic.py and make_bold.py apply it to the styles
they make (after their own kerning), and smallcaps.py again after the small
caps' kerning, so the values follow each style's outlines. Only the entries
of entries() are touched (reviewed collisions: PAIRS, and the sign pairs
found by scripts/quality/collisions.py, glyph by glyph):
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
unkerned where even that is too near). A guarded member that an entry's
group decides gets its own exception where the group's value leaves it
touching. Idempotent.
"""

import argparse
import math
import sys
import unicodedata
from pathlib import Path

import pathops
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))
import respace
from kern_coverage import MIN_GAP, Profiles

CLEAR = 20  # units of white the inks keep, measured across
# a sign beside a letter keeps more (chosen on running text,
# proofs/sign-clearance-*-2026-11-13.pdf): the opening signs before a
# letter, ! ? after one, the other closing signs after one
OPEN_CLEAR = 100
MARK_CLEAR = 60
CLOSE_CLEAR = 40
MARKS = ("exclam", "question")
ROW_MARGIN = 20  # rows 10 units apart may miss ink between them: two rows either way
STEP = 2
LIMIT = 600  # no pair needs more: a sign that something else is wrong
KEY = "org.myiadidot.kernCleared"
GUARD_KEY = "org.myiadidot.kernGuarded"  # {letter: [side, ...]}, by kern_groups.py
GUARD = MIN_GAP  # units of white a guarded letter keeps (kern_groups' measure)
# letters guarded against only these left entries, not in all their pairs
# (GUARD_KEY's): the accented round letters before ſ and ſſ, kerned -60
# (Bold Italic -80) so that ſ's hook overhangs them (ſc too
# wide, 2026-11-05), the accent then under the hook; their other pairs
# left as they were (review: A.sc ö.sc kept at -78)
GUARDED_AGAINST = {
    **{name: ("longs", "longs_longs") for name in (
        "ccaron", "ebreve", "ecaron", "edieresis", "emacron", "obreve", "odieresis", "omacron", "otilde",
        "uni01ED", "uni1E15", "uni1E17", "uni1E21", "uni1E4D", "uni1E51", "uni1E53", "uni1EBD", "uni1EE1")},
}

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
    # the opening signs over j's hook (Regular, Bold: [j (j; found by
    # scripts/quality/collisions.py, 2026-11-13)
    *((o, "public.kern2.j") for o in ("parenleft", "bracketleft", "braceleft", "exclamdown", "questiondown")),
]

# The signs set beside letters, by character (scripts/quality/collisions.py
# sweeps them; sets() takes the letters and figures from the font)
CLOSERS = "?!)]}”“’*:;"
OPENERS = "([{„“‘¿¡"
NOTE_LETTERS = ("ordfeminine", "ordmasculine")  # ª º: set after a word, as the superiors
FIGURE_SUFFIXES = {"pf", "tf", "zero"}
F_FAMILY = ("f", "longs", "ff", "fi", "fl", "ffi", "ffl")  # f ſ and their ligatures (f_b, longs_t ...)


def sets(font):
    """{name: [glyph names]} for LETTERS FIGURES CAPITALS CLOSERS OPENERS
    SUPERIORS F_FAMILY, as docs/claude/collisions.md defines them: taken
    from the font, so a new letter is in them the day it is added."""
    from make_bold import LINING_FIGURES, SMALL_SUFFIXES

    cut_for = respace.classifier(font, 1, 1)
    superiors = [f + SMALL_SUFFIXES[0] for f in LINING_FIGURES if f + SMALL_SUFFIXES[0] in font]
    superiors += [n for n in NOTE_LETTERS if n in font]
    letters = sorted(g.name for g in font if g.width and cut_for(g.name) and g.name not in superiors)
    oldstyle = tuple(f + "oldstyle" for f in LINING_FIGURES)
    figures, lining = [], []
    for g in font:
        base, *suffixes = g.name.split(".")
        if base in LINING_FIGURES + oldstyle and set(suffixes) <= FIGURE_SUFFIXES:
            figures.append(g.name)
            if base in LINING_FIGURES:
                lining.append(g.name)

    def first_char(name):
        base = name.split(".")[0].split("_")[0]
        if "." not in name and "_" not in name and font[name].unicode is not None:
            return chr(font[name].unicode)
        g = font[base] if base in font else None
        if g is not None and g.unicode is not None:
            return chr(g.unicode)
        return respace.NAMES.get(base) or respace.agl.toUnicode(base)[:1]

    def small(name):
        return name.partition(".")[2].split(".")[0] in ("sc", "c2sc")

    def capital(name):
        c = first_char(name)
        return not small(name) and bool(c) and unicodedata.category(c) == "Lu"

    def by_char(chars):
        cmap = {g.unicode: g.name for g in font if g.unicode is not None}
        return [cmap[ord(c)] for c in chars if ord(c) in cmap]

    return {
        "LETTERS": letters,
        "FIGURES": sorted(figures),
        "CAPITALS": sorted([n for n in letters if capital(n)] + lining),
        "CLOSERS": by_char(CLOSERS),
        "OPENERS": by_char(OPENERS),
        "SUPERIORS": superiors,
        "F_FAMILY": [n for n in letters if not small(n) and (
            n.split(".")[0] in F_FAMILY or n.split(".")[0].split("_")[0] in ("f", "longs"))],
    }


def entries(font):
    """PAIRS and the glyph pairs of a sign and a letter or figure: every
    opening sign before one, every closing sign after one, and the case
    forms beside the capitals (reviewed 2026-11-13). Each glyph pair its
    own entry, so that one member's overhang does not loosen its group;
    kern_clear adds one only where the inks come nearer than clearance()."""
    s = sets(font)
    words = s["LETTERS"] + s["FIGURES"]
    out = list(PAIRS)
    out += [(o, b) for o in s["OPENERS"] for b in words]
    out += [(a, c) for a in words for c in s["CLOSERS"]]
    out += [(o + ".case", b) for o in s["OPENERS"] if o + ".case" in font for b in s["CAPITALS"]]
    out += [(a, c + ".case") for c in s["CLOSERS"] if c + ".case" in font for a in s["CAPITALS"]]
    return list(dict.fromkeys(out))


SIGN_NAMES = {}


def sign_names():
    """{"open": names, "close": names} of the signs, by the characters
    (the AGL names; a font without one has no pair with it)."""
    from fontTools import agl

    return {k: {agl.UV2AGL.get(ord(c), f"uni{ord(c):04X}") for c in chars}
            for k, chars in (("open", OPENERS), ("close", CLOSERS))}


def clearance(left, right):
    """The white a pair keeps across: a sign's own (OPEN_CLEAR before a
    letter, MARK_CLEAR for ! ? after one, CLOSE_CLEAR for the other
    closing signs), else CLEAR. left and right are glyph names or kerning
    keys; “ ‘ open before a letter and close after one."""
    a, b = (n.removesuffix(".case") for n in (left, right))
    if not SIGN_NAMES:
        SIGN_NAMES.update(sign_names())
    if a in SIGN_NAMES["open"]:
        return OPEN_CLEAR
    if b in MARKS:
        return MARK_CLEAR
    if b in SIGN_NAMES["close"]:
        return CLOSE_CLEAR
    return CLEAR


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

    def touch(self, a, b, kern, clear=CLEAR):
        """Do a's ink and b's, set after it with kern, come within clear
        units (CLEAR unless given; scripts/quality/collisions.py asks
        for less to measure the white left)?"""
        dx = self.font[a].width + kern - clear
        both = pathops.op(self.path(a, 0), self.path(b, dx), pathops.PathOp.INTERSECTION)
        return abs(both.area) > 1


def needed(ink, pairs, kern, clear=CLEAR):
    """The kerning, from kern up, at which no pair comes within clear
    (None: kern does)."""
    v = kern
    while any(ink.touch(a, b, v, clear=clear) for a, b in pairs):
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
    prof = Profiles(font)
    record = {}
    # the guarded letters have exceptions of their own (guard()): they do
    # not loosen their group's pairs
    held = {s: {n for n, side, _ in guarded(font) if side == s} for s in (1, 2)}
    for left, right in entries(font):
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
        c = clearance(left, right)
        # cheap first: the rows show which pairs cannot come within c
        pairs = [(a, b) for a, b in pairs if (g := prof.gap(a, b, kern)) is not None and g < c + ROW_MARGIN]
        v = needed(ink, pairs, kern, clear=c) if pairs else None
        if v is not None:
            font.kerning[(left, right)] = v
            record[f"{left} {right}"] = "added" if was is None else was
            if log is not None:
                log.append(f"kern_clear: {left} {right} {kern} -> {v}")
    guard(font, record, log)
    # a guarded member was left out of its group's entry above (its accent
    # must not loosen the group) but takes the entry's value all the same,
    # unless guard() gave it an exception: where that value leaves it
    # touching, an exception of its own (the Bold's ( ɉ, 2026-11-13)
    _, entry = kern_lookup(font)
    for left, right in entries(font):
        if (left, right) not in font.kerning:
            continue
        own = {}
        for a in members(font, left):
            for b in members(font, right):
                mine = (a, right) if a in held[1] and left != a else (left, b) if b in held[2] and right != b else None
                if mine is not None and mine not in font.kerning and entry(a, b) == (left, right):
                    own.setdefault(mine, []).append((a, b))
        for mine, its in own.items():
            v = needed(ink, its, font.kerning[(left, right)], clear=clearance(left, right))
            if v is not None:
                font.kerning[mine] = v
                record[f"{mine[0]} {mine[1]}"] = "added"
                if log is not None:
                    log.append(f"kern_clear: {mine[0]} {mine[1]} (guarded) -> {v}")
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
    full = list(guarded(font))
    held = {(n, s) for n, s, _ in full}
    only = [(n, 2, group, against) for n, (group, against) in sorted(
        (n, (g, a)) for n, a in GUARDED_AGAINST.items()
        for g in [next((k for k, m in font.groups.items() if k.startswith("public.kern2.") and n in m), None)]
        if g is not None and (n, 2) not in held)]
    # the letters guarded on the left first, each one's exceptions in the
    # kerning before the next is measured: a member of a right group with
    # an exception of its own (ᵬ against ɉ) then answers by it and is not
    # measured for its group, so one member's accent no longer loosens the
    # whole group (b o p ... before ɉ; tried 2026-11-04, rebuilt 2026-11-08)
    for name, s, group, against in sorted([(*t, None) for t in full] + only, key=lambda t: t[1]):
        for (left, right), v in list(font.kerning.items()):
            mine, other = (left, right) if s == 1 else (right, left)
            # a pair at 0 too: the italics keep the upright's pairs they set
            # plain at 0 (italic_kerning.apply), and a member's accent may
            # still reach the other letter there
            if mine != group or v > 0 or (against is not None and other not in against):
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
