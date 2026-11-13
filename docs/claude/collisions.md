# The collision sweep over letter-and-sign pairs (phase 1's specification)

Written 2026-11-11 (F6) from a reading of `kern_clear.py`,
`quality/kern_touch.py` and `quality/kern_coverage.py` at ab3f15bc.
Nothing was run for it. For the session that builds it (Opus); the fixes
by family that follow are phase 1's next steps and not specified here.

## What exists, and what it misses

- `kern_clear.clear` loosens the entries named in `kern_clear.PAIRS` until
  the inks keep `CLEAR` (20) units of white across; nothing finds pairs
  for that list.
- `kern_touch.touching` (`make kerntouch`) looks only at kerning entries
  with a negative value: `f?` `f!` `(j` `[j` have no entry and are never
  seen.

The sweep is a sibling, `scripts/quality/collisions.py`, built on the
same two pieces (`kern_clear.Ink`, `kern_coverage.Profiles`) so that
**the sweep's verdict and kern_clear's repair are one measure**: a pair
the sweep lists is a pair `kern_clear` would loosen if it were in `PAIRS`,
and a pair in `PAIRS` is never listed afterwards.

    python scripts/quality/collisions.py UFO [--out TXT] [--sheet PDF] [--show N]
    make collisions        # four styles: build/quality/collisions-STYLE.{txt,pdf}

It reads a UFO (outlines, kerning, groups), like its siblings; it writes
nothing into it.

## The pair sets

Glyph sets, taken from the font and not from lists of names, so that a
new letter is swept the day it is added:

| set | members |
|---|---|
| `LETTERS` | every glyph with an advance that `respace.classifier(font, 1, 1)` counts as a letter (encoded letters, their `.sc`, locl and other suffixed forms, ligatures of letters), without the superiors below |
| `FIGURES` | the ten figures of `make_bold.LINING_FIGURES`, their `…oldstyle` forms, and the `.pf` `.tf` `.zero` forms of both (not the figure space and dash that `FIGURE_NAMES` also holds) |
| `CAPITALS` | the members of `LETTERS` whose character is `Lu` (also the capital of a ligature's first part, `T_h`), and the lining figures |
| `CLOSERS` | `? ! ) ] } ” “ ’ * : ;` |
| `OPENERS` | `( [ { „ “ ‘ ¿ ¡` |
| `SUPERIORS` | the superior figures ⁰-⁹ and `ª º` (the note marks set after a word), by `make_bold.SMALL_SUFFIXES[0]` and the two names |

Pairs swept, left glyph then right:

1. `(LETTERS ∪ FIGURES) × CLOSERS`
2. `(LETTERS ∪ FIGURES) × SUPERIORS`
3. `OPENERS × (LETTERS ∪ FIGURES)`
4. the case forms, as `case` sets them in capitals: `CAPITALS × c.case`
   for each closer `c` that has a `.case` glyph, and `o.case × CAPITALS`
   for each opener; small caps are not set with case forms.
5. `OPENERS × CLOSERS` is not swept (`()` is nobody's text), nor marks,
   nor glyphs without an advance.

A triple such as `(f)` is its two pairs. About 1500 × 30 pairs a style;
see "Cost".

Each pair is measured **at the kerning it takes**: the value of
`kern_clear.kern_lookup(font)`'s `entry(a, b)`, else 0. So a kerned pair
that still touches is listed too, and one `kern_clear` has cleared is
not.

## The measure of white

`white(a, b, kern)`: how far b, set after a at that kerning, can still
move left before the inks meet; negative when they overlap (how far it
must move right to come free). In units, in steps of `kern_clear.STEP`
(2), found as `kern_clear.needed` finds its value:

- `Ink.touch` gets a parameter, `touch(a, b, kern, clear=CLEAR)`, the
  default as now (so `make reproduce` is unmoved);
- `white = max w in {…, -2, 0, 2, …, CLEAR}` with `not touch(a, b, kern,
  clear=w)`; searched down from `CLEAR`, and for an overlap up from 0 to
  `kern_clear.LIMIT`. `white == CLEAR` means clear: not listed.
- Cheap first: only pairs with `Profiles.gap(a, b, kern) < CLEAR + 2 *
  kern_coverage.STEP` are intersected (rows 10 units apart, widened two
  rows either way; the margin covers what the rows miss between them).
  The step-0 check below tests that this filter loses nothing.

Two kinds, as on kern_touch's sheet: **touch** (`white <= 0`: ink in
common, red) and **near** (`0 < white < CLEAR`, orange).

The measure is across only, as `kern_clear`'s is: an f's hook 15 units
above a question mark's top with no row in common is not found. Left so
on purpose (one measure); if the sheets show such a case, it is written
into TODO.md as a question for the designer, not built into the sweep
alone.

## Output

`--out` (and stdout), one line per glyph pair, sorted by white then
names; glyph names, since a list is grepped and tested by them:

    f question -34  f?  loosen 54   public.kern1.f question (12 of 14 members)
    uni0237 parenright.case 8  ȷ)  loosen 12   -

