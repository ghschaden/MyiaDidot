# Bold Italic currency-sign drafts

The review reviewed the 20 Bold Italic currency-sign drafts on 2026-11-08
and approved 18 unchanged. Sheet:
build/glyph-review/bold-italic-currency-drafts-2026-11-08/review.pdf.

Two repairs requested:

- uni20AE (₮): the two bars do not show on the left of the stem: centre
  them better or make them longer.
- uni20B4 (₴): the lower bar does not show on the left: make both bars
  longer so that they show on both sides.

Both were emboldened whole from the Italic: the stem and the S grew over
the bars' left ends. They now have their own Bold Italic recipes
(make_bold.ITALIC_BOLD_REBUILD and ITALIC_BOLD_RECIPES), drawn on the Bold
Italic's T and S at the emboldened bars' weight:

- ₮: the bars centred on the stem, standing out 150 a side at their middles,
  rising as the Regular's (0.48), 104 across. Advance 1496 to 1462 (T's
  spacing). One handle at the arm's join (1081,1293) set on the stem edge's
  line (rounding had left a 2.6 degree break); marked drawn so make_bold
  keeps it. This also clears three older findings (kink, smooth, wobble).
- ₴: Ƨ with both bars standing out about 140-150 past the S on both sides,
  75 thick; advance 1411 to 1467 (side bearings about 45 by the bar's thin
  end, 54 on the right as before).

The review approved both on 2026-11-08; all 20 currency signs are accepted.
Shaping of the full corpus (2,119,735 strings) changes in 5,706, all the
two advances alone; baselines accepted from that exact report.
Retained proof: proofs/bold-italic-currency-drafts-2026-11-08.pdf (sheet,
₮ and ₴ before and after).
