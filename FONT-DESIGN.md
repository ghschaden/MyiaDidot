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

- Shared parts compared across glyphs (2026-10-27, measured on the
  outlines; the drawn glyphs agree, the generators make these):
  - Hook endings: the curl recipes' balls were fixed numbers, 20-60 %
    under the drawn balls of c a f r y. Done for derive.py's recipes in
    the Regular and Bold (2026-10-27, derive.ball_for; ʋ ɻ keep theirs:
    no room in the Bold). The italic tails off a stem (retroflex,
    descender: ɳ ʈ ɭ ɖ Ɽ ң қ ...) keep their ball at half the hook's
    stroke, flush with the curl's end (the person's decision, 2026-10-27).
    The italics' curls over the top (2026-10-27): the Italic's take the
    case's ball (about 72; its curls too small for its drawn c's 94); the
    Bold Italic's drawn at its weight, wider (balls 80-126 for its c's
    121, J's 143: more closed the counters). Its ⱳ.sc, emboldened from
    the Italic's draft, still has kinks and a wobble at the curl; ɦ.sc a
    step where Ɦ's top serif is cut (both in quality-BoldItalic.txt).
    Left: whether the person wants the capitals' curls larger still, to
    carry balls as large as J's; Ⱳ keeps its number (w_curl.py's
    approved connection); Bold Italic a's ball does not grow (68 -> 66).
  - Dots: in the Bold and Bold Italic they are widened three times as
    much as heightened (period about 1.36:1, ⸁ ⸄ ⸅ ⸇ ⸈ 271x182, Bold Italic
    ※ ⁜ ⸓ ⸖ 323x207); ※ ⁜ ⸓ ⸖ take the accent dot (248), not the
    period's (256), and in the Italic their dots differ within a glyph.
  - Serifs: consistent but where make_bold.part_serifs shortens them, also
    those with no neighbour: Bold ﬀb ﬀh ﬀt ﬄ ſſl reach 103 (f 141); Щ, Bold
    Italic Ш; Bold m.sc ɦ.sc ƭ.sc ʝ.sc, Bold Italic ƙ.sc ϗ.sc ы.sc about 100
    (135-152). Bold ɫ.sc's top serif has a 1-unit end face. At hairline
    stems (N M U) the Bold's serifs reach 250 against 196.
- Wobbles (checks.py `wobble`, 2026-10-27): the emboldening puts short
  reversals into curves its source glyph has not. In the Bold a fitted
  curve now keeps its source's bends (keep_bends: 169 -> 130 glyphs);
  the rest bend back across a node, between two curves, which the guard
  (one curve at a time) does not see. In the Bold Italic (375; г, o's
  inner side) the same guard took only 16 away: another cause, to be
  found. Large ones at ball necks (ƒ y) may be design.
- Review the step candidates (checks.py `step`, 2026-10-27, in
  `tests/data/quality-*.txt`): a short straight jog between edges running
  on the same way, as Bold Italic ʈ ɳ ɚ ɝ had. Some are designed (ǥ ɉ bar
  ends, ₿); others look like faults (Ƈ Ɠ ƴ hook tops, ɾ, ʝ, Serbian г п,
  Regular ɝ, ʋ).
- Bold Italic, seen in print (2026-10-27): ʋ's curl starts narrower than
  the stem (a step each side; a curl is one thickness all round, a
  tapering one or a drawn recipe is needed, emboldened whole it runs into
  the first stem); ʷ's left stroke turns at its join; г's inner curves
  flattened upright (the handle fit, as ψ's); Ɯ's join into its second
  stem not smooth below.
- Bold Italic: keep_bends is on (2026-10-27); still to try the Bold's two
  other repairs (make_bold: keep_smooth for the rounder way, runs_on by
  weight; keep_smooth adds inflections there, Codex's study). Tried
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
