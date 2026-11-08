# Italic small-cap bottom hinting review, 2026-10-26

[Production raster proof](../proofs/italic-smallcap-bottoms-hinting-review-2026-10-26.pdf)
compares r.sc, ɍ.sc and Cyrillic ж.sc/к.sc/я.sc in Italic and Bold Italic.
Each row starts with o, o.sc, h.sc and n.sc. Both pages show native-size
rasters and 3× nearest-neighbour enlargements at 24, 28 and 29–32 ppem,
under FreeType interpreters v35 and v40. Both final PNG pages were inspected,
including the rightmost glyphs; there is no clipping.

## Findings

All five target glyphs have an outline bottom of −23, matching lowercase
o. The small-cap controls differ: o.sc bottoms at −35, h.sc at 0 and n.sc
at −25. These are not interchangeable outline alignment coordinates.
The existing audit compares the targets with lowercase o at their shared
−23 coordinate; the proof also provides small caps as visual context.

| Styles | Interpreter | Affected sizes | Target bottom | Reference o bottom |
|---|---|---|---|---|
| Italic and Bold Italic | v35 | 29–32 ppem | −0.5 px | 0 px |
| Italic and Bold Italic | v40 | none in 8–32 ppem | no reported mismatch | — |

At 24 and 28 ppem there is no reported mismatch. At the affected sizes,
the curved feet/leg terminals retain a half-pixel descent while lowercase
o snaps to baseline. The visible feet remain continuous and consistent
with the surrounding small caps. This is the reverse phase of the earlier
G/Cyrillic round-bottom finding, where the target snapped to baseline and
the round reference extended below it.

Recommendation: retain the current hints and the existing ten exception
entries (five per weight). This review does not demonstrate a visual defect
requiring a correction, and does not propose an isolated-point delta.
The review approved retaining the current hints on 2026-10-26.

## Scope and validation

Reference revision: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with the
existing uncommitted pipeline changes present. The sources were not edited.
`make fonts/ttf/MyiaDidot-Italic.ttf fonts/ttf/MyiaDidot-BoldItalic.ttf`
confirmed both production targets current before inspection.

The full alignment audit covered 8–32 ppem in both interpreters and both
weights. Both regenerated italic TrueType hint-zone tests passed. Only
exception comments are clarified: keys and counts are unchanged. No outlines,
hint programs, generator code, shaping baselines or acceptance metadata change.

Reproduction script: `build/glyph-review/smallcap-bottoms/review.py`.
Full audit, outline bounds and production-font SHA-256 hashes:
`build/glyph-review/smallcap-bottoms/audit.json`.
Test log: `build/glyph-review/smallcap-bottoms/tests.log`.
Those build files are disposable; the PDF preserves the reviewed rasters.

Next unreviewed hinting group: Ʋ's top in both italic weights, then horn
findings. The earlier V/W small-cap tip trial and round-bottom reviews
retain their separate pending verdicts.
