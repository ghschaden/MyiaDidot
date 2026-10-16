"""Design quality beyond the outlines' faults: construction (smooth nodes,
kinks, extremes, whole units), alignment zones, stem weights, the italic's
slant, accent gaps and the Bold's widths against the Regular's.

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
