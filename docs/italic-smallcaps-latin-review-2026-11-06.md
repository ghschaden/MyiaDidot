# Italic basic Latin small caps

Scope: a.sc–z.sc, 26 glyphs in `sources/MyiaDidot-Italic.ufo`. This is
the first batch of the outstanding Italic small-cap review, not approval
of the extended Latin, Greek or Cyrillic small caps. Reference:
`3d692354` plus the subsequently approved G-hook drawings and a.ipa
acceptance metadata; neither changes these 26 drawings.

The person accepted all 26 drawings unchanged on 2026-11-06. Acceptance
fingerprints are recorded in the Italic UFO. The one-page sheet shows each full capital, small
capital and lowercase at the same em scale, with baseline, x-height,
small-cap and cap-height guides, then n/small-cap/n and H/small-cap/H
contexts. No clipping, closed counters or obvious joins requiring a
redraw were visible. The small-cap proportions and stroke contrast read
consistently with their same-style capitals and lowercase comparisons.

Evidence under `build/glyph-review/italic-smallcaps-latin/`:

- `review.pdf` / `review.png`: the inspected 26-letter sheet.
- `words.svg` / `words.png`: compiled English text with smcp and c2sc,
  including a pangram and h.sc/n.sc/o.sc outline comparisons.
- `checks.json`: exact source fingerprints, lint and shaping records.

The sheet uses `scripts/smallcap_review.py` and a font compiled from the
actual current Italic UFO. Its `selection.ufo` is a scratch copy with
the other small caps removed only to select the 26 cells for the sheet;
the compiled font uses the complete production source. No source drawing,
feature, spacing or baseline changes were made.

All 26 lowercase letters map to the expected glyph with smcp, and all 26
uppercase letters map to the same expected glyph with c2sc: 52 explicit
HarfBuzz checks pass (`script=latn`, `language=en`). Outline lint has no
findings for any of the 26 glyphs. These are outline and shaping proofs,
not a screen-hinting review.

The preceding a.ipa approval was recorded in all four styles, normalized,
and checked with the acceptance suite: 10 tests pass.

Accepted proofs are retained as `proofs/italic-smallcaps-latin-2026-11-06.pdf`
and `proofs/italic-smallcaps-latin-words-2026-11-06.svg`. Work complete.
After stamping and normalization, the acceptance suite passes all 10 tests.
