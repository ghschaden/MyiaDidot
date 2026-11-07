# Bold Italic extended Latin drafts

The person reviewed 39 extended Latin drafts, approved 37 unchanged, then
approved reconstructed uni0187 and uni0188 on 2026-11-08. All 39 now carry
acceptance records in production. The two local drawings are marked drawn
and tied to their Italic source fingerprints.

Capital Ƈ's hook continues from the final same-style C's right-hand edge,
without the earlier thickening in the stem. Lowercase ƈ keeps the complete
final same-style c, including its terminal; the original hook is slightly
thickened and attached at the terminal's outer edge. Its inner arc gains
12 units of thickness. Advances, anchors, features and kerning are retained.
The hook overhangs grow; the smaller-size repeated specimens were reviewed
with the drawings. Only these two glyph objects were changed in the local
proposal; approved unrelated drawings remain fixed.

Retained proofs:

- proofs/bold-italic-c-hook-capital-2026-11-08.pdf: capital's approved version
  is on the right. Its lowercase is superseded by the next proof.
- proofs/bold-italic-c-hook-lowercase-2026-11-08.pdf: final approved lowercase,
  with the unchanged same-style c as reference.

Scratch before/candidate/installed snapshots and checks are under
build/glyph-review/bold-italic-c-hooks-2026-11-08/.
The original 39-form sheet and fingerprints are under
build/glyph-review/bold-italic-extended-latin-drafts-2026-11-07/.
All 39 direct latn/en shaping checks passed. Both repaired outlines pass
lint. The person also approved the existing small step in uni0198 and the
notch in uni023A; no exception lists were enlarged for those findings.
Source-outline proofs were visually inspected; they do not establish
hinted rendering quality.

For reference, comparison.pdf under
build/glyph-review/bold-italic-c-hook-references-2026-11-08/ shows actual
Charis SIL 6.200 Bold Italic and Libertinus Serif 7.051 Semibold Italic at
matched x-height. Installed Libertinus 7.051 Bold Italic lacks U+0188.
Both references retain c's terminal and add a compact hook nearby; that
comparison informed the final full-c construction.

Final installation cleanup aligns two control handles at Ƈ's hook
attachment (5 and 3 units respectively) to eliminate tiny tangent breaks.
The approved design, bounds and advance are retained. Before/after proof:
proofs/bold-final-outline-cleanup-2026-11-08.pdf.
