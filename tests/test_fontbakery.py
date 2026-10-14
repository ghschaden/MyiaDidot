"""fontbakery's universal profile: no FAIL/ERROR/FATAL beyond the allowlist.

data/fontbakery-allow.txt lists "check-id  # reason" for known failures; a
listed check that passes again must be removed, so the list only shrinks.
"""

import json
import subprocess

import pytest
import ufo2ft
import ufoLib2
from conftest import ROOT
from test_composites import read_list

BAD = {"FAIL", "ERROR", "FATAL"}


@pytest.fixture(scope="session")
def release_otf(ufo_path, tmp_path_factory):
    path = tmp_path_factory.mktemp("release") / f"{ufo_path.stem}.otf"
    ufo2ft.compileOTF(ufoLib2.Font.open(ufo_path)).save(path)
    return path


def fontbakery_failures(font_path, tmp_path):
    report = tmp_path / "fb.json"
    subprocess.run(
        [str(ROOT / ".venv/bin/fontbakery"), "check-universal", "--json", str(report), str(font_path)],
        capture_output=True, text=True, check=False,
    )
    data = json.loads(report.read_text())
    failed = {}
    for section in data["sections"]:
        for check in section["checks"]:
            if check["result"] in BAD:
                msgs = [log["message"].get("message", "") for log in check.get("logs", []) if log.get("status") in BAD]
                check_id = check["key"][1].removeprefix("<FontBakeryCheck:").rstrip(">")
                failed[check_id] = msgs
    return failed


def test_fontbakery_universal(release_otf, tmp_path):
    allowed = read_list("fontbakery-allow.txt")
    failed = fontbakery_failures(release_otf, tmp_path)
    new = {k: v for k, v in failed.items() if k not in allowed}
    stale = sorted(set(allowed) - set(failed))
    assert not new, "new fontbakery failures:\n" + "\n".join(
        f"  {k}: {' / '.join(str(m)[:300] for m in v)}" for k, v in new.items())
    assert not stale, f"fontbakery checks pass again, remove from the allowlist: {stale}"
