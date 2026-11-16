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
| `FIGURES` | the ten figures of `make_bold.LINING_FIGURES`, their `…oldstyle` forms, and the `.tf` `.zero` forms of both (not the figure space and dash that `FIGURE_NAMES` also holds) |
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

Reviewed on `proofs/2026-11/collisions-review-2026-11-13.pdf`: all three shown
taken as faults, to be loosened. Then, on the before | after sheet, 20
units still read as touching: a sign beside a letter wants more than the
floor against ink meeting. Chosen on running text
(`proofs/2026-11/sign-clearance-text-2026-11-13.pdf`,
`-open-close-`, `-exclam-question-`): 100 after an opening sign, 60
before ! ?, 40 before the other closers (kern_clear.clearance), and
every sign beside every letter cleared, not only the families below; the
sweep measures each pair against the same clearance. The superiors
after: superior figures 60, ª º 20 (`proofs/2026-11/superior-clearance-text-2026-11-13.pdf`),
and with them the lists are empty. What follows was the first step, at 20. Carried out in `kern_clear.entries()`
(spacing.md says which pairs), the italics' [j by hand at +60 (of
`proofs/2026-11/italic-bracket-j-candidates-2026-11-13.pdf`). The sets moved
from this script into `kern_clear.sets()`, one definition for the sweep
and the repair. Found on the way: guarded members were left out of a
group entry's value but took it, so the Bold's (ɉ stayed 2 units short
and the ogonek letters before ɉ ʝ ϳ were never cleared (letter pairs, not
swept); mended in kern_clear. After: Regular 313 pairs (from 383),
Italic 938 (1798), Bold 240 (306), Bold Italic 795 (1665); before | after
on `proofs/2026-11/collisions-loosened-2026-11-13.pdf`. Left for phase 1's
Sonnet sessions: superiors after f and the hooks, accented small caps
before closers and superiors, the Greek capitals with breathings after
the openers, ) ] after η's group, and the rest of the lists.

## Letters against letters: capitals before ascenders (2026-11-13)

Not swept here (signs only, measured across). Üb on the pangram page
(the italics' top serifs meeting on a diagonal) is kept clear by
`kern_clear.ascender_entries` with its own measure every way above the
x-height (`Ink.white_above`, ASCENDER_CLEAR 60; spacing.md), held by
`tests/test_collisions.py::test_capitals_clear_ascenders`. The same for
a capital before a lowercase mark above (N ǐ, H ȉ, Γ ῖ):
`kern_clear.accent_entries`, ACCENT_CLEAR 40,
`test_capitals_clear_marks_above`.

## The guard's result held by a test (specified 2026-11-16 on Fable; the first two assertions built the same day)

The case (open-for-fable.md, phase 3): the italic rule dropped the group
pairs b v, b j, o j; `kern_clear.guard` walks the kerning's group pairs,
so the guarded members those pairs had held (ᵬ ổ ồ) lost their
exceptions and met their neighbours. Mended by keeping such a pair at 0;
found by reading a shaping report. What was asked for: a rule that a
generator's kerning change is checked over every member, kerned or not.

Counted first (2026-11-16, on the UFOs, `Profiles.gap` at the value each
pair takes, the guarded letters of `kern_clear.guarded` against every
encoded letter of their script, 50 304 pairs a style, 2 s):

| | Regular | Italic | what they are |
|---|---|---|---|
| under GUARD, no entry at all | 2640 | 8119 | below |
| under GUARD at a positive value | 68 | 239 | the reviewed ą į ų before j, ζ before breathings; the rest 36 to 39 |
| under GUARD at a negative value | 25 | 181 | the guard's own results: 40 in the Regular, 37 in the Italic |
| kerned group pairs of the source style gone from the generated one, a guarded member then under GUARD | (the source) | 0 | Bold and Bold Italic 0 too (9, 0, 4 keys gone, all harmless) |

So "every member, kerned or not" is not one rule but two, and the
second is not the guard's:

1. **What the guard decides is held by a test, on the result.** No step
   of a generator has to remember the guard; the test reads the UFO
   after all of them, as `test_collisions.py` does. Three assertions,
   per style, in `tests/test_collisions.py`:
   - *Kept keys.* Every group pair kerned (≤ 0) in the style this one
     is generated from (Regular for Italic and Bold, Italic for Bold
     Italic), whose group on either side holds a guarded member of that
     side, either is a key of this style's kerning (at any value, 0
     too), or every guarded member beside every member of the other
     side stands at GUARD or more unkerned. This is the phase-3 fault
     as a set comparison; it holds today in all three styles with no
     list.
   - *Held white.* For every guarded letter and every member of the
     other side of a pair its group has (the pairs `guard` walks, and
     the exceptions it wrote): `Profiles.gap` at the value the pair
     takes ≥ GUARD − 4. The 4 is the Italic's 37: the guard measures
     before a later step rounds (not looked for which; if it is one
     step, mend it there and take the 4 back to 1). Pairs listed in
     `kern_clear.PAIRS` as reviewed are left out by reading PAIRS, not
     by a second list.
   - *Positive pairs.* `guard` skips a group pair above 0 (`v > 0`):
     a pair loosened for the model may still be too little for the
     member's mark. Take the condition out (measure at any value); the
     68 and 239 rows are what it then answers, less the reviewed ones.
     This changes kerning: its own commit, the shaping report read for
     loosenings only, as for any kern_clear change.
   The measure is the guard's own (`kern_coverage.Profiles`, GUARD),
   not the sweep's `Ink`: a test that measures otherwise than the step
   it holds disagrees with it at the limit.
