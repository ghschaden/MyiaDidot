# IPA ɶ and ᴅ at the x-height, 2026-11-09

Scope: ɶ (U+0276) and ᴅ (U+1D05) in all four styles. As aliases of oe.sc
and d.sc they stood at the small caps' height (1040, ink to 1064), a size
above ɢ ɪ ʙ ʀ ʏ ʟ ʜ ɴ, which stand at the x-height since 2026-11-01 (ʛ
followed 2026-11-08); Charis and Libertinus set ɶ at the x-height. Seen in
an outside review that called ɶ "at cap height, like Œ"; it was at the
small caps' height. The same review's ʘ (a circle with a central dot
already) and ɵ (a barred o at the x-height, apart from θ) needed nothing.

Proofs (`build/glyph-review/ipa-oe/`, not retained): `regular` (before and
after, beside ɢ ʀ ɪ œ), `Italic-new` and `BoldItalic-new`.

## Decision

Made as the other IPA small capitals are (derive.py "enlarge", stems at
n's weight): ᴅ from d.sc, its flat edges on 0 and 884; ɶ from oe.sc
fitted to -20..904, so its flat edges lie on 0 and 884 and its round side
overshoots as o's. Regular advances: ɶ 1360 (1551 before), ᴅ 1035.

## Findings

- All four styles: ɶ and ᴅ the size and weight of ʙ ʀ ɪ (stem 164 in the
  Regular, as ʀ's and ɪ's). Accepted.
- Outline findings of the recipe, as on the other IPA small capitals
  (2026-11-01): Regular ɶ a 2.3 degree join at its foot; Italic ɶ and ᴅ
  kinks of 4-6 degrees; the italics' ɶ top +20 from 884, its round side
  overshooting as their small caps do (their o has none at the top);
  Bold Italic ɶ a 4 degree wobble. Accepted with the letters.
