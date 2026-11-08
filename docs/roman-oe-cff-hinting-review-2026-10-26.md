# Roman Œ CFF hinting review, 2026-10-26

[Production raster proof](../proofs/roman-oe-cff-hinting-review-2026-10-26.pdf)
compares H O Œ E O in Regular and Bold at 12, 14, 15, 21, 22 and 32 ppem.
Each panel shows CFF production and a TrueType v40 control, at native size
and 4× nearest-neighbour enlargement. Both final PNG pages were inspected,
including the rightmost O; no glyphs are clipped.

## Findings and recommendation

The CFF audit covers all sizes 8–32 ppem. Both weights have identical
reported Œ deltas relative to O:

| Edge | Sizes | Difference from O |
|---|---|---|
| top at source y=1462 | 15–32 | +0.078125 to +0.171875 px |
| bottom at source y=−28 | 22–32 | −0.078125 to −0.09375 px |

These reproduce the existing eighteen top and eleven bottom reports per
weight. The earlier sizes fall within the audit's 1/16-pixel tolerance.
The displacement is a small fraction of a raster row, not a whole-row
alignment failure. The inspected bowl remains continuous and visually
compatible with O; Œ's stem and serifs remain compatible with E.

Recommendation: retain the current hints and four exception entries.
No correction trial or production change is proposed. Retention was approved on 2026-10-26.

The old explanation that only E's stems receive hints was incomplete.
Decompiled Œ charstrings contain horizontal hints for both the O-like bowl
and E-like body, plus changing hint masks; O and E themselves have simpler
hint programs. This review establishes the displacement and visual result,
but does not isolate a particular mask or instruction as its cause.
Exception comments now state the measured behavior without claiming that
Œ's bowl has no hints.

## Scope and validation

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes. Make confirmed both production OTF targets
current; TrueType controls were confirmed current in the preceding review.
No outlines, sources, hint programs, generator logic, layout or shaping
baselines change. Only exception annotations are clarified; keys/counts
remain unchanged.

The audit, production OTF SHA-256 hashes, decompiled charstrings and proof
script are under `build/glyph-review/oe-cff/` (`audit.json`, `charstrings.txt`,
`proof.py`). Those build files are disposable; the PDF preserves the
inspected rasters. The first regenerated CFF test run was blocked by the
sandbox's local helper-socket restriction; the rerun uses normal permission
escalation for otfautohint. Both regenerated roman CFF hint-zone tests
pass. Local links and `git diff --check` pass.

Next unreviewed CFF group: Fraktur 𝔖, then ƙ.sc, ъ and ẞ where still listed.
Earlier small-cap-tip and G/Cyrillic round-bottom verdicts remain separate.
