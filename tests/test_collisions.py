"""Letters and figures meeting the signs beside them (phase 1's sweep).

scripts/quality/collisions.py sets every letter and figure before the
closing signs and superiors, after the opening ones, and the capitals
beside the case forms, at the kerning each pair takes, and finds those
with less white across than kern_clear.clearance asks (20, or a
sign's own). Each style's known ones are in data/collisions.txt (collisions-Italic.txt ...), "left right
white  # date reason": a new pair fails, a listed one no longer found
fails (delete its line), and one whose white fell more than SLACK under
the listed value fails (it got worse). A line is added only with a dated
reason, in the commit that brings the pair (docs/claude/collisions.md).
"""

import sys
from functools import cache

import pytest
import ufoLib2
from conftest import DATA, ROOT, UFO_PATHS, style_data

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import collisions
import kern_clear

SLACK = 4  # a run's rounding, not a change


def read(path):
    """{(left, right): white} from an exception list."""
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            fields = line.split("#", 1)[0].split()
            if fields:
                left, right, w = fields
                out[(left, right)] = int(w)
    return out


@cache
def found(ufo_path):
    font = ufoLib2.Font.open(ufo_path)
    pairs, _ = collisions.sweep(font)
    return {(a, b): w for a, b, _, w in pairs}


def test_collisions(ufo_path):
    path = style_data("collisions.txt", ufo_path)
    listed = read(path)
    now = found(ufo_path)
    new = {f"{a} {b} {w}": w for (a, b), w in now.items() if (a, b) not in listed}
    fixed = sorted(f"{a} {b}" for a, b in set(listed) - set(now))
    worse = {f"{a} {b}": f"{listed[(a, b)]} -> {w}" for (a, b), w in now.items()
             if (a, b) in listed and w < listed[(a, b)] - SLACK}
    command = f"python scripts/quality/collisions.py {ufo_path.relative_to(ROOT)} --sheet SHEET.pdf"
    assert not new, (f"letters meeting signs, not in {path.name} (fix by kern_clear.PAIRS, or list "
                     f"with a dated reason; see them: {command}): {sorted(new, key=new.get)[:40]}"
                     f"{f' and {len(new) - 40} more' if len(new) > 40 else ''}")
    assert not worse, f"collisions worse than listed in {path.name}: {worse}"
    assert not fixed, f"collisions fixed, delete their lines in {path.name}: {fixed}"


# the tool itself

def boxes(gap):
    """A font of two rectangles: 'a' 0-100 wide 100, 'b' set gap after it."""
    font = ufoLib2.Font()
    for name, x0 in (("a", 0), ("b", gap)):
        g = font.newGlyph(name)
        g.width = 100 if name == "a" else 100 + gap
        pen = g.getPen()
        pen.moveTo((x0, 0))
        pen.lineTo((x0, 500))
        pen.lineTo((x0 + 100, 500))
        pen.lineTo((x0 + 100, 0))
        pen.closePath()
    return font


@pytest.mark.parametrize("gap, expect", [(12, 12), (-7, -8), (20, 20), (40, 20)])
def test_white(gap, expect):
    font = boxes(gap)
    assert collisions.white(kern_clear.Ink(font), "a", "b", 0) == expect
    listed, _ = collisions.sweep(font, pairs={("a", "b")})
    assert (len(listed) == 1) == (expect < kern_clear.CLEAR)


REGULAR = next(p for p in UFO_PATHS if p.stem.endswith("-Regular"))


def test_finds_what_kern_clear_clears():
    """With kern_clear's entries undone, the sweep lists ( ɲ, which
    kern_clear.PAIRS holds; and no pair kern_clear decides is listed as the
    Regular is."""
    font = ufoLib2.Font.open(REGULAR)
    _, entry = kern_clear.kern_lookup(font)
    now = found(REGULAR)
    for left, right in kern_clear.entries(font):
        for a in kern_clear.members(font, left):
            for b in kern_clear.members(font, right):
                assert not (entry(a, b) == (left, right) and (a, b) in now), (a, b)
    kern_clear.undo(font)
    undone, _ = collisions.sweep(font)
    assert ("parenleft", "uni0272") in {(a, b) for a, b, _, _ in undone}


def test_row_filter_loses_nothing():
    font = ufoLib2.Font.open(REGULAR)
    exact, _ = collisions.sweep(font, exact=True)
    assert {(a, b): w for a, b, _, w in exact} == found(REGULAR)


