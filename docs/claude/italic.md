# The Italic against the Regular: phase 6's measure

Phase 6's first step (TODO.md), specified 2026-11-15 on Fable and built
the same day: `scripts/quality/italic_measures.py` (measures, gate and
table in one; tests/test_italic_measures.py), its first run read and the
specification corrected by it ("The first run" below). Not built: the
sheet (built 2026-11-17: `scripts/italic_sheet.py`, "What is left to
build"). The model is F4's `docs/claude/bold.md` and its two scripts.

The question: where does the Italic read as another typeface beside the
Regular? The Regular is Theano Didot's, the Italic's letters are Old
Standard's, weighted and zone-scaled (`docs/claude/styles.md`); its core
set (a-z, A-Z, O Q, Greek and Cyrillic lowercase) is redrawn on clean
nodes and kept as saved since 2026-11-10 to 15. "Another typeface" is
made a number so: an italic differs from its roman in every family, and
how much is what the references show. A feature is a fault where Myia's
**relation** Italic to Regular lies outside the relations of the
references' own pairs.

## Pairs

| | regular | italic | counts for |
|---|---|---|---|
| Myia | `sources/MyiaDidot-Regular.ufo` | `sources/MyiaDidot-Italic.ufo` | |
| Old Standard | `OldStandard-Regular` | `OldStandard-Italic` | the range |
| Bodoni Moda 11 | `BodoniModa-11-Regular` | `BodoniModa-11-Italic` | the range |
| Libre Bodoni | `LibreBodoni-Regular` | `LibreBodoni-Italic` | the range |
| Libertinus Serif | `LibertinusSerif-Regular` | `LibertinusSerif-Italic` | the second voice |
| Charis SIL | `CharisSIL-Regular` | `CharisSIL-Italic` | the second voice |
| EB Garamond | `EBGaramond-Regular` | `EBGaramond-Italic` | shown only |

(build/refs/, `fetch_refs.py`. GFS Didot has no italic there.) The
three Didones are the calibrated range. Libertinus and Charis are no
Didones, their values do not widen the range; they speak only by the
reference-font rule: both on the range's side of Myia makes a candidate
a fault (below). EB Garamond is beside them for the eye, an old-style
italic's relation to its roman.

Old Standard's pair is Myia's own ancestry on the italic side: where
Myia's relation leaves Old Standard's, the cause is the Regular's side
(Theano) or `make_italic`'s weighting, and the report says which by
printing both styles' own-scale values, not the relation alone.

## Scale

As bold_measures.py: outlines deslanted by the font's italic angle, a
1000 em. Then every value on the style's own scale: **a thickness over
the stem** (the lowercase's for lowercase, the capitals' for capitals),
**a size over the zone** (a width, a counter, a serif's or a hook's
reach: over the x-height or the cap height); the ball, read against the
stem beside it, over the stem. The stem is taken a third of the way up
(an italic stem swells towards the branch), the same in every font: the
runs there at least 0.6 of the widest (`stem_runs`; a hook's hairline
is none).

Sizes were first put over the stem too. The italic capitals' stem is
lighter against the Regular's than most references' (0.875, the range
0.853 to 0.995: the kept contrast), and every capital serif then read
10 to 15 % too long, one decision counted six times. Over the cap
height the same serifs are inside.

The x-height is x's top. In a roman that is the flat letters' height.
In an italic all the lowercase reaches one line (x z o n u v, in all
seven fonts), so an italic has no overshoot above to measure; what is
measured instead is where that line lies against the roman's flat
letters ("x-height I / R").

A thickness is taken across the stroke: the ink's run in a column or a
row, times the cosine of the stroke's lean there, the lean read from
the run's middle 2 units to either side (`across`); where the run to
one side is another stroke (the arch running into its stem) there is no
lean, and the place is left out.

Two kinds of measure:

- **Relation** (both styles have the feature): r = the Italic's value on
  its own scale over the Regular's on its own. Myia's r against the
  range of the three Didones' r.
- **Italic's own** (the Regular has no counterpart: entry and exit
  hooks, the single-storey a, f's descender): the Italic's value on its
  own scale against the three Didone italics' values directly.

## What is measured

| | on | how | kind, scale |
|---|---|---|---|
| stem | median of i l n m h u; of H I E L | across, a third up | relation, over the zone |
| long stems | l t f; b d h k; p q, each over the stem above | l t f across, a third up; b d h k halfway between the x-height and the top, p q halfway down the descender, where the stem stands alone (`long_stem`) | relation, over the stem |
| hairline | o top and bottom, e's bar, n's arch between its stems, v's thin stroke; H's bar, O's top, A's thin stroke | across, where thinnest (o O: over the middle half of the width; v A: the thinner of two runs at half, 0.65 of the zone) | relation, over the stem (the contrast) |
| colour | a-z together, and each | ink in the x-zone over advance x x-height | relation |
| width | a-z's advances (mean); n o e a each; A-Z, H O | advance | relation, over the zone |
| counter | n o e b d p q | the widest disc in the largest counter (bold_measures) | relation, over the x-height |
| ball | c f r y j | the widest disc in the terminal's region (bold_measures `BALLS`) | relation, over the stem; good to about 3 % (2 units a pixel) |
| serif, capitals | H I both sides, E L left | reach past the stem's edge in the row just above the foot; thickness near the left tip and at half the reach | relation; reach over the cap height, thickness over H's bar |
| foot | p q at the descender's end | as the capitals' | relation; reach over the x-height, the tip over o's hairline |
| hooks | n i entry and exit, u exit, l's head | reach past the stem's edge (top fifth, lower 45 %); the hook's stroke where thinnest | italic's own; reach over the x-height, thickness over the stem |
| x-height | x | the Italic's x top over the Regular's | relation |
| overshoot | o below; O above and below | the round's edge past the line, per cent of the zone | difference Italic less Regular |
| ascender | b d l | top over the cap height | relation |
| stress | o, O | the angle from the vertical of the line through the stroke's thin places above and below | difference in degrees |
| slant | the font's angle; what lean n H l's stem keeps after deslanting | | shown only |

Not measured as a relation: joins (bold_measures reads a column beside
the stem; on a deslanted italic arch that is not the same place as on the
roman's) and whatever counts different counters in the two styles.

Traps, as the first run found them (`--marks DIR` draws every measured
place on the letters, one PNG per font and style: look before a number
is believed, and again after a letter is redrawn):

- The Italic's a and g are single-storey: their ball regions hold a
  bowl's top and a stem. Neither is in the ball family (c f r y j); g's
  colour differs by a fifth for the same reason and is no finding.
- The Italic's f has a hook below since 2026-11-11 (a ball there too):
  the region for f's ball is the top one only, and finds it.
- Sizes over the stem, the x-height of an italic, the lean beside a
  step: "Scale" above.
- A roman's l has a head serif, an italic's an entry stroke: l's head is
  the italic's own, with the hooks. The entries' reach spreads by 40 to
  60 % among the three Didones (Old Standard's long, the Bodonis'
  short) and is never gated.
- EB Garamond's q has no stem where the others have (its foot reads
  negative): shown only, as that font is anyway.
- An italic n's counter is open below: its width is comparable (and
  measured), its aperture is not.

