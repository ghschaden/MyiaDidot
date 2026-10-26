# Italic ƙ.sc and ъ CFF hinting review, 2026-10-26

[Production raster proof](../proofs/italic-k-hook-hard-sign-cff-review-2026-10-26.pdf)
shows two pages: h.sc o.sc k.sc ƙ.sc h.sc, then x o ъ ь o. Each compares
CFF production with TrueType v40 at 8, 9, 10, 11, 12 and 16 ppem, at native
size and 6× nearest-neighbour enlargement. Both rendered pages were visually
inspected; the labels identify the separate groups and no glyphs are clipped.

## Findings and recommendation

| Glyph | Source top | Reference | Affected size | Hinted top | Reference top |
|---|---|---|---|---|---|
| ƙ.sc (`uni0199.sc`) | 1040 | h.sc | 10 ppem | 6.09375 px | 6 px |
| ъ (`uni044A`) | 884 | x | 8 ppem | 4.171875 px | 4 px |

These are the only reports for the two targets across 8–32 ppem. The
small-cap's top is less than one tenth of a pixel above h.sc; the hard
sign's flag is about one sixth of a pixel above x. The older hard-sign
annotation described 0.3 pixel and is corrected to the measured value.

In context, ƙ.sc retains its k construction and hook without a conspicuous
height jump. The tiny hard-sign flag remains continuous with its stem;
the bowl stays compatible with ь. Recommendation: retain current hints and
the two existing exception entries. No trial, outline repair or font hint
adjustment is proposed. The person approved retaining these hints on 2026-10-26.

## Scope and verification

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with the existing
uncommitted pipeline changes. Make confirmed the Italic OTF/TTF current.
The complete production Italic CFF audit at 8–32 ppem matches all four
current exception keys/counts, including unrelated 𝔖 and ẞ findings.
The production OTF hash matches the font audited in the preceding Fraktur
review, whose regenerated italic CFF checks passed with helper-socket access;
those regeneration tests were not rerun for these comment-only changes.

Only two exception comments are clarified. No sources, generator code,
font programs, metrics, layout or shaping baselines change. Full audit,
outline bounds, OTF hash, proof script and audit check result are in
`build/glyph-review/k-hook-hard-sign/` (`audit.json`, `proof.py`, `checks.txt`).
These files are disposable; the PDF preserves the inspected raster samples.

Next unreviewed CFF finding: ẞ in both italic weights. Earlier small-cap-tip
and G/Cyrillic round-bottom verdicts remain separate.
