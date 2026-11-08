# Bold aleph serif review, 2026-10-25

The four Bold ℵ (`uni2135`) ledge findings exposed tilted serif ends,
including a backward undercut at the lower-right foot. The generator now
restores the four rectangular ends by moving four corners. The
[two-page proof](../proofs/bold-aleph-serif-before-after-2026-10-25.pdf)
shows all styles, the complete Bold before/after, and Regular/Bold details
for every flagged join plus the unflagged lower-left serif repair.

## Source construction and fault

Regular ℵ is the original straight-stroke drawing in
`scripts/draft_letterlike.py:alef`: a thick diagonal, an upper arm, a lower
leg and four rectangular serifs. The recipe's rounded outline, translated
20 units left, matches the current Regular outline exactly (zero symmetric
difference area). Its original 1420-unit advance became 1380 after spacing.

The former `LEDGE_KEEP` comment and Regular exception attributed this to
Libertinus Math. That is incorrect: `draft_letterlike.py` imports its
Fraktur from Libertinus Math; the roman aleph is drawn by the local recipe.
Corrected those comments. Italic ℵ has separate Old Standard provenance,
and its curved lower-tip/upper-join repairs from 2026-10-24 remain unchanged.

The Regular's short serif/diagonal lips are part of the drawing. But
weighting the combined outline tilted four formerly vertical serif ends
and their flat edges. The lower-right foot changed from an outward lip
at `(1010,64) → (1021,64)` into a backward undercut:
`(1027,0) → (1063,68) → (1033,71)`. Thus the existing exception did not
justify retaining every weighted join.

## Repair

`scripts/aleph.py:_roman_serifs`, called by the existing generated-style
writer after rounding/cleanup, restores each end from its unchanged
vertical and horizontal neighbours. It changes only these four corners:

| Serif end | Before | After |
| --- | --- | --- |
| Upper right, left end | 975,1285 | 944,1282 |
| Upper left, right end | 451,1363 | 462,1362 |
| Lower right, left end | 1063,68 | 1027,71 |
| Lower left, right end | 697,70 | 712,71 |

The fourth repair addresses the same unflagged deformation. Every other
node is retained, including the central diagonal, arm, leg and the cap
projecting below the upper-right serif. Overall bounds, advance and
anchors are unchanged. The pass checks neighbouring points and segment
types, accepts its already repaired result, and fails if the generator's
local construction changes unexpectedly.

The 11-unit and 25-unit findings disappear because the restored flat
serif projections are now longer than the detector's 32-unit limit.
The former reversed 30-unit join becomes the source-style outward 6-unit
lip. The 21-unit upper-arm cap is unchanged. Reduce the Bold exception
from four ledges to two, with refreshed comments; the Regular's three
source lips remain. This is a demonstrated generator repair and retention
recommendation for the remaining lips, not recorded final visual acceptance.

## Validation

The regression reloads the old Bold glyph, verifies the four original
findings, then checks that exactly four corners change to square ends,
the lower-right foot projects outward, metadata is preserved and a second
pass is identical. Existing Bold Italic repair regressions still apply.

**26 focused checks pass**: four aleph regressions; Bold lint, quality,
UFO, composite and TrueType hinting checks; three shaping regressions;
and CFF hinting. The production Bold OTF compiles, receives its PostScript
hints and STAT table. The hinter and CFF test required local helper-socket
access after their sandboxed runs were blocked; both completed successfully
with that access.

The whole Bold was regenerated, its small caps rebuilt, and all masters
normalized. Master comparison finds exactly one outline changed:
`uni2135`. Every advance and anchor matches. Independent OTF compilation
finds only its CFF charstring changed; `hmtx`, `GPOS`, `GSUB`, `GDEF`,
`cmap`, `OS/2` and `hhea` are byte-identical. No shaping baselines or
quality exceptions changed. Ruff, source sync and whitespace checks pass.
`make reproduce` passes for all three generated styles: Italic, Bold and
Bold Italic.

Working proof, snapshot and comparison logs are in
`build/bold-aleph-review/`.

Next review: Regular acute counters in M/Mu and their Cyrillic/accented
relatives, trademark and №. Existing design annotations do not record
the final acceptance. Bold ˀ curve/weight and spacing, dollar
drawing, and ɸ optical weight remain open separately.
