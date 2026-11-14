# `--only`: a partial run of the generators (T2's specification)

Written 2026-11-11 (F6) from a reading of `make_bold.py`, `make_italic.py`,
`built_from.py`, `check_reproducible.py`, `ufo_io.py` and `stroke_cache.py`
at 3bc787ee. Nothing was run or timed for it. To be carried out as written;
where the code turns out otherwise, the tests of the last section decide,
not this page.

**Carried out 2026-11-13: step 0 and stage A** (`scripts/scratch_out.py`,
`scripts/only_sheet.py`, `make only`, tests/test_only.py); the timings and
the profile in TODO.md under T2. Stage B not built. Found in carrying out:
make_bold reads the Bold beside its SOURCE for the Bold Italic's kerning
(`italic_kerning`), so a trial Italic in scratch with no Bold beside it is
kerned against the committed Bold (said in the run's output); the drafts
store is made read-only by `fontforge_inputs.READ_ONLY`, set by `--out`
already in stage A, not only under `--only`.

## What it is for

One or a few glyphs of a generated style, made again after an edit to their
source or to their recipe, in a scratch UFO and on a sheet, without the
whole run and without touching `sources/`.

    make_bold.py   [SOURCE.ufo] [TARGET.ufo] --only GLYPH ... [--out UFO]
    make_italic.py [REGULAR.ufo] [ITALIC.ufo] --only GLYPH ... [--out UFO]
    make only STYLE=BoldItalic GLYPHS="n m"        # the run and its sheet

GLYPH is a glyph name or a single character. With `--only`, TARGET is read
and never written (the glyphs kept as drawn, the acceptances, the Italic's
`previous`); the result goes to `--out`, by default
`build/only/<TARGET's name>`. The Bold Italic of a trial Italic: SOURCE is
that Italic's scratch UFO, which is a whole font (see "Putting it
together").

## Step 0, before anything is built: is it needed?

T2's "5 min 40 s" for the Bold Italic is older than the stroke cache
(`stroke_cache.py`, keyed by outline, arguments and code: after an edit to
one letter only that letter and what is stroked from it miss). So first,
by font-runner, each generator timed once into a copy, as
`check_reproducible.reproduce` runs them, with the cache warm, and once
more after moving one node of `n` in a copy of the source:

| run | time, warm | time, one letter changed |
|---|---|---|
| make_italic (with its smallcaps.py) | | |
| make_bold Regular → Bold, smallcaps.py | | |
| make_bold Italic → Bold Italic, smallcaps.py | | |

- **Every run under about a minute:** stop at stage A below. It gives the
  scratch UFO and the sheet; there is no closure to keep right and the
  equivalence holds by construction.
- **Otherwise:** stage B, for the generators that are slow. Profile the
  slow one first (`cProfile`, by cumulative time, the top 15): if one whole-font pass holds most of it,
  say so in TODO.md before writing B; a cache for that pass may be the
  smaller change.

## Stage A: the whole run into scratch

`--out UFO` alone (no `--only`): TARGET is copied to `--out`
(`shutil.copytree`, the old one removed first), the generator runs with
`--out` in TARGET's place, exactly as `check_reproducible.reproduce` does
on its copies. `make only` then draws the sheet from it. No change to the
generators beyond the argument; `smallcaps.py` is run on `--out` by the
`make` target (make_italic runs it itself, line 2908, on the path it
wrote).

## Stage B: the closure

`org.myiadidot.builtFrom` is not enough by itself, and the page T2 names
it on should not be read so:

- only the Regular carries it (`make_bold.finalize` drops it from every
  generated style): 304 of the Regular's 2197 glyphs, none in the Italic;
- it records what `derive.py`'s recipes read, and `space_figures`' and
  `oldstyle_figures`' slashed zeros; not components (1236 composites),
  small caps, figures' sets, case forms, ligatures, or what a generator
  reads by name (`data_bold.SLASHED`: Ø from O, and Ø has no builtFrom).

So the graph is put together in a new `scripts/only.py`, from six
sources, as `reads(source, regular, generator) -> {glyph: set of glyphs}`
("to make this glyph the generator reads those"). **Too many edges cost
time; a missing edge costs a wrong preview.** Where in doubt, the edge is
added.

1. **Components** of the glyph in SOURCE (marks too).
2. **builtFrom** of the glyph of the same name in the Regular (also when
   SOURCE is the Italic: the recipes mostly coincide, and the surplus is
   harmless).
3. **Recipes:** for each `(ch, op, base, band)` of
   `derived.recipes(italic)` (make_bold: `follow_bases`,
   `attached_small`, `rederive`), and of `ITALIC_SC_RECIPES +
   data_regular.RECIPES` with `ITALIC_RECIPES`' replacements (data_italic; make_italic:
   `derive_stage`): glyph of `ch` reads glyph of `base`, resolved with
   `derive.resolve` as those functions do.
