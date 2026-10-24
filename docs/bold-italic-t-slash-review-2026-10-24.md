# Bold Italic Ⱦ foot counter repair, 2026-10-24

[Before/after proof](../proofs/bold-italic-t-slash-before-after-2026-10-24.pdf)
shows the complete glyph and the lower serif at a larger scale.

The slash and foot serif enclosed a residual counter of 402 square font
units, bounded by x=427–464 and y=75–135. Its narrow tip rasterized as a
notch: the current glyph-lint checker reported 446,100, 44 pixels. The
historical exception recorded an earlier measurement of 460,126, 36 pixels.
This is an enclosed counter, unlike dollar's open terminal channel.

The repair removes only this small counter. All points in the outer
outline and upper counter are unchanged. The upper counter remains open
within the glyph; the tiny white slit above the lower serif disappears.

`scripts/t_slash.py` runs in the generated-style writer after rounding
and general cleanup. It targets only Bold Italic `uni023E`, removing
oppositely wound contours of at most 600 square units wholly between
y=0 and y=160. These limits isolate the residual foot counter from the
upper counter and the outer outline. Other styles are unchanged.

The obsolete glyph-lint exception is removed. The smooth-break count for
Ⱦ drops from two to one because one flagged point belonged to the removed
counter; its known quality entry is tightened accordingly. No exceptions
are added and no shaping baselines change. Master comparison confirms that exactly one
outline changes; all advances, anchors, metadata, kerning, groups,
features and glyph order match the pre-repair master. Compiled cmap,
hmtx, GPOS, GSUB, GDEF, OS/2 and hhea tables are byte-identical.

Regression tests reintroduce the original counter and verify its exact
402-unit ink difference, preservation of the complete remaining glyph,
absence of lint findings, idempotence and no changes to other styles.

Working reports and proof source: `build/t-slash-review/`.

Validation: the two repair tests, four glyph-lint checks and four quality
checks pass (the Bold Italic quality check was rerun after tightening the
count). All 68 composite, recipe, derived-letter and UFO structural checks
pass. Both Bold Italic TrueType and CFF hint-zone checks pass; CFF required
a rerun with local helper-socket access after the sandbox blocked it.
Ruff, source sync and whitespace checks pass. The full suite was not run.

All three styles reproduce. The initial `make reproduce` completed the
generators but failed during comparison because the sync client renamed
six scratch Bold glyph files with `[conflicted]`. A copy of the generated
trees in `/tmp`, with those missing files restored from their renamed
copies after checking their glyph names, compares with zero differences
for Italic, Bold and Bold Italic. No source files needed restoration.
