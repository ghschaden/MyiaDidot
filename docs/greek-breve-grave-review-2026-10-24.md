# Greek breve/grave stack review, 2026-10-24

[Before/after proof](../proofs/greek-breve-grave-before-after-2026-10-24.pdf).

The inherited `brevecmb_uni0313_gravecomb.grek` and
`brevecmb_uni0314_gravecomb.grek` stacks have fixed component offsets.
In Bold and Bold Italic, the grave's foot touches the breve's right tip,
leaving a short ledge. The component glyphs themselves have no lint
findings. Cleaning the merged outline would conceal a placement problem
and lose the independent components.

`scripts/make_bold.py` now raises each complete breathing/grave pair until
its lower ink bound clears the breve's upper bound by `STACK_GAP_LC`
(90 units, the existing lowercase mark-stacking setting). It measures the
final rounded outlines; measuring before rounding produced an unnecessary
extra unit in Bold Italic. This finishing step is enabled only by the Bold
generator, so the shared writer leaves Italic generation unchanged.

The pairs' y offsets change from 320 to 440 (smooth breathing) and 424
(rough breathing). Both bold styles retain the existing x offsets, the
breve placement, zero advances, attachment anchors and component outlines.
The resulting stack tops are 2004 and 1988, within the existing vertical
metrics. Regular and Italic are unchanged. These two legacy grave stacks
are the scope of this pass; other breve ligatures retain their placement.

Exactly two glyphs change per bold style. Font metadata, groups, kerning,
features and glyph order are unchanged. Four obsolete glyph-lint entries
are removed; no exception or shaping baseline is added. The regression
check restores the old touching placement, reruns the correction, verifies
the actual component clearance and lint, and checks idempotence.

`make reproduce` passes for Italic, Bold and Bold Italic. Diffenator against
HEAD reports exactly the two intended outlines per bold style, with no
changed words or tables outside the outlines. Before/after HarfBuzz shaping
of 2,119,788 strings per bold style has zero differences. Compiled cmap,
hmtx, GPOS, GSUB, GDEF, OS/2 and hhea tables are identical. The sync check,
Ruff and whitespace checks pass. `make proof` passes. The focused quality
and lint audit passes all eight style checks, all 16 composite checks pass,
and all four CFF hinting checks pass with helper-socket access allowed.

The full sandboxed run reports 151 passed, 3 skipped and four CFF failures
caused by its blocked helper socket. The separate CFF rerun passes all four,
giving **155 passed, 3 skipped** across the two runs. No other tests fail.