4. **Names:** `a_b` and `a_b.sfx` read `a` and `b`; `x.sfx` reads `x`
   where `x` exists (`.case .cap .tf .dnom .horn .zero .loclSRB
   .loclBGR .grek .i .iota ...`); `x.sc` reads the capital and the
   lowercase `smallcaps.smcp_map` pairs it with; each figure of a set
   (the defaults, `.tf`, `…oldstyle`, `…oldstyle.tf`, the `.zero` forms)
   reads all ten of its set and `zero` (`space_figures.space`,
   `tabular_figures`).
5. **Named in the code:** a table `EXTRA` in `only.py`, each line with the
   function that reads it. Known from this reading; to be completed by
   grepping `font["` and `regular["` in every function the two `main`s
   call:
   `data_bold.SLASHED` (name ← ring); `make_italic.redraw_w` (W ← V,
   w.sc ← v.sc); `swapped_sidebearings` (the pairs it returns: ɘ ← e);
   `serbian_gje`, `serbian_bars` (their `.loclSRB` glyphs ← и ш ī's bar
   as read there); `y_dot.y_dot_anchor` (y, dotbelowcomb);
   `t_dot_anchor`; `r_hook` (uni027A ← l; uni027D ← r);
   `italic_i.install` (I); `horn_stage`, `refit_horns`;
   `italic_ligatures.NAMES` ← their parts; `cyrillic_signs.redraw`;
   `ITALIC_LOCL`, `OS_LOCL`, `ROMAN_GLYPHS`.
6. **Measures** (`ROOTS`): glyphs every other glyph is measured against,
   always present in the run: `o` (`derive.strokes(…, "o")` scales every
   recipe in `rederive` and `derive_stage`), `n`, `H`, `l`, `bar`
   (`smallcaps_stage`, `_clickbar`), `zero`, `zerosuperior`
   (`small_glyphs`' scale), `f` (the hooks' top), and what
   `stack_anchors` and `finalization.PASSES` read by name.

From it:

- `D` = the glyphs asked for and every glyph that reads one, however far
  (the result of the run);
- `N` = `D`, everything `D` reads, however far, and `ROOTS` (what the run
  holds).

**A measure cannot be asked for.** If `D` meets `ROOTS` (asked for `o`, or
for something `o` is built from), the run ends: "o is a measure of the
whole style: use --out without --only". Likewise a glyph that is not in
TARGET yet, or a change that removes one: the glyph order, categories and
features change with it.

The first line printed: `only: 2 asked, 41 built from them, 96 read`.
A glyph asked for that TARGET keeps as drawn (`drawn.saved`, the Italic's
`reviewed`) comes out as saved; the run says so by name, since then only
what is built from it is new.

### The run

The generator's own `main`, with three changes, each behind
`if args.only`:

1. After the working font is opened from SOURCE: every glyph outside `N`
   deleted from it. `regular`, `previous` and Old Standard stay whole;
   they are only read.
2. The sets taken from the whole source and used to index the working
   font (`rule_made`, `kept`, `marks` where indexed, `small`) cut to `N`;
   a pass that names a glyph absent from `N` skips it (`if name in
   font`), at that pass, not by a catch-all.
3. `write` goes to `build/only/work/<TARGET's name>` (a copy of TARGET
   made first, so `saved`, `acceptances` and `previous` read what they
   read in a whole run); then `smallcaps.py` on that path, as after a
   whole run.

Nothing else differs: the same passes in the same order on fewer glyphs.
No pass is skipped for speed. One process unless `MYIA_JOBS` is given
(the four-core limit counts this run with whatever else is going).

### Putting it together

`--out` = a copy of TARGET in which the glyphs of `D` (outline, width,
anchors, unicodes, glyph lib) are replaced by the work font's. Everything
of the font's own stays TARGET's: kerning, groups, features, glyph order,
info, font lib.

**Not shown by a partial run**, and printed under its first line: pairs
`kern_clear` would loosen or let go, kerning scaled or made by
`smallcaps.scale_kerning`, the smcp/c2sc block, `WHOLE_KEY` and
`CUT_KEY`, win metrics. The sheet's words are set with TARGET's kerning.

### The check every run makes

