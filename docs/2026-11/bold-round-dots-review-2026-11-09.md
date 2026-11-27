# Bold and Bold Italic round dots, 2026-11-09

Scope: every dot of the two bold styles, which the emboldening widened far
more than it heightened (AX against AY): the Bold's period 357 x 262
(1.36:1) of the Regular's 256 round, i's dot 278 x 256, the dotted
circle's dots 1.5:1; the Bold Italic's period 366 x 272. The references'
bold dots are round, 1.00-1.05 (Bodoni Moda, Libre Bodoni, Old Standard,
Charis, Libertinus, EB Garamond). Reference state: 2e1cec7c.

Proofs (`build/glyph-review/bold-round-dots/`, not retained): `today-vs-area`
and `today-vs-width` (the two candidates), `bold-pass` and
`bolditalic-pass` (the pass on both styles), `accepted-Bold` and
`accepted-BoldItalic` (the accepted glyphs it changed).

## Decision

Round at the same area (chosen over the same width, which made the Bold's
period 174 per 1000 against 149, and over keeping the ovals). Each dot is
its source style's (the Regular's for the Bold, the Italic's for the Bold
Italic) scaled evenly to the emboldened dot's area: scripts/bold_dots.py,
run in make_bold before y's dot below is placed and the composites and
recipes read the dots. Placement: a glyph with a dot on the baseline keeps
that dot's bottom (. ! ? ⋮, the others in it moved alike); one whose dots
all stand above the x-height keeps the top of its highest (i's on its
1496 zone, the accents); the rest keep their centres (※ ⸓ ⸖).

## Findings

- Period, colon, ! ?, ˙ ¨, ※ ⁜ ⸓ ⸖, ⋮, ◌, ⸁ ⸄ ⸅ ⸇ ⸈, the Greek
  dialytika marks: round, as dark as before. Accepted.
- Colon: its upper dot (period moved by the Regular's 668) now reaches
  949 in the Bold (906 before, the Regular's 924). Accepted as it stands.
- ⋮: the gaps between its dots narrow from about 138 to 92 (the
  Regular's 144). Accepted as it stands.
- Bold ṫ, Bold Italic ɨ ɉ ʝ ⁱ ʲ ᶤ (accepted before): their dots now round,
  ɨ ɉ ʝ's as i's and j's. Accepted again.
- The capitals' dieresis (Dieresis, on the small caps' tops at 1434):
  at 211 its dots stood just over a pixel at 10 ppem and the CFF hinting
  set ä.sc ë.sc ï.sc ö.sc ü.sc ÿ.sc ẅ.sc ё.sc ї.sc ϊ.sc ϋ.sc 0.8 px above
  the zone; tried 200 / 204 / 205 / 211, 204 and under hint on it. Its dots
  are 204 (3 % smaller than the lowercase dieresis's 211).
- Side effects: the narrower dieresis lets ſ ſſ f kern 5-6 units tighter
  before ë ö ï (the clearance guard); y's dot-below anchor in the Bold
  Italic 3 units right (its gap to the rounder dot kept).
