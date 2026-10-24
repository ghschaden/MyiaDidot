# Italic ṫ dot placement review, 2026-10-24

[Before/after proof](../proofs/italic-t-dot-before-after-2026-10-24.pdf)
compares t, ṫ and ż in both italic weights.

The remaining Bold Italic ṫ step was an intersection artifact: its dot
merged into the flat top of t. Italic had the same collision without a
lint finding. Both inherited the Regular's Dotaccent anchor height even
though the italic t rises to 1374 rather than 1164.

`make_italic.t_dot_anchor` now derives t's Dotaccent height from z's
anchor and the difference between the two letters' ink tops, before
composites are built. The anchor moves along the italic slant, preserving
its horizontal alignment in the upright frame. Bold Italic inherits the
corrected anchor through its generator. The pass is idempotent.

The anchor moves 269 units up and 73 units right; the dot offset changes
from y=221 to y=490. The gap is 198 units in Italic and 194 in Bold Italic,
exactly matching ż in each weight. The standalone dot and base outlines
are unchanged. Regular and Bold are unchanged; their smaller ṫ gap remains
an independent visual-review item in TODO.md.

Seven glyph objects change per italic style: t, ţ, ț, ṫ, ṭ, ṯ and ṱ.
Only ṫ changes visible ink. The other six carry the corrected Dotaccent
anchor, including below-mark composites so they accept an additional dot
at the same height. No advances, kerning, groups, feature source, font
metadata or glyph order change. Compiled cmap, hmtx, GSUB, GDEF, OS/2 and
hhea tables match; GPOS changes only for the corrected anchors.

Before/after shaping covers 2,119,788 strings per italic weight. Exactly
ten strings differ per style, all dot positioning above t with a below
mark. Each moves the dot by (+73,+269); glyph selection and advances
are identical. The complete differences are in
`build/t-dot-review/shaping-{Italic,BoldItalic}.log`. Only the two full-corpus
digests are updated for these intended differences; golden cases remain
unchanged. The Bold Italic ṫ step exception is removed.

The regression tests compare dot clearance across t and z, check both
styles for lint, and exercise anchor repair, retention of other geometry
and anchors, and idempotence. The existing composite tests cover NFC/NFD
and anchor-based construction.

Validation: **161 passed, 3 skipped**, including TrueType and CFF hinting.
All three generated styles reproduce; `make proof`, Ruff, source sync and
whitespace checks pass. The sandboxed full run had 157 passes and four CFF
helper-socket failures; the final full run with socket access passed.

Diffenator against HEAD reports only ṫ plus the earlier uncommitted cedilla
and Greek-stack work: Cedilla and ṫ in Italic, those two plus the two
breve/grave stacks in Bold Italic. Its sole changed word per style is Ṫṫ,
as expected. No advance or unrelated layout changes appear. The default
visual reference was an older approval tag, so that first report was
superseded by the HEAD comparison. The sync client renamed the Italic
HTML report with a conflict suffix; its contents were copied to the task
review directory for the summary at `build/t-dot-review/diffenator-summary.txt`.
