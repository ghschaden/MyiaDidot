# Bold Italic h and o: whole-arc fitting — 2026-10-27

The scratch candidates improve two focused areas without changing production
sources: the inner crown of **h**, and the counter of **o**. Both pass the new
local geometry gates. They remain unaccepted drawing proposals; this is not a
claim that all Bold Italic curves, or even the whole h, have been repaired.

[Open the proofs](../build/glyph-review/bolditalic-fair-curves/index.html) and
[full report](../build/glyph-review/bolditalic-fair-curves/report.json).
The reference is the production source state at `96921b8a`. The report records
all four source byte hashes, implementation hashes and the toolchain identity.

## What changed

**h:** Replace the two cubic segments between the rising inner stem and the
inner crown with one fitted chain of six cubics. The recipe identifies this arc
by its line-to-curve construction and crown height, and refuses ambiguous or
changed topology. It preserves both endpoints exactly. Boundary directions and
curvature come from the retained neighbouring spans, so the transition joins
have G2 continuity. Internal joins have C2 continuity. The rest of h, including
its outer shoulder and lower return, stays unchanged.

**o:** Keep the entire outside contour and fit only the counter. Split at its
four native extrema and fit six cubics per quadrant. The extrema stay fixed;
adjoining quadrants share an endpoint curvature derived from the two original
sides. A bend-sign constraint removes the counter's two inflections. The final
control polygons certify consistent bend sign, and positive projections of
all derivative controls exclude stationary points within each new segment.
These are checked properties of the output, not assumptions about optimiser
convergence. Internal joins are C2; quadrant joins are G2.

The solver fits samples of the current Bold Italic drawing, with a penalty on
third derivatives in an approximate arc-length parameter. That penalty is a
fairness proxy, not exact curvature minimisation or a guarantee of a global
optimum. Endpoint equalities use a null-space solve; the counter's nonlinear
bend constraints use a deterministic iterative penalty method. Independent
geometry gates must pass before a candidate is described as checked.

The extra segments are experimental construction geometry, not a recommended
production point count. A future generator should reduce unnecessary points
and validate the finished integer outlines again.

## Measured tradeoffs

| Measurement | h | o |
|---|---:|---:|
| Changed whole-glyph ink | 0.142% | 1.235% |
| Total ink area change | −0.006% | −0.453% |
| Interior inflections in the replaced geometry | 2 → 1 | 2 → 0 |
| Largest absolute change in sampled normal stroke sections | 6.98% | 8.88% |
| Whole-glyph bounds drift | 0 | 0 |
| Unchanged outside spans | Exact | Exact |
| Sampled counter-clearance gate | Pass | Pass |

h retains one reversal within its fitted arc. The remaining bend is explicitly
reported and still needs optical judgement; it is not silently classified as
intentional. The repair controls curvature continuity without claiming the
entire inner shoulder is convex. Its inner arc's rightmost extent moves by
about 9.38 units within the declared blend region, while the crown, attachments,
whole-glyph bounds and advance remain fixed.

For o, both native counter extrema and outer bounds remain fixed. Preserving
those extrema alone would not establish weight preservation: the normal-section
measurements are essential. Both candidates satisfy a 10% local section-change
budget and the existing sampled counter-clearance budget. These are explicit
experimental guard limits, not typographic acceptance thresholds.

Normal sections follow fixed normals to the original edges, sampled at three
positions per original segment. They report changed intervals and refuse
ambiguous correspondence. The three unresolved h samples belong to an existing
zero-length line outside the edited area; the candidate preserves it. No new
correspondence failure is ignored. These samples do not prove continuous stroke
thickness or minimum clearance everywhere.

Ink area uses polygonal approximations with 64 and 128 subdivisions per segment;
the results must agree within 0.01 percentage points. The changed counter or arc
is compared separately, cancelling unchanged spans before Boolean operations.
This avoids failures involving thousands of coincident edges. Outside protection
is established by curve-span identity and the bounded construction, not by a
rounded area result. These area figures are approximate, not exact coordinate
round-trip claims.

## Why the smaller h repair

Whole-shoulder smoothing lowered the inner arch and changed thin strokes too
much, even when the whole-glyph ink difference was modest. Fixing crown points
helped, but fitting the broader region still introduced unwanted bends. Using
the Italic as a directly fitted donor also changed the Bold Italic's weight too
much. The final h recipe therefore works on the complete problematic inner
arc, retaining its same-style neighbouring geometry.

A four-cubic o counter could remove inflections, but balancing its join curvature
changed sampled strokes too much. The longer C2 chains supply the additional
freedom needed to retain weight and extrema while keeping the counter convex.
Exploratory proofs under the output directory are not the selected candidates;
the index links only the final run.

## Validation and production boundary

Run with the shared validation lock and one BLAS thread:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/shape_fairing.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  PYTEST_ADDOPTS='tests/test_shape_fairing.py tests/test_shape_curvature.py tests/test_shape_seams.py tests/test_shape_ports.py tests/test_shape_roundness.py tests/test_shape_consistency.py' \
  make test
```

All 43 focused tests pass through the shared lock; Ruff and whitespace checks
pass. New tests cover C2/G2 geometry, inconsistent and degenerate constraints,
cardinal splitting, an independently known area, the actual candidates' gates,
UFO-compatible coordinates, source preservation and refusal of unknown topology.

The preview verifies unrelated glyph/font data, widths, anchors, components and
features, reports component and recorded flattened dependants, checks scratch
UFO save/reopen, compares compiled shaping and runs affected outline lint.
The unchanged Italic is included as a reference rather than automatically
receiving the Bold Italic recipe.

No production source, generator, baseline, exception list or acceptance record
is changed. The scratch fonts contain fractional coordinates and reconstructed
point metadata. Flattened generator dependants are not rebuilt. Integration
still needs the authoritative generator stage, integer finishing, extrema and
hinting checks, and review of the rebuilt family. The remaining h lower return
is a separate fitting task.

The completed preview passes **73 compiled shaping comparisons** and introduces
**no new outline-lint findings** across the two direct changes and 33 component
dependants. No recorded acceptance is affected; no flattened dependants are
recorded in these source libraries. All four source byte hashes remain unchanged.
Area-resolution differences are below 0.00023 percentage points. Measured G2
curvature jumps are below 1.1e-13 inverse units.

Visually inspected both enlarged filled-ink comparisons, both curvature combs,
and the full Bold Italic before/after sheet with n/m/u peers, circumflex h,
dieresis o, anchors, text-size repeats and shaped words. o's counter is more
regular; h's inner transition is subtler, and its lower return remains visibly
untouched. No new spacing displacement was apparent in those words. This does
not establish improvement in hinted small-screen rendering. The separate
Italic reference sheet was generated but not individually inspected.
