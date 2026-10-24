# Italic ỵ dot placement review, 2026-10-24

Implemented after review with a closer, 25-unit gap; see the
[final placement and validation](italic-y-dot-review-2026-10-24.md).

[Comparison proof](../proofs/y-dot-placement-review-2026-10-24.pdf).

The inherited Italic ỵ notch is a dot/descender collision, rather than a
fault in y's outline. Bold Italic has the same collision even though its
merged shape passes glyph lint. Path intersection measures 869 square
font units of overlap in Italic and 7,633 in Bold Italic; Regular and Bold
have none. The Roman styles already place the dot beside the descender.

The proof compares all four current styles with a trial that retains the
italic dot's height and places it beside the descender. The trial leaves
50 units horizontally between the dot's left bound and the descender's
right bound within the dot's vertical band. This moves the dot 535 units
right in Italic and 599 in Bold Italic. These are review candidates, not
accepted spacing values; the 50-unit gap is a trial choice.

Both trials have zero intersection with y and pass all glyph-lint checks
for ỵ. Their glyph advances and base outlines are unchanged in memory.
No masters, generators or test baselines were changed. The proof script
is `build/y-dot-review-2026-10-24/proof.py`; measurements and its SVG/PNG
are in that directory. No full regression run is warranted for this
proof-only review.

Implementation should correct y's DotBelow attachment anchor before
composites are rebuilt, in both italic weights. It should derive the
placement from the final weighted base and mark, so precomposed and
combining text agree. Updating only the ỵ component would leave decomposed
text broken. Account for y-related composites carrying that anchor and
review all resulting shaping differences before updating baselines.

Next: judge the beside-descender trial in the proof, then implement the
anchor correction and run reproduction, shaping and outline comparisons.
