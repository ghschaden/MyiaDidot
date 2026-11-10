"""A straight stem is one thickness from top to bottom: it never steps in
where it meets its serif (scripts/stem_joins.py; the designer, 2026-11-10).

The generated styles are mended by their last finishing pass; a glyph drawn
by hand is mended where it is drawn. data/stem-retreats.txt (per style,
stem-retreats-Bold.txt ...) lists what is known and only shrinks.
"""

import stem_joins
from conftest import style_data
from test_composites import read_list
from ufoLib2.objects import Glyph


def stem(foot):
    """an upright stem 150 wide on a foot serif, the join at its left drawn
    by foot(pen) from the serif's flat (20,60 ... ) up to the edge at 100,100"""
    g = Glyph("l")
    pen = g.getPen()
    pen.moveTo((20, 0))
    pen.lineTo((330, 0))
    pen.lineTo((330, 60))
    pen.lineTo((250, 60))
    pen.lineTo((250, 700))
    pen.lineTo((100, 700))
    pen.lineTo((100, 100))
    foot(pen)
    pen.lineTo((20, 60))
    pen.closePath()
    g.width = 350
    return g


def bracket(pen):  # one curve, outside the edge: sound
    pen.curveTo((100, 78), (82, 60), (60, 60))


def collapsed(pen):  # the edge moved out, the bracket's nodes left behind
    pen.curveTo((96, 105), (118, 92), (118, 80))
    pen.curveTo((118, 70), (116, 62), (110, 60))


def test_sound_bracket_and_square_join_are_no_retreat():
    assert stem_joins.retreats(stem(bracket)) == []
    assert stem_joins.retreats(stem(lambda pen: pen.lineTo((100, 60)))) == []


def test_a_stem_stepping_in_is_found_and_mended():
    g = stem(collapsed)
    found = stem_joins.retreats(g)
    assert [(x, y) for x, y, _ in found] == [(100, 100)] and 15 < found[0][2] <= 18
    assert stem_joins.mend(g) == found and stem_joins.retreats(g) == []
    pts = [(p.x, p.y, p.type) for p in g.contours[0].points]
    # the edge still a line from the top to the bracket, at x 100; the
    # bracket one curve from it to the flat, nowhere right of the edge
    edge = [p for p in pts if p[2] and p[0] == 100]
    assert (100, 700, "line") in edge and len(edge) == 2 and min(p[1] for p in edge) <= 100
    low = min(p[1] for p in edge)
    assert all(p[0] <= 100 for p in pts if p[1] < low and p[0] < 200)
    assert sum(1 for p in pts if p[2] == "curve") == 1
    assert g.width == 350


def test_no_stem_steps_in_at_its_serif(ufo, ufo_path):
    listed = read_list(style_data("stem-retreats.txt", ufo_path).name)
    found = {f"{g.name} {x},{y}": units for g in ufo if g.contours for x, y, units in stem_joins.retreats(g)}
    new = {k: v for k, v in found.items() if k not in listed}
    assert not new, ("stems stepping into the ink before their serif (python scripts/quality/stem_retreats.py UFO; "
                     f"a drawn glyph is mended by hand): {new}")
    stale = sorted(set(listed) - set(found))
    assert not stale, f"mended, remove from the list: {stale}"
