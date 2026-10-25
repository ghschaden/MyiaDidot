# Roman ṫ dot spacing review, 2026-10-25

[Comparison proof](../proofs/roman-t-dot-spacing-review-2026-10-25.pdf)
shows current and proposed Regular/Bold drawings enlarged and at three
text sizes. The proposal raises only ṫ's dot component by 59 units,
matching the clearance above ż in each weight.

| Style | Current gap | Proposed gap | Vertical shift |
|---|---:|---:|---:|
| Regular | 139 | 198 | +59 |
| Bold | 135 | 194 | +59 |

The existing tighter gap is inherited from the Roman placement. Matching
ż gives a more even separation without altering t or the dot drawing.
The person approved the proposal and requested continuation on 2026-10-25.
The Regular master now has the higher dot and corrected Dotaccent anchors
on t and its five below-mark composites; Bold inherits these through its
normal generator. Exactly seven glyph objects change per Roman style;
only ṫ changes visible ink.

`scripts/roman_t_dot_review.py` reproduces the proof, scratch UFOs and
measurements in `build/roman-t-dot-review/`. The script checks that the
advance stays exact and the composite top moves by the intended amount.
The PNG has been inspected for clipping and placement; Ruff passes.
The proof generator pins its before-state to `7b2a1117`, retaining a
reproducible comparison after integration.

The italic generator compensates for the Roman anchor change at its
existing anchor-nudge stage. This preserves the reviewed hooked/tailed-t
recipe anchors; plain italic t continues to use its independent clearance
repair. No italic master changes are required.

Both Roman corpus comparisons shape 2,119,788 strings. Exactly ten strings
per weight change, all positions only: an added dot above a t with a below
mark moves up 59 units. Glyph selection and advances match. The two
full-corpus digests record those reviewed differences; golden cases stay.
The two obsolete ṫ accent-gap quality entries are removed, with no new
exceptions. Compiled cmap, hmtx, GSUB, GDEF, OS/2, hhea and name tables
match; the only changed CFF charstring is ṫ. GPOS changes are the intended
dot-anchor heights. Regular/Bold OTF, TTF and WOFF2 rebuild successfully.
All three generated styles reproduce exactly after the generator adjustment.
All four CFF hinting checks pass with helper-socket access.
The 49 focused checks cover composites, quality/lint, shaping and hinting.
The first sandboxed run had 44 passes, one stale Bold quality entry and
four blocked CFF helper sockets. After removing the stale entries, the
quality/t-dot rerun has nine passes and the CFF rerun has four passes.
Ruff and whitespace checks pass.
The final Roman composite/quality/lint/t-dot selection passes all 14 checks.

Validation logs and compiled/shaping comparisons are in
`build/roman-t-dot-review/`. Final validation results are recorded in TODO.md.

The commit-time suite also found four stale `builtFrom` fingerprints on
Regular ƭ/ʈ/ᵵ/ⱦ. Undoing only t's approved +59 Dotaccent move reproduces
each recorded fingerprint exactly. These derivatives retain their reviewed
1241-height dot anchors and unchanged drawings; refresh only their t
fingerprints. All nine built-from/alias checks pass after that metadata fix.
