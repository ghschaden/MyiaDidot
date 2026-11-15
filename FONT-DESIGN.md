# Open font-design work

Open items only; consolidated 2026-11-15. The finished work, with its
evidence and verdicts, is in [FONTLOG.txt](FONTLOG.txt) (the design record
of 2026-10-26 to 2026-11-10 that stood here is its last section,
"Appendix: the design record"); detailed evidence stays in `docs/` and
`proofs/`. Tooling and publication tasks belong in
[DEVELOPMENT.md](DEVELOPMENT.md), the plan in [TODO.md](TODO.md).
A diagnostic finding is a candidate for review, not proof of a design fault.
The exception files in `tests/data/` are the current inventories; do not copy
counts here, where they quickly become stale. Every entry in
`hint-zones*.txt` and `glyph-lint-*.txt` carries a dated verdict; reopen one
only on new evidence (a raster or a proof).

## Construction and optical quality

- Italic ※ ⁜ ⸓ ⸖: their dots still differ within a glyph (216 x 201-219),
  and take the accent dot (248), not the period's (256).
- Bold Italic ⱳ.sc (emboldened from the Italic's draft): kinks and a
  wobble at the curl (`quality-BoldItalic.txt`).
- Bold Italic wobbles (checks.py `wobble`, about 190 glyphs after the
  strokes): shortening the handles at the curves' joins would take out
  more, but changes Ⱳ's approved curl; not done. The Bold's remaining
  wobbles (about 80 glyphs) bend back across a node between two curves,
  which keep_bends does not see.
- Bold Italic's stroker, left as faults for later: k's hook where arm meets
  leg, z's bottom-left curl; arcs holding the cleaning's leftovers
  (1-unit cubics, a handle doubling back: d k r z); capital serif curves
  over 120 units, refused by the fairing. See `docs/claude/stroking.md`.
- Bold Italic: still to try the Bold's two other repairs (make_bold:
  keep_smooth for the rounder way, runs_on by weight). Tried, they smooth
  § 3 ₵ ø.sc Θ ẞ but add side space (3 +21, § +13), notch ẞ, move ɽ's
  advance and ƙ.sc's CFF top, and runs_on kinks ð ɨ ђ ћ љ ˁ: each needs
  review before they are switched on.
- Bold Italic ᵘ ⁿ: refused by the gate (made small, n's arch crotch is a
  notch at that size), keep their 32 degree corner. Still to decide
  whether г's inner curves (upright from the stroking itself; s з 3 2
  alike) should be rounder. Bold Italic n.sc and ɴ keep small wobbles
  where their brackets meet the stems.
- Step candidates (checks.py `step`, `tests/data/quality-*.txt`): the rest
  still marked "a candidate to review" (₿ ǥ ɉ bar ends, ₡ ₹ ₮, ꞁ ɑ.sc
  ⱦ.sc ...). From the sheets of 2026-11-09, whose fixes are not recorded
  as done: Regular 𝑙 (U+1D459) to smooth; ɉ's bar too short on the right;
  ɝ's hook badly attached; Italic Ⱦ not flat on top; ₮'s bars too short on
  the right, off centre; ⱦ.sc a step on top. Bold: ɉ's bar off centre; 𝑙
  to smooth; ǥ's bar too short; ₿'s bars unequal. Bold Italic: 𝑙 to
  smooth. (𝑙: draft_letterlike.py italic_l.) Check each against the
  current glyph before drawing.
- Bold: the hooks' inner corners (J ȷ ɽ ɳ, Œ) turned a little tighter by
  stem_handles; the middle tildes (ᵬ-ᵳ), drawn on the Bold's own base,
  likely lighter than emboldened: both to review.
- Bold serifs: Bold ɫ.sc's top serif has a 1-unit end face; at hairline
  stems (N M U) the Bold's serifs reach 250 against 196 (seen and settled
  2026-11-09; reopen on a proof).
- Derived letters still emboldened whole
  (`tests/data/emboldened-whole-*.txt`): each has a reviewed reason in
  BOLD_KEEP_WHOLE / ITALIC_BOLD_KEEP_WHOLE; what is left needs a recipe
  drawn at the style's weight (BOLD_RECIPES, ITALIC_BOLD_RECIPES) or a
  landmark-placed cut, letter by letter.
- Work through `tests/data/quality-*.txt`: extrema, kinks, smooth joins,
  stroke weight, zones, slant, width and accent gaps (T9 and phase 6 give
  the entries a status). Many italic findings are inherited from Old
  Standard and propagate to Bold Italic. Keep broad contour cleanup
  separate from individual drawing changes and inspect `make diffenator`
  results. W-family diagonal slant and i/j dot gaps can be intentional.
  Extremes more than about 20 units past remain in Bold Ʒ ℓ, Bold Italic
  ѫ ® л @.
- Drafts: none unaccepted in any style (`scripts/accepted.py UFO
  --drafts`); acceptance is recorded with accepted.py, not by clearing
  draft flags (docs/claude/quality.md). New drafts go through the same
  sheets (`make proof`: drafts-review-STYLE.pdf, smallcaps-review-STYLE.pdf).
- ſ ſſ before the round letters: kern_clear's full guard would also loosen
  12 other pairs (A.sc before ö.sc ō.sc õ.sc ǭ.sc č.sc ḡ.sc ..., −78 → −13
  for ö.sc; F ỡ; V Y ě); left as they were.

## Coverage: the end aim (2026-11-09)

Full IPA (with extIPA and the phonetic blocks) and Latin as wide as
Charis SIL's: then 980 Latin code points against Myia's 654, IPA and
phonetic 368 against 133 (Greek stays ahead: 333 against 23). First the
open review work above on what the font has; then the letters that
compose from existing glyphs (the Irish dotted Ḃ ḃ Ḟ ḟ Ṁ ṁ Ṗ ṗ, Ǆ ǅ ǆ
Ǉ-ǌ, ḁ ḉ ḝ), those derived like ɢ ʙ (the Uralic small capitals ᴀ ᴄ ᴆ ᴇ
...), and last the medievalist and Germanist blocks (Latin Extended-D,
-E), which need new drawing. `scripts/coverage.py` holds the current
target (TARGET); a new set goes in there when it is taken up.

## Ligatures

None to make. Dropped 2026-11-09: ch ck tz (from Fraktur) and ſs.

## Spacing: revisit only if specimens warrant it

Four Bold Italic pairs (`of`, `Wh`, `it`, `ba`) were reviewed on 2026-10-20
and retained despite tight measurements against references. They are not
unresolved repair tasks; reopen only on visual evidence.
