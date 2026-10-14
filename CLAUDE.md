# Myia Didot — working notes for Claude

Fork of Theano Didot (akryukov/theano) aiming at full Latin-script, Greek and
basic Cyrillic coverage in Regular/Italic/Bold/Bold Italic with real small
caps. Phases and the coverage target: README.md, FONTLOG.txt,
`scripts/coverage.py` (`TARGET`).

## Ground rules

- **`sources/*.ufo` is the master.** Never run `make reimport` or the import
  scripts (`sfd_export.py`, `postprocess_import.py`); they overwrite every
  edit since the import. `sources/upstream/` is the pinned upstream source:
  read-only reference.
- Change glyphs with scripts (ufoLib2) where possible; the person may edit the
  same UFO in FontForge or Fontra. After any UFO change: `make normalize`.
- Composites are generated: `scripts/composites.py` (anchor-driven, follows
  upstream's accent conventions). After moving an anchor, rerun the builder
  for the affected composites rather than hand-editing offsets. Upstream's
  deliberate special designs are in `SPECIAL` there.
- Accent conventions: spacing accents 880 wide centred at x=440; combining
  marks are those shifted −880; lowercase bases carry Top/Acute/Grave/
  Dotaccent (Acute/Grave = Top−20, Dotaccent = Top+20), Bottom/DotBelow,
  Cedilla; capitals carry TopCap and take `.cap` accents; stacking via
  TopMark/_TopMark, computed from ink (`--stack-anchors`).
- Win metrics must cover the bbox: `make winmetrics` after adding tall or
  deep glyphs (the fontbakery test flags it).

## Tests are the safety net

- `make test` (≈12 s) runs on every commit via the pre-commit hook
  (`make setup` installs it) and in GitHub Actions.
- What they hold: UFO integrity, composites in sync with anchors, NFC and NFD
  rendering the same ink (with precomposed glyphs removed from cmap so
  HarfBuzz cannot recompose), coverage ratchet, golden shaping corpus
  (`tests/data/shaping-corpus.txt`), a digest over ~1.2M shaped strings, and
  fontbakery with an allowlist.
- Exception lists in `tests/data/*.txt` only shrink: a test fails when an
  entry is no longer needed. Fixing an entry = deleting its line.
- When a test fails: find the cause first (`make regress` diffs shaping
  against HEAD; `scripts/nfd_debug.py UFO CHARS` shows NFC vs NFD). Only for
  an intended change, regenerate baselines with
  `scripts/update_test_data.py` (asks the person first via the plugin) and
  say in the commit what changed and why.
- Never commit with `--no-verify` unless the person asked for it.

## Handy commands

| | |
|---|---|
| `make` | OTF, hinted TTF, WOFF2 into `fonts/` |
| `make test` / `make regress` | test suite / shaping diff vs `REF=HEAD` |
| `make proof` | `build/proofs/charset.pdf` (new glyphs in red) + `proof.pdf` |
| `make qa` | full fontbakery reports in `build/qa/` |
| `python scripts/coverage.py fonts/otf/MyiaDidot-Regular.otf --list` | what is missing |
| `python scripts/status.py --long` | coverage per glyph set + last test run |
| `python scripts/composites.py UFO --check` | composites vs rules |

Run Python as `.venv/bin/python -I`.

## Claude Code plugin

`tools/claude-plugin/myia-didot` (marketplace file at `.claude-plugin/`):
status line, guards (deny re-import and writes to `sources/upstream/`; ask
before rewriting baselines, `--no-verify`, force-push), and `/font-status`,
`/font-test`, `/font-proof`. Its rules have tests: `claude plugin test
tools/claude-plugin/myia-didot`.
