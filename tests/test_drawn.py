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
