"""Accepted glyphs are as the person accepted them.

scripts/accepted.py records a visual acceptance in the glyph's lib (date,
review, fingerprint) without freezing the glyph: the generators make it
anew and carry the record over. A glyph changed since, by an edit or a
generator, fails here: look at it again, then accept it anew
(accepted.py UFO GLYPH --date --review) or --withdraw.
"""

import ufoLib2
from accepted import KEY, acceptances, carry, changed, stamp
from conftest import ROOT


def test_accepted_glyphs_unchanged(ufo):
    assert not changed(ufo), f"changed since accepted (review, then accepted.py again): {sorted(changed(ufo))}"


def test_acceptances_name_their_review(ufo):
    for name, acceptance in acceptances(ufo).items():
        review = acceptance["review"]
        assert acceptance["date"] and review, name
        if review.startswith(("docs/", "proofs/")):
            assert (ROOT / review).exists(), f"{name}: {review} missing"


def test_carry_keeps_acceptance_on_a_glyph_made_anew():
    font = ufoLib2.Font()
    g = font.newGlyph("a")
    g.width = 500
    stamp(font, "a", "2026-10-26", "docs/x.md")
    accepted = acceptances(font)
    del font["a"]
    font.newGlyph("a").width = 500
    carry(accepted, font)
    assert font["a"].lib[KEY]["date"] == "2026-10-26"
    assert not changed(font)
    font["a"].width = 510
    assert changed(font) == {"a": accepted["a"]}
    # another style's acceptance (the Bold begins as the Regular's glyphs) is not carried
    font.newGlyph("b")
    stamp(font, "b", "2026-10-26", "docs/x.md")
    carry({}, font)
    assert not acceptances(font)