## The gate

Per measure, Myia's position against the Didones' range as
bold_targets.py's `position`: 0 inside, +6 six per cent above the
highest, -9 nine below the lowest.

| position | with | reads as | goes to |
|---|---|---|---|
| inside | | the italic of this roman | nothing |
| outside by 3 % or more (`OUTSIDE`) | | a candidate | the sheet |
| outside by 3 % or more | Libertinus and Charis both on the range's side of Myia | another typeface | the change list |
| outside by 10 % or more (`FAR`) | | another typeface | the change list |

- A measure whose three references spread by more than 30 % of their
  median between lowest and highest does not discriminate: shown, never
  gated (`SPREAD`; the table prints each measure's spread).
- Stress is gated in degrees: more than 5 beyond the range (`STRESS`);
  an overshoot at half a per cent of its zone beyond it (`OVERSHOOT`:
  about 4 units of the font's em).
- The numbers stand as proposed after the first run: of some 60
  measures 8 spread past 30 % (the entries' reach, the feet's inner
  side, y's ball, H's and L's left serif by Libre Bodoni's short one;
  and two of the kept capital hairlines);
  the others spread by 3 to 29 %, and no finding sits between 3 and
  10 % without the second voice agreeing, so the middle row has not yet
  had to decide anything.
- **Kept, never on the change list**: the capitals' contrast (H's bar,
  O's top, A's thin stroke over the capital stem). The report prints the
  rows with "kept: declined 2026-10-21 and 2026-11-02".
- Colour and width, expected about 5 % lighter and narrower: measured
  2 % lighter (the Didones' italics 1 to 3 %) and 7 % narrower (theirs
  1 to 10 %). Inside.
- The change list is a proposal to the designer, one review round on
  the sheet; what is struck there gets its date in this file.

## The sheet

One PDF (`proofs/italic-against-regular-DATE.pdf`), files before the
sheet:

1. The table: per measure the two own-scale values of Myia and of each
   reference, the relation, the position, the verdict. Candidates and
   faults first.
2. Per feature that is a candidate or a fault, one row at 144 pt:
   Myia Regular | Myia Italic | the nearest Didone's pair, the letters
   of that measure (c f r y for balls, H I p for serifs, o e n v for
   hairlines, o x z for overshoots), the place measured marked, the
   value beneath.
3. Running text, the only place where "another typeface" is seen:
   roman lines with italic words and phrases set in them, 24 and 12 pt,
   Myia and beside it Old Standard and Bodoni Moda set the same. Latin,
   then one Greek and one Cyrillic line.
4. The change list, each entry with its measure, the letters, and where
   the change would be made (next section).

## Where a fault is mended

The core set is kept as saved (marked drawn): `make_italic`'s constants
(`WEIGHT`, `CAP_WEIGHT`, the zone scaling) no longer reach it, only the
long tail still taken from Old Standard and everything derived.

| the fault | where |
|---|---|
| one letter's (r's ball, one serif) | that letter in the Italic: a small script or by hand in a scratch UFO, fitted by redraw.py, sheet, `--install` (redraw.md, "A letter given another shape"); what is built on it follows by `make generate` |
| a family's in the core set (all balls, all hairlines, every stem's weight) | one script over the kept letters of that family (as `f_hook.py`: the change made of the style's own shapes or by `reweight`), each result through redraw.py's gate and the sheet; **and** the generator's constant set to the same value, so the long tail and the recipes (`recipe_scale`, the stems measured on n and H) agree. Never the constant alone: it would move the tail and leave the core |
| colour or width by spacing | spacing (`docs/claude/spacing.md`), not the outlines |
| width in the outlines (counters) | the designer: a letter's proportions are a drawing |
| overshoots, zones | kept letters by hand in the fit's 1-unit bound (the gate holds bounds to a unit: a zone change is an install with the reason, not a redraw); the tail in make_italic's zone scaling |
| the Regular's side (Myia's relation leaves Old Standard's because the Regular differs from Old Standard's roman) | nothing in the Italic without the designer: the Regular is the master |

