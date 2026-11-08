# Italic old-style figures optical weight proposal, 2026-10-25

After approval and integration of Ⱳ, continued to the remaining old-style
figure weight review. [Before/proposal proof](../proofs/italic-oldstyle-figures-weight-2026-10-25.pdf)
shows 3, 4, 5 and 9 beside n/o, the complete figure set, unchanged lining
figures and three text sizes. Production remains unchanged in this pass.

The trial uses the existing thick-stroke-only adjustment in the upright
frame, with negative amounts for these four figures. Hairlines are
excluded from deliberate reweighting. The glyphs are horizontally
recentered on their original ink centers; advances and all vertical ink
bounds remain exact. Metadata and anchors are retained. True extrema and
near-tangent finishing remove small construction findings after rounding.

| Figure | Weight adjustment | Measured stroke before → after | Ratio to lowercase reference before → after |
|---|---:|---:|---:|
| 3 | −64 | 244 → 205 | 1.42 → 1.19 |
| 4 | −50 | 226 → 177 | 1.35 → 1.06 |
| 5 | −81 | 261 → 188 | 1.52 → 1.09 |
| 9 | −56 | 237 → 182 | 1.38 → 1.06 |

These are current `strokes.py` measurements, rather than the older TODO
estimates. A stroke's lean, sampled position and curvature affect the
ratio; the amount removed is not necessarily the same as the change in
measured stroke. The 3 remains 19% above its reference. I recommend judging
this first reduction in the text specimens before further thinning it.
The goal is an even text colour, not an exact numerical ratio for every
figure.

All four rounded trial glyphs have no construction or glyph-lint findings.
The other figures and lining drawings are unchanged. This proposal
concerns weight alone: the current old-style forms' heights, descenders,
spacing and feature assignments are retained. No production generator,
master, exception or shaping-baseline change is made here, and user
acceptance is not yet recorded. Bold Italic is outside this first trial;
its inherited result needs review when the Italic drawing is selected.

Scratch source, trial UFO, SVG/PNG and measurements:
`build/italic-figures-review/`. Production integration still requires
rebuilding the figure/tabular family, reproduction, quality/shaping and
hinting checks, and final font builds.

## 9 distinguished from g

The review found the proposed 9 too similar to g. The inherited rounded
bowl and long curled ball-terminal descender make the resemblance clear
in a direct g/9 comparison. [Revised 9 proof](../proofs/italic-nine-open-tail-2026-10-25.pdf)
retains the lighter bowl and upper descender, replacing the lower curl
and ball with a shorter open sweep and cut terminal. This is a drawing
change in addition to the weight adjustment, intentionally changing the
lower ink bounds. Advance, anchors, metadata and the other figure trials
are retained. It has no construction or glyph-lint findings.

Scratch source and candidate: `build/italic-figures-review/nine.py`,
`Open-nine.ufo`. The revision remains for visual review, with production
unchanged. The original ball-terminal 9 is superseded as a proposal;
no figure drawing has yet been recorded as accepted.
