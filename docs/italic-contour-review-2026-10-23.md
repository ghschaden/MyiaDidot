# Italic contour review, 2026-10-23

[Implemented design pass: before/after comparison](../proofs/italic-contours-before-after-2026-10-23.pdf).

The local finishing pass is now implemented in `scripts/italic_contours.py`
and called by both style generators before clearance kerning. It removes
24 construction findings: 14 in Italic and 10 in Bold Italic. Exactly the
eight reviewed outlines change in each style. Advances, anchors, kerning,
features, other glyphs and the accepted upstream Cyrillic signs are unchanged.

The repaired areas use tangent-aligned handles, a short curve at ƈ's
shoulder, and curve splitting at the final slanted extrema. The light қ's
outer leg node moves two units outward to meet its tangent while retaining
its original weight. All changes are generated; no individual glyphs were
copied into the masters. The whole styles were regenerated and normalized.

The largest measured ink difference is about 0.20% of a glyph's original ink
area (Bold Italic ʄ); all glyph bounds change by less than 0.35 units.
The local outline lint checks are clean and no quality finding increased.
Fourteen obsolete quality entries were deleted and six remaining counts
were reduced. No new quality exceptions or shaping baselines were accepted.

The original review below records the starting point. The remaining base
letter findings and ɮ's style heuristic warning are outside this local pass.
Bold Italic ʄ's upper hook is finished; its older whole-emboldening/base
retention issue still warrants a separate recipe review.

Validation: `make reproduce` passes for all three generated styles. The
focused structural, contour and quality run has 83 passes, one skip and
two failures from the remaining inherited quality findings. Both italic
weights pass TrueType and CFF hinting (four tests). Before/after shaping
of 2,119,788 strings per italic weight has zero differences; final cmap,
hmtx, GPOS, GSUB and GDEF tables match that comparison. All ten accepted
upstream Cyrillic sign files remain byte-identical to upstream. The full
suite was not rerun; earlier shaping-baseline failures remain separate.

## Initial review

[Review sheets: context and enlarged contour details](../proofs/italic-contour-review-2026-10-23.pdf).

Reviewed ƈ ʑ ɮ ʄ Җ җ Қ қ in Italic and Bold Italic against their
current bases. These sheets show the current masters, not proposed
replacements. No outlines, metrics, generators or test baselines were
changed during this review. The accepted upstream ь ы ъ and Bulgarian
signs remain untouched.

Recommendation: retain the overall designs and finish the local joins
and missing extrema. The checks do not justify wholesale reweighting.
The clearest remaining joins are the ƈ hook entrance and the new
Cyrillic descenders. Final visual acceptance remains open.

## Findings and recommended work

| Glyph | Evidence in the current contours | Recommended action |
|---|---|---|
| ƈ | Italic: 5.3° break at 748,1095 and 7.5° at 637,853. Bold Italic: 3.4° at 767,1094. The upper break is at the straight stroke's entrance into the hook. | Make the hook entrance tangent to its stem, then inspect the lower shoulder. Preserve c's bowl and the existing terminal size. |
| ʑ | Two missing extrema in the lower loop in each weight: about 5–6 units in Italic, 5–7 in Bold Italic. Italic also has five smooth-node breaks of 2.1–3.4°, some above the edited lower loop. | Add extrema in the final slanted frame, preserving the curve. Smooth the local join near 551,-12 separately. Keep the small loop and upright tail; these implement the chosen design. |
| Җ | Italic: 6.5° break at 1524,-160 where the new descender enters its curl. Bold Italic: 5.9° at 1220,-163 on the curl's inner return. | Fair these joins locally. Do not smooth the whole Ж-derived outline: several other findings lie on the inherited body. |
| җ | Italic: 5.4° at 986,-160 and 4.9° at 786,-158, on the new curl. Bold Italic: a missing extreme near 775,-159. | Finish both sides of the light curl, add the bold curl's extreme. Preserve the upright descender. |
| Қ | Italic: two small smooth-node breaks near the curl, 2.1° and 2.4°. Bold Italic: 6.5° at 833,208 on the leg/descender join, plus an 8-unit missing extreme near 636,-154. | Prioritize the bold leg join; preserve the foot's width and curl clearance. Add the extreme after slanting. |
| қ | Italic: 4.2° at 724,200 at the leg join, plus smaller smooth breaks. Bold Italic: a 6-unit missing extreme near 373,-154. | Fair the local leg join and add the bold extreme. Some upper smooth findings belong to к's inherited hook. |
| ɮ | Its l stem and adjacent ʒ now read as the intended combined construction. The remaining shoulder kink is 3.9° in Italic, 5.0° in Bold Italic. The new style warning compares the whole composite with l alone. | Keep the overall construction and ZH_DX=150. Review the shoulder's shallow kink independently; do not undo the wider design to satisfy the style comparison. |
| ʄ | Italic's measured stem now matches ɟ. Bold Italic still has a 20-unit missing extreme near 698,1145 in the upper hook; its base-retention warning remains. | Add the hook extreme without flattening its curve. Inspect a dedicated bold recipe before changing its weight: the current bold glyph is still retained as an emboldened whole. |

