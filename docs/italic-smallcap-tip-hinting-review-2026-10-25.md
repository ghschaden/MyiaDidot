# Italic small-cap tip hinting trial, 2026-10-25

[Current/trial proof](../proofs/italic-smallcap-tip-hinting-review-2026-10-25.pdf)
shows h.sc, v.sc, w.sc and o.sc, plus Cyrillic izhitsa.sc and W-curl.sc,
under both FreeType TrueType interpreters. Specimens are enlarged 2× by
nearest-neighbour sampling, with native-size HVWO copies below. The final
PNG was inspected for layout and placement.

After the accepted Þ counter-audit repair, continued to the remaining
Italic small-cap tip reports. v.sc, w.sc, uni0475.sc and uni2C73.sc have
outer bottom edges at −35, matching the round reference's outline height.
Unlike the preceding counter reports, these comparisons concern outside
edges. At 30/32 ppem their hinted bottom tips can extend nearly one pixel
below the round reference. v35 flags 32 ppem; v40 flags both 30 and 32.
The four glyphs share the issue. Bold Italic does not have these reports.

The scratch trial adds a +0.5 pixel `touch` shift to their on-curve bottom
points, at 30 and 32 ppem only. A full pixel would overcorrect v35's
half-pixel reference phase. The shared half-pixel adjustment also changes
v35 at 30 ppem, where its original deviation was just below the audit's
0.5-pixel threshold. This visual tradeoff is shown in the proof alongside
unchanged control sizes 24, 28, 29 and 31.

The trial gives the tips a steadier baseline in the two affected sizes.
It remains for visual review; no production integration or acceptance is
recorded. The original overshoot and all source drawings are preserved.

Verification against the current production TTF:

- Only the four intended glyph instruction programs differ.
- All glyph coordinates, end points and flags match exactly.
- cmap, hmtx, GSUB, GPOS, GDEF, OS/2 and hhea match; so do the shared
  fpgm and prep hint programs.
- Raster comparison across 8–32 ppem finds changes only at 30 and 32,
  for each of the four glyphs in both interpreters.
- The audit removes four v35 and eight v40 glyph/size findings, represented
  by eight exception entries. It adds no findings. Production exception
  lists remain unchanged until a drawing/raster verdict is made.

No source UFO, production font, generator, layout or shaping baseline is
changed by this trial. No font-wide rendering adjustment is proposed.

Scratch inputs, TTF/control files, reports and proof scripts are in
`build/smallcap-tip-review/`: `trial.py`, `verify.py`, `proof.py`,
`Before.ttf`, `Before.txt`, `Trial.ttf`, `Trial.txt`, `audit.json`, and
`verification.json`. `trial.py` reads the current unhinted Italic TTF
from `build/unhinted/`, then uses the existing ttfautohint settings.
If accepted, integrate the targeted hint rule with point discovery rather
than fixed point numbers, update the eight reviewed exception entries,
and rebuild/verify TTF and WOFF2.
