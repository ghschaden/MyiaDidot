# Bold Italic hooked b/d small-cap stems

Scope: uni0253.sc and uni0257.sc in Bold Italic. The person clarified that
the concern was the small caps for hooked b and d, not h, and especially
the bottom of the main stroke toward the lower serif; the top could also
need attention. The approved Italic drawings are unchanged. This Bold
Italic follow-up awaits visual acceptance.

The initial investigation focused on the upper joins. It found an inward
bend before the outside edge turned into the hook, and a backwards turn
at d's counter-head bracket. These are corrected locally in the Bold
Italic finishing stage of `scripts/italic_smallcap_repairs.py`.

The lower joins were the main issue. On the outside, the serif-top curve
started inside the stem rather than outside it, forcing the outline to
turn back before joining the straight edge. On the inside, the counter's
bottom bracket ended left of its stem edge, forcing another reversal.
Each is replaced with one rounded bracket tangent to its straight stem
and horizontal serif edge. Serif thickness (69 units), baseline, stem
endpoints and established advances remain unchanged. The hook's size and
placement are unchanged.

The changes are local drawn exceptions in Bold Italic. No shared fitter
or generator rule changes, and no edits to h.sc or uni0266.sc.

Evidence under `build/glyph-review/bold-italic-hook-stems/`:

- `before.ufo` preserves the source before the upper-join follow-up;
  `lower-before.ufo` preserves the state before correcting the feet.
- `lower-joins.svg` / `lower-joins.png`: the lower joins, before and after,
  enlarged and deslanted for inspection. Both sides of both stems are
  shown. The final image was inspected.
- `revised.svg` / `revised.png`: full letters and compiled English text
  with c2sc, `script=latn`, including nƁn/nƊn and HƁH/HƊH. The final
  proof was inspected at enlarged and text sizes.

These proofs show outlines and shaping, not screen hinting.

Focused checks: six regression cases pass. They cover connected lowered-r
contours in both italic weights, smooth upper joins in the approved
Italic hooks, and the correct direction of both head and foot brackets
in the two Bold Italic hooks. Outline lint and construction checks find
no defects in either edited Bold Italic glyph. Ruff passes.

Final validation: **368 tests passed, 7 skipped**, with one dependency
deprecation warning. `make reproduce`: Italic, Bold and Bold Italic all
**as generated**. No test baselines were changed for this follow-up.
`scope.json` confirms that only uni0253.sc and uni0257.sc changed
geometrically; all advances, kerning, features and groups are unchanged.
Previously accepted glyph fingerprints remain valid in all four styles.

The person approved Bold Italic uni0257.sc on 2026-11-06; its acceptance
fingerprint is recorded. Approved evidence is retained as
`proofs/bold-italic-hook-stems-2026-11-06.svg` and
`proofs/bold-italic-hook-feet-2026-11-06.svg`.

For uni0253.sc, the person requested a rounder upper counter, like its
lower one, and subsequently approved it. That follow-up is recorded in
[upper-counter review](bold-italic-b-upper-counter-review-2026-11-06.md).
