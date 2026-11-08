# Italic arches and belted-l attachments, 2026-10-25

**Verdict 2026-10-26:** The inherited open arch joins (m, ɯ, т, ш and their aliases) accepted as drawn after visual review.

The next lint group comprised the Italic m/arch family and ɬ. The
[arch comparison](../proofs/italic-arches-review-2026-10-25.pdf) includes
Old Standard's source drawings, Myia's two italic weights and enlarged
flagged regions. The [belt before/after sheet](../proofs/italic-l-belt-before-after-2026-10-25.pdf)
shows the repair to lowercase ɬ and capital Ɬ. The
[Bold Italic inheritance sheet](../proofs/bold-italic-l-belt-before-after-2026-10-25.pdf)
shows the corresponding regenerated drawings.

## Belts attached to their stems

The three lowercase findings were actual gaps: the top and bottom ring
ends and the bar stopped short of the light Italic stem. Capital Ɬ had
the same detached pieces without a lint finding. An independent Astra
inspection identified this construction fault before reaching its usage
limit. The small-cap form was already joined.

`scripts/l_belt.py`, called by the generated-style writer after rounding,
extends those three hidden ends into the measured final l/L stem edges.
It works in the upright frame, follows the italic slant, and uses three
units of overlap. Ring placement, outer ring curves, visible bar arms,
base-letter sources, advances and anchors are retained. Normal outline
union and whole-unit rounding settle the intersection points. The result
has a connected outer outline and enclosed belt counter, replacing three
floating pieces. The pass is repeatable. Only ɬ and Ɬ are targeted.

The Bold Italic rebuild inherits the connected source and retains its
final base letters. Extracting the added pieces is limited to their actual
recipe band: otherwise thin base-rounding remnants attached to a real
piece can be emboldened into an unwanted stem extension. The band's bounds
come from the same Regular degree recipe used during Italic derivation.
Explicit optical-fit corrections retain the established advances and
anchors before the derived drawings are rebuilt. This prevents an
attachment repair from changing spacing.

Removed the three-notch Italic ɬ exception. The original base glyphs and
small caps remain unchanged; no shaping baseline updates are intended.

## Reference check requested after the drawing review

The review asked whether the empty space was deliberate and requested a
Charis/Libertinus comparison. The [actual-outline reference sheet](../proofs/l-belt-charis-libertinus-comparison-2026-10-25.pdf)
places the installed reference fonts beside Myia's original and joined
versions at equal em sizes.

- Charis SIL 6.200 joins the belt to the stem in both Italic and Bold Italic,
  for lowercase ɬ and capital Ɬ.
- Libertinus Serif 7.051 Italic joins lowercase ɬ. This installed family
  lacks the other compared forms; missing glyphs are marked rather than
  replaced by fallback shapes.
- The white counter inside the belt is intentional and remains present.
  These references do not leave the three open slits between the ring/bar
  and the stem that were present in Myia's light Italic.

The existing Myia Italic uses the Regular attachment recipes for both
characters; there is no Italic-specific override specifying a gap. Those
fixed piece positions no longer overlap the lighter italic stem. This is
additional evidence for a placement mismatch, not proof of the original
aesthetic intent. After the reference comparison, the review explicitly
accepted the connected belts: “lets stay with connected
belts then” (2026-10-25). This accepts ɬ and Ɬ in the two italic weights;
the separate arch-family retention recommendations are unchanged.

Reference files: `/usr/share/fonts/TTF/CharisSIL-{Italic,BoldItalic}.ttf` and
`/usr/share/fonts/libertinus/LibertinusSerif-{Italic,BoldItalic}.otf`.
Reference proof source: `build/l-belt-reference-review/proof.py`.

## Arch findings retained for visual review

The narrow white tips in m, turned m (ɯ), Serbian т and ш belong to the
inherited Old Standard construction. They are open acute arch joins,
without floating pieces, attachment steps or residual enclosed pinholes.
The source comparison shows the same design before Myia's weighting.

Italic m and Cyrillic т have identical decomposed outlines. Bulgarian т
aliases the Cyrillic form, and ḿ/ṃ retain m as a component. Bulgarian ш
aliases ш. Thus the nine listed glyphs represent four constructions, not
nine independent drawing defects. The Bold Italic versions have the same
basic forms and no notch findings in this group.

Recommendation: retain these nine drawings and existing exception keys.
Refreshed their measurements and annotations. This records a review
recommendation, not final visual acceptance or resolution of unrelated
weight findings. The earlier ɉ terminal review remains unchanged.

Validation: **51 focused checks pass**: five repair regressions, 44
lint/quality/UFO/composite/derived/emboldening/shaping/TrueType checks across
both italic weights, and two CFF hinting checks with helper-socket access.
The shaping goldens and full digests (2,119,788 strings per weight) match;
no shaping baselines or quality exceptions change.

Master and compiled comparisons show exactly ɬ and Ɬ changed per italic
weight. Advances and anchors match. `GPOS`, `GSUB`, `GDEF`, `cmap`, `OS/2`
and `hhea` tables are identical; `hmtx` advances also match. The only bearing
change is Bold Italic ɬ's compiled left bearing, 47 → 48, reflecting its
slightly changed ring bounds. Only the two intended CFF charstrings change
in each font. Regular, Bold, base l/L and small caps are unchanged.

`make reproduce` passes for all three generated styles. Both affected
production OTFs rebuild with hints and STAT tables. Ruff, source sync and
whitespace checks pass.
Working scripts and reports: `build/l-belt-review/` and
`build/italic-arches-review/`.
