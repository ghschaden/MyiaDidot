# Italic round-bottom hinting review, 2026-10-25

**Verdict 2026-10-26:** Current curves and hints accepted after visual review of the proof.

[Production raster proof](../proofs/italic-round-bottom-hinting-review-2026-10-25.pdf)
compares both italic weights in FreeType v35 and v40 at 24, 28 and
29–32 ppem. Each group begins with O; Latin/Cyrillic C and O provide
additional controls. Samples use 3× nearest-neighbour enlargement.
Both final PNG pages were inspected, including their rightmost glyphs.

The affected group is G, Ɠ, Ǥ and Є З Э Ю Ѳ Ѵ Ә Ө. All have outline
bottoms at −35, matching O. A full 8–32 ppem audit finds:

| Style | v35 sizes | Difference from O | v40 reports in this group |
|---|---|---|---|
| Italic G/Ɠ/Ǥ | 30–32 | +0.5 pixel | none |
| Italic Cyrillic group | 29–32 | +0.5 pixel | none |
| Bold Italic whole group | 29–32 | +0.5 pixel | none |

In each case the flagged letter's hinted bottom is exactly zero, while
O's is −0.5 pixel. C and Cyrillic О/С follow O. At 28 ppem all these
bottoms are zero in both interpreters; v40 keeps them at zero throughout
29–32 too. This is a half-pixel overshoot-phase difference at the largest
audited sizes, not the whole-row displacement described in older notes.
Raster coverage can consequently differ on the row below the baseline.

The current rasters retain continuous curves. Recommendation: keep the
existing hints and exceptions, pending the visual verdict on
this proof. There is no demonstrated curve-preserving correction here;
no trial or production adjustment is proposed. In particular, the
isolated-point ν trial does not provide a suitable recipe for these
round extremes. This review does not mark the current rendering accepted.

Only exception annotations are clarified. No counts, keys, generator
code, outlines, production fonts or shaping baselines change. The audit
covers all text sizes 8–32 in both interpreters, in both italic weights.
Both regenerated italic TrueType hint-zone checks pass, and
`git diff --check` passes. Its detailed findings are in `build/round-bottom-review/audit.json`;
`proof.py` in that directory regenerates the proof from production TTFs.

Next unreviewed hint group: r.sc, ɍ.sc and Cyrillic ж.sc/к.sc/я.sc
bottoms, followed separately by Ʋ's top and the horn findings. The
small-cap V/W tip trial remains awaiting its separate visual verdict.
