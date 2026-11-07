# Bold Greek small caps

The person approved 16 unchanged Greek small caps and the regenerated
Latin capital upsilon (uni01B1), then approved the rounder lowercase theta
and stronger koppa capital/small cap (uni03DE and uni03DF.sc).
All 17 Greek small caps in this batch are now approved (2026-11-07).

Theta keeps its exterior and crossbar; both counters now follow one smooth
oval. Koppa keeps its horizontals and serifs, with thicker main diagonals.
All three repaired glyphs retain their advances and bounds and pass outline
lint. No other decomposed glyphs change in the proposal. The original sheet's
57 grek/el smcp/c2sc mappings passed. These are source-outline proofs, not
hinted-rendering checks.

Retained proof: proofs/bold-theta-koppa-2026-11-07.pdf.
Before/candidate/installed snapshots and checks are under
build/glyph-review/bold-greek-theta-koppa-2026-11-07/.

Whole Bold regeneration, small-cap rebuilding and normalization preserve
the installed font exactly: no outline or advance changes and no stale
acceptances. Acceptance and drawn-preservation tests pass (12 tests).

Final installation cleanup splits theta's new inner oval at its extrema
and rounds it to whole units. The approved shape, exterior, bar, bounds
and advance are retained. Before/after proof:
proofs/bold-final-outline-cleanup-2026-11-08.pdf.
