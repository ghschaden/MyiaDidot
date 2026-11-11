# The Bold against its references: measures, rules proposed, the Bold Italic

F4 of TODO.md, ahead of phase 7's drawing (2026-11-11). Nothing here is
carried out: the rules are proposals for the trial sheet and the
designer's eye. The references are a calibrated range, not a target.

Measures: `scripts/quality/bold_measures.py --range` (and `--italic`),
then `scripts/quality/bold_targets.py` (`--italic`), which puts each
measure on the font's own scale (over its stem, or its x-height or cap
height) and says where Myia lies against Old Standard, Bodoni Moda and
Libre Bodoni: `build/quality/bold-targets.md`, `bold-targets-italic.md`.
Lengths below are units of a 1000 em unless marked "font units" (the
sources' 2048 em, in which make_bold's constants are written).

## How the upright Bold is made today

`scripts/make_bold.py`, `main()`; the upright Bold never goes through the
stroker (that is the italic source's path, `docs/claude/stroking.md`).

1. Each glyph is widened across by `KX` 1.04 ("so the counters keep their
   light"), then emboldened by weight (`derive.embolden_by_weight`): every
   node is moved along its normal, across by `AX` 90 font units times a
   share k, up and down by `AY` 8 always. k runs from 0 at a stroke 60
   thick (`THIN`) to 1 at 160 (`THICK`). A junction takes the heavier
   stroke's k (derive.py `factor`). Serif brackets the move overran are
   slid back (`keep_brackets`); flat edges return to their zones
   (`rezone`).
2. The gain is additive: lowercase stems 164 to 254 font units, capital
   stems 208 to 298.
3. The advance is `width × KX + AX`; the side space is then fitted to the
   white a plain emboldening leaves (`optical_fit`), cut by `BOLD_CUT` 19
   (figures 28, then tabular), and `BOLD_SIDEBEARINGS` added (t, N).
4. By family or feature today: `OVALS` (o O zero: the Regular's curves
   refitted to the emboldened box and area); `part_serifs` (serif tips
   that merge are shortened in the source until half the gap stays);
   `stem_handles.fair` (a curve's handle past a stem's edge: arches of
   n m h, u's foot, J's hook); `r_hook.fair_bold_stem` (r); `bold_dots`
   (i j and the points); `stem_joins` at finalization.
5. Nothing treats counters, apertures, join thickness or balls of the
   core letters apart: no constant, no table. Balls are thick strokes like
   any other: AX across, AY up and down.
6. No core letter a-z A-Z is marked drawn; of the figures, four and
   fouroldstyle are.
7. Point for point with the Regular: built that way but enforced by no
   test. Of a-z A-Z 0-9 all agree in point count and types except k
   (27 | 25) and eight (52 | 50); the step that drops them is not found.

Where a family rule can go: a name set read in the per-glyph loop (as
OVALS, with its `refit` slot); per-glyph AX, AY, THIN, THICK or KX passed
in `make()` (the small glyphs' `sc` does this); per node in `factor`
(derive.py, where a junction's weight is chosen); after the loop beside
`stem_handles.fair`, before the derived letters are built from the bases;
or a finalization pass for the Bold.

## What the measures say

The working assumption of phase 7 (counters and apertures to open, joins
to thin) is not what the measures show. On its own scale the upright Bold
lies inside the three references' range in most measures, and where it
leaves it, it is on the open side.

| | Myia | Old Standard | Bodoni Moda | Libre Bodoni |
|---|---|---|---|---|
| n stem, Regular > Bold | 80 > 128 | 72 > 116 | 88 > 139 | 110 > 138 |
| H stem | 102 > 149 | 92 > 148 | 96 > 156 | 134 > 158 |
| H stem over n stem | 1.27 > 1.17 | 1.28 > 1.28 | 1.09 > 1.12 | 1.22 > 1.14 |
| n advance | 553 > 599 | 540 > 556 | 596 > 628 | 596 > 614 |
| n counter width | 202 > 166 | 198 > 142 | 214 > 166 | 178 > 162 |
| n gap between the feet | 66 > 26 | 70 > 46 | 86 > 58 | 38 > 30 |
| m gap between the feet | 50 > 14 | 62 > 38 | 66 > 46 | 30 > 26 |
| o advance | 488 > 528 | 496 > 504 | 561 > 567 | 562 > 589 |
| o counter width | 234 > 198 | 222 > 150 | 250 > 190 | 210 > 186 |
| O advance | 771 > 822 | 700 > 712 | 750 > 774 | 782 > 823 |
| O counter width | 442 > 417 | 366 > 250 | 408 > 330 | 374 > 362 |
| r ball | 74 > 116 | 80 > 122 | 106 > 157 | 106 > 144 |

(x-heights 432, 456 > 474, 460, 450; cap heights 700, 712, 750, 754.)

1. **Width.** The Bold's advance gains 8 % (KX and AX together) where the
   references gain 0 to 5 %. So the counters are wider against the stem
   than in any of the three: arches (n m h u) +6 %, bowls (b d p q) +7 %,
   o +13 %, the capital rounds +11 to +22 % (O Q +22). The references
   take the weight inward; Myia's goes outward. The Regular lies inside
   the range in all of these: this is the emboldening's doing, and KX's
   stated purpose.
2. **Gaps between serifs close.** The stems grow 44 toward each other and
   the serifs keep their reach, so the gap between n's feet falls to 0.39
   of the Regular's, the counter only to 0.82: the gap is 0.16 of the
   counter's width where the Regular has 0.33. The references keep the
   gap's share (gain 0.89 to 0.91 in all three). Outside the range: n
   -15 %, m -45 %, w -47 %, v -7 %, and in the capitals X -43 %, K -26 %,
   Y -22 %, M -21 %, F -23 % (against its stem), J -22 %.
3. **Joins are inside the range.** Where n's arch leaves its stem: 32 >
   33 (gain 1.04); Old Standard thins (0.83), the two Bodonis thicken
   (1.08, 1.19). Bowls join thinner than the references' (gain against
   the stem 0.56; theirs 0.63 to 0.77), inside the range. Nothing asks for
   thinner joins but Old Standard alone.
4. **Balls are inside the range**, except r's: 0.91 of the stem where the
   references have 1.04 to 1.13 (-13 %); the Regular's is already at the
   bottom of its range (-5 %). Not measured: whether a ball that gains 44
   across and 4 up and down is still round.
5. **Capital stems lose against the lowercase** because the gain is
   additive: H over n falls from 1.27 to 1.17. Old Standard keeps 1.28,
   the Bodonis have 1.12 and 1.14: inside the range, and the capital stem
   is already at its top against the cap height (+2 %). No change follows
   from the numbers; whether the capitals look light beside the lowercase
   is for the eye.
6. **The pilot's other letters.** a: counters and joins in range; the
   opening under its ball stays as wide as the Regular's (171 of 1000
   x-heights; references 101 to 108), the open side. e: eye larger than
   any reference's (+23 % area), lower counter and aperture in range.
   s: in range, counters 6 to 10 % wide. g: in range where the measure
   holds (its counters are counted 4 in the Regular, 3 in the Bold).
   c: aperture 12 % narrow against the stem, inherited from the Regular
   (-7 %).
7. **Figures.** Counters wide as the letters' (5 6 7 9: +9 to +12 %);
   zero's thick stroke is 12 % under the range in the Bold and 11 % in
   the Regular: the Regular's design, not the emboldening.

## Rules proposed for make_bold

In the order of what the numbers support. Each is a fault a family
shares, so it belongs in the generator (CLAUDE.md, "Fix finished letters
locally"); none is to be accepted before its sheet.

**B1. Serif gaps keep their share of the counter** (n m h; v w; X Y K M;
then whatever the sweep finds: small caps, Cyrillic п и н, Greek η π).
Where two serifs face each other across a counter, the Bold's gap is at
least 0.9 of the Regular's share of the counter's width: n 26 > 49
(each inner serif about 12 shorter, 24 font units), m 14 > 36. The
mechanism exists: `part_serifs` (make_bold.py, `PART_GAP`, `PART_KEEP`,
`PART_STEP`) already shortens serif tips in the source until a share of
the gap stays; today it acts only where tips partly merge. The rule is a
second condition there, measured against the counter (bold_measures'
`counters()` gives gap and width). To see on the sheet: whether inner
serifs shorter than outer ones read as a fault at 144 pt (Old Standard's
Bold does it: gap 46 of a counter 142).

**B2. How much wider the Bold is: KX** (every letter; one constant). Not
a family rule but the one decision behind finding 1. At KX 1.00 n's
counter comes to about 158 (1.23 stems; the references 1.17 to 1.22) and
the advance gain to about 1.04, the top of the range instead of beyond
it. Proposed as a trial only, KX 1.04 | 1.02 | 1.00 side by side at 12
and 144 pt: wider counters are no fault in text, and the present value
was chosen for them. If KX stays, B1 matters more, since the stems then
stay where they are and only the serifs can give.

**B3. Capital rounds take their weight inward** (O C G Q; by extension
D's bowl). Their counters are 11 to 22 % wider against the stem than any
reference's; KX 1.00 for this family alone brings O from 822 to about
791 and still leaves it some 10 % over. To reach the range O would keep
the Regular's advance (771), as Old Standard's does (700 > 712). Trial
values: KX 1.00, and the Regular's advance kept, through the `OVALS`
refit, which already fits the Regular's curves to a given box.

**B4. r's ball at the stem's weight** (one letter, so a fix in
`r_hook.py` beside `fair_bold_stem`, or drawn): 116 > about 133, the
references' lowest share (1.04 stems).

**Not proposed:** thinner joins (finding 3; if the sheet asks for Old
Standard's thinning after all, the place is derive.py's `factor`, which
gives a junction the heavier stroke's weight: a share between the two
strokes' there thins every join at once); a proportional gain for the
capitals (finding 5); c's aperture and zero's weight (the Regular's, for
phase 5 to 8's Regular review if at all).

**Beside the rules, for phase 7's list:** a test that the core set's
Bold agrees point for point with the Regular, k and eight entered as
exceptions that may only go; and the ball's roundness measured (finding
4) before any ball is judged on the sheet.

## The trial

a e s g n o carry B2 only (of the six, n alone has serifs facing each
other): the sheet needs m h u r v w and H O X beside them for B1, B3 and
B4. `make_bold.py REGULAR OUT.ufo` writes to any path, so a trial is
generated into `build/`, never into `sources/`. One sheet as PDF, today's
Bold | trial | Old Standard Bold, at 144 and 12 pt; one review round.

Made 2026-11-11, awaiting that round: `proofs/bold-trial-2026-11-11.pdf`
(`scripts/pilot/bold_trial.py`, `bold_trial_sheet.py`), six rows, each
adding one rule: today's Bold; B1; B1 and B4; with B3; with B2 (KX
1.00); Old Standard Bold. At 125 and 12 pt, no kerning in any row.

- B1 as tried (`gap_serifs`, in place of `part_serifs` for the run): for
  part_serifs' own pairs of facing tips, the gap's share of the white
  between the strokes, measured a quarter of the x-height into the
  letter, stays at 0.9 of the source's; both tips shortened in steps of
  4 font units. 122 glyphs' serifs come out shorter, mostly by 8 or 12
  font units a tip (n m h H: 12); the gap between n's feet 26 > 50, m's
  14 > 38, w's tops 22 > 46. Nothing else moves in those letters; with
  the letters built from them 223 glyphs differ from today's Bold. A pair whose target is not reached within the
  serifs' length is left as it is (one glyph, a small cap).
- KX 1.00: n's advance 599 > 577, its counter 166 > 158, its stem 128 >
  124 (the stem is weighed after the widening); o 528 > 509, O 822 > 791,
  as computed above.
- What the KX 1.00 row shows wrongly: its side space. `BOLD_CUT`,
  `BOLD_SIDEBEARINGS` and `BOLD_KERNING` were set for KX 1.04, so x and
  k stand too close there; the row is for the letters' proportions, not
  their fit. Two guards also tie the generator to today's KX and were
  why a KX 1.02 row is missing: `sc_feet.k_sc` (mends k.sc at fixed
  coordinates; switched off in the trial) and numero's optical fit
  ("review its placement"). A changed KX therefore means respacing the
  Bold and revisiting both, which is part of B2's cost.
- B4 as tried (`grow_ball`): the ten nodes of r's terminal scaled by
  1.147 from the neck's inner edge and the top, so that both joins stay
  smooth: the ball 116 > 137 (1.04 stems, wanted 133; the measure is the
  largest disc), the advance 453 > 472 with the ink. In the generator
  this belongs beside `r_hook.fair_bold_stem`.
- B3 as tried: O C G Q taken from a run at KX 0.943, which keeps the
  Regular's ink width: O's advance 822 > 746 (the Regular's 771 less the
  Bold's cut of the side space), its counter 417 > 374, C 755 > 685,
  G 792 > 718. Against the stem the counter is then 2.5, still above the
  references (1.7 to 2.3). In the generator a KX per family, in `make()`
  and where the advance is set.

## How this carries to the Bold Italic (phase 8)

The Bold Italic is stroked (`docs/claude/stroking.md`), not offset, and
its faults lie the other way. Against Bodoni Moda and Libre Bodoni
(Old Standard has no bold italic; two references make a narrow range):

| | Myia | Bodoni Moda | Libre Bodoni |
|---|---|---|---|
| H stem, Italic > Bold Italic | 90 > 143 | 95 > 155 | 115 > 149 |
| n advance | 538 > 580 | 571 > 586 | 560 > 592 |
| n counter width | 126 > 95 | 177 > 134 | 167 > 146 |
| o counter width | 185 > 146 | 230 > 161 | 220 > 186 |
| O advance | 671 > 764 | 714 > 752 | 769 > 789 |

1. **The arches' counters are too narrow**: against the stem n -24 %,
   h -25 %, u -28 %, and with them g -26 %, t -24 %, f -16 %. n's counter
   (95) is narrower than its stem (about 128); the references' are as
   wide as the stem or wider (1.0, 1.08). The Italic itself is inside the
   range, so this is the stroker's and its widening's doing, and a family
   fault: the arches need about 30 more across (n's advance 580 > about
   610) or the weight taken from the inside. Bowls (-4 %) and rounds
   (-3 %) are close to the range.
2. **B1 does not carry**: the italic has no serifs facing each other; its
   apertures against the counter are above the range (+19 %).
3. **B2 carries with the sign turned**: the upright's question is whether
   KX is too much, the Bold Italic's whether its widening is enough for
   the arches. They are one decision per style, not one constant.
4. **B3 carries in part**: the capital rounds' advance gains 13 % (the
   references 2 to 5 %) and lies 4 to 9 % over, but their counters are
   inside the range: the weight is right, the letter wide.
5. **Inherited from the Italic, not the stroker's** (outside in both):
   the capital straights' advance (+8 % Italic, +11 % Bold Italic), the
   capital bowls' joins (+76 %, +37 %), a's ball (-17 %, -23 %). These
   belong to phase 5 and 6, before phase 8 measures again.
6. **The method carries whole**: `bold_measures.py --italic` then
   `bold_targets.py --italic`, with the caution that in the Bold Italic n
   has no straight stem the measure finds (the style's stem is the median
   of the lowercase stems it does find), and joins are found in few
   letters (r's reads +67 %, one letter, to be looked at before believed).

None of this can be tried before phase 8: the stroker's constants are
mapped in stroking.md, and a change there waits for T4.
