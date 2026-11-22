"""The pre-commit hook's shortcut for commits that only accept baselines
(tools/git-hooks/rerun_plan.py, TODO.md T11), on a throwaway repository."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("rerun_plan", ROOT / "tools/git-hooks/rerun_plan.py")
rerun_plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rerun_plan)


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env |= {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org"}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True, env=env).stdout.strip()


def tree(repo, files):
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
    git(repo, "add", "-A")
    return git(repo, "write-tree")


def test_plan(tmp_path, monkeypatch):
    repo, state = tmp_path / "repo", tmp_path / "state"
    repo.mkdir()
    state.mkdir()
    git(repo, "init", "-q")
    base = tree(repo, {
        "tests/test_quality.py": 'style_data("quality.txt", p)\n',
        "tests/test_other.py": "nothing\n",
        "tests/data/quality-Italic.txt": "a\n",
        "tests/data/unread.txt": "a\n",
        "scripts/x.py": "a\n",
    })
    git(repo, "commit", "-q", "-m", "base")
    head = git(repo, "rev-parse", "HEAD")
    monkeypatch.chdir(repo)
    (state / "k.log").write_text("FAILED tests/test_other.py::test_b[x] - no\n")
    rerun_plan.record(str(state), "k", base, head, "T", "1", "fail")
    assert json.loads((state / "k.meta").read_text())["failed"] == ["tests/test_other.py::test_b[x]"]

    only_data = tree(repo, {"tests/data/quality-Italic.txt": "b\n"})
    out = rerun_plan.plan(str(state), only_data, head, "T", "1")
    assert out.read_text().split() == ["tests/test_other.py::test_b[x]", "tests/test_quality.py"]
    # another HEAD or toolchain: everything
    assert rerun_plan.plan(str(state), only_data, "0" * 40, "T", "1") is None
    assert rerun_plan.plan(str(state), only_data, head, "U", "1") is None
    # a script changed too: everything
    git(repo, "checkout", "-q", "--", ".")
    with_script = tree(repo, {"tests/data/quality-Italic.txt": "b\n", "scripts/x.py": "b\n"})
    assert rerun_plan.plan(str(state), with_script, head, "T", "1") is None
    # a data file no module names: everything
    unread = tree(repo, {"scripts/x.py": "a\n", "tests/data/unread.txt": "b\n"})
    assert rerun_plan.plan(str(state), unread, head, "T", "1") is None


def test_record_skips_failures_not_of_tests(tmp_path):
    (tmp_path / "k.log").write_text("pre-commit: a generator run would change the generated styles\n")
    rerun_plan.record(str(tmp_path), "k", "t", "h", "T", "1", "fail")
    assert not (tmp_path / "k.meta").exists()
