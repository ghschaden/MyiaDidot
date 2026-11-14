"""The short f (TODO.md phase 2, 2026-11-14): calt sets f.short and
ff.short before a letter whose mark or ascender f's hook meets (fî fǐ fä
fľ). Its class in features.fea holds every Latin lowercase letter the
f of the Regular and the Bold comes within kern_clear.ACCENT_CLEAR of
(kern_clear.short_f_letters); the ligatures still form; the italics'
short fs are their f and ff."""

import re
import sys

import pytest
import ufoLib2
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import kern_clear

REGULAR = ROOT / "sources" / "MyiaDidot-Regular.ufo"


def calt_class():
    text = (REGULAR / "features.fea").read_text(encoding="utf-8")
    m = re.search(r"@ShortFBefore = \[(.*?)\];", text, re.DOTALL)
    assert m, "caltShortF's class @ShortFBefore not in features.fea"
    return set(m[1].replace("\\", " ").split())


@pytest.mark.parametrize("style", ["Regular", "Bold"])
def test_class_holds_the_measured_letters(style):
    font = ufoLib2.Font.open(ROOT / "sources" / f"MyiaDidot-{style}.ufo")
    missing = sorted(set(kern_clear.short_f_letters(font)) - calt_class())
    assert not missing, f"f's hook meets these, not in @ShortFBefore (features.fea): {missing}"


def test_italic_short_f_is_its_f(ufo, ufo_path):
    if "Italic" not in ufo_path.stem:
        pytest.skip("the uprights draw their own")
    font = ufo
    for name, base in (("f.short", "f"), ("ff.short", "ff")):
        g = font[name]
        assert not g.contours and [c.baseGlyph for c in g.components] == [base], name
        assert g.width == font[base].width, name


def test_shaping(shaper, ufo_path):
    def names(text, **kw):
        return [g for g, *_ in shaper.shape(text, **kw)]

    assert names("fî")[0] == "f.short"
    assert names("ffî")[0] == "ff.short"
    assert names("fľ")[0] == "f.short"
    assert names("fi") == ["fi"]
    assert names("fl") == ["fl"]
    assert names("fa")[0] == "f"
    # liga off: the short f where the hook meets the next letter
    assert names("fl", features={"liga": False})[0] == "f.short"
    # Turkish keeps f and i apart (the dot): f.short there
    assert names("fi", language="tr")[0] == "f.short"
