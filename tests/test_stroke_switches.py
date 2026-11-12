"""Nothing that changes an outline is read from the environment (T4,
docs/claude/stroking.md): the stroker's two stages kept for finding faults
are keyword-only arguments, and the reproduction check refuses a MYIA_*
variable the project does not read.
"""

import inspect
import math
import subprocess
import sys

import pytest
import ufoLib2
from conftest import ROOT, SOURCES
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen

sys.path.insert(0, str(ROOT / "scripts"))
import stroke_cache
from stroke_bold import embolden_by_strokes


def test_diagnostics_keyword_only():
    """make_bold's jobs pass their arguments positionally (stroke_bold.
    emboldened): they cannot turn a stage off, nor can the cache key it"""
    params = inspect.signature(embolden_by_strokes).parameters
    for name in ("fair", "one_way"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert params[name].default is True


@pytest.fixture(scope="module")
def stroked_n():
    import make_bold as mb

    italic = ufoLib2.Font.open(SOURCES / "MyiaDidot-Italic.ufo")
    slant = math.tan(math.radians(-italic.info.italicAngle))

    def run(**kw):
        wide = RecordingPen()
        mb.contours_only(italic["n"]).replay(
            TransformPen(TransformPen(wide, (mb.KX, 0, 0, 1, 0, 0)), (1, 0, -slant, 1, 0, 0)))
        glyph = embolden_by_strokes(wide, mb.ITALIC_AX, mb.AY, mb.ITALIC_THIN, mb.ITALIC_THICK, mb.ITALIC_HAIR,
                                    slant, **kw)
        out = RecordingPen()
        glyph.draw(out)
        return out.value
    return run


@pytest.mark.parametrize("off", ["fair", "one_way"])
def test_each_diagnostic_changes_n(stroked_n, off):
    """each stage, turned off, changes n (as fitted: fewer nodes; its entry
    stroke not kept turning one way); the defaults are the shipped stroker"""
    assert stroked_n(**{off: False}) != stroked_n()


def test_unknown_variables():
    assert stroke_cache.unknown({"MYIA_JOBS": "2", "MYIA_STROKE_OUT_LOG": "f", "PATH": "/bin"}) == []
    assert stroke_cache.unknown({"MYIA_G2": "0", "MYIA_JOBS": "2"}) == ["MYIA_G2"]
    assert stroke_cache.STEERING <= stroke_cache.KNOWN


def test_reproduce_refuses_a_stale_switch(monkeypatch):
    """a switch left set in a shell is named, before anything runs"""
    monkeypatch.setenv("MYIA_ONE_WAY", "0")
    got = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/check_reproducible.py")],
                         capture_output=True, text=True, timeout=60)
    assert got.returncode == 2
    assert "MYIA_ONE_WAY" in got.stderr
