# Bold Italic extended Latin small caps

Reference: `7eb071e0` with the approved basic Latin small-cap repairs
installed. This batch contains 42 unaccepted small caps reached from
extended Latin characters, including ligatures, bars, ogoneks and hooks.
Previously accepted hooked b/d, hooked c/g and other accepted forms are
excluded. Exact names, fingerprints, lint findings and shaping records
are in `build/glyph-review/bold-italic-smallcaps-extended-latin/` as
`glyphs.txt` and `checks.json`. All 42 are now accepted, including the
four subsequently repaired forms (last approval 2026-11-07).

Proof: `review.pdf` in that directory, two pages. Both pages were rendered
as `review-1.png` and `review-2.png` and visually inspected. Each cell shows
capital, small cap and lowercase at the same em scale over height guides,
then n/H contexts at text size. No redraw is proposed before the
review. Of particular interest: uni2C65.sc (ⱥ.sc) has a notch finding at
297,207 (65 pixels in the lint raster), where the slash meets the letter.
The existing lint inventory records this as an accepted tapered lower
counter at the slash/foot junction (2026-10-26). That verdict is retained;
the glyph is included for its overall drawing review, with no new fault
or repair inferred from the diagnostic alone.

All 84 explicit smcp/c2sc mappings pass (`script=latn`, `language=en`)
using the font compiled from the complete current Bold Italic source.
Apart from uni2C65.sc's notch, outline lint reports no findings in the
batch. `prepare.py` repeats preparation and inserts a break after five
rows; the scratch selection UFO only selects proof cells. Minor TeX
overflow warnings do not obscure specimens or labels. These are source
outline and shaping specimens, not screen-hinting proofs. No drawings,
spacing, baselines or acceptance records changed for this batch.

The review approved 38 unchanged forms, then approved the repaired
uni0242.sc and uni0263.sc on 2026-11-06. Their records are installed.
florin.sc and uni01A5.sc were subsequently approved on 2026-11-07,
together with full capital Ƒ (uni0191), after Astra's reconstruction
from finished same-style reference curves. Paired
Italic work and subsequent hook revisions are recorded in the
[paired review](paired-italic-extended-smallcaps-review-2026-11-06.md).
