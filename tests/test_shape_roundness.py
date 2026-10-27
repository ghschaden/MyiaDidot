"""Independent area and scope checks for the roundness experiment."""

import sys
from pathlib import Path

import pytest
import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shape_roundness as study


def rectangle(x0, x1):
    glyph = ufoLib2.objects.Glyph()
    pen = glyph.getPen()
    pen.moveTo((x0, 0))
    pen.lineTo((x1, 0))
    pen.lineTo((x1, 100))
    pen.lineTo((x0, 100))
    pen.closePath()
    return glyph


def test_ink_measurement_is_bounded_and_matches_known_overlap():
    a, b, c = rectangle(0, 100), rectangle(50, 150), rectangle(200, 300)
    assert study.difference(a, a) == 0
    assert study.difference(a, b) == pytest.approx(100*100/150)
    assert study.difference(a, c) == pytest.approx(100)


def test_oval_does_not_accept_connected_bowls():
    with pytest.raises(ValueError, match="explicit closed-round"):
        study.oval_trial(None, None, "h")


@pytest.mark.parametrize("style,source", [("Bold", "Regular"), ("BoldItalic", "Italic")])
def test_oval_experiments_preserve_input_and_report_bounded_changes(style, source):
    before = ufoLib2.Font.open(study.consistency.source_paths()[source])
    current = ufoLib2.Font.open(study.consistency.source_paths()[style])
    original = current.json_dumps()
    for name in ("o", "O", "zero"):
        candidate, report = study.oval_trial(before, current, name)
        assert len(candidate.contours) == 2
        assert candidate.width == current[name].width
        assert 0 < report["ink_difference_percent"] < 10
        assert not report["new_lint_findings"]
    assert current.json_dumps() == original