def test_lists_named_as_the_styles():
    names = {style_data("collisions.txt", p).name for p in UFO_PATHS}
    assert {p.name for p in DATA.glob("collisions*.txt")} <= names


# Capitals before ascenders (kern_clear.ascender_entries, Üb on the
# pangram page, 2026-11-13): the top serifs keep ASCENDER_CLEAR every way
ASCENDER_PAIRS = [("U", "b"), ("Udieresis", "b"), ("Udieresis", "l"), ("N", "l"), ("H", "h"),
                  ("V", "h"), ("W", "k"), ("Y", "b"), ("J", "b"), ("K", "h"), ("I", "l")]


def test_capitals_clear_ascenders(ufo_path):
    font = ufoLib2.Font.open(ufo_path)
    ink = kern_clear.Ink(font)
    _, entry = kern_clear.kern_lookup(font)
    short = []
    for a, b in ASCENDER_PAIRS:
        k = font.kerning[e] if (e := entry(a, b)) else 0
        w = ink.white_above(a, b, k)
        if w is not None and w < kern_clear.ASCENDER_CLEAR - kern_clear.SAMPLE:
            short.append(f"{a} {b} {w:.0f}")
    assert not short, f"capitals nearer than ASCENDER_CLEAR to an ascender: {short} (run scripts/kern_clear.py)"


ACCENT_PAIRS = [("N", "uni01D0"), ("U", "uni01D0"), ("H", "uni0209"), ("T", "uni0209"), ("U", "ibreve"),
                ("F", "idieresis"), ("Gamma", "uni1FD6"), ("Upsilon", "iotadieresis"), ("uni0474", "uni0457")]


def test_capitals_clear_marks_above(ufo_path):
    """N ǐ, H ȉ, Γ ῖ: a lowercase mark over the capital's serif (kern_clear.accent_entries)."""
    font = ufoLib2.Font.open(ufo_path)
    ink = kern_clear.Ink(font)
    _, entry = kern_clear.kern_lookup(font)
    short = []
    for a, b in ACCENT_PAIRS:
        k = font.kerning[e] if (e := entry(a, b)) else 0
        w = ink.white_above(a, b, k, kern_clear.ACCENT_CLEAR)
        if w is not None and w < kern_clear.ACCENT_CLEAR - kern_clear.SAMPLE:
            short.append(f"{a} {b} {w:.0f}")
    assert not short, f"capitals nearer than ACCENT_CLEAR to a mark above: {short} (run scripts/kern_clear.py)"


def test_marked_lowercase():
    """the dotted and accented lowercase, not the ascenders, small caps or plain letters."""
    font = ufoLib2.Font.open(REGULAR)
    right = {b for _, b in kern_clear.accent_entries(font)}
    assert {"i", "j", "uni01D0", "uni0209", "idieresis", "uni1FD6", "uni0457", "uni0451"} <= right
    assert not {"n", "o", "dotlessi", "lcaron", "b", "iacute.sc", "aogonek"} & right


def test_ascenders_by_their_base_letter():
    """ľ ḷ by their l, the dotted letters not by their dot, t not at all."""
    asc = set(kern_clear.sets(ufoLib2.Font.open(REGULAR))["ASCENDERS"])
    assert {"b", "l", "lcaron", "uni1E37", "thorn", "uni0431"} <= asc
    assert not {"i", "j", "ibreve", "icircumflex", "uni0456", "uni0457", "ij", "t"} & asc


# The guard's result (kern_clear.guard), held on the UFO after every step of
# the generators, so that none of them has to remember it (the italic rule
# once dropped b v, b j, o j, and ᵬ ổ ồ lost their exceptions;
# docs/claude/collisions.md, "The guard's result held by a test"). Measured
# as the guard measures (kern_coverage.Profiles, GUARD), not by Ink.

FROM = {"Italic": "Regular", "Bold": "Regular", "BoldItalic": "Italic"}  # the style each is made from


def style_of(ufo_path):
    return ufo_path.stem.rsplit("-", 1)[1]


