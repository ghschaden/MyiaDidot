# To do

## IN PROGRESS, uncommitted: Italic glyph fixes (2026-10-22)

The person's list of italic faults, worked through in one session. Working
tree holds the changes (scripts + regenerated UFOs, `make generate` run);
**nothing committed, baselines not updated, `make test` fails 13 (below)**.

Done (in the generators unless noted):
- ƈ: a speck (rest of c's ball) cut away (make_italic ITALIC_RECIPES).
- ʄ: the recipe's stem/bar/curl numbers set to ɟ's current stem (350-495
  in the derive frame; it was tuned before the reweighting).
- җ: descender upright like қ ң ҷ (it leaned with the leg).
- Қ Җ: Ц's wedge tail replaced by the lowercase construction (exit stroke
  cut, make_italic.descender); both added to NO_TRANSPLANT.
- ʑ: rebuilt as the Regular's: bottom stroke runs on and thins (poly) into
  a small loop at its end, upright tail through the loop's left side. The
  person rejected the first version (big ɕ-like loop) as worse.
- ɮ: ʒ set whole beside l's stem as in the Regular (ZH_DX = 150 right, its
  top bar run on to the stem by a rect), stem rect matched to l's (no step).
  quality check now says "closer to the Regular's ɮ than to l": intended.
- ₫: line fitted to the italic d (ITALIC_RECIPES). ₸ (person said 20B6,
  meant 20B8): second line moved ABOVE the T in all styles (derive.py,
  as Charis/Libertinus); the Regular's ₸ rebuilt by derive.py (a draft now).
- ь ы ъ: Old Standard's outlines edited in the Italic and marked "drawn"
  (kept by reruns, but no longer follow weight changes). ь/ы: stem's
  outer edge one curve from bowl to hook, counter corner (19.5°) smoothed.
  ъ: Old Standard's design kept, its curled ear at the stem top replaced
  by one rise from the wave, the flag terminal's wobble smoothed. Scripts
  that made the edits (re-runnable on Old Standard's original points
  only): `build/italic-fixes-2026-10-22/redraw_{soft,hard}_sign.py`.
  Tried and dropped: ъ built from ь plus a flag (reads as ь, or the ear
  comes back).
- Bold Italic (make_bold.py): own recipes at its weight (ITALIC_BOLD_RECIPES
  + ITALIC_BOLD_REBUILD) for ʑ, ƈ, Қ Җ җ қ (descender balls 0.48 of the
  stroke so the curl ends without a step; Җ sweep 155 so the ball clears
  the middle stem's foot); ь pinned to ITALIC_BOLD_BY_WEIGHT (the rounder
  way came out light, 0.82).

**The person's verdict on the Bold Italic: bad before, bad after (only
differently).** The emboldened Cyrillic soft signs and their kin (ь ы ъ,
the Bulgarian ь ъ with a spur/notch where bowl meets the raised stem, ы's
dented stem) need a real pass of their own, not more patching: likely
recipes drawn at the Bold Italic's weight or a different emboldening for
these letters. Look at `sg2.png`-style before/after sheets (render tool
below) with the person.

Still failing in `make test` (all from the changes above):
- golden shaping + full-corpus digest: Italic, Bold, Bold Italic (₸, ʄ
  widths etc.): `update_test_data.py --golden --digest` once accepted.
- quality lists: Regular/Bold `uni20B8 kink` fixed (remove); new small
  kinks/smooth/extremes on ʑ Қ Җ җ ɮ ƈ ь (2-8°); `--quality`.
- emboldened-whole Bold Italic: ƈ җ қ no longer whole (list shrinks).
- glyph lint Bold Italic: new notches uni044A.loclBGR, uni044C.loclBGR
  (the Bulgarian forms, see verdict above).
- Cyrillic pairs Bold Italic: ль at 0.175 outside the references (ь's
  left side moved): an ITALIC_BOLD_KERNING entry, or wait for the pass.
Then `make reproduce` (expected clean), commit with the attribution line.

Not done from the list: nothing; everything the person named was
addressed, Bold Italic quality open as above.

Tools for this kind of work (in `build/italic-fixes-2026-10-22/`, copy
out before `make clean`): `render.py UFO OUT.png GLYPH|U+XXXX ...`
(outline + points; INK=1 solid; SCALE TOP BOTTOM env), `up.py UFO OUT
GLYPH...` (upright copy + render), `try.py OUT CH...` (rebuild a derive
recipe in the current Italic: frame lacks the generator's ~16-unit
respace offset). For exact results: copy the Italic UFO to scratch and
run `make_italic.py REGULAR COPY` (~22 s) or `make_bold.py ITALIC COPY`.
Lessons: curl `t` is (across vertical parts, across horizontal parts), not
start/end; curl radius must exceed half the stroke or the counter slits;
recipe coordinates are in the derive frame (final + ~16 in the Italic).

## Outline faults left (glyph lint, `tests/data/glyph-lint-*.txt`)

