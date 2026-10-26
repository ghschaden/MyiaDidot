"""Hinting: letters end on their alignment zones, TrueType and CFF.

Each style is built as a TTF as `make ttf` does (components flattened,
overlaps removed: fontmake's defaults, which decide the point order) and
hinted by scripts/hint_control.py; scripts/quality/hint_zones.py then lists
the letters' outer contours that end half a pixel or more off their zone's row
(8 to 32 ppem, FreeType's v40 and v35 interpreters).  Each style has its list
of known ones, data/hint-zones.txt (the Regular's), hint-zones-Italic.txt
...: one "interpreter glyph:zone count" per line with a reason.  A new one
fails, and so does a listed one that is gone (delete its line).
After an intended change: scripts/update_test_data.py --hinting.

The CFF fonts likewise (test_cff_hint_zones): an OTF built as `make otf`
does (overlaps removed: conftest's OTF keeps them, and otfautohint then
leaves hundreds of letters off their zones), hinted by scripts/ps_hints.py, measured by whole glyphs with
FreeType's CFF engine (hint_zones.measure_cff), against hint-zones-cff.txt,
hint-zones-cff-Italic.txt ...
"""
import shutil
import sys

from conftest import ROOT, style_data
from test_composites import read_list

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
from font_builds import compiled_variant
from hint_control import hint  # noqa: E402
from hint_zones import INTERPRETERS, measure, measure_cff, summary  # noqa: E402
from ps_hints import hint as ps_hint  # noqa: E402


def hinting_keys(ufo_path, tmp):
    """{"v40 glyph:top1434 count": ""} for a style, hinted as `make ttf` does."""
    unhinted, hinted = tmp / "unhinted.ttf", tmp / "hinted.ttf"
    shutil.copyfile(compiled_variant(ufo_path, "hint_ttf"), unhinted)
    hint(unhinted, hinted)
    keys = {}
    for version in INTERPRETERS:
        for contour, count in summary(measure(hinted, interpreter=version)).items():
            keys[f"v{version} {contour} {count}"] = ""
    return keys


def cff_hinting_keys(ufo_path, tmp):
    """{"cff glyph:top1434 count": ""} for a style, built and hinted as
    `make otf` does."""
    hinted = tmp / "hinted.otf"
    shutil.copyfile(compiled_variant(ufo_path, "cff_otf"), hinted)
    ps_hint(hinted)
    return {f"cff {glyph} {count}": "" for glyph, count in summary(measure_cff(hinted)).items()}


def check(listed, found):
    new = sorted(set(found) - set(listed))
    stale = sorted(set(listed) - set(found))
    assert not new, ("letters hinted off their zones (python scripts/quality/hint_zones.py FONT; "
                     f"if intended: update_test_data.py --hinting): {new}")
    assert not stale, f"hinting findings fixed, remove from the list: {stale}"


def test_cff_hint_zones(ufo_path, tmp_path):
    check(read_list(style_data("hint-zones-cff.txt", ufo_path).name), cff_hinting_keys(ufo_path, tmp_path))


def test_hint_zones(ufo_path, tmp_path):
    check(read_list(style_data("hint-zones.txt", ufo_path).name), hinting_keys(ufo_path, tmp_path))
