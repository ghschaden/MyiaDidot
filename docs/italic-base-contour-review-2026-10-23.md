# Inherited italic contour cleanup, 2026-10-23

[Before/after proof](../proofs/italic-base-contours-before-after-2026-10-23.pdf)

## Implemented scope

The Ж/ж family is finished in both italic weights, including Bulgarian ж,
ж.sc and җ.sc. Their base letters are aligned before derivation. A final
pass repairs shallow joins and missing extrema left by Boolean rebuilding,
small-cap generation and rounding. It also finishes the inherited bodies
of ʑ, Җ, җ, Қ and қ. The twenty changed outlines have no remaining
construction findings: 55 findings removed in Italic, 40 in Bold Italic.

The generators regenerate complete styles. The advances, anchors, glyph
metadata, kerning and features are preserved. Bold Italic's Bulgarian ж
has a one-unit spacing correction to compensate for a rounding change in
optical fitting; its reviewed advance and anchor coordinates are retained.
The ten accepted upstream Cyrillic sign files remain byte-identical.

Whole-font quality audits show no increased finding counts. Forty obsolete
quality entries are removed (21 Italic, 19 Bold Italic), including stale
ʄ and ₸ entries from the earlier glyph work. No exception was added.

## Geometry comparison

Ink difference is the symmetric difference divided by the starting glyph's
ink area. The largest global bound changes are under 0.22 units in Italic
and 0.43 units in Bold Italic. Bulgarian ж's bold outline retains its
reviewed origin after the optical-fit correction.

| Style | Glyph | Construction findings | Changed ink |
|---|---|---:|---:|
| Italic | `uni0291` | 4 → 0 | 0.080% |
| Italic | `uni0416` | 3 → 0 | 0.033% |
| Italic | `uni0436` | 4 → 0 | 0.041% |
| Italic | `uni0436.loclBGR` | 3 → 0 | 0.050% |
| Italic | `uni0436.sc` | 11 → 0 | 0.131% |
| Italic | `uni0496` | 11 → 0 | 0.095% |
| Italic | `uni0497` | 3 → 0 | 0.054% |
| Italic | `uni0497.sc` | 12 → 0 | 0.134% |
| Italic | `uni049A` | 0 → 0 | 0.021% |
| Italic | `uni049B` | 4 → 0 | 0.043% |
| BoldItalic | `uni0291` | 0 → 0 | 0.015% |
| BoldItalic | `uni0416` | 3 → 0 | 0.041% |
| BoldItalic | `uni0436` | 5 → 0 | 0.057% |
| BoldItalic | `uni0436.loclBGR` | 4 → 0 | 0.082% |
| BoldItalic | `uni0436.sc` | 8 → 0 | 0.201% |
| BoldItalic | `uni0496` | 3 → 0 | 0.046% |
| BoldItalic | `uni0497` | 3 → 0 | 0.047% |
| BoldItalic | `uni0497.sc` | 11 → 0 | 0.224% |
| BoldItalic | `uni049A` | 2 → 0 | 0.027% |
| BoldItalic | `uni049B` | 1 → 0 | 0.015% |

## The ɮ style heuristic

ɮ is intentionally built from l and ʒ. Comparing the combined silhouette
with l alone incorrectly suggested that it came from the Regular. The
style check now also compares a multi-input attachment with its declared
same-style recipe before reporting a style mismatch. Base-retention and
stem checks continue to examine the primary base independently.

For the current Italic ɮ the attachment overlap is about 0.98. A regression
test replaces it with the sloped Regular ɮ: the overlap falls to about
0.51, while the Roman comparison reaches 1.00, and the style check fails.
This fixes the false positive without exempting the letter from checking.

## Remaining work

The К/к base cleanup was deferred in this pass. An experimental correction to Italic К
changed its Bold weighting by about 3.7% of ink and shifted the advances
of К, Ќ and Қ by eight units. That result was discarded. The accepted pass
preserves their existing base drawings and fixes only the local breaks in
Қ/қ's already-rebuilt bodies. Review the weight-sensitive generator step
before changing those bases.

That review is now complete: [К/к cleanup](italic-ka-review-2026-10-23.md).
The lower-leg correction retains the existing optical-spacing reference
and all advances.

Bold Italic ʄ's older whole-emboldening/base-retention recipe review remains
open. The wider inherited-outline backlog in TODO.md also remains.

## Validation

The full suite passes: **150 passed, 3 skipped** (one deprecation warning),
including glyph lint, both formerly failing quality checks, all four
styles' shaping baselines, and TrueType/CFF hinting. The skips concern the
Regular itself, which is neither generated nor weighted.

`make reproduce` reports Italic, Bold and Bold Italic as generated. Full
before/after shaping covers 2,119,788 strings per italic weight with zero
differences. Compiled cmap, GPOS, GSUB and GDEF tables and all advances are
identical; the small changed x-extrema can alter hmtx left sidebearings.
`make diffenator VISUAL_REF=HEAD VISUAL_STYLES="Italic BoldItalic"`
confirms exactly the ten intended outline changes per style, with no
changed words or layout rules. The only metric-table differences are
left sidebearings on Bulgarian ж, ж.sc, җ and җ.sc; advances are identical.
Its summary is `build/visual/diffenator-summary.txt`.

Sync checks, Ruff and `git diff --check` pass.

Raw geometry/quality audits, reference and generated masters, shaping
comparisons and diagnostic PNG/SVG pages are in `build/base-contours/`.