- Notches are measured at four raster phases now (2026-10-21), so the
  lists hold what stays a notch. **Bold Italic** 19 glyphs (dollar Ⱦ ɉ ɸ ɽ
  ɽ.sc ʸ ы ь ң ᵍ ᵳ ᶤ ṫ ₡ ℵ ⱥ.sc and two Greek accent stacks): ы is kept
  emboldened by weight (ITALIC_BOLD_BY_WEIGHT; the rounder way came out
  light and dented), ы.sc the rounder way (ITALIC_BOLD_ROUNDER). ɽ ᶤ ⱥ.sc
  ℵ came with the weighting change (near-threshold notches at joins, for
  the eye). **Italic** 14: ɬ ỵ ɉ, Ç ç.sc (steps under a unit), and the
  narrow arch crotch of m ḿ ṃ т ш ɯ at exactly the threshold (Old
  Standard's design).
- Regular 10, Bold 10 (see the lists).

## Derived letters still emboldened whole (junctions thicken)

`tests/data/emboldened-whole-*.txt`: Bold 37, Bold Italic 33, Italic 0
(2026-10-21: the Italic is weighted as its letters are taken, so nothing
in it is weighted whole any more).
Mostly hooks, attached pieces and curls whose recipe, rerun on the Bold,
"strays" from the emboldened letter or "misses". Candidates for recipes
drawn at the Bold's weight (`BOLD_RECIPES` / `ITALIC_BOLD_RECIPES`) or a
fixed rederive; the Bulgarian forms (в г ж ъ ь ю) and two rhotic letters
in the Bold Italic too.

## Quality findings backlog (`tests/data/quality-*.txt`)

| | Regular | Bold | Italic | Bold Italic |
|---|---|---|---|---|
| extreme (curve past its ends, no point there) | 15 | 157 | 281 | 527 |
| kink (corner meant smooth) | 101 | 208 | 569 | 609 |
| smooth (smooth node broken > 2°) | 74 | 65 | 487 | 209 |
| stroke (darker/lighter than its kind ±10 %) | 78 | 69 | 127 | 111 |
| zone (flat edge near a zone) | 58 | 59 | 143 | 139 |
| slant | | | 64 | 71 |
| width | | 27 | | |
| accent gaps | 3 | 3 | 2 | 2 |

(Counts of points, 2026-10-21. The italics' slant includes W Ⱳ w.sc
ⱳ.sc: the uncrossed W's thick diagonal leans 5°, inside the check's
window for stems.)

- Most of the Italic's are Old Standard's own outlines ("known at the
  start"); the Bold Italic inherits them. A cleanup pass on the Italic's
  sources (extremes added, near-smooth nodes made smooth) would lower both,
  but changes many glyphs: do it as its own step, with `make diffenator`.
- **stroke:** review with `make strokes` (`build/quality/strokes-STYLE.pdf`);
  designed exceptions go on the known lists.
- **Italic reweighted (2026-10-21, done):** lighter, more even, 13 tighter;
  then weighted as its letters are taken (nothing weighted whole), the W
  uncrossed (1.25 cap heights, of two narrowed Vs; w.sc of v.sc, Ⱳ ⱳ.sc
  ₩ refitted) and a's bowl 40 lighter (FONTLOG). Left from it:
  - Review the Italic's drafts (all derived letters, small caps and
    figures are drafts): `drafts-review-Italic.pdf`,
    `smallcaps-review-Italic.pdf` (`make proof`).
  - r and I still as heavy as n and H (Old Standard's): a preview first,
    if they still stand out on full pages with the new W and a.
  - The old-style figures came out a little darker (made from the
    weighted lining ones): 3 4 5 9 at 1.35-1.52 of their stem kind.
  - Bold Italic Ⱳ: the middle serif runs into the curl's stroke at the
    top; for the eye.
- **accent gaps (2026-10-21, done for the Greek capitals):** the breathings
  and tonos beside Ὀ Ὁ Ό … sit at one height, as Libertinus's do; the
  check measured the capitals' overshoot. It skips marks set beside a
  letter now, and counts from the flat zone a round edge overshoots (dots
  below and hooks sit at one height in Libertinus and Charis too). Left:
  i j (their own dot, designed) and ṫ in the Regular and Bold: its dot
  sits about 60 units nearer the t than ż's to the z, where Libertinus
  and Charis keep the two gaps equal. For the person's eye.

## Hinting

- Letters still off their zone (glyphs): TrueType Regular 3, Italic 10,
  Bold Italic 3; CFF Regular 1, Bold 1, Italic 4, Bold Italic 3
  (`tests/data/hint-zones*.txt`). Most are designed (𝔖 Fraktur, the horn,
  Ʋ); a few round bottoms one row off O's in the v35 interpreter only.
  New in the Italic (2026-10-21): v.sc w.sc ѵ.sc ⱳ.sc bottoms and ae.sc's
  top a pixel or two off, and Þ's bowl top (1077) 7-11 px off in v35/v40
  though Þ did not change: the small caps' tips moved a unit and the
  small-cap zone with them. Check Þ at small sizes.

## Features

- The italics lack the Regular's extra ligatures (ct st, fb fh fk ft and
  their ff forms, the long-s ligatures), left out with their rules
  (`make_italic.drop_ligatures`, styles-agree-Italic.txt). Italic forms
  would have to be drawn.

## Small leftovers

- **ɺ, Bold Italic:** the arm's bracket bulges 6 units past its end (the
  extreme check allows 5), at 617,1384, where the italic stem leans back
  past the end point. Its foot has the same at HEAD (9 units, 191,66).
  Likely the italic's natural shape rather than a fault.
- **Smooth rounding in the Italic:** `make_italic.py` saves with
  `write(..., smooth=False)`. With `make_bold.round_smoothly` the Italic's
  smooth breaks would go 678 → 540, but the Bold Italic is made of the
  Italic's outlines, and the unit shifts move about 14 Bold Italic glyphs
  across the checks' thresholds (new smooth breaks and extremes there).
  Turn it on only together with a look at those.
- **Four Bold Italic pairs** (of Wh it ba) measure tight against the
  references; reviewed 2026-10-20 and left (they look right beside Bodoni
  Moda). Nothing to do unless the proofs say otherwise.
- **Git stash `batch2-wip`** (91 files, older work): check whether anything
  in it is still wanted, then drop it.
