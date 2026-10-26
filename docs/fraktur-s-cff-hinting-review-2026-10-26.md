# Fraktur 𝔖 CFF hinting review, 2026-10-26

[Production raster proof](../proofs/fraktur-s-cff-hinting-review-2026-10-26.pdf)
compares O S 𝔐 𝔓 𝔖 O in Italic and Bold Italic at 8, 9, 10, 11, 12 and
16 ppem. It shows CFF production and a TrueType v40 control at native size
and 6× nearest-neighbour enlargement. Both final PNG pages were inspected,
including the rightmost O; the samples and Fraktur descenders are not clipped.

## Findings and recommendation

Full CFF audits cover 8–32 ppem in all four styles. Only the italic
weights report 𝔖 alignment differences:

| Style | Size | 𝔖 top | O top | Difference |
|---|---|---|---|---|
| Italic | 10 | 7.1875 px | 7 px | +0.1875 px |
| Italic | 11 | 8.3125 px | 8 px | +0.3125 px |
| Bold Italic | 9 | 7.09375 px | 7 px | +0.09375 px |
| Bold Italic | 10 | 7.203125 px | 7 px | +0.203125 px |
| Bold Italic | 11 | 8.3125 px | 8 px | +0.3125 px |

The italic 𝔐/𝔓/𝔖 outlines top at 1473, matching O's outline overshoot.
The flagged 𝔖 height is therefore a real small raster displacement, not
merely a comparison between different source heights. Regular/Bold 𝔖 top
near 1456, below O's 1462, so the audit does not compare their tops to O's
zone. Their absence from the report does not establish exact alignment.

The inspected 𝔖 terminal remains continuous and recognizably part of its
Fraktur construction beside 𝔐/𝔓. These very small sizes simplify its detail,
but the small raised top does not establish a repair need. Recommendation:
retain current hints and the two existing exception entries. No delta trial,
outline modification or hint-program change is proposed. The person approved retaining these hints on 2026-10-26.

The imported Libertinus Math outlines were adapted to the family's height
and weight; their distinct Fraktur construction is intentional. This review
concerns their CFF top alignment, not a redesign or renewed acceptance of
all Fraktur drawings.

## Scope and verification

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes. Make confirmed all four production OTFs
current; the TTF controls were confirmed current in preceding reviews.
Both regenerated italic CFF hint-zone tests pass with local helper-socket
access. Local links and `git diff --check` pass. Only two exception annotations
are clarified, with keys/counts preserved.
No sources, font programs, metrics, layout, generators or shaping baselines
change.

Full audit, exact outline bounds, production OTF hashes, decompiled hint
programs and the proof script are in `build/glyph-review/fraktur-s/`
(`audit.json`, `charstrings.txt`, `proof.py`). These files are disposable;
the preserved PDF contains the inspected rasters.

Next unreviewed CFF findings: Italic ƙ.sc and ъ, followed by italic ẞ in
both weights. Earlier small-cap-tip and G/Cyrillic round-bottom verdicts
remain separate.
