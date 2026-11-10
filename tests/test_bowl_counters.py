"""scripts/bowl_counters.py: a bowl's inside between two flats as two curves."""

import bowl_counters as B
from ufoLib2.objects import Glyph


def dee(shoulder=True):
    """a D: a stem, two flats, a bowl; its counter drawn with a tight
    shoulder, a straight run down to a corner, and a diagonal (five curves)
    or, sound, with two"""
    g = Glyph("D")
    pen = g.getPen()
    pen.moveTo((100, 0))
    pen.lineTo((500, 0))
    pen.curveTo((800, 0), (1000, 300), (1000, 700))
    pen.curveTo((1000, 1100), (800, 1400), (500, 1400))
    pen.lineTo((100, 1400))
    pen.closePath()
    pen.moveTo((300, 60))  # the counter, clockwise
    pen.lineTo((300, 1340))
    pen.lineTo((500, 1340))
    if shoulder:
        pen.curveTo((620, 1340), (700, 1290), (740, 1180))
        pen.curveTo((765, 1110), (785, 1010), (797, 900))
        pen.curveTo((806, 830), (812, 760), (812, 700))
        pen.curveTo((812, 560), (760, 420), (700, 300))
        pen.curveTo((640, 180), (580, 60), (500, 60))
    else:
        pen.curveTo((690, 1340), (812, 1050), (812, 700))
        pen.curveTo((812, 350), (690, 60), (500, 60))
    pen.closePath()
    g.width = 1100
    return g


def counter(g):
    return [(p.x, p.y, p.type, p.smooth) for p in g.contours[1].points]


def test_a_lumpy_counter_becomes_two_curves():
    g = dee()
    done = B.redo(g)
    assert len(done) == 1 and done[0][2] == 6 and 3 < done[0][3] < B.MOST
    pts = counter(g)
    assert sum(1 for p in pts if p[2] == "curve") == 2 and sum(1 for p in pts if p[2] == "line") == 3
    # the flats' ends and the stem's edge where they were
    assert {(300, 60), (300, 1340), (500, 1340), (500, 60)} <= {(p[0], p[1]) for p in pts}
    widest = max((p for p in pts if p[2]), key=lambda p: p[0])
    i = pts.index(widest)
    assert widest[3] and pts[i - 1][0] == widest[0] == pts[i + 1][0]  # upright there, smooth
    assert 805 <= widest[0] <= 813
    # level out of the flats
    assert pts[i - 2][1] == 1340 and pts[(i + 2) % len(pts)][1] == 60
    # the outside untouched
    assert [(p.x, p.y) for p in g.contours[0].points] == [(p.x, p.y) for p in dee().contours[0].points]


def test_a_sound_counter_is_left_and_the_redone_one_too():
    g = dee(shoulder=False)
    before = counter(g)
    assert B.redo(g) == [] and counter(g) == before
    g = dee()
    B.redo(g)
    once = counter(g)
    assert B.redo(g) == [] and counter(g) == once


def test_no_bowl_no_change():
    g = Glyph("o")
    pen = g.getPen()
    for r in (400, 300):
        k = r * 0.5523
        pen.moveTo((500 + r, 500))
        pen.curveTo((500 + r, 500 + k), (500 + k, 500 + r), (500, 500 + r))
        pen.curveTo((500 - k, 500 + r), (500 - r, 500 + k), (500 - r, 500))
        pen.curveTo((500 - r, 500 - k), (500 - k, 500 - r), (500, 500 - r))
        pen.curveTo((500 + k, 500 - r), (500 + r, 500 - k), (500 + r, 500))
        pen.closePath()
    assert B.redo(g) == []
