"""`--out`: a generator's whole run into a scratch UFO (T2, docs/claude/only.md).

    make_bold.py   [SOURCE.ufo] [TARGET.ufo] --out build/only/MyiaDidot-Bold.ufo
    make_italic.py [REGULAR.ufo] [ITALIC.ufo] --out build/only/MyiaDidot-Italic.ufo

TARGET is copied to --out and the generator runs on the copy as on TARGET
(the glyphs kept as drawn, the acceptances and the Italic's `previous` read
from it), exactly as check_reproducible.reproduce runs on its copies. TARGET
and everything under sources/ stay untouched: an --out there is refused
before a file is opened, and the small-cap drafts store is only read
(fontforge_inputs.READ_ONLY: a draft it lacks ends the run).
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def refused(out):
    """why --out may not be written, or None"""
    out = Path(out).resolve()
    if out == SOURCES or SOURCES in out.parents:
        return f"--out {out} is under sources/: a scratch run never writes there"
    if out.suffix != ".ufo":
        return f"--out {out}: not a .ufo"
    return None


def prepare(target, out):
    """TARGET copied to OUT (the old OUT removed first); the drafts store
    made read-only for this process; OUT's path returned for the run"""
    if why := refused(out):
        raise SystemExit(why)
    import fontforge_inputs

    fontforge_inputs.READ_ONLY = True
    out = Path(out).resolve()
    if out == Path(target).resolve():
        raise SystemExit("--out is TARGET itself")
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(target, out)
    return out
