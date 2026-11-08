# Bold Italic Latin and modifier-letter drafts

The person reviewed 49 Bold Italic drafts (Latin letters and modifier
letters, neither Cyrillic nor currency signs) on 2026-11-08 and approved
47 unchanged. Sheet: build/glyph-review/bold-italic-latin-modifier-drafts-2026-11-08/review.pdf.

Two repairs requested:

- uniA7B4 (Ꞵ): the descender at the stem's thickness. The Bold Italic took
  the Italic's recipe pieces unweighted (a 166-unit descender under a 288
  stem). Ꞵ now has its own Bold Italic recipe (make_bold.ITALIC_BOLD_RECIPES):
  B's stem running down at 288, aligned with it, ending in a foot serif at
  B's own height (67) and overhang (167 a side). ꞵ.sc is drawn on its own and
  does not change.
- uni2C73 (ⱳ): the arm the hook leaves was thinner than the hook (30-48
  against ~82; w's own arm is 74-85). derive.fair_joins, run for the
  Italic's join (590-700), refitted the arm's whole outer edge from the curl
  down to the foot. The outer edge is redrawn: one curve from the curl,
  tangent to it, to w's own outer edge at y 480, and w's curve below. The arm
  now runs 75-95. On the person's second look, the inner edge's corner
  at 595 (w's hairline leaning left into the straight piece leaning right,
  about 30 degrees) is faired: one curve from w's edge at 554 to the curl at
  775, tangent to both. On the third look the arm still grew toward its
  end (measured across the stroke: 54 at the foot, 91 at 600, 75 at the
  curl). The outer edge is refitted as two curves joined smoothly at
  (1395,419), fitted by least squares to stay 77 units (the curl's stroke)
  from the inner edge: the arm now runs 76-79 from y 200 into the curl,
  narrowing only below 150 into w's bowl. On the fourth look the ball was
  made fuller: the recipe's ball 80 to 95 (make_bold.ITALIC_BOLD_RECIPES,
  as the other x-height curl at 95), regenerated, and the two arm repairs
  reapplied by their scripts (w_inner.py, w_even.py). Marked drawn
  (org.myiadidot.drawn), so make_bold keeps it.

Both repairs approved by the person on 2026-11-08; all 49 forms are
accepted. Ꞵ's old kink at the join (quality list) is gone. Shaping of the
full corpus (2,119,735 strings) is unchanged. Retained proof:
proofs/bold-italic-latin-modifier-drafts-2026-11-08.pdf (the review sheet,
Ꞵ and ⱳ before and after, the ⱳ ball close-up). Working proofs and the
repair scripts: build/glyph-review/bold-italic-beta-w-hook-2026-11-08/.
