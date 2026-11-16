# Spacing, kerning, figures

Moved from CLAUDE.md (its ground rules apply).

- Spacing: the Regular's letters were tightened once by `scripts/respace.py`
  (20 a side, Greek lowercase 10, of which 8 were given back after measuring
  Greek pairs; recorded in lib `org.myiadidot.respaced`, a second run
  refuses). Greek spacing and kerning are measured against Greek references
  (GFS Didot, EB Garamond, Libertinus, Charis), calibrated by each style's
  own Latin: `scripts/quality/greek_pairs.py STYLE`; the italics' Greek
  cuts are ITALIC_CUT_GREEK (data_italic.py) and BOLD_ITALIC_CUT_GREEK
  (data_bold_italic.py), their Greek pairs in ITALIC_KERNING, BOLD_KERNING and
  ITALIC_BOLD_KERNING. Cyrillic likewise (`greek_pairs.py STYLE --script
  cyrillic`, against Old Standard, EB Garamond, Libertinus, Charis); the
  Regular's pairs made for the upright д л ѵ are dropped in the italics
  (ITALIC_UNKERNED). Accented letters share their base letter's
  kerning groups, letters shaped like another its groups (ALIKE): both by
  `scripts/kern_groups.py` on the Regular. Where the group's kerning
  would bring the accent too near in any style (Yì, fï, ΤἈ) the letter
  joins guarded (lib `org.myiadidot.kernGuarded`): kern_clear.py gives
  it, per style, exceptions as tight as 40 units of white allow (looser
  than unkerned where even that is too near: the italics' ĽV); then
  kern_clear.py, smallcaps.py. Gaps: `scripts/quality/kern_coverage.py UFO`.
  Reviewed collisions (ą į ų before j, the Bold Italic's AY) are
  loosened to CLEAR units of white by `scripts/kern_clear.py` (PAIRS),
  per style: the generators undo the source's (lib
  `org.myiadidot.kernCleared`) and find their own. Pairs for PAIRS are
  found by `scripts/quality/collisions.py` (`make collisions`): every
  letter and figure beside the closing and opening signs, superiors and
  case forms, kerned or not, by kern_clear's own measure; what is left is
  listed in `tests/data/collisions*.txt` (docs/claude/collisions.md).
  Besides PAIRS, kern_clear.entries() takes every sign beside every
  letter and figure, glyph by glyph so one member's overhang does not
  loosen its group: the opening signs ( [ { „ “ ‘ ¡ ¿ before one, the
  closing ? ! ) ] } ’ ” “ * : ; after one, the case forms beside the
  capitals. A sign keeps more white than CLEAR (kern_clear.clearance,
  chosen on running text 2026-11-13): OPEN_CLEAR 100 after an opening
  sign, MARK_CLEAR 60 before ! ?, CLOSE_CLEAR 40 before the other
  closers, SUPERIOR_CLEAR 60 before a superior figure (a note's number;
  proofs/2026-11/superior-clearance-text-2026-11-13.pdf); ª º after a letter and
  letters against letters keep CLEAR (20). Every capital before an
  ascender letter of its script (kern_clear.ascender_entries: U b, N l,
  Ü h, Н б, Η β; the ascenders by their base letter, so ľ ḷ count and
  ĭ î do not) keeps ASCENDER_CLEAR (60) units of white measured every way
  on the inks above the x-height (Ink.white_above): the top serifs meet
  on a diagonal, b's just above U's, where the measure across has no row
  in common, and foot serifs are left to the spacing (A n as A b). Found
  as Üb on the pangram page (2026-11-13): the italics' serifs met (1-3
  units), the Bold's U b had 28; the value was chosen on running text
  (proofs/2026-11/ascender-clearance-2026-11-13.pdf). Every capital before a
  lowercase letter of its script with a mark or dot above that is no
  ascender (kern_clear.accent_entries: N ǐ, H ȉ, Γ ῖ, Υ ϊ, Ѵ ї) keeps
  ACCENT_CLEAR (40, GUARD's white) by the same measure: a wide mark on a
  narrow i reaches over the capital's serif (the Bold's U ǐ met, Charis
  and Libertinus keep 90-130 there; proofs/2026-11/accent-clearance-2026-11-13.pdf,
  candidates 20/40/60; 40 chosen by the designer 2026-11-14). f before
  a letter whose mark or ascender its hook meets (fî fǐ fä fľ, and fl
  with liga off) is f.short, ff ff.short (calt, caltShortF after the
  ligatures; drawn by draft_ligatures.short_hook: the hook x0.6 about the
  stem's top; the italics' are their f and ff), its class every Latin
  lowercase letter kern_clear.short_f_letters finds within ACCENT_CLEAR
  of f in the Regular or the Bold (tests/test_f_short.py); where a wide
  mark still reaches back over its stem (ǐ ĭ ȉ ǰ) the short f keeps
  ACCENT_CLEAR the same way (short_f_entries; f.short ȉ +146), but not
  before an ascender: the italics' short f is their f, its hook over the
  ascender beside it, and German sets f h, f b unligated (kerned apart,
  the italic Kaufhaus opened 140 units). Its glyph entries take the place of a group
  guard that one member's mark had forced (Ɐ before all of i's group for
  ĭ, U before ẫ for Ư's horn). An entry in two families is measured by
  each in turn, the second from the first's value (Ƙ l: PAIRS, then the
  ascenders). A
  guarded member that a group entry decides gets its own exception where
  the group's value leaves it touching (the Bold's (ɉ, ąɉ). The italics'
  [j (j {j are looser by hand besides (data_italic.ITALIC_KERNING +60). make_bold.py adds the Bold's own cut, make_italic.py
  undoes the Regular's in memory (it is tuned on the old spacing) and
  applies the Italic's; derive.py too builds on the uncut spacing and cuts
  again. It leaves kerning alone. The Bold's figures have a cut of their
  own (data_bold.py BOLD_FIGURE_CUT), then share their mean width
  (tabular_figures; the figure space and dash too). The Italic's letters are made at Old
  Standard's weight and their thick strokes made heavier at the end
  (data_italic.py WEIGHT, make_italic.weight_thick):
  recipe widths are for the weight before that; derived letters that keep
  their whole base are then made of the weighted base (make_bold's
  follow_bases, as in the Bold). Emboldening (derive.embolden)
  keeps smooth nodes smooth and fits the handles; derive.rezone puts flat
  edges it moved back on the zones. The figures are proportional by
  default, lining and old-style alike (2026-11-14, as GFS Didot, Bodoni
  Moda and Libre Bodoni; Charis, Libertinus, EB Garamond and Old Standard
  default to tabular): `scripts/space_figures.py`, run by
  make_bold.py/make_italic.py and on the Regular (check-regular), fits each
  by its shapes: the old-style ones each side as n and o, the lining ones
  each side the 0's optical space plus its own amount
  (`data_regular.FIGURE_SIDES`, 2026-11-14 on
  `proofs/2026-11/figures-sides-2026-11-14.pdf`: equal sides set the figures 0.2
  H-gaps tighter than seven references and the open sides, 4's left and
  the 7, too close; each side to the references' median), with a floor
  (across the foot serifs' band the ink keeps I's mean side, `FOOT`). The
  italics have tables of their own (`data_italic.ITALIC_FIGURE_SIDES`,
  `data_bold_italic.BOLD_ITALIC_FIGURE_SIDES`, 2026-11-14 on
  `proofs/2026-11/figures-italics-2026-11-14.pdf`): each side over the H's on that
  side, no foot floor, fitted by `figure_pairs.py`'s absolute fit (pair
  gaps over the cap height, figures beside H O n o too). Judged upright
  the italic letters stand left in their advance; over the 0's the
  figures stood about 95 units right of them (0 o and 1 H tight, H 1
  loose), which figure-figure pairs cannot show. Over H H the Bold
  Italic's figures looked tight only because its capitals are loose (H H
  0.32 of the cap height, references 0.22-0.25). Figure kerns, in the
  Regular (the Bold by KX, the italics by their rule): 5 before 1 7 2,
  7 before 1 3, 7 and 2 before . , (what the sides leave, against the
  other figures before the period). Makes the tabular `.tf` forms (components, centred in the
  0's width) that tnum gives, and the lnum/pnum/tnum/zero block; make_bold's
  `tabular_figures` sets the figure space and dash to the 0's width. Capital spacing (cpsp): `scripts/cpsp.py` on
  the Regular. Case-sensitive punctuation (case, `.case` glyphs):
  `scripts/case_forms.py`, run by make_bold.py/make_italic.py on what they
  make. Per-style spacing tweaks: data_bold.py BOLD_SIDEBEARINGS,
  data_italic.py ITALIC_SIDEBEARINGS and ITALIC_KERNING; one-off sidebearing
  changes with respace.sidebearings() (it carries composites along).

## The italics' Latin kerning (TODO.md F2 / phase 3)

State 2026-11-12: in the generators. make_italic.py and make_bold.py (the
Bold Italic, against the Bold) call `italic_kerning.apply` on the finished
outlines, just before kern_clear; the hand tables go over it. The measure,
rule and prototype: `scripts/italic_kerning.py`, tests/test_italic_kerning.py;
the values approved on `proofs/2026-11/italic-kerning-2026-11-11.pdf`
(`scripts/italic_kerning_sheet.py`; `--before REV` sets an italic at a
revision beside the one in sources/) with nothing tightened past the
upright and one wish, K y (below). The pairs left outside the reference
italics' range are held by tests/test_latin_pairs.py
(tests/data/latin-pairs-Italic.txt, -BoldItalic.txt; only shrink).

**The rule.** An upright pair's kerning says how much white that pair is to
have against the style's plain rhythm; the italic of the same weight
(Italic from Regular, Bold Italic from Bold) gets the kerning that gives
its own shapes the same share of its own rhythm.

- White of a pair: the mean white between the two inks over the rows where
  they face each other (from the higher of their lowest points to the
  lower of their highest), each row counted no further than 0.2 x-heights
  past the pair's near white. The near white is the row at the 20 %
  quantile, not the nearest row: an exit or entry hairline counts by the
  rows it fills, an overhang (f's top, T's bar) by the rows where it faces
  ink. Row distances are the same sloped or upright, so nothing is
  deslanted.
- Rhythm: the same white of n n, H H, H n or n H, by the two letters' case
  (figures and punctuation stand with the capitals).
- Italic value = share x the italic's rhythm - the italic's unkerned white,
  where share = (upright white + upright kerning) / upright rhythm.
- Three limits. No tighter than the upright's value (TIGHTEN = 0). The
  inks no nearer than the upright's pair has them, or than the italic's own
  rhythm has them where that is less. A kerning keeps its sign or goes.
- Group pairs are measured on the group's name-giving glyph; the accented
  members are kern_clear's (guard) afterwards, as now.

**Why no tightening.** The rule alone would close what the slope opens at
the baseline after V Y P F T (V, from -320 to -467, P a from -72 to -178).
The reference italics do not: pairs outside the range of five of them
(Bodoni Moda, Libre Bodoni, EB Garamond, Libertinus, Charis; share as
above, kerning on), of about 215 measured, Italic / Bold Italic: today
81 / 59, all of them too tight; rule with full tightening 60 / 41; half
45 / 33; none 40 / 29. In Bodoni Moda, Libertinus and Charis a pair's share
in the italic is the roman's or a little more (A V 1.39 / 1.48, 1.23 /
1.19, 1.75 / 1.79), which is the rule's premise; Myia's Italic today has
A V at 0.90 against the Regular's 1.19, A T 0.93 / 1.20, A v 0.78 / 1.11.

**What it changes** (build/quality/italic-kerning-STYLE.tsv; `--refs` adds
the references' range). Of 218 Latin pairs in the Italic 132 change by 8
units or more, all looser: the capital A's pairs most (A V -284 to -124,
A Y -295 to -117, A T -180 to -37, A’ -272 to -145), L T L V L Y, the
rounds and P before V Y (O Y -152 to -95, P Y -112 to -14), R and B before
V Y, T before a c (-80 to -46, -108 to -77), and
41 pairs go altogether, mostly lowercase diagonals and k, whose italic
forms are other letters (A v, a y, k c, v e, y and v before comma, b x).
The Bold Italic alike (141 of 229).

**What stays a hand exception** (ITALIC_KERNING, ITALIC_BOLD_KERNING,
applied after the computed values):

| entries | why the rule does not give them |
|---|---|
| Greek, Cyrillic pairs | not computed: measured against their own references per style (greek_pairs.py), with tests that hold them |
| f before i u m p r (-60, Italic) | no pair in the Regular; the italic f's own overhang |
| ƴ before a c e (-120) | tighter than the upright's -40, which TIGHTEN refuses; its hook sets its right side |
| ſ ſſ before c e g q (-80, Bold Italic) | tighter than the Bold's -62; from a proof (2026-11-05) |
| u t, w a, g h, g a, i f, G r, a f, a y, v a, u f, R e (positive), f r, f t (Bold Italic) | no pair in the Bold, or a sign the rule does not turn (a y, v a: it gives 0); phase 3's re-proof decides each |
| small caps (B.sc O.sc ...) | not computed; smallcaps.py |
| K before y, slightly tighter (the review of 2026-11-11, on "Kyoto"; -30 in ITALIC_KERNING since 2026-11-12, the Bold Italic's -31 by KX, to be confirmed on the sheet) | unkerned in all four styles, and the rule would not kern the italics even if the Regular did: the upright K y is the looser one (share 1.69 and 1.75 against the italics' 1.34; the reference italics 1.36-1.98), so a Regular pair goes by its sign. A hand value for both italics, about -30 to start from (the inks are 321 and 333 apart), set on a sheet with K v and K w, which leave the same white |

Deleted when the rule went in (2026-11-12), as it makes them needless: a
before v (-44, the rule -19), v y before c (-10, the rule 0), and
ITALIC_UNKERNED's t t and t f (the rule drops them by sign).

Not carried into the Bold Italic, as today: the Bold's own exceptions
(BOLD_KERNING's Latin: n t, a t, a s, a u, k t, z t, f s, S m, t r, a g,
x t), made for the upright bold shapes. The prototype's table lists them
with a value; the generator is to leave them out.

**In the generators** (2026-11-12). make_italic.py: after
`install_italic_i`, the computed values over the Regular's (opened as saved,
not the respace-undone copy the run reads its offsets from), then
ITALIC_KERNING, ITALIC_UNKERNED, kern_clear. make_bold.py for the Bold
Italic: the Italic's kerning scaled by KX as before, then at the same point
the values computed against the Bold beside the Italic it reads
(`sources/MyiaDidot-Bold.ufo`; check_reproducible.py's snapshot), leaving
out BOLD_KERNING's keys, then ITALIC_BOLD_KERNING (moved there from after
the scaling), kern_clear. So the Bold must be generated before the Bold
Italic, as `make generate` does. Greek, Cyrillic and small-cap pairs keep
their path; the small caps follow the capitals' new values (smallcaps.py).
Pairs the rule does not compute (no rows) keep the Italic's, scaled.
A pair the rule sets plain stays in the kerning at 0, and kern_clear's
guard holds the guarded letters clear under a 0 as under a negative value:
removed, the guard went with it, and the accented members its group pair
had held met their neighbours (ᵬ's tilde 10-14 units into v w y, the Bold
Italic's ổ 48 into ǰ, ồ ǰ and ᵬ ϳ within 8-18; found in the shaping
report, 2026-11-12). Held by a test on the result, not by the step
remembering (collisions.md, "The guard's result held by a test",
specified 2026-11-16): the source style's kerned group pairs with
guarded members stay keys, and the guard's white is measured again at
the end. Where no group pair was ever kerned the guard does not reach,
and phase 1's sweep (signs only) does not either: those pairs are found
by family (the same section, point 2).

**Open.** The quantile and the depth are set by reasoning and by the
count above, not tuned. Pairs that do not face each other (’ before s)
are not measured; there are none among today's Latin pairs. Unkerned
upright pairs are never kerned by the rule, though the italic may need
them (phase 2 gives the Regular its missing pairs first).

## One measure for Latin kerning, upright and italic (2026-11-15)

Decided on Fable from the two measures' construction and checked the
same day by `scripts/quality/pair_measures.py` (the gap with one of its
choices at a time replaced by the share's, all four styles:
build/quality/pair-measures-STYLE.md; "Confirmed" below, which corrects
two of the table's first attributions). The question was open-for-fable.md's "Two pair
measures, no rule which one decides" (phase 2, 2026-11-13) and the Bold
Italic's f r of 2026-11-14.

**The share decides, in all four styles.** A Latin pair is judged by
`italic_kerning`'s share: the pair's white as set (kerning on) over the
plain rhythm of its two cases, Myia's against the reference fonts' for
the same pair (`Built.share`, `outside`). It is the measure the italics'
kerning is computed from and tests/test_latin_pairs.py holds; an upright
pair set by another yardstick would hand the italics a share that
yardstick never looked at. pairs.py's gap is no second judge: it stays
for what it is good at, finding the pairs (below).

**Why the two disagree**: four differences of construction. Which
family goes with which is the run's finding, not the first reading's
(R v w y had been laid to "over", T's pairs to "rows").

| | gap (quality/pairs.py) | share (italic_kerning.py) | what the gap's choice does |
|---|---|---|---|
| over | n n, for every pair | the cases' own rhythm: n n, H H, H n, n H | a capital's pair is told against lowercase spacing. It matters only where a style's capitals stand wider against its lowercase than the references' do: the Bold's H H (a fifth over the references' median and past their highest; the Regular's H n and H H lie within 3 % of the median, the italics' inside the range). Switched alone it settles the Bold's R O, R Q and A" and nothing else |
| rows | baseline to x-height, always | where the two inks face each other, from the higher foot to the lower head | a quote is not seen at all, or by its tail (A“ A" L“ “A: no gap to give). For letters and figures the rows change little by themselves (R v, R O, T u, 7. within a few per cent of the gap as it was) |
| near white | the nearest single row | the row at the 20 % quantile | one row of a serif's or a hairline's tip sets the depth all other rows are cut at; the eye reads the tip by the rows it fills. The largest part of the disagreement: T before lowercase (the foot serif's tip: the gap reads half the references' white, the quantile puts T u p z m n r inside or within 7 % of the range), the Bold's R v w y (R's leg: a fifth too loose by the gap, inside by the quantile), f r in the Bold Italic (f's bar) |
| verdict | 0.15 n-gaps past the references' range, of four fonts or more | past the range of three or more that set the pair | the Bold's 7. is outside only by the gap's own references and margin; on the share's five it is inside by either measure |

So for a sign the gap measures another thing or nothing; for letters
the two differ mostly in the near white, and there the quantile is the
one reasoned for (the italics' rule, above).

**Confirmed** (2026-11-15, the fonts built that day): on R v w y, W v w,
R O Q, 7. 1., A“ A", T u p z m n r (uprights) and f r, R v, W v, R O, T u
(italics), wherever the gap and the share give different verdicts
against the same five references, one switch alone brings the gap to the
share's: the near white for T's pairs, the Bold's R v w y and the
italics' f r and T u; "over" for the Bold's R O, R Q, A" and the Italic's
R O; for A“ only the rows give a number at all. The Regular's T p z m n
r keep 1 to 7 % past the range after the near white's switch where the
share has them inside: the other two choices together. In the Regular as
it stands the two measures agree on R v w y, W v w, R O Q, 7. and 1.
(inside by both): the disagreement of 2026-11-13 there was the gap
against its references' median and its own set of fonts, and phase 2's
pairs have been set since. Both measures call R v too tight in the two
italics (10 to 25 % under the range).

**f r in the Bold Italic** (-95, a hand exception: no pair in the Bold)
goes by the share like every pair in tests/data/latin-pairs-BoldItalic.txt:
inside the reference italics' range it is done; outside, it is set to
the range's nearer edge on the next sheet. The gap's verdict on it is
dropped either way. Measured 2026-11-15: its share is 1.10 against the
references' 1.23 to 1.50, a tenth too tight (the gap had it loose): for
the next sheet.

**Setting a pair** (phase 2's open pairs, on Sonnet):

1. The list: the upright's kerned pairs (`latin_pairs`) and pairs.py's
   300 most frequent of the corpus, and the phase's requested ones: the
   gap script's job is the list, kerned or not.
2. Each pair's share in Myia and in the five references of the style
   (Bodoni Moda, Libre Bodoni, EB Garamond, Libertinus, Charis: the same
   five as the italics').
3. First **spacing or pair** (next paragraph), then the pairs left.
4. A pair is changed when it lies outside the range of the references
   that set it (three at least) **and** Libertinus and Charis both lie on
   the range's side of Myia (the reference-font rule). Inside the range
   nothing is set, whatever a sheet of numbers suggests: that is the
   eye's, on a proof.
5. The value: the range's nearer edge, as kerning = edge x Myia's rhythm
   - Myia's unkerned white; under 8 units (`DROP`) no pair. Never
   nearer than kern_clear's `GUARD`.
6. In the Regular only (the Bold by KX, the italics by the rule), as an
   absolute value per group key; before writing, no two pairs of the
   round on one key; an accented right group (kern2.agrave ...) gets its
   base pair's change and is never left tighter than the base.
7. A sheet of words per family in four styles, `make regress` and `make
   diffenator` read, then tests/data/latin-pairs-*.txt: lines that fall
   away deleted. For the uprights the lists do not exist yet (below).

**Spacing or pair.** Before any pair of a letter is set: that letter's
`off` (the share past the range, signed) over all its partners of one
case on one side, kerned or not. If two thirds of them, six at least,
are off the same way, it is the letter's side bearing: the median `off`
x the rhythm is the change, made in the Regular's side bearing (the
master; this file's first sections for what follows
in the generated styles), on a sheet for the designer, since a side
bearing moves every line of text. The pairs are measured again after
it. Known from phase 2: ' and ” before the stem capitals, G before the
lowercase. A letter with fewer partners off is pairs.

**What the share does not see**, and what is used there:

- Fewer than 8 facing rows (`MIN_ROWS`: a quote before a round
  lowercase, ’ s; 41 of phase 2's pairs): no share. There the measure is
  the nearest ink every way (kern_clear's `Ink`, the collision sweep's
  measure) over the same of the cases' rhythm, against the references:
  a clearance, used only where the share is None, never beside it.
- White deeper than 0.2 x-heights past the near white (W's open side
  before o: the nearest ink said "in range" where the eye said "too
  big"): cut off by `DEPTH`, by design. Such a pair is the eye's:
  candidates on a sheet, the chosen value a hand entry with its date
  (W c a u, 2026-11-14), and it stays out of the reference lists.
- Greek, Cyrillic and small caps: their own tools, as before.

**For Opus, to build** (none of it exists):

- `quality/pairs.py`: its list kept, the gap replaced by `Built.share`
  with the verdict of step 4, `off` printed; for pairs without a share,
  the clearance. `make pairs` then says what test_latin_pairs says.
- A per-letter table for "spacing or pair" (letter, side, case of the
  partners, how many measured, how many off each way, the median).
- tests/data/latin-pairs-Regular.txt and -Bold.txt, and
  test_latin_pairs over the uprights: today's outside pairs listed with
  phase 2's reasons, lists that only shrink.
- (Done 2026-11-15: the confirmations, `scripts/quality/pair_measures.py
  STYLE [--pairs "Rv Tu ..."]`; run it again on a family before setting
  it, since it reads the built fonts.)

## Kerning groups: who sets a key, who is measured, what follows (2026-11-15)

Decided on Fable for the entries of `docs/claude/open-for-fable.md` that
had no answer (phase 2's last three, Üb's "two conventions", "what else
to sweep" and "cross-script groups"). Read from kern_clear.py,
kern_groups.py and the four UFOs' groups and kerning; nothing in
sources/ changed, the tools named at the end do not exist.

**What a group claims.** A kerning group says: on this side these
letters are one shape. Its name-giving glyph is the model
(`italic_kerning.representative`); 53 of the Regular's groups are Latin,
and they are by side, not by base letter (o p ơ in b's right-side group,
d e o in c's left-side one, n in i's).

1. **A key's value comes from its model alone.** Whoever sets, computes
   or measures a pair of group keys does it on the two name-giving
   glyphs: a hand value, the italics' rule, kern_clear's families, the
   share in a test. No member's overhang, mark or horn moves the group's
   value.
2. **A member that needs more white gets an exception**, glyph against
   the other key, never the reverse: an exception only loosens. A member
   that would want it *tighter* than its group is not that shape (4).
3. **Which convention a new kern_clear family takes** follows from 1
   and 2, by one question: does the group's model show the feature the
   family measures?
   - Yes, and most members with it (a capital's top serif before an
     ascender, a capital before a marked lowercase): the entry is the
     group key, measured on the model; a member that needs more gets its
     exception from the group's new value (`clear()`'s `above` branch:
     the italics' Ĳ in J's group).
   - No: the feature is what single members add to the model (a mark, a
     horn, an overhang beside a sign), or the other side's group holds
     letters without it (d's left-side group holds c e o, so an
     ascender is entered as itself): glyph by glyph, added only where
     that glyph needs it, the group's pair untouched (`entries()`,
     `short_f_entries`).
   - A guarded letter is in no model and loosens no group: it has its
     exceptions (`guard`), and where a family's group value still leaves
     it touching, one more (`clear()`'s last loop).
   The three conventions the code has are these three cases; a fourth
   is not wanted. An entry in two families is measured by each in turn,
   the second from the first's value, as now.
4. **Alike is measured, not only listed.** A member's side distance from
   its model: its unkerned white beside the rhythm's letter (n for
   lowercase, H for capitals; `italic_kerning.white`) less the model's,
   over the rhythm. In the Regular 18 members of 10 groups lie more
   than 0.05 off: Ʌ Ɐ (as A and V, both sides), Ɓ, Ľ, Ɔ, Ʋ, ɞ, the
   middle dot in the colon's group, and W Ŵ Ẁ Ẃ Ẅ Ẉ Ẇ Ⱳ on the left side
   in V's group (0.06 nearer). Such a member's pairs are measured in
   their own right wherever the group's are (tests/test_latin_pairs.py:
   the group's pairs with the member in the model's place); within 0.05
   the model stands for it. A member the share then puts outside the
   references where its model is inside leaves the group on that side
   (as W left V's on the right, 2026-11-13) or keeps it with exceptions
   if they are few; that is a choice on a sheet.
   **When the measured set grows**, old faults appear as new. "Lists
   only shrink" holds between two widenings of a measure, not across
   one: the widening is a baseline change of its own commit, every new
   line entered with "measured since DATE" and the report's digest, and
   nothing else changed in that commit.
5. **An accented group follows its base group.** Two right-side groups
   exist for letters whose mark reaches left of the base (à's, with á â
   ..., beside a's; è's, with ò ô ć ..., beside c's). The invariant, in
   every style: for each left key, the accented group's pair is **never
   tighter than the base group's**; a mark draws no letter nearer. A
   change to the base pair is made to the accented pair by the same
   amount, then the invariant applied. Broken today, each for the next
   kerning sheet (set to the base's value):
   Regular and Bold v è, y è (-80 against -50, -83 against -52: v ò
   stands 30 units nearer than v o); Italic T à (-76 against -46), A è
   (-37, -33); Bold Italic T à (-79 against 0), T è (-65, -33), A è
   (-11, -9). The italics' are the rule's: it computes the accented
   key's pair on à and è, whose marks fill rows the base has not, and
   the base's value is not its floor. The floor belongs in
   `italic_kerning.compute` (shared machinery, one family of pairs:
   after the designer has seen T à beside T a).
6. **Setting pairs** (step 6 of "Setting a pair" above, as a tool): a
   round of changes is a table of (left glyph, right glyph, absolute
   value). Each is resolved to its keys; two lines on one key pair with
   different values refuse the whole round (W o, W e, W c on c's group:
   three increments had made -192 into +138); a line whose glyph is not
   its group's model is an exception and says so. Then 5 for the
   accented groups, and kern_clear after it as always. Increments are
   never applied to resolved values.
7. **Scripts.** A family that pairs letters of one script judges it on
   the glyphs, not on the key: Y's group holds Cyrillic Ү Ұ, so (Y's
   group, һ) exists as an entry; it is measured only on the members of
   һ's script, the model being the name-giver if it is of that script
   and the first member that is otherwise. Harmless as it stands (+2);
   the rule is for the next family.
8. **The sweep lists what kern_clear measures.** One table of families
   in kern_clear (name, the entries' function, the white kept, the
   measure: across, or every way above the x-height) read by `clear()`
   and by quality/collisions.py alike, so a pair found on a proof
   becomes a family once and is listed from then on. Letter pairs on a
   diagonal are then listed as the signs are. Families still to add are
   the eye's finds, not a search: after the italics' t (if the designer
   counts it an ascender: open), f's hook is the short f's.

**For Opus, to build:**

- `scripts/kern_set.py UFO TABLE` (6), on the Regular; the Bold and the
  italics follow by their generators.
- tests/test_kerning_groups.py: the invariant of 5 in every style, with
  today's nine (five pairs over the styles) in `tests/data/kern-accent-STYLE.txt` (lists that only
  shrink); no exception tighter than its group's value but those of
  hand tables, each with its date (2).
- test_latin_pairs: the members of 4 measured (the side distance from
  the UFO, cached), entered by the widening rule.
- kern_clear's table of families and collisions.py reading it (8).
- The floor of 5 in `italic_kerning.compute`, after the sheet.