After any of them: redraw.md's steps 7 and 8 (generate, sweep, tests,
the second sheet with the Bold Italic), the measure letters (o n H O)
tried through `make generate` in a scratch copy first.

## The first run (2026-11-15)

`build/quality/italic-targets.md`, every value in
`build/quality/italic-measures.json`. The table's last columns put
Myia's Regular and Italic each over Old Standard's (R/OS, I/OS): that
is where a finding comes from.

**Inside**: the stems' weight (lowercase 0.99, capitals 0.875), the
lowercase hairlines (o, e's bar, n's arch), colour, the widths of a-z,
n o e a, A-Z and H, e's and b's counters, f's and j's balls, the
capitals' serifs in reach and thickness, the feet of p and q, every
hook's reach and thickness, the stress of o and O, the x-height (the
Italic's lowercase stands at the Regular's flat height as Old
Standard's does; the two Bodonis' italics stand 2 to 3 % higher, at
their romans' rounds).

**Outside, read as another typeface**:

| | Myia | the Didones | past | R/OS | I/OS |
|---|---|---|---|---|---|
| counters of n o d p q over the x-height | 0.62 to 0.79 | n 0.68-0.92, o 0.87-1.02, d p q 0.80-0.99 | -7 to -10 % | +8 to +20 | -1 to +1 |
| O's width | 0.87 | 0.95-1.01 | -9 % | +12 | -4 |
| c's ball over the stem | 1.05 | 0.93-0.96 | +9 % | -14 | -3 |
| r's ball | 1.32 | 0.92-1.10 | +20 % | -17 | -1 |
| v's thin stroke over the stem | 1.25 | 0.92-1.12 | +12 % | -27 | -1 |
| ascenders of b d l over the cap height | 0.96 | 1.00 (all three, both styles) | -4 % | +4 | 0 |
| o's overshoot below | +0.8 % of the x-height | 0.0 to +0.1 | 0.6 | | |
| O's overshoot above | +0.8 % of the cap height | -0.4 to 0.0 | 0.8 | | |
| p's foot, left reach | 1.36 | 1.06-1.32 | +3 % | -1 | +5 |

**Kept** (the capitals' contrast): O's top 45 % past the range, A's
thin stroke 16 %, H's bar 4 % (the last two on references that spread).

What the columns say: but for the overshoots and p's foot, **every
finding is the Regular's side**. On those measures Myia's Italic is Old
Standard's italic to within 4 %, and Old Standard's pair is inside its
own family's range; Myia's Regular is Theano's, with wider bowls and a
wider O than Old Standard's roman, a heavier stem (17 %), a thinner
diagonal hairline and, against that stem, smaller balls, and ascenders
4 % over the capitals where every reference's stand at the capitals'
height in both styles. By "Where a fault is mended" none of these is
changed in the Italic without the designer. What the Italic could be
given, for the sheet to show and the designer to choose from:

1. the bowls of n o d p q (and what shares them: b a g h m u) wider by
   about a tenth of the counter, O wider by a tenth: proportions, the
   designer's drawing (the widths of a-z and of A-Z as a whole are
   inside: it is the round letters, not the fit);
2. r's ball smaller by a sixth, c's by a twelfth (f's and j's are
   inside: one family is not one size);
3. v's thin stroke (and w y's, not measured) thinner by a tenth;
4. the ascenders raised to the Regular's 4 % over the capitals: the
   likeliest to be seen in running text, where b d h k l stand beside
   roman ones;
