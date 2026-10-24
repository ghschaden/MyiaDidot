# Italic ỵ dot placement, 2026-10-24

[Before/after proof](../proofs/italic-y-dot-before-after-2026-10-24.pdf)
compares the original collision, the first beside-descender trial and the
closer placement requested after review.

The person accepted placing the dot beside the descender and asked to move
it a little left. The horizontal clearance is now 25 font units rather than
the first trial's 50. The dot's height is unchanged. Rounding makes the
revised position 24 units left of the original trial in Italic and 25 in
Bold Italic. Both have zero overlap and no glyph-lint findings for ỵ.

`scripts/y_dot.py` derives y's DotBelow anchor from the descender's right
edge within the dot's vertical band and the combining mark's ink and
attachment anchor. Both style generators run this before rebuilding
composites, using their own weighted outlines. It is idempotent. Italic's
anchor moves 511 units right; Bold Italic's moves 574. The placement therefore
works for both precomposed and decomposed text.

Nine glyphs change per style: y, ý, ÿ, ŷ, ȳ, ỳ, ỵ, ỷ and ỹ. Only ỵ changes
visible ink; the others carry the corrected attachment anchor. Base and
mark outlines, advances, other anchors, kerning, groups, features and font
metadata are unchanged. Compiled cmap, hmtx, GSUB, GDEF, OS/2 and hhea
match; GPOS differs only in eight horizontal DotBelow anchor coordinates
per style. Regular and Bold masters are unchanged.

Before/after shaping of 2,119,788 strings per italic weight finds eight
position-only differences, all U+0359 COMBINING ASTERISK BELOW on y or an
above-accented y. This mark shares the DotBelow attachment class. The dot
below itself normally composes to ỵ, whose component now uses the same
anchor. Glyph selection and advances are unchanged. The two corpus digests
are updated for these intended differences; golden snapshots are unchanged.
The obsolete Italic ỵ notch exception is removed.

Regression tests check both weighted masters for clearance and lint,
anchor repair and idempotence, and preservation of y's outline, advance
and anchor height. Existing composite tests cover NFC/NFD agreement.

Working reports and proof source: `build/y-dot-fix/`.

Validation: **163 passed, 3 skipped** across the full suite and separate
CFF rerun. The sandboxed full suite has 159 passes and four CFF
helper-socket failures; all four pass with socket access. All three
generated styles reproduce. `make proof`, Ruff, source sync and whitespace
checks pass. The focused composite, glyph-lint and clearance run has
22 passes.
