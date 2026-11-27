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
already in stage A, not only under `--only`. (Since 2026-11-21 `--out`
drafts into a copy of the store beside OUT instead,
`fontforge_inputs.redirect_drafts`: a capital whose small cap is drafted
from it (Ƥ: ƥ.sc) can be tried with `--only` too; before, the run ended.)

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
- **One generator just over a minute and no pass holding most of it**
  (the case found 2026-11-13: the Bold Italic, spread over the slit
  check, smallcaps.py and the write): not stage B. Those passes read the
  whole font, and a glyph that many read (n, o) has most of the font in
  its closure, so B would keep them. What would shorten them is a cache
  per pass, keyed as the stroke cache is; each is its own item, taken
  only when the wait is felt. Decided so by the designer 2026-11-13
  (TODO.md, T2).

## Stage A: the whole run into scratch

`--out UFO` alone (no `--only`): TARGET is copied to `--out`
(`shutil.copytree`, the old one removed first), the generator runs with
`--out` in TARGET's place, exactly as `check_reproducible.reproduce` does
on its copies. `make only` then draws the sheet from it. `--out` also
sets `fontforge_inputs.READ_ONLY` (since 2026-11-21: points the drafts
store at a copy beside OUT, `scratch_out.drafts_for`): a whole run saves `sources/drafts`
when a draft is stale or held, not only a run under `--only`, so the
argument alone would have written under `sources/`. Otherwise no change
to the generators; `smallcaps.py` is run on `--out` by the
`make` target (make_italic runs it itself, line 2908, on the path it
wrote).

## Stage B: the closure

`org.myiadidot.builtFrom` is not enough by itself, and the page T2 names
it on should not be read so:

- only the Regular carries it (`style_write.finalize` drops it from every
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
| reads | `sources/*.ufo`, the Bold beside SOURCE for the Bold Italic's kerning (`italic_kerning`; the committed Bold where SOURCE is a scratch Italic with none beside it, said in the run's output), `sources/oldstand`, `sources/drafts`, `tests/data/nfd-exceptions.txt` |
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

## `generate(glyph)`: the common case of stage B (built 2026-11-20)

`scripts/only_glyph.py STYLE CHAR...` (Bold or BoldItalic) makes a recipe
glyph (attach, bar, curl, hook) again on the finished base of its style in
about a second, to `build/only_glyph/` with a sheet; `generate(style, ch,
recipe=...)` takes a recipe override. It does what `make_bold.rederive`
does for one letter. The recipes' numbers are in the frame rederive meets,
not the saved font's (later passes shift it), so one full run with
`MYIA_DUMP_FRAME=build/only_glyph/frame-BoldItalic.ufo` makes the
snapshot first. Checked: Ƈ Ɠ equal the saved outlines up to a translation
in x and 3 units (tests/test_only_glyph.py, skipped without the snapshot).
Since 2026-11-27 the frame is stamped (`make_bold.frame_stamp`: the source
UFO's digest, each generator file's hash) and `_frame` warns, naming what
changed, when it no longer holds; after a build `generate` runs
`make_bold.finish_recipe`, the same passes as rederive (fair joins, runs,
corners, specks, pinholes, fix, smooth_curves, side bearings): before
that it lacked smooth_curves and a trial disagreed with the run.
A band may be a callable, `band(up, source, name)` (`scripts/recipe_bands.py`).
Not every letter of the recipes runs through rederive (ƈ is stroked
elsewhere and differs): test a family before using it.

## Stage B: the graph built (2026-11-20)

`scripts/only.py` (`only.py STYLE GLYPH...`, `--closures`): `reads()`, `closure()`
and the refusals as written above, from sources 1-4 and 6, with `EXTRA`
(seven lines and `data_bold.SLASHED`) still to be completed by reading what
the two `main`s read by name. tests/test_only_graph.py is tier 1 (51 cases, no
generator run). Closure sizes for a-z A-Z (`build/only/closures.txt`): mean D
34, mean N 96 of 2345; O has the largest (D 143, N 365); refused: o n H l f in
each style. Not built: `--only` in `make_bold.py` and `make_italic.py` (cut the
working font to N, the sets taken from the whole source, the write into scratch,
the equivalence check), tiers 2-5, the sheet's join. Edit the generators only
when no `make generate` is running: its second `make_bold` call reads the file
later.

### The Bold's `--only` built, the Bold Italic's not yet exact (2026-11-20)

