"""The Bold Italic's letters emboldened by their strokes, kept from run to run.

make_bold strokes each of the Italic's letters (stroke_bold.emboldened,
about half a second a letter, 9 of make generate's 11 minutes; 2026-11-04);
a letter whose outline, arguments and code are unchanged comes out the same,
so its result is kept, keyed by:

- the job's outline and arguments (exactly, by repr: floats round-trip);
- the source of stroke_bold.py and every project module it imports, at
  any depth (any edit to them starts afresh);
- the versions of Python and every installed package;
- the MYIA_* variables of the environment (stroke_bold reads several),
  but for those that only steer the run (MYIA_JOBS ...).

The cache is a SQLite file outside the synced working copy
($XDG_CACHE_HOME/myiadidot/strokes.sqlite, ~/.cache by default), shared by
every working copy (it is keyed by content, so they cannot mix). Entries
unused for PRUNE_DAYS go. MYIA_STROKE_CACHE=0 turns it off;
MYIA_STROKE_CACHE=PATH puts it elsewhere. With MYIA_BLEND_LOG the cache
is not used: that log is written while stroking.
`make reproduce` checks that a run from the cache makes the styles as
saved; to check the cache itself, run it once with MYIA_STROKE_CACHE=0.
"""

import ast
import hashlib
import importlib.metadata
import os
import pickle
import platform
import sqlite3
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ENTRY = "stroke_bold"
PRUNE_DAYS = 30
# variables that change how a run goes, not what it makes
STEERING = {"MYIA_JOBS", "MYIA_RECHECK", "MYIA_STROKE_CACHE", "MYIA_BLEND_LOG"}


def modules(entry=ENTRY):
    """{module name: sha256 of its source} for entry and the project
    modules it imports at any depth (imports inside functions too)."""
    seen, todo = {}, [entry]
    while todo:
        name = todo.pop()
        path = SCRIPTS / f"{name}.py"
        if name in seen or not path.exists():
            continue
        source = path.read_bytes()
        seen[name] = hashlib.sha256(source).hexdigest()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                todo += [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                todo.append(node.module.split(".")[0])
    return seen


def code_key():
    packages = sorted((d.metadata["Name"] or "", d.version) for d in importlib.metadata.distributions())
    env = sorted((k, v) for k, v in os.environ.items() if k.startswith("MYIA_") and k not in STEERING)
    blob = repr((sorted(modules().items()), packages, platform.python_version(), env))
    return hashlib.sha256(blob.encode()).hexdigest()


def path():
    """The cache file, or None when it is off."""
    setting = os.environ.get("MYIA_STROKE_CACHE", "")
    if setting == "0" or os.environ.get("MYIA_BLEND_LOG"):
        return None
    if setting:
        return Path(setting)
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "myiadidot" / "strokes.sqlite"


class Cache:
    """get(jobs) -> {name: value} of those kept; put(jobs, done) keeps the rest."""

    def __init__(self):
        self.file = path()
        self.db = None
        if self.file is None:
            return
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.file, timeout=60)
            self.db.execute("CREATE TABLE IF NOT EXISTS strokes (key TEXT PRIMARY KEY, value BLOB, used REAL)")
        except (OSError, sqlite3.Error) as e:
            print(f"  stroke cache off ({self.file}: {e})")
            self.db = None
            return
        self.code = code_key()

    def key(self, job):
        _name, value, args = job
        return hashlib.sha256(f"{self.code}\n{value!r}\n{args!r}".encode()).hexdigest()

    def get(self, jobs):
        if self.db is None:
            return {}
        keys = {}  # key: the names of the jobs with it (letters drawn alike share one)
        for job in jobs:
            keys.setdefault(self.key(job), []).append(job[0])
        found, hit = {}, []
        rows = list(keys)
        for i in range(0, len(rows), 500):
            part = rows[i:i + 500]
            query = f"SELECT key, value FROM strokes WHERE key IN ({','.join('?' * len(part))})"
            for key, blob in self.db.execute(query, part):
                value = pickle.loads(blob)
                found.update((name, value) for name in keys[key])
                hit.append(key)
        now = time.time()
        with self.db:
            self.db.executemany("UPDATE strokes SET used = ? WHERE key = ?", [(now, k) for k in hit])
        return found

    def put(self, jobs, done):
        """done: {name: value} for jobs (those just stroked)"""
        if self.db is None:
            return
        now = time.time()
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO strokes VALUES (?, ?, ?)",
                                [(self.key(job), pickle.dumps(done[job[0]], protocol=4), now) for job in jobs])
            self.db.execute("DELETE FROM strokes WHERE used < ?", (now - PRUNE_DAYS * 86400,))

    def close(self):
        if self.db is not None:
            self.db.close()
