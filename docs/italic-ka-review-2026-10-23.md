# Italic К/к contour review, 2026-10-23

[Before/after proof](../proofs/italic-ka-before-after-2026-10-23.pdf)

The К/к cleanup is implemented in `scripts/italic_contours.py`. Both style
generators align the base joins before derivation and finish the remaining
rounding breaks and missing extrema afterward. К is treated only in its
lower-leg band, y=180–350; к and к.sc receive the complete finishing pass.
Қ/қ inherit the corrected bases, and Ќ/ќ/ќ.sc follow through components.

## Why the earlier trial changed spacing

The Bold generator calculates optical spacing against a temporary outline
made with its older emboldening method. When that reference has more
outline faults than the source, it tries the rounder method instead.
The reference is separate from the actual outline weighted for the font.

Aligning К's unflagged shallow upper joins removes a fault in that temporary
reference, switching the spacing calculation to the other method. The
left/right correction changes from (5, 0) to (0, −3). That moves the letter
five units and reduces the advances of К, Ќ and Қ by eight units. Most of
the reported 3.7% ink difference is the resulting displacement, rather than
a change in stroke weight.

The implemented correction leaves those upper joins intact and aligns only
the flagged lower-leg tangent. The spacing correction remains (5, 0).
К/к's curves are not split in the early base pass; any needed extrema are
added after weighting. No weighting or spacing algorithm was changed.
A regression test checks that the early К repair preserves its other
points and curve segmentation.

## Result

Five glyph files change per style. Three composites inherit the outlines;
their own files are unchanged. All advances, anchors, components, glyph
metadata, kerning, features and font metadata are preserved. Regular and
Bold are unchanged, as are the accepted upstream Cyrillic signs.

Ink difference is symmetric difference divided by the original ink area.

| Style | Glyph | Construction findings | Changed ink |
|---|---|---:|---:|
| Italic | К | 1 → 0 | 0.0201% |
| Italic | к | 2 → 0 | 0.0321% |
| Italic | к.sc | 6 → 0 | 0.1567% |
| Italic | Қ | 0 → 0 | 0.0364% |
| Italic | қ | 0 → 0 | 0.0056% |
| Bold Italic | К | 1 → 0 | 0.0145% |
| Bold Italic | к | 4 → 0 | 0.0582% |
| Bold Italic | к.sc | 4 → 0 | 0.1496% |
| Bold Italic | Қ | 0 → 0 | 0.0273% |
| Bold Italic | қ | 0 → 0 | 0.0731% |

Whole-font audits find no increased quality counts. Eighteen construction
findings disappear; ten obsolete quality entries are removed. No quality
exceptions or shaping baselines are added or changed.

Before/after shaping of 2,119,788 strings per italic weight has zero
differences. Compiled cmap, GPOS, GSUB and GDEF tables and all advances
are identical. Small changes in x-extrema can change left sidebearings.

The full suite passes: **152 passed, 3 skipped**, including TrueType/CFF
hinting and all four styles' shaping regressions. `make reproduce` passes
for all three generated styles, and `make proof` succeeds. Ruff and
`git diff --check` pass.

`make diffenator VISUAL_REF=HEAD VISUAL_STYLES="Italic BoldItalic"`
reports exactly the five intended glyph outlines per style, with no changed
words, metric tables or layout rules. Its summary is
`build/visual/diffenator-summary.txt`.

Diagnostic scripts, original and generated masters, geometry/quality
audits and full shaping logs are in `build/ka-review/`.
