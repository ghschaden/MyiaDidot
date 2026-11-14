"""scripts/redraw.py: an outline redrawn onto extremes, corners and line ends."""

import math

import numpy as np
import pytest
import redraw as R
import ufoLib2
from conftest import SOURCES
from quality.checks import construction
from ufoLib2.objects import Glyph


def oval(name="o", arcs=8, slant=0.27, rx=400, ry=450, turn=0.3):
    """a slanted oval drawn with `arcs` curves, its nodes off the extremes"""
    g = Glyph(name)
    pen = g.getPen()
    k = 4 / 3 * math.tan(math.pi / (2 * arcs))
    P = lambda x, y: (round(500 + x + slant * y), round(430 + y))  # noqa: E731
    at = lambda a: (rx * math.cos(a), ry * math.sin(a))  # noqa: E731
    d = lambda a: (-rx * math.sin(a), ry * math.cos(a))  # noqa: E731
    pen.moveTo(P(*at(turn)))
    for i in range(arcs):
        a, b = turn + 2 * math.pi * i / arcs, turn + 2 * math.pi * (i + 1) / arcs
        (x0, y0), (x1, y1), (dx0, dy0), (dx1, dy1) = at(a), at(b), d(a), d(b)
        pen.curveTo(P(x0 + k * dx0, y0 + k * dy0), P(x1 - k * dx1, y1 - k * dy1), P(x1, y1))
    pen.closePath()
    g.width = 1000
    return g


def stem_and_arch():
    """a stem whose side runs into an arch with a kink of about 4 degrees,
    a line of 4 units left in the crotch, square corners at the foot"""
    g = Glyph("h")
    pen = g.getPen()
    pen.moveTo((100, 0))
    pen.lineTo((100, 600))
    pen.curveTo((114, 800), (240, 900), (400, 900))  # leaves the stem 4 degrees off upright
    pen.curveTo((560, 900), (700, 780), (700, 600))
    pen.lineTo((700, 0))
    pen.lineTo((560, 0))
    pen.lineTo((560, 600))
    pen.curveTo((560, 700), (500, 780), (400, 780))
    pen.curveTo((320, 780), (262, 700), (242, 603))
    pen.lineTo((240, 600))                            # the crotch's leftover
    pen.curveTo((240, 400), (240, 200), (240, 0))     # a straight side drawn as a curve
    pen.closePath()
    g.width = 800
    return g


def kinds(glyph):
    out = []
    for c in glyph.contours:
        pts = list(c.points)
        for i, p in enumerate(pts):
            if p.type:
                out.append(("smooth" if p.smooth else "corner", p.x, p.y, pts[i - 1], pts[(i + 1) % len(pts)]))
    return out


def test_oval_onto_its_four_extremes():
    g = oval()
    new, rep = R.redraw(g)
    assert rep["nodes_before"] == 8 and rep["nodes_after"] == 4
    assert rep["count"] == {"corner": 0, "line": 0, "extreme": 4, "extra": 0}
    assert rep["dev"] < 1.5 and rep["bounds_moved"] <= 1 and abs(rep["area"]) < 0.3
    assert R.gate(rep) == ([], [])
    # every node smooth, on whole units, its handles level or upright
    for kind, x, y, before, after in kinds(new):
        assert kind == "smooth" and x == int(x) and y == int(y)
        assert (before.x == x == after.x) or (before.y == y == after.y)
    assert not construction(new)
    # one curvature at the nodes, which the eight arcs' rounding had not
    assert rep["jump"] < 0.1


def test_redrawing_the_redrawn_changes_nothing_much():
    once, _ = R.redraw(oval())
    twice, rep = R.redraw(once)
    assert rep["nodes_after"] == R.node_count(once) and rep["dev"] < 1


def test_kink_made_smooth_short_line_closed_corners_kept():
    g = stem_and_arch()
    assert any(f[0] == "kink" for f in construction(g))
    new, rep = R.redraw(g)
    assert not rep["findings"] and R.gate(rep)[0] == []
    assert any("made smooth" in n for n in rep["notes"]) and any("closed" in n for n in rep["notes"])
    corners = {(x, y) for kind, x, y, *_ in kinds(new) if kind == "corner"}
    assert {(100, 0), (700, 0), (560, 0), (240, 0)} <= corners
    # the stem's side still a line, the arch leaving it in its direction
    stem = next(k for k in kinds(new) if (k[1], k[2]) == (100, 600))
    assert stem[0] == "smooth" and stem[4].x == 100 and stem[4].y > 600
    assert rep["nodes_after"] <= rep["nodes_before"]


def test_an_extra_node_only_where_one_curve_does_not_hold():
    g = oval(rx=250, ry=450, slant=0.6)  # a narrow oval far slanted: its long flanks
    loose, rep_loose = R.redraw(g, tol=8)
    tight, rep_tight = R.redraw(g, tol=0.3)
    assert rep_loose["count"]["extra"] == 0
    assert rep_tight["count"]["extra"] > 0 and rep_tight["dev"] < rep_loose["dev"]
    assert R.gate(rep_tight)[1]  # extras off extremes and inflections are remarked


