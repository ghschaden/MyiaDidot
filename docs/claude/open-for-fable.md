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
