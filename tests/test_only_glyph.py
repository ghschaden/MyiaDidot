"""scripts/only_glyph.py: one recipe glyph made again equals the saved one
up to a translation in x and the slant's rounding. Needs the frame dump of
one full run (MYIA_DUMP_FRAME=build/only_glyph/frame-BoldItalic.ufo, see
only_glyph.py); skipped without it."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FRAME = ROOT / "build/only_glyph/frame-BoldItalic.ufo"


def shape(font, glyph):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen

    rec, box = DecomposingRecordingPen(font), BoundsPen(font)
    glyph.draw(rec)
    glyph.draw(box)
    return [(op, [(x - box.bounds[0], y) for x, y in args]) for op, args in rec.value if args]


@pytest.mark.skipif(not FRAME.exists(), reason="no frame dump (one full make_bold run)")
@pytest.mark.parametrize("ch", ["Ƈ", "Ɠ"])
def test_matches_saved(ch):
    import only_glyph

    frame = only_glyph._frame("BoldItalic")
    glyph, name, font = only_glyph.generate("BoldItalic", ch, frame=frame)
    saved, made = shape(font, font[name]), shape(font, glyph)
    assert len(saved) == len(made)
    for (op1, a), (op2, b) in zip(saved, made):
        assert op1 == op2
        assert all(abs(x1 - x2) <= 3 and abs(y1 - y2) <= 3 for (x1, y1), (x2, y2) in zip(a, b))
