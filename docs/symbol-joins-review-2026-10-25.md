# Roman upper-left joins and Bold Italic trademark, 2026-10-25

The person rejected the thin white slits in Regular №, M and Cyrillic м,
identified the low middle M tip, and requested improvement of the complete
upper-left joins. They also identified Bold Italic ™'s bulging T stem and
unequal outer M stroke angles, clarifying that only the leftmost and
rightmost strokes should be parallel; the middle diagonal need not change.

The [three-page before/after proof](../proofs/symbol-joins-before-after-2026-10-25.pdf)
shows the complete Regular forms and enlarged upper-left serif joins,
Bold Italic trademark details, and both roman weights against baseline
guides. This supersedes the earlier recommendation to retain the Regular
counter tips. The person accepted the proposal on 2026-10-25 ("proposal accepted").

## Upper-left joins and baseline tips

The old Regular contours inserted a short curve almost parallel to the
upright before returning horizontally to it. That produced the white
slits under the top serif. `scripts/symbol_joins.py` extends the existing
diagonal directly to its intersection with the existing upright instead.
This fills the slit and gives a direct, clean join rather than burying
the defect with a separate patch. Serif outer profiles and upright stem
edges are preserved. The same repair is applied to the identical reduced
M construction within Regular trademark.

M's two middle-tip points rise from −28 to 0, and Cyrillic м's from −26
to 0. Trademark's corresponding M tip rises from 586 to its own feet at
612. Bold inherits these source changes at its own weight. Greek Mu and
Cyrillic М alias M, and Ḿ/Ṃ retain it as a component, so they follow the
same source automatically. No alphabetic small-cap drawings change.

The master-edit script accepts its repaired result on a second run. Its
coordinate guards stop if the original construction changes. The Bold
generator's optical fit otherwise shifts № two units right and widens
its advance six units; the finishing hook restores its previous placement
and 2475-unit advance. No spacing changes are accepted for this ink repair.

## Bold Italic trademark

The T's upper brackets had large reversing control handles. Its left
handle ran 66 units beyond the stem endpoint and the right shoulder
reversed back into the stem. The writer's finishing hook fairs the two
short shoulder curves, preserving the straight stem, outer T bar and
lower foot. The excessive upper-stem swellings disappear.

For M, the outer edge of the left hairline and inner edge of the right
stem are brought to the font's 15.2° slope, with matching upper/lower
tangents. The four outer-stem edges measure 15.18–15.36°, within whole-unit
rounding of one common slope. The middle diagonal's endpoints and handles
are unchanged. The repair changes eight existing points; it is guarded
and repeatable, and preserves glyph bounds, advance and anchors.

## Validation

Eight Regular lint entries disappear (the four constructions and M's
aliases/composites). The Cyrillic м baseline-zone exception is removed
in Regular and Bold. Bold Italic trademark's kink exception disappears
and its extreme count shrinks from four to three; the remaining extrema
are inherited at the foot and outer terminals. No new quality or lint
exceptions and no shaping baseline changes are introduced by this pass.

The focused suite passes **95 checks, with one skip**, covering the two
new repairs, aleph integration, all-style lint/quality/UFO/composites,
derived letters, emboldening and shaping goldens/full corpus digests.
All **eight TrueType/CFF hinting checks pass**, with the CFF hinter's
required local helper-socket access. Final Bold shaping is also verified
after retaining №'s established spacing.

Master/compiled comparison confirms only four master outlines per roman
weight change: M, м, trademark and numero. With M's aliases and composites,
exactly eight CFF charstrings change per roman. Italic is identical;
Bold Italic changes only trademark. Every existing advance, anchor and
kerning pair matches. Compiled `hmtx`, `GPOS`, `GSUB`, `GDEF`, `cmap`,
`OS/2` and `hhea` tables match byte-for-byte in every style.

Working scripts, snapshots, proof sources, comparisons and validation logs:
`build/symbol-joins-review/`. No commit has been made.

All three generated styles reproduce: the full run verified Italic and
Bold Italic; a fresh complete Bold generation and small-cap rebuild verify
the final № placement. Production OTF/TTF/WOFF2 builds pass. Final Bold and
Bold Italic quality/lint/shaping reruns pass (12 checks). Ruff, source sync
and whitespace checks pass.
