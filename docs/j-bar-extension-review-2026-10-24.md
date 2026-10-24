# Bold Italic ɉ right bar extended, 2026-10-24

[Before/after proof](../proofs/bold-italic-j-bar-before-after-2026-10-24.pdf).

The person found the Bold Italic bar too short in the four-style review.
That correction supersedes the recommendation to retain this style's
bar in `j-bar-ledges-review-2026-10-24.md`. The Roman and light Italic
drawings are unchanged.

The bar now projects 80 units past the right stem edge at both its top
and bottom, 1.25 times its 64-unit thickness. Its terminal follows the
slant. Only two corners change: 553,471 becomes 652,474 and 537,413 becomes
632,410. The stem corners remain 572,474 and 552,410. The left arm, dot,
hook, descender and every other point are preserved, as are the advance,
anchors, metadata, kerning and layout sources.

`scripts/j_bar.py` applies this extension in the generated-style writer
after rounding. It derives the terminal from the two stem corners and
bar thickness, is idempotent and runs only on Bold Italic ɉ. The old
two-ledge lint exception is removed; the bar is now long enough to pass.

Extending the bar changes which sample rows the stroke checker accepts.
Previously it measured 243 units and classified the glyph as round
(0.91 of its reference); now it measures 241 and classifies it as straight
(0.88). The existing stem outline is unchanged. Added a documented
stroke exception for this measurement rather than changing the stem to
satisfy a sampling side effect. No shaping baselines change.

Validation: two regression tests, Bold Italic glyph lint and quality,
15 composite/UFO checks, and both TrueType/CFF hinting checks pass. CFF
ran with local helper-socket access. Full Bold Italic generation followed
by small caps matches the master. The compiled cmap, hmtx, GPOS, GSUB,
GDEF, OS/2 and hhea tables are byte-identical before and after. Ruff,
source sync and whitespace checks pass. The full suite was not run.

Working reports and proof source: `build/j-bar-review/`.