The work font's glyphs of `N` outside `D` are compared with TARGET's
(`check_reproducible.differences`, the glyph lines). Nothing asked for is
read by them, so they must come out as committed. If one does not, the
run still writes `--out`, lists them ("outside the closure but changed:
…") and exits 2: either the sources are not as generated (`make
reproduce` says so too) or the graph lacks an edge, or a pass looks at
glyphs it is not told to. This is the equivalence test, on some hundred
glyphs, at every use.

## State

| | a run with `--out` or `--only` |
|---|---|
| reads | `sources/*.ufo`, `sources/oldstand`, `sources/drafts`, `tests/data/nfd-exceptions.txt` |
| writes | `--out`, `build/only/work/`, the stroke cache (keyed by content: the entry is the same whoever writes it) |
| never | anything under `sources/` or `tests/data`: `--out` resolving inside `sources/` is refused before a file is opened; `fontforge_inputs.drafts` asked for a draft the store lacks ends the run ("run make generate") where a whole run would call FontForge and write `sources/drafts`; no `make normalize` |
| locks | not the validation lock (nothing shared is written); `flock build/only/.lock`, so two runs do not share a work folder |

## The sheet

`scripts/only_sheet.py STYLE GLYPH ...`, called by `make only`:
`redraw_sheet.py` with `--col "source=SOURCE" --col "committed=TARGET"
--col "new=--out"`, node views, 144 pt, and `--words` at 12 pt chosen for
the glyphs asked (each between n and o, H and O, and in three words from
`proofs/`' word lists). PDF, to `build/only/<style>-<first glyph>.pdf`.
For a composite or a small cap asked for by its base, the sheet shows `D`
up to 24 glyphs, the asked ones first.

## Tests (`tests/test_only.py`)

`make reproduce` holds on every commit, so TARGET as committed *is* the
whole run's result: no test here runs a whole generator.

1. **The graph, every commit, no generator run.** Every edge's ends exist
   in SOURCE; `ROOTS` exist; asking for `o` is refused; `--out
   sources/x.ufo` is refused; fixed expectations: `D(b)` in the Regular
   holds `uni0253` (ɓ, builtFrom b and f), `D(e)` holds `uni0258` (ɘ),
   `D(a)` holds `aacute`, `D(O)` holds `Oslash`, `D(V)` for make_italic
   holds `W`, `D(zero)` is refused.
2. **Equivalence, every commit, one run per generated style** with the
   sample below asked for at once: no difference over all of `N`
   against TARGET, exit 0. If a run takes over a minute it moves to
   tier 3 and TODO.md's T8 gets the line.
3. **Singles** (`make only-check`; after any change to a generator's
   `main`, to `only.py`, and before a release): each sample glyph asked
   for alone, and 20 more drawn at random (the seed printed, the date by
   default). Only this tier finds a missing edge: asked together, one
   glyph's closure supplies what another's lacks.
4. **The test can fail:** with `EXTRA` emptied (monkeypatched), tier 3's
   `O` must report `Oslash`; with source 1 off, `a` must report
   `aacute`.
5. **Sources untouched:** `git status --porcelain sources tests/data`
   the same before and after tiers 2 and 3.

The sample, one glyph per way of being made (names as in the Regular;
replace one that turns out to sit in `ROOTS`' closure):

| glyph | what it exercises |
|---|---|
| `a` | a letter, its composites rebuilt from anchors, a.sc's accented forms |
| `b` | recipes: `follow_bases`, `rederive` (ɓ) |
| `O` | `SLASHED`, an oval refit |
| `V` | `redraw_w` in the Italic |
| `e` | `swapped_sidebearings` (ɘ) |
| `gravecomb` | a mark: every composite carrying it, stacks |
| `four` | figures: four.tf, fouroldstyle and its .tf, `space_figures` |
| `T` | small cap draft, `T_h`, Ť made from base and mark |
| `uni0433.loclSRB` | locl forms, the Serbian bars |
| `hyphen` | `case_forms` (hyphen.case), punctuation outside the letters' cut |
| one drawn glyph per style | kept as saved, and what is built from it |

## Order of carrying out

1. Step 0's table (font-runner), into TODO.md under T2.
2. Stage A, the sheet, `make only`; `--out` under `sources/` refused,
   with its test. Usable from here.
3. Only if step 0 says so: `only.py` with the graph and test tier 1 (no
   generator touched); the sizes of `D` and `N` for a-z and A-Z written
   to `build/only/closures.txt` and looked at: a letter whose `N` is
   half the font names an edge too coarse (source 4's figure sets, a
   mark) or a real hub.
4. `--only` in `make_bold.py`, with tiers 2 to 5 for Bold and Bold
   Italic; then `make_italic.py`.
5. `docs/claude/commands.md` gets the commands; this page, cut down to
   what was built, stays as the description.
