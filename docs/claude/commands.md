# Handy commands and the Claude Code plugin

Moved from CLAUDE.md (its ground rules apply).

| | |
|---|---|
| `make` | OTF, hinted TTF, WOFF2 into `fonts/` |
| `make test` / `make regress` | test suite / shaping diff vs `REF=HEAD` |
| `make lint` | ruff, lint only (no formatter: the recipe tables are aligned by hand); pre-commit and CI run it |
| `make generate [STYLES=auto]` | regenerate Italic, Bold, Bold Italic from the Regular (only the styles a change reaches with `STYLES=auto`, below) (then normalize, check for sync conflicts); the Bold Italic's stroking is cached (`scripts/stroke_cache.py`; `MYIA_STROKE_CACHE=0` for a run without) |
| `make reproduce` | do the generated styles come out of their generators as the current UFOs specify? |
| `make only STYLE=BoldItalic GLYPHS="n m" [SOURCE=UFO]` | a generated style made again whole into `build/only/MyiaDidot-STYLE.ufo` (`make_bold.py`/`make_italic.py --out UFO`; `sources/` untouched, an `--out` there refused), then the sheet `build/only/STYLE-n.pdf`: source style \| committed \| new, node views, 144 pt, words (`scripts/only_sheet.py`, `docs/claude/only.md`) |
| `make strokes` | `build/quality/strokes-STYLE.pdf`: glyphs darker or lighter than their kind, each between its references, for review |
| `make proof` | `build/proofs/`: `charset.pdf` (new glyphs in red), `proof.pdf`, `samples.pdf` (running text, many languages, sizes), `textpages.pdf` (full book pages, mixed styles), `smallcaps.pdf`, `smallcaps-review.pdf` (every small cap over guide lines, drafts not yet accepted first), `drafts-review.pdf` (other drafted letters not yet accepted, by kind); the same two as `-Italic`, `-Bold`, `-BoldItalic` |
| `make visual` | `build/visual/report/index.html`: ~130 fixed specimens (golden corpus, feature samples, running text) per style rendered in the working tree and in `VISUAL_REF` (default: tag `proofs-approved`, else HEAD), changed ones as before / after / overlay; `make visual-approve` moves the tag to HEAD; `make diffenator`: diffenator2 on TTFs against the same revision, summary in `build/visual/diffenator-summary.txt`. CI runs `make visual` against the previous commit |
| `make udhr` | `build/proofs/udhr-quarto.pdf`: one quarto page per language (the UDHR; `scripts/udhr_book.py`, texts fetched once into `build/udhr/`) |
| `make qa` | full fontbakery reports in `build/qa/` |
| `make quality` | design quality against reference fonts (`scripts/quality/`, references fetched into `build/refs/`): colour, spacing, pairs, alignment, construction, transitions, accents, slant, small sizes, into `build/quality/` |
| `python scripts/coverage.py fonts/otf/MyiaDidot-Regular.otf --list` | what is missing |
| `python scripts/status.py --long` | coverage per glyph set + last test run |
| `python scripts/composites.py UFO --check` | composites vs rules |
| `python scripts/glyph_lint.py UFO [GLYPH ...]` | outlines gone wrong: where, what |
| `python scripts/quality/pair_summary.py [STYLE ...]` | Latin, Greek, Cyrillic pairs outside the references, one table (built fonts) |
| `python scripts/redraw.py SRC.ufo OUT.ufo GLYPH ...` | a glyph redrawn onto extremes, corners and line ends, as a candidate with its gate verdict (`docs/claude/redraw.md`); `scripts/redraw_sheet.py` for the review sheet |
| `python scripts/redraw_sweep.py UFO [--rev REV]` | what moved in a style since a revision, in units: outline distance, advance, anchors, kerning, by kind (redrawn, composite, other); after a redraw's `make generate` |
| `python scripts/quality/stem_retreats.py UFO ...` | stems that step into the ink before their serif (`scripts/stem_joins.py`; none allowed) |
| `python scripts/quality/bold_measures.py [--range] [--italic]` | phase 7 (F4): the Bold's gain over the Regular per letter and family (counter area, width and aperture, joins, balls, stem, widths) beside Old Standard's (`--range`: Bodoni Moda, Libre Bodoni too; `--italic`: the Bold Italic over the Italic), from the UFOs, into `build/quality/bold-measures*.md/.json`, about 1.5 min |
| `python scripts/italic_sheet.py [OUT.pdf]` | phase 6's sheet: the Italic against the Regular (`docs/claude/italic.md`): the table, a page per finding at up to 144 pt with the measured places drawn, running text, the change list; measures as italic_measures.py, about 30 s |
| `python scripts/quality/bold_targets.py [--italic]` | from bold_measures' JSON (`--range`, `--italic`): each measure on the font's own scale (over the stem, the zone) and where Myia's Regular and Bold lie against the references' range, per family, into `build/quality/bold-targets[-italic].md`; reading: `docs/claude/bold.md` |
| `python scripts/bowl_counters.py UFO [GLYPH ...] [--out OUT.ufo]` | the bowls' insides that are not two clean curves, and what redoing them moves; candidates to OUT.ufo |
| `make collisions` | `build/quality/collisions-STYLE.{txt,pdf}`: letters and figures meeting the signs beside them (`? ! ) ] „ ¡` superiors, case forms), kerned or not, worst first and by sign; `scripts/quality/collisions.py UFO` for one style, 3 s (`docs/claude/collisions.md`) |
| `python scripts/sync_check.py` | sync conflict copies and lost glyph files in the UFOs |

