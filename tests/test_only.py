"""T2's stage A (docs/claude/only.md): a generator's whole run into scratch
with --out, never into sources/. No generator is run whole here: make
reproduce holds the run's result on every commit, and --out only moves
where it is written."""

import subprocess
import sys
from pathlib import Path

import fontforge_inputs
import only_sheet
import pytest
import scratch_out
import ufoLib2

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


@pytest.mark.parametrize("script, target", [("make_bold.py", "MyiaDidot-Bold.ufo"),
                                            ("make_italic.py", "MyiaDidot-Italic.ufo")])
@pytest.mark.parametrize("out", ["sources/x.ufo", "sources/MyiaDidot-Bold.ufo", "sources/drafts/y.ufo"])
def test_out_under_sources_refused(script, target, out, tmp_path):
    before = subprocess.run(["git", "status", "--porcelain", "sources"], cwd=ROOT, capture_output=True, text=True).stdout
    r = subprocess.run([PY, "-I", str(ROOT / "scripts" / script), str(ROOT / "sources/MyiaDidot-Regular.ufo"),
                        str(ROOT / "sources" / target), "--out", str(ROOT / out)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0 and "under sources/" in r.stderr
    after = subprocess.run(["git", "status", "--porcelain", "sources"], cwd=ROOT, capture_output=True, text=True).stdout
    assert before == after
    assert not (ROOT / out).exists() or out == "sources/MyiaDidot-Bold.ufo"


def test_refused():
    assert scratch_out.refused(ROOT / "sources")
    assert scratch_out.refused(ROOT / "sources/../sources/a.ufo")
    assert scratch_out.refused(ROOT / "build/only/x")  # not a UFO
    assert scratch_out.refused(ROOT / "build/only/MyiaDidot-Bold.ufo") is None


def test_prepare_copies_and_reads_drafts_only(tmp_path, monkeypatch):
    monkeypatch.setattr(fontforge_inputs, "READ_ONLY", False)
    target = tmp_path / "T.ufo"
    font = ufoLib2.Font()
    font.newGlyph("a").width = 500
    font.save(target)
    out = tmp_path / "scratch" / "O.ufo"
    out.mkdir(parents=True)
    (out / "stale.txt").write_text("from an older run")
    assert scratch_out.prepare(target, out) == out.resolve()
    assert fontforge_inputs.READ_ONLY
    assert not (out / "stale.txt").exists()
    assert ufoLib2.Font.open(out)["a"].width == 500
    with pytest.raises(SystemExit):
        scratch_out.prepare(target, target)


def test_read_only_store_refuses_a_draft_to_make(monkeypatch):
    """a scratch run never calls FontForge into sources/drafts: asked for a
    draft anew it ends, naming make generate"""
    monkeypatch.setattr(fontforge_inputs, "READ_ONLY", True)
    up = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo")
    with pytest.raises(SystemExit, match="make generate"):
        fontforge_inputs.drafts(up, 0.7, "1/1", redraft=True)


def test_sheet_words():
    w = only_sheet.words(["v"]).split()
    assert w[:2] == ["nvo", "HvO"] and len(w) == 5 and all("v" in x for x in w[2:])
    font = ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Bold.ufo")
    assert only_sheet.characters(font, ["n", "aacute", "f_f"])[:2] == ["n", "á"]
