# Gaps found carrying out redraw.md

## Italic Greek lowercase batch (Sonnet, 2026-11-12)

Fit of 25 letters: 14 candidates at once, 5 more after one spec entry each,
6 still failing the gate (beta eta phi chi psi mugreek).

- **`bent_back` at an inflection extra node (eta 777,-302 and 765,229; psi
  778,576 and 563,-409).** redraw.md covers a stem edge drawn as a curve
  (`line`), but here the flagged node is an inflection the tool put on an
  S-shaped descender; `line` is refused ("no node within 15 units", the
  node is not an old one) and `extra` at the same place changes nothing.
  Missing: what to do with a bend-back at a node the tool itself made.
- **`line` refused for beta 192,-531 (6.5 units off its chord) and phi
  517,-47 (136 units)**: those are real curves; the doc's "look for the
  same in descenders (ρ φ р ф)" does not say what next. ρ passed untouched.
- **chi**: 622,-309 is 6.3 units off; an `extra` there brings it to 4.2
  (limit 4) at another place (541,-389), and the bend-back at 510,58
  (1.22 degrees, a corner next to a short line) stays. No entry found.
- **mugreek**: fails `extreme 731,-23 5 units past`; the doc has no entry
  for an extreme the gate wants a node at.
- **A spec point on an off-curve point crashes** ("operands could not be
  broadcast together with shapes (201,1) (4,2)") instead of being refused
  as "no node there". Tool bug, cheap to mend; the bend-back messages
  give the curve's start node, but beta/phi/mugreek spec points I tried
  were handles.
- alpha and lambda pass only with the tolerance widened by the tool itself
  (2.8): the doc says not to raise `tol` for one glyph, yet the tool does
  it unasked and reports it only as a remark.

## Phase 3: the italic kerning rule into the generators (Opus, 2026-11-12)

Carried out as spacing.md said; the values came out as the prototype's
(A V -124, A T -37, P Y -15). One gap:

- **A dropped pair took kern_clear's guards with it.** spacing.md said the
  accented members are kern_clear's "afterwards, as now", but the guard
  only looks at group pairs that are kerned (negative): where the rule
  removed b v, b j, o j, ᵬ ổ ồ lost their exceptions and met v w y, ǰ
  (to 48 units of overlap). Mended by keeping such pairs at 0 and guarding
  at 0 too (italic_kerning.apply, kern_clear.guard). Found only by reading
  the shaping report for tightenings, not by any test: worth a rule that
  a generator's kerning change is checked with the guard's measure over
  every member, kerned or not (phase 1's sweep).

## Phase 1's collision sweep (Opus, 2026-11-13)

Built as `docs/claude/collisions.md` said, nothing in it wrong to carry
out; two gaps, both in what it assumed rather than in the method:

- **Step 2 checked the measure against renderings of 2026-11-09**, two
  redraws old for the italics. Their `f?` `f!` `[j` are clear across
  (and were before the redraw too); the italics' `[j` looks tight only on
  the diagonal, which the doc rules out of the measure. A check against
  pictures wants pictures of the same state, or a pair measured by hand.
- **The italics' `„`** (799 and 812 pairs: `„A` -188, `„s` -34, `„D`,
  `„I`, the Greek capitals) is the largest family by far and was not in
  the renderings' list; the doc's families (f ſ, j, overhanging f,
  ascenders against brackets) did not foresee it. Whether `„` before a
  slanted foot is fixed by kern_clear's measure across (it would loosen
  `„A` by 208) or by a narrower `„` in the italics is a design question.

## T2's step 0 and stage A (Opus, 2026-11-13)

Carried out as `docs/claude/only.md` said; three gaps:

- **The Bold Italic reads a third UFO.** make_bold's italic kerning reads
  the Bold beside SOURCE (`Path(args.regular).with_name(...)`); the page's
  State table lists only SOURCE and TARGET. With a trial Italic in
  `build/only/` and no Bold there, the run would have stopped; it now
  falls back to the committed Bold and says so.
- **The drafts store is written by a whole run too**, not only under
  `--only`: `fontforge_inputs.drafts` saves `sources/drafts` when a
  draft is stale or held. Stage A's "no change beyond the argument" would
  have let `make only STYLE=Italic` write under sources/; `--out` makes it
  read-only.
- **Step 0's rule had no case for "one generator just over a minute,
  and no single pass holding most of it".** The Bold Italic is ~80 s
  after kern_clear's cache, spread over whole-font passes (slit check
  19 s, smallcaps.py 22 s, write 12 s); stage B would not remove those
  for a glyph that is read by many. Left to the designer.

## T5, the tables into data modules (Opus, 2026-11-13)

Carried out as `docs/claude/tables.md` said, in four commits; two gaps:

- **The order could not be kept.** make_italic's ITALIC_RECIPES are
  written with derive's `BIG`, so data_italic.py could not import it
  without importing derive (decision 5) before BIG was itself in a data
  module. derive went second, make_italic third.
- **"Text" and "value" look alike to a pointer sweep.** BOLD_REBUILD's
  reason strings name `derive.SPACING`; repointed as if a comment, the
  table's value changed. Proof (b) caught it; the strings stay as written.
  The page's rule for pointers should say "comments and docs, never a
  string in a table".

## Phase 2, the Regular's missing kerning (Opus, 2026-11-13)

- **Two pair measures, no rule which one decides.** TODO's phase 2 says
  "make pairs against the Latin references" (gap over n n, the whole
  x-height band); the italic rule and tests/test_latin_pairs.py use
  italic_kerning's share (white over the case's own rhythm: H n for a
  capital before a lowercase). On the same fonts they disagree in
  direction for R v w y, R O Q, A“ A", 7. 1. 1, W v w (the gap measure
  calls Myia too loose, the share in range or too tight), and in size
  everywhere (the share moves 2-3 times as far per unit). One measure for
  upright kerning is missing (one source of truth); the round set only
  pairs on which both agree.
- **Spacing or pair?** A fault shared by all the partners of one letter
  (' and ” loose before every stem capital, G tight before every
  lowercase) is the letter's sidebearing, not a pair; the phase lists
  them as pairs ('D, Gi) and no step says how to tell the two apart or
  who changes a sidebearing across the generated styles.
- **The italic test sees only a group's name-giving glyph.** W's pairs
  were never measured while W stood in V's group; splitting it made old
  faults (W, WA WJ WO WÆ Wj) appear as new, which the "lists only
  shrink" rule has no case for (they were listed with that reason).
  Members whose shape differs from the representative go unmeasured.
- **Increments compound on shared keys.** A script that adds to the
  resolved value per glyph pair adds several times where the pairs share
  one group key (W o, W e, W c in kern2.c: -192 became +138). The phase
  should say: set absolute values per group key, and check that no two
  requested pairs land on one key.
- **Accented right groups (kern2.agrave, kern2.egrave) do not follow
  their base pair.** Loosening V a or W o leaves V à W è at the old,
  now tighter value; nothing (kern_groups, kern_clear, a test) carries
  or checks it. Set by hand here (same delta, never tighter than the
  base).
