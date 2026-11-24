"""Design quality beyond the outlines' faults: construction (smooth nodes,
kinks, extremes, whole units), alignment zones, stem weights, the italic's
slant, accent gaps, the Bold's widths against the Regular's, and derived
letters against the letters they are made from (scripts/quality/derived.py).

scripts/quality/checks.py finds them; each style has its list of known
findings, data/quality.txt (the Regular's), quality-Italic.txt,
quality-Bold.txt: one "glyph kind count" per line with a reason. A new
finding fails, and so does a listed one that is gone (delete its line), so
the lists only shrink. After an intended change:
scripts/update_test_data.py --quality.
"""

import sys
from pathlib import Path

from conftest import style_data
from test_composites import read_list

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "quality"))
from checks import check


def quality_keys(ufo, ufo_path):
    """{"glyph kind count": the findings, as text} for a font."""
    keys = {}
    for name, items in check(ufo, ufo_path).items():
        kinds = {}
        for kind, where, detail in items:
            kinds.setdefault(kind, []).append(f"{where} {detail}".strip())
        for kind, found in kinds.items():
            keys[f"{name} {kind} {len(found)}"] = "; ".join(found)
    return keys


def test_quality(ufo, ufo_path):
    listed = read_list(style_data("quality.txt", ufo_path).name)
    found = quality_keys(ufo, ufo_path)
    new = {k: v for k, v in found.items() if k not in listed}
    stale = sorted(set(listed) - set(found))
    assert not new, ("quality findings (python scripts/quality/checks.py UFO; if intended: "
                     f"update_test_data.py --quality): {new}")
    assert not stale, f"quality findings fixed, remove from the list: {stale}"


# the glyphs whose wobbles changed when the check stopped depending on the
# contours' direction and start (2026-11-24): a lobe split at the start
# (Ө ∅ ѳ.sc u.sc.horn), a bend near the threshold one way only (a ß)
WOBBLE_SAMPLE = ["a", "germandbls", "uni04E8", "uni2205", "uni0473.sc", "u.sc.horn", "o", "S", "uni2E0E"]


def test_wobbles_read_either_way(ufo):
    """checks.reversals finds the same with every contour reversed or begun
    at another node"""
    from checks import reversals
    from fontTools.pens.pointPen import ReverseContourPointPen
    from ufoLib2.objects import Glyph

    def redrawn(glyph, turn):
        g = Glyph()
        pen = g.getPointPen()
        for c in glyph.contours:
            if turn:
                c.drawPoints(ReverseContourPointPen(pen))
                continue
            pts = list(c.points)
            ons = [i for i, p in enumerate(pts) if p.type]
            k = ons[len(ons) // 2] if ons else 0
            pen.beginPath()
            for p in pts[k:] + pts[:k]:
                pen.addPoint((p.x, p.y), p.type, p.smooth)
            pen.endPath()
        return g

    for name in (n for n in WOBBLE_SAMPLE if n in ufo):
        found = reversals(ufo[name])
        assert reversals(redrawn(ufo[name], True)) == found, name
        assert reversals(redrawn(ufo[name], False)) == found, name