- name, name, white, the two as text (NFC, `kern_touch.label`), the
  loosening that gives `CLEAR` (`CLEAR - white`);
- last, as a help for the fixes by family: the most general kerning key
  pair (`keys(a, b)`, last first) of which at least half the member
  pairs inside the swept sets are listed, with the count; `-` where only
  the glyph pair itself is.

The last line, to stderr: `MyiaDidot-Bold.ufo: 212 pairs within 20 (61
touching), 48110 swept`.

`--sheet`: a PDF (memory: sheets as PDF), `kern_touch.draw` reused: per
sign one block, its pairs worst first, each as set and beside it at the
loosened value, `--show` (default 40) pairs a block, the rest counted in
the block's caption. Capitals with case forms in their own block.

## The exception lists and the test

`tests/data/collisions.txt` and `collisions-Italic.txt`, `-Bold.txt`,
`-BoldItalic.txt` (the names the other lists use, not `-Regular`):

    # Letter-and-sign pairs with less than kern_clear.CLEAR of white (scripts/quality/collisions.py: left right white); fixing one = deleting its line.
    f question -34                   # 2026-11-12 known at the start: f?
    uni0283 parenright 6             # 2026-11-14 meant: ʃ's hook under the bracket, reviewed on proofs/…

`tests/test_collisions.py`, per style, on the UFO (no build needed):

1. a pair found and not listed fails, with the line to look at and the
   command for its sheet;
2. a pair listed and no longer found fails ("fixed: delete its line"),
   as the other lists do;
