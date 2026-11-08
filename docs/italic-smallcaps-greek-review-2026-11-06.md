# Italic Greek small caps

Reference: `f471c107`, with the subsequently approved Latin/phonetic
small-cap acceptance records. No outlines changed. Acceptance of this
Greek batch was partially approved on 2026-11-06: all 14 forms except
delta.sc, lambda.sc and theta.sc are accepted unchanged. Their acceptance
fingerprints are recorded in the Italic UFO. The reviewed sheet is retained
as `proofs/italic-smallcaps-greek-partial-2026-11-06.pdf`.

The batch contains 17 remaining unaccepted small caps reached from Greek
characters, including archaic forms. omega.sc was already reviewed and
approved in the Latin/phonetic batch, so it is excluded here. Names and
fingerprints are in `build/glyph-review/italic-smallcaps-greek/glyphs.txt`
and `checks.json`. `prepare.py` repeats the preparation.

Proof: `build/glyph-review/italic-smallcaps-greek/review.pdf`, one page,
rendered as `review.png` and visually inspected. Each cell shows capital,
small cap and lowercase over height guides, followed by text-size n/H
contexts. The bowls and strokes appear connected in these specimens;
archaic forms and the short bars of xi.sc warrant the closer
inspection beside their capitals. No redraw is proposed from this initial
inspection. Minor TeX overflow warnings do not obscure specimens or labels.

All 57 smcp/c2sc mappings pass with explicit `script=grek`, `language=el`
using the font compiled from the complete current Italic source. Outline
lint reports no findings for this batch. The scratch selection UFO only
selects cells; it is not the compiled font's source. This is an outline
and shaping proof, not a screen-hinting review. No Greek acceptance records,
outlines, spacing or baselines changed during the initial review.

## Three forms sent back

The review found delta.sc and lambda.sc more slanted than their capitals
and theta.sc's inside unround. The two diagonal forms now have a local
candidate mapping both long outside diagonals to their capitals' exact
directions; after integer rounding the slopes differ by less than 0.001.
Their heights and advances stay fixed. theta.sc's counter is reconstructed
from the approved o.sc counter, translated eight units right to align with
its bowl, and divided by the existing crossbar at y=486–548. Its outer
contour is retained exactly.

Candidate script: `scripts/italic_greek_smallcap_repairs.py`. Actual before
sources are saved in `build/glyph-review/italic-greek-repairs/before.ufo`.
The candidate is `candidate.ufo` alongside. It marks the three drawings as
drawn, so the Italic generator will preserve them upon installation.
No shared generator settings changed.

The focused before/after proof `review.svg` (rendered as `review.png` in
the same directory) was visually inspected. It includes the full capitals,
the three small caps, o.sc, text-size repeats and compiled Greek smcp text.
Checks in `checks.json` confirm only these three outlines differ, all
advances and accepted fingerprints are retained, features/kerning/groups
are unchanged, lint is clear, and six explicit Greek smcp/c2sc mappings
pass. This remains an outline/shaping proof, not a hinting proof.

A later review approved all three repairs on 2026-11-06. They
are installed in the Italic, marked drawn and accepted; all 17 forms in
this Greek batch are now accepted. The focused approved proof is retained
as `proofs/italic-greek-smallcap-repairs-2026-11-06.svg`.

Bold Italic was regenerated as a whole, followed by smallcaps.py. Only the
same three glyphs changed geometrically; no kerning or feature changes.
The generator changed delta.sc's advance by +1 and lambda.sc's by -2;
their existing advances are retained via the script's
`--finish-bold-italic BEFORE.ufo` option and drawn marks tied to the final
Italic source fingerprints. Bold Italic acceptance is a separate review.
Normalization completed. Full test and reproduction results follow below.

The first full test run passed 368 tests, skipped 7, and found fractional
anchors in the two transformed diagonals, plus theta.sc's kink count
falling from three to two. Anchors are now rounded to whole units and the
existing theta.sc kink exception shrank to two (the preserved outside's
joins). The approved outlines were not changed. The initial reproduction
run overlapped the anchor correction and reported those two anchor
differences; both gates were restarted on the final normalized sources.
The completed rerun passed **369 tests, 7 skipped**. `make reproduce`
reported Italic, Bold and Bold Italic **as generated**.
