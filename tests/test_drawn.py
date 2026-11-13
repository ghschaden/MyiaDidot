"""Glyphs marked drawn (scripts/drawn.py) come back as saved."""

import ufoLib2
from drawn import KEY, restore, saved, stale
from ufoLib2.objects import Glyph


def square(name, x):
    g = Glyph(name)
    pen = g.getPen()
    pen.moveTo((x, 0))
    pen.lineTo((x + 100, 0))
    pen.lineTo((x + 100, 100))
    pen.lineTo((x, 100))
    pen.closePath()
    g.width = 200 + x
    return g


def test_saved_and_restored(tmp_path):
    font = ufoLib2.Font()
    font.layers.defaultLayer.insertGlyph(square("H", 3), "H")
    font.layers.defaultLayer.insertGlyph(square("I", 0), "I")
    font["H"].lib[KEY] = {"date": "2026-11-03", "why": "test", "source": ""}
    font.save(tmp_path / "MyiaDidot-BoldItalic.ufo")
    kept = saved(tmp_path / "MyiaDidot-BoldItalic.ufo")
    assert list(kept) == ["H"]
    made = ufoLib2.Font()  # the generator's own, made anew
    made.layers.defaultLayer.insertGlyph(square("H", 0), "H")
    made.layers.defaultLayer.insertGlyph(square("I", 9), "I")
    assert restore(kept, made) == ["H"]
    assert made["H"].width == 203 and made["H"].contours[0][0].x == 3 and KEY in made["H"].lib
    assert made["I"].width == 209  # the others as made
    assert saved(tmp_path / "missing.ufo") == {}


def test_stale_when_the_source_changed():
    from built_from import fingerprint

    source, font = ufoLib2.Font(), ufoLib2.Font()
    source.layers.defaultLayer.insertGlyph(square("H", 0), "H")
    font.layers.defaultLayer.insertGlyph(square("H", 3), "H")
    font["H"].lib[KEY] = {"date": "d", "why": "w", "source": fingerprint(source, "H")}
    assert not stale(font, source)
    source["H"].width += 1
    assert list(stale(font, source)) == ["H"]


def test_restored_on_the_spacing_still_to_come():
    """before the derived letters are made (make_bold), a drawn glyph comes
    back on the side bearings the glyph made anew has then: its spacing
    still to come would otherwise space the finished glyph twice"""
    kept = {"H": square("H", 3)}  # ink 3..103, advance 203: final spacing
    made = ufoLib2.Font()
    made.layers.defaultLayer.insertGlyph(square("H", 27), "H")  # ink 27..127, advance 227
    restore(kept, made, spaced=True)
    assert made["H"].contours[0][0].x == 27 and made["H"].width == 227
    restore(kept, made)
    assert made["H"].contours[0][0].x == 3 and made["H"].width == 203


def test_source_of():
    from pathlib import Path

    from drawn import source_of

    d = Path("sources")
    assert source_of(d / "MyiaDidot-Italic.ufo") == d / "MyiaDidot-Regular.ufo"
    assert source_of(d / "MyiaDidot-Bold.ufo") == d / "MyiaDidot-Regular.ufo"
    assert source_of(d / "MyiaDidot-BoldItalic.ufo") == d / "MyiaDidot-Italic.ufo"


def styled(angle, weight):
    font = ufoLib2.Font()
    font.info.italicAngle = angle
    font.info.openTypeOS2WeightClass = weight
    font.layers.defaultLayer.insertGlyph(square("H", 0), "H")
    return font


def test_mark_sets_the_italics_provenance_only():
    from drawn import SOURCE_KEY, is_drawn, mark, release

    source = styled(0, 400)
    source.layers.defaultLayer.insertGlyph(square("H", 0), "H")
    italic, bold_italic = styled(-15.2, 400), styled(-15.2, 700)
    for font in (italic, bold_italic):
        mark(font, "H", "2026-11-13", "test", source)
        assert is_drawn(font["H"]) and font["H"].lib[KEY]["source"]
    assert italic["H"].lib[SOURCE_KEY] == "drawn"
    assert SOURCE_KEY not in bold_italic["H"].lib
    release(italic, "H")
    assert not is_drawn(italic["H"]) and italic["H"].lib[SOURCE_KEY] == "drawn"
    mark(italic, "H", "d", "w", ufoLib2.Font())
    assert italic["H"].lib[KEY]["source"] == ""


def test_strip_leaves_no_mark():
    from drawn import strip

    font = styled(-15.2, 400)
    font.layers.defaultLayer.insertGlyph(square("I", 0), "I")
    font["H"].lib[KEY] = {"date": "d", "why": "w", "source": ""}
    assert strip(font) == ["H"]
    assert not any(KEY in g.lib for g in font)


def test_a_cleared_draft_flag_keeps_nothing():
    """draft flags are review status only (docs/claude/drawn.md, rule 3)"""
    from make_italic import kept_names

    previous = styled(-15.2, 400)
    previous.layers.defaultLayer.insertGlyph(square("I", 0), "I")
    previous["H"].lib.update({"org.myiadidot.italicSource": "derived", "org.myiadidot.draft": False})
    previous["I"].lib[KEY] = {"date": "d", "why": "w", "source": ""}
    assert kept_names(previous, previous) == ["I"]


def test_make_bold_drops_the_source_styles_marks():
    """rule 5: a glyph taken from the source style and not drawn in this
    one comes back unmarked (make_bold's opening: strip, then restore)"""
    from drawn import strip

    source = styled(-15.2, 400)
    source["H"].lib[KEY] = {"date": "d", "why": "italic", "source": ""}
    source.layers.defaultLayer.insertGlyph(square("I", 0), "I")
    source["I"].lib[KEY] = {"date": "d", "why": "italic", "source": ""}
    own = square("I", 5)
    own.lib[KEY] = {"date": "e", "why": "bold italic", "source": ""}
    strip(source)
    restore({"I": own}, source)
    assert KEY not in source["H"].lib and source["I"].lib[KEY]["why"] == "bold italic"


def committed(style):
    from pathlib import Path

    return ufoLib2.Font.open(Path(__file__).resolve().parents[1] / f"sources/MyiaDidot-{style}.ufo")


def test_the_committed_marks():
    """in the Italic italicSource "drawn" implies the mark; every mark is
    whole; the Bold Italic carries none of the Italic's"""
    from drawn import SOURCE_KEY

    italic, bold_italic = committed("Italic"), committed("BoldItalic")
    assert not [g.name for g in italic if g.lib.get(SOURCE_KEY) == "drawn" and KEY not in g.lib]
    for font in (italic, committed("Bold"), bold_italic):
        assert not [g.name for g in font if KEY in g.lib and not {"date", "why", "source"} <= set(g.lib[KEY])]
    same = [g.name for g in bold_italic if KEY in g.lib and g.name in italic and KEY in italic[g.name].lib
            and (g.lib[KEY]["date"], g.lib[KEY]["why"]) == (italic[g.name].lib[KEY]["date"], italic[g.name].lib[KEY]["why"])]
    assert not same