`make_bold.py REGULAR BOLD --only GLYPH... [--out UFO]` (shared parts in
`scripts/only_run.py`): BOLD is read, a copy of it in `build/only/work/<pid>/` is
what the run writes, the font is cut to N right after it is opened, and the result
is BOLD with the glyphs of D from the work font (default `--out
build/only/MyiaDidot-Bold.ufo`). Checked on a b O e T hyphen
uni0433.loclSRB: made in 5-14 s (the whole run is about 25 min with the Italics'),
D identical to the committed Bold and the N glyphs outside D too (tests/test_only.py,
tier 2, five runs). `zero` and `four` (its figure set reads zero) refuse.

What the generator needed, all behind `--only`, a whole run unchanged: a guard `if name
in font` at the passes that name glyphs (SLASHED, `r_hook.fair_bold_stem`,
`rederive`, `tabular_figures`, `separate_breve_grave_stacks`, the rule-made rebuild,
the side-bearing table), `finalization.SKIPPED` (a finishing pass that names a glyph
the run lacks is skipped and listed), `only_run.Context.step` for the Italic's own
whole-font passes, kern_clear and italic_kerning left out (the kerning stays the
target's), `smallcaps.py --glyphs-only` on the work font. In the graph (`only.py`):
every glyph reads the glyphs of its NFD (and a circumflex + tone pair glyph),
a mark reads its `.cap .i ...` variants, `PASS_GROUPS` (sc_feet; the f-ligatures: a
group meeting D is made again whole, one meeting N held whole), the root `I`.

Open: see the end of this page.

### The Bold Italic's `--only` exact (2026-11-20, later)

Six runs (hyphen a T m ь y) come out as committed, D and the glyphs read but not asked for
(tests/test_only.py, tier 2, `test_bold_italic_only_...`; `build/only/battery.log` has
b O e s i ú Ƈ ǥ ... by hand, 10-130 s each). What the first runs lacked:

- **Kept (drawn) glyphs outside the run were put back whole.** `drawn.restore` inserts every
  kept glyph, finished and already cut, into the work font; `respace` then cut m a second
  time (68 -> 44) and the passes that name it (smooth_joins' n m) ran on it. Under `--only`
  `kept` is cut to the glyphs the run holds (make_bold.main, after `only_ctx.cut`).
- **A finishing pass that names a glyph not held stopped half-way** (smooth_joins at ʊ, so
  n's join was never made; sc_feet at x.sc, so `brackets` never ran over i.sc). Now
  `finalization.absent(font, name)` (true only under `--only`) lets the pass go on without
  the glyph: smooth_joins, sc_feet, cyrillic_signs.redraw; italic_ligatures.make has each
  ligature in `with held():` (a KeyError or NameError of a ligature whose parts are not
  held leaves it out; a whole run still raises). The passes left to skip whole (y_dot_anchor,
  serbian_bars, cedilla, dollar, trademark, phi, oldstyle figures) name one glyph or a family
  each: asked for it, it is held and they run.
- **Edges the graph lacked:** `space` (a recipe's width; a ROOT now), `h.sc` and `o.sc` for every
  enlarged small cap (`make_bold.small_cap_stems`, `derive.enlarge`), `l.sc` for a recipe on a
  small cap (`derive.ball_for`), level_gain's h.sc, capital and H for s.sc and n.sc. O's closure
  grew by it (N 365 -> 590 of 2345: o.sc is every enlarged small cap's measure).
- A recipe that fails under `--only` (a glyph it reads is not held) is named in the skipped list
  ("rederive uni2C73.sc: KeyError 'l.sc'"); in a whole run it is left whole silently, as before.

### The Italic's `--only`, the sheet's join, tier 4 (2026-11-20, evening)

- `make_italic.py REGULAR ITALIC --only GLYPH... [--out UFO]`: as the Bold's, in `main`
  (the font cut to N after it is opened, `previous` and `kept` cut to what the run holds,
  `step(...)` around the passes that name glyphs: redraw_w, lighten_a, mirror_zhe, lean_as,
  round_shoulder, serbian_gje/bars, the dot anchors, redraw_cyrillic_signs, finish_contours,
  install_italic_i; the side-bearing tables and `stand_as` filtered to what is held; the
  kerning left out; `only_ctx.finish()` after `write`). Exact on hyphen a T m W ь y e
  (tests/test_only.py, `test_italic_only_...`). Edges added: t reads z (t_dot_anchor),
  `ITALIC_STANDS_AS`.
- `make only STYLE=Bold|BoldItalic GLYPHS="n m" PARTIAL=1` makes the glyphs with `--only`
  and draws the sheet from the result (all three styles).
- The 9-unit stacked-accent difference of ǜ.sc ḕ.sc (asked via gravecomb) is gone: with the
  kept glyphs no longer put back whole the Bold's gravecomb run is exact (a case of
  tier 2 now). `smallcaps.py --glyphs-only` no longer fails on `uni0307` (idotaccent.sc is
  made only where the mark is held).
- Tier 4, `test_the_equivalence_check_can_fail`: a glyph read but not asked for that
  comes out unlike the committed ends the run with 2 and lists it.
- Tier 5 (sources and tests/data untouched) is checked in each of the runs above.

Later the same evening: a battery of 30 asked glyphs in the Italic found three more groups of
missing edges, all in `only.py`: `serbian_gje` and `serbian_bars` read imacron, ḗ, macron,
ū's macron, и ш; `greek_cap_room` reads each capital's sample composite
(`GREEK_CAP_SAMPLES`); `Q_u` reads O, the long-s ligatures their f ligature. After them
hyphen a b O s i k z t T m W e Q ь т г Ƈ ǥ ú ǜ c x r p g ɸ $ Α come out exact in the Italic
(tests: the 13 of `test_italic_only_...`). Not tried in any style: figures (`zero` is a measure,
so a figure asked for is refused), the Greek and the less common Latin.
