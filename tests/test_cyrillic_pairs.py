"""Cyrillic pairs: none outside the references' whole range.

A frequent Cyrillic pair set wider or tighter than Old Standard, EB
Garamond, Libertinus and Charis all do, after the shift by Myia's own Latin,
by more than the tolerance (scripts/quality/greek_pairs.py --script
cyrillic, outside). Not Charis and Libertinus agreeing, as for Greek: for
Cyrillic they are the outliers, Old Standard and EB Garamond side with
Myia. Each style's known ones are in data/cyrillic-pairs.txt
(cyrillic-pairs-Italic.txt ...), "pair  # off N: reason". A new pair fails,
a listed one that is fixed fails (delete its line), and so does one gone
further off than listed (by more than SLACK). Needs the references and the
UDHR texts (`make udhr`); skipped without them.
After an intended change: scripts/update_test_data.py --cyrillic --ufo UFO.
"""

import os
import re
import sys
from pathlib import Path

import pytest
from conftest import ROOT, style_data
from test_composites import read_list

sys.path.insert(0, str(ROOT / "scripts" / "quality"))
SLACK = 0.03


def cyrillic_findings(ufo_path, otf):
    """{pair: off}, or None without the references or texts."""
    from greek_pairs import SCRIPTS, outside

    udhr = ROOT / "build" / "udhr"
    if not all((udhr / n).exists() for n in (*SCRIPTS["cyrillic"]["texts"], "udhr_eng.xml")):
        return None
    try:
        return outside(Path(ufo_path).stem.split("-", 1)[-1], myia=otf)
    except FileNotFoundError:
        return None


def test_cyrillic_pairs(otf_path, ufo_path):
    found = cyrillic_findings(ufo_path, otf_path)
    if found is None:
        if os.environ.get("MYIA_REQUIRE_REFERENCES") == "1":
            pytest.fail("required references or UDHR texts missing; provision pinned inputs first")
        pytest.skip("references or UDHR texts missing (build/refs/, make udhr)")
    listed = read_list(style_data("cyrillic-pairs.txt", ufo_path).name)
    new = {p: off for p, off in found.items() if p not in listed}
    fixed = sorted(set(listed) - set(found))
    worse = {}
    for p, why in listed.items():
        m = re.match(r"off (-?[\d.]+)", why)
        if p in found and m and abs(found[p]) > abs(float(m[1])) + SLACK:
            worse[p] = f"{m[1]} -> {found[p]}"
    assert not new, ("outside the Cyrillic references' range (python scripts/quality/greek_pairs.py "
                     f"STYLE --script cyrillic; if intended: update_test_data.py --cyrillic): {new}")
    assert not worse, f"Cyrillic pairs further off than listed: {worse}"
    assert not fixed, f"Cyrillic pairs fixed, remove from the list: {fixed}"
