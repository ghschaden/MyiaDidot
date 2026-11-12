# Spacing, kerning, figures

Moved from CLAUDE.md (its ground rules apply).

- Spacing: the Regular's letters were tightened once by `scripts/respace.py`
  (20 a side, Greek lowercase 10, of which 8 were given back after measuring
  Greek pairs; recorded in lib `org.myiadidot.respaced`, a second run
  refuses). Greek spacing and kerning are measured against Greek references
  (GFS Didot, EB Garamond, Libertinus, Charis), calibrated by each style's
  own Latin: `scripts/quality/greek_pairs.py STYLE`; the italics' Greek
  cuts are ITALIC_CUT_GREEK (make_italic.py) and BOLD_ITALIC_CUT_GREEK
  (make_bold.py), their Greek pairs in ITALIC_KERNING, BOLD_KERNING and
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
  `org.myiadidot.kernCleared`) and find their own. make_bold.py adds the Bold's own cut, make_italic.py
  undoes the Regular's in memory (it is tuned on the old spacing) and
  applies the Italic's; derive.py too builds on the uncut spacing and cuts
  again. It leaves kerning alone. The Bold's figures have a cut of their
  own (make_bold.py BOLD_FIGURE_CUT), then share their mean width
  (tabular_figures; the figure space and dash too). The Italic's letters are made at Old
  Standard's weight and their thick strokes made heavier at the end
  (make_italic.py WEIGHT, weight_thick):
  recipe widths are for the weight before that; derived letters that keep
  their whole base are then made of the weighted base (make_bold's
  follow_bases, as in the Bold). Emboldening (derive.embolden)
  keeps smooth nodes smooth and fits the handles; derive.rezone puts flat
  edges it moved back on the zones. Old-style figures are proportional
  (`scripts/space_figures.py`, run by make_bold.py/make_italic.py; tnum gives
  the .tf ones; it also makes the proportional lining .pf (pnum) and the
  lnum/pnum/tnum/zero block). Capital spacing (cpsp): `scripts/cpsp.py` on
  the Regular. Case-sensitive punctuation (case, `.case` glyphs):
  `scripts/case_forms.py`, run by make_bold.py/make_italic.py on what they
  make. Per-style spacing tweaks: make_bold.py BOLD_SIDEBEARINGS,
  make_italic.py ITALIC_SIDEBEARINGS and ITALIC_KERNING; one-off sidebearing
  changes with respace.sidebearings() (it carries composites along).

## The italics' Latin kerning (TODO.md F2 / phase 3)

State 2026-11-12: in the generators. make_italic.py and make_bold.py (the
Bold Italic, against the Bold) call `italic_kerning.apply` on the finished
outlines, just before kern_clear; the hand tables go over it. The measure,
rule and prototype: `scripts/italic_kerning.py`, tests/test_italic_kerning.py;
the values approved on `proofs/italic-kerning-2026-11-11.pdf`
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
report, 2026-11-12). Phase 1's sweep is what finds such pairs where no
group pair was ever kerned.

**Open.** The quantile and the depth are set by reasoning and by the
count above, not tuned. Pairs that do not face each other (’ before s)
are not measured; there are none among today's Latin pairs. Unkerned
upright pairs are never kerned by the rule, though the italic may need
them (phase 2 gives the Regular its missing pairs first).