2. **The unkerned rest is not a guard fault and gets no blanket rule.**
   The 2640 and 8119 are pairs with no entry on either side's group.
   Most are nobody's text: a lowercase letter or a capital before a
   Greek capital with its breathing at the left (three fifths of the
   Regular's, four fifths of the Italic's: such a capital begins a
   word), IPA letters beside Vietnamese or Croatian accents (ʐ ǰ,
   ɠ ȉ). Others are never set as measured: f ſ before ȉ take the short
   f (`short_f_entries`), so the UFO's pair is not the text's. An
   invariant over all of them would be mended by thousands of
   exceptions for pairs no one sets. They are found as phase 1 finds
   signs: by family, each with the text that sets it, entered in
   kern_clear (`accent_entries`, `ascender_entries` are two such) and
   then swept. Candidates seen in the count, for the designer, none
   judged: the italics' Ľ before ascenders and before Ɓ Ɗ Ƥ (Ľb −132),
   Ầ before Ȉ Ï in capitals (−155, −103), ổ ể before Y V W T in the
   italics (a lowercase before a capital: only in mixed setting), χ ϟ ϡ
   ξ ζ before ϳ, ї after ї ё ҳ җ (−7 to 28), Q before ǰ ɉ ʝ.

Order: the kept-keys and held-white assertions first (no font change;
whatever held-white finds beyond the table goes into
`tests/data/collisions*.txt` with its date, as the lists' rule says);
then the positive pairs in `guard`; the families of point 2 only as the
designer names them. The count's script is not kept: the test is it.

**Built 2026-11-16 (Opus), the first two:** `test_guard_keys_kept` and
`test_guard_white_held` in `tests/test_collisions.py`, no font change.
Where it differs from the above:

- *Held white has no tolerance and no list.* The Italic's 37 was not a
  rounding after the guard: every pair under GUARD (27 Regular, 191
  Italic, 12 Bold, 161 Bold Italic, all at 36.5 or more) has its key
  written by `clear()`'s own Ink measures, nearly all `accent_entries`
  (a capital before a lowercase mark above, Y ỉ, V ȁ, W ĭ) and their
  members' exceptions beyond the group (Ư ẫ), two `entries()`. The guard
  finds the key already there and leaves it, so the pair is held by
  ACCENT_CLEAR on `Ink.white_above` (within SAMPLE), not by GUARD on
  `Profiles`: the two measures differ by up to 3.5 units at the limit.
  The test leaves out the pairs whose entry, or the group entry it is an
  exception to, is one of `kern_clear.measured(font)` (PAIRS among
  them); what is left holds at GUARD exactly in all four styles.
- *Kept keys* measures a dropped pair's members at the value they take
  now (a less specific entry, or none), against GUARD.
- Both read kern_clear's own lists: `measured()` (what clear() measures
  with Ink) and `guarded_all()` (the letters guard() walks, with
  GUARDED_AGAINST's) were drawn out of clear() and guard() for it,
  nothing else changed (kern_clear finds nothing to change in any style).
- Checked on a copy of the Italic with the guard's exceptions and the
  Regular's guarded group pairs taken out: both tests fail (ᵬ's kind,
  f ĭ at -60 with its mark 114 units into f's hook).

Left: the positive pairs in `guard` (its own commit, kerning changes).

## The italics' `„`: neither kerning nor a narrower sign (2026-11-16, Fable; the low quotes built the same day)

The question left open (open-for-fable.md): the italics' `„` before a
slanted foot, the sweep's largest family, to be loosened pair by pair or
drawn narrower. Read from the UFOs, it is neither; the sign stands in
the wrong place in its advance.

- `„` and `‚` are composites of `quoteright` moved down 1242, in the
  Italic at the Regular's offsets `(0, -1242)` and `(372, -1242)`.
  The Italic's `quoteright` is placed for its height (left bearing 285,
  right −87: a sign up at the capitals leans that far right). Moved
  straight down, the low quote keeps the high one's place: left bearing
  285, right −87 at the baseline, where the comma has 44 and 181. The
  Regular's has 122 and 128.
