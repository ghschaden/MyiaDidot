"""The Regular's generated parts are as their scripts make them now.

The generated styles are checked by `make reproduce`; the Regular is drawn,
but parts of it are generated too: the derived letters' records
(derive.py), letters in the kerning groups of their base or model
(kern_groups.py), pairs loosened where inks meet (kern_clear.py), the
small caps' aliases, accented forms, kerning, groups and
smcp/c2sc block (smallcaps.py), the breve resized (adjust_accents.py), the
anchors composites keep from their base and the stacked ones
(composites.py), the figures' spacing, their tabular forms and their lnum/pnum/tnum/zero
block (space_figures.py), the capital spacing block (cpsp.py), the case-sensitive forms
(case_forms.py). Each is idempotent: run again on a copy, nothing
may change. A difference means an edit made by hand to a generated part, or
a script changed without being rerun. (nfd_compose.py's ccmp block is
checked by what it does: NFC and NFD render alike, test_composites.py.)
"""

import shutil
import subprocess
import sys

import pytest
from conftest import ROOT, SOURCES

STEPS = [
    ["scripts/derive.py"],
    ["scripts/kern_groups.py"],
    ["scripts/kern_clear.py"],
    ["scripts/smallcaps.py"],
    ["scripts/adjust_accents.py"],
    ["scripts/composites.py", "--carry-anchors", "--stack-anchors", "--rebuild-stacked"],
    ["scripts/space_figures.py"],
    ["scripts/cpsp.py"],
    ["scripts/case_forms.py"],
]


def test_regular_generated_parts_current(tmp_path):
    regular = SOURCES / "MyiaDidot-Regular.ufo"
    if not regular.exists():
        pytest.skip("no Regular")
    copy = tmp_path / regular.name
    shutil.copytree(regular, copy)
    for script, *args in STEPS:
        subprocess.run([sys.executable, "-I", str(ROOT / script), str(copy), *args],
                       check=True, capture_output=True)
    subprocess.run([str(ROOT / ".venv/bin/ufonormalizer"), "-q", "-a", "-m", str(copy)], check=True)
    diff = subprocess.run(["diff", "-r", str(regular), str(copy)], capture_output=True, text=True, check=False)
    assert diff.returncode == 0, (
        "the Regular's generated parts differ from what their scripts make now (rerun them on it, "
        f"then `make normalize`; {', '.join(s[0] for s in STEPS)}):\n" + diff.stdout[:2000])
