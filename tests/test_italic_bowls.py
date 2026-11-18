"""scripts/italic_bowls.py: the Italic's bowls widened at their counters' middle."""

import italic_bowls as B
import italic_harmonise as H
import ufoLib2
from conftest import SOURCES

ITALIC = SOURCES / "MyiaDidot-Italic.ufo"


def font():
    return ufoLib2.Font.open(ITALIC)


def test_counters_found_between_the_stems():
    f = font()
    assert len(B.counters(f["n"], f)) == 1
    assert len(B.counters(f["m"], f)) == 2
    assert len(B.counters(f["o"], f)) == 1
    assert len(B.counters(f["C"], f)) == 1  # open on the right


def test_left_stays_right_moves_whole():
    f = font()
    g = f["n"]
    fn, grow, gaps, bands, _shift = B.mapping(g, f)
    sl = H.slant_of(f)
    (lo, hi), = bands
    d = B.widen_of("n")
    assert grow == d
    for c in g.contours:
        for p in c.points:
            x = p.x - sl * p.y
            nx, ny = fn(p.x, p.y)
            assert ny == p.y
            if x <= lo:
                assert nx == p.x
            elif x >= hi:
                assert abs(nx - p.x - d) < 1e-9
            else:
                assert p.x <= nx <= p.x + d


def test_construction_grows_by_the_widening():
    f = font()
    g = f["m"]
    new, _fn, gaps = B.bowls(f, g)
    assert new.width == g.width + 2 * B.widen_of("m")
    assert all(float(a.x).is_integer() and float(a.y).is_integer() for a in new.anchors)


def test_spec_points_follow_the_map():
    shift = lambda x, y: (x + 10, y)  # noqa: E731
    assert B.moved_spec({"line": [[419, -364]]}, shift) == {"line": [[429, -364]]}
    assert B.moved_spec(None, shift) is None
