"""`--out`: a generator's whole run into a scratch UFO (T2, docs/claude/only.md).

    make_bold.py   [SOURCE.ufo] [TARGET.ufo] --out build/only/MyiaDidot-Bold.ufo
    make_italic.py [REGULAR.ufo] [ITALIC.ufo] --out build/only/MyiaDidot-Italic.ufo

TARGET is copied to --out and the generator runs on the copy as on TARGET
(the glyphs kept as drawn, the acceptances and the Italic's `previous` read
from it), exactly as check_reproducible.reproduce runs on its copies. TARGET
and everything under sources/ stay untouched: an --out there is refused
before a file is opened, and the Italic's small caps are drafted into a copy
of the drafts store beside OUT (OUT-drafts.ufo, fontforge_inputs.redirect_drafts),
so a letter whose small caps are drafted from it (Ɓ Ɗ Ƥ, Ƈ Ɠ) can be made
again in a scratch run as well (2026-11-21; before, a draft to make ended
the run).
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


def drafts_for(out):
    """the scratch drafts store of a run into OUT"""
    out = Path(out).resolve()
    return out.with_name(out.stem + "-drafts.ufo")


def prepare(target, out):
    """TARGET copied to OUT (the old OUT removed first); this process's
    drafts store a copy beside it (drafts_for); OUT's path returned for the run"""
    if why := refused(out):
        raise SystemExit(why)
    import fontforge_inputs

    out = Path(out).resolve()
    fontforge_inputs.redirect_drafts(drafts_for(out))
    if out == Path(target).resolve():
        raise SystemExit("--out is TARGET itself")
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(target, out)
    return out
