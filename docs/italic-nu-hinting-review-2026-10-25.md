# Italic ν hinting review, 2026-10-25

[Current/trial proof](../proofs/italic-nu-hinting-review-2026-10-25.pdf)
contains both italic weights at every size from 8 through 32 ppem. Each
cell compares current and trial output under FreeType v35 and v40, using
Latin o and Greek ν υ ν ο at 2× nearest-neighbour enlargement. Both PNG
pages were inspected for layout and raster behaviour.

ν has an outside bottom point at −23, the same outline height as o.
These are genuine outside-edge findings, unlike the earlier Þ counter
false positive. v40 puts the Italic bottom about 0.50–0.78 pixels below
o at 8–21, 23 and 24 ppem (16 sizes). Bold Italic is about 0.52–0.75
pixels below at 8–19 ppem (12 sizes). v35 has no ν report.

A scratch trial applies `touch ... yshift 0.5` to the original on-curve
bottom point at those sizes only, discovered from the unhinted coordinates.
This is a diagnostic trial, not an approved production change. It removes
seven Italic and six Bold Italic glyph/size findings without adding audit
findings. Nine and six respectively remain.

The reason for rejecting this isolated-point approach is clearer in the
hinted coordinates than in the report counts: at 8 ppem the original
bottom point moves from about −0.78 (Italic) / −0.73 (Bold Italic) to
+0.40625 pixels, while neighbouring on-curve points still reach about
−0.70 / −0.66 pixels. The control adjustment participates in the hinter's
processing; its final effect is not a simple half-pixel translation.
The curve's original lowest point no longer remains lowest. The trial also
changes v35 rasters at every targeted size, despite its original passing
alignment. A lower report count alone does not establish an improvement.

Recommendation: retain the production hints and current exception keys.
A future repair needs coherent curve/segment handling and a fresh visual
comparison, rather than a larger delta to this one point. This review
records the acceptance of the current production hints on
2026-10-25. The isolated-point trial is rejected.

Verification against the current production TTFs:

- Only ν's glyph instruction program changes in each scratch font.
- Every glyph's coordinates, contour endpoints and flags match exactly.
- cmap, hmtx, GSUB, GPOS, GDEF, OS/2, hhea, fpgm and prep match exactly.
- Raster checks across 8–32 ppem in both interpreters change only ν at
  the targeted sizes; the other sizes remain identical.
- A full zone audit of each trial adds no findings, but retains the
  residual ν findings described above.

No production font, UFO, generator or baseline is changed by this review.
Scratch inputs, controls, TTFs, audit and verification JSON, proof script
and rendered pages are in `build/italic-nu-review/`. Reproduce with
`trial.py`, `verify.py`, then `proof.py` using the project virtualenv.
The source TTFs and controls come from the current `build/unhinted/`,
`build/hinting/` and `fonts/ttf/` outputs.

Next hinting review: the shared v35 round-bottom reports in G and the
Cyrillic capital family. The earlier small-cap tip trial remains awaiting
its separate visual verdict.
