# Bold Italic remaining drafts

Sheet: build/glyph-review/bold-italic-final-drafts-2026-11-08/sheet.pdf
(old-style figures; U.horn, u.sc.horn; the Bulgarian forms; each beside
the Italic's).

The person approved the 10 old-style figures on 2026-11-08. U.horn,
u.sc.horn and the 12 Bulgarian forms remain to be reviewed.

The person approved 11 of the 12 Bulgarian forms on 2026-11-08. Requested:
- u.sc.horn: uneven at the horn. The stem below it had a kink on its outer
  edge (u.sc's cut serif bracket) and a bulge on its inner bracket; now the
  outer edge runs straight at the stem's slant to the top corner and the
  inner bracket is one curve tangent to the stem (107 widening smoothly to
  141 at 940, where it stepped out to 153). Kept as drawn. Pending review.
- uni0436.loclBGR (Bulgarian ж): the c on the left the mirror image of the c
  on the right.

ж (both italics, at the person's request 2026-11-08): the left half is
now the right c mirrored about the stem (ball at the top left), not Old
Standard's c turned (ball at the bottom). Made in make_italic.mirror_zhe on
Old Standard's ж before anything is made of it, and moved 41 left (the
advance 41 less) so its left side bearing stays the old 28; the Italic's
җ and Bulgarian ж recipes moved with it, the Bold Italic's own recipes
(make_bold ITALIC_BOLD_RECIPES: җ; Bulgarian ж, its stem run up into l's
top by a widening piece instead of the Italic's cut, which left a notch)
by the 50 units its ж moved. ж, Bulgarian ж and җ: side bearings 28/19 in
the Italic, about 37/2 in the Bold Italic, lint clean. A first attempt
mirrored only the Bulgarian forms and left them 32-52 units off the stem
(a step in the Italic's stem, the Bold Italic leaning): replaced.
Reopened: the Italic's Bulgarian ж and җ approvals (2026-11-05) and the
Bold Italic's җ (2026-11-08). Pending the person's review, with
u.sc.horn (U.horn and u.sc.horn are the horn's bases: the horn is a
separate mark in Ư and the small-cap ư). Proof:
build/glyph-review/italic-zhe-mirror-2026-11-08/zhe-final.pdf.

The person approved ж (both italics), the Bulgarian ж (both), u.sc.horn
and U.horn on 2026-11-08. җ: a slight swelling/kink on the descender's
inner edge. Its inner edge left the crossbar leaning as the descender
does, dropped upright down the c's lower inside, then leaned again: a 13°
kink at the cut in the Italic, a tight bend (a swelling) in the Bold
Italic. Now one curve from the crossbar's corner to the descender line
(make_italic ITALIC_RUNS, straighten_run), and the outer edge's 12° corner
at the cut rounded (ITALIC_CORNERS, round_corner); both generators apply
them. The descender now 132-136 wide in the Italic and 214-217 in the Bold
Italic, no corner over 1.5° in that stretch. Approved by the person on
2026-11-08. Proof:
build/glyph-review/zhe-descender-2026-11-08/zhe-descender.pdf.

After the approvals, two quality findings were cleared without changing
the design: ж's stem is now left untouched by mirror_zhe (the right half
taken from 3 units right of the stem, cut 6 left of it: the mirrored
sliver of the stem's right edge had bent its left edge by 0.6 units in the
Italic, which emboldened became a 5-unit wobble in the Bold Italic), and
u.sc.horn's inner bracket is split at its extreme. The approvals of ж,
Bulgarian ж and җ (both italics) and of u.sc.horn were renewed for these
outline cleanups.
