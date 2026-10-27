# Roundness in Bold and Bold Italic — 2026-10-27

Yes: the irregular curves can be reduced, but preserving tangent continuity
alone is insufficient. The current Bold Italic o has a lumpy, nearly straight
section in its counter; h also has uneven curvature through its shoulder and
return. These are visible in the enlarged proofs, even where tangent joins are
already smooth. A blanket node-smoothing operation would miss these problems
and could damage deliberate corners and thin/thick contrast.

[Open the comparative proofs](../build/glyph-review/shape-roundness/index.html)
or the focused [Bold Italic o experiment](../build/glyph-review/shape-roundness/BoldItalic-o-oval.svg).
The [report](../build/glyph-review/shape-roundness/report.json) records source
identities, construction parameters through the pinned script identities,
geometric diagnostics, ink changes, stroke samples and lint findings.

## Two different interventions

### Preserve curves during emboldening

The existing generator already has relevant controls:

- `embolden_by_weight(..., keep_bends=True)` suppresses some new inflections
  where the lighter source curve bent only one way.
- `embolden_simple(..., keep_smooth=True)` keeps handles attached to smooth
  nodes instead of moving each point independently.

In this worktree's `make_bold.py`, these protections are enabled for Bold
(with explicit exceptions) but disabled for Bold Italic. The comments say
the italic cases have not yet been reviewed. This is a concrete route to
investigate, not a recommendation to turn on every flag indiscriminately.

The study compares both flags off/on for 22 representative glyphs in each
style, independently for both construction methods: 88 paired experiments.
Inputs, weight and widening are identical within each pair. It does **not**
replay production route selection, zoning, bridges, repairs, optical spacing,
extrema, integer rounding or hinting. The finished current glyph is shown
separately so a construction-stage result cannot be mistaken for a finished
candidate.

| Bold Italic method | Inflecting cubics, off → on | Near-smooth curve joins with angular breaks, off → on |
|---|---:|---:|
| Weighted, `keep_bends` | 140 → 110 | 4 → 4 |
| Rounder fallback, `keep_smooth` | 100 → 145 | 124 → 3 |

These are diagnostic counts over the sample, not numbers of defective glyphs:
deliberate S-curves and corners can be valid. Inflections are sampled within
each cubic; joins are compared between adjacent cubic segments, with handles
at least five units long and angles between 2 and 45 degrees. These criteria
are not a comprehensive curvature-quality test.

The tradeoff is real. The rounder fallback loses most small tangent breaks but
introduces additional reversals in some shapes. In the h comparison it remains
visibly dented. The weighted protection removes one of h's detected inflections,
but does not remove its larger shape irregularities. Neither switch changes
the weighted o example. Bold already enables these protections, so its
remaining problems need more than repeating that change.

### Rebuild closed rounds from smoother source shapes

A separate experiment reconstructs o, O and zero in Bold and Bold Italic.
Each uses its own lighter counterpart: Regular for Bold, Italic for Bold
Italic. Capital, lowercase and figure shapes remain separate contexts.

The outer contour and counter are fitted independently to the current bold
contours' deskewed bounding boxes, then slanted back. Thus the current outer
dimensions and counter dimensions guide the weight, while the smoother
lighter outline supplies curve structure. This is a construction experiment,
not a post-processing filter. It refuses connected bowls and arbitrary glyphs.

| Style/glyph | Changed ink | Total ink area change | Native bounding-box drift |
|---|---:|---:|---:|
| Bold o | 6.21% | +6.62% | 0 units |
| Bold O | 5.28% | +5.58% | 0 units |
| Bold zero | 6.47% | +6.92% | 0 units |
| Bold Italic o | 5.97% | +2.74% | 5.93 units |
| Bold Italic O | 5.03% | +2.54% | 7.53 units |
| Bold Italic zero | 4.04% | +2.30% | 8.69 units |

The Bold Italic o counter becomes visibly more rounded and its two detected
within-cubic inflections disappear. Zero's four disappear as well. The
uppercase O already has no detected inflections: this metric alone cannot
decide whether rebuilding it is desirable.

These candidates are **not weight-neutral**. The added ink is distributed
between the principal stroke axes; preserving contour extrema does not
preserve every local thickness. The italic outlines also change their native
overhang despite equal deskewed bounds. The report therefore includes ten
horizontal/vertical stroke sections per glyph, area changes and native bounds.
Those changes require optical tuning before any production use. All six
isolated alternatives introduce no new findings in the current outline lint.

## What this implies for the grammar

Shared parts need curve-quality constraints in addition to the
[seam contracts](shape-seams.md):

1. Mark deliberate inflections and intentional corners explicitly.
2. Keep convex arcs convex unless the optical design requires otherwise.
3. Control curvature through an entire arc, not only the tangent at a seam.
4. Use separate outer/counter profiles, with weight checked at several
   positions around the curve rather than inferred from bounding boxes.
5. Keep optical context and contrast; use constrained fitting or deliberate
   redrawing where offsetting the lighter outline creates a flat spot.

The oval experiment is a promising first implementation of that approach.
Connected shoulders/returns still need source-guided or fair-curve fitting
inside the seam contract. The existing seam work provides fixed attachment
positions and directions, but does not yet constrain curvature between them.

## Reproduce and scope

```sh
flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/shape_roundness.py
PYTEST_ADDOPTS='tests/test_shape_roundness.py' make test
```

All generated proofs and isolated candidate outlines are under
`build/glyph-review/shape-roundness/`. No source UFO, production generator,
acceptance record or baseline changed. Four focused tests pass, covering known
ink areas, scope restrictions, source preservation and bounded measurements
for all six oval alternatives; Ruff passes.

Visually inspected: Bold Italic h under both stage methods, o under the
weighted method, phi under the rounder method, and rebuilt Bold o / Bold
Italic o, O and zero. Other generated sheets were not individually reviewed.
The study does not compile candidate fonts, test shaping, demonstrate hinting,
or validate a regenerated family. It supplies evidence and isolated geometry
for a subsequent optical-design and generator-integration review.
