"""scripts/stale.py: which styles a run must make (make generate STYLES=auto).

Against a stamp in a temporary directory, made from the sources as they are,
so the real stamp (build/stale) is never touched.
"""

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import stale  # noqa: E402


@pytest.fixture(scope="module")
def stamped(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("stale")
    mp = pytest.MonkeyPatch()
    mp.setattr(stale, "DIR", tmp)
    mp.setattr(stale, "STAMP", tmp / "stamp.json")
    with contextlib.redirect_stdout(io.StringIO()):
        stale.stamp()
    yield stale.STAMP.read_text()
    mp.undo()


def styles():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        stale.styles()
    return buf.getvalue().split()


def test_fresh_stamp_makes_nothing(stamped):
    stale.STAMP.write_text(stamped)
    assert styles() == []


@pytest.mark.parametrize("changed, made", [
    ("data_italic.py", ["Italic", "BoldItalic"]),
    ("make_italic.py", ["Italic", "BoldItalic"]),
    ("data_bold_italic.py", ["BoldItalic"]),
    ("derive.py", ["Italic", "Bold", "BoldItalic"]),
    ("a_file_not_named_in_REACHES.py", ["Italic", "Bold", "BoldItalic"]),
])
def test_generator_file_reaches(stamped, monkeypatch, changed, made):
    stale.STAMP.write_text(stamped)
    code = stale.generator_hashes()
    monkeypatch.setattr(stale, "generator_hashes", lambda: {**code, changed: "changed"})
    assert styles() == made


@pytest.mark.parametrize("style, entry, made", [
    ("Italic", "@kerning", ["Italic", "BoldItalic"]),  # the Bold Italic with the Italic
    ("Bold", "@features", ["Bold"]),
    ("BoldItalic", "a", ["BoldItalic"]),
])
def test_source_change(stamped, style, entry, made):
    data = json.loads(stamped)
    data["styles"][style]["source"][entry] = "old"
    stale.STAMP.write_text(json.dumps(data))
    assert styles() == made


def test_partial_stamp_keeps_the_others(stamped):
    data = json.loads(stamped)
    data["styles"]["Bold"]["source"]["a"] = "old"
    data["styles"]["BoldItalic"]["source"]["a"] = "old"
    stale.STAMP.write_text(json.dumps(data))
    with contextlib.redirect_stdout(io.StringIO()):
        stale.stamp("BoldItalic")
    assert styles() == ["Bold"]


def test_no_stamp_makes_all(stamped):
    stale.STAMP.unlink()
    assert styles() == stale.STYLES


def test_proof_holds_and_breaks(stamped, monkeypatch):
    """the hook's `proven`: true right after the run it was stamped by, false
    when an output or an input differs, or when FULL_REPRODUCE asks"""
    stale.STAMP.write_text(stamped)
    if not all("proof" in v for v in json.loads(stamped)["styles"].values()):
        pytest.skip("stamped in an environment that is not a plain run")
    with contextlib.redirect_stdout(io.StringIO()):
        assert stale.proven() == 0
        out, inputs = stale.proof_output, stale.proof_inputs
        monkeypatch.setattr(stale, "proof_output", lambda s: out(s) + ("x" if s == "Bold" else ""))
        assert stale.proven() == 1
        monkeypatch.setattr(stale, "proof_output", out)
        monkeypatch.setattr(stale, "proof_inputs", lambda s: inputs(s) + ("x" if s == "Italic" else ""))
        assert stale.proven() == 1
        monkeypatch.setattr(stale, "proof_inputs", inputs)
        monkeypatch.setenv("FULL_REPRODUCE", "1")
        assert stale.proven() == 1


def test_review_marks_are_not_output(tmp_path):
    """accepted.py writes into a generated style after its run: not part of
    what the proof compares; a real change is"""
    import shutil

    import ufoLib2
    from accepted import KEY

    ufo = tmp_path / "B.ufo"
    shutil.copytree(stale.SOURCES / "MyiaDidot-Bold.ufo", ufo)
    before = stale.ufo_digest(ufo)
    font = ufoLib2.Font.open(ufo)
    font["n"].lib[KEY] = {"date": "2026-01-01", "review": "x.pdf", "glyph": "0"}
    font.save()
    assert stale.ufo_digest(ufo) == before
    font["n"].width += 1
    font.save()
    assert stale.ufo_digest(ufo) != before


def test_unproven_per_style(stamped, monkeypatch):
    """each style's proof on its own: one that no longer holds is the only one
    the hook makes again"""
    stale.STAMP.write_text(stamped)
    if not all("proof" in v for v in json.loads(stamped)["styles"].values()):
        pytest.skip("stamped in an environment that is not a plain run")
    quiet = lambda m: None  # noqa: E731
    assert stale.unproven(say=quiet) == []
    out = stale.proof_output
    monkeypatch.setattr(stale, "proof_output", lambda s: out(s) + ("x" if s == "BoldItalic" else ""))
    assert stale.unproven(say=quiet) == ["BoldItalic"]
    data = json.loads(stamped)
    del data["styles"]["Bold"]["proof"]
    stale.STAMP.write_text(json.dumps(data))
    assert stale.unproven(say=quiet) == ["Bold", "BoldItalic"]


def test_scripts_digest_blind_to_comments_and_docstrings(tmp_path):
    """the proof holds over an edit to comments or docstrings alone (T8), not
    over a change of code or of a plain string; dot-directories (ruff's
    cache, which only the working copy has) and __pycache__ are not read"""
    root = tmp_path / "scripts"
    (root / "sub").mkdir(parents=True)
    src = '"""Module."""\n\n\ndef f(x):\n    """Doc."""\n    return x + 1  # one\n\n\nS = "kept"\n'
    (root / "m.py").write_text(src)
    (root / "sub" / "d.json").write_text("{}")
    base = stale.scripts_digest(root)

    (root / "m.py").write_text(src.replace("Module.", "Other.").replace("Doc.", "Else.")
                               .replace("# one", "# two\n    # three"))
    (root / ".ruff_cache").mkdir()
    (root / ".ruff_cache" / "x").write_text("cache")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "m.pyc").write_bytes(b"\0")
    assert stale.scripts_digest(root) == base

    for changed in (src.replace("x + 1", "x + 2"), src.replace('"kept"', '"other"')):
        (root / "m.py").write_text(changed)
        assert stale.scripts_digest(root) != base
    (root / "m.py").write_text(src)
    (root / "sub" / "d.json").write_text('{"a": 1}')
    assert stale.scripts_digest(root) != base
