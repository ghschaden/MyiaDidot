"""No derived letter emboldened whole without saying so.

Emboldened (or, in the Italic, weighted) as one shape, a derived letter
thickens at its junctions unlike its base: a slash eats the stem beside it,
a small ring closes up. make_bold.py and make_italic.py make such letters
of their style's own base instead (make_bold.follow_bases, attached_small);
those they leave whole, with the reason, go into the style's lib
(make_bold.WHOLE_KEY). Each weighted style has its list of them,
data/emboldened-whole-Bold.txt ...: a new one fails, and so does a listed
one that is no longer whole (delete its line), so the lists only shrink.
After an intended change: scripts/update_test_data.py --emboldened.
"""

import pytest
from conftest import style_data
from make_bold import WHOLE_KEY
from test_composites import read_list


def test_derived_letters_not_emboldened_whole(ufo, ufo_path):
    if WHOLE_KEY not in ufo.lib:
        pytest.skip("not a weighted style")
    listed = read_list(style_data("emboldened-whole.txt", ufo_path).name)
    found = ufo.lib[WHOLE_KEY]
    new = {k: v for k, v in found.items() if k not in listed}
    stale = sorted(set(listed) - set(found))
    assert not new, ("derived letters emboldened whole, their junctions thickened (make them of "
                     "their base in the generator, or if intended: update_test_data.py --emboldened): "
                     f"{new}")
    assert not stale, f"no longer emboldened whole, remove from the list: {stale}"


def test_serif_top_finds_each_styles_foot_serif():
    """rederive raises a hook's cut from the source's foot-serif top to the
    Bold's: measured above the baseline row (a sliver there in the Bold's d),
    None where a stem has no foot serif."""
    import ufoLib2
    from conftest import ROOT
    from make_bold import serif_top

    regular = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Regular.ufo")
    bold = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Bold.ufo")
    assert [serif_top(regular, g, p) for g, p in (("l", "first"), ("F", "first"), ("d", "last"))] == [48, 52, 48]
    assert [serif_top(bold, g, p) for g, p in (("l", "first"), ("F", "first"), ("d", "last"))] == [55, 59, 55]
    assert serif_top(bold, "t", "first") is None


def test_fill_pinholes_only_where_the_emboldened_letter_is_solid():
    """rederive fills a rebuilt letter's pinhole where the letter emboldened
    whole has ink (Bold Ɦ's ball over its serif), not one it shares (a
    curl closed on its stroke, ң), which is judged as a fault."""
    import ufoLib2
    from make_bold import fill_pinholes

    def square(pen, x0, y0, x1, y1, ccw=True):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pen.moveTo(pts[0])
        for pt in pts[1:] if ccw else pts[:0:-1]:
            pen.lineTo(pt)
        pen.closePath()

    font = ufoLib2.Font()
    solid, holed = font.newGlyph("solid"), font.newGlyph("holed")
    square(solid.getPen(), 0, 0, 500, 500)
    square(holed.getPen(), 0, 0, 500, 500)
    square(holed.getPen(), 200, 200, 240, 240, ccw=False)
    for shares, contours in ((False, 1), (True, 2)):
        new = font.newGlyph("new")
        square(new.getPen(), 0, 0, 500, 500)
        square(new.getPen(), 200, 200, 240, 240, ccw=False)
        fill_pinholes(new, holed if shares else solid, font)
        assert len(new.contours) == contours
        del font["new"]
