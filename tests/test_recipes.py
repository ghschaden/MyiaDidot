"""Metadata that breaks things silently.

A recipe written with the wrong code point builds a letter nobody asked for
(Ꞁ L with belt, U+A7AD, was once typed as U+A780, the turned L: they look
alike in an editor). And a combining mark the font calls a base glyph is
never positioned (the combining cedilla and ogonek were so, and every
decomposed ç put its cedilla 110 units low)."""

import sys
import unicodedata

import ufoLib2
from conftest import ROOT, SOURCES

sys.path.insert(0, str(ROOT / "scripts"))

# characters made by recipes beyond the target, on purpose
EXTRA = {"‐", "‑"}  # hyphen, non-breaking hyphen: the hyphen-minus's shape


def test_recipes_make_wanted_characters():
    import coverage
    import derive
    import glyphsets

    wanted = set()
    for name in coverage.TARGET:
        wanted |= set(glyphsets.unicodes_per_glyphset(name))
    regular = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    have = {u for g in regular for u in g.unicodes}

    def ok(ch):
        if ord(ch) in wanted or ch in EXTRA:
            return True
        # a case counterpart of a wanted letter, or of one the font has
        # (Ꞁ of ɬ, Ʀ of ʀ, Ϳ of ϳ): fontbakery's case mapping asks for them
        return any(len(c) == 1 and c != ch and (ord(c) in wanted or ord(c) in have)
                   for c in (ch.lower(), ch.upper()))

    # a variant (ɔ.sc, б.loclSRB) by its character
    odd = [f"{ch} U+{ord(ch[0]):04X} {unicodedata.name(ch[0], '?')}"
           for ch, *_ in derive.RECIPES if not ok(ch[0] if derive.variant(ch) else ch)]
    assert not odd, f"recipes for characters outside the target (a wrong code point?): {odd}"


def test_combining_marks_are_marks(ufo):
    cats = ufo.lib.get("public.openTypeCategories", {})
    bad = [f"{g.name} U+{g.unicode:04X}" for g in ufo
           if g.unicode is not None and unicodedata.category(chr(g.unicode)) == "Mn"
           and cats.get(g.name) != "mark"]
    assert not bad, f"combining marks not categorised as marks (never positioned): {bad}"
