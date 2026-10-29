# Curvature at connected seams — 2026-10-27

The current G1 seam fitter can introduce curvature reversals and sharp curvature
changes even when its ink, bounds, clearance, lint and shaping checks pass.
The earlier small ink differences are therefore insufficient evidence for
production reuse. The fitting rule needs revision before integration.

This follow-up adds diagnostics to `scripts/shape_seams.py`, implemented in
`scripts/shape_curvature.py`. It does not change the fitting algorithm, production
UFOs, generators, acceptance records or baselines. Reference: clean production
inputs at `96921b8a`; the generated report records their byte hashes and the
modified implementation hashes.

[Open the comparative proofs](../build/glyph-review/shape-curvature/index.html).
The [full report](../build/glyph-review/shape-curvature/report.json) contains the
per-segment measurements, join measurements and existing validation results.

## Measurements

Curvature is signed `cross(B′, B″) / |B′|³`, in inverse font units, measured in
native coordinates after restoring slant. This matters because curvature is not
invariant under shear or independent axis scaling.

For each fitted arc the report includes:

- Original and fitted curvature at 33 parameter positions per segment.
- Interior sign-changing roots of `cross(B′, B″)`, solved analytically for
  cubics. Roots within 1e-9 of a segment endpoint are excluded to avoid
  classifying numerical endpoint residuals as interior reversals. Lines and
  quadratics cannot have regular interior inflections.
- Position gaps, tangent angles and signed curvature jumps at internal joins.
  A curvature jump at an intentional corner is not a smoothness defect; the
  tangent angle is retained to distinguish those cases.
- Changes in endpoint curvature relative to the target arc at each seam.
  These are changes to the inside edge, not absolute jumps against the outside
  curve. Existing outside spans are unchanged by the fitter.

Zero-speed evaluations are unresolved (`null`), not zero curvature. Sampling
cannot prove absence of stationary points or bound the maximum curvature.
Inflection counts exclude segment endpoints and do not count cross-join bend
reversals; they are not a whole-arc convexity proof or a perceptual score.

Curvature comb proofs use 17 samples per segment, a common signed display scale
of 1500 and a cap of ±40 font units. Subdivision changes sample density. Capped
combs expose local changes but cannot quantify peak values; use the report.
The original and candidate drawings have the same em scale.

Measurements describe the attempted fit. For `already-consistent` operations,
the scratch font and visual proof retain the original target, as before.

## Findings

Interior inflections in the fitted part, original → candidate:

| Style | h entry shoulder | I capital foot |
|---|---:|---:|
| Regular | 0 → 0 | 0 → 0 |
| Italic | 0 → 3 | 0 → 2 |
| Bold | 1 → 1 | 0 → 0 |
| Bold Italic | 2 → 6 | 0 → 2 |

Among internal joins whose tangent angle is below 0.01°, the largest absolute
curvature jump in Italic h rises from 0.01123 to 0.03789 inverse units; in Bold
Italic h, from 0.04405 to 0.08891. The foot collars are more extreme: Italic I
rises from 0.01038 to 8.21406, and Bold Italic I from 0.00926 to 21.82365.
These values are local endpoint measurements, not whole-glyph averages.

Visually inspected the Italic h, Bold Italic h and Bold Italic I comb proofs.
They show new local spikes at fitted transitions that were difficult to see in
the filled-ink overlays. The basic silhouettes remain very close. These are
unhinted source-outline diagnostics, not visual acceptance or evidence of a
specific defect at text size. The other five comb sheets were generated but
not individually inspected.

All eight fits still pass the existing geometric budgets; all 184 compiled
shaping comparisons pass and affected outline lint finds no new issues. All four
production UFO byte hashes are unchanged. The curvature findings deliberately
do not inherit the meaning of `geometry_gate_passed`: that existing flag covers
only its documented ink, bounds, clearance and lint checks.

## Reproduce and validate

```sh
flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/shape_seams.py \
  --out build/glyph-review/shape-curvature
PYTEST_ADDOPTS='tests/test_shape_curvature.py tests/test_shape_seams.py tests/test_shape_ports.py tests/test_shape_consistency.py' make test
```

All 31 focused tests pass through the shared lock; Ruff passes. Six new tests
cover a line and analytic parabola, scaling/reflection/subdivision invariance,
an analytic cubic inflection, G1 joins with different curvature, subdivision
continuity and unresolved stationary endpoints. No full release suite or
hinted rendering was run; candidate geometry and production inputs are unchanged.

The next construction experiment should replace the short independently moved
collars with curvature-constrained transitions. Preserve the existing seam
positions and directions, explicitly control bend sign and endpoint curvature,
and retain the ink/clearance budgets. Matching curvature only at the endpoints
would still not guarantee a fair interior curve. Deliberate inflections need
explicit optical roles before these diagnostics can become acceptance gates.

The [Bold Italic h/o follow-up](bolditalic-fair-curves.md) now implements
whole-arc candidates with curvature-continuous joins and local thickness gates.
It replaces the problematic h inner crown arc and o counter in scratch fonts;
it does not enable the earlier donor-collar fitter or change production sources.