5. the Italic's own: o's and O's overshoots taken back to the
   Regular's (o below 2.6 against 1.8 % of the x-height, O above 2.7
   against 2.0 % of the cap height; O was drawn 2026-11-12), p's foot
   left as it is (3 %, at the gate's edge).

Not found, though TODO.md's phase 6 named them: the serifs' length and
thickness, the hairlines of the lowercase, colour and width as a whole.

## The long stems (2026-11-16)

Added after longtail.md's family 5 found 52 lines of the Italic's
quality list saying one thing (`stroke Latin lc lighter`, `weight` on
b d k l p q). The first run could not see it: its stem is the median of
i l n m h u, which the x-height letters decide.

| long stem over the x-height letters' stem | Myia | Old Standard | Bodoni Moda | Libre Bodoni | Libertinus, Charis |
|---|---|---|---|---|---|
| Italic, l b d h k f t p q | 0.87 to 0.90 | 0.87 to 0.88 | 0.95 to 1.01 | 0.96 to 1.02 | 0.98 to 1.01 |
| Regular, the same | 1.00 (t 0.99) | 1.00 | 1.00 to 1.03 | 1.00 | 1.00 |

- **Inside, all nine**, and by one font: Old Standard draws its italic
  so, and Myia's Italic has it from there to within 2 %. An x-height
  stem (i n u m) swells to its middle between the entry and the exit
  hook; a stem that leaves the x-height (l t f, the ascenders and
  descenders of b d h k p q) is one thickness from end to end, an
  eighth lighter. The two Bodonis and both second voices draw every
  italic stem alike.
- So by the gate it is no fault: a Didone italic may do this, one of
  three does. It is a **question for the designer on the sheet**, not
  an entry of the change list: kept as Old Standard's (the 52 lines
  then `designed`), or the long stems brought to the x-height letters'
  (a family's change in the core set: "Where a fault is mended", second
  row, with `reweight` on nine kept letters and what is built on them).
  Beside the Regular, whose stems are all one, the Italic's l stands at
  0.87 of the roman l's weight on its own scale where its n stands at
  0.99; the Didones' l at 0.87 to 0.93.
- The quality list overstates it. `checks.weights` takes its reference
  from n's first run at half the x-height, and an italic n's arch
  leaves the stem there: 195 units where the stem a third up is 162.
  "l 149 against 195" is 0.76; against the stem it is 0.88. The check's
  reference is left as it is until the designer has answered (the lines
  stay either way: 0.88 is at its tolerance of 12 %), but no line of
  this cluster should be read by its number.

On the sheet: one row n i u | l t f | b d h k | p q at 144 pt with the
marked places, Myia's two styles beside Old Standard's and Bodoni
Moda's pairs, and the running text's words chosen to hold them (hill,
full, little, tilt).

## The designer's round (2026-11-17)

On `proofs/2026-11/italic-against-regular-2026-11-17.pdf`, all six taken:

1. The bowls of n o d p q (and what shares them: b a g h m u) and O
   wider, by about a tenth of the counter: **taken**.
2. r's ball smaller by about a sixth, c's by a twelfth: **taken**.
3. v's thin stroke (and w y's) thinner by about a tenth: **taken**.
4. The ascenders raised to the Regular's, 4 % over the capitals:
   **taken**.
5. o's and O's overshoots taken back to the Regular's: **taken**; p's
   foot left as it is.
6. The long stems brought to the x-height letters' stem: **taken, as
   one family across the three scripts**, not the nine Latin letters
   alone. Old Standard lightens every stem that leaves the x-height;
   bringing up only l t f b d h k p q would leave ſ (beside f in ſt ſſ
   and the ligatures), ß, j's descender and the Greek and Cyrillic
   ascenders and descenders (β ζ η φ ψ, б д ф ђ ћ and their kind)
   lighter than the Latin beside them. The 52 `stroke Latin lc
   lighter` and `weight` lines are then mended, not marked designed.

Each change goes by "Where a fault is mended": a family's in the core
set by one script over the kept letters, each result through
redraw.py's gate and a sheet, **and** make_italic's constant or zone
scaling set to the same value for the tail. Nothing in the Regular.

### The order of work

Small first, then the proportions, then the zones and stems together,
so that each step starts from letters already final and no letter is
installed twice for the same reason.