3. a listed pair whose white is more than 4 units under the listed
   value fails (it got worse; 4 covers a run's rounding, not a change).

Rule 2 is what makes the list shrink, as for the other lists
(`docs/claude/tests.md`); a line is added only with a dated reason, in
the commit that brings the pair.

A pair that is to stay (reviewed, `meant` in its comment) stays in the
list with its date and proof; there is no second list.

Tests of the tool itself, in the same file:

- two rectangles as glyphs of a font made in the test, 12 units apart:
  `white == 12`; overlapping by 7: `white == -8` (steps of 2, the first
  clear value); 20 apart: not listed;
- the Regular with `kern_clear.undo` applied in memory lists `( ɲ`
  (`parenleft uni0272`, which `PAIRS` holds): what `kern_clear` clears,
  the sweep finds;
- the row filter: for the Regular, the pairs listed with the filter off
  (`--exact`, every pair intersected; slow, marked for the slow tier)
  are those listed with it on.

## Cost

Per style about 45 000 pairs: profiles for 2197 glyphs once, the row gaps
in numpy, intersections only near `CLEAR`. To be measured when built;
over 20 s a style, the test runs the four styles in the suite's parallel
workers or moves to the slower tier (TODO.md's T8), and the page says
which.

## Order of carrying out

1. `Ink.touch`'s parameter; `collisions.py` with `--out`; the tool's
   three tests. `make reproduce` unchanged.
2. Run for the four styles (font-measure). Check against what the
   renderings showed: `f?` `f!` listed in Regular, Italic, Bold; `(j` in
   Regular and Bold; `[j` in both italics. One of them missing is a fault
   in the sets or the measure, to be found before going on.
3. `--sheet`, `make collisions`; the lists read for families, a summary
   by family into TODO.md under phase 1 (how many pairs, which key pairs
   cover them).
4. The exception lists as found, each line "known at the start", and
   `test_collisions.py`; `docs/claude/spacing.md` and `tests.md` get
   their paragraphs, `commands.md` the command.
5. Then phase 1's fixes (Sonnet): entries in `kern_clear.PAIRS` by
   family, as products of named sets like those already there; every
   style regenerated; the lists' lines deleted as they clear. A family
   where `kern_clear` refuses an entry because its members take
   different kernings ("take [...]" in `clear`) needs the entry split by
   those values, not a hand-set kern in a style.

## Built 2026-11-13 (Opus): what came out against the above

Steps 1-4 carried out as written; `make reproduce` is untouched (only
`Ink.touch` got its parameter). Where it differs or adds:

- **Cost.** 3 s a style with the row filter, 6 s with `--exact`
  (pathops is fast), so the filter test runs in the normal suite, not a
  slow tier; the whole test file takes about 16 s on four workers.
- **Swept**: 53 847 pairs a style. Listed at the start: Regular 383
  (289 touching), Italic 1798 (1543), Bold 306 (266), Bold Italic 1665
  (1478); the lists are `tests/data/collisions*.txt`, every line "known
  at the start". The invariant holds in all four styles: no pair that
  `kern_clear.PAIRS` decides is listed, and with `kern_clear.undo` the
  Regular lists `( ɲ` again (both in the test).
- **Step 2's check against the renderings** held for the Regular (`f?`
  -12, `f!` -30, `[j` -30, `(j` 16) and the Bold (`f!` -60, `f?` -50,
  `(j` -10, `[j` -6), not for the italics: their `f?` (32 and 30 units
  of white across), `f!` (100, 70) and `[j` (56, 64) are clear, both
  today and at 30f20e1a, before F7's redraw. What the renderings showed
  in the italics' `[j` is j's ball coming near the bracket's foot on the
  diagonal, which the measure across does not see by design: a question
  for the designer (TODO.md, phase 1), not a fault in the sets. The
  redrawn italic f instead now runs into `(` and `[` (`(f` -102, `[f`
  -132; clear at 30f20e1a), which the renderings called "very tight".
- **The sheet** groups by sign (the glyph on the other side of a letter
  or figure), the case forms after the plain signs; each pair as set and
  beside it loosened to CLEAR, six to a row, `--show` a block.

## The first fixes, 2026-11-13

Reviewed on `proofs/collisions-review-2026-11-13.pdf`: all three shown
taken as faults, to be loosened. Then, on the before | after sheet, 20
units still read as touching: a sign beside a letter wants more than the
floor against ink meeting. Chosen on running text
(`proofs/sign-clearance-text-2026-11-13.pdf`,
`-open-close-`, `-exclam-question-`): 100 after an opening sign, 60
before ! ?, 40 before the other closers (kern_clear.clearance), and
every sign beside every letter cleared, not only the families below; the
sweep measures each pair against the same clearance. What follows was
the first step, at 20. Carried out in `kern_clear.entries()`
(spacing.md says which pairs), the italics' [j by hand at +60 (of
`proofs/italic-bracket-j-candidates-2026-11-13.pdf`). The sets moved
from this script into `kern_clear.sets()`, one definition for the sweep
and the repair. Found on the way: guarded members were left out of a
group entry's value but took it, so the Bold's (ɉ stayed 2 units short
and the ogonek letters before ɉ ʝ ϳ were never cleared (letter pairs, not
swept); mended in kern_clear. After: Regular 313 pairs (from 383),
Italic 938 (1798), Bold 240 (306), Bold Italic 795 (1665); before | after
on `proofs/collisions-loosened-2026-11-13.pdf`. Left for phase 1's
Sonnet sessions: superiors after f and the hooks, accented small caps
before closers and superiors, the Greek capitals with breathings after
the openers, ) ] after η's group, and the rest of the lists.
