"""Progress of a long run, for people and for the Claude Code progress pane.

    scripts/progress.py begin TARGET STEPS      # a run starts
    scripts/progress.py step TARGET N "label"   # step N of STEPS starts
    scripts/progress.py end TARGET              # the run is over

Writes build/progress/TARGET.json: {target, started, step, steps, label,
stepStarted, updated, done, estimate} (times in seconds since the epoch).
The length of every step is kept in build/progress/TARGET.history.json, so
the next run can say "step 2 of 4, about 60 % done": the estimate is the
elapsed time over the previous run's total, step by step. Nothing here
touches sources/; a failed write never stops a build.

MYIA_PROGRESS_DIR: another directory (the commit hook, which runs in a
snapshot of the staged tree, writes to the working copy's build/progress).
Targets: generate, only, reproduce, test, commit (2026-11-26).
"""

import json
import os
import sys
import time
from pathlib import Path

DIR = Path(os.environ.get("MYIA_PROGRESS_DIR") or Path(__file__).resolve().parent.parent / "build" / "progress")


def _load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _save(path, data):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(path)
    except OSError:
        pass


def _close_step(state, hist, now):
    if state.get("step"):
        hist.setdefault("steps", {})[str(state["step"])] = round(now - state["stepStarted"], 1)


def _estimate(state, hist, now):
    """share done 0..0.99, from the previous run's steps; None without one"""
    prev = hist.get("last", {})
    total = sum(prev.values())
    if not total:
        return None
    done = sum(v for k, v in prev.items() if int(k) < state["step"])
    return round(min(0.99, (done + min(now - state["stepStarted"], prev.get(str(state["step"]), 1e9))) / total), 2)


def begin(target, steps):
    now = time.time()
    hist = _load(DIR / f"{target}.history.json")
    hist["steps"] = {}
    _save(DIR / f"{target}.history.json", hist)
    _save(DIR / f"{target}.json", {"target": target, "started": now, "step": 0, "steps": int(steps), "label": "starting",
                                   "stepStarted": now, "updated": now, "done": False, "estimate": None})


def step(target, n, label):
    now = time.time()
    state = _load(DIR / f"{target}.json") or {"target": target, "started": now, "steps": int(n)}
    hist = _load(DIR / f"{target}.history.json")
    _close_step(state, hist, now)
    state.update(step=int(n), label=label, stepStarted=now, updated=now, done=False)
    state["estimate"] = _estimate(state, hist, now)
    _save(DIR / f"{target}.history.json", hist)
    _save(DIR / f"{target}.json", state)


def end(target):
    now = time.time()
    state = _load(DIR / f"{target}.json")
    hist = _load(DIR / f"{target}.history.json")
    if state:
        _close_step(state, hist, now)
        hist["last"] = hist.get("steps", {})
        state.update(done=True, updated=now, estimate=1.0, label="done")
        _save(DIR / f"{target}.history.json", hist)
        _save(DIR / f"{target}.json", state)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"begin": begin, "step": step, "end": end}[cmd](*args)
