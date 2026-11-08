# Bold Italic hooked-b small-cap upper counter

The review approved uni0257.sc and requested the inside of uni0253.sc's
upper loop a little rounder, like its lower loop. Only uni0253.sc's upper
counter is redrawn. The review approved it on 2026-11-06, and its
acceptance fingerprint is recorded in the Bold Italic UFO.

`scripts/italic_smallcap_repairs.py --round-b-counter` fits the round side
of the lower counter into the previous upper counter's bounding box.
The upper counter's left stem edge and head bracket stay in place. The
new side has two cubic curves derived from the lower loop rather than
the old flatter, more angular sequence. Its area increases from 113679.6
to 119203.2 square units (about 4.9%).

The outside contour and lower counter remain exactly unchanged, including
their point data. The advance is unchanged. The approved uni0257.sc is
unchanged and its acceptance fingerprint remains valid.

Evidence: `build/glyph-review/bold-italic-b-upper-counter/` contains
`before.ufo`, the trial `candidate.svg`/`candidate.png`, and the installed
`final.svg`/`final.png`. Both trial and final were visually inspected,
enlarged and at text size. Text is compiled and HarfBuzz-shaped with
explicit English/Latin and c2sc: nƁn, HƁH and ƁƁƁ. These are outline and
shaping proofs, not screen-hinting proofs.

`scope.json` records that only uni0253.sc changed geometrically; the outer
contour, lower counter, advance and approved uni0257.sc are unchanged.
Outline lint and construction checks have no findings; Ruff passes.
All 11 focused checks pass: the six local regression cases, Bold Italic
quality, acceptance, golden shaping, and TTF/CFF hint-zone checks.
`make reproduce` reports Italic, Bold and Bold Italic **as generated**.
No baselines are updated for this drawing.

Accepted evidence is retained as
`proofs/bold-italic-b-upper-counter-2026-11-06.svg`. Work complete.
