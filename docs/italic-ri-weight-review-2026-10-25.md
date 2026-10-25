# Italic r / I weight review, 2026-10-25

[Comparison proof](../proofs/italic-ri-weight-review-2026-10-25.pdf)
compares the current drawings with a modest lighter trial, enlarged beside
n/H and in repeated paragraph specimens at three sizes. These are
unkerned outline specimens; the spacing and advances are the same in both
columns. Only scratch r and I outlines differ.

| Glyph | Current main stroke | Current reference ratio | Lighter trial stroke | Trial ratio |
|---|---:|---:|---:|---:|
| r | 176 | 1.025 | 164 | 0.978 |
| I | 180 | 0.973 | 165 | 0.892 |

The old TODO suggested these letters might still be too heavy after the
Italic reweighting. The assistant initially recommended retention, using
the reference ratios to argue that thinning I would make it weak beside
H. The person found the lighter trial I acceptable and approved it.
That visual judgment supersedes the numerical recommendation: a reference
ratio is diagnostic, not a design veto. Feedback concerned I; r is retained.

The right-hand trial uses
the existing thick-stroke adjustment at −15 units in the upright frame,
preserving advances, anchors and the original horizontal ink centre
before rounding and local curve finishing. It is a comparison aid, not
a proposed family-wide change; accented and derived relatives are outside
this trial.

`scripts/italic_ri_review.py` reproduces the scratch UFO, measurements,
PNG and PDF in `build/italic-ri-review/`. The final PNG was inspected
for layout and text colour. The script asserts retained advances and
anchors; Ruff passes. The before-state is pinned to `7b2a1117` so the
comparison remains reproducible after integration.

## Approved I integrated

`scripts/data/italic-i/I.glif` stores the accepted drawing exactly.
`scripts/italic_i.py` installs its contours in final spacing in the Italic
generator. This changes I and its component-based accents and aliases;
33 glyphs have different visible ink in each italic style. Bold Italic
inherits the lighter base through its normal weighting. Advances, anchors,
metadata, kerning and feature source are unchanged. Small caps, r, barred
I and the separately drawn Iogonek are retained. The earlier generation
experiment that changed small-cap widths and Greek mark spacing is not
part of production.

[Production comparison](../proofs/italic-i-production-review-2026-10-25.pdf)
shows the accepted Italic and its Bold Italic inheritance. Italic's final
I equals the approved trial exactly. The lighter I adds one intentional
stroke exception; the two unchanged barred-I drawings add stem-comparison
exceptions because their reference I is now lighter. No construction
findings are introduced. Both italic corpus comparisons shape 2,119,788
strings with zero changes; no italic shaping baselines change.

Validation and comparison logs are in `build/italic-i-production/`.
All three generated styles reproduce exactly. Italic/Bold Italic
OTF, TTF and WOFF2 rebuild. Compiled cmap, GSUB, GPOS, GDEF, OS/2, hhea
and name tables match; every advance stays exact. The changed ink edges
update the corresponding hmtx left sidebearings. Exactly the expected
33 I-family charstrings change per weight. Ruff and whitespace pass.
All 24 focused checks pass, including TrueType/CFF hinting, shaping,
composites, quality/lint and exact agreement with the approved I.
