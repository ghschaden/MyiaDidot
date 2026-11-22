"""The pre-commit hook's shortcut for a commit that only accepts baselines
(TODO.md, T11): when the staged tree differs from one already checked only
under tests/data/, run what that can change instead of the whole suite.

    rerun_plan.py record STATE KEY TREE HEAD TOOLCHAIN REPRO OUTCOME
        after a run: STATE/KEY.meta, with the tests that failed (read from
        STATE/KEY.log's FAILED/ERROR lines) when OUTCOME is "fail"
    rerun_plan.py plan STATE TREE HEAD TOOLCHAIN REPRO
        before a run: prints the path of a file listing the pytest
        selection, or nothing (run everything)

A run is reused only with the same HEAD, toolchain and reproduce flag. The
selection is the earlier run's failed tests and every test module that
names a changed data file (its name without the style, as style_data()
builds it). A data file no test module names gives no plan: the full
suite runs. A run whose failure was not a test (reproduce, a crash) or
that was stopped records nothing.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

STYLES = ("BoldItalic", "Regular", "Italic", "Bold")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def failed_tests(log):
    """The node ids pytest's summary names as FAILED or ERROR."""
    found = []
    for line in log.splitlines():
        m = re.match(r"(?:FAILED|ERROR) (\S+)", line)
        if m and m.group(1) not in found:
            found.append(m.group(1))
    return found


def record(state, key, tree, head, toolchain, repro, outcome):
    state = Path(state)
    log = (state / f"{key}.log").read_text(errors="replace") if (state / f"{key}.log").exists() else ""
    if outcome == "pass":
        failed = []
    else:
        failed = failed_tests(log)
        # a failure that is not a test's (make reproduce, a crash): not reusable
        if not failed or "a generator run would change" in log or "fontforge missing" in log:
            return
    (state / f"{key}.meta").write_text(json.dumps(
        {"tree": tree, "head": head, "toolchain": toolchain, "repro": repro, "failed": failed}))


def stem(path):
    """quality-Italic.txt -> quality.txt; the name a test module asks for"""
    name = Path(path).name
    base, dot, ext = name.partition(".")
    for s in STYLES:
        if base.endswith("-" + s):
            return base[: -len(s) - 1] + dot + ext
    return name


def plan(state, tree, head, toolchain, repro):
    state = Path(state)
    metas = sorted(state.glob("*.meta"), key=lambda p: p.stat().st_mtime, reverse=True)
    for meta in metas:
        try:
            m = json.loads(meta.read_text())
        except (OSError, ValueError):
            continue
        if (m.get("head"), m.get("toolchain"), m.get("repro")) != (head, toolchain, repro):
            continue
        if m["tree"] == tree:
            continue
        changed = git("diff-tree", "-r", "--name-only", m["tree"], tree).split()
        if not changed or not all(p.startswith("tests/data/") for p in changed):
            continue
        modules = git("ls-tree", "--name-only", tree, "tests/").split()
        modules = [p for p in modules if re.match(r"tests/test_.*\.py$", p)]
        texts = {p: git("show", f"{tree}:{p}") for p in modules}
        selection = set()
        for path in changed:
            names = {stem(path), Path(path).name}
            users = {p for p, text in texts.items() if any(n in text for n in names)}
            if not users:
                return None  # a data file no module names: everything
            selection |= users
        for node in m["failed"]:
            if node.split("::")[0] not in selection:
                selection.add(node)
        out = state / f"{tree}.select"
        out.write_text("\n".join(sorted(selection)) + "\n")
        return out
    return None


def main():
    cmd, *args = sys.argv[1:]
    if cmd == "record":
        record(*args)
    elif cmd == "plan":
        out = plan(*args)
        if out:
            print(Path(out).resolve())
    else:
        sys.exit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
