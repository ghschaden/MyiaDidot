"""Phase 7's measures (scripts/quality/bold_measures.py) find what they name on
the Regular: o's counter closed, c's open at its mouth, e's eye closed above
its open lower counter, n's two stems with one counter between them (the
hollows beside its serifs are no counters), the arch's join thinner than
the stem, c's ball wider than that join; and the distance transform is exact."""

import sys

import numpy as np
import pytest
from conftest import ROOT, SOURCES

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import bold_measures as bm


@pytest.fixture(scope="module")
def regular():
    return bm.Source(SOURCES / "MyiaDidot-Regular.ufo")


def test_counters(regular):
    o, c, e, n = (bm.measure(regular, ch)["counters"] for ch in "ocen")
    assert [k["aperture"] for k in o] == [0.0]
    assert len(c) == 1 and 0.2 * c[0]["width"] < c[0]["aperture"] < c[0]["width"]
    assert len(e) == 2 and e[0]["aperture"] == 0.0 and e[1]["aperture"] > 0  # eye above
    assert len(n) == 1


def test_stems_joins_ball(regular):
    n = bm.measure(regular, "n")
    assert len(bm.stems(regular, "n")) == 2 and len(bm.stems(regular, "m")) == 3
    assert 0 < n["joins"]["0R top"] < n["stem"]
    assert bm.measure(regular, "c")["ball"] > n["joins"]["0R top"]


def test_edt_is_exact():
    rng = np.random.default_rng(7)
    feature = rng.random((23, 31)) < 0.05
    got = bm.edt(feature)
    ys, xs = np.nonzero(feature)
    rows, cols = np.indices(feature.shape)
    want = np.sqrt(((rows[..., None] - ys) ** 2 + (cols[..., None] - xs) ** 2).min(axis=2))
    assert np.allclose(got, want)


def test_targets_position_and_scale():
    """bold_targets: a value's place against the references' range, and a
    letter's measures over the style's own stem and zone."""
    import bold_targets as bt

    assert bt.position(5, [4, 6]) == 0
    assert bt.position(3, [4, 6]) == pytest.approx(-0.25)
    assert bt.position(9, [4, 6]) == pytest.approx(0.5)
    style = {"xHeight": 400, "capHeight": 700, "chars": {
        "n": {"advance": 500, "ink": 450, "stem": 100, "white": 40000, "joins": {"0R top": 30},
              "counters": [{"area": 40000, "width": 150, "aperture": 60}]},
        "o": {"advance": 480, "ink": 420, "white": 50000, "counters": [{"area": 50000, "width": 200, "aperture": 0}]},
    }}
    n, o = bt.ratios(style, "n"), bt.ratios(style, "o")
    assert n["counter width/stem"] == 1.5 and n["aperture/counter width"] == 0.4
    assert n["join/stem top"] == 0.3 and n["advance/zone"] == 1.25
    assert o["round stroke/stem"] == pytest.approx(1.1) and "aperture/stem" not in o
