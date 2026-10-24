# Bold Italic ʄ recipe review, 2026-10-23

[Before/after proof](../proofs/bold-italic-j-hook-before-after-2026-10-23.pdf)

Bold Italic ʄ is now rebuilt from its own ɟ base, rather than emboldened
whole. Its recipe is in `ITALIC_BOLD_RECIPES`, with an explicit rebuild
entry in `scripts/make_bold.py`.

The light Italic recipe extended a stem between x=351 and 495, and cut
the bar at x=500. In the Bold Italic generator's upright frame, ɟ's stem
at y=600 spans about x=335–586. Reusing the light coordinates therefore
cut through the heavier base and failed the recipe comparison. The
generator kept the whole-emboldened outline instead; its lower body
differed from ɟ and its stroke stayed lighter than the surrounding letters.

The first redraw passed numerical checks but was rejected visually: its
narrow elliptical hook pinched the inner counter and produced a lumpy
terminal. The revised recipe retains the old hook's open counter, arch
and rounded terminal. Explicit cubic curves replace the overlapping
ellipse construction, with a continuous inner return and a gradual
transition into the heavier stem. The descender and lower stem still
come from the same-style ɟ. The rightmost edge and advance are preserved.

The finishing pass also aligns three shallow joins in the retained body
and stem connection. Both the original and final glyphs have zero
construction and glyph-lint findings. This finishing applies to Bold
Italic ʄ; the other styles are preserved.

## Measurements

| Check | Before | After |
|---|---:|---:|
| Base retained by the sampled quality check | about 22% | about 65% |
| Main stroke relative to its kind | 0.85 | 0.92 |
| Advance | 680 | 680 |
| Top | 1309 | 1309 |
| Rightmost ink | 940 | 940 |
| Leftmost ink | −373 | −381 |

The lower body below the bar differs from the shifted same-style ɟ by
about 1% of ink, including final rounding and contour finishing. The
regression test compares that complete lower body, independently of the
quality check's sampled spans; the former whole-emboldened body differed
by about 5% in the same comparison.

The complete outline's symmetric difference is about 3.15% of the original
ink. Its ink area is measured as union minus intersection: the diagnostic
Skia XOR on these oppositely wound outlines returned incorrectly wound
nested contours. The union/intersection measurement agrees when either
input winding is reversed.

Exactly one glyph outline changes. Its advance, anchors, components,
Unicode mapping and glyph metadata are preserved, as are vertical font metrics,
kerning, groups, features and every other glyph. The font's whole-emboldening
record loses only ʄ. Removed its one whole-emboldening exception and two
quality exceptions; no exceptions or shaping baselines are added.

Before/after shaping over 2,119,788 strings has zero differences. Compiled
cmap, GPOS, GSUB, GDEF and all advances are identical.

The updated before/after PDF shows the revised hook at full-glyph and
contour-detail sizes. The final generated master matches the recipe
exactly; comparison with the original master confirms just one changed
outline and the removal of its whole-emboldening record.

The suite reported **152 passed, 3 skipped**, with one failure because the
edited UFO needed normalization. After normalizing the changed glyph, all
four normalization checks and the lower-body retention test passed. The
Bold Italic master was regenerated and compared exactly; compiled-font
shaping and layout comparisons pass. `make proof`, Ruff and
`git diff --check` pass.

The original and generated masters, diagnostic scripts, audits, shaping
logs and detail sheets are in `build/j-hook-review/`.
