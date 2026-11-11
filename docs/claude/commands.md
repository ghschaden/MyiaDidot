# Handy commands and the Claude Code plugin

Moved from CLAUDE.md (its ground rules apply).

| | |
|---|---|
| `make` | OTF, hinted TTF, WOFF2 into `fonts/` |
| `make test` / `make regress` | test suite / shaping diff vs `REF=HEAD` |
| `make lint` | ruff, lint only (no formatter: the recipe tables are aligned by hand); pre-commit and CI run it |
| `make generate` | regenerate Italic, Bold, Bold Italic from the Regular (then normalize, check for sync conflicts); the Bold Italic's stroking is cached (`scripts/stroke_cache.py`; `MYIA_STROKE_CACHE=0` for a run without) |
| `make reproduce` | do the generated styles come out of their generators as the current UFOs specify? |
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
| `python scripts/quality/bold_targets.py [--italic]` | from bold_measures' JSON (`--range`, `--italic`): each measure on the font's own scale (over the stem, the zone) and where Myia's Regular and Bold lie against the references' range, per family, into `build/quality/bold-targets[-italic].md`; reading: `docs/claude/bold.md` |
| `python scripts/bowl_counters.py UFO [GLYPH ...] [--out OUT.ufo]` | the bowls' insides that are not two clean curves, and what redoing them moves; candidates to OUT.ufo |
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
