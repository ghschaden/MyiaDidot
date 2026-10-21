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
  own (make_bold.py BOLD_FIGURE_CUT). The Italic's letters are made at Old
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
