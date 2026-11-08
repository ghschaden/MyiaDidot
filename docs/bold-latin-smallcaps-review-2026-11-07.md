# Bold basic Latin small caps

Reference: 26eca0dd170ff7bae3c7f28cbe1d0ba5727132c4. The review approved
25 forms from a.sc through z.sc unchanged on 2026-11-07, requesting a
little more white space inside j.sc's bottom hook. That request concerns
the drawing, not the vertical layout of the proof.

The other 25 acceptances are recorded with their reviewed fingerprints.
A later review approved the j.sc proposal. All 26 forms are now
accepted, with j.sc marked drawn against its Regular source fingerprint.
The original one-page A4 proof and all 26
fingerprints are under build/glyph-review/bold-smallcaps-latin-2026-11-07/.
All 52 explicit smcp/c2sc mappings pass (Latin, English), and outline lint
has no findings in this batch. The proof was rendered and visually inspected.
These are compiled outline/shaping specimens, not a screen-hinting review.

The focused j.sc proposal follows the same-style full J's inside curves,
mapped to the small cap's existing inner stem and terminal height. This
opens the narrow gap beside the terminal and slightly lowers the inside
floor, while preserving the original outside points, advance and anchors.
Candidate and focused evidence are in the same scratch directory. The
proposal was visually approved and installed, followed by whole-style
Bold regeneration so its component and derived dependants follow it.
The approved focused proof is retained at
[Bold J small-cap hook](../proofs/bold-j-smallcap-hook-2026-11-07.pdf).
Regeneration retains the approved J exactly. Its six component/alias forms
follow automatically; uni0249.sc is also rebuilt from the final j.sc and
is included, still unaccepted, in the next extended Latin review batch.
No other outlines change, and all 26 accepted fingerprints remain valid.

Final installation audit: the barred J derived from j.sc (uni0249.sc)
keeps a drawn local copy tied to its Regular source. Its generated hook
had a two-unit side jog and a small tangent reversal; the jog is aligned
and one handle lowered two units. Bounds and advance are unchanged. The
cleanup is shown in proofs/bold-final-outline-cleanup-2026-11-08.pdf; its
appearance was checked against the approved form. Its approval record is
refreshed to the cleaned installed geometry.
