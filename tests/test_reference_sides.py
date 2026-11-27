"""scripts/quality/reference_sides.py on drawn shapes (TODO T12): a letter
whose hook grows on the other side than every reference's is found, one on
the same side not; a form drawn the other way round is found by the raster
test, a reference symmetric in itself never counts; an italic is measured
deslanted; the small caps are read from features.fea's lookups. No reference
fonts needed: candidates for a sheet, no list or gate yet."""

import math
import sys

import ufoLib2
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import reference_sides as rs  # noqa: E402


def rect(glyph, x0, y0, x1, y1):
    pen = glyph.getPen()
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def face(name, shapes, angle=0, upm=1000):
    """a Face of rectangles: {char: [(x0, y0, x1, y1), ...]}"""
    font = ufoLib2.Font()
    for ch, boxes in shapes.items():
        g = font.newGlyph(f"u{ord(ch):04X}")
        g.unicodes = [ord(ch)]
        g.width = 1000
        for box in boxes:
            rect(g, *box)
    cmap = {u: g.name for g in font for u in g.unicodes}
    return rs.Face(name, font, cmap, angle, {}, upm)


STEM = (100, 0, 200, 700)
H_LEFT = [STEM, (0, 600, 100, 700)]  # a flag out to the left at the top
H_RIGHT = [STEM, (200, 600, 300, 700)]


def test_hook_on_the_other_side_is_found():
    mine = face("Myia", {"l": [STEM], "ł": H_RIGHT})
    refs = [face(n, {"l": [STEM], "ł": H_LEFT}) for n in ("A", "B")]
    notes = rs.side_notes(rs.profile(mine, "ł", "l"), [(r.name, rs.profile(r, "ł", "l")) for r in refs])
    assert any(n.startswith("refs grow L") for n in notes)
    assert any(n.startswith("Myia grows R") for n in notes)
    same = face("Myia", {"l": [STEM], "ł": H_LEFT})
    assert rs.side_notes(rs.profile(same, "ł", "l"), [(r.name, rs.profile(r, "ł", "l")) for r in refs]) == []


def test_units_per_em_do_not_count():
    small = face("A", {"l": [STEM], "ł": H_LEFT})
    big = face("B", {"l": [tuple(2 * v for v in STEM)], "ł": [tuple(2 * v for v in b) for b in H_LEFT]}, upm=2000)
    assert small.stats(small.glyph("ł")) == big.stats(big.glyph("ł"))


def test_italic_measured_deslanted():
    t = math.tan(math.radians(15))
    slanted = ufoLib2.Font()
    g = slanted.newGlyph("l")
    g.unicodes = [ord("l")]
    pen = g.getPen()
    pen.moveTo((100, 0))
    pen.lineTo((100 + 700 * t, 700))
    pen.lineTo((200 + 700 * t, 700))
    pen.lineTo((200, 0))
    pen.closePath()
    f = rs.Face("It", slanted, {ord("l"): "l"}, -15, {})
    (x0, _, x1, _), _ = f.stats("l")
    assert abs((x1 - x0) - 100) < 1e-6


def image_of(boxes):
    return rs.image(face("x", {"l": boxes}), "u006C")


def test_mirrored_form_found_symmetric_reference_ignored():
    hook = [STEM, (200, 0, 400, 100)]  # a foot out to the right
    mirrored = [STEM, (-100, 0, 100, 100)]
    refs = [("A", image_of(hook)), ("B", image_of(hook))]
    found = rs.raster_notes(image_of(mirrored), refs)
    assert [w for w, _ in found] == ["mirrored"]
    assert rs.raster_notes(image_of(hook), refs) == []
    symmetric = [(0, 0, 300, 100), STEM]  # an upturned T: its own mirror
    assert rs.raster_notes(image_of(mirrored), [("A", image_of(symmetric)), ("B", image_of(symmetric))]) == []


def test_small_caps_from_the_feature_lookups():
    text = ("lookup SmallCapsLower {\n    sub \\a by \\a.sc;\n} SmallCapsLower;\n"
            "lookup SmallCapsUpper {\n    sub \\A by \\a.sc;\n    sub \\uni0193 by \\uni0260.sc;\n} SmallCapsUpper;\n")
    cmap = {ord("a"): "a", ord("A"): "A", 0x193: "uni0193", ord("b"): "b"}
    assert rs.sc_from_features(text, cmap) == {ord("a"): "a.sc", ord("A"): "a.sc", 0x193: "uni0260.sc"}