| step | what | letters | how | model |
|---|---|---|---|---|
| A | balls, thin strokes (2, 3; the overshoots went to C, below) | r c; v w y (and what is built on them: ŵ ẁ ẃ ẅ ý ỳ ...); o O | a small script per change (the ball shrunk about its centre on the stroke's own curve; the thin stroke by `reweight` on the hairline only; the overshoot by moving the round's extremes and their handles), fitted by redraw.py, one sheet | Opus writes the scripts, Sonnet the sheet and the install |
| B | the bowls wider (1) | n o d p q, b a g h m u, O (and whether C G Q D follow: on the sheet) | an operation that cuts a bowl at its vertical middle and moves the right half out, stems and hairlines untouched, the advance and the right side growing with it; widths of a-z and A-Z checked to stay inside after it. The designer may prefer to draw some by hand: the operation gives candidates | Opus (the operation), the designer on the sheet |
| C | the ascenders raised and the long stems weighted (4, 6) | measured first: `italic_measures.py`'s `LONG` widened to ſ ß j and the Greek and Cyrillic letters with an ascender or descender; then every long stem `reweight`ed to the x-height letters' stem and the ascenders raised by 4 % of the cap height, in one install | one script over the family; make_italic's zone scaling and `WEIGHT` for the tail set to match | Opus (the measure and the script), Sonnet the sheets |
| D | what follows | the ligatures on f t l ſ (about 30, many drawn), the derived letters (đ ħ ł ƀ ɓ ɗ ƙ ...), the drawn Bold Italic glyphs whose bases moved | `make generate`; the drawn ones each against what the generator now gives (redraw.md's steps 7 and 8, phase 8's step) | Sonnet |

