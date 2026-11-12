# The stroking: a map of `stroke_bold.py` and `fair_arcs.py`

For whoever changes the Bold Italic's emboldening after 2026-11-11 (F3).
What the machinery does letter by letter is told in `styles.md` (Bold
Italic) and in the modules' own comments; the studies and reviews in
FONT-DESIGN.md ("Bold Italic from strokes"). This file is the map: the
stages in order, what each constant governs and what moved when it was
changed, what a change must keep, how to test one, what not to try
again, and T4's decision for every switch.

Read first: CLAUDE.md's rule of 2026-11-03. The shared machinery is
changed only for a fault a whole family of letters shares. Every stage
below moves hundreds of letters when touched (the crotches' change of
2026-11-03: about 330; the entry strokes': 108); one letter's fault goes
into its recipe, a per-letter table in make_bold (below), or is drawn
and marked (`scripts/drawn.py`).

## Who calls what

`make_bold.py` (Bold Italic only) deslants each letter, widens it (KX),
and hands it as a job to `stroke_bold.emboldened` in a pool of JOBS
processes; marks and ITALIC_BOLD_BY_POINTS (dollar ℵ ™) stay by weight.
The job's arguments are all the stroker is told about a letter:

| argument | from make_bold | governs |
|---|---|---|
| ax | ITALIC_AX 102 × gain | a stem's gain across |
| ay | AY | gain up and down |
| thin, thick | ITALIC_THIN 60, ITALIC_THICK 160 | section widths read as weight 0 and 1 |
| hair | ITALIC_HAIR 12 | a hairline's gain across (0, 12, 24 tried: 12 chosen 2026-10-28) |
| slant | SLANT | the frame: which direction counts as upright |
| sliver | SLIVER × scale² | cleaned contours under this area dropped |
| root | ITALIC_BOLD_ROOTS (k, & 0.7) | a hairline heavier where it leaves a crotch |
| split | ITALIC_BOLD_SPLIT (ξ) | more than one cubic into a crotch |
| free | ITALIC_BOLD_CAP_FREE (q.sc 300) | CLEAR lifted near a crotch |

gain is ITALIC_BOLD_HEAVIER (z 1.15) times the scale of a glyph made
small. A job that raises (ValueError, IndexError, ZeroDivisionError,
LinAlgError) returns None and make_bold **falls back to by weight
without stopping**: after a change to the machinery, check which letters
no longer come from the stroker. Results are kept by `stroke_cache.py`,
keyed by outline, arguments, the source of stroke_bold and all it
imports, package versions and every `MYIA_*` variable but the steering
ones; so any edit to either module strokes everything afresh (about 9
minutes of `make generate`).

After the stroker, still in make_bold: `smooth_counter` (q.sc), the
spacing (as by weight: the by-weight letter is still made for every
letter and its optical fit taken, then STROKE_OUT gives a letter's side
back the white its stroked ink took, then BOLD_ITALIC_CUT), the rebuilt
derived letters (ITALIC_BOLD_REBUILD), `italic_counter` /
`italic_inside` for the rounds, and the finishing passes (stem_joins,
smooth_joins, bowl_counters: `quality.md`). A fault seen in the font may
come from any of these; find the stage before changing one (below).

## The stages in order

`embolden_by_strokes` strokes a letter up to three times and chooses:

1. **Tidy**: overlaps merged, the merge's near-zero lines dropped (TINY).
2. **First stroking**, one_way off: its only use when one_way is on is
   to find the knees on the outline as plainly moved.
3. **Second stroking** (whenever ONE_WAY is on, or a knee was found):
   the knees' curves blended into their lines whatever their length,
   one_way on for all arcs but the knees. This is the candidate.
4. **The gate**, only if something was blended: a third stroking with
   the blend off ("plain"); the candidate is taken only if against plain
   it removes a step, adds no step, bend or quality finding (matched one
   by one, `compared`), and `guarded` holds. Else plain is the result.
5. **Knees drawn** (`knee_turned`), only on a candidate the gate took.

One stroking (`stroked` → `Strokes.draw`) runs, per contour:

| # | stage | function | constants |
|---|---|---|---|
| a | sample the outline, classify nodes (corner, extreme) | `sample` | STEP, CORNER |
| b | weights: a ray into the ink per sample, the section shared by both sides, smoothed along the outline between crotches; the cap by the white in front; a crotch's root | `weights`, `smooth` | BLOCK, PARALLEL, SIGMA, ACROSS, SHALLOW, CLEAR, ROOT, FULL |
| c | too-tight concave rounds become crotches; serif brackets marked to move whole | `crotches`, `rigid` | TIGHT |
| d | the lines' own mean weights taken, *before* e changes the curves' | (in `draw`) | |
| e | a short curve before a line takes on the line's weight | `blend` | BLEND, BLEND_SHORT, BLEND_STEP, KNEE_BLEND |
| f | every sample moved: across by its weight, up and down by ay (FULL, ZONE_NEAR) | `move` | FULL, ZONE_NEAR |
| g | arcs leaving a stem into a hook kept turning one way | `Strokes.one_way` | ONE_WAY_* |
| h | extreme nodes slid to where the moved outline is level or upright again | (in `draw`) | |
| i | node positions: a line parallel by its mean weight; convex corners mitred; a crotch of two lines where they meet; a crotch with a curve where the moved sides cross, each side by its own weight; a short-line crotch to one point; brackets shifted whole | `mitre`, `meet`, `crossing` | (each side by its own weight to a corner, and the crossings: fixed since T4) |
| j | one cubic per source curve through the moved samples, tangents from the moved outline, extremes exact | `fit_cubic` | TS |
| k | smooth joins of two curves given one curvature | `join_curvature`, `fit_g2` | G2_ERR, TS_G2 |
| l | knees noted (a curve beside a line whose fit bends back); one-way curves refitted to bend one way | `one_way_fit` | ONE_WAY_LIMIT, _SCALES, _SHARP, _HANDLE |
| m | listed letters: a curve into a crotch fitted with more cubics | `split_fit` | SPLIT_ERR |
| n | cleaning: pathops removes the crossing sides; slivers dropped | `merged_glyph` | SLIVER |
| o | the cleaning's splits undone, its leftovers merged; near a blend a short curve joined into its curve | `rejoined` | LEFTOVER, BLEND_SHORT, REGION, G2_ERR |
| p | each whole arc (corner to corner) refitted fair, taken only within LIMIT; a faired contour crossing itself more than the fitted is refused | `fair_arcs.fair_contour` | fair_arcs' |

Why this order, where it is not obvious:

- d before e: a line's weight is its own mean; blend changes the
  samples of the curve next to it, not the line.
- h after f and g: the offset is wider across than up and down, so an
  extreme moves along the outline; left fixed, the inner crowns bent
  back (2026-10-28).
- k in the fitter, before the cleaning: the cleaning cuts curves, and
  `rejoined` keeps a merged run's end curvatures when it puts them
  together again.
- o before p: fair_arcs refuses an arc holding a cubic under SHORT (8)
  units or doubling back, so leftovers are merged first.
- p last, and only p adds nodes freely (a transition curve where a
  curve leaves a line): a stem join cannot be made straight by one cubic
  (dead ends, G2 into lines).
- knees are found on the outline as moved without one_way (2) and
  left out of g: both act on a curve beside a line, and a knee has its
  own repair (blend, gate, knee_turned).
- knee_turned after the gate: the gate judges the blend; the turn is
  drawn only on a candidate it took (blended only, the knee still went
  inward before turning).

`fair_arcs.fair_contour`, per arc: brackets (up to three curves under
BRACKET between lines) and the curves at a slit (SLIT) held as drawn; a
curve next to a line split in two, its curvature only fading towards
the line; nodes and handles solved together (Levenberg-Marquardt, OUTER
rounds of INNER steps) against the old outline's samples; the arc taken
if it strays at most LIMIT and holds no degenerate piece.

## The constants

"Record" is what was tried and what moved; where it says none, the value
was set with the first commit of its stage and never reviewed apart.
Only two values were ever changed after their commit: STEP_TURN and
fair_arcs' INNER.

### Weight (stages a, b, f)

| constant | value | governs | record |
|---|---|---|---|
| STEP | 2 | units between samples | the pilot's; none since |
| BLOCK | 32 | samples measured together (speed only) | none |
| PARALLEL | cos 40° | how parallel a facing side must be to count as the stroke's other side | none |
| CORNER | 28° | a node turning more, not smooth, is a corner | none |
| SIGMA | 90 | smoothing of the weight along the outline | 45 left г's spine a knee where the weight rose within one curve (2026-10-28) |
| ACROSS | 0.45 | a shallow diagonal read by its width nearer the horizontal, at least this | 1 read z's spine as a hairline; 0.6 with FULL 0.5: z s still light |
| SHALLOW | 0.55 | which strokes gain up and down too: under about 33° from level, fading to 44° | a steeper one (κ's arm, 45°) pulled a waist where its hairline leg leaves |
| FULL | 0.75 | share of its offset a heavy shallow stroke gains up and down | 0: z s г spines lighter than stems; 0.5 still light; 1 rounds dark |
| ZONE_NEAR | 100 | that gain fades within this of the zones | without, v w y z α rose past their overshoots |
| CLEAR | 0.25 | a side moves at most this share of the white in front | z's loop stays open, no exception needed. Lifted for every letter near crotches: broke the oldstyle 2, filled q's crotch; a larger CLEAR alone left q.sc an S. Hence `free`, q.sc only |
| ROOT | 160 | distance over which `root` fades | per letter: k 0.7 chosen of 0.3, 0.5, 0.7; n m h declined (thin arches kept); & 0.7 (foot 29 → 19 aside; 1.0 bracketed the diagonal's crotch) |
| TIGHT | 2 | a bracket under TIGHT × its offset in radius moves whole | point by point the capitals' brackets (radius 40-65) folded into a corner and a jog; the value itself: none |
| OPEN | 1e9 | (technical: an unclosed run's length in `smooth`) | |

Results of the weight model at its adoption (2026-10-28): z s г 2
+11-15 % ink against by weight, o +7 %, stems −5 %; quality kinks 495 →
about 110, wobbles 352 → about 190.

### Fit and joins (stages j, k, m, o)

| constant | value | governs | record |
|---|---|---|---|
| G2_ERR | 3 | units a curve may move from its own fit to share a curvature; else the join stays tangent-only | bounded by the samples instead, a curve moved 40-65 units (Ә's counter, q.sc's tail). Joins needing more (p g a) stay as fitted. Jumps over 1/250: 1999 → 1236 |
| SPLIT_ERR | 3 | units one cubic may stray before `split_fit` cuts it (letters with `split`) | split for every letter: ɱ's hook, щ's stems bent; all round a letter: ξ's, q.sc's bowls faceted |
| TINY | 4 | a line this short from the overlap removal is dropped | 2's and 7's kinks were 3-unit lines; a contour starting on one hung `tidy` (2026-11-04, tested) |
| LEFTOVER | 8 | a cleaned piece shorter is merged (must equal fair_arcs.SHORT; a separate literal) | flagged pieces 386 → 234 |
| SLIVER | 800 | area of a crotch's crossing sides, dropped | none |
| TS, TS_G2 | 200, 80 | sampling of a cubic in the fits | none |

### Blend, knees and the gate (stages e, 4, 5)

| constant | value | governs | record |
|---|---|---|---|
| BLEND | 120 | length over which a curve takes on its line's weight | y's descender met its inner line in a sideways step (line 23, curve 45) |
| BLEND_SHORT | 40 | only a curve this short before the line (a longer one's fit takes the difference up) | |
| BLEND_STEP | 4 | only where line and curve would stand further apart | |
| KNEE_TURN, KNEE_NEAR | 8°, 20 | a knee: a step this large within this of a curve whose fit bends back | u: 10 here, 18 finished; none in n h m v w a b d p q r |
| KNEE_BLEND | 240 | a knee's blend length | 120 kinked u at its line once rounded; 500 a little below; 200-300 clean |
| KNEE_QUARTER, _RATIO, _CLEAR, _HANDLES | 46/160, 1.48, 0.364, (…) | the turn drawn as the Italic's u | quarter 30 and 38 tried, 46 chosen; the others measured on the Italic's u |
| STEP_TURN | 20° | what counts as a sideways step | 12 missed four of the eight old steps; 20 finds all (25-72°) and none in n h v w o |
| STEP_REACH, STEP_WIDTH, STEP_SIDE, NOTCH | 40, 30, 1, 12 | the step's shape; a drawn notch is not one | calibrated with STEP_TURN |
| NEAR, WORSE, BEND_NEAR | 20, 0.1, 40 | when two findings are the same one, when worse | totals instead of one by one let a wobble gone pay for a kink added |
| REGION, OUTSIDE, WIDTH | 1 × ax, 1, 3 | where a blended candidate may differ from plain, and by how much | `rejoined(short=)` beyond REGION: ц's tail overshot its extreme 16 instead of 11 |

Refused by the gate today and so as plain: f_h f_f_h u.sc ² ʸ Ɠ љ Қ Ѫ
(`MYIA_BLEND_LOG=file` lists every verdict and why).

### One way (stage g)

| constant | value | governs | record |
|---|---|---|---|
| ONE_WAY_TOL, _DIP, _MAX | 3°, 1°, 10° | the source turns one way, the moved points turn back by 1-10° (more is a crotch's, 20-25°) | cause: the weight fading from stem to hairline tilted the edge back faster than the curve turns (3.7 units at u's entry) |
| ONE_WAY_STEM, _HOOK, _FADE | 0.7, 0.3, 0.2 | only a stem fading into a hook | none |
| ONE_WAY_UPRIGHT | 30° | only from a near-upright line | s S ʂ's spines (55°) accepted as they are |
| ONE_WAY_SHARE | 0.5 | share of the source's turn kept | 0.8 and 1 pinched the hook's counter |
| ONE_WAY_GIVE | 20° | the rest of the arc must turn this much to take the shift back | given back by turning: a foot's tight turn folded into a cusp |
| ONE_WAY_LIMIT, _SCALES, _SHARP, _HANDLE | 4, 0.1-1.6, 2, 12 | the one-way refit | handles under 12 rounded the course off by 3.6 units |

108 glyphs moved (2026-11-09), accepted but for ſh ɯ ᵯ ɰ, since done
by hand on m.

### fair_arcs

| constant | value | governs | record |
|---|---|---|---|
| FAIR | 3000 | weight of the curvature's relative change (log \|k\| per unit) | the squared change of curvature instead rounded n's and h's tight counter tops by up to 9 units, a Didot mark lost |
| JOIN | 3e4 | weight of a curvature jump at a join | none |
| BEND | 1e5 | weight of bending back, of a transition swelling | without it the transitions were S-bends |
| LIMIT | 6 | units an arc may stray, else left as fitted (also the gate's zone) | 3 refused n m h u v w |
| BRACKET | 120 | curves between lines under this in all are a bracket, held | longer capital serif curves are refused anyway: straight ends would move them 12-18 units |
| SLIT | 120° | a crotch turning more is a slit, its curves held | ɕ's slit, joined smooth, was closed by the fairing |
| SHORT | 8 | a cubic with a shorter chord is not refitted; none under 16 split | |
| HOLD, TOL | 0.1, 1e-8 | pull to the drawing; when the solve ends | added for reproducibility (below) |
| OUTER, INNER | 3, 20 | rounds and steps | INNER 15 → 20; 6 and 30 within a unit |
| K0, SMOOTH, NK, STEP, DENSE | | sampling and thresholds | none |

At its adoption: curve joins jumping over 1/250 1236 → 860, curves
leaving lines 826 → 585, n m h 8-11 nodes more, the style 3 min 10 s →
5 min 40 s uncached.

## What a change must keep

1. **The source's structure.** One cubic per source curve, one line per
   line, nodes where the Italic has them, extremes level or upright in
   the slanted frame. Only three places add nodes: `split_fit` (listed
   letters), fair_arcs' transition at a line, `knee_turned`. A change
   that adds nodes elsewhere is a different method, not a tuning.
2. **A stroke has one weight across.** Both sides of a section share
   it; smoothing stops at crotches (round a crotch it thickened the
   arch springing from it: m's joins filled black).
3. **Lines stay lines and move parallel**; a stem keeps one thickness
   and does not step in at its serif (`scripts/quality/stem_retreats.py`);
   brackets move whole and keep their radius.
4. **Counters stay open**: no side past CLEAR of the white in front.
5. **A repair stage is gated per letter.** Blend, knee: taken only
   where the letter gets better by measure and nothing else moves, else
   the letter is exactly as without. A new repair stage comes in the
   same way, and its commit says which letters it lands in; all others
   bit-identical (as 10ddbcdc: "y ʎ ʲ Џ м 7 ƴ; all other glyphs, the
   controls included, bit-identical").
6. **The same on every machine.** The solves use no sine, cosine,
   exponential or logarithm, central differences, rounded-off kinks in
   one-sided terms, ties broken alike; numpy and OpenBLAS pinned to AVX2
   by make_bold. A 1e-9 nudge moves an outline 1e-4 units at most. New
   numerics follow this or CI's `make reproduce` fails on other hardware
   (68, then 49 glyphs before it was done).
7. **Everything that steers the result is an argument or source.** No
   environment, no file read at run time: the cache's key and
   reproduction both rest on it (T4, done 2026-11-12: `check_reproducible.py`
   refuses a `MYIA_*` variable outside `stroke_cache.KNOWN`).
8. **No silent fallbacks added.** A new exception type in a job is
   caught as failure and the letter goes by weight; compare the list of
   stroked letters before and after.
9. **Drawn letters do not follow.** `scripts/drawn.py UFO` lists them;
   after a change that should have reached one, it is redrawn or its
   mark dropped, by decision.

## How to test a change

Before: say which letters should move and how many, and the controls
that must not (n h u v w o for anything about joins; add s z k g for
weights, γ ξ & q.sc for crotches).

1. Unit tests while working: `tests/test_stroke_steps.py`,
   `test_stroke_gate.py`, `test_stroke_cache.py`,
   `test_stem_joins.py` (pytest selection, font-runner).
2. `make generate`, then `make reproduce` (font-runner). With
   `MYIA_BLEND_LOG=file` once, and the verdicts diffed against the same
   from before: a letter whose verdict changed is a finding (the log
   turns the cache off, so that run takes the full time).
3. Counts, Bold Italic, before | after (font-measure):
   `scripts/quality/checks.py` by kind (kink, wobble, extreme, smooth,
   step), `corners.py`, `glyph_lint.py`, `stem_retreats.py`,
   `strokes.py` for the stems' and hairlines' weights,
   `scripts/pilot/g2_measure.py` for curvature jumps. Findings gone and
   new are both listed by glyph; "fewer in total" is not a result.
4. `make diffenator` / `make regress` for every glyph that moved, not
   only those meant to: the count against what was said before.
5. Sheets (PDF) for the designer: Italic | today | new with node views
   for the letters meant and a sample of those not meant; curvature
   combs (`scripts/pilot/comb_sheet.py`, `node_sheet.py`) for anything
   about joins; words at text size, since a change of weight reads there
   and not at 144 pt (spacing fitted to the stroked white read
   "noticeably blacker" in text and was undone).
6. Only after approval: baselines by `scripts/update_test_data.py` with
   the report's digest; `tests/test_accepted.py`'s letters accepted
   anew (it has moved at nearly every stroking commit: Ɽ Ⱳ ɬ ɸ ʈ.sc).

To find which stage makes a fault, stroke the one letter with stages
off (by argument, `embolden_by_strokes(fair=False)` or `one_way=False`,
called from a pilot past the cache) in this order:
fairing off (is it in the fitted outline?), one_way off, then the
gate's verdict from the log (blended or plain?). If it is in none, it
comes after the stroker (first section's last paragraph).

## Dead ends: not to be tried again without a new idea

Weight:
- Raising a cut end's weight (to 0.5 or 0.8, over 60 or 160 units): a
  knob with a waist behind it. Leaving the cut end out of the measure
  (`pilot/thin-ends.patch`): "still edgy"; breaks ℵ in the Bold.
- Limiting the gain on tight inner turns: moved the bend, added corners
  (k r c W J).
- Letting the zone fade spare inner edges: +2 % for z, counters pulled
  off their zones.
- Spacing from the stroked letter's own white: 23 units closer, blacker.
- A root weight for the arches of n m h; a heavier root for k's upper
  arm (not seen in print).
- Capitals with thinner hairlines and heavier stems: uneven colour;
  declined twice.

Fit:
- A curve made straight where it leaves a line, in the fitter
  (G2_LINES): within 3 units only gentle joins go straight; at 8, a
  spike on n's and h's shoulders, a blob in the bowl, jumps elsewhere
  1236 → 1313. One cubic cannot do it; fair_arcs' transition does.
- Bounding G2 by the samples rather than the fit.
- Shortening handles against wobbles: changed Ⱳ's approved curl.
- Refitting runs with the fewest one-way cubics (`pilot/fair_runs.py`):
  n a c h barely change; as the stroker's fitter, 91 nodes in n.
- More cubics into crotches for every letter; lifting CLEAR near
  crotches for every letter (both: per-letter tables now).
- The Bold's oval refit on stroked o O 0: cusps (now `italic_counter`).

Cleaning and fairing:
- Ending a curve where its samples run back into a corner (k's arm a
  chord); giving a doubled-back end its samples' direction (notched ξ);
  making the merged join smooth (closed ɕ's slit).
- Fairing by the squared change of curvature, or weighted by curvature;
  without the one-way term; LIMIT 3.

Blend and knees:
- The blend alone for knees (still inward before turning, too tight);
  KNEE_BLEND 120 or 500; the gate by totals; STEP_TURN 12;
  `rejoined(short=)` anywhere in a blended letter.
- one_way's shift given back by turning (cusp) or eased along the arc
  (bent back again); SHARE 0.8 or 1.

Whole letters:
- Slashed letters as base plus bar by strokes (the "bar" took half the
  letter); ʉ, Ɯ stroked on their own; modifier letters stroked at their
  scale (a 32° corner in the curl; ᵘ ⁿ still are). All rebuilt from the
  Bold Italic's own letters now.

Not tried, open: paired fitting of a stroke's two sides (agreed
2026-10-28 as the step after G2, never run); keep_smooth / runs_on for
the Bold Italic (each letter needs review: FONT-DESIGN.md); the exits'
weight at text size (phase 8). Known leftovers: k's hook where arm
meets leg, z's bottom-left curl, leftovers in arcs of d k r z.

## T4: the switches, decided (2026-11-11), carried out (2026-11-12)

Done as below, the settled ones and the diagnostics in one commit (the
deletions each proved by `make reproduce` reporting nothing), the list of
known variables and the refusal with them; `tests/test_stroke_switches.py`.
The table is kept as the record of what each switch was.

Rule (TODO.md): nothing that changes an outline or a side bearing is
read from the environment. Three classes:

- **settled**: the switch and the branch not taken are deleted; the
  value becomes a plain constant.
- **diagnostic**: a stage that is still turned off to locate a fault
  becomes a keyword-only argument of `embolden_by_strokes`, default
  on, after `log`. A job's tuple is passed positionally, so make_bold
  and the cache cannot set it; a pilot script calls
  `embolden_by_strokes` itself, past the cache.
- **environment**: logs and steering only.

| variable | today | decision | to do in the code |
|---|---|---|---|
| `MYIA_G2` | on | settled: on since 2026-10-28, reviewed, nothing compared against it since | delete; the two `if G2:` (`draw`, `rejoined`) unconditional |
| `MYIA_G2_ERR` | 3 | settled | `G2_ERR = 3.0` |
| `MYIA_G2_LINES` | off | settled as a dead end (above) | delete with its branches: `straight` and its two uses in `join_curvature`; in `rejoined` the ends at a line get `None`; the comment points here |
| `MYIA_G2_LINE_ERR` | = G2_ERR | goes with G2_LINES | delete the constant |
| `MYIA_FAIR` | on | diagnostic: "fitted or faired?" is the first question of every fault | argument `fair=True`, passed on to `stroked` |
| `MYIA_ONE_WAY` | on | diagnostic: the newest stage, phase 8 will measure against it | argument `one_way=True`, sets `Strokes.turning` and the condition for the second stroking |
| `MYIA_ONE_WAY_SHARE` | 0.5 | settled: 0.8 and 1 rejected | `ONE_WAY_SHARE = 0.5` |
| `MYIA_BLEND` | on | settled: the gate itself strokes without the blend and decides per letter; the log says which | delete; `self.blending = True` in `Strokes.__init__` (the gate's `plain.blending = False` stays) |
| `MYIA_KNEE_BLEND` | 240 | settled: 120 and 500 rejected, 200-300 alike | `KNEE_BLEND = 240.0` |
| `MYIA_SPLIT` | on | settled: the control is the per-letter `split` argument | delete; `split_fit`'s `or not SPLIT` goes |
| `MYIA_CORNER_OWN` | "2" | settled at 2 (each side its own weight to its end: what was accepted 2026-11-03 and everything since) | delete modes 0 and 1: `if nd["corner"] and kline[k - 1] is None: ka, va = kc[first[k] - 1], kv[first[k] - 1]`; the comment rewritten, it describes mode 1 |
| `MYIA_CORNER_MEET` | on | settled, same review | delete; its three conditions in `draw` unconditional |
| `MYIA_BLEND_LOG` | unset | environment (a log; turns the cache off) | stays |
| `MYIA_STROKE_OUT` (make_bold) | on | settled: side bearings, corrections since rest on it; not in T4's list but under its rule | delete; `STROKE_OUT` gone, its two conditions unconditional |
| `MYIA_STROKE_OUT_LOG` | unset | environment (a log) | stays |

Order of carrying out, each step a commit of its own:

1. The settled ones, one switch a commit. Proof for each: `make
   reproduce` reports nothing (editing stroke_bold invalidates the
   cache, so each run strokes afresh: plan about 10 minutes a step, or
   group the deletions and bisect only if a difference shows).
2. The two diagnostics as keyword-only arguments; make_bold's jobs
   and `emboldened` do not change. A test: `fair=False` and
   `one_way=False` each change a known letter (n), the defaults give
   the committed outline.
3. One list of the known variables, in `stroke_cache.py` beside
   STEERING (one source of truth): `MYIA_JOBS`, `MYIA_RECHECK`,
   `MYIA_STROKE_CACHE`, `MYIA_BLEND_LOG`, `MYIA_STROKE_OUT_LOG`,
   `MYIA_REPRODUCE_KEEP`, `MYIA_SOURCES`, `MYIA_REQUIRE_REFERENCES`.
   `check_reproducible.py` refuses to run with any other `MYIA_*` set
   and names it (so a stale `MYIA_G2=0` in a shell is told, not
   ignored). The cache goes on keying every variable outside STEERING.
   `tests/test_stroke_cache.py` uses `MYIA_G2_ERR` as its example of a
   keyed variable: any name outside STEERING does.
4. The records that say "MYIA_…=0 to compare" brought in line:
   `styles.md` (blend, one way, fair), stroke_bold's and fair_arcs'
   comments, `commands.md`. FONT-DESIGN.md and FONTLOG.txt are history
   and stay.

Open points found on the way, for T4's session to look at, not to fix
blind:

- CORNER_OWN's comment says that with the heavier side moved by its own
  weight "γ's loop met its stem in a notch", yet mode 2, which does
  that, is what ships. No record says why 2 was taken over 1. Look at
  the Bold Italic γ's loop at its stem on a sheet when the comment is
  rewritten; if the notch is there it is γ's own fault (drawn, or its
  recipe), not a reason to bring the mode back.
- With one_way on, every letter is stroked twice even without a knee
  (the first pass only finds knees). Finding the knees needs the fits,
  not the cleaning and fairing; skipping those in the first pass would
  save a good part of the uncached time. An optimisation with a
  bit-identity proof, not part of T4.
- LEFTOVER (stroke_bold) and SHORT (fair_arcs) must be equal and are two
  literals: import one from the other when the file is open anyway.
- The work of 2026-10-29 (blend, gate, knees) has no entry in
  FONT-DESIGN.md or FONTLOG.txt; styles.md, the commits 10ddbcdc,
  960a90fa, cef605f8 and this file are its record.
