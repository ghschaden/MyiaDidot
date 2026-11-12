"""The local finishing pass fixes the reviewed pieces without moving metrics."""

import copy
import sys

import pathops
import pytest
import ufoLib2
from conftest import ROOT, SOURCES

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/quality"))
from checks import construction
from derive import to_path
from italic_contours import BASES, BODY_JOINS, FOLLOWERS, TARGET_SOURCES, finish, finish_bases
from strokes import strokes


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_reviewed_contours_are_finished_and_stable(style):
    font = ufoLib2.Font.open(SOURCES / f"MyiaDidot-{style}.ufo")
    before = copy.deepcopy(font)
    finish(font, smooth=style == "BoldItalic")
    for glyph in font:
        old = before[glyph.name]
        if glyph.name not in TARGET_SOURCES:
            assert glyph == old, glyph.name
            continue
        assert (glyph.width, glyph.anchors, glyph.lib, glyph.unicodes, glyph.components) == (
            old.width, old.anchors, old.lib, old.unicodes, old.components)
        # These are contour refinements, not a new silhouette or weight.
        a, b = to_path(before, old), to_path(font, glyph)
        delta = pathops.op(a, b, pathops.PathOp.XOR)
        assert abs(delta.area) < abs(a.area) * 0.002 + 1, glyph.name
    assert not construction(font["uni0188"])
    for name in (*BASES, *BODY_JOINS, *FOLLOWERS):
        assert not construction(font[name]), name
    for name in ("uni0291", "uni0284"):
        assert not any(kind == "extreme" for kind, _, _ in construction(font[name])), name
    for name in ("uni0496", "uni0497", "uni049A", "uni049B"):
        tail_faults = [(kind, where) for kind, where, _ in construction(font[name])
                       if kind in ("smooth", "kink", "extreme") and int(where.split(",")[1]) < 0]
        assert not tail_faults, (name, tail_faults)
    assert font.kerning == before.kerning
    assert font.lib == before.lib
    assert font.features == before.features
    if style == "Italic":
        # Fairing қ's leg must retain the base's weight, not shave the
        # already light outer edge to bring its handle into line.
        measured = strokes(font, {"uni049B"})[1]["uni049B"]
        original = strokes(before, {"uni049B"})[1]["uni049B"]
        assert measured[0] >= original[0]
        # (0.88 since к was redrawn onto clean nodes: 151 -> 148, the old
        # outline's bulge not kept; accepted by the designer 2026-11-12)
        assert measured[1] >= 0.88
    settled = copy.deepcopy(font)
    finish(font, smooth=style == "BoldItalic")
    assert all(glyph == settled[glyph.name] for glyph in font)


def test_empty_selection_and_reviewed_letters_are_untouched():
    font = ufoLib2.Font()
    font.info.italicAngle = -15.2
    for name in ("c", "uni0188", "uni0291", "uni0416", "uni0436"):
        glyph = font.newGlyph(name)
        # An intentional tiny detached piece would be removed by generic
        # cleanup. Neither an unrelated base nor a kept drawing may lose it.
        pen = glyph.getPen()
        for x, y, w, h in ((0, 0, 500, 700), (1000, 1000, 1, 1)):
            pen.moveTo((x, y))
            pen.lineTo((x + w, y))
            pen.lineTo((x + w, y + h))
            pen.lineTo((x, y + h))
            pen.closePath()
    font["uni0188"].lib["org.myiadidot.italicSource"] = "drawn"
    font["uni0291"].lib["org.myiadidot.italicSource"] = "derived"
    font["uni0416"].lib["org.myiadidot.italicSource"] = "drawn"
    font["uni0436"].lib["org.myiadidot.italicSource"] = "Old Standard"
    before = copy.deepcopy(font)
    finish_bases(font, skip={"uni0436"})
    finish(font, skip={"uni0291", "uni0436"})
    assert all(glyph == before[glyph.name] for glyph in font)


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_ka_base_cleanup_preserves_spacing_reference_curves(style):
    font = ufoLib2.Font.open(SOURCES / f"MyiaDidot-{style}.ufo")
    before = copy.deepcopy(font["uni041A"])
    finish_bases(font)
    # Cleaning К's upper serif or splitting its curves can switch the
    # Bold's optical-spacing reference and change three advances by eight
    # units. Only the broken lower-leg tangent belongs to this pass.
    for old, new in zip(before.contours, font["uni041A"].contours, strict=True):
        assert len(old.points) == len(new.points)
        for a, b in zip(old.points, new.points, strict=True):
            if not 180 <= a.y <= 350:
                assert a == b
    assert font["uni041A"].width == before.width
    assert font["uni041A"].anchors == before.anchors
