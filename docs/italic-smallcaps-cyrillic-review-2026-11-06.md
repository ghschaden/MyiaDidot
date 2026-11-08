# Italic Cyrillic small caps

Reference: `f471c107` with approved Latin/phonetic and Greek small-cap
reviews integrated. This batch contains the remaining 40 unaccepted
Italic small-cap drafts, all Cyrillic. The review approved 39 unchanged
and sent back uni044E.sc on 2026-11-06. Those 39 acceptance fingerprints
are recorded in the Italic UFO. The reviewed sheet is retained as
`proofs/italic-smallcaps-cyrillic-partial-2026-11-06.pdf`.

Proof: `build/glyph-review/italic-smallcaps-cyrillic/review.pdf`, two
pages of 20 forms. Both pages were rendered as `review-1.png` and
`review-2.png` and visually inspected. Each cell shows capital, small cap
and lowercase at the same em scale over height guides, then n/H text-size
contexts. The main letters, extended Cyrillic, historical forms and
descender variants are included. No broken construction is apparent in
these specimens. Barred round forms such as uni0473.sc and uni04E9.sc
merit close inspection beside their capitals after the Greek theta.sc
counter repair. No redraw is proposed before the review.

`glyphs.txt` and `checks.json` in the proof directory contain the exact
names, fingerprints, lint and mappings. All 80 explicit smcp/c2sc mappings
pass using the complete compiled Italic source with `script=cyrl`,
`language=ru`; outline lint reports no findings. The selection UFO selects
proof cells only. This is an outline/shaping proof, not a screen-hinting
review. Minor TeX overflow warnings do not obscure labels or specimens.
The proof has an explicit page break after five rows.

## Ю.sc sent back

The review found the bowl lighter than the stem, the stem too fat and
a small bump on the bowl's lower-right side. Upright horizontal cuts
confirm a 200–205-unit stem against sides around 150–175 units.

`scripts/italic_yu_smallcap_repair.py` makes a review candidate from the
approved final i.sc and o.sc at their own weight. The bowl stays at the
previous right edge; its side joins have aligned tangents, retaining their
endpoints. A 62-unit connector joins the stem and bowl at the old bar's
height. The original advance and anchors are retained. No shared drawing
or weighting settings change.

Before and candidate UFOs are in `build/glyph-review/italic-yu-repair/`.
The focused `review.svg`, rendered as `review.png`, was visually inspected:
uppercase Ю, small-cap Ю, i.sc and o.sc, plus text-size repeats and compiled
Russian smcp text. The revised stem is lighter and the bowl fuller; the
lower-right side runs smoothly through its former corner.

`checks.json` confirms only uni044E.sc differs geometrically; all advances,
features, kerning, groups and accepted fingerprints are retained. Both
explicit Cyrillic smcp/c2sc mappings pass, and outline lint reports no
findings. The review approved the revision on 2026-11-06. It is installed
in the Italic, marked drawn and accepted; all 40 forms in this batch and
all remaining Italic small-cap drafts are now accepted. The approved proof
is retained as `proofs/italic-yu-smallcap-repair-2026-11-06.svg`.

During finalization, a short head-bracket handle inherited from i.sc was
aligned to the stem by one unit to remove its rounding kink. The old
Ю.sc extreme and two kink exceptions are removed. No exceptions were
added. Bold Italic is regenerated as a whole before the commit gates;
the mandatory pre-commit gates validate tests and reproduction on the
complete staged source state. No shaping or hinting baselines change.

Final installed proofs `final.svg` and `bold-final.svg` in the scratch
directory were rendered and inspected after normalization. The retained
Italic proof reflects the one-unit bracket alignment. `final-scope.json`
confirms that across this review only delta.sc, lambda.sc, theta.sc and
uni044E.sc differ geometrically in each italic weight. All advances,
kerning and features are unchanged, all accepted fingerprints are valid,
and no unaccepted Italic small-cap drafts remain. Ю.sc has no construction
findings in either italic weight. Bold Italic's previous advance is
retained with a drawn mark tied to the final Italic source fingerprint.
Source synchronization and whitespace checks pass.