**Step A, 2026-11-17**: `scripts/italic_harmonise.py` (the
constructions, each redrawn and gated as redraw.py does; the numbers
calibrated on italic_measures' relation and printed by each run),
candidates on `proofs/2026-11/italic-harmonise-a-2026-11-17.pdf`
(Regular | today | step A, overlay, words):

- r's ball scaled 0.81 about the top of its disc, c's 0.885, the neck
  blended back over 2.3 radii (1.9 left a 7.9-degree kink in r's
  neck); the advance loses what the right edge lost (r 819 -> 804,
  c 808 -> 799). Relations 1.06 and 0.95, inside.
- v's and w's rising thin strokes 10 units thinner across, the curves
  quartered before the move (unquartered, the band moved only at the
  stroke's far nodes and v lost 2 units where it is measured).
  v's relation 1.07, inside. y has no such stroke: its right stroke is
  its stem; not changed.
- **The overshoots moved to step C.** The Italic's whole lowercase
  reaches -23 (o c e a s d b, ο о с, and x n u with their exit hooks),
  every round capital -35 and 1473 (O C G S Q Θ О С Э); the Regular's
  -16, and -28 and 1462. o and O alone would stand out of line with
  their neighbours: it is a zone, made in one install with the
  ascenders (step C), the tail by make_italic's zone scaling.
  italic_harmonise.py's `overshoot` is kept for it (it moves a glyph
  along the italic angle by height); not run in step A.

**Step B, 2026-11-17**: `scripts/italic_bowls.py` (the operation; tests
in tests/test_italic_bowls.py), candidates on
`proofs/2026-11/italic-bowls-b-2026-11-17.pdf` (Regular | today |
step B, overlay, words). Nothing installed; built while step A waits
for the designer (B touches none of r c v w).

- Each counter is found on the row through the middle of the zone
  (deslanted): the white between two ink runs (m has two; C and G,
  open on the right, run from the left side's inside to the ink's
  right edge). Everything right of the counter's middle moves out by
  `WIDEN` units, eased in by smoothstep over the counter's middle 60 %,
  so stems and thick sides move whole or not at all and only the
  near-horizontal hairlines crossing the band stretch. Anchors move
  with it; the advance grows by the same units, both sidebearings
  stay. Only the curves reaching into the band are quartered before
  the map: quartering b's short curve at its stem's foot let the
  redraw drop the stem's edge node.
- Units: n 34 (h m u with it), o 42, d p q 40 (a b g with them), O 140
  (Q C G D with it when named). Relations after: counters n 0.703, o
  0.880, d p q 0.829, b 0.880, O's width 0.959, all inside; widths n
  1.003, o 0.925 (the range ends at 0.931), a-z 0.952, A-Z 0.966 (0.981
  with C G Q D), hairlines o and n's arch inside.
- **a's advance leaves the range**: 1.083 -> 1.125 against 1.026-1.085
  (it was at the edge already). For the designer: a widened as its kin,
  or a's bowl left, or widened with its sidebearings taken in.
- b passes the gate at tolerance 1.5, not 2 (`TOLS`). G's bar and beak
  stretch with the band (they lie in it): on the sheet.
- **The designer's verdict, 2026-11-17**: all taken, C G Q D with O
  (judged in running text: `proofs/2026-11/italic-bowls-b-text-2026-11-17.pdf`,
  today | O Q only | O Q C G D; O and Q alone stood wider than C G D
  beside them), and a widened with its kin, its advance past the range.
  Installed the same day, marked drawn, lib org.myiadidot.redrawn
  "harmonise": "bowls".
- What followed, 2026-11-17/18. **Recipes placed by coordinates did not
  follow** the wider bases, each set by hand to where its base moved:
  ɰ (ɯ's last stem +68, ɥ's descender +34; in the Bold Italic, whose
  m is drawn, ɥ +35, 32 once scaled), ₡ (its slashes +70, the middle
  of the wider C: the right one notched the Bold Italic's terminal),
  Ƈ Ɠ (the spur and its cut +140 in the Italic's recipe; the Italic's
  ƈ.sc ɠ.sc are drafted from them), ƈ.sc (+116 in the Bold Italic),
  smooth_joins' ɱ node (+68), and ₵ ₲ (their lines +70 in the Italic,
  as they stood before; ₵ +73 in the Bold Italic, and its ₡ given its
  own recipe there: the Italic's numbers strayed on the wider C and it
  fell back to emboldened whole). Look for
  the like after step C: `glyph_lint.py` on both italics and a render
  of every recipe on a moved base, not only the tests.
- u was installed again at tolerance 1: at 2 its crotch opened into a
  slit (glyph_lint's notch, 30 px); the script now refuses a fit with a
  notch the construction has not.
- n's left stem came out 1.5 units thinner at half the x-height (the
  redraw: its inner edge and its arch are one curve; bowls()' docstring
  for what was tried). The small caps take their drafting stem from n
  there, rounded to a unit (make_italic, `f"{stem:.0f}"`): 181 became
  180 and FontForge drafted every small cap again, with new kinks
  across them, and the Bold Italic's stroker lost ψ.sc's whole left
  arm on its new draft (test_sc_clearance found it). Mended in n, by
  hand after the install (its drawn mark says so): the inner curve's
  lower handle shortened along itself (390,335 -> 384,314), the stem
  191.4 again (HEAD 191.1), the drafts store as it was, only the small
  caps of the widened capitals drafted again. A stem that moves at XH/2
  moves every small cap: look there first after any redraw of n.
- The Bold Italic's drawn glyphs on the moved bases did not follow:
  step D. derived.py finds them against HEAD (Ƈ 15 % of C kept, Ɠ 7 %
  of G, ɖ 51 % of d, ɳ 36 % of n, ɠ 40 % of ɡ: drawn, so the old
  letter beside the wider base), with m, g.sc and the rest; Ƈ Ɠ's
  recipe there still has the old numbers (C G moved 145 and 148).
  Two of them, u and m, carry what is built on them in the run (ú ù û,
  ʉ, Q_u): made on the letter as the run spaces it, then the drawn one
  put back as saved, they stood 3-4 units off its anchors. u and m were
  moved (shape untouched) to where the spacing puts them now, so saved
  and spaced agree again as before step B. (drawn.stale cannot pick
  such glyphs: 44 of the Bold Italic's drawn glyphs were already stale
  at HEAD.)
- Found in the shaping report, left for step D: the Italic's ą ǫ ų are
  Old Standard's own outlines, not built from a o u, and Ǫ is drawn, so
  their bowls stayed as narrow as before (ǭ Ǭ, built on ǫ Ǫ, with them);
  ď, one of composites.SPECIAL taken whole, kept its advance and its
  caron's offset, so the caron stands 40 nearer the wider d's stem. To
  find the like: every letter whose NFD base widened but which did not
  (a dozen lines over HEAD's UFO and the new one).
- **Step D, first part, 2026-11-19** (uncommitted, for the designer's sheet
  `proofs/2026-11/italic-ogonek-d-2026-11-19.pdf`, Italic then Bold Italic):
  the Italic's ą ǫ ų Ǫ widened by italic_bowls.py with their bases (KIN:
  aogonek -> d's 40, oogonek o's 42, uogonek n's 34, Oogonek O's 140; the
  tail moves with the right half, as a's own foot did), ą ǫ ų then through
  italic_long.py for the overshoot; advances now equal their bases'.
  ď: make_italic's `ITALIC_VERTICAL_CARON` (data_italic) keeps its caron
  and advance as distances from d's ink edge (-110, +186), not as places;
  the generator did not move it because caroncommaaccent is no mark.
  Tests failing as intended (baselines NOT yet accepted): test_accepted
  (oogonek.sc; BI aogonek uogonek), golden shaping and corpus digest (4
  cases with ą ų), test_hinting's stale `cff dcaron:top1495 8`, test_quality's
  stale BI `aogonek wobble 1` `uogonek wobble 1`. Two that are not just
  baselines: test_stroke_gate's WIDTHS lacks uogonek (BI 1192 -> 1232), and
  test_knee_turns_one_way[uogonek] finds a bend at (332,159), 38 from the
  fixed knee (345,195): the BI ų's inner stem edge is slightly S-shaped at the
  crotch (u's is not). The designer's eye: a hand fix marked drawn, or taken.
  Still open in step D: the BI's drawn letters (u, m, Ƈ Ɠ ɖ ɳ ɠ ...).
- **Bold Italic bottoms, 2026-11-20** (sheet `proofs/2026-11/bolditalic-bottoms-2026-11-20.pdf`, approved): k m u x ƈ т ⱳ, drawn, stood at -23; every point at y -23 set to -15 (nodes and handles together), the letters built on them regenerated (`KEEP_DRAFTS=1 make generate`; reproduce clean). ɖ ɳ ɠ ɧ looked at: the saved drawn ones match the wider bases, the regenerated recipes notch; left. Small caps' overshoot (+23 Regular, +27 Italic) measured, 4 units at most: left on that day, set the next (below).
- **ſ and the f-ligatures, 2026-11-21** (sheet
  `proofs/2026-11/italic-long-c-fligatures-2026-11-21.pdf`, approved: "all
  approved"). Step C's install had left ſ (Old Standard's own, never drawn, so
  `--all` passed it) and the drawn fi fl ff ffi ffl f_j f_f_j (no character of
  their own) at Old Standard's top 1451 and stem 139, beside f at 1512 and 161;
  italic_ligatures.py builds f_b f_h f_k f_t and every ſ-ligature from them, so
  about 30 ligatures in both italics stood on the old f. Found by comparing,
  between 6eecb101^ and HEAD, every glyph whose base (NFD base, ligature parts)
  moved while it did not. `italic_long.py` now takes the drawn f-ligatures by
  name (`LIGATURES`, made as f: raised as f is); in a ligature only the stems
  light at their middle (under `LIGHT` of n's) are weighted, so fi's i keeps
  its own 157/164 and fl's l, thick only at its head, is weighted. Installed:
  ſ and the seven, stems 160-162, tops 1512.
  With it the Bold Italic's k, drawn 2026-11-04 (the counter's turn into the
  ball), stood at the old 1434 with an ascender stem of 238 (h l b: 259-265);
  the stroker's k from today's Italic k (top 1495, 67 nodes against 77,
  advance 1006 -> 1024) was approved on the same sheet. Generated, it showed
  the old fault again (the counter's turn into the ball 7 units past its
  extreme, between nodes): the curve split exactly at the extreme (762,788),
  shape unchanged, and k marked drawn again on the new letter.
  What it took in the Bold Italic: make_bold.part_ff splits the ff-ligatures'
  points below the baseline between the first f and the second f's ball at
  `FF_SPLIT` past the first stem's edge; the heavier stem brought that edge 11
  nearer the ball (now 3 past it), so 8 became 2. Taken into the lists, with
  the designer (2026-11-21): 16 wobble and kink entries in the Bold Italic's
  built ligatures (f_b f_h f_t f_k and their ff and ſ forms, f_j f_f_j:
  near-coincident node pairs where the stroker meets the joins, not visible
  at text size), for phase 8's long tail; and ſg, 0.012 tighter than the
  reference italics' range in the Bold Italic only (the heavier ſ's narrower
  right side). The Italic's `stroke` lines for ff ffl fl ſ fell.
- **Cyrillic long stems approved as they stand, 2026-11-19.** The Italic's
  б д ф ђ ћ ц щ џ (unchanged since step A, seen on the overlay sheet
  against step A's) were looked at by the designer and taken: no install
  through italic_long.py. Not measured against n's stem; the approval is
  of the look.
- The second sheet, approved by the designer 2026-11-18:
  `proofs/2026-11/italic-bowls-b-bold-italic-2026-11-18.pdf` (the Bold
  Italic at HEAD and now, the bowls and their followers) and
  `proofs/2026-11/italic-bowls-b-followers-2026-11-18.pdf` (the
  Italic's letters placed on the wider bases, ψ.sc ε.sc υ.sc).
- Ø ø, 2026-11-18 (`scripts/italic_slashed.py`, sheet
  `proofs/2026-11/italic-slashed-sc-rounds-2026-11-18.pdf`, approved with
  the Bold Italic following): they are single hand-redrawn outlines with
  the slash merged into the ring, so italic_bowls.py cannot widen them
  and they stood at the old O's and o's advance (1374, 883) beside the
  wider O o (1514, 925). Each is now the widened ring joined to the slash
  of the old letter: a straight bar of the old thickness and angle, put
  across the middle of the widened ring, its ends as far beyond the ring
  and as high and low as before (Ø's corners at -35 and 1473, ø's at -23
  and 884). The union itself is kept, not a redraw's refit of it: the
  counters are the ring's own arcs cut at the slash, a refit put a knee
  into the counter just past the slash. Tried first and found wrong: the
  slash moved point by point (thicker in the middle), kept at its lower
  end and moved at its upper (flatter, met the counters at other angles).
  Ø.sc ø.sc: ø.sc marked drawn and kept as it was (see below).
- **o.sc q.sc ø.sc not widened, deferred to phase 8.** The Italic's o.sc
  (1060) stands narrower than c.sc d.sc (1148, 1221) since step B, where
  the Regular's is the widest of the three. Found 2026-11-18, tried and
  taken out again: a FontForge draft of the widened O comes out square
  inside; widening o.sc with italic_bowls.py pushes the width into a
  straight right side; made as the small caps' own recipe makes a small cap
  of a capital (derive.enlarge from the widened O Q, the strokes measured
  on the old o.sc, `scripts/italic_round_sc.py`: stem, sides and top
  brought to the old o.sc's, an oval like O's, 1145 wide) it is right in
  the Italic. But o.sc is the measure of dozens of recipes (data_regular's
  ("O", "o.sc") band): a unit in its stem or sides moves n.sc s.sc g.sc ɴ ɢ ʛ
  by 1 to 6 units, which opens 2-degree smooth and kink entries in the
  quality lists; and the Bold Italic, whose o.sc is stroked from the
  Italic's, got a stem measure 13 heavier (313 -> 327) on the new shape, so
  ƙ.sc ƭ.sc ƴ.sc ʋ.sc n.sc made against it moved 13 and ƙ.sc fell to
  emboldened whole, ө.sc's union with its base failed. Holding the Bold
  Italic's o.sc as a drawn glyph does not help: a drawn glyph is put
  back at the end of the run, what is derived reads the stroked one
  while it runs. So: to be taken with the Bold Italic's o.sc in phase 8,
  where the measure has to be settled anyway (the script is kept for it,
  not run). Whole-glyph pins of the measure inside make_italic were tried
  and are no better (the upright frame pads the sides; the small caps of
  the rounds then differ by 32).
- Found with it: Bold Italic `test_greek_pairs` fails for μπ (-0.156, 0.006
  past the tolerance) at 6eecb101 as well, with the references as
  installed; listed in greek-pairs-BoldItalic.txt for the designer's eye
  (Charis and Libertinus agree against Myia).

After each step: `make generate`, `make reproduce`, `redraw_sweep.py`,
`make diffenator`, the second sheet with the Bold Italic, the quality
lines that fell deleted, baselines with their reports' digests; and
`italic_sheet.py` run again, which should show the finding gone and
nothing new outside. The italic kerning is computed from the shapes and
moves with them: `make pairs` after B and C.

## What is left to build

1. ~~The sheet~~ Built 2026-11-17: `scripts/italic_sheet.py`, rendered
   as `proofs/2026-11/italic-against-regular-2026-11-17.pdf` (11 pages:
   the table on two, a page per change-list entry and one for the long
   stems, running text at 24 and 12 pt, the change list with a box per
   entry to take or strike). It measures as italic_measures.py does
   (the run of 2026-11-17 gave the first run's findings unchanged) and
   draws each page's own measures only: a fresh `Cut` per measure, the
   discs of balls and counters found again as bold_measures finds them
   (`ball_disc`, `counter_disc`), the italics slanted back with their
   marks. Each finding page sets the Didone whose relation lies nearest
   Myia's; the long stems' sets Old Standard's and Bodoni Moda's. The
   running text has no Greek in any reference and no Cyrillic in Bodoni
   Moda (build/refs/); those places are left blank and say so.
2. The references' marked letters looked through once (`--marks`): on
   Myia's two styles every place was checked on 2026-11-15; on the
   references only the values' plausibility (EB Garamond's q, Old
   Standard's i entry).
3. ~~After the designer's round~~ Done 2026-11-17: all taken, the
   order of work above ("The designer's round").

- **Small caps' overshoot set to 20, 2026-11-20** (sheets `proofs/2026-11/smallcap-overshoot-{Regular,Italic,Bold,BoldItalic}-2026-11-20.pdf`, approved: "everything good"; each shows 21 glyphs, the re-accepted ones are 2, 72, 44 and 71). The capitals' 28 over 1434 scaled to the small-cap height is 20: the Regular's 46 base small caps (`scripts/sc_overshoot.py`, the extreme's own nodes and handles only, 15..30 over the zone; **not** scaling everything past the zone, which bent smooth nodes beside the extreme: the first method left about 100 new quality findings, this one about 40), the Bold follows in `make generate`, the Italic's drafts through `overshoot_scaled` (HEAD's scale, then the extreme alone to `SC_OVERSHOOT`), the drawn small caps of the three styles by `sc_overshoot.py --drawn-only` (the generators keep them as saved). Order matters: `make check-regular`, `make generate KEEP_DRAFTS=1`, then the drawn fix only if it is not in the UFOs yet, then `make reproduce`; a drawn fix made after a generate leaves what is built on it stale (`scripts/stale.py` lists it). Baselines taken with reasons: quality lists (8, 13, 13, 10 new against 13, 33, 18, 24 gone: the "only shrink" rule bent on net-smaller lists), hinting (the `oe.sc:top1060`-type, 1 or 2 per style), shaping (Italic 34254 and Bold Italic 28045 strings, 72 and 71 glyphs: IPA small capitals and the marks after them, at most 7 units; the Bold's 17 golden cases, s.sc 998 -> 997). Left: the new kinks in ɩ.sc and ꞷ.sc and the Italics' kinks in c.sc, ɔ.sc and ȼ.sc (about 40 findings listed in the quality files), for the designer's eye.
