"""scripts/italic_kerning.py: an italic's kerning from the white its shapes leave."""

import italic_kerning as K
import pytest
import ufoLib2
from kern_coverage import Profiles


def box(font, name, left, right, width, top=900, code=None, extra=()):
    g = font.newGlyph(name)
    if code:
        g.unicodes = [ord(code)]
    pen = g.getPen()
    for x0, y0, x1, y1 in [(left, 0, right, top), *extra]:
        pen.moveTo((x0, y0))
        pen.lineTo((x1, y0))
        pen.lineTo((x1, y1))
        pen.lineTo((x0, y1))
        pen.closePath()
    g.width = width
    return g


def family(side=100, o_right=100, o_extra=(), n_extra=()):
    """n, H and two letters o v as boxes; the "italic" is given other sides"""
    f = ufoLib2.Font()
    f.info.xHeight = 900
    box(f, "n", side, 600 - side, 600, code="n", extra=n_extra)
    box(f, "H", side, 800 - side, 800, top=1400, code="H")
    box(f, "o", 100, 600 - o_right, 600, code="o", extra=o_extra)
    box(f, "v", 100, 500, 600, code="v")
    return f


def value(upright, italic):
    return K.compute(upright, italic)[("o", "v")]


def test_same_shapes_same_kerning():
    u = family()
    u.kerning[("o", "v")] = -50
    row = value(u, family())
    assert row["value"] == -50 and row["note"] == ""


def test_a_wider_side_is_kerned_away(monkeypatch):
    u = family()
    u.kerning[("o", "v")] = -50
    # the italic o stands 30 further from what follows: 30 more kerning,
    # of which TIGHTEN is taken (none as set: no tighter than the upright)
    assert value(u, family(o_right=130))["value"] == -50
    monkeypatch.setattr(K, "TIGHTEN", 1.0)
    assert value(u, family(o_right=130))["value"] == -80
    # and looser where it stands nearer
    assert value(u, family(o_right=80))["value"] == -30


def test_share_of_the_style_s_own_rhythm(monkeypatch):
    monkeypatch.setattr(K, "TIGHTEN", 1.0)
    u = family()
    u.kerning[("o", "v")] = -50
    # the italic sets n n at 3/4 of the upright's white: so the pair
    # (upright 200 - 50 = 150 of 200; italic 3/4 * 150 = 112 of its 200)
    assert value(u, family(side=75))["value"] in (-87, -88)


def test_a_hairline_counts_by_its_rows():
    # an exit stroke 60 units long over 50 of the 900 units of height:
    # the white less by 60 * 50/900, not by 60
    f = family(o_extra=[(500, 0, 560, 50)])
    assert K.white(f, Profiles(f), "o", "v") == pytest.approx(200 - 60 * 50 / 900, abs=0.5)


def test_deep_white_is_clipped():
    # a notch 500 deep over a third of the height counts DEPTH x-heights
    f = family()
    box(f, "c", 100, 500, 600, top=300, code="c", extra=[(100, 300, 0, 600), (100, 600, 500, 900)])
    f["c"].contours[1].move((0, 0))
    assert K.white(f, Profiles(f), "c", "v") == pytest.approx(200 + K.DEPTH * 900 / 3, abs=1)


def test_no_nearer_than_the_upright(monkeypatch):
    monkeypatch.setattr(K, "TIGHTEN", 1.0)
    u = family()
    u.kerning[("o", "v")] = -150  # the upright's inks 50 apart
    # the italic's o 100 further off but with a spur reaching 150 back:
    # the mean asks for about -242, the spur's 50 units of white allow -100
    i = family(o_right=200, o_extra=[(400, 400, 550, 450)])
    row = value(u, i)
    assert row["note"] == "nearest"
    assert Profiles(i).gap("o", "v", row["value"]) >= 50


def test_a_kerning_keeps_its_sign_or_goes():
    u = family()
    u.kerning[("o", "v")] = -50
    row = value(u, family(o_right=20))  # 80 nearer already
    assert row["value"] == 0 and row["note"] == "sign"


def test_white_needs_facing_rows():
    f = family()
    box(f, "quote", 100, 300, 400, code="'").contours[0].move((0, 1000))
    assert K.white(f, Profiles(f), "quote", "n") is None
    u = family()
    box(u, "quote", 100, 300, 400, code="'").contours[0].move((0, 1000))
    u.kerning[("quote", "n")] = -40
    row = K.compute(u, f)[("quote", "n")]
    assert row["value"] is None and row["note"] == "no rows"


def test_apply_sets_drops_and_skips():
    # the generators' step: a computed pair set, one come to 0 kept at 0,
    # one not computed (no rows) and one skipped kept as the italic had them
    u = family()
    box(u, "quote", 100, 300, 400, code="'").contours[0].move((0, 1000))
    u.kerning.update({("o", "v"): -50, ("n", "o"): -50, ("quote", "n"): -40, ("v", "o"): -50})
    i = family(o_right=20)  # o v 80 nearer already: sign, 0
    box(i, "quote", 100, 300, 400, code="'").contours[0].move((0, 1000))
    i.kerning.update({("o", "v"): -50, ("quote", "n"): -40, ("v", "o"): -7})
    assert K.apply(u, i, skip={("v", "o")}) == (1, 1)
    assert i.kerning[("o", "v")] == 0
    assert i.kerning[("n", "o")] == -50 and i.kerning[("quote", "n")] == -40 and i.kerning[("v", "o")] == -7
