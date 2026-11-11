# Redrawing a core letter (phase 5 and after)

CLAUDE.md's ground rules apply. What this is for: TODO.md, phases 5-8.
The tool: `scripts/redraw.py` (tests/test_redraw.py); the sheet:
`scripts/redraw_sheet.py`; the sweep after an install:
`scripts/redraw_sweep.py`. Pilot of 2026-11-10: n a e o s g of the Italic,
`proofs/italic-redraw-pilot-2026-11-10.pdf`.

## What a redraw is

The letter's shape is kept, its nodes are rebuilt. Today's outline is the
target; the tool sets a new node structure on it and fits one cubic
between each two nodes. Nothing is designed: a letter that needs another
shape (n's slant, s's weight) goes back to the designer, see the last
section. The output is a candidate; the review on the sheet decides.

The structure is not copied from the Regular's letter. Only o, and partly
s c, have a Regular counterpart of the same construction (the italic n has
hooks where the roman has serifs). It is derived from the target by the
rules the Regular is drawn to, which gives the Regular's structure where
the letters correspond (o: 4 + 4 nodes) and works the same for the letters
with no counterpart (italic a e f g k v w y z, Greek, Cyrillic). The
Regular's node count is used as a yardstick only.

| node | where | the curve there |
|---|---|---|
| corner | the target turns more than 8 degrees at a node (`CORNER`) | each side keeps its own direction |
| line | the ends of a straight edge | leaves in the line's direction, so a kink there (1-8 degrees) is gone |
| extreme | the curve runs level or upright: true extremes in the font's own frame (the slanted one), found on the curve, not taken from old nodes | level or upright exactly |
| extra | only where one cubic between two of the above is further from the target than the tolerance | the target's direction there |

- A line of 8 units or less between two curves (`SHORT_LINE`: a crotch's
  leftover in n a g) is closed, its ends drawn together.
- An extreme nearer than 12 units (`MIN_SPAN`) to a corner or a line's end
  gets no node; nor one that lies less than 5 units (`BULGE`, checks.py's
  own limit for `extreme`) beyond its neighbouring nodes: a serif's
  bracket leaning over by the slant (H would gain four nodes, b h l one).
- The tolerance is 2 units (`TOL`), for a short curve a hundredth of its
  length but at least 1 (`FINE`, `span_tol`): a ball's neck is held closer
  than a bowl.
- If the redraw comes out with more nodes than the target has, the
  tolerance is widened (x1.4, twice at most) and that result taken when it
  brings the count down within the gate's 4 units; the report's `tol` and
  a remark say so.
- An extra node is put at the inflection if the span has one, else at the
  old node nearest the worst place, else where the span has made half its
  turn; a span is split twice at most (`DEPTH`).
- Then all handle lengths of a contour are found together so that two
  curves meeting smoothly share one curvature (`fair`), as far as each
  curve stays within one and a half times its tolerance; where that is
  not possible the joint keeps a jump and the report says so. No handle
  is made more than half longer or shorter than its plain fit for it
  (`FAIR_SPAN` 1.5). The
  Regular's own plain letters have jumps of 0.0-0.45 (o: 0.01); the
  Italic's as they are 0.6-0.8.
- Nodes and handles are on whole units. A handle off the axes is rounded
  to the neighbouring whole point that keeps its direction best, so the
  `smooth` check stays quiet.
