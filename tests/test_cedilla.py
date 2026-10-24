"""Capital cedilla tips remain buried in their attached letters."""

from copy import deepcopy

import pytest
import ufoLib2
from cedilla import finish
from conftest import ROOT
from glyph_lint import lint


@pytest.mark.parametrize("style", ["Bold", "Italic", "BoldItalic"])
def test_cedilla_attachments(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    names = ["Ccedilla", "Scedilla", "ccedilla.sc", "Cedilla"]
    assert not lint(font, names)
    # Recreate an overlong attachment, then shorten it without changing
    # the visible body, attachment anchors, or composite placements.
    mark = font["Cedilla"]
    max((p for c in mark.contours for p in c.points), key=lambda p: p.y).y = -87
    before = deepcopy(font)
    finish(font)
    for name in font.keys():
        if name != "Cedilla":
            assert font[name] == before[name]
    assert mark.anchors == before["Cedilla"].anchors
    assert mark.width == before["Cedilla"].width
    for contour, original in zip(mark.contours, before["Cedilla"].contours):
        for point, old in zip(contour.points, original.points):
            if old.y <= -122:
                assert point == old
    assert not lint(font, names)
    settled = deepcopy(mark)
    finish(font)
    assert mark == settled
