# Italic Þ hinting and counter-zone audit, 2026-10-25

The person accepted this review and correction on 2026-10-25, after
clarifying that the red dashed line illustrates the mistaken counter
reference. A true outside alignment guide belongs on the outside edge.

[Diagnostic and small-size proof](../proofs/italic-thorn-hinting-review-2026-10-25.pdf)
shows the counter boundary, the unrelated reference glyph and TrueType
rendering before/after in both FreeType interpreters. The large raster
specimens are nearest-neighbour enlargements, with native-size copies below.

The pending Þ report was misleading. Its outer contour reaches 1434;
the second contour, its counter, reaches 1077. The latter happens to equal
o.sc's outer top. The checker treated this internal boundary as a small-cap
alignment edge. The old TODO's “7–11 px off” was also incorrect: 7 and 11
were counts of affected sizes, not distances. The measured differences
were about one pixel (up to 1.33 pixels in v35).

More seriously, `hint_control.py` consumed that false alignment finding and
generated `Thorn touch 42, 43 yshift -1 @ 27`, shifting the counter at
27 ppem. Removing that comparison removes the unwanted instruction.

`scripts/quality/hint_zones.py` now audits outer ink contours only.
It computes signed quadratic contour areas, establishes the outer winding
from the largest contour and excludes opposite-winding holes. Original
glyf point indices are preserved for valid hint-control targets. Disconnected
outer pieces remain eligible, and fully reversed glyphs are handled too.
CFF's existing whole-glyph measurement is unchanged.

Auditing the same four before-fonts with old/new code removes exactly:

| Style | Counter | v35 sizes | v40 sizes | Accidental reference |
|---|---|---:|---:|---|
| Italic | Þ top 1077 | 7 | 11 | o.sc outer top |
| Italic | æ.sc top 884 | 6 | 7 | x outer top |
| Regular | ϐ upper counter top 1462 | 5 | 19 | O outer top |

No other reports change and no findings are added. Six obsolete exception
entries are removed. The old Regular ϐ annotation also misidentified its
counter as a round outside top; the source contours confirm it is a hole.

All four TTFs and WOFF2s rebuild. Font comparison verifies every glyph's
coordinates, end points and flags remain exact; all advances, layout and
shared hint tables match. Only Italic Þ's glyph instructions change.
Regular, Bold and Bold Italic have no changed glyph programs. Across
8–32 ppem, Þ's raster changes only at 27 ppem, in both v35 and v40.
No UFO, OTF, shaping baseline or drawing change is required.

Validation: **6 checks pass**: two winding/index regression cases and all
four TrueType hint-zone checks. Ruff and whitespace checks pass. The
synthetic regression glyph has a hole followed by a disconnected outer
piece, testing both counter exclusion and retained point numbering in
either winding direction. The final proof PNG was visually inspected.

Before fonts, old/new audit counts, font/raster comparisons and proof
generation inputs are in `build/italic-thorn-review/` (`audit.py`,
`compare.py`, `proof.py`, `audit.json`, `comparison.json`, `tests.log`).
