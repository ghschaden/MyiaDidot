# IPA a review

Reference: `3d692354`, plus the approved Bold Italic G-hook drawings (which
do not affect this review). Scope: `a.ipa` in Regular, Italic, Bold and
Bold Italic, compared with each style's `a`, `uni0251` (ɑ), `n` and `o`.
No drawings changed. The person accepted a.ipa in all four styles on
2026-11-06; the acceptance fingerprints are recorded in the UFOs.

Decision: retain the current drawings, as accepted by the person.
The Roman styles' a.ipa is an exact component alias
of their ordinary two-storey a, with the same advance. In both italics,
a.ipa is the sloped Roman two-storey form; ordinary a and ɑ use the
single-storey Italic design. The two-storey a is visibly distinct from ɑ
at enlarged and text sizes. The reviewed words show no closure or
collision that warrants a local redraw. The Roman source's top at 900
is 16 units above the Italic n/o top at 884; this small difference does
not alone justify changing the drawing.

Inspected proofs (standalone SVGs and rendered PNGs):

- `build/glyph-review/ipa-a/roman.svg` / `roman.png`: Regular beside Bold.
- `build/glyph-review/ipa-a/italic.svg` / `italic.png`: Italic beside Bold
  Italic. The renderer's “Before” and “Current” columns here denote the
  two styles, not a proposed change.

Direct glyph rows show a, a.ipa, ɑ, n and o. Text rows are compiled and
HarfBuzz-shaped with explicit `script=latn`, `language=und-fonipa`:
`sat sɑt ɐ æ á ā̃ ǻ` and `mana mɑnɑ panɑ paɲa`. They are source-outline
and shaping proofs, not pixel-hinting proofs.

Checks: `build/glyph-review/ipa-a/checks.json` contains the source
fingerprints, bounds, advances, lint and exact shaping records.

- In each style, English `a` maps to `a`; IPA `a` maps to `a.ipa`;
  IPA `ɑ` maps to `uni0251`.
- All 25 encoded accented lowercase a forms in each style use a.ipa in
  IPA mode and produce exactly the same glyphs, advances and offsets as
  their NFD sequences: 100 comparisons pass across four styles.
- Outline lint has no findings for a, a.ipa or ɑ in any style.
- Acceptance fingerprints remain valid in all four styles. After
  recording the approved G hooks, the focused acceptance suite passes
  (10 tests); the preceding complete suite passed 362 tests, with 7
  skipped. No baselines changed for this review.

Accepted proofs are retained as `proofs/ipa-a-roman-2026-11-06.svg` and
`proofs/ipa-a-italic-2026-11-06.svg`. Work complete.
