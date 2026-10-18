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
- The Italic, Bold and Bold Italic are generated: change them only through
  the Regular or their generators (a recipe, a constant in make_italic.py /
  make_bold.py), never by editing or scripting the generated UFO alone, or
  the next run undoes it. `make reproduce` (≈40 s) reruns the generators
  into build/reproduce/ and lists whatever would change; run it before
  committing changes to the generated styles. Hand-drawn exceptions in the
  Italic are marked "drawn" (org.myiadidot.italicSource), which a run keeps.
- Composites are generated: `scripts/composites.py` (anchor-driven, follows
  upstream's accent conventions). After moving an anchor, rerun the builder
  for the affected composites rather than hand-editing offsets. Upstream's
  deliberate special designs are in `SPECIAL` there.
- Accent conventions: spacing accents 880 wide centred at x=440; combining
  marks are those shifted −880; lowercase bases carry Top/Acute/Grave/
  Dotaccent (Acute/Grave = Top−20, Dotaccent = Top+20), Bottom/DotBelow,
  Cedilla; capitals carry TopCap and take `.cap` accents; stacking via
  TopMark/_TopMark, computed from ink (`--stack-anchors`).
- Small caps: `scripts/smallcaps.py UFO` rebuilds aliases, accented small
  caps, specials, scaled kerning and the generated smcp/c2sc block in
  features.fea (between BEGIN/END markers; never hand-edit it). It never
  overwrites outlines. Drafts from `smallcaps_draft.py` carry lib key
  `org.myiadidot.smallcapDraft`; clear it once a glyph is reviewed. Other
  drafted glyphs (ẞ) carry `org.myiadidot.draft`. Small-cap height is
  1040 (lib `org.myiadidot.smallcapHeight`, chosen by the person after
  comparing 960/1000/1040); small caps take the `.cap` accents at TopCap =
  height + 146. To redraft: `smallcaps_draft.py` then `smallcaps.py
  --drafts ... --redraft` (replaces only unreviewed drafts).
- New letters derived from existing ones (same shape, turned, mirrored, with a bar, slash or middle tilde merged in, the Ц tail added, enlarged to capital weight):
  recipes in `scripts/derive.py` (also their small caps, "ɔ.sc"); drafts
  carry `org.myiadidot.draft` and are reviewed in `drafts-review.pdf`.
  The Vietnamese hook and horn, and circumflex + tone marks set side by
  side (ccmp lookup ccmpVietnameseToneMarks; composites.py uses them):
  `scripts/draft_vietnamese_marks.py`; IPA
  diacritics and symbols: `scripts/draft_ipa_marks.py`; arrows, geometric
  shapes, circled letters: `scripts/draft_symbols.py`; ℓ 𝑙 ℮ ℵ ℶ, and
  𝔐 𝔓 𝔖 𝔭 from Libertinus Math (OFL, credited in OFL.txt and the
  copyright notice): `scripts/draft_letterlike.py`; ligatures ct st
  (dlig), f-ligatures fb fh fk ft (liga) and long-s ligatures (own liga
  lookups): `scripts/draft_ligatures.py`. Hooks: `hook` (f top or ȷ tail
  scaled to the stem) and `curl` (an elliptical ring with a ball, at the
  stroke's own weight) in derive.py. Shaping in this shell defaults to
  German (locale), which has no f-ligatures: pass `--language=en`.
- Inherited accents resized at the same weight (the Latin breve):
  `scripts/adjust_accents.py` (idempotent; then `composites.py
  --stack-anchors --rebuild-stacked`).
- **Bold** (`sources/MyiaDidot-Bold.ufo`) is generated from the Regular by
  `scripts/make_bold.py` (then `smallcaps.py` on it, `make normalize`):
  rerun it after changes to the Regular until the Bold has reviewed edits
  of its own. Tests and baselines are per style (`style_data` in
  tests/conftest.py: `shaping-golden-Bold.json` ...;
  `update_test_data.py --ufo sources/MyiaDidot-Bold.ufo`). Derived letters
  are made of the Bold's own base where the source letter is its base
  turned or mirrored, or keeps all of it (`follow_bases`): emboldened
  whole, their junctions thicken unlike the base's strokes. Letters that
  attach a scaled-down glyph (ɬ Ꞁ's ring, ⁂) take it at the weight of its
  scale (`attached_small`). The paragraphos ⸏ ⸐ ⸑ are emboldened as marks.
- **Bold Italic** (`sources/MyiaDidot-BoldItalic.ufo`) is generated from the
  Italic by the same script: `make_bold.py sources/MyiaDidot-Italic.ufo
  sources/MyiaDidot-BoldItalic.ufo` (then `smallcaps.py` on it, `make
  normalize`); it works in the upright frame (deslanted by the italic
  angle). Rerun it after changes to the Italic. Its own tweaks:
  ITALIC_SIDEBEARINGS / ITALIC_ANCHOR_NUDGE in make_bold.py.
- **Italic** (`sources/MyiaDidot-Italic.ufo`) is generated by
  `scripts/make_italic.py` from Old Standard Italic (Kryukov, OFL; source
  pinned in `sources/oldstand/`, converted into `build/oldstand/`) plus the
  Regular: Old Standard's letters zone-scaled to Myia's metrics, Myia's
  marks and features sloped 15.2°, composites rebuilt. What Old Standard
  lacks is made in an upright frame (derive.py recipes, transplants from
  the Regular, FontForge small caps, fitted old-style figures); the
  Regular's extra ligatures (fb ft ſt ct ...) are left out with their
  rules, so don't run draft_ligatures.py on it; it runs smallcaps.py itself. Lib
  `org.myiadidot.italicSource` says where each glyph came from; a rerun
  keeps "drawn" glyphs (set it after hand-editing one) and reviewed drafts
  (draft key cleared). Then `make normalize`. Review sheets:
  `drafts-review-Italic.pdf`, `smallcaps-review-Italic.pdf`. A style's own
  fontbakery allowances: `tests/data/fontbakery-allow-Italic.txt`.
- Spacing: the Regular's letters were tightened once by `scripts/respace.py`
  (20 a side, Greek lowercase 10; recorded in lib `org.myiadidot.respaced`,
  a second run refuses). make_bold.py adds the Bold's own cut, make_italic.py
  undoes the Regular's in memory (it is tuned on the old spacing) and
  applies the Italic's; derive.py too builds on the uncut spacing and cuts
  again. It leaves kerning alone. The Bold's figures have a cut of their
  own (make_bold.py BOLD_FIGURE_CUT). The Italic's letters are made at Old
  Standard's weight and their thick strokes made heavier at the end
  (make_italic.py WEIGHT, weight_thick):
  recipe widths are for the weight before that; derived letters that keep
  their whole base are then made of the weighted base (make_bold's
  follow_bases, as in the Bold). Emboldening (derive.embolden)
  keeps smooth nodes smooth and fits the handles; derive.rezone puts flat
  edges it moved back on the zones. Old-style figures are proportional
  (`scripts/space_figures.py`, run by make_bold.py/make_italic.py; tnum gives
  the .tf ones). Per-style spacing tweaks: make_bold.py BOLD_SIDEBEARINGS,
  make_italic.py ITALIC_SIDEBEARINGS and ITALIC_KERNING; one-off sidebearing
  changes with respace.sidebearings() (it carries composites along).
- The working copy is inside a pCloud/Nextcloud-synced folder: rewriting
  many files fast can leave "(conflicted)" copies and missing glyph files;
  check for them after big generation runs.
- Win metrics must cover the bbox: `make winmetrics` after adding tall or
  deep glyphs (the fontbakery test flags it).

## Tests are the safety net

- `make test` (≈90 s) runs on every commit via the pre-commit hook
  (`make setup` installs it) and in GitHub Actions.
- What they hold: UFO integrity, composites in sync with anchors, NFC and NFD
  rendering the same ink (with precomposed glyphs removed from cmap so
  HarfBuzz cannot recompose), coverage ratchet, golden shaping corpus
  (`tests/data/shaping-corpus.txt`), a digest over ~1.2M shaped strings,
  fontbakery with an allowlist, and outlines gone wrong
  (`scripts/glyph_lint.py`: specks, twists, pinholes, slivers, notches,
  steps, ledges) and design quality (`scripts/quality/checks.py`: smooth
  nodes, kinks, extremes, whole units, alignment zones, stem weights, the
  italic's slant, accent gaps, the Bold's widths, and derived letters
  against their recipe's base, `scripts/quality/derived.py`: base kept,
  stem, whole advance, an italic one made from the roman; `quality*.txt`, regenerate
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

## Handy commands

| | |
|---|---|
| `make` | OTF, hinted TTF, WOFF2 into `fonts/` |
| `make test` / `make regress` | test suite / shaping diff vs `REF=HEAD` |
| `make reproduce` | do the generated styles come out of their generators as committed? |
| `make proof` | `build/proofs/`: `charset.pdf` (new glyphs in red), `proof.pdf`, `samples.pdf` (running text, many languages, sizes), `textpages.pdf` (full book pages, mixed styles), `smallcaps.pdf`, `smallcaps-review.pdf` (every small cap over guide lines, drafts first), `drafts-review.pdf` (other drafted letters, by kind) |
| `make udhr` | `build/proofs/udhr-quarto.pdf`: one quarto page per language (the UDHR; `scripts/udhr_book.py`, texts fetched once into `build/udhr/`) |
| `make qa` | full fontbakery reports in `build/qa/` |
| `make quality` | design quality against reference fonts (`scripts/quality/`, references fetched into `build/refs/`): colour, spacing, pairs, alignment, construction, transitions, accents, slant, small sizes, into `build/quality/` |
| `python scripts/coverage.py fonts/otf/MyiaDidot-Regular.otf --list` | what is missing |
| `python scripts/status.py --long` | coverage per glyph set + last test run |
| `python scripts/composites.py UFO --check` | composites vs rules |
| `python scripts/glyph_lint.py UFO [GLYPH ...]` | outlines gone wrong: where, what |

Run Python as `.venv/bin/python -I`.

## Claude Code plugin

`tools/claude-plugin/myia-didot` (marketplace file at `.claude-plugin/`):
status line, guards (deny re-import and writes to `sources/upstream/`; ask
before rewriting baselines, `--no-verify`, force-push), and `/font-status`,
`/font-test`, `/font-proof`. Its rules have tests: `claude plugin test
tools/claude-plugin/myia-didot`.
