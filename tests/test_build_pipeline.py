"""Failure paths must never publish an incomplete artifact or baseline."""

import json
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import ufoLib2
from build_font import build
from build_support import atomic_output, publish_files
from check_reproducible import differences


@pytest.mark.parametrize("stage", ("compile", "hints", "stat"))
@pytest.mark.parametrize("existing", (False, True))
def test_failed_font_build_preserves_previous_output(tmp_path, stage, existing):
    output = tmp_path / "font.otf"
    if existing:
        output.write_bytes(b"previous valid font")
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        phase = "compile" if "--output-path" in command else (
            "hints" if any(str(x).endswith("ps_hints.py") for x in command) else "stat")
        if phase == "compile":
            Path(command[-1]).write_bytes(b"unfinished")
        if phase == stage:
            raise subprocess.CalledProcessError(1, command)

    for attempt in range(2):
        with pytest.raises(subprocess.CalledProcessError):
            build("otf", tmp_path / "source.ufo", output, run=run)
        assert output.read_bytes() == b"previous valid font" if existing else not output.exists()
        assert len(calls) == (attempt + 1) * {"compile": 1, "hints": 2, "stat": 3}[stage]
    assert list(tmp_path.iterdir()) == ([output] if existing else [])


def test_atomic_output_only_replaces_on_success(tmp_path):
    path = tmp_path / "font"
    path.write_bytes(b"old")
    with pytest.raises(RuntimeError), atomic_output(path) as temporary:
        temporary.write_bytes(b"partial")
        raise RuntimeError("failed postprocessing")
    assert path.read_bytes() == b"old"
    with atomic_output(path) as temporary:
        temporary.write_bytes(b"complete")
    assert path.read_bytes() == b"complete"


def test_baseline_publication_rolls_back(tmp_path, monkeypatch):
    import build_support

    first, second = tmp_path / "first", tmp_path / "second"
    first.write_bytes(b"original")
    replace = build_support.os.replace

    def fail_second(source, destination):
        if destination == second:
            raise OSError("injected publication failure")
        return replace(source, destination)

    monkeypatch.setattr(build_support.os, "replace", fail_second)
    with pytest.raises(OSError):
        publish_files({first: b"new", second: b"new"})
    assert first.read_bytes() == b"original"
    assert not second.exists()


@pytest.mark.parametrize(("field", "value"), (("familyName", "Changed"), ("unitsPerEm", 2048),
                                               ("openTypeOS2WinAscent", 1500)))
def test_reproduction_detects_font_info(field, value):
    source = ufoLib2.Font()
    changed = deepcopy(source)
    setattr(changed.info, field, value)
    assert f"font info {field}" in differences(changed, source)


def test_reproduction_detects_unicode_and_order():
    source = ufoLib2.Font()
    source.newGlyph("A").unicodes = [65]
    changed = deepcopy(source)
    changed["A"].unicodes = [66]
    assert any("unicodes" in line for line in differences(changed, source))
    changed = deepcopy(source)
    changed.lib["public.glyphOrder"] = ["A"]
    assert "font lib public.glyphOrder" in differences(changed, source)


def test_exact_report_approval_rejects_different_changes(tmp_path, monkeypatch):
    import update_test_data as updater

    monkeypatch.setattr(updater, "ROOT", tmp_path)
    monkeypatch.setattr(updater, "toolchain", lambda: {"python": "test"})
    (tmp_path / "scripts").mkdir()
    source, font = tmp_path / "font.ufo", tmp_path / "font.otf"
    source.write_text("source")
    font.write_text("compiled")
    changes = [{"text": "fi", "features": {}, "script": None, "language": "en",
                "before": [["f", 10, 0, 0]], "after": [["fi", 15, 0, 0]]}]
    monkeypatch.setattr(updater, "shaping_changes", lambda *_: (1, changes, "digest"))
    report = tmp_path / "report.json"
    with pytest.raises(SystemExit, match="--accept-report"):
        updater.check_changes(source, font, tmp_path, 1, report_path=report)
    approval = json.loads(report.read_text())["approval_sha256"]
    assert updater.check_changes(source, font, tmp_path, 1, approval, report) == ("digest", 1)
    changes[0]["text"] = "fl"
    with pytest.raises(SystemExit, match="--accept-report"):
        updater.check_changes(source, font, tmp_path, 1, approval, report)


