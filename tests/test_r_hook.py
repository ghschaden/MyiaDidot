"""Italic r shoulders are rounded; retroflex r uses its body and a full hook."""

from copy import deepcopy

import pytest
import ufoLib2
from conftest import DATA, ROOT
from fontTools.ufoLib.glifLib import readGlyphFromString
from glyph_lint import lint
from r_hook import finish, round_shoulder


def restore(glyph, filename):
    glyph.clearContours()
    readGlyphFromString((DATA / filename).read_text(),
                       glyphObject=glyph, pointPen=glyph.getPointPen())


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_r_hook_matches_body_and_preserves_metadata(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    expected = deepcopy(font["uni027D"])
    glyph = font["uni027D"]
    restore(glyph, "r-hook-before-Italic.glif" if style == "Italic" else "r-hook-before.glif")
    before = deepcopy(glyph)
    assert min(p.y for c in glyph.contours for p in c.points) == -275
    finish(font)
    assert glyph == expected
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    assert glyph.lib == before.lib
    assert glyph.unicodes == before.unicodes
    assert min(p.y for c in glyph.contours for p in c.points) == -420
    # The entire body above the attachment and its outer stem are the
    # final r's actual points; this also checks propagation of its shoulder.
    body, hook = font["r"].contours[0].points, glyph.contours[0].points
    assert [p for p in body if p.y > 130] == [p for p in hook if p.y > 130]
    assert not lint(font, ["r", "uni027D"])
    finish(font)
    assert glyph == expected


@pytest.mark.parametrize("style", ["Italic", "BoldItalic"])
def test_r_shoulder_rounding_is_local_and_idempotent(style):
    font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
    restore(font["r"], f"r-shoulder-before-{style}.glif")
    before = deepcopy(font["r"])
    points = before.contours[0].points
    lo = next(i for i, p in enumerate(points) if p.type and 690 < p.y < 710 and p.x > 600)
    tip = next(i for i, p in enumerate(points) if p.type and 800 < p.y < 825 and p.x > 600)
    assert tip - lo == 9  # Previous shoulder had three small cubics.
    round_shoulder(font)
    glyph = font["r"]
    rounded = glyph.contours[0].points
    new_tip = next(i for i, p in enumerate(rounded) if p.type and (p.x, p.y) == (points[tip].x, points[tip].y))
    assert rounded[:lo + 1] == points[:lo + 1]
    assert rounded[new_tip:] == points[tip:]
    assert all(p.smooth for p in rounded[lo:new_tip + 1] if p.type)
    assert rounded[lo + 1].x == rounded[lo].x
    assert rounded[new_tip - 1].y == rounded[new_tip].y
    assert glyph.width == before.width
    assert glyph.anchors == before.anchors
    expected = deepcopy(glyph)
    round_shoulder(font)
    assert glyph == expected


def test_r_hook_roman_styles_unchanged():
    for style in ("Regular", "Bold"):
        font = ufoLib2.Font.open(ROOT / f"sources/MyiaDidot-{style}.ufo")
        before = deepcopy(font["uni027D"])
        finish(font)
        assert font["uni027D"] == before


def test_bold_inner_stems_do_not_dent():
    from fontTools.misc.bezierTools import calcCubicParameters

    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-Bold.ufo')
    for name in ('r', 'uni027D'):
        points = font[name].contours[0].points
        start = next(i for i, p in enumerate(points) if p.type == 'curve' and p.y == 699)
        curve = points[start:start + 4]
        a, b, c, d = calcCubicParameters(*[(p.x, p.y) for p in curve])
        xs = [a[0] * t**3 + b[0] * t**2 + c[0] * t + d[0] for t in [i / 100 for i in range(101)]]
        assert all(left >= right for left, right in zip(xs, xs[1:]))
        assert min(xs) >= curve[-1].x


def test_bold_italic_turned_r_top_bracket_is_l_s():
    """Bold Italic ɺ's bracket under the top serif is its l's, shifted onto
    its stem (r_hook.finish_turned_r_top); emboldened with the letter it
    swelled 10 units past l's."""
    font = ufoLib2.Font.open(ROOT / 'sources/MyiaDidot-BoldItalic.ufo')
    def top(name):  # the stem's end, the bracket, the serif's underside
        return [(p.x, p.y, p.type) for p in font[name].contours[0].points if 1320 < p.y <= 1374]
    l, turned = top('l'), top('uni027A')
    dx = turned[0][0] - l[0][0]
    assert dx > 200
    assert turned == [(x + dx, y, t) for x, y, t in l]
