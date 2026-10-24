# Cedilla attachment review, 2026-10-24

[Before/after proof](../proofs/cedilla-attachments-before-after-2026-10-24.pdf)
shows complete letters alongside enlarged attachment details.

Glyph lint found short steps inside the counters of Bold Ç, Ş and ç.sc,
and Italic Ç and ç.sc. The shared capital cedilla's top corner protruded
past the inner edge of the bottom stroke. The standalone mark had no lint
finding: the defect appeared only when its ink was merged with the base.

`scripts/cedilla.py` shortens only the buried tip of `Cedilla` after
rounding in the generated-style writer. Capital cedillas attach at y=122;
the Italic C's inner edge begins at y=30. The tip is now limited to y=29
when attached (y=−93 in the standalone mark), one unit inside that edge.
Only points above the attachment baseline (y=−122 in the mark) can move.
The slanted styles retain the tip's upright x position to whole-unit
precision. The mark's lower body, attachment anchors, advance and metadata
are preserved. Its existing aliases and composites follow the shared mark;
there is no per-composite outline patch or placement override.

The Italic tip is shortened by one unit; the Bold tip by six units.
Bold Italic follows the revised Italic source and receives the same final
tip limit. Weighting that revised source also moves two adjacent neck
handles horizontally by one unit; the lower curl is unchanged. Regular is
unchanged. The final pass is idempotent.

Exactly one master glyph (`Cedilla`) changes per generated style. After
decomposition, ten glyphs per style follow it: `Cedilla`, `uni0327.cap`,
`Ccedilla`, `Scedilla`, `Tcommaaccent`, `uni0228`, `ccedilla.sc`,
`scedilla.sc`, `tcommaaccent.sc` and `uni0229.sc`. All other outlines and
all advances, anchors, font metadata, kerning, groups, features and glyph
order are preserved. Five obsolete glyph-lint exceptions are removed;
no quality exceptions or shaping baselines are added.

Before/after shaping over 2,119,788 strings per generated style has zero
differences. Compiled cmap, hmtx, GPOS, GSUB, GDEF, OS/2 and hhea tables
are identical. All three focused attachment tests pass, including local
repair of an overlong tip, retention of the visible body, and idempotence.

The full suite passes: **158 passed, 3 skipped**, including TrueType and
CFF hinting. `make proof`, sync, Ruff and whitespace checks pass. The full
suite runs with local-socket access for its parallel workers and CFF hinter.

`make reproduce` passes for all three generated styles. Diffenator's
word-list sweep against HEAD reports only `Cedilla` in Italic and
`Cedilla` plus the earlier two Greek stack repairs in each bold style.
There are no changed words, advances or layout rules. The first comparison
attempt encountered a missing cached Italic reference; rebuilding that
reference from the unchanged pre-pass Italic resolved it.
