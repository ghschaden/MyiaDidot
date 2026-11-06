# Italic extended Latin small caps

Scope: the next 46 unaccepted Italic small-cap drafts reached from extended
Latin characters, including ligatures, ogoneks, barred letters and hooked
capitals. The exact list and outline fingerprints are in
`build/glyph-review/italic-smallcaps-extended-latin/glyphs.txt` and
`checks.json`. Basic a.sc–z.sc were accepted separately; Greek, Cyrillic
and remaining phonetic forms are outside this batch.

Initial recommendation withdrawn for uni0280.sc, uni0253.sc and uni0257.sc
after the person's closer review. Those three required correction; the
initial batch was not accepted. See the resolution and focused findings below. Both pages of
`review.pdf` were rendered and inspected.

Subsequent resolution: those three Italic glyphs were repaired and
approved on 2026-11-06, including cleanup of the two hook stems. See
[small-cap repairs](italic-smallcap-repairs-2026-11-06.md). The other
43 glyphs in this batch were subsequently approved unchanged on 2026-11-06.

After commit `6e0fba21` was pushed to main, the remaining 43 were given
a refreshed two-page sheet:
`build/glyph-review/italic-smallcaps-extended-latin-remaining/review.pdf`
(rendered as `review-1.png` and `review-2.png` alongside). Both refreshed
pages were visually inspected. Their fingerprints match the original
43 drawings exactly; no sources changed for this refresh. All 86 smcp/c2sc
checks pass, and outline lint has no findings. The three corrected,
accepted forms are excluded. The person approved this remaining batch
unchanged; all 43 acceptance fingerprints are recorded in the Italic UFO.
The accepted sheet is retained as
`proofs/italic-smallcaps-extended-latin-2026-11-06.pdf`.
The sheet shows the full capital, small cap and lowercase at the same em
scale, with baseline/x-height/small-cap/cap-height guides, then n/small-cap/n
and H/small-cap/H contexts. Hook counters remain open, the bars remain
distinct, and ogoneks remain attached and legible in these specimens.
The initial inspection missed a broken bowl in uni0280.sc and did not
adequately compare the two left hooks with their uppercase equivalents.

Proof: `build/glyph-review/italic-smallcaps-extended-latin/review.pdf`.
The final pages are also `balanced-1.png` and `balanced-2.png`. Specimens
are 38 pt in four columns, with an explicit break after six rows to keep
the wide letters separated and the last rows clear of the page edge.
The header has a small TeX overfull-box warning but is visibly complete;
there are no missing-character warnings or specimen-cell overflow warnings.

The proof uses `scripts/smallcap_review.py` and a font compiled from the
complete current Italic source. `selection.ufo` is a scratch copy with
other small caps removed only to select the cells. No production outlines,
features, spacing or baselines were changed.

Checks:

- 92 explicit HarfBuzz mappings pass: lowercase smcp and uppercase c2sc
  reach the expected glyphs (`script=latn`, `language=en`). Exact inputs,
  glyphs, advances and offsets are recorded in `checks.json`.
- Outline lint has no findings in any of the 46 glyphs.
- The preceding approval of a.sc–z.sc is recorded, normalized and checked:
  the acceptance suite passes all 10 tests.
- This is an outline/shaping review, not a pixel-hinting review.

Batch names:

```
ae.sc aogonek.sc aringacute.sc eng.sc eogonek.sc eth.sc florin.sc
germandbls.sc hbar.sc iogonek.sc lslash.sc oe.sc oogonek.sc oslash.sc
tbar.sc thorn.sc uni0199.sc uni019A.sc uni01A5.sc uni01B4.sc uni01B9.sc
uni01DD.sc uni01E5.sc uni023C.sc uni0242.sc uni0249.sc uni024D.sc
uni0253.sc uni0254.sc uni0257.sc uni025B.sc uni0263.sc uni0268.sc
uni0269.sc uni026F.sc uni0272.sc uni0280.sc uni0288.sc uni0289.sc
uni028A.sc uni028B.sc uni028C.sc uni0292.sc uni2C65.sc uni2C66.sc uogonek.sc
```

All 46 Italic small caps in this batch are accepted: the three corrected
forms separately, and the remaining 43 unchanged from the refreshed sheet.

## Follow-up: three glyphs sent back

The person identified uni0280.sc's defect and questioned the large, low
hooks of uni0253.sc and uni0257.sc. The focused source proofs confirm both
concerns. No production drawings were changed during this investigation.

Evidence: `build/glyph-review/italic-extended-queries/r.png`, `hooks.png`
and `matched-height.png` (standalone SVGs alongside). Measurements are
in `measurements.json`. In the matched-height proof the left column is
each capital uniformly scaled by 1040/1434 as a comparison reference,
not a proposed finished drawing. The right column is the current small
cap. All three proofs were visually inspected.

- **uni0280.sc:** the bowl is visibly torn and the lower leg detached.
  It consists of two outer contours (signed areas −338046 and −87929),
  not an outer contour and a counter. The `lower` recipe cuts everything
  right of the first run measured at y=500 and moves it down 145 units.
  On r.sc that run includes the bowl's crossbar: the cut is at x=692.4,
  whereas the stem's right edge measured below the crossbar is about
  x=393. The cut therefore bisects the bowl. Recommendation: reconstruct
  locally from the final r.sc with a cut at the actual stem, keeping the
  lowered bowl and leg connected, and compare with the final capital Ʀ.
- **uni0253.sc and uni0257.sc:** the capitals Ɓ/Ɗ use the Italic's drawn
  curl recipe; the small caps still use the generic hook recipe, which
  grafts f's top scaled to the stem. Their upright left overhangs from
  the stem are about 562/553 units, versus 397 on the full capitals,
  even before accounting for the smaller case height. Their left hook
  portions descend to y=549/576, about 53–55% of small-cap height,
  against y=1177 (82% of cap height) for the capitals. Recommendation:
  use compact curls matching the capitals' construction and relative
  placement, drawn on the final b.sc/d.sc at their own stroke weight.

HarfBuzz c2sc maps Ʀ/Ɓ/Ɗ to exactly these three glyphs, confirming that the
defects concern the actual small-cap forms, not a wrong proof character.
The earlier clean outline lint did not detect the broken construction;
it is not evidence that the drawing is sound.
