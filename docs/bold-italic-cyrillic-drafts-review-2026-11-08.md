# Bold Italic Cyrillic drafts

The person reviewed the 15 encoded Bold Italic Cyrillic drafts on
2026-11-08 (sheet: build/glyph-review/bold-italic-cyrillic-drafts-2026-11-08/review.pdf)
and approved 14 unchanged. Requested: uni04B2 (Ҳ), its descender's hook
unified with Ң's and Ҷ's (uni04A2, uni04B6).

## Ҳ

The Bold Italic's Ҳ is the only letter there with tail_step's sloped fill
(Қ Җ have their own curled tails): its tail's top dropped from the X's
foot serif (1595,69) to the tail's corner (1730,30), where Ң's and Ҷ's
run level with their serifs out to a sharp corner. The corner is now on
the serif's top at (1742,70) and the outer edge at Ң's slant; kept as drawn
(org.myiadidot.drawn). Pending the person's review.

## Serbian italic forms (both italics)

At the person's request, compared against Charis and Libertinus (which
agree): г is ī, ѓ is ī with the acute over the bar, п is и with the bar
free above, т is ш with a bar 1.84 times п's. Made in the Italic
(make_italic ITALIC_RECIPES, serbian_gje, serbian_bars; Old Standard's own
fused-bar п т no longer taken, OS_LOCL empty) and in the Bold Italic
(make_bold calls the same after its own composites, so ѓ stacks as its ḗ
and the bars stand as its ū's). Approved by the person on 2026-11-08 in both
italics (Italic г ѓ п т; Bold Italic б г д ѓ п т). Four old quality
findings on the Old Standard п т are gone. Shaping: the corpus (shaped
English by default) is unchanged; the golden Serbian cases take the new
advances (п 1037 to 1101, т 1501 to 1564 in the Italic).

The Bulgarian forms remain to be reviewed.

Retained proof: proofs/bold-italic-cyrillic-drafts-2026-11-08.pdf (the
sheet; the Serbian forms beside the references and enlarged; Ҳ's tail
before and after beside Ң Ҷ).
