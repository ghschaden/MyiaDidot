# Tests are the safety net

Moved from CLAUDE.md (its ground rules apply).

- `make test` (≈90 s) runs on every commit via the pre-commit hook
  (`make setup` installs it) and in GitHub Actions. With `make reproduce`
  a commit takes ≈2–3 min: give `git commit` a Bash timeout of 600000.
  The checks run detached, once per state of the tree: if a commit times
  out anyway, run the same commit again; it waits for the run in progress
  or takes its result (a failure too, without rerunning; `MYIA_RECHECK=1`
  forces a new run). Results and logs: `.git/myia-checks/`.
- The post-commit hook rebuilds the proofs (`make proof`) in the
  background after commits touching sources, scripts or proofs/: the
  commit built is in `build/proofs/built-from`, the output in
  `build/proofs/refresh.log`. Look there before building proofs by hand.
- What they hold: UFO integrity, composites in sync with anchors, NFC and NFD
  rendering the same ink (with precomposed glyphs removed from cmap so
  HarfBuzz cannot recompose), coverage ratchet, golden shaping corpus
  (`tests/data/shaping-corpus.txt`: real text in 56 languages, every
  feature alone and combined; tests/test_corpus.py wants a case for each
  feature and language system the fonts have), a digest over ~1.2M shaped strings,
  fontbakery with an allowlist, and outlines gone wrong
  (`scripts/glyph_lint.py`: specks, twists, pinholes, slivers, notches,
  steps, ledges) and design quality (`scripts/quality/checks.py`: smooth
  nodes, kinks, extremes, whole units, alignment zones, stem weights, the
  italic's slant, accent gaps, the Bold's widths, and derived letters
  against their recipe's base, `scripts/quality/derived.py`: base kept,
  stem, whole advance, an italic one made from the roman; glyphs darker or
  lighter than their kind, `scripts/quality/strokes.py`: each main stroke
  against n/o, H/O, h.sc/o.sc, ±10 %; `quality*.txt`, regenerate
  with `update_test_data.py --quality`) against each style's known findings (`glyph-lint*.txt`; regenerate
  with `update_test_data.py --lint`). derive.py, make_italic.py and
  make_bold.py clean specks, twists, pinholes, steps and ledges from what they
  make; `glyph_lint.py UFO --fix` does it for drawn glyphs.
- Exception lists in `tests/data/*.txt` only shrink: a test fails when an
  entry is no longer needed. Fixing an entry = deleting its line.
- When a test fails: find the cause first (`make regress` diffs shaping
  against HEAD; `scripts/nfd_debug.py UFO CHARS` shows NFC vs NFD). Only for
  an intended change, regenerate baselines with
  `scripts/update_test_data.py` (asks the person first via the plugin) and
  say in the commit what changed and why.
- Never commit with `--no-verify` unless the person asked for it.