Run Python as `.venv/bin/python -I`. Run
`.venv/bin/python -I scripts/quality/fetch_refs.py` and
`.venv/bin/python -I scripts/reference_inputs.py --udhr` to provision
the pinned comparison inputs.

## Claude Code plugin

`tools/claude-plugin/myia-didot` (marketplace file at `.claude-plugin/`):
status line (with "OTF stale" when a UFO is newer than its built font),
guards (deny re-import and writes to `sources/upstream/`; ask before
rewriting baselines, `--no-verify`, force-push, and before writing into a
generated style by anything but its generator), a note on the output of
scripts that measure `fonts/otf/` while it is stale, a sync-leftover check
after commands that rewrite UFOs (toast, and again 30 s later), and
`/font-pairs` (`scripts/quality/pair_summary.py`: Latin, Greek and Cyrillic
pairs outside the references, all styles), `/font-status`,
`/font-test`, `/font-proof`. Its rules have tests: `claude plugin test
tools/claude-plugin/myia-didot`.

## What is stale before a regeneration (2026-11-20)

`.venv/bin/python -I scripts/stale.py` lists, in two seconds, the source
glyphs (Regular for the Italic and Bold, Italic for the Bold Italic) whose
fingerprint differs from the stamp the last `make generate` wrote
(`build/stale/stamp.json`), composites included, and the generator files that
changed. It answers what `make reproduce` finds in twenty minutes, not what a
run will make of it (drawn glyphs are kept as saved). Order of work after a
hand fix in a generated style: edit, `scripts/stale.py`, then one
`make generate`, then `make reproduce`; a fix applied after a generate leaves
what is built on it stale, and the list says so.

`make generate` begins with `stale.py guard`: the Regular must have been
through `make check-regular` as it now stands (that run is marked in
`build/stale/regular-checked.json`, failures or not); `SKIP_CHECK=1` waives it.
A source's kerning, groups and features are fingerprinted too (`@kerning`
`@groups` `@features`, 2026-11-21).

**Only the styles a change reaches (2026-11-21).** The stamp is kept per
style. `make generate STYLES=auto` makes only the styles `stale.py styles`
names: those whose source changed, or one of whose generator files did
(`stale.REACHES`: data_italic.py, make_italic.py, fontforge_inputs.py,
smallcaps_draft.py reach the Italic and Bold Italic, data_bold_italic.py the
Bold Italic alone; every other file all three), and the Bold Italic whenever
the Italic is made. `STYLES="Italic BoldItalic"` names them by hand; without
STYLES all three are made, as before. Only the styles made are stamped.
`REACHES` rests on make_bold.py reading data_italic's and data_bold_italic's
tables and importing from make_italic only behind its `italic` flag; a new
use outside it means the file reaches the Bold as well (take it out of
`REACHES`). The generator files are GENERATOR_GLOBS and every project
module make_italic, make_bold and smallcaps import at any depth
(stroke_cache.modules). Tests: tests/test_stale.py. `make reproduce` stays
whole; the commit's hook may take a plain full run's proof instead
(docs/claude/tests.md).

`.venv/bin/python -I scripts/make_bold.py sources/MyiaDidot-Regular.ufo sources/MyiaDidot-Bold.ufo --only a b`
makes those glyphs and what is built from them (the Bold only; the Bold Italic's is not
exact yet) into `build/only/MyiaDidot-Bold.ufo` in seconds, and says what it did not show.
`scripts/only.py Bold a` prints the closure alone. docs/claude/only.md, last section.
