# Bold Italic dollar terminal review, 2026-10-24

**Historical review, superseded for the bars.** The user subsequently
identified that the through-strokes were not straight. The
[bar correction and new proof](bold-italic-dollar-bars-review-2026-10-24.md)
align all four edges while preserving the ball terminals and open channel.
Dollar now has no glyph-lint finding; its old notch exception is removed.
The observations below describe the earlier drawing and the limited scope
of this initial terminal review.

[Comparison proof](../proofs/dollar-terminal-review-2026-10-24.pdf)
shows the current Italic and Bold Italic, with enlarged lower terminals.

The first remaining Bold Italic glyph-lint entry is dollar. The current
checker reports one notch at 476,372, 34 pixels (the historical annotation
recorded 477,376, 35 pixels). Italic has no findings for dollar.

The flagged region is the open white channel between the lower ball
terminal and the left diagonal stroke. The Italic has the same construction;
in Bold Italic the heavier ball approaches the diagonal closely enough to
trigger morphological closing. Inspection of the outline and solid proof
shows an open terminal, rather than a misplaced attached component or a
short ledge. The checker reports no other fault in either dollar.

Recommendation: retain this drawing and its existing exception. Filling
the channel would attach the ball to the diagonal; widening it would alter
the ball or stroke. Neither change is justified by this near-threshold
finding alone. This is an agent review recommendation, not recorded user
acceptance of a drawing change.

No outlines, generators, metrics, anchors, layout rules or shaping
baselines changed. Validation uses the current glyph-lint checker on
dollar in both italic masters and visual inspection of the proof. The
full font suite is unnecessary for this documentation-only review.

Next unreviewed Bold Italic entry: Ⱦ (`uni023E`).
