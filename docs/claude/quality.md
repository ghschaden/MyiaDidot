# Quality principles (learned the hard way)

Moved from CLAUDE.md (its ground rules apply).

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
  further off; `update_test_data.py --greek`.) Not for Cyrillic, where
  Charis and Libertinus are the outliers and Old Standard, Kryukov's own
  Didot Cyrillic, sides with Myia: there no frequent pair may fall outside
  all four references' range (tests/test_cyrillic_pairs.py,
  `cyrillic-pairs*.txt`, `update_test_data.py --cyrillic`).
- After a change that should touch only some glyphs, scripts or pairs,
  sweep for side effects: `make diffenator` (diffenator2's word lists over
  every script, against `VISUAL_REF`) writes
  `build/visual/diffenator-summary.txt` (tables, changed glyphs, words per
  script, the pairs behind them in units). Hand it to the font-measure
  agent with what the change was meant to do; it reports what falls
  outside. Its pairs are a sample of its word lists, not every pair.
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

