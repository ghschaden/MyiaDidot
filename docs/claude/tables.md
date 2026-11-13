# The generators' tables apart from their machinery (T5's specification)

Written 2026-11-13 (F6) from a reading of the code at 32a13088 (an AST
map of the three modules, every importer in `scripts/` and `tests/`,
and the `shape-grammar` branch's readers); nothing changed, nothing
run. For the session that carries it out (Opus). Line numbers are those
of 32a13088.

## What there is

| module | lines | module-level names | of which per-glyph tables | functions | imports inside functions |
|---|---|---|---|---|---|
| `derive.py` | 2,997 | 31 | 5 (`RECIPES` alone 648 lines) | 63 | 7 |
| `make_italic.py` | 2,962 | 69 | about 35 (`ITALIC_RECIPES` 381) | 63 | 57 (18 of them `import derive`, already imported at the top) |
| `make_bold.py` | 3,070 | 97 | about 50 (`ITALIC_BOLD_RECIPES` 327, `ITALIC_BOLD_REBUILD` 99, `ITALIC_BOLD_KERNING` 76) | 47 | 63 (8 `import derive`) |

The one real cycle: `make_italic` imports `make_bold` at the top
(`WHOLE_KEY, mark_like, redraw, write`, 57), so `make_bold` imports
`make_italic` only inside functions (`rederive` 2382-2554, `main`
2661-3036, `follow_bases` 2027, 2065). Of what it takes there, the data
are `WEIGHT`, `POINT_REPAIRS`, `ITALIC_JOINS`, `ITALIC_CORNERS`,
`ITALIC_RUNS`, `SC_LEVEL_GAIN`, `SC_DRAFT_SIDES`, `ITALIC_SIDEBEARINGS`;
the rest are functions (`round_corner`, `straighten_run`, `build_own`,
`level_gain`, `capital_width`, `uncrossed`, `recipe_scale`,
`serbian_bars`, `serbian_gje`) and `XH`, `shear` (italic_geometry's,
passed through). The other imports inside functions are habit, not
cycles (`import derive` where `derive` is already imported).

Who reads the tables from outside (to keep working, unchanged):

- `derive`: `RECIPES` (l_belt, make_bold, make_italic, quality/derived,
  quality/derived_spacing, smallcap_review, tests/test_recipes),
  `SPACING` (kern_clear, make_bold, make_italic, derived_spacing),
  `NARROW` (quality/derived), `ENLARGE_LIKE` (make_italic), `BIG` (12
  scripts), `ZONE_BOTTOMS`/`ZONE_TOPS` (stroke_bold), `STROKE_KEY`,
  `DRAFT_KEY`.
- `make_italic`: `ITALIC_RECIPES` (derive's comments, quality/derived,
  r_hook), `ITALIC_SC_RECIPES` (quality/derived), `ITALIC_SIDEBEARINGS`
  (make_bold, tests/test_j_hook), and make_bold's list above.
- `make_bold`: `WHOLE_KEY` (make_italic, update_test_data, two tests),
  `ITALIC_BOLD_RECIPES` (make_italic), `ITALIC_BOLD_ROOTS`,
  `ITALIC_BOLD_SPLIT` (stroke_bold, comments only), `BOLD_KERNING`
  (italic_kerning_sheet), `LINING_FIGURES`, `SMALL_SUFFIXES`
  (kern_clear), `ITALIC_BOLD_REBUILD`, `ITALIC_BOLD_REBUILD_OPS`,
  `ITALIC_BOLD_KNEES`, `ITALIC_LOOSER`, `BOLD_CUT`, `BOLD_ITALIC_CUT`,
  `SLANT` (tests).
- `scripts/pilot/` (`import make_bold as mb`): reads `mb.KX`, `mb.AY`,
  `mb.ITALIC_AX`, `mb.ITALIC_THIN`, `mb.ITALIC_THICK`, `mb.PART_GAP`;
  **assigns** `mb.KX` and `mb.part_serifs` (bold_trial.py 199-201).
- The `shape-grammar` branch (Codex, not merged): reads `make_bold.AX`,
  `AY`, `KX`, `THIN`, `THICK`, `ITALIC_AX`, `BOLD_FIT_AS_IS`. It edits
  none of the three files, so the moves cannot conflict with it in a
  merge; its readers must find the names where they are now.

Names rebound at run time, which therefore must be read through the
generator and never through a data module: make_bold.main's `global
SLANT, AX, THIN, THICK` (2589-2603: the Bold Italic's values set over
the Bold's), the pilots' `mb.KX`, and the cache `FAULTS` (filled by
`faults`, 1561). Nothing else is assigned or mutated after import (no
`.update`/`.add` on a table at module level or in a function; checked
by grep at 32a13088; the session checks again).

## The decision

1. **Four data modules, flat in `scripts/` as the project's modules
   are**: `data_regular.py` (derive's, which every style takes unless
   it replaces an entry), `data_italic.py` (make_italic's),
   `data_bold.py` and `data_bold_italic.py` (make_bold's, by the style
   each table serves; what both styles read goes in `data_bold.py`, and
   `data_bold_italic.py` imports what it builds on, e.g. `ITALIC_OVALS =
   OVALS | ...`, `BOLD_ITALIC_CUT` from `BOLD_CUT`).
2. **What moves**, by kind, not one by one:
   - every table keyed by glyph name or character (dict, set, recipe
     list), with the comment block above it and the comments inside it;
   - the style's numbers that tables are written in or that say the
     style's weight and fit: make_bold's `KX AX AY ITALIC_AX THIN THICK
     ITALIC_THIN ITALIC_THICK ITALIC_HAIR MARK_AX MARK_AY BOLD_CUT
     BOLD_CUT_GREEK BOLD_ITALIC_CUT_GREEK ITALIC_LOOSER BOLD_ITALIC_CUT
     BOLD_FIGURE_CUT`, make_italic's `KX AX AY WEIGHT CAP_WEIGHT
     TUNED_AX TUNED_AY ITALIC_CUT ITALIC_CUT_GREEK MADE_WITH` (needed:
     `ITALIC_BOLD_RECIPES` is written with `56 + AY`, `MADE_WITH` with
     the weights, and a data module may not import its generator);
   - the constants and pure constructors the entries are written with:
     derive's `BIG F_TOP F_HOOK J_TAIL`, make_italic's `ZH_DX`,
     `retroflex`, `descender` (they return tuples, read nothing),
     make_bold's `CURL_CAP CURL_ARM CURL_LOW`.
3. **What stays with the machinery**: lib keys (`*_KEY`, `WHOLE_KEY`,
   `SOURCE_KEY`), paths and environment (`ROOT`, `JOBS`,
   `STROKE_OUT_LOG`, `STROKE_OUT_MIN`), an operation's own parameters
   not keyed by glyph (derive's `BARS BAR_Y SLASH TAIL TAIL_Y HOOK_*
   SMOOTH_TURN MIDTILDE_TAPER BALL_OF_* ZONE_*`, make_bold's `PART_*
   GAP_* MOVED_EXACT MIN_PIECE SPECK ITALIC_BOLD_FF_APART FF_LIGATURES
   FF_STRETCH`, make_italic's `ITALIC_W_* DHOOK_CUT SRB_TE_BAR
   SC_STROKE_* OVERSHOOT_NEAR ZHE_SHIFT OS_XH OS_CAP`), dispatch tables
   holding functions (derive's `SHAPES`), caches (`FAULTS`), facts of
   the glyph set (`FIGURES FIGURE_NAMES LINING_FIGURES SMALL_SUFFIXES
   KEEP_ANCHORS ASCII_VARIANTS TRANSPLANT_OPS`), and make_bold's
   `SLANT`.
   Where the session is unsure of an entry, the rule decides: keyed by
   glyph → data; otherwise it stays. Any entry so decided is named in
   the commit message.
4. **A move only.** No name renamed (make_italic's and make_bold's
   `ITALIC_SIDEBEARINGS` and `ANCHOR_NUDGE` keep their names, apart in
   their modules), no value or order changed, no comment rewritten
   except a pointer where a comment block described a table and the
   function beside it (the text goes with the table; the function gets
   `# (data_bold.NAME)`). Renaming is not T5's.
5. **A data module imports only data**: other `data_*` modules,
   `italic_geometry` (make_italic's `ANCHOR_NUDGE` uses `SLANT`) and
   the standard library. No numpy (smallcaps.py's note: `arithmetic`
   must load before numpy), no generator, no `derive`. A test holds
   it (step 4).
6. **The generators re-export.** Each generator imports from its data
   modules, explicitly, every name it uses and every name read as
   `GENERATOR.NAME` elsewhere (the lists above, the pilots and
   shape-grammar's): `make_bold.KX` and the rest go on working, and
   the pilots' `mb.KX = ...` still reaches make_bold's functions, which
   read their own module's global. The re-exported but unused ones on
   one import with `# noqa: F401  (read as make_bold.NAME elsewhere)`;
   ruff selects F. The re-exports stay after T5 (shape-grammar and the
   pilots), until the designer merges or retires them.
7. **The two functions in a table.** `BOLD_RECIPES`' ɾ and ɮ (319,
   323) hold `lambda up: fishhook_band(up)` and `lambda up:
   lezh_band(up)`, machinery that reads the Bold's glyphs. In
   `data_bold.py` they become the strings `"fishhook_band"` and
   `"lezh_band"`; rederive (2433-2435) resolves them:
   `if isinstance(band, str):  band = {"fishhook_band": fishhook_band,
   "lezh_band": lezh_band}[band](up)` in place of the `callable` test.
   Both glyphs are made by this path in today's Bold (neither is marked
   drawn), so `make reproduce` covers the change. The one code change
   of the moves, named in the commit.

## The order, one commit each

Preconditions, before commit 1: on `main`, clean; `make reproduce`
exits 0 and `make test` passes at the starting commit (font-runner; a
reproduction that already differs proves nothing about a move); the
stroke cache warm. T6 (`docs/claude/drawn.md`) is done first if it is
still open: it cites make_italic and make_bold by line, which these
moves shift by hundreds.

1. **make_bold → `data_bold.py`, `data_bold_italic.py`.** First,
   because phase 3's open item re-proofs `ITALIC_BOLD_KERNING` and
   phase 7 works in `BOLD_RECIPES`, `BOLD_KEEP_WHOLE`, `BOLD_REBUILD`.
   About 950 lines with their comments. make_bold's local imports of
   make_italic stay as they are here (data_italic does not exist yet).
2. **make_italic → `data_italic.py`.** About 650 lines. make_bold's
   imports of make_italic's data stay as they are here too.
3. **derive → `data_regular.py`.** About 700 lines. Last: `stroke_bold`
   imports `derive`, so the stroke cache (keyed on the source of every
   module stroke_bold imports, at any depth) starts cold and this
   commit's `make reproduce` takes the whole 9 to 11 minutes; no phase
   waits on it. TODO's bowls item (the brackets lost in
   `derive.embolden`, "worth doing when T5 takes derive.py apart")
   comes after, as its own change: it changes outlines.
