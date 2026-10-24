# r shoulders and retroflex hooks, 2026-10-24

The user requested rounded r shoulders and retroflex-r hooks that resemble
the Regular and Bold drawings. This extends the original review of the
Bold Italic lowercase shoulder notch at 680,770 (35 pixels).

The [before/after proof](../proofs/r-shoulders-hooks-before-after-2026-10-24.pdf)
places r and ɽ beside their previous drawings and the corresponding roman
weight. Enlarged shoulder panels show the change to the inner return.
The [initial four-style review](../proofs/r-hook-review-2026-10-24.pdf)
also includes the small caps.

`scripts/r_hook.py` rounds r's short inner return into its ball. The new
curve keeps the top of the return, the leftmost ball node, the lower ball
curve and the outer silhouette. Both italic generators apply this before
building derivatives. True extrema are added without changing the curves;
the final pass finishes shallow joins left by Boolean work and rounding.

The lowercase ɽ now takes the complete body of its final r. Its hook uses
the actual Regular or Bold ɽ hook at the corresponding weight, calibrated
to the italic stem width and sheared to the font's italic angle. This
retains the roman hook's rounded U turn, upright terminal and vertical
hairline thickness. The depth changes from -275 to -420, matching the
roman drawings. A short tangent-matched transition joins the stem to the
hook. The glyph's own advance, anchors, Unicode and metadata are retained.
The corresponding roman UFO is a generator input; `make generate` already
builds Bold before Bold Italic.

The person subsequently identified an inward bump on the right side of
the Bold r and ɽ stems, and an uneven left shoulder in Bold Italic. The
Bold correction shortens the outgoing shoulder handle along its tangent
so the inner edge approaches the straight stem monotonically. It changes
only these two Bold outlines. The Bold Italic left shoulder now has one
rounded inner arch instead of several small turns; its derivatives follow
the corrected base. The other accepted hook and ball shapes are retained.

The Bold generator also pins the established weighting choices for ɍ,
ɺ, ɻ, ɾ and ɽ. Otherwise its automatic fault comparison would let this
local shoulder correction switch the weighting of entire bodies, changing
stem thickness and spacing. This keeps that independent design decision
stable. Their original optical-spacing references are pinned separately
from their body weighting, preserving the previous advances and anchors.

The affected family comprises r, ɍ (`uni024D`), ɹ (`uni0279`), ɺ
(`uni027A`), ɻ (`uni027B`), ɽ (`uni027D`), ɾ (`uni027E`), r with middle
tilde (`uni1D72`) and r with fishhook and middle tilde (`uni1D73`). Accented
composites inherit r's new outline through their existing components.

The small-cap finding at 817,-23 (107 pixels) is the narrow open gap
between its curled leg and the swash. Its drawing and exception are
retained. This is a visual-review recommendation, not recorded user
acceptance. No small-cap hook redesign was requested in this pass.

Master comparison confirms exactly two changed Bold outlines and nine
per italic weight. Advances, anchors, Unicode values, kerning, groups and
feature text match the previous masters. Compiled `hmtx`, `GSUB`, `GPOS`,
`GDEF`, `cmap`, `OS/2` and `hhea` tables match; CFF changes are limited to
these letters and the five existing accented r composites per style.
Regular is unchanged. Shaping baselines are unchanged.

Removed the lowercase Bold Italic ɽ notch exception and the ᵳ notch
exception resolved by its inherited shoulder. Quality exceptions only
shrink: the repaired extremes and joins are removed. Existing unrelated
findings remain.

The next unreviewed Bold Italic glyph-lint entry is ʸ (`uni02B8`). The
dollar drawing pass and ɸ optical weight review remain open separately.

Validation: **175 passed, 3 skipped** across the full suite and separate
CFF rerun. The sandboxed run reports 171 passes and four helper-socket
failures; all four CFF checks pass with local socket access. This includes
shaping goldens/digests, TrueType hinting, all-style lint/quality, structural
and six focused r-family regression checks. `make reproduce` passes for
Italic, Bold and Bold Italic. `make proof` passes with helper-socket access;
all four production OTFs have hints and STAT tables. Ruff, source sync and
whitespace checks pass.

Working proof scripts and comparison logs: `build/r-hook-review/`.
