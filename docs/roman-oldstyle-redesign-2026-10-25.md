# Roman old-style figure redesign proposal, 2026-10-25

The person asked whether Regular was adapted along with the approved
Italic set. It was not: the approved proof was Italic, with Bold Italic
inheritance. Regular and Bold production drawings still have the earlier
historical proportions.

[Regular redesign proof](../proofs/roman-oldstyle-redesign-2026-10-25.pdf)
now shows a matching Roman proposal, including the complete before/after
set, Libertinus Serif Regular at equal x-height and text specimens.

The new bands match the approved Italic rhythm: 0/1/2 around x-height,
3/4/5/7/9 with x-height tops and moderate descenders, and 6/8 with shorter
ascenders. The original Roman shapes remain, including the angular-topped
3, open 4 and curled ball-terminal 9. Widths and advances are reduced
with the drawings; the 4 is 25% narrower. Thick strokes are balanced for
Regular's own lowercase references, rather than reusing Italic weight
adjustments. This avoids making the resized Roman 3/4/5 too light.

All ten rounded trial glyphs are construction/lint clean. The fitted
Roman 3/4/5 measure 160/167/160 units across their sampled thick strokes,
near Regular's lowercase band, while 6 measures 167.

This is a scratch proposal only. Regular and Bold production masters are
unchanged. The Bold result, tabular variants and production checks follow
selection of the Roman drawings. User acceptance is not yet recorded.

Scratch source: `build/roman-figures-review/proposal.py`; candidate:
`Restored-nine.ufo` in that directory. Measurements, construction/lint
reports and SVG/PNG rendering are alongside it.

## Accepted and integrated

The person accepted this proposal and requested commit and push.
The reviewed Regular outlines and advances are now fixed design inputs in
`scripts/data/oldstyle-regular/`. The shared old-style helper loads them
when Regular figure spacing is rebuilt, preserving their approved fit,
and regenerates the old-style slashed zero and tabular components. The
slash's base fingerprint is refreshed after rebuilding. Bold inherits
its final Regular bases through the normal weight generator, with local
construction finishing. The approved italic design inputs remain separate.

The original Roman numeral shapes and curled ball-terminal 9 are retained.
Lining figures, Unicode coverage, kerning and feature rules are independent
of this old-style redesign. Narrower proportional advances intentionally
change the positions of old-style numeral strings.

Bold finishing retains a modest, fixed 20-unit optical increase on the
reduced 3 and 5. It deliberately avoids chasing the sample-row stroke
metric on 5, where the selected stroke changes discontinuously as its
bowl becomes wider. A generated-glyph marker makes this adjustment
repeatable without applying it twice. The open 4 receives an 820-unit
advance (approximately the normal 1.08× Regular ratio) with positive,
balanced ink bearings; the old automatic fit had produced negative
bearings after narrowing. Its tabular component follows that final fit.
The tiny extra vertex at the angular 3's weighted flag is removed.

The Roman shaping sweep covers 2,119,788 strings per style. Eight Regular
strings and ten Bold strings change only positions, as expected for the
approved proportional advances. Italic and Bold Italic remain unchanged
from their accepted integrated figure sets. Kerning, groups and feature
text match the pre-Roman-integration masters.

## 2026-10-26: 5 lightened

In running text the 5's bowl stood out dark: 276 units across its right
side against 222 in the 3's bowl. The reviewed design's inner bowl edge
moved 50 units right (226 now; Bold 345, the 3's 341); outline, advance
and spacing are unchanged. See FONTLOG.
