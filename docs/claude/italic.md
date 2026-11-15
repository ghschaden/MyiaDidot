# The Italic against the Regular: phase 6's measure

Phase 6's first step (TODO.md), specified 2026-11-15 on Fable; nothing
here is built or measured yet. Opus writes the script and the sheet from
it; the numbers marked "proposed" are set at the first run (last
section). The model is F4's `docs/claude/bold.md` and its two scripts.

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
1000 em. Then, as bold_targets.py, every length over the style's own
stem (the lowercase's for lowercase, the capitals' for capitals) or over
its zone (x-height, cap height), areas over the zone squared. The
italic's stem is taken a third of the way up (`derive.straight_stem`: an
italic stem swells towards the branch), the same in every font.

Two kinds of measure:

- **Relation** (both styles have the feature): r = the Italic's value on
  its own scale over the Regular's on its own. Myia's r against the
  range of the three Didones' r.
- **Italic's own** (the Regular has no counterpart: entry and exit
  hooks, the single-storey a, f's descender): the Italic's value on its
  own scale against the three Didone italics' values directly.

## What is measured

| | on | how | kind | have |
|---|---|---|---|---|
| stem | n (lc), H (uc); median of i l n m h u, of H I E L | width a third up, deslanted | relation, over the zone | `stems()`, at another height |
| hairline | o top and bottom, e's bar, n's arch at its thinnest, v's thin stroke; H's bar, O's top, A's thin stroke | the ink's run across the stroke where it is thinnest: vertical at mid width for o O e H, across the lean for v A (strokes.py's narrowing), the least over the arch's columns for n | relation, over the stem (the contrast) | new; o's as `derive.strokes` |
| colour | a-z together, and each | ink in the x-zone over advance x zone (colour.py's zone colour) | relation | colour.py, per style |
| width | a-z's advances summed; n, o, e, a each; the same for A-Z, H O | advance over x-height (cap height) | relation | bold_measures |
| counter | n o e (b d p q) | counter's width over the stem | relation | bold_measures |
| ball | c f r y j (g's ear) | the widest disc in the terminal's region, over the stem | relation | bold_measures `BALLS` |
| serif, capitals | H I (E L's feet) | length: the foot's reach past the stem's edge, each side, at the baseline row; thickness at the tip and at half the reach (the ink's vertical run in that column) | relation; length over the stem, thickness over the hairline | new |
| serif, lowercase feet | p q (the descender's foot), l's head | as the capitals' | relation | new |
| hooks | n's entry and exit, i, u's exit | reach past the stem's edge at the zone's line; thickness where thinnest | italic's own | new |
| overshoot | o against x and z (x-height, baseline), O against H, b d l against H (ascender) | the round's edge past the flat one, over the zone | relation | zones.py per UFO; the references by bounds |
| stress | o, O | the angle of the line through the ring's two thinnest places, after deslanting | relation (a difference in degrees) | transitions.py's profile |
| slant | n, H, l | the stems' angle | shown only | checks.py `slant` |

Not measured as a relation: joins (bold_measures reads a column beside
the stem; on a deslanted italic arch that is not the same place as on the
roman's) and whatever counts different counters in the two styles.

Traps known from the docstrings, to check on the first run before any
number is believed:

- The Italic's a is single-storey: `BALLS["a"]` finds the bowl's top or
  the stem there, not a ball. a leaves the ball family; "c a f r y" in
  TODO.md's wording is c f r y for the relation.
- The Italic's f has a hook below since 2026-11-11 (a ball there too):
  the region for f's ball is the top one only.
- `stems()` wants edges straight within 1.5 % over its rows: an italic
  stem that swells may not be found; then `derive.straight_stem`'s
  slice, and the report says which was used.
- An italic n's counter is open below (it sees ink in seven of eight
  directions): the counter's width is comparable, its aperture is not
  the Regular's gap between feet.

## The gate

Per measure, Myia's position against the Didones' range as
bold_targets.py's `position`: 0 inside, +6 six per cent above the
highest, -9 nine below the lowest.

| position | with | reads as | goes to |
|---|---|---|---|
| inside | | the italic of this roman | nothing |
| outside by 3 % or more (proposed, `OUTSIDE`) | | a candidate | the sheet |
| outside by 3 % or more | Libertinus and Charis both on the range's side of Myia | another typeface | the change list |
| outside by 10 % or more (proposed) | | another typeface | the change list |

- A measure whose three references spread by more than 30 % of their
  median between lowest and highest does not discriminate: shown, never
  gated (proposed; the first run prints each measure's spread).
- Stress is gated in degrees: more than 5 beyond the range (proposed).
- **Kept, never on the change list**: the capitals' contrast (H's bar,
  O's top, A's thin stroke over the capital stem). The report prints the
  rows with "kept: declined 2026-10-21 and 2026-11-02".
- Expected and to be confirmed, not found: colour about 5 % lighter,
  width about 5 % narrower (TODO.md's assessment). If the Didones'
  italics are 3-10 % lighter and narrower than their romans, that is
  inside.
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

## For Opus: what to build

1. `scripts/quality/italic_measures.py`: bold_measures' machinery
   (`measure`, `run`, `gains`) with the pairs above, a third of the way
   up for the stem, and the new measures (hairline, serif, hook,
   overshoot, stress). `--json build/quality/italic-measures.json`.
   Each new measure with a test on a drawn shape whose value is known
   (a stem of 80 with a serif of 60 by 12; a ring whose thin places lie
   at a known angle).
2. `scripts/quality/italic_targets.py` (or bold_targets.py given the
   pairing as an argument): own-scale values, relations, positions, the
   spread per measure, the verdicts of the gate;
   `build/quality/italic-targets.md`.
3. Run by font-measure; the traps above checked against a rendering of
   the letters with the measured places marked, before the table is
   read.
4. The proposed numbers set from the spreads and written here; then the
   sheet.
