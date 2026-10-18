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
  deliberate special designs are in `SPECIAL` there. Where a precomposed
  letter is drawn otherwise than its decomposition places the marks
  (polytonic Greek, the capital breve), `scripts/nfd_compose.py` composes
  the decomposed form back in ccmp (a generated block in the Regular's
  features.fea); rerun it when the NFD test reports a new mismatch. The
  combining cedilla and ogonek are marks (they were base glyphs, so they
  were never positioned).
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
  height + 146. A capital before a small cap is kerned only where a style
  falls outside the references (CAP_SC_KERNING there, final values per
  style from `scripts/quality/capsc_pairs.py STYLE`). To redraft: `smallcaps_draft.py` then `smallcaps.py
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
  scale (`attached_small`). Those that cut their base (hooks, Ц's tail)
  are made again by their recipe from the Bold's own glyphs (`rederive`;
  what recipes draw by number at the Bold's stems and hairlines,
  derive.STROKE_KEY), kept where the result stays close and clean; recipes
  that miss in the Bold are reviewed exceptions (BOLD_KEEP_WHOLE,
  ITALIC_BOLD_KEEP_WHOLE). The paragraphos ⸏ ⸐ ⸑ are emboldened as marks.
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
  the Regular (the part at the Italic's stems before the weight pass,
  measured on n and H), FontForge small caps, fitted old-style figures); the
  Regular's extra ligatures (fb ft ſt ct ...) are left out with their
  rules, so don't run draft_ligatures.py on it; it runs smallcaps.py itself. Lib
  `org.myiadidot.italicSource` says where each glyph came from; a rerun
  keeps "drawn" glyphs (set it after hand-editing one) and reviewed drafts
  (draft key cleared). Then `make normalize`. Review sheets:
  `drafts-review-Italic.pdf`, `smallcaps-review-Italic.pdf`. A style's own
  fontbakery allowances: `tests/data/fontbakery-allow-Italic.txt`.
- Spacing: the Regular's letters were tightened once by `scripts/respace.py`
  (20 a side, Greek lowercase 10, of which 8 were given back after measuring
  Greek pairs; recorded in lib `org.myiadidot.respaced`, a second run
  refuses). Greek spacing and kerning are measured against Greek references
  (GFS Didot, EB Garamond, Libertinus, Charis), calibrated by each style's
  own Latin: `scripts/quality/greek_pairs.py STYLE`; the italics' Greek
  cuts are ITALIC_CUT_GREEK (make_italic.py) and BOLD_ITALIC_CUT_GREEK
  (make_bold.py), their Greek pairs in ITALIC_KERNING, BOLD_KERNING and
  ITALIC_BOLD_KERNING. Accented letters share their base letter's
  kerning groups (a Greek capital's left side excepted: its accents stand
  there), letters shaped like another its groups (ALIKE): both by
  `scripts/kern_groups.py` on the Regular, where the accent stays clear
  of what the group kerns against in all four styles (Yì, fï stay out);
  then smallcaps.py. Gaps: `scripts/quality/kern_coverage.py UFO`.
  Reviewed collisions (ą į ų before j, the Bold Italic's AY) are
  loosened to CLEAR units of white by `scripts/kern_clear.py` (PAIRS),
  per style: the generators undo the source's (lib
  `org.myiadidot.kernCleared`) and find their own. make_bold.py adds the Bold's own cut, make_italic.py
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
  check for them after big generation runs (tests/test_ufo.py fails on
  them).
- Win metrics must cover the bbox: `make winmetrics` after adding tall or
  deep glyphs (the fontbakery test flags it).

## Quality principles (learned the hard way)

- Build a derived glyph from its base in the same style, after that base is
  final; order generator stages so bases come first, and know what is
  already transformed (the italic ɗ from the Regular's d; italic small caps
  derived before the italic small caps existed; kept glyphs weighted twice).
  (Enforced in the Regular: derive.py records a fingerprint of every glyph a
  recipe read, lib `org.myiadidot.builtFrom`; tests/test_built_from.py fails
  when one changed since: rebuild, or look and `scripts/built_from.py UFO
  GLYPH --accept`.)
- Never embolden or weight a combined shape whole: junctions thicken unlike
  the base (Ⱦ's stem eaten, ɬ's ring closed). Process the base and the
  added piece apart (the piece at the weight of its scale), then join.
  (Enforced: the generators record the derived letters they leave whole, and
  why, in lib `org.myiadidot.emboldenedWhole`; tests/test_emboldened.py holds
  them to `emboldened-whole-STYLE.txt`; `update_test_data.py --emboldened`.)
- One source of truth per decision: where two settings must agree
  (composites and anchors/GPOS), generate one from the other. (Enforced:
  the Regular's generated parts are as their scripts make them now,
  tests/test_generated_current.py reruns derive, smallcaps, adjust_accents,
  stacking and space_figures on a copy.)
- Generated styles change only through their generators (enforced: `make
  reproduce` in the pre-commit hook).
- Check glyphs against each other, not only one by one: against their base
  (derived.py), their kind (strokes.py: n/o, H/O, h.sc/o.sc) and their
  other encoding (NFC/NFD), and styles against the Regular (enforced:
  glyphs, code points, categories, kerning groups, anchors,
  tests/test_styles_agree.py, `styles-agree-STYLE.txt`). Per-glyph lint
  passed every one of today's faults. Weight belongs to the context: old-style figures to the
  lowercase, lining to the capitals.
- Reference fonts are a range, not a target, and calibrated: ask whether
  Greek sets as Myia's own Latin does, not as Garamond does (greek_pairs.py
  shifts by the style's Latin offset). Charis and Libertinus agreeing
  against Myia: fix it. (Enforced where the references are installed:
  tests/test_greek_pairs.py, `greek-pairs*.txt`, a listed pair may not get
  further off; `update_test_data.py --greek`.)
- Read `make regress` before accepting a new baseline: one composition rule
  once changed 1098 strings where a few were meant. (Enforced:
  `update_test_data.py --golden/--digest` shows the strings that differ from
  HEAD and writes nothing without `--expect-changes N`, N being that count.)
- Metadata fails silently: glyph categories (enforced: combining marks are
  marks, tests/test_recipes.py), glyph order, lookup order (enforced: the
  compiled lookup order per style, `lookups*.txt`, tests/test_lookups.py;
  read the diff, then `update_test_data.py --lookups`). Code points look
  alike (enforced: recipes make target characters or their case pairs;
  glyph names and code points agree, tests/test_ufo.py; U+A780 was typed
  for U+A7AD).
- Geometry operations need verifying: Skia's union fails on coinciding
  curves (check the result row by row), differences leave slivers (filter
  by area), transformations leave fractions (round to whole units).
- Do not copy single glyphs between UFOs: aliases keep stale widths,
  composites point at other versions. Regenerate whole styles. (Enforced:
  aliases are as wide as their glyph, tests/test_built_from.py,
  `alias-widths*.txt`.)
- The tools find candidates; the person's eye decides. Make review sheets
  (`make strokes`, `make proof`), and put designed exceptions (ξ, 7) on the
  known lists rather than "fixing" them.

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

## Working economically

Token budgets run out on this project; keep the expensive model for
analysis, design decisions and new tools, and hand the loops to the project
agents (`.claude/agents/`):

- `font-runner` (Haiku): `make generate`, tests, `make reproduce`, `make
  otf`/`proof`, baseline updates you name exactly. Reports pass/fail and
  failing names only.
- `font-measure` (Sonnet): strokes.py, derived.py, checks.py, glyph_lint.py,
  greek_pairs.py, `make pairs`, `make regress`: returns a short table and
  the paths of the full reports.
- Searches through the code: the built-in Explore agent.

Write long outputs to files and grep them; render only the glyphs in
question, small. One task per session (`/clear` between tasks): CLAUDE.md
and git hold the state.

## Handy commands

| | |
|---|---|
| `make` | OTF, hinted TTF, WOFF2 into `fonts/` |
| `make test` / `make regress` | test suite / shaping diff vs `REF=HEAD` |
| `make generate` | regenerate Italic, Bold, Bold Italic from the Regular (then normalize, check for sync conflicts) |
| `make reproduce` | do the generated styles come out of their generators as committed? |
| `make strokes` | `build/quality/strokes-STYLE.pdf`: glyphs darker or lighter than their kind, each between its references, for review |
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