- So it overhangs its advance by 87 into whatever follows, and
  kern_clear answers with an entry for nearly every letter: 1432 pairs
  with `„` on the left in the Italic (mean +149), 1420 in the Bold
  Italic, against 2 in the Regular. The lists are empty today because
  of those entries, not because the sign is right; and before a space
  or a sign with no entry nothing mends it (a wide hole before `„`, none
  after).
- The mend is in make_italic, where a composite's parts are placed: a
  part moved down by `dy` goes left by what the slant gives over that
  height. The pure shear is `SLANT × 1242` = 337, which is too much
  here (the high quote was itself moved left of its sheared place by
  about 160 when the italic signs were centred): take the shift that
  gives `‚` the comma's bearings (about 240; one source of truth, the
  low quote stands as the comma does), and `„` the same with its 372
  between the two. The Bold Italic follows from the Italic.
- After it: kern_clear's `„` entries are made anew by the run and most
  fall away (the test's rule 2 does not apply, they are not listed);
  the shaping report shows `„` pairs tighter by about the shift less
  their old entry, to be read for any pair now under CLEAR; `“` as a
  German closing quote is not touched.
- The same reading over all composites: 36 in the Italic have a part
  moved up or down by more than 300 at exactly the Regular's offsets:
  `: ; ·` and the Greek question mark, `÷ ±`, the dot signs U+2056 to
  U+205E, the denominators and inferiors, ⅐. Whether the colon's upper
  dot leans with the text (0.27 × its height, about 170) and the
  inferiors stand left of the superiors by the slant is the designer's
  to see on a sheet; none judged here, and no change without it.

Order: the low quotes first (one rule in make_italic, `make generate`,
the shaping report, the sweep's sheet for `„`); the 36 on one sheet for
the designer before anything else moves.

Built 2026-11-16: `data_italic.ITALIC_STANDS_AS` names the sign each low
quote stands as (the comma), and `make_italic.stand_as` moves the
composite's parts together, on the final bearings, until its left
bearing is that sign's; the advance stays. The shift is measured, not a
constant: 241 in the Italic. The Bold Italic takes the Italic's offsets
through `tx_offset` (250; its `‚` stands within 9 units of its own
comma, `„` on it). Bearings after: Italic `‚` 44 and 180, `„` 44 and
154; Bold Italic `‚` 84 and 196, `„` 93 and 170. `„`'s right bearing is
less than the comma's by the high double quote's own tightness (its
advance is the Regular's 900 on a wider single quote); left so, as `”`.
kern_clear's entries with `„` on the left fell from 1432 to 329 in the
Italic and from 1420 to 155 in the Bold Italic (what is left: the
letters reaching left below the baseline or at it, f ſ and their kind,
Ά, the capitals with a slanted foot); nothing else in the kerning
changed, and the sweep stays empty in all four styles. What a reader
sees: the hole before `„` closed by the shift, and the white after it no
longer kern_clear's least everywhere but the sign's own (wider than
before by up to the shift where the old entry was small). Held by
`tests/test_collisions.py::test_low_quotes_stand_as_the_comma`; sheet
`proofs/2026-11/low-quotes-italics-2026-11-16.pdf`.
