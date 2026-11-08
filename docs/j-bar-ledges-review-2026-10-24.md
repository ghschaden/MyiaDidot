# ɉ bar ledges reviewed, 2026-10-24

**Superseded for Bold Italic:** the review found its bar too short.
See [the implemented extension](j-bar-extension-review-2026-10-24.md)
and its before/after proof. The other three styles retain their drawings.

[Four-style comparison proof](../proofs/j-bar-ledges-review-2026-10-24.pdf)
shows the complete letters and enlarged right bar ends at matching scales.

Bold Italic ɉ has two lint findings at the right end of its horizontal
bar. These are the short upper and lower edges where the bar projects
past the stem. Regular, Bold and Italic have the same construction.
The current checker reports:

| Style | Edge locations and lengths |
| --- | --- |
| Regular | 382,414: 30 units; 412,470: 30 units |
| Bold | 465,410: 11 units; 476,472: 11 units |
| Italic | 471,414: 16 units; 503,470: 15 units |
| Bold Italic | 552,410: 15 units; 553,471: 19 units |

These are intentional bar terminals. `scripts/derive.py` declares ɉ as
a bar added to j; `bar_shape` limits its default extension to the base's
ink bounds. This gives the bar a long left arm and a short projection
on the right. `scripts/glyph_lint.py` explicitly includes `uni0249` and
its small cap in `LEDGE_KEEP`, documenting that the bar ends in a stub
past the stem. Both derivation and cleanup preserve those ledges.

Recommendation: retain the existing drawing and both exceptions in every
style. Removing these edges would shorten or taper the bar terminal.
The solid proof shows no separate attachment step requiring repair.
This records an agent review, not new user acceptance of a drawing.

Corrected the two italic lint annotations, which had called these
ledges “narrow arch crotches,” and refreshed the Roman measurements.
All four `uni0249 ledge 2` keys are unchanged. No font sources,
generators, layout data or shaping baselines change.

Validation: focused glyph lint on ɉ in all four masters finds exactly
the two known ledges per style and no other findings. Inspected the
outline against Bold Italic j and the solid four-style proof. No tests
were added or full suite run for this documentation-only review.
Proof source and working renderings: `build/j-bar-review/`.

Next unreviewed Bold Italic glyph-lint entry: ɸ (`uni0278`).