def test_combined_baseline_failure_leaves_quality_unchanged(tmp_path, monkeypatch):
    import update_test_data as updater

    baseline = tmp_path / "quality.txt"
    baseline.write_text("# original\n")
    monkeypatch.setattr(updater, "style_data", lambda *_: baseline)
    monkeypatch.setattr(updater, "read_list", lambda *_: {})
    monkeypatch.setattr(updater, "quality_keys", lambda *_: {"new finding": "why"})
    monkeypatch.setattr(updater.ufoLib2.Font, "open", lambda *_: object())
    monkeypatch.setattr(updater, "Builds", lambda *_: SimpleNamespace(font=object(), otf=Path("unused")))
    monkeypatch.setattr(updater, "TTFont", lambda *_: object())
    monkeypatch.setattr(updater, "Shaper", lambda *_: object())

    def refuse(*_):
        raise SystemExit("review required")

    monkeypatch.setattr(updater, "check_changes", refuse)
    monkeypatch.setattr(updater.sys, "argv", ["update", "--quality", "--golden"])
    with pytest.raises(SystemExit, match="review required"):
        updater.main()
    assert baseline.read_text() == "# original\n"


def test_shaping_script_and_language_are_keyword_only():
    import inspect

    from font_shaping import Shaper

    signature = inspect.signature(Shaper.shape)
    for name in ("language", "script"):
        assert signature.parameters[name].kind == inspect.Parameter.KEYWORD_ONLY


def test_snapshot_uses_frozen_sources_and_reference_inputs(tmp_path, monkeypatch):
    import sys

    import validate_snapshot

    root = tmp_path / "repository"
    root.mkdir()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    (root / "source.txt").write_text("committed")
    git("add", "source.txt")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
    (root / "source.txt").write_text("edited during validation")
    (root / ".venv").mkdir()
    reference = root / "build/refs/input"
    reference.parent.mkdir(parents=True)
    reference.write_text("pinned input")
    monkeypatch.setattr(validate_snapshot, "ROOT", root)
    monkeypatch.setattr(validate_snapshot, "toolchain", lambda: {"python": "test"})
    command = [sys.executable, "-I", "-c", (
        "from pathlib import Path; "
        "assert Path('source.txt').read_text() == 'committed'; "
        "assert Path('build/refs/input').read_text() == 'pinned input'; "
        "Path('build/refs/input').write_text('changed only in snapshot')")]
    assert validate_snapshot.run_snapshot("HEAD", command) == 0
    assert (root / "source.txt").read_text() == "edited during validation"
    assert reference.read_text() == "pinned input"
    manifest = json.loads(next((root / "build/validation").glob("*.json")).read_text())
    assert manifest["commit"] == git("rev-parse", "HEAD")
    assert manifest["inputs"]["refs"]


def test_failed_snapshot_publishes_no_validation_manifest(tmp_path, monkeypatch):
    import sys

    import validate_snapshot

    # Exercise failure after snapshot creation using the real project tree.
    monkeypatch.setattr(validate_snapshot, "toolchain", lambda: {})
    monkeypatch.setattr(validate_snapshot, "atomic_output", lambda *_: pytest.fail("published a failed run"))
    assert validate_snapshot.run_snapshot("HEAD", [sys.executable, "-I", "-c", "raise SystemExit(7)"]) == 7