def test_spec_adds_and_drops_nodes():
    g = oval()
    plain, _ = R.redraw(g)
    top = max((p for c in plain.contours for p in c.points if p.type), key=lambda p: p.y)
    more, rep = R.redraw(g, spec={"extra": [[500 - 283 + 86, 430 + 318]]})
    assert rep["count"]["extra"] == 1 and rep["extras"] == ["spec"]
    fewer, rep = R.redraw(g, spec={"drop": [[top.x, top.y]], "tol": 50})
    assert rep["count"]["extreme"] == 3 and rep["tol"] == 50
    with pytest.raises(ValueError):
        R.redraw(g, spec={"drop": [[5000, 5000]]})


def test_spec_extra_on_a_node_of_the_structure_is_refused():
    """an extra where the structure has a node already made a span of no
    length, and fit_cubic's early return crashed the fit (Italic beta at
    192,-531, the place its gate named; 2026-11-14): refused by name"""
    g = oval()
    plain, _ = R.redraw(g)
    top = max((p for c in plain.contours for p in c.points if p.type), key=lambda p: p.y)
    with pytest.raises(ValueError, match="has a node there already"):
        R.redraw(g, spec={"extra": [[top.x, top.y]]})
    ctrl = R.fit_cubic(np.array([[10.0, 10.0], [10.0, 10.0]]), np.array([10.0, 10.0]), np.array([1.0, 0.0]),
                       np.array([10.0, 10.0]), np.array([1.0, 0.0]))
    assert ctrl.shape == (4, 2)


def test_refuses_what_it_cannot_redraw():
    g = oval()
    g.components.append(ufoLib2.objects.Component("o"))
    with pytest.raises(ValueError):
        R.redraw(g)


def test_gate_names_the_failures():
    rep = {"dev": 5.2, "dev_at": [1, 2], "findings": [["kink", "3,4", "5.0 degrees"]], "nodes_after": 9,
           "nodes_before": 8, "bounds_moved": 0, "area": 0.1, "extras": [], "jump": 0.1, "jump_at": [0, 0],
           "jump_before": 0.2}
    rep["tol"] = 2.0
    fail, look = R.gate(rep, counterpart=4)
    assert len(fail) == 2 and "5.2 units" in fail[0] and "kink" in fail[1]
    assert "more nodes" in look[0] and look[1] == "9 nodes against the Regular's 4"


def test_install_marks_the_italic_glyph_drawn(tmp_path):
    from drawn import is_drawn

    font = ufoLib2.Font()
    font.info.italicAngle, font.info.openTypeOS2WeightClass = -15.2, 400
    g = oval()
    g.lib[R.ITALIC_SOURCE_KEY] = "Old Standard"
    font.layers.defaultLayer.insertGlyph(g, "o")
    new, rep = R.redraw(font["o"])
    R.install(font, "o", new, "2026-11-10", "proofs/sheet.pdf", rep)
    assert R.node_count(font["o"]) == 4 and font["o"].width == 1000
    assert font["o"].lib[R.ITALIC_SOURCE_KEY] == "drawn" and is_drawn(font["o"])
    assert font["o"].lib["org.myiadidot.drawn"]["why"] == "redrawn onto clean nodes, proofs/sheet.pdf"
    assert font["o"].lib[R.KEY]["source"] == "Old Standard" and font["o"].lib[R.KEY]["review"] == "proofs/sheet.pdf"
    font.save(tmp_path / "x.ufo")
    assert R.node_count(ufoLib2.Font.open(tmp_path / "x.ufo")["o"]) == 4


def test_the_italic_o_passes_the_gate():
    font = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    new, rep = R.redraw(font["o"])
    assert R.gate(rep)[0] == [] and rep["nodes_after"] <= rep["nodes_before"]
    assert new.width == font["o"].width and [a.name for a in new.anchors] == [a.name for a in font["o"].anchors]


def test_a_curve_bent_back_at_one_end_is_found_and_mended():
    import numpy as np

    # the Italic n's 809,649 as first fitted: its second handle a unit and
    # a half past the point where the stem's line and the upright meet
    bent = np.array([[809, 649], [829, 694], [843, 724], [843, 764]], float)
    end, degrees = R.wrong_turn(bent)
    assert end == 0 and 0.5 < degrees < 2
    mended = R.one_bend(bent, R.unit(bent[1] - bent[0]), R.unit(bent[3] - bent[2]))
    assert R.wrong_turn(mended) is None
    assert (mended[[0, 1, 3]] == bent[[0, 1, 3]]).all() and 724 < mended[2][1] <= 727 and mended[2][0] == 843
    # an S meant as one is left alone, a plain bend too
    assert R.wrong_turn(np.array([[0, 0], [100, 0], [100, 200], [200, 200]], float)) is None
    assert R.wrong_turn(np.array([[0, 0], [0, 55], [45, 100], [100, 100]], float)) is None