4. **The imports and the pointers.** make_bold's function-local imports
   of make_italic's data become top-level imports of `data_italic`
   (`XH`, `shear` from `italic_geometry`); the redundant local `import
   derive`s go; the other in-repo readers of moved tables may import
   from the data module (quality/derived, kern_clear, r_hook, l_belt),
   except for the rebound names (`AX THIN THICK SLANT KX`), which are
   read through make_bold. The 41 citations in `scripts/` and `tests/`
   (code and comments) that cite `make_bold.TABLE`, `make_italic.TABLE`, `derive.TABLE`
   point to the data module; so do `docs/claude/` (glyphs, styles,
   bold, stroking, spacing, redraw, only: 54 lines naming a table),
   CLAUDE.md's ground rule ("through the Regular or their generators
   (a recipe, a constant)" names the data modules) and its table (a
   row for this page). Dated review documents in `docs/*.md` are
   history: left as written. `tests/test_data_modules.py`: each
   `scripts/data_*.py` parsed with `ast`, its imports only `data_*`,
   `italic_geometry` and the standard library (decision 5), and no
   function in it reads a name outside its own arguments but for
   `math` (decision 2's constructors).

What remains after T5, not T5's: the cycle of functions between the
generators (make_italic's top-level import of make_bold's `mark_like`,
`redraw`, `write`, `WHOLE_KEY`; make_bold's local imports of
make_italic's nine functions). Its cure is a module of what both
generators use, a machinery move with its own proof; written into
TODO.md as a later item, not done in passing.

## The proof that nothing changed

For commits 1-3, three checks, the first two in a scratch script (not
committed; its output's last line in the commit message), the third
the project's:

**a. Every line moved, none lost.** The lines removed from the
generator, as a multiset, all reappear in its data modules; the lines
the data modules add beyond them are only their docstring, imports and
blank lines; the lines the generator adds are only its imports and the
pointers of decision 4.

```bash
git diff -U0 HEAD -- scripts/make_bold.py | grep '^-[^-]' | cut -c2- | sort > removed
cat scripts/data_bold.py scripts/data_bold_italic.py | sort > added
comm -23 removed added      # must be empty
comm -13 removed added      # only docstring, imports, blank lines
git diff -U0 HEAD -- scripts/make_bold.py | grep '^+[^+]'   # only imports, pointers, decision 7
```

**b. Every value equal.** The generator's module namespace at the
previous commit against the union of its namespace and its data
modules' now: each name of then present, with an equal value, in the
same order for dicts and lists; callables compared by module and
qualified name (the two lambdas of decision 7 are the exception,
named). Each side imported in its own `.venv/bin/python -I` process,
the old one from `git archive PREV scripts | tar -x -C $TMP` with its
`sys.path` set to that tree (if an import reads `sources/`, a symlink
to the working copy's, read only):

```python
import importlib, json, sys, types
sys.path.insert(0, sys.argv[1])
mods = [importlib.import_module(m) for m in sys.argv[2:]]
def canon(v):
    if isinstance(v, dict): return ["dict", [[canon(k), canon(x)] for k, x in v.items()]]
    if isinstance(v, (set, frozenset)): return ["set", sorted(map(repr, v))]
    if isinstance(v, (list, tuple)): return [type(v).__name__, [canon(x) for x in v]]
    if callable(v): return f"<{getattr(v, '__module__', '?')}.{getattr(v, '__qualname__', '?')}>"
    return repr(v)
out = {}
for m in mods:
    for k, v in vars(m).items():
        if k.startswith("__") or isinstance(v, types.ModuleType): continue
        if callable(v) and getattr(v, "__module__", None) == m.__name__: continue  # its own functions
        out.setdefault(k, canon(v))
print(json.dumps(out, sort_keys=True))
```

Old: `make_bold`; new: `make_bold data_bold data_bold_italic`. The
moved constructors (`retroflex`, `descender`) change their module and
are compared by name; their values are in the recipes, compared whole.

**c. The generators make the same fonts.** `make reproduce` exits 0
(font-runner), and the commit's own hook (`make test`, which also runs
`tests/test_generated_current.py`: derive on a copy of the Regular,
the check that matters for commit 3, since derive keeps the Regular's
existing glyphs and `make reproduce` does not run it). `scripts/sync_check.py`
after each run, as after any generation.

Commit 4 is proven by b (the generators' namespaces as before) and c,
and by ruff (the imports sorted, nothing unused but the noqa'd
re-exports).

## What the session does not do

- Rename, reorder, regroup or reformat a table (the aligned columns are
  kept by hand; no formatter: pyproject's note).
- Repoint a reader of `AX THIN THICK SLANT KX` to a data module.
- Touch `sources/`, a baseline or an exception list: if any check
  differs, the move is wrong, and the commit waits.
- Write in `~/src/MyiaDidot-shapes`.
