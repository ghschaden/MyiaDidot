"""Atomic publication and input/toolchain identities shared by build tools."""

import fcntl
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
import unicodedata
from contextlib import ExitStack, contextmanager
from functools import cache
from pathlib import Path


def content_hash(path):
    path = Path(path)
    digest = hashlib.sha256()
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts) if path.is_dir() else [path]
    for item in files:
        digest.update(str(item.relative_to(path) if path.is_dir() else item.name).encode())
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@cache
def toolchain():
    import uharfbuzz

    versions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    ff = subprocess.run(["sh", "-c", "command -v fontforge >/dev/null && fontforge -version"],
                        capture_output=True, text=True, check=False)
    return {"python": platform.python_version(), "unicode": unicodedata.unidata_version,
            "harfbuzz": uharfbuzz.version_string(), "packages": dict(sorted(versions.items())),
            "fontforge": (ff.stdout + ff.stderr).strip()}


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@contextmanager
def atomic_output(path):
    """Build beside the destination; keep the previous artifact on failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{path.stem}-", dir=path.parent) as directory:
        temporary = Path(directory) / path.name
        yield temporary
        os.replace(temporary, path)


def publish_files(outputs):
    """Prepare all replacements before writing; roll back a failed publication."""
    originals = {p: p.read_bytes() if p.exists() else None for p in outputs}
    published = []
    try:
        with ExitStack() as stack:
            prepared = {}
            for path, data in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                directory = stack.enter_context(tempfile.TemporaryDirectory(prefix=".publish-", dir=path.parent))
                temporary = Path(directory) / path.name
                temporary.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
                prepared[path] = temporary
            for path, temporary in prepared.items():
                os.replace(temporary, path)
                published.append(path)
    except BaseException:
        for path in reversed(published):
            if originals[path] is None:
                path.unlink()
            else:
                with atomic_output(path) as temporary:
                    temporary.write_bytes(originals[path])
        raise


@contextmanager
def file_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield
