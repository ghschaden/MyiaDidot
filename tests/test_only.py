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


def test_prepare_copies_and_drafts_beside_it(tmp_path, monkeypatch):
    monkeypatch.setattr(fontforge_inputs, "READ_ONLY", False)
    monkeypatch.setattr(fontforge_inputs, "DRAFTS_UFO", fontforge_inputs.DRAFTS_UFO)
    target = tmp_path / "T.ufo"
    font = ufoLib2.Font()
    font.newGlyph("a").width = 500
    font.save(target)
    out = tmp_path / "scratch" / "O.ufo"
    out.mkdir(parents=True)
    (out / "stale.txt").write_text("from an older run")
    assert scratch_out.prepare(target, out) == out.resolve()
    # the drafts go to a copy beside OUT, never to sources/drafts
    assert fontforge_inputs.DRAFTS_UFO == (tmp_path / "scratch" / "O-drafts.ufo").resolve()
    assert (fontforge_inputs.DRAFTS_UFO / "metainfo.plist").exists()
    assert not fontforge_inputs.READ_ONLY
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


# stage B, tier 2 (docs/claude/only.md): the Bold's `--only` makes what it is
# asked for exactly as the whole run did, and what it holds but was not asked
# for comes out as committed. The Bold Italic's, below, the same with the Italic's
# own finishing passes (finalization.absent: a pass goes on without a glyph the run
# does not hold).
@pytest.mark.parametrize("asked", [["a"], ["b"], ["O"], ["e"], ["T", "hyphen"], ["gravecomb"]])
def test_bold_only_makes_the_glyphs_as_committed(asked, tmp_path):
    out = tmp_path / "MyiaDidot-Bold.ufo"
    before = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                            capture_output=True, text=True).stdout
    r = subprocess.run([PY, "-I", str(ROOT / "scripts/make_bold.py"), str(ROOT / "sources/MyiaDidot-Regular.ufo"),
                        str(ROOT / "sources/MyiaDidot-Bold.ufo"), "--only", *asked, "--out", str(out)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    assert "come out as committed" in r.stdout
    from check_reproducible import differences

    lines = [ln for ln in differences(ufoLib2.Font.open(out), ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Bold.ufo"))
             if ln.startswith("glyph ")]
    assert not lines, lines[:5]
    after = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    assert before == after


@pytest.mark.parametrize("asked", [["hyphen"], ["a"], ["T"], ["m"], ["uni044C"], ["y"]])
def test_bold_italic_only_makes_the_glyphs_as_committed(asked, tmp_path):
    out = tmp_path / "MyiaDidot-BoldItalic.ufo"
    before = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                            capture_output=True, text=True).stdout
    r = subprocess.run([PY, "-I", str(ROOT / "scripts/make_bold.py"), str(ROOT / "sources/MyiaDidot-Italic.ufo"),
                        str(ROOT / "sources/MyiaDidot-BoldItalic.ufo"), "--only", *asked, "--out", str(out)],
                       capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    assert "come out as committed" in r.stdout
    from check_reproducible import differences

    lines = [ln for ln in differences(ufoLib2.Font.open(out), ufoLib2.Font.open(ROOT / "sources/MyiaDidot-BoldItalic.ufo"))
             if ln.startswith("glyph ")]
    assert not lines, lines[:5]
    after = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    assert before == after


@pytest.mark.parametrize("asked", [["hyphen"], ["a"], ["T"], ["m"], ["W"], ["uni044C"], ["y"], ["e"], ["b"],
                                   ["Q"], ["uni0442"], ["Alpha"], ["t"]])
def test_italic_only_makes_the_glyphs_as_committed(asked, tmp_path):
    out = tmp_path / "MyiaDidot-Italic.ufo"
    before = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                            capture_output=True, text=True).stdout
    r = subprocess.run([PY, "-I", str(ROOT / "scripts/make_italic.py"), str(ROOT / "sources/MyiaDidot-Regular.ufo"),
                        str(ROOT / "sources/MyiaDidot-Italic.ufo"), "--only", *asked, "--out", str(out)],
                       capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    assert "come out as committed" in r.stdout
    from check_reproducible import differences

    lines = [ln for ln in differences(ufoLib2.Font.open(out), ufoLib2.Font.open(ROOT / "sources/MyiaDidot-Italic.ufo"))
             if ln.startswith("glyph ")]
    assert not lines, lines[:5]
    after = subprocess.run(["git", "status", "--porcelain", "sources", "tests/data"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    assert before == after


def test_a_measure_cannot_be_asked_for_in_a_run():
    r = subprocess.run([PY, "-I", str(ROOT / "scripts/make_bold.py"), str(ROOT / "sources/MyiaDidot-Regular.ufo"),
                        str(ROOT / "sources/MyiaDidot-Bold.ufo"), "--only", "zero"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0 and "measure" in (r.stdout + r.stderr)


def test_the_equivalence_check_can_fail(tmp_path):
    """tier 4: a glyph read but not asked for that comes out unlike the
    committed makes the run end with 2 and list it (an edge the graph lacks,
    or a pass that looks at glyphs it is not told to)"""
    import only_run

    def font(width_b):
        f = ufoLib2.Font()
        f.info.unitsPerEm = 2048
        for name, width in (("a", 500), ("b", width_b)):
            g = f.newGlyph(name)
            g.width = width
            pen = g.getPen()
            pen.moveTo((0, 0))
            pen.lineTo((100, 0))
            pen.lineTo((100, 100))
            pen.closePath()
        return f

    target, work, out = tmp_path / "T.ufo", tmp_path / "w" / "W.ufo", tmp_path / "o" / "O.ufo"
    font(600).save(target)
    work.parent.mkdir()
    font(650).save(work)
    ctx = only_run.Context(tmp_path / "S.ufo", target, out, {"a"}, {"a", "b"}, work, False)
    assert ctx.finish() == 2
    work.parent.mkdir()  # (finish removed the work folder)
    font(600).save(work)
    ctx2 = only_run.Context(tmp_path / "S.ufo", target, out, {"a"}, {"a", "b"}, work, False)
    assert ctx2.finish() == 0