def test_reference_cache_rebuilds_when_recipe_or_bytes_change(tmp_path, monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("reference_fetcher", Path(__file__).parents[1] / "scripts/quality/fetch_refs.py")
    fetcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetcher)
    monkeypatch.setattr(fetcher, "REFDIR", tmp_path)
    monkeypatch.setattr(fetcher, "FONTS", {"Reference": ("raw.ttf", {"wght": 400})})
    monkeypatch.setattr(fetcher, "RAW_SHA256", {"raw.ttf": "pin1"})
    monkeypatch.setattr(fetcher, "fetch", lambda *_: None)
    monkeypatch.setattr(fetcher, "fetch_system_references", lambda *_: None)
    builds = []

    class Font:
        def save(self, path):
            builds.append(True)
            path.write_bytes(b"compiled reference")

    monkeypatch.setattr(fetcher, "TTFont", lambda *_: Font())
    monkeypatch.setattr(fetcher, "instantiateVariableFont", lambda font, axes: font)
    fetcher.main()
    fetcher.main()
    assert len(builds) == 1
    fetcher.FONTS["Reference"] = ("raw.ttf", {"wght": 700})
    fetcher.main()
    assert len(builds) == 2
    (tmp_path / "Reference.ttf").write_bytes(b"corrupted")
    fetcher.main()
    assert len(builds) == 3


def test_reference_checksum_failure_keeps_existing_file(tmp_path):
    from reference_inputs import fetch

    path = tmp_path / "reference"
    path.write_bytes(b"wrong bytes")
    with pytest.raises(ValueError, match="SHA-256"):
        fetch("https://unused.invalid", path, "expected hash")
    assert path.read_bytes() == b"wrong bytes"


def test_baseline_compiles_only_requested_variants(tmp_path, monkeypatch):
    import font_builds

    calls = []

    def compile_selected(source, variant):
        calls.append(variant)
        path = tmp_path / f"{variant}.otf"
        path.write_bytes(b"compiled")
        return path

    monkeypatch.setattr(font_builds, "compiled_variant", compile_selected)
    builds = font_builds.Builds("unused.ufo", tmp_path)
    assert not calls
    assert builds.otf == builds.otf
    assert calls == ["test_otf"]
    assert not (tmp_path / "release_otf.otf").exists()
    assert not (tmp_path / "decomposed.otf").exists()


def test_compilation_cache_keys_sources_and_options(tmp_path, monkeypatch):
    import font_builds

    source = tmp_path / "source.ufo"
    source.mkdir()
    (source / "glyph").write_text("first")
    monkeypatch.setattr(font_builds, "ROOT", tmp_path)
    monkeypatch.setattr(font_builds, "toolchain", lambda: {"compiler": "test"})
    monkeypatch.setattr(font_builds.ufoLib2.Font, "open", lambda *_: object())
    builds = []

    class Font:
        def save(self, path):
            path.write_bytes(b"compiled")

    class Parsed:
        def __init__(self, path, **kwargs):
            if path.read_bytes() != b"compiled":
                raise ValueError("truncated cached font")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def ensureDecompiled(self):
            pass

    def compile_otf(*args, **options):
        builds.append(options)
        return Font()

    monkeypatch.setattr(font_builds, "TTFont", Parsed)
    monkeypatch.setattr(font_builds.ufo2ft, "compileOTF", compile_otf)
    first = font_builds.compiled_variant(source, "test_otf")
    assert font_builds.compiled_variant(source, "test_otf") == first
    assert len(builds) == 1
    release = font_builds.compiled_variant(source, "release_otf")
    assert release != first
    assert builds == [{"useProductionNames": False, "optimizeCFF": 0}, {}]
    first.write_bytes(b"truncated")
    assert font_builds.compiled_variant(source, "test_otf") == first
    assert len(builds) == 3
    (source / "glyph").write_text("changed")
    assert font_builds.compiled_variant(source, "test_otf") != first
    assert len(builds) == 4


def test_published_font_manifest_hashes_file_bytes(tmp_path, monkeypatch):
    import hashlib

    import build_font

    source = tmp_path / "input.ttf"
    source.write_bytes(b"source bytes")
    destination = tmp_path / "output.woff2"
    (tmp_path / "scripts").mkdir()
    (tmp_path / "uv.lock").write_text("locked")
    monkeypatch.setattr(build_font, "ROOT", tmp_path)
    monkeypatch.setattr(build_font, "toolchain", lambda: {})
    monkeypatch.setattr(build_font.sys, "argv", ["build_font", "woff2", str(source), str(destination)])
    monkeypatch.setattr(build_font, "build", lambda kind, src, dst: dst.write_bytes(b"finished font"))
    build_font.main()
    manifest = json.loads(destination.with_suffix(".woff2.json").read_text())
    assert manifest["output_sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest()
