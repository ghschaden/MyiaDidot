"""A capital construction reference calibrates findings without hiding faults."""

import sys

import pytest
import ufoLib2
from conftest import ROOT, SOURCES

sys.path.insert(0, str(ROOT / "scripts/quality"))
from case_reference import KEY, case_reference, reference_top
from checks import Shapes, zones
from strokes import strokes


@pytest.fixture(params=["Italic", "BoldItalic"])
def referenced_gamma(request):
    font = ufoLib2.Font.open(SOURCES / f"MyiaDidot-{request.param}.ufo")
    font["uni0263.sc"].lib[KEY] = "uni0194"
    return font


def test_gamma_matches_its_capitals_relative_stroke(referenced_gamma):
    found, measures = strokes(referenced_gamma, {"uni0263.sc"})
    assert not found
    assert 0.9 <= measures["uni0263.sc"][1] <= 1.1
    assert case_reference(referenced_gamma, referenced_gamma["o.sc"]) is None


def test_reference_still_finds_an_overweight_gamma(referenced_gamma):
    for contour in referenced_gamma["uni0263.sc"].contours:
        for point in contour.points:
            point.x *= 2
    findings = strokes(referenced_gamma, {"uni0263.sc"})[0]
    assert any(name == "uni0263.sc" and "darker" in detail
               for name, _, _, detail in findings)


def test_reference_inherits_overshoot_and_still_finds_bad_alignment(referenced_gamma):
    font = referenced_gamma
    glyph = font["uni0263.sc"]
    assert abs(glyph.getBounds(font).yMax - reference_top(font, glyph)) <= 6
    assert not any(name == glyph.name for name, *_ in zones(font, Shapes(font)))
    # This would sit near a generic o.sc overshoot, but not its own Ɣ's.
    glyph.move((0, 15))
    assert any(name == glyph.name and which == "top"
               for name, _, which, _ in zones(font, Shapes(font)))


def test_invalid_reference_is_not_silently_accepted(referenced_gamma):
    font = referenced_gamma
    font["uni0263.sc"].lib[KEY] = "H"
    with pytest.raises(ValueError, match="corresponding capital"):
        case_reference(font, font["uni0263.sc"])
