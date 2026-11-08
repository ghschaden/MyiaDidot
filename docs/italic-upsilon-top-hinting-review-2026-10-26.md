# Italic Ʋ top hinting review, 2026-10-26

[Production raster proof](../proofs/italic-upsilon-top-hinting-review-2026-10-26.pdf)
compares H O U Ʋ U H in Italic and Bold Italic at 8, 9, 10, 12, 16 and
24 ppem in FreeType v35/v40. Each sample appears at native size and 4×
nearest-neighbour enlargement. Both final PNG pages were inspected,
including the rightmost controls, with no clipping.

## Findings and recommendation

Ʋ and U have the same outline bounds vertically: −35 to 1434. H tops at
1434 too. At 8 and 9 ppem the original top on-curve points of Ʋ align
exactly with H at 6 pixels, but hinting raises another part of its curved
hook above them. The audit correctly measures the whole outer contour,
not just the originally highest points.

| Style | Interpreter | Sizes | Highest hinted point | H top |
|---|---|---|---|---|
| Italic | v35 | 8, 9 | 6.59375 px | 6 px |
| Bold Italic | v35 | 8, 9 | 6.609375 px | 6 px |
| Both | v40 | 8, 9 | 7 px | 6 px |

There are no Ʋ alignment reports at 10–32 ppem in either interpreter or
weight. The proof shows a faint raised hook pixel at the smallest sizes;
the hook remains continuous. At larger control sizes it retains its curved
terminal beside U's flat serif without a reported alignment mismatch.

Recommendation: retain the current hints and four exception entries.
The small-size displacement is real, but this inspection does not establish
that flattening or shifting the hook would improve its readability. Moving
only the original highest points would target points already aligned to H.
No correction trial is proposed or integrated. Retaining these hints was approved on 2026-10-26.

## Scope and checks

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes present. Make confirmed both production TTFs
current before inspection. Full alignment audits covered 8–32 ppem in
v35/v40, both weights. Exception comments now identify the actual sizes
and the curved hook's displacement; keys/counts remain unchanged.

No sources, generator logic, production hint programs, metrics, layout or
shaping baselines change. Reproduction inputs and full audit with font
SHA-256 hashes are in `build/glyph-review/upsilon-top/review.py` and
`build/glyph-review/upsilon-top/audit.json`. These build files are disposable;
the preserved PDF contains the reviewed rasters.

Next unreviewed hinting group: horn findings. Earlier small-cap tip and
G/Cyrillic round-bottom verdicts remain separate. The small-cap r.sc and
Cyrillic bottom hints were approved on 2026-10-26.
