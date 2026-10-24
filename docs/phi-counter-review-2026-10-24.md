# Bold Italic ɸ counter cusps reviewed, 2026-10-24

[Current Italic/Bold Italic comparison](../proofs/phi-counter-review-2026-10-24.pdf).

The two glyph-lint flags are at the tapered ends of the counters where
the central stem intersects the bowl: 448,696 (100 pixels) and 569,233
(54 pixels). They are not exterior attachment steps or residual enclosed
pinholes. The light Italic has the same o-plus-stem construction and no
lint findings; Bold, Regular and Italic ɸ are all clean. In Bold Italic,
the heavier stem and bowl leave very narrow counters.

A scratch reconstruction from the current Bold Italic o and a central
stem measured from l still produces two notch findings (72 and 83 pixels).
It therefore does not resolve the lint task and was not applied. The
trial exists only in `build/phi-review/Trial.ufo` and `trial.py`.

Recommendation for this lint pass: retain the two counter cusps rather
than fill or arbitrarily cut them. Widening the counters would require
an optical weight/drawing decision about the stem or bowl. The existing
`uni0278 style` quality finding and the overall weight of this drawing
remain open; this review does not resolve those or record user acceptance.

No font, generator, metric, layout or shaping-baseline changes are made
for ɸ. Refreshed only the historical lint annotation's measurements.
Validation is focused lint in all four masters, inspection of current
outlines and the comparison proof, and the discarded reconstruction
experiment. No tests were added for this review.

Next unreviewed Bold Italic glyph-lint entry: ɽ (`uni027D`).
