"""Latin pairs in the italics: none outside the reference italics' range.

The upright's kerned Latin pairs, set in the built Italic (Bold Italic)
with kerning, their white over the style's own rhythm (n n, H H, H n, n H:
scripts/italic_kerning.py, share), against the same in Bodoni Moda, Libre
Bodoni, EB Garamond, Libertinus and Charis (docs/claude/spacing.md, "The
italics' Latin kerning"). Each style's known ones are in
data/latin-pairs-Italic.txt and latin-pairs-BoldItalic.txt, "pair  # off N:
reason", N past the range in shares of the rhythm (+ loose, - tight). A new
pair fails, a listed one that is fixed fails (delete its line), and so does
one gone further off than listed (by more than SLACK). The upright styles'
pairs are their own reviews' (pairs.py), not tested here. Needs the
references (build/refs/, scripts/quality/fetch_refs.py); skipped without.
After an intended change: scripts/update_test_data.py --latin --ufo UFO.
"""

import os
import re
import sys
from pathlib import Path

import pytest
from conftest import ROOT, style_data
from test_composites import read_list

sys.path.insert(0, str(ROOT / "scripts"))
SLACK = 0.03


def latin_findings(ufo_path, otf):
    """{pair: off}; {} for an upright style; None without the references."""
    import italic_kerning

    style = Path(ufo_path).stem.split("-", 1)[-1]
    if style not in italic_kerning.UPRIGHT:
        return {}
    try:
        return italic_kerning.outside(style, otf)
    except FileNotFoundError:
        return None


def test_latin_pairs(otf_path, ufo_path):
    if Path(ufo_path).stem.split("-", 1)[-1] not in ("Italic", "BoldItalic"):
        pytest.skip("the italics' test")
    found = latin_findings(ufo_path, otf_path)
    if found is None:
        if os.environ.get("MYIA_REQUIRE_REFERENCES") == "1":
            pytest.fail("required references missing; provision pinned inputs first")
        pytest.skip("references missing (build/refs/, scripts/quality/fetch_refs.py)")
    listed = read_list(style_data("latin-pairs.txt", ufo_path).name)
    new = {p: off for p, off in found.items() if p not in listed}
    fixed = sorted(set(listed) - set(found))
    worse = {}
    for p, why in listed.items():
        m = re.match(r"off (-?[+\d.]+)", why)
        if p in found and m and abs(found[p]) > abs(float(m[1])) + SLACK:
            worse[p] = f"{m[1]} -> {found[p]}"
    assert not new, ("Latin pairs outside the reference italics' range (scripts/italic_kerning.py; "
                     f"if intended: update_test_data.py --latin): {new}")
    assert not worse, f"Latin pairs further off than listed: {worse}"
    assert not fixed, f"Latin pairs now in range, remove from the list: {fixed}"
