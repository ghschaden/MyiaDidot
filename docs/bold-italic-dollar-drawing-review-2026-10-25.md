# Bold Italic dollar drawing proposal, 2026-10-25

After the review accepted the roman joins and trademark proposal, work
continued to the requested dollar drawing pass. The earlier straight-bar
repair had left a broad waist and swollen terminal entrances. The
[two-page proof](../proofs/bold-italic-dollar-drawing-before-after-2026-10-25.pdf)
shows the new drawing at display and text sizes, beside figures, and with
enlarged waist/terminal details. The review approved this dollar drawing on 2026-10-25, after the earlier
separate symbol-join/trademark acceptance.

`scripts/dollar_drawing.py` runs after the existing straight-bar correction
in the generated-style writer. The waist now follows two common parallel
diagonals, with vertical intercepts 1015 and 1217 at slope −0.6. Their
perpendicular separation is about 173 units, approximately 20% narrower
than the former 218-unit central band. Endpoint intersections are solved
against the four existing bar edge lines, then rounded on those lines.
This preserves their straightness rather than bending bars around the
narrower waist. Adjoining bowl handles follow the new diagonal tangents.

Both terminal entrances lose their extra short, backward neck curves.
Four continuous cubics form each compact ball and its approach to the
bowl. The ball protrusions are less broad; the characteristic ball-ended
dollar design remains. Bowl-side endpoints and their incoming/outgoing
tangents are retained. The rest of each bowl is kept.

The 15° bars retain their 86-unit widths and 95-unit clear gap, with all
sixteen exposed segments still lying within half a unit of the four
common lines. Whole-unit bounds, 1290-unit advance, anchors, metadata and
five-contour topology remain. Exactly six redundant contour points are
removed. The finishing helper is guarded and repeatable.

Validation: **30 focused checks pass**, including old bar repair tests,
new drawing regressions, prior symbol/aleph repairs, Bold Italic quality,
lint, UFO/composite checks and shaping goldens/full digest. Both **TrueType
and CFF hinting checks pass** (CFF with the required local helper socket).
No quality/lint exceptions or shaping baselines change.

Master comparison finds exactly `dollar: outline`. Only its CFF
charstring changes. Every advance and anchor matches, and compiled
`hmtx`, `GPOS`, `GSUB`, `GDEF`, `cmap`, `OS/2` and `hhea` tables are
byte-identical. The preceding accepted symbol repairs remain intact.
The prior straight-bar regression now compares against its retained
pre-drawing fixture, so it continues to check that independent repair.

Proof sources, snapshots and full validation/build logs:
`build/dollar-drawing-review/`.

A fresh complete Bold Italic generation and small-cap rebuild reproduce
the master. Ruff, source sync and whitespace checks pass.
Production OTF, TTF and WOFF2 builds complete successfully.