- No curve bends the other way at one end: after the rounding a handle
  that reaches past the point where the curve's two directions meet is
  drawn back a unit at a time (`one_bend`; the notes say "a handle
  shortened"). The Regular has no such curve in a-z A-Z, Old Standard's
  Italic 16.
- Width, anchors, lib, contour order and direction are kept.

## The steps for a batch

One style, about 20 letters, nothing written to `sources/` before step 6.

1. Fit:

       .venv/bin/python -I scripts/redraw.py sources/MyiaDidot-Italic.ufo \
           build/redraw/BATCH.ufo a b c ... --json build/redraw/BATCH.json

   One line a glyph: nodes before -> after, the Regular's count, the
   distance from the target, the worst curvature jump before -> after,
   the gate's verdict. About 4 s a letter. Exit status 1 if any glyph
   fails the gate or is refused.
2. Read the lines. `candidate`: go on. `FAIL` or `[look: ...]`: next
   section. The notes of each glyph (kinks made smooth, lines closed,
   extra nodes and why, joints left with a jump) are in the JSON under
   `notes`; read them for every glyph, they say what changed.
3. Correct the structure where needed in
   `scripts/data/redraw-STYLE.json` (read by default; the format is in
   redraw.py's docstring: `extra`, `drop`, `corner`, `smooth`, `keep`,
   `line`, `tol` per glyph name) and fit again. The spec is the record of every decision
   that is not the rules': keep it in the repository.
4. Sheet (PDF, for the designer):

       .venv/bin/python -I scripts/redraw_sheet.py proofs/NAME-DATE.pdf "a b c ..." \
           --col "Old Standard=sources/oldstand/OldStandard-Italic.ufo" \
           --col "today=sources/MyiaDidot-Italic.ufo" \
           --col "redrawn=build/redraw/BATCH.ufo" \
           --over today,redrawn --words "words made of the batch's letters"

   Node views (a ringed node is a smooth one off the extremes: what the
   gate remarks), the overlay today red / redrawn black, 144 pt filled,
   words at 24 and 12 pt. For the Bold or Bold Italic the first column is
   the style it is made from. Look at the sheet yourself before handing
   it over: render one row (`pdftoppm -r 110 -png`, crop) and compare the
   overlay where the report names its worst place.
5. Review by the designer. Nothing is installed without it.
6. Install the accepted ones (the plugin asks before writing into a
   generated style: that is this step):

       .venv/bin/python -I scripts/redraw.py sources/MyiaDidot-Italic.ufo \
           build/redraw/BATCH.ufo a b c ... --install --date DATE --review proofs/NAME-DATE.pdf

   It replaces the contours, marks the Italic's glyph "drawn"
   (org.myiadidot.italicSource, so make_italic keeps it) and records the
   redraw in lib org.myiadidot.redrawn (date, review, the fingerprint of
   what it replaced, the old source mark, the tolerance). A glyph failing
   the gate is not installed. In the Bold and Bold Italic mark it with
   `scripts/drawn.py` as well (until T6 makes one mark of the three).
   The record's `source` is the mark the glyph had: make_italic reads it
   (`origin`), since a redrawn Old Standard letter still carries the
   weight added to those. `--install` saves the UFO as ufoLib2 writes it
   (as drawn.py and accepted.py do): `make normalize` follows in step 7.
7. Then as TODO.md's phase 5 says, by the agents: `make normalize`, `make
   generate` (the derived letters, small caps and the Bold Italic follow),
   `scripts/sync_check.py`, `make reproduce`, and the sweep, before any
   test is read:

       .venv/bin/python -I scripts/redraw_sweep.py sources/MyiaDidot-Italic.ufo \
           --rev REV --json build/redraw/sweep-Italic.json > build/redraw/sweep-Italic.txt

   (REV: the commit before the install; with staged work beside it,
   `$(git write-tree)`; the same for the Bold Italic; 80 s a style.) It
   lists every glyph that differs with the distance its outline moved,
   in units, and its advance, by kind: redrawn, composite, other. Read
   it against "What may move" below; everything flagged (!) gets an
   answer, a cause or a place on the sheet for the designer. Only then
   `make test`: `make regress` and `make diffenator` for what the sweep
   does not see (shaping, rendering); lines that fall away deleted from
   `tests/data/quality-*.txt`; `accepted.py` for the letters; shaping
   baselines with the report's digest; FONTLOG.
8. A second sheet for the designer, of what followed: the Bold Italic's
   redrawn letters before | after (the first column the Italic), and
   every glyph of either style the sweep flags for its outline. The
   accepted glyphs that changed are accepted anew from it, not before.

## What may move after an install

Measured on the pilot (n a e o s g; `build/redraw/sweep-*.txt`).

| | Italic | Bold Italic |
|---|---|---|
| the redrawn letters | up to the fit's distance (3.1) | much more where two sides meet at a narrow angle: n's crotch 49 units shallower, g 22, a 10; advances by 1-7 |
| their composites | as their letter; advance unchanged | as their letter |
| letters derived from one (ɲ ɳ ɠ ʂ ɸ) | as the base, 1-3 units; advance unchanged | as the base |
| letters that read one as a measure | 1-2 units, advance 1-5 (0.3 %) | 2-8 units |
| small caps FontForge drafts from a capital that moved | anything: ʝ.sc's eye 31 units | follows |

- **The measure letters** are read by recipes that never use their
  outline: o for the stems and hairlines every recipe stroke is scaled
  to (`derive.strokes`, `recipe_scale`) and for every enlarged letter (Ɩ
  Ɣ Ꞷ ɢ ʙ ...), n and H for the small caps' stem, O and o.sc beside
  them. A redraw moves such a measure by a few tenths of a unit (o's
  stem 172.4 -> 173.0), and about 40 letters follow by a unit. Redraw the
  measure letters in as few batches as possible (o and n are done; O H
  with the capitals), and expect the "other" kind then.
- **A capital that moved by a unit is drafted anew by FontForge** (its
  fingerprint in sources/drafts/*/lib.plist), and a new draft can differ
  by tens of units in a detail. Each such small cap goes on the second
  sheet.
- **The Bold Italic's crotches.** Where the Italic's two sides meet at
  7-9 degrees, the place the emboldened sides cross moves by 15-20 units
  for each degree. Closing a crotch's short line (n: 6 units) turned the
  sides by 1.9 degrees; the Italic's crotch moved 3 units, the Bold
  Italic's 49. Not a fault of the stroke, and not to be tuned away: the
  designer sees both on the second sheet and says which crotch stays.
  If the old one: `"keep": [[416, 452]]` in the spec leaves the short
  line open, the sides' directions as they were (tried on n: 67.5 and
  60.6 degrees as before, 27 nodes).
- Anchors altogether: a derived letter or an alias takes a kept base's
  anchors as that base was saved, with what later stages set on it
  (Cyrillic у: DotBelow 396 -> 897, y's own; ʈ ƭ: t's Dotaccent; ʉ ʋ).
  Flagged as "anchors N"; check the base's own anchor is the one meant.
- Horn anchors: a derived letter copies its base's anchors when it is
  built; from a kept o it gets o's own Horn (744,759), found on the
  Italic's outline, not the Regular's sloped one (763,774) that stood
  there before `horn_stage`. About 20 letters, none with a horn in use;
  the sweep flags them as "anchors 34".

Not expected, and each one a fault to find before going on: an advance
changing by more than 5 units; a composite's advance changing at all;
anything of the "other" kind moving more than its base did, in a letter
that is not on the list above.

## The gate, as numbers

`redraw.gate` (constants at the top of redraw.py). A failure stops the
install; a remark is looked at on the sheet.

| | limit | kind |
|---|---|---|
| distance from the target, both ways, after rounding | 4 units (`DEV`) | failure |
| `checks.construction` on the result (smooth, kink, extreme, step, grid) | none | failure |
| a curve bending the other way at one end (`bent_back`) | none | failure |
| bounds | moved by 1 unit at most (zones, overshoots kept) | failure |
| ink area | within 1 % | failure |
| extra nodes that are not at an inflection or from the spec | none | remark |
| curvature jump at a smooth node | 0.5 (`JUMP`), or the target's worst if that was more | remark |
| nodes | not more than before (more: an extreme that had no node, K's 859,62 from the quality list, or a shape one curve does not hold) | remark |
| tolerance | widened for this glyph | remark |
| nodes against the Regular's counterpart | 4 more at most | remark |

TODO.md's gate for a core letter adds what the tool cannot say: no entry
in the style's quality list (after step 7), and accepted at 144 pt beside
the Regular and in words at text size.

The jump: |k0 - k1| / max(|k0|, |k1|, 1/1500), the curvatures either side
of the node: 0 one curvature, 1 one side straight, 2 an inflection in the
node. A jump of 1 where a round runs into a nearly straight stretch (a's
bowl into the stem at 581,174) is the letter's design and stays a remark.

## The pilot's results (2026-11-10)

| | nodes | Regular | from the target | jump before -> after | what changed |
|---|---|---|---|---|---|
| n | 27 -> 26 | 25 | 2.8 | 0.82 -> 0.54 | crotch line closed; 1 kink smooth; the arch keeps its old node at 550,607 |
| a | 23 -> 20 | 25 | 3.1 | 0.71 -> 0.60 | crotch line closed; 1 kink smooth; bowl keeps 199,649 and 562,291 |
| e | 16 -> 15 | 13 | 2.2 | 0.64 -> 0.18 | three old nodes kept as extras |
| o | 10 -> 9 | 8 | 2.5 | 0.71 -> 0.16 | the inner flank keeps 587,252 |
| s | 23 -> 21 | 23 | 2.5 | 1.84 -> 0.43 | 5 kinks smooth (both list entries gone); necks without their inflection nodes |
| g | 27 -> 22 | 33 | 2.7 | 1.60 -> 0.38 | crotch line closed; outer bowl onto its extremes |

Read with them:

- The letters were close to the Regular's economy already; the gain in
  these six is in kinks, short lines and curvature, not in the count. The
  count falls where Old Standard has nodes in the diagonals (b d p q h m
  u and the capitals carry most of the Italic's 1410).
- "Extremes only" (tolerance 6, the sheet's fourth column) reaches the
  Regular's counts (o 8, e 12, n 25) at 3-5 units from the target: a and
  e then fail the gate's 4 units. The old nodes kept as extras are the
  price of keeping Old Standard's shapes to 2 units. Whether those 3-5
  units are a loss is the designer's to say on the sheet; with a yes the
  default tolerance goes up, not the letters one by one.
- The fit moves every curve a little (1-3 units): on the overlay the red
  shows at s's necks and lower ball, at g's bowl. That is the fairing
  taking the curvature jumps out; at 144 pt it is under 0.2 pt.

### The whole alphabet, fitted but not reviewed (2026-11-10)

To find the cases before the batches do: a-z (dotlessi, uni0237 for i j)
and A-Z, `build/redraw/alphabet.txt` (not kept in git; 2 min 15 s). All
52 pass the gate.

| | nodes | Regular | kinks made smooth | extras | furthest from target | jump, median |
|---|---|---|---|---|---|---|
| a-z | 610 -> 564 | 541 | 28 | 38 | 3.1 | 0.82 -> 0.43 |
| A-Z | 662 -> 663 | 542 | 33 | 23 | 3.7 | 0.40 -> 0.15 |

- TODO.md's "Italic 1410 / 1172 against 924 / 816" counts handles with
  the nodes. On-curve nodes: Italic 576 + 662 against the Regular's 518 +
  542 (i j as they are, composites in both): 11 % and 22 % more, not half
  as many again. The capitals' surplus is serifs and brackets (corners
  and line ends, which a redraw keeps), not nodes in curves: a redraw
  does not bring A-Z nearer the Regular's count. What it removes there
  is 33 kinks and the curvature jumps.
- Fitted again the same evening with the guard against curves bending
  back (`build/redraw/alphabet2.txt`): the same counts; 23 letters had a
  handle shortened; 51 pass. q is refused: its stem's right edge is one
  curve of 617 units from 419,-364 to 582,229 whose end directions and
  chord allow no curve of one bend (the start leaves 0.4 degrees outside
  the chord: Old Standard's own S). The `extra` node proposed here for
  the batch did not do it; what did is under "Faults seen" (a stem's
  edge drawn as a curve).
- With a remark for the count or the tolerance: v K O Q T X (one or two
  nodes more: extremes that had none, O Q's flanks), A S V Y Z (tolerance
  widened). O and Q are the ones to look at first: Old Standard's italic
  O is not four curves a contour.

## Faults seen and their fixes

- **The handles cross at a short curve** (first version): without bounds
  the least squares gave a loop. Fixed in the tool: handles stay inside
  the triangle their directions make (`handle_bounds`).
- **One curvature forced at every node moved curves 3-6 units**: the
  first fairing was all or nothing and gave up. Fixed: a joint's weight
  is halved while a curve beside it is over its limit, so each joint gets
  as near one curvature as its tolerance allows.
- **A ball's neck redrawn as one curve between two uprights** (s, g's
  ear): within 2 units, yet a small shape read differently. Fixed by
  `span_tol` (short curves held closer). If a neck still looks changed on
  the sheet: `"extra": [[x, y]]` at its inflection.
- **A curvature jump measured between two flat edges** counted like one
  in a tight round: measured against 1/1500 where both are flatter.
- **A corner of 5-8 degrees that is meant** (a chamfer, a calligraphic
  break) is made smooth by the rules: `"corner": [[x, y]]`. The notes
  list every kink made smooth with its angle; anything over 5 degrees
  deserves a look at the overlay.
- **A short line that is meant** (over 8 units it stays; a's 5-unit
  chamfer between a curve and the stem's line stays too, since only a
  line between two curves is closed).
- **An extreme the letter is better without** (a hook's end 15 units
  from a corner, a node 13 units from another): `"drop": [[x, y]]`, and
  check the `extreme` finding does not come back (5 units of bulge).

- **A curve bent 1 degree the wrong way before its bend** (n's
  809,649, where the stem's line runs into the counter's top; e, g; 23 of
  the 52 alphabet candidates): fitted, the second handle ended at the
  point where the line and the upright meet; rounding the nodes moved
  that point 2 units and left the handle past it. Nothing to see in the
  Italic; Skia cut the curve there in every letter built on n (a stub of
  5 units in ɳ), and the Bold Italic's stroke stepped aside (n failed
  test_stroke_steps, a control letter). Fixed in the tool (`one_bend`)
  and in the gate (`bent_back`); tests/test_redraw.py holds every
  redrawn letter to it.
- **Advances 32 narrower in 30 derived letters** (ɲ ɳ ɠ ʂ ɸ ɵ ...): the
  first drawn base letters. make_italic kept a drawn letter as saved,
  cut, and cut what was built on it again. Fixed in make_italic: kept
  glyphs stand uncut through its stages and are put back as saved after
  `respace` (and before the swapped side bearings: ɘ takes e's).
- **Ꞷ 87 narrower, the enlarged small caps 12**: `weight_of` knew only
  the marks "Old Standard", "derived", "small cap draft" as carrying the
  added weight; o, marked drawn, was measured with it. Fixed:
  `make_italic.origin` reads the mark the redraw recorded. And taking
  the weight off again moves nodes, a round between them follows: on
  o's four extremes it took 8.2 units off where Old Standard's nodes
  lost 9.6. A redrawn letter read for a measure has its curves halved
  first (`reweight(fine=True)`): 163.3 against 162.6.
- **A recipe that leaned on a kink of its base**: ɳ's descender was
  faired into the stem up to its top because n had a kink of 1.3
  degrees at 682,361, which made that node part of the run
  (`derive.fair_joins`: nodes turning 1-25 degrees). Redrawn smooth, the
  node ended the curve: 10 degrees of turn in 40 units, a corner. Fixed
  in the recipe: `ITALIC_JOINS_THROUGH` (min_turn 0). ɱ will need it
  when m is redrawn: check it in the sweep (ɱ unmoved today), and any
  other `ITALIC_JOINS` letter whose base is in the batch.
- **A mark's corner out of the letter by 0.3 units** (ȩ: the cedilla's
  top corner at 317,30, glyph_lint "step"): e's inner edge moved under
  it. Fixed on the letter: a Cedilla anchor on the drawn e, 2 units
  lower (344,-2). Look for the same wherever a composite's mark is sunk
  into its letter (ç ş ţ, ogoneks, horns): `glyph_lint.py UFO` on the
  composites of the batch.
- **A stem's edge drawn as a curve** (q, 2026-11-11: the left edge
  below the bowl, 419,-364 to 582,227, one cubic with its first handle
  on the node, 0.9 units off its chord; refused, no curve of one bend).
  An `extra` node where the run seems to end leaves a curve of 580 units
  that is straight but for a degree, and that one bends the other way
  first (gate: `bent_back`). It is a line: `"line": [[419, -364]]` in
  the spec takes the curve leaving that node as the line between its
  ends, and refuses if the curve is more than the tolerance (2 units)
  off it. The bracket then runs into the line's direction; the crotch's
  4-unit line stays (between a line and a curve, as a's chamfer). Look
  for the same in the descenders of Greek and Cyrillic (ρ φ р ф) before
  trying anything else on a "refused: no curve of one bend".
- **A spec's point refused as "the outline is 57 units away"** though
  it lies on the outline: the spec was given to every contour of the
  glyph, and the counter refused what named the outer contour. Fixed in
  the tool (`spec_by_contour`: each point goes to the contour nearest
  to it). The pilot never met it: none of its six needed a spec.
- **A small quarter-turn come out square** (2026-11-11, found only
  after the install: f's inner hook, the exit tips of h m u w, ȷ's
  hook, z, k): one handle at the corner its two directions make, the
  other 3-8 units long. Inside the tolerance, passing the gate; the
  only sign was the remark "curvature jump 1.0 (the target's worst
  0.74)". The fairing had given the curve's shape up to meet a flat
  neighbour's curvature of nought. Fixed in the tool (`FAIR_SPAN`). A
  jump that comes out *higher* than the target's is never a remark to
  pass on: look at that curve's handles before the sheet is made. What
  found it was a recipe (ɾ, made of f's hook) moving 25 units in the
  sweep.
- **Hint zones**: the Bold Italic's G and Ɠ sit 4/64 px off their bottom
  zone at 35 ppem though neither outline moved (test_hint_zones). The
  cause is not traced yet (`scripts/quality/hint_zones.py FONT`): do
  that before `--hinting`.

## A letter given another shape: f's hook (2026-11-11)

Asked for on the first batch's sheet: the Italic's f with a hook below
"like other italic fs" (Old Standard's ends in a flat cut), in the
f-ligatures too, ſ as it is. Not a redraw, but done with its tools, and
the order is the one to keep for the next such wish:

1. The new shape is made of what the style has, by a script that says
   how (`scripts/f_hook.py`: each flat foot replaced by ȷ's descender,
   its ends set on the f's stem edges), into a scratch UFO; the result
   fitted by redraw.py like any letter (the "target" is the
   construction). Sheet, review, then `--install` (marked drawn; lib
   org.myiadidot.redrawn has "hook").
2. The model letter first: ȷ was in the same batch, so the hook is the
   redrawn ȷ's. The script is run after the batch's install, not before.
3. Then everything that is made of the letter, each looked at in the
   sweep: the made ligatures (f_b ... from fl ffl) and ᵮ took the hook
   by themselves; the long-s ligatures are made of the f-ligatures with
   ſ's stem set in, and had to clear the hook (italic_ligatures.py:
   by its measured reach, all clearings before the stems are set, the
   j's part taken from its own ink contour). ʃ ɾ and the hooks over the
   top take only f's top.
4. The Bold Italic has less room than the Italic. In ff ffi ffl ffj the
   second hook's ball stood 36 units from the first f's tail; emboldened
   they closed on each other, a white island between the stems (and the
   long-s ligature read that island as part of the j). Decided by the
   designer: the second f 50 units further right in the Bold Italic
   (`make_bold.part_ff`, before the emboldening). Whenever a shape
   reaches under or over its neighbour, measure the white in the Bold
   Italic (`derive.stems_at` at a few heights) before its sheet.
5. Open after it: f's kerning was set for a stem without a hook (g j y
   p q before f; phase 1's sweep); the Bold Italic's ſſ ligatures are
   50 wider with their ff.

## After the batch of 2026-11-11: what the tests found (open)

Twenty letters at once met what the pilot's six did not. `make test`
after the fourth run: 27 failing (`build/redraw/g4-failures.txt`). Sort
them so before touching a baseline:

Accept with their reports, once the faults below are mended (the
changes are the approved ones): test_accepted (both italics),
test_quality (both), test_regression golden and digest (both),
test_glyph_lint Italic (four `notch` lines to delete: m ɯ ḿ ṃ),
test_stroke_gate's fixtures for u y ƴ ʎ (advances and anchors by a
unit), test_hinting's zones.

Faults, each to find and mend in its place:

- **A drawn Bold Italic letter whose Italic letter moved** (k, drawn
  before; x, drawn 2026-11-11): make_bold puts it back on the new
  letter's side bearings before the derived letters are built
  (`drawn.restore(spaced=True)`), so its aliases, composites and
  ligatures take that width (k 1021, x 1165), and `write` then puts it
  back as saved (1022, 1167). Failing: test_built_from aliases,
  test_composites (ẋ), test_nfc_and_nfd (ǩ ḱ ḳ ḵ, ẋ),
  test_italic_ligatures (f_k, ſk by a unit). To try: `write` restoring
  spaced as well (the saved outline on the bearings the font has for
  it at the end); in the steady state that changes nothing, check with
  `make reproduce` and an empty diff of the Bold.
- **A kept Italic letter's composite a unit off** (ỵ: dotaccent at 53,
  the rules give 54): the kept letters stand uncut while the composites
  are placed and are put back as saved after `respace`; half a cut
  rounds one way going and the other coming back. The pilot's six did
  not show it.
- **Repair scripts that know their letter by fixed points** (TODO T7):
  y_dot (the Bold Italic's ỵ: its dot 21 units into the tail,
  test_y_dot; with it test_composites and test_nfc_and_nfd for ỵ),
  l_belt (ɬ in the Italic: the test's own rebuild differs from the
  generated one), r_hook (the Bold Italic: a unit of width). Each
  against the redrawn letter's nodes.
- **The stroking's guards on letters that moved**:
  test_stroke_steps[u] (two bends new at 331,173 and 329,162, the
  Bold Italic's u, approved on the sheet as it is: see whether the
  bends are the approved shape or a fault under it),
  test_controls_not_blended[v] and [w] (the control letters' expected
  behaviour changed with their outlines: docs/claude/stroking.md).

The lesson for the next batch: run `make test` on the first generated
state, before the second sheet is made, and sort the failures like
this; the sheet then shows what the mended generators give.

## Hand back to the designer rather than fit

- A glyph with components is refused: redraw its parts (i j: `dotlessi`
  and `uni0237`; the dot is its own glyph), never decompose it.
- The glyph is refused otherwise (an open contour, quadratic curves) or
  fails the gate after one honest correction of its spec. Do not raise
  `tol` for a single glyph to pass it.
- More than three extras on one contour: the shape does not want the
  structure, it wants drawing.
- The fault is the shape's, not the nodes': an entry of kind slant, zone,
  stroke, weight or accent in the quality list (n's 19.7 degrees, s 0.79
  of its kind's stroke). The redraw keeps those faithfully.
- Letters built in parts whose parts overlap or touch (Old Standard's 1
  and 4, a bar through a stem): the parts are designed apart; redraw
  after the designer says whether they are merged.
- Letters make_italic changes after taking them from Old Standard
  (`redraw_w`, `lighten_a`, `lean_as`, `finish_bases`, `r_hook`): once
  marked drawn they no longer pass through those steps. For a (lightened)
  and s (leaned) the target already holds the result; say so in the
  review document, and after `make generate` compare the glyph with the
  candidate: it must be identical.
- A drawn Bold Italic glyph whose Italic letter is redrawn (TODO phase 8:
  `scripts/drawn.py UFO` lists them as stale): the drawn fix is judged
  again by the designer, not refitted.
- Anything where the overlay shows a difference you would have to argue
  for. The tool finds candidates; the designer's eye decides.

## When the method does not cover a case

Move the session up a model, solve it, and add the case to "Faults seen"
here with its fix, so the next one does not need to (TODO.md, "Which
model after that").
