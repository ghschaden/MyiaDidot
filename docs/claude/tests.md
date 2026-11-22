# Tests are the safety net

Moved from CLAUDE.md (its ground rules apply).

- `make test` runs on every commit via the pre-commit hook
  (`make setup` installs it) and in GitHub Actions. With `make reproduce`, allow several minutes for validation. Tests run
  against the exact staged tree in a private workspace.
  The checks run detached, once per state of the tree: if a commit times
  out anyway, run the same commit again; it waits for the run in progress
  or takes its result (a failure too, without rerunning; `MYIA_RECHECK=1`
  forces a new run). Results and logs: `.git/myia-checks/`.
- The hook's `make reproduce` makes again only the styles without a
  proof (`scripts/stale.py unproven`, `check_reproducible.py STYLE ...`;
  none: skipped), 2026-11-21. A style has one when a plain `make generate`
  made it and nothing it read or wrote has changed since: each style's proof in
  `build/stale/stamp.json` is a digest of its inputs (its source UFO, all
  of scripts/, Makefile, pyproject.toml, uv.lock, .python-version, the
  toolchain with FontForge) and of the UFO it wrote (accepted.py's review
  marks left out). No proof after `KEEP_DRAFTS` or a `MYIA_*` switch that
  is not one that only steers; after `STYLES=` the styles not made keep
  their proofs, which hold while scripts/ and their source are unchanged
  (a hand fix in the Italic: the Bold Italic alone is made again; a
  generator change: all three). Given up: the check that two runs
  agree (the designer's decision, 2026-11-21). `FULL_REPRODUCE=1 git
  commit ...` runs `make reproduce` regardless.
- After a change to the Regular, `make check-regular` first (a minute or
  two): its generated parts made again (scripts/regular_steps.py: the
  STEPS of tests/test_generated_current.py, then nfd_compose.py) and the
  tests but the generated styles' own. Only then `make generate`, and
  after reviewing the baselines commit: the hook runs `make test` and
  `make reproduce` on the staged tree, so they need not be run by hand
  as well (2026-11-14: a batch took six 25-minute rounds, five of them
  failing on what the Regular alone showed).
- The hook runs pytest without `-x`: a failing commit lists every
  failure, so one round of baselines takes them all. A commit whose tree
  differs from one the hook already checked (same HEAD, same toolchain)
  only under `tests/data/` runs just the tests that failed there and the
  modules naming a changed data file (`tools/git-hooks/rerun_plan.py`,
  T11, 2026-11-22; tests/test_rerun_plan.py); a data file no module
  names, or `MYIA_RECHECK=1`, runs everything.
- The proof that lets the hook skip `make reproduce` (`stale.py
  unproven`) reads a style's source as `ufo_digest` does, without the
  acceptances `accepted.py` writes after a run: accepting the Italic's
  glyphs no longer unproves the Bold Italic made from them (2026-11-22;
  it had cost every such commit a Bold Italic reproduce). It does read
  `tests/data/nfd-exceptions.txt`, the one data file the generators
  read.
- The post-commit hook rebuilds the proofs (`make proof`) in the
  background after commits touching sources, scripts or proofs/: the
  commit built is in `build/proofs/built-from`, the output in
  `build/proofs/refresh.log`. Look there before building proofs by hand.
- What they hold: UFO integrity, composites in sync with anchors, NFC and NFD
  rendering the same ink (with precomposed glyphs removed from cmap so
  HarfBuzz cannot recompose), coverage ratchet, golden shaping corpus
  (`tests/data/shaping-corpus.txt`: real text in 56 languages, every
  feature alone and combined; tests/test_corpus.py wants a case for each
  feature and language system the fonts have), a digest over more than 2M shaped strings per style,
  fontbakery with an allowlist, and outlines gone wrong
  (`scripts/glyph_lint.py`: specks, twists, pinholes, slivers, notches,
  steps, ledges) and design quality (`scripts/quality/checks.py`: smooth
  nodes, kinks, extremes, steps on the outline (a short straight jog
  between edges running on the same way: a tail or hook set beside its
  stroke, which the raster lint misses), wobbles (the Bold and Bold
  Italic: a curve bending back for a short stretch more often than in
  its source glyph), whole units, alignment zones, stem weights, the
  italic's slant, accent gaps, the Bold's widths, and derived letters
  against their recipe's base, `scripts/quality/derived.py`: base kept,
  stem, whole advance, an italic one made from the roman (`--json` for
  other tools: measures, findings, outline hashes); glyphs darker or
  lighter than their kind, `scripts/quality/strokes.py`: each main stroke
  against n/o, H/O, h.sc/o.sc, ±10 %; `quality*.txt`, regenerate
  with `update_test_data.py --quality`) against each style's known findings (`glyph-lint*.txt`; regenerate
  with `update_test_data.py --lint`). derive.py, make_italic.py and
  make_bold.py clean specks, twists, pinholes, steps and ledges from what they
  make; `glyph_lint.py UFO --fix` does it for drawn glyphs.
- Letters and figures meeting the signs beside them
  (`tests/test_collisions.py`, `scripts/quality/collisions.py`): every
  pair with less than kern_clear.CLEAR of white across, kerned or not,
  against `collisions*.txt` ("left right white  # date reason"); a new
  pair fails, a fixed one fails until its line is deleted, one more than
  4 units worse fails. A line is added by hand with a dated reason.
  In the same file, the guard's result (kern_clear.guard, measured as it
  measures): `test_guard_keys_kept` (a group pair the source style kerns
  with a guarded member stays a key, or the members keep GUARD) and
  `test_guard_white_held` (every guarded letter keeps GUARD in the pairs
  the guard walks; no list, no tolerance).
- Exception lists in `tests/data/*.txt` only shrink: a test fails when an
  entry is no longer needed. Fixing an entry = deleting its line.
- A small cap drawn to its capital's distinctive stroke profile may carry
  `org.myiadidot.caseReference` (currently ɣ.sc → Ɣ in the two italics).
  The reference must be its actual Unicode capital. Stroke diagnostics
  compare the capital/H proportion at small-cap weight; zone diagnostics
  inherit the capital's relative overshoot. The tag records construction,
  not a diagnostic exemption: wrong weights/heights still fail, as held by
  `tests/test_case_reference.py`.
- When a test fails: find the cause first (`make regress` diffs shaping
  against HEAD; `scripts/nfd_debug.py UFO CHARS` shows NFC vs NFD). Only for
  an intended change, regenerate baselines with
  `scripts/update_test_data.py` (review the complete JSON report and
  pass its SHA-256 to `--accept-report`; the plugin may ask for approval) and
  say in the commit what changed and why.
- Never commit with `--no-verify` unless explicitly asked to.

