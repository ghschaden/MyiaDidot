# Italic ẞ CFF hinting review, 2026-10-26

[Production raster proof](../proofs/italic-capital-sharp-s-cff-review-2026-10-26.pdf)
compares H O S ẞ ß O in Italic and Bold Italic at 10, 12, 13, 16, 24 and
32 ppem. Each panel shows CFF production and a TrueType v40 control at
native size and 3× nearest-neighbour enlargement. Both final PNG pages were
inspected, including the rightmost O and lowercase ß's descender; no glyphs
are clipped.

## Findings and recommendation

The complete CFF audits cover 8–32 ppem. Both weights give identical
capital sharp-s top deltas relative to O. Their outline tops both equal
1473, so this is a small hinting displacement at a shared source height.

| Sizes | Top above O |
|---|---|
| 13–14 | 0.078125 px |
| 15–17 | 0.09375 px |
| 18–19 | 0.109375 px |
| 20–22 | 0.125 px |
| 23–24 | 0.140625 px |
| 25–27 | 0.15625 px |
| 28–29 | 0.171875 px |
| 30–31 | 0.1875 px |
| 32 | 0.203125 px |

No ẞ alignment reports occur at 8–12 ppem or on its bottom in this range.
The inspected curved top stays continuous and compatible with S/O; the
small excess does not produce a conspicuous height jump. Recommendation:
retain the current hints and two exception entries. No trial, outline repair
or hint-program change is proposed. The person approved retaining these hints on 2026-10-26.
This concerns hinting only; it does not change drawing/draft metadata.

## Scope and verification

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes. Make confirmed both italic OTFs and TTFs
current. Complete production CFF audits in both weights match every current
exception key/count. OTF hashes match the preceding Fraktur review, whose
regenerated italic CFF tests passed with helper-socket access. Those tests
were not rerun for these comment-only changes.

Only the two ẞ exception annotations change; keys/counts are preserved.
No source outlines, font programs, generators, metrics, layout, shaping
baselines or glyph acceptance metadata change. Full audit, outline bounds,
production OTF hashes and proof script are in
`build/glyph-review/capital-sharp-s/` (`audit.json`, `proof.py`). These files
are disposable; the PDF preserves the inspected rasters.

This completes initial review of the listed CFF findings. Next unreviewed
TrueType entry: Regular prosgegrammeni (U+1FBE). The prepared small-cap-tip
trial and G/Cyrillic round-bottom review still await separate verdicts.