def test_gate_fails_a_curve_bent_back():
    g = oval()
    new, rep = R.redraw(g)
    assert rep["bent_back"] == []
    rep["bent_back"] = [[809.0, 649.0, 1.05]]
    assert "809,649 bends 1.05 degrees the other way" in R.gate(rep)[0][0]


def test_no_redrawn_letter_bends_back():
    """the letters redrawn so far (their record in the lib), all styles'"""
    for style in ("Italic",):
        font = ufoLib2.Font.open(SOURCES / f"MyiaDidot-{style}.ufo")
        found = {g.name: R.bent_back(g) for g in font if R.KEY in g.lib and g.contours}
        assert not {n: f for n, f in found.items() if f}


def test_a_second_install_keeps_the_first_source_mark():
    font = ufoLib2.Font()
    g = oval()
    g.lib[R.ITALIC_SOURCE_KEY] = "Old Standard"
    font.layers.defaultLayer.insertGlyph(g, "o")
    for date in ("2026-11-10", "2026-11-12"):
        new, rep = R.redraw(font["o"])
        R.install(font, "o", new, date, "proofs/sheet.pdf", rep)
    assert font["o"].lib[R.KEY]["source"] == "Old Standard" and font["o"].lib[R.KEY]["date"] == "2026-11-12"


def test_sweep_tells_the_redrawn_its_composites_and_the_rest():
    import redraw_sweep as S

    def font(shift=0, wide=0, redrawn=False):
        f = ufoLib2.Font()
        o = oval()
        if redrawn:
            o, rep = R.redraw(o)
            o.lib[R.KEY] = {"date": "2026-11-10"}
        f.layers.defaultLayer.insertGlyph(o, "o")
        acc = f.newGlyph("oacute")
        acc.width = 1000
        acc.components.append(ufoLib2.objects.Component("o"))
        other = oval("c")
        for p in (p for c in other.contours for p in c.points):
            p.x += shift
        other.width += wide
        f.layers.defaultLayer.insertGlyph(other, "c")
        same = oval("e")
        f.layers.defaultLayer.insertGlyph(same, "e")
        return f

    rows, kerning = S.sweep(font(), font(shift=9, redrawn=True), limit=4, advance=5)
    by = {r["glyph"]: r for r in rows}
    assert set(by) == {"o", "oacute", "c"} and not kerning
    assert by["o"]["kind"] == "redrawn" and 0 < by["o"]["distance"] < 2 and not by["o"]["flag"]
    assert by["oacute"]["kind"] == "composite" and by["oacute"]["distance"] == by["o"]["distance"]
    assert by["c"]["kind"] == "other" and 8.5 < by["c"]["distance"] <= 9 and by["c"]["flag"]
    rows, _ = S.sweep(font(), font(wide=6), limit=4, advance=5)
    assert [(r["glyph"], r["advance"], r["flag"]) for r in rows] == [("c", [1000, 1006], True)]
    rows, _ = S.sweep(font(), font(wide=3), limit=4, advance=5)
    assert [r["flag"] for r in rows] == [False]


def test_make_italic_reads_a_redrawn_letters_former_source():
    import make_italic as M
    from fontTools.pens.recordingPen import RecordingPen

    g = oval()
    g.lib[M.SOURCE_KEY] = "drawn"
    assert M.origin(g) == "drawn"  # drawn by hand: no weight of Old Standard's to take off
    g.lib[M.REDRAWN_KEY] = {"source": "Old Standard"}
    assert M.origin(g) == "Old Standard"
    g.lib[M.SOURCE_KEY] = "derived"
    assert M.origin(g) == "derived"
    rec = RecordingPen()
    oval(arcs=4).draw(rec)
    assert sum(op == "curveTo" for op, _ in M.halved(rec).value) == 8


def test_spec_keeps_a_crotch_line():
    g = stem_and_arch()
    _, closed = R.redraw(g)
    kept, rep = R.redraw(g, spec={"keep": [[242, 603]]})
    assert any("closed" in n for n in closed["notes"]) and not any("closed" in n for n in rep["notes"])
    assert {(242, 603), (240, 600)} <= {(x, y) for _, x, y, *_ in kinds(kept)}


def test_spec_points_go_to_their_own_contour():
    """a spec's point names a place on one contour of the glyph; the others
    do not look for it (q's extra was refused by its counter, 57 units off)"""
    g = oval()
    inner = oval(rx=200, ry=250)
    g.contours.append(inner.contours[0])
    _, rep = R.redraw(g, spec={"extra": [[500 - 283 + 86, 430 + 318]]})
    assert rep["extras"].count("spec") == 1


def test_spec_takes_a_straight_curve_as_a_line():
    """a stem's edge drawn as a curve within the tolerance of its chord
    becomes a line by the spec (the Italic's q); a real curve is refused"""
    g = stem_and_arch()
    lined, rep = R.redraw(g, spec={"line": [[240, 600]]})
    assert any("taken as a line" in n for n in rep["notes"])
    foot = next(p for c in lined.contours for p in c.points if (p.x, p.y) == (240, 0))
    assert foot.type == "line"
    with pytest.raises(ValueError):
        R.redraw(g, spec={"line": [[560, 600]]})
