# Horn hinting review, 2026-10-26

[Production raster proof](../proofs/horn-hinting-review-2026-10-26.pdf)
compares H, standalone Horn/horn, and O Ơ U Ư o ơ u ư in all four styles.
Samples at 9, 11, 12, 13, 14 and 20 ppem cover every size reported for
standalone horns. Each appears at native size and 3× nearest-neighbour
enlargement in v35/v40. All four PNG pages were inspected, including the
rightmost glyphs; the samples and upper horns are not clipped.

## Findings

The reported glyphs are unencoded Horn/horn construction shapes. They have
880-unit advances and source `base` categories (compiled GDEF class 1),
whereas horncomb/horncomb.cap are combining marks (GDEF class 3). In Regular
and Italic the construction glyphs' tails are at y=0, a local attachment
coordinate. That does not make them letters intended to align to H's baseline.
Bold and Bold Italic have slightly lower construction tails, at −5, and
therefore do not trigger the same y=0 zone comparison.

The audit's `letters()` fallback interprets an unencoded name as a sequence
of encoded letter names. `Horn` and `horn` pass because H/h, o, r and n are
letters. These findings are consequently misleading baseline comparisons.

| Style | Glyph | Interpreter | Sizes | Bottom relative to H at 0 px |
|---|---|---|---|---|
| Regular | Horn | v35 | 20 | +0.5 px |
| Regular | Horn | v40 | 9 / 14 / 20 | −0.578125 / +0.546875 / +0.5 px |
| Italic | Horn | v35 | 11 | +0.5 px |
| Italic | horn | v40 | 12 / 13 / 14 | +0.53125 / +0.53125 / +0.515625 px |

All 24 encoded characters whose Unicode names contain WITH HORN, including
all tone-accented Ơ/Ư/ơ/ư forms, have **zero alignment reports** over
8–32 ppem under both interpreters in all four styles. The visual proof
shows the four plain horn letters alongside their bases; the tone-accented
forms were audited numerically, not individually included in this proof.
Attached horns remain connected in the inspected samples.

Recommendation: retain current font hints. Do not move construction tails
to the baseline to satisfy this comparison. Retaining these hints was accepted on 2026-10-26. A separate development follow-up should refine the audit's letter
classification and verify that valid unencoded letters and ligatures remain
covered; merely relying on GDEF mark class would not exclude these shapes.

## Scope and verification

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes. Make confirmed all four TTF targets current.
All four regenerated TrueType hint-zone tests pass; local links and
`git diff --check` pass. Only the four exception comments are clarified; keys/counts remain exact.
No source glyphs, production font hints, generator logic, audit behavior or
shaping baselines change.

The script and full audit, including production TTF hashes, are in
`build/glyph-review/horns/review.py` and `build/glyph-review/horns/audit.json`.
These files are disposable; the preserved PDF retains the inspected rasters.

Next remaining hinting reviews: CFF Œ alignment in the roman weights,
followed by Fraktur 𝔖, ƙ.sc, ъ and ẞ where still listed. Previously prepared
small-cap-tip and G/Cyrillic round-bottom verdicts remain separate.

## Follow-up 2026-10-26: audit refined

`hint_zones.letters()` no longer reads an unencoded name letter by letter.
Unencoded glyphs count as letters when named after an encoded letter (as
before) or when GSUB makes them of letters (`idotaccent.sc`); marks stay out.
`Horn`, `horn`, `Hook`, `hook` and `caroncommaaccent` are no longer audited,
and their four exception lines are gone. Production hints are byte-identical
(glyf, fpgm, prep, cvt, gasp in all four styles). See FONTLOG.
