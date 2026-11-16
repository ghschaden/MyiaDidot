# The Italic against the Regular: phase 6's measure

Phase 6's first step (TODO.md), specified 2026-11-15 on Fable and built
the same day: `scripts/quality/italic_measures.py` (measures, gate and
table in one; tests/test_italic_measures.py), its first run read and the
specification corrected by it ("The first run" below). Not built: the
sheet. The model is F4's `docs/claude/bold.md` and its two scripts.

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

## What is left to build

1. The sheet (`scripts/italic_sheet.py`, as bold.md's trial sheet): the
   table, the rows at 144 pt for the findings above with the measured
   place marked (the marks are in `Cut.marks`, `draw_marks` draws
   them), the running text, the change list above. Opus.
2. The references' marked letters looked through once (`--marks`): on
   Myia's two styles every place was checked on 2026-11-15; on the
   references only the values' plausibility (EB Garamond's q, Old
   Standard's i entry).
3. After the designer's round: what is struck gets its date here; what
   is taken goes by "Where a fault is mended".
