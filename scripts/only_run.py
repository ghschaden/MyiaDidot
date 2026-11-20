"""`--only` in a generator's main: the shared parts (docs/claude/only.md, "The run").

    ctx = only_run.begin(source_path, target_path, out, asked)   # after parsing the arguments
    ... ctx.work is where the generator writes (a copy of TARGET), instead of TARGET
    ctx.cut(font)       # the working font, cut to N, right after it is opened from SOURCE
    ctx.finish()        # after the write: D composed into --out, the equivalence check

TARGET is never written: the generator runs on a copy of it (`ctx.work`), so
the glyphs kept as drawn, the acceptances and the Italic's `previous` are read
as in a whole run. `--out` is a copy of TARGET in which the glyphs of D (the
asked glyphs and everything built from them) are those of the work font.
Everything else of the font's own (kerning, groups, features, glyph order, info,
lib) stays TARGET's: what a partial run does not show is printed first.

The check every run makes: the work font's glyphs of N outside D are compared
with TARGET's. Nothing asked for is read by them, so they must come out as
committed; if one does not, `finish` lists them, still writes --out, and
returns 2 (the sources are not as generated, or the graph lacks an edge, or a
pass looks at glyphs it is not told to).
"""

import os
import shutil
import sys
from pathlib import Path

import ufoLib2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

NOT_SHOWN = ("pairs kern_clear would loosen or let go, kerning scaled or made by smallcaps.scale_kerning, "
             "the smcp/c2sc block, WHOLE_KEY and CUT_KEY, win metrics")


class Context:
    def __init__(self, source, target, out, D, N, work, italic):
        self.source, self.target, self.out = Path(source), Path(target), Path(out)
        self.D, self.N, self.work, self.italic = D, N, Path(work), italic
        self.skipped = []  # passes that named a glyph the run does not hold (finalization.SKIPPED)

    def step(self, label, function, *args):
        """function(*args), a whole-font pass of the Italic's: under --only one
        that names a glyph the run does not hold is skipped and recorded."""
        try:
            return function(*args)
        except KeyError as missing:
            self.skipped.append(f"{label}: {missing.args[0]}")

    def cut(self, font):
        """Every glyph outside N deleted from the working font."""
        for name in [g.name for g in font if g.name not in self.N]:
            del font[name]

    def finish(self):
        import subprocess

        from check_reproducible import differences

        # as after a whole run (make generate): smallcaps.py on what was written
        done = subprocess.run([sys.executable, "-I", str(HERE / "smallcaps.py"), str(self.work), "--glyphs-only"],
                              capture_output=True, text=True, check=False)
        if done.returncode:
            print(f"only: smallcaps.py on the work font failed ({done.stderr.strip().splitlines()[-1:]}); "
                  "its glyphs are as the generator left them")
        work = ufoLib2.Font.open(self.work)
        target = ufoLib2.Font.open(self.target)
        # the check: the glyphs of N outside D, as committed
        outside = sorted(n for n in self.N - self.D if n in target)
        lines = [ln for ln in differences(_subset(work, outside), _subset(target, outside))
                 if ln.startswith("glyph ")]
        # the result: TARGET with the glyphs of D from the work font
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.target, self.out)
        result = ufoLib2.Font.open(self.out)
        for name in sorted(self.D):
            if name in work:
                result.layers.defaultLayer.insertGlyph(work[name].copy(), name, overwrite=True)
        result.save(self.out, overwrite=True)
        shutil.rmtree(self.work.parent, ignore_errors=True)
        print(f"only: {len(self.D)} glyphs made again in {self.out}")
        print(f"only: not shown by a partial run: {NOT_SHOWN}")
        if self.skipped:
            print(f"only: {len(self.skipped)} finishing passes skipped, naming glyphs the run does not hold:")
            print("  " + "; ".join(self.skipped))
        if lines:
            print("only: outside the closure but changed:")
            for ln in lines:
                print("  " + ln)
            return 2
        print(f"only: the {len(outside)} glyphs read but not asked for come out as committed")
        return 0


def _subset(font, names):
    """A font of only these glyphs (outline, width, anchors, lib), for the comparison."""
    sub = ufoLib2.Font()
    for name in names:
        if name in font:
            sub.layers.defaultLayer.insertGlyph(font[name].copy(), name)
    return sub


def begin(source, target, out, asked):
    """The context for a run with --only, or SystemExit with why not."""
    import only
    import scratch_out

    if not out:
        out = ROOT / "build" / "only" / Path(target).name
    if why := scratch_out.refused(out):
        raise SystemExit(why)
    src_font = ufoLib2.Font.open(source)
    regular = src_font if "Italic" not in Path(source).name else ufoLib2.Font.open(ROOT / "sources" / "MyiaDidot-Regular.ufo")
    italic = bool(src_font.info.italicAngle) or "Italic" in Path(target).name
    try:
        D, N = only.closure(only.reads(src_font, regular, italic), src_font, asked)
    except only.OnlyError as e:
        raise SystemExit(f"only: {e}") from e
    # the generator runs on a copy of TARGET, read-only drafts as in --out
    # one work folder per process: two runs never share one (removed by finish)
    work = ROOT / "build" / "only" / "work" / str(os.getpid()) / Path(target).name
    scratch_out.prepare(target, work)
    print(f"only: {len(asked)} asked, {len(D) - len(asked)} built from them, {len(N)} read")
    return Context(source, target, out, D, N, work, italic)
