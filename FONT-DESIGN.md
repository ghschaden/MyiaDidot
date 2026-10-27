# Open font-design work

Current backlog, consolidated 2026-10-26. Completed work belongs in
[FONTLOG.txt](FONTLOG.txt); detailed evidence stays in `docs/` and `proofs/`.
Tooling and publication tasks belong in [DEVELOPMENT.md](DEVELOPMENT.md).
A diagnostic finding is a candidate for review, not proof of a design fault.
The exception files in `tests/data/` are the current inventories; do not copy
counts here, where they quickly become stale. Every entry in
`hint-zones*.txt` and `glyph-lint-*.txt` carries a dated verdict
(2026-10-26); reopen one only on new evidence (a raster or a proof).
One awaits it: Fraktur 𝔖's CFF top in both italics after its curves were
split at their extremes (marked PENDING REVIEW in hint-zones-cff-*.txt).

## Construction and optical quality

- Bold Italic, seen in print (2026-10-27): ʋ's curl starts narrower than
  the stem (a step each side; a curl is one thickness all round, a
  tapering one or a drawn recipe is needed, emboldened whole it runs into
  the first stem); ʷ's left stroke turns at its join; г's inner curves
  flattened upright (the handle fit, as ψ's); Ɯ's join into its second
  stem not smooth below.
- Bold Italic: try the Bold's two emboldening repairs of 2026-10-27
  (make_bold: keep_smooth for the rounder way, runs_on by weight). Tried
  there they smooth § 3 ₵ ø.sc Θ ẞ but add side space (3 +21, § +13),
  notch ẞ, move ɽ's advance and ƙ.sc's CFF top, and runs_on kinks ð ɨ ђ
  ћ љ ˁ: each needs review before switching them on.
- Review derived letters still emboldened whole in
  `tests/data/emboldened-whole-*.txt`. Hooks, attachments and curls may need
  recipes drawn at the final weight when rederivation strays or misses.
  Include Bulgarian forms and rhotic letters where still listed; the
  repaired Bold Italic ʄ is complete. Every remaining entry now has a
  reviewed reason in BOLD_KEEP_WHOLE / ITALIC_BOLD_KEEP_WHOLE (2026-10-26):
  the generic rederive fixes are spent, what is left needs a recipe drawn
  at the style's weight (BOLD_RECIPES, ITALIC_BOLD_RECIPES) or a
  landmark-placed cut, letter by letter.
- Work through `tests/data/quality-*.txt`: extrema, kinks, smooth joins,
  stroke weight, zones, slant, width and accent gaps. Many italic findings
  are inherited from Old Standard and propagate to Bold Italic. Keep broad
  contour cleanup separate from individual drawing changes and inspect
  `make diffenator` results. Use `make strokes` for optical-weight proofs.
  W-family diagonal slant and i/j dot gaps can be intentional.
  Extremes lost to a slant or turn are split by the generators now
  (2026-10-26), the rederived Bold Italic letters too (2026-10-27); none
  left runs more than about 20 units past (Bold Ʒ ℓ, Bold Italic ѫ ® л @).
- Accept, or send back, the drafts not yet accepted: `scripts/accepted.py
  UFO --drafts` (about 350 in each italic weight, ₸ ct st in the Romans).
  Acceptance is recorded with accepted.py, not by clearing draft flags
  (docs/claude/quality.md). `make proof` writes the review sheets of
  exactly those (drafts-review-STYLE.pdf, smallcaps-review-STYLE.pdf):
  the next step is the person's pass through them. Bold and Bold Italic
  old-style figures (not drafts, so not on the sheets) have no recorded
  acceptance; Regular old-style 3 and 5 changed after theirs.

## Spacing: revisit only if specimens warrant it

Four Bold Italic pairs (`of`, `Wh`, `it`, `ba`) were reviewed on 2026-10-20
and retained despite tight measurements against references. They are not
unresolved repair tasks; reopen only on visual evidence.