Coordinates refer to each master's final, slanted frame. Missing-extreme
coordinates identify the start of the reported curve, not the location
of the missing point. Angles are the construction check's tangent breaks.
They locate candidates; a small angle alone is not a reason to redraw a
letter.

## Why the weight warnings need context

The stem measurements below use the existing `strokes.py` method,
rounded to font units. They are comparisons within a style, not suggested
new weights.

| Derived/base | Italic | Bold Italic |
|---|---|---|
| ƈ / c | 171 / 171 | 272 / 273 |
| ʑ / z | 108 / 75 | 155 / 141 |
| ɮ / l | 140 / 142 | 240 / 237 |
| ʄ / ɟ | 144 / 144 | 242 / 260 |
| җ / ж | 141 / 142 | 237 / 237 |

In particular, ʑ's low measurement against n/o is not evidence that the
new loop made it too light: it measures heavier than z. Likewise, the
relative lightness of ɮ and җ is largely shared by their bases. The bold
ʄ warrants a separate base comparison; increasing every derived letter
to n's weight would damage these relationships.

Several apparent regressions are inherited or change classification
after Boolean rebuilding and rounding. For example, Italic Ж already
has the 4.4° break at 1475,452 seen in Җ; Bold Italic ж and җ both have
the 4.8° break at 1640,840. These should be handled in a separate base
cleanup, not by changing the descender recipes.

## Generator locations and verification for a follow-up fix

- `scripts/make_italic.py`: ITALIC_RECIPES for ƈ, ʑ, ɮ and ʄ;
  `descender()` and the Қ/Җ/җ/қ recipes. The hook's line enters at
  approximately 79°, while the curl recipe starts at 75° in both weights.
  Check that mismatch before adjusting the terminal's shape.
- `scripts/make_bold.py`: ITALIC_BOLD_RECIPES for the hook, loop and
  Cyrillic descenders. Keep any finishing restricted to the edited joins.
- `scripts/derive.py`: `with_extremes()` already provides curve splitting;
  apply it after the final shear if used here. `fair_joins()` already
  provides local smoothing. Avoid a global change to `draw_path()` or
  enabling smooth rounding for every Italic glyph during this pass.

A follow-up implementation should regenerate whole styles into scratch
copies, compare every glyph and metric with the starting masters, and
then run glyph lint, quality checks and reproducibility. Check that the
ten accepted upstream sign files still match upstream. Do not add quality
exceptions or accept new shaping baselines merely to clear the failures.

The PDF contains one context page and one diagnostic page per weight.
Red rings mark reported nodes or curve starts; blue lines show the local
control directions. The raw measurements and SVG/PNG versions are in
`build/contour-review/` in this working copy.
