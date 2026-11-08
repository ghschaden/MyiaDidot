# Bold Italic basic Latin small caps

Reference: `7eb071e0`. Current-design review of a.sc–z.sc; no drawings,
spacing, baselines or acceptance records changed. Of the 26 forms, c.sc
and g.sc are already accepted and are included as references; the other
24 await the review.

Proof: `build/glyph-review/bold-italic-smallcaps-latin/review.pdf`, two
pages. Both pages were rendered as `review-1.png` and `review-2.png` and
visually inspected. Each cell shows capital, small cap and lowercase at
the same em scale over height guides, then n/H text-size contexts. Drafts
come first; the two accepted forms appear at the end of page two.
No broken construction is apparent in these specimens. N/n.sc's stem
brackets and Q/q.sc's small tail loop merit close inspection. No redraw
is proposed from this initial inspection.

All 52 explicit smcp/c2sc mappings pass using a font compiled from the
complete current Bold Italic source (`script=latn`, `language=en`).
Outline lint reports no findings. Exact names, fingerprints and shaping
records are in `glyphs.txt` and `checks.json` alongside the proof.
`prepare.py` repeats preparation; the selection UFO only selects proof
cells, while compilation uses the complete source. Minor TeX overflow
warnings do not obscure specimens or labels. This is an outline/shaping
review, not a screen-hinting review. No full test rerun was needed for
proof generation alone.

## Approval and three local repairs

The review approved the other forms, sent back b.sc and q.sc for their
upper counters, and then identified narrowing before the stem serifs of
b.sc and d.sc. d.sc's initial acceptance was withdrawn for that repair.
The final three revisions were approved on 2026-11-06. All 26 basic
Latin small caps are now accepted: 21 newly approved unchanged, the three
repaired forms, and the previously accepted c.sc/g.sc references.

`scripts/bold_italic_b_q_smallcaps.py` makes local drawings in Bold Italic:

- b.sc's upper counter takes the round side of its lower counter, fitted
  to the upper box. Its stem sides now run straight at the existing main
  weight into single rounded brackets at head and foot.
- d.sc receives the same local straight-stem and serif-bracket treatment.
  Both letters' brackets widen out to the serif rather than pinching in
  before it. Across y=110–925 their widths remain within one unit of
  310 (b.sc) and 307 (d.sc) in the upright frame.
- q.sc's upper counter arc takes the approved o.sc's upper oval, fitted
  separately on each side to preserve Q's lower endpoints. Its tangent
  directions into the lower counter are retained; the outside, tail and
  small lower loop remain exactly unchanged.

The approved focused proof is retained as
`proofs/bold-italic-b-d-q-smallcap-repairs-2026-11-06.svg`. The original
sheet is retained as `proofs/bold-italic-smallcaps-latin-partial-2026-11-06.pdf`.
Before sources and intermediate/final candidate proofs are under
`build/glyph-review/bold-italic-b-q-smallcaps/`. `revised.svg`/`revised.png`
were visually inspected, including enlarged forms and compiled English
c2sc text. Installed drawings are marked drawn, with fingerprints of
their Italic source letters, and their acceptance records are stamped.

`checks-revised.json` records the three direct edits and their ten
component dependants (B/Ve aliases, accented B/D small caps and IPA ᴅ).
All affected forms pass outline lint; b.sc/d.sc/q.sc have no construction
findings. All advances, anchors, features, kerning and groups are retained.
Six explicit Latin smcp/c2sc mappings pass, as do four accented NFC/NFD
comparisons. All existing accepted fingerprints remain valid. Normalization
completed; full validation is run after installation. These are source
outline and shaping proofs, not hinting proofs. No baselines changed.

Final integration rebuilds the barred-D small cap on the corrected d.sc,
with local whole-unit join finishing recorded by
`--finish-barred-d` in the repair script. Its saved same-style base hash
and a four-height stem/bowl comparison guard against a stale derivative.
