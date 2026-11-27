"""scripts/quality/curvature.py's runs measure on drawn shapes: a style that
only adds to every radius (emboldening) reads clean, one whose arc turns
tight then flat where its source turns evenly is found there."""

import sys

import ufoLib2
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
import curvature  # noqa: E402

K = 0.5523  # a quarter circle's handle, over its radius


def ring(radius, cx=600, cy=600, uneven=False):
    """a glyph of one round contour; uneven: its top-left quarter drawn with
    short handles, flat at both ends and tight in the middle"""
    font = ufoLib2.Font()
    g = font.newGlyph("o")
    g.width = 1200
    r, k = radius, K * radius
    quarters = [((cx + r, cy), (cx + r, cy + k), (cx + k, cy + r), (cx, cy + r)),
                ((cx, cy + r), (cx - k, cy + r), (cx - r, cy + k), (cx - r, cy)),
                ((cx - r, cy), (cx - r, cy - k), (cx - k, cy - r), (cx, cy - r)),
                ((cx, cy - r), (cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))]
    if uneven:
        p0, _, _, p3 = quarters[1]
        quarters[1] = (p0, (cx - 0.2 * r, cy + r), (cx - r, cy + 0.2 * r), p3)
    pen = g.getPen()
    pen.moveTo(tuple(round(v) for v in quarters[0][0]))
    for _, a, b, c in quarters:
        pen.curveTo(*(tuple(round(v) for v in p) for p in (a, b, c)))
    pen.closePath()
    return g


def test_one_glyph_against_itself_reads_clean():
    g = ring(400)
    assert curvature.runs(g)
    assert curvature.run_finds(g, ring(400)) == []


def test_offset_alone_reads_clean():
    """every radius 80 units larger: what emboldening does"""
    assert curvature.run_finds(ring(480), ring(400)) == []


def test_uneven_arc_found_in_its_quarter():
    found = curvature.run_finds(ring(480, uneven=True), ring(400))
    assert found
    x, y = max(found, key=lambda f: abs(f["q"]))["at"]
    assert x < 600 and y > 600, (x, y)
