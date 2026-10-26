"""Greek pairs: none where Charis and Libertinus agree against Myia.

Two text faces made apart, setting a frequent Greek pair alike and both
wider (or both tighter) than Myia does, after the shift by Myia's own Latin
(scripts/quality/greek_pairs.py): that pair is to be fixed (CLAUDE.md,
reference fonts). Each style's known ones are in data/greek-pairs.txt
(greek-pairs-Italic.txt ...), "pair  # off N: reason", N the distance in
n n gaps. A new pair fails, a listed one that is fixed fails (delete its
line), and so does one gone further off than listed (by more than SLACK).
Needs the references (build/refs/, the installed Libertinus and Charis) and
the UDHR texts (`make udhr`); skipped without them.
After an intended change: scripts/update_test_data.py --greek --ufo UFO.
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


def greek_findings(ufo_path, otf):
    """{pair: off}, or None without the references or texts."""
    from greek_pairs import agreeing_against

    udhr = ROOT / "build" / "udhr"
    if not all((udhr / n).exists() for n in ("udhr_ell_monotonic.xml", "udhr_ell_polytonic.xml", "udhr_eng.xml")):
        return None
    try:
        return agreeing_against(Path(ufo_path).stem.split("-", 1)[-1], myia=otf)
    except FileNotFoundError:
        return None


def test_greek_pairs(otf_path, ufo_path):
    found = greek_findings(ufo_path, otf_path)
    if found is None:
        if os.environ.get("MYIA_REQUIRE_REFERENCES") == "1":
            pytest.fail("required references or UDHR texts missing; provision pinned inputs first")
        pytest.skip("references or UDHR texts missing (build/refs/, make udhr)")
    listed = read_list(style_data("greek-pairs.txt", ufo_path).name)
    new = {p: off for p, off in found.items() if p not in listed}
    fixed = sorted(set(listed) - set(found))
    worse = {}
    for p, why in listed.items():
        m = re.match(r"off (-?[\d.]+)", why)
        if p in found and m and abs(found[p]) > abs(float(m[1])) + SLACK:
            worse[p] = f"{m[1]} -> {found[p]}"
    assert not new, ("Charis and Libertinus agree against Myia (python scripts/quality/greek_pairs.py "
                     f"STYLE; if intended: update_test_data.py --greek): {new}")
    assert not worse, f"Greek pairs further off than listed: {worse}"
    assert not fixed, f"Greek pairs fixed, remove from the list: {fixed}"