def short_of_guard(font, pairs):
    """The pairs (a, b) of a guarded letter nearer than GUARD at the value they take."""
    from kern_coverage import Profiles

    _, entry = kern_clear.kern_lookup(font)
    prof = Profiles(font)
    out = []
    for a, b in pairs:
        e = entry(a, b)
        k = font.kerning[e] if e else 0
        gap = prof.gap(a, b, k)
        if gap is not None and gap < kern_clear.GUARD:
            out.append(f"{a} {b} {k} ({gap:.1f})")
    return out


def test_guard_keys_kept(ufo_path):
    """A group pair kerned (<= 0) in the style this one is made from, whose
    group holds a guarded member, stays a key here (at any value), or every
    guarded member beside the other side keeps GUARD at what it takes now."""
    style = style_of(ufo_path)
    if style not in FROM:
        pytest.skip("the Regular is the master")
    font = ufoLib2.Font.open(ufo_path)
    source = ufoLib2.Font.open(ufo_path.with_name(ufo_path.name.replace(style, FROM[style])))
    held = {}
    for name, side, group in kern_clear.guarded(source):
        held.setdefault((side, group), []).append(name)
    pairs = set()
    for (left, right), v in source.kerning.items():
        if v > 0 or (left, right) in font.kerning:
            continue
        for side, group, other in ((1, left, right), (2, right, left)):
            for name in held.get((side, group), []):
                if name in font:
                    pairs |= {(name, o) if side == 1 else (o, name) for o in kern_clear.members(font, other)}
    short = short_of_guard(font, sorted(pairs))
    assert not short, (f"group pairs of the {FROM[style]} dropped, their guarded members now nearer than "
                       f"GUARD (keep the pair, at 0 if need be): {short[:40]}")


def test_guard_white_held(ufo_path):
    """Every guarded letter beside every member of a pair its group has
    (at any value, the pairs guard() walks, and its own exceptions) keeps GUARD at
    the value the pair takes. The pairs clear() measures with Ink (PAIRS,
    the signs, the capitals before ascenders and marks) are left out: their
    own measure and tests hold them, and the two measures differ by a few
    units at the limit."""
    font = ufoLib2.Font.open(ufo_path)
    keys, entry = kern_clear.kern_lookup(font)
    # measured() reads the kerning (which letters f's hook meets, at f's
    # kerning): taken as clear() takes it, after undo(), or the short fs'
    # entries before î ï are missed once kern_clear has cleared f î
    before = ufoLib2.Font.open(ufo_path)
    kern_clear.undo(before)
    inked = {(left, right) for left, right, _ in kern_clear.measured(before)}
    pairs = set()
    for name, side, group, against in kern_clear.guarded_all(font):
        for left, right in font.kerning:
            mine, other = (left, right) if side == 1 else (right, left)
            if mine not in (group, name) or (against is not None and other not in against):
                continue
            for o in kern_clear.members(font, other):
                a, b = (name, o) if side == 1 else (o, name)
                if entry(a, b) != (left, right):
                    continue  # decided by a more specific entry, met in its own turn
                k = keys(a, b)
                # an Ink entry, or a member's exception beyond its group's Ink entry
                if {(left, right), (k[2][0], right), (left, k[1][1])} & inked:
                    continue
                pairs.add((a, b))
    assert pairs
    short = short_of_guard(font, sorted(pairs))
    assert not short, f"guarded letters nearer than GUARD (run scripts/kern_clear.py): {short[:40]}"


# the italics' low quotes (docs/claude/collisions.md, "The italics' „")

BI_FOLLOWS = 12  # the Bold Italic's offset follows the Italic's (tx_offset), its comma its own


def test_low_quotes_stand_as_the_comma(ufo_path):
    """„ and ‚ are the high quote moved down, and the high quote leans right
    of its advance: in the italics they are set where the comma stands, and
    do not overhang what follows (kern_clear mended that letter by letter)."""
    from data_italic import ITALIC_STANDS_AS

    font = ufoLib2.Font.open(ufo_path)
    if not font.info.italicAngle:
        pytest.skip("upright: the high quote stands in its advance")
    slack = 0 if "Bold" not in ufo_path.stem else BI_FOLLOWS
    for name, ref in ITALIC_STANDS_AS.items():
        g = font[name]
        left, _, right, _ = g.getBounds(font)
        assert abs(left - font[ref].getBounds(font).xMin) <= slack, f"{name}: left bearing {left}, {ref}'s differs"
        assert right <= g.width, f"{name} overhangs its advance by {right - g.width}"
