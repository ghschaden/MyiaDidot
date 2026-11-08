# Bold Italic ɸ optical weight review, 2026-10-25

[Drawing comparison](../proofs/bold-italic-phi-weight-review-2026-10-25.pdf).

The current drawing has slit-like counters and looks congested beside o.
The earlier counter-tip review did not resolve this optical weight issue.
This proof compares four drawings at equal scale, including three text
sizes. These are scratch proposals; production outlines remain unchanged.

Rebuilding from the final Bold Italic o and a stem measured from l at
half x-height does not by itself open the counters sufficiently. Its
236.38-unit stem still produces two notch findings (69 and 89 pixels).
This confirms the earlier experiment using the current sources.

Two alternatives are shown:

- **Stem 20% lighter:** use the final o unchanged, with a 189.11-unit
  through-stem. This opens both counters and has no glyph-lint findings.
  The nominal advance remains 978, with the reconstructed bowl bounds
  unchanged. The through-stem is deliberately lighter than l: an optical
  adjustment for the extra ink where three heavy strokes meet.
- **Bowl 18% wider:** horizontally scale the final o about its ink center,
  retaining the full 236.38-unit l stem. This also has no glyph-lint
  findings, but increases the bowl's horizontal stroke weight as well as
  its width. Ink bounds extend from about -16 to 1008 within the unchanged
  978 advance. This is a drawing comparison, not a finished spacing fit;
  integration would require a wider advance or another spacing decision.

I recommend the lighter-stem trial for visual review. It opens the
counters without broadening the letter relative to neighbouring o's.
Neither alternative has recorded user acceptance. Clearing raster lint
alone does not establish the right drawing, and no quality exceptions or
shaping baselines have been changed.

Scratch source, UFOs, measurements and SVG/PNG rendering are in
`build/phi-weight-review/`; `proof.py` regenerates the comparison from
production sources. The scratch union curves are not production-finished
or rounded. Validation consists of glyph lint on each candidate and
inspection of the rendered proof. Production tests are not needed for
this proof-only pass. An adopted candidate still needs generator
integration, contour finishing, metadata/metrics comparison, reproduction,
quality/shaping and hinting checks, and production rebuilds.

## Requested refinement

The review selected the third option with a bowl 5% wider, retaining the
black stroke thickness and putting the extra width into the white middle.
[Refined comparison](../proofs/bold-italic-phi-wider-counters-2026-10-25.pdf)
shows that proposal against the previous third option.

In the upright construction frame, the bowl's outer and inner contours
both gain the same 42.37 units of horizontal width, centered on their own
existing ink centers. This avoids increasing the black ring's thickness
by 5% as a whole-outline scale would. Vertical coordinates and the
189.11-unit through-stem remain unchanged. Measured mid-height bowl black
is 268.81 → 268.93 units; top hairline is 54.773 → 54.770 units. Thus the
extra width goes essentially into the counters. The candidate has no
glyph-lint findings. The original advance remains in the comparison.

Scratch regeneration: `build/phi-weight-review/refine.py`; candidate:
`build/phi-weight-review/Lighter-stem-wider-white.ufo`. This revision is
prepared for visual review; production integration and checks remain.

## Inner-curve smoothing

The review identified bumps in the upper left and lower right inner
curves. Each affected return had an extra segment that flattened before
turning into the stem, creating an uneven curve. Each is now replaced
by one convex cubic, following the adjacent curve's direction and opening
toward its existing counter tip. The other counter segments, entire outer
contour, stem edges, 5% bowl widening and 978 advance are unchanged.

[Smoothed comparison](../proofs/bold-italic-phi-smooth-counters-2026-10-25.pdf)
shows the previous wider-bowl proposal on the left and smoothed drawing
on the right. Glyph lint remains clean; ink bounds match exactly. Each
counter loses three points. Scratch source: `build/phi-weight-review/smooth.py`;
candidate: `build/phi-weight-review/Smooth-inner-curves.ufo`.
This remains a review drawing awaiting production integration.

## Approved and integrated

The review approved the smoothed drawing and requested the next task.
`scripts/phi_drawing.py` now rebuilds it from final Bold Italic o/l in the
style writer. Outer and inner bowl widths expand equally; the two approved
convex inner returns are retained. Whole-unit rounding, true extrema and
near-tangent finishing leave no construction or lint findings.
[Production before/after](../proofs/bold-italic-phi-production-2026-10-25.pdf).

Only `uni0278` changes in the master. Complete Bold Italic generation and
small-cap rebuilding reproduce it exactly. Advances, anchors, Unicode,
glyph/font metadata, kerning and layout features remain unchanged. Removed
the two old construction exceptions and counter-notch exception. The
existing style warning is reannotated; one base-overlap exception records
the approved widened bowl (45% exact/covered overlap with unexpanded o).
The checker remains active; no shaping baselines change.

22 focused checks pass: repair regression (2), quality/lint (2), structural
and shaping checks (16), TrueType/CFF hinting (2). The CFF check and production
hinter require a local helper socket and pass with that access. OTF, TTF
and WOFF2 build; production OTF hinting and STAT metadata finish successfully.
Ruff and whitespace checks pass. Build and comparison logs are under
`build/phi-production/`. The next drawing proposal is Ⱳ's curl connection,
documented separately in `docs/w-curl-review-2026-10-25.md`.

Compiled comparison confirms only ɸ's CFF charstring changes. `GPOS`,
`GSUB`, `GDEF`, `cmap`, `OS/2` and `hhea` are byte-identical. The sole
`hmtx` difference is ɸ's left bearing 58 → 38 with its 978 advance retained,
as expected from the wider bowl.
