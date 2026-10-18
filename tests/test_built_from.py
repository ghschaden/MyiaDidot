"""Derived glyphs follow their bases: built on the bases as they are now.

A glyph made from others (derive.py records which, scripts/built_from.py)
whose base was edited since is built on the old base: rebuild it, or check
it and `built_from.py UFO GLYPH --accept`. An alias (one component, unmoved)
follows its glyph's outline but keeps the width it was given: it must be as
wide as its glyph, unless listed in data/alias-widths.txt (per style,
alias-widths-Bold.txt ...), which only shrinks.
"""

from built_from import changed
from conftest import style_data
from test_composites import read_list


def test_derived_glyphs_built_on_current_bases(ufo):
    found = changed(ufo)
    assert not found, ("built on bases changed since (rebuild, or after checking: "
                       f"python scripts/built_from.py UFO GLYPH ... --accept): {found}")


def alias_widths(ufo):
    """{alias: "width / glyph width"} for aliases not as wide as their glyph."""
    out = {}
    for g in ufo:
        if g.contours or len(g.components) != 1:
            continue
        c = g.components[0]
        if tuple(c.transformation) != (1, 0, 0, 1, 0, 0) or c.baseGlyph not in ufo:
            continue
        if ufo[c.baseGlyph].width != g.width:
            out[g.name] = f"{g.width} / {c.baseGlyph} {ufo[c.baseGlyph].width}"
    return out


def test_aliases_as_wide_as_their_glyph(ufo, ufo_path):
    listed = read_list(style_data("alias-widths.txt", ufo_path).name)
    found = alias_widths(ufo)
    new = {k: v for k, v in found.items() if k not in listed}
    stale = sorted(set(listed) - set(found))
    assert not new, f"aliases not as wide as their glyph (a stale width?): {new}"
    assert not stale, f"alias widths fixed, remove from the list: {stale}"


def test_an_edited_base_is_found():
    import ufoLib2
    from conftest import SOURCES

    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-Regular.ufo")
    font["a"].anchors[0].x += 10  # ɐ took its anchors from a's
    assert "uni0250" in changed(font)
