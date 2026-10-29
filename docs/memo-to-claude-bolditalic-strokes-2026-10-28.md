# Memo to Claude: pen-like Bold Italic strokes

Date: 2026-10-28  
From: Codex, shape-grammar worktree  
Subject: Design smooth strokes as coherent movements, with appearance taking priority

## User direction

The user wants Bold Italic to look smooth and naturally drawn with a pen, and
explicitly prefers good looks over rendering time. They asked for this memo.
This supports spending more computation on construction, optimisation and
validation. It does not constitute acceptance of any particular candidate.

## Recommendation

Continue from your stroke-based construction. Model and fit the stroke's
trajectory and thickness together, then refine both outline edges jointly.
Avoid relying on independent node offsets followed by local handle repairs.

A pen model is a useful design framework: a path, nib shape, nib angle and
pressure profile generate a coherent stroke envelope. Myia Didot still needs
optical corrections and deliberate contrast beyond a literal nib simulation.
The objective is a convincing drawing, not physical simulation for its own sake.

## What our comparison found

I compared committed main at `411eae10` with a byte-verified snapshot of your
uncommitted Bold Italic on 2026-10-28. That snapshot may already be older than
your current work. The report records its exact source and implementation-file
hashes; the implementation snapshot is provenance, not a reproduction claim.

Your new h/n/u construction improves the broad shapes and reduces within-segment
inflections. The new n downstroke looks more regular. However, curvature jumps
remain, and entry/exit strokes are appreciably lighter.

| Diagnostic | h | n | u | o |
|---|---:|---:|---:|---:|
| Interior inflections, committed → working | 6 → 3 | 10 → 5 | 8 → 6 | 2 → 2 |
| Resolved fixed-normal sections changing over 10% | 7/53 | 16/51 | 17/53 | 6/30 |
| Unresolved normal sections | 25 | 33 | 28 | 0 |

These are diagnostics, not defect counts or acceptance gates. Fixed reference
rays can conflate shifted stroke positions with thickness changes, especially
with the many unresolved correspondences in h/n/u. The visible terminal thinning
is real, but its desired amount remains an optical decision. No new outline-lint
findings appeared in the four glyphs and their component dependency closures.

Our earlier h/o scratch candidates are useful comparative evidence, not outlines
to transplant into your newer construction. They were built against older
sources. Our o counter became convex with continuous curvature at its fitted
joins, but required substantially more segments. Our h repair addressed only
its inner crown and retained one reversal. Neither candidate was accepted.

## Techniques to combine

### 1. Smooth the stroke trajectory and width profile

Represent major strokes explicitly. Let width evolve smoothly with distance
along each stroke, with separate controls for downstrokes, hairlines, turns,
entries and exits. Where useful, express that width through nib orientation and
pressure. Do not let incidental outline segmentation dictate local weight.

The two sides of a section should agree on the intended stroke thickness.
At junctions, model the meeting strokes separately before resolving the join,
then check excess ink and counter clearance.

### 2. Control curvature across complete arcs

Matching tangents gives G1 continuity, which removes a kink but permits an
abrupt change in how tightly the curve bends. Match curvature as well—G2—and
control its development between joins. A shoulder or return should tighten and
relax deliberately, without short alternating bulges.

Consider a fairness objective based on curvature variation with respect to arc
length, subject to shape, weight and clearance constraints. Our penalty on third
derivatives in approximate arc-length coordinates was only a proxy for this.
Matching endpoint curvature alone is insufficient: the interior can still wobble.

Do not force all arcs to be convex. Mark intended inflections and corners by
optical role, and preserve them. Conversely, a supposedly convex bowl segment
should have its bend sign checked over the whole segment, not only at samples.

### 3. Use suitable curve representations during construction

Euler spirals and Spiro-style splines are useful for gradual curvature changes,
particularly straight-to-curved transitions. They need not be the final font
representation. Allow stronger, deliberate curvature variation where the drawing
requires it; a universally stiff or uniformly gentle curve is not necessarily
an attractive one.

An expensive internal representation can be fitted to ordinary Bézier outlines
at export. Validate the approximation's shape, tangents, curvature behaviour and
local thickness, rather than accepting it solely on positional error.

### 4. Fit both boundaries together

An attractive outside edge does not guarantee an attractive counter. Couple the
inner and outer fits with constraints on thickness, contrast, counter clearance
and extrema. Include several positions around a turn, not only principal-axis
measurements or total ink area.

Whole-glyph ink difference can conceal a large relative change to a hairline.
Our early whole-shoulder fits demonstrated exactly that: modest total differences
accompanied unacceptable changes to thin strokes and the inner crown.

### 5. Let intermediate nodes move

Preserve meaningful landmarks: baseline, crown height, overshoot, stem placement
and attachment positions. Give intermediate points enough freedom to find a fair
curve. A misplaced node may force a dent regardless of handle lengths.

Use a modest number of segments where possible, but do not make node count the
primary objective. Simplification should preserve the drawing and its weight.
Your plan to retain the Italic's structural organisation is valuable; exact
retention of every derived node position should remain negotiable.

### 6. Design terminals and joins as optical constructions

Give the exit a deliberate taper, direction and ending shape. At a crotch or
junction, control the accumulated ink and the counter opening. These deserve
explicit local recipes or constraints rather than a generic smoothing pass.

The immediate unresolved choice is how much weight h/n/u entries and exits
should retain. Decide that visually before optimising their curves more strongly.
A smoother but unintended weight distribution would not satisfy the objective.

## Suggested next experiment

1. Pin a current source and generator snapshot. Work on h/n/u/o first, with
   the Italic and the previous Bold Italic beside it.
2. Make two or three explicit entry/exit weight variants. Keep the major stem
   weights and other design variables as stable as practical so the comparison
   answers the weight question.
3. On the preferred weight profile, fit paired boundaries over complete
   shoulders and returns. Preserve the essential landmarks; allow intermediate
   nodes to move. Constrain intended bend sign and curvature continuity.
4. Produce enlarged filled-ink and curvature-comb proofs, node views, and words
   at reading size. Look at h/n/u rhythm together and compare their colour with o.
5. Measure local stroke sections and counter clearance, with correspondence
   failures explicit. Check curvature inside segments and across every join,
   including contour closure. Keep lint and shaping checks as separate evidence.
6. Once the construction is convincing, extend to the broader lowercase sample
   and dependent glyphs, then validate integer finishing, extrema, hinting and
   the regenerated family through the authoritative production pipeline.

The user's appearance priority allows a slower construction process. Most of
that cost can be paid during font generation; it need not translate into slow
text rendering. Avoid excessive final point counts when they add no visible
benefit, but do not sacrifice the drawing to minimise computation.

## Evidence and references

Repository reports in the shape-grammar worktree:

- [Audit of your new stroke construction](main-stroke-audit-2026-10-28.md)
- [Comparison of committed main, working main and our scratch candidates](main-comparison-2026-10-28.md)
- [Earlier h/o whole-arc experiments](bolditalic-fair-curves.md)
- [Why tangent-preserving collars were insufficient](shape-curvature.md)

Generated proof index on this machine:
`/home/gerhard/src/MyiaDidot-shapes/build/glyph-review/main-stroke-audit/index.html`.
Generated evidence stays under build and is not a production acceptance record.

Primary technical references:

- Raph Levien, [From Spiral to Spline: Optimal Techniques in Interactive Curve Design](https://raph.levien.com/phd/phd.html):
  the theory and numerical methods behind Spiro, including font applications.
- Henry Moreton and Carlo Séquin, [Minimum Variation Curves and Surfaces for Computer-Aided Geometric Design](https://epubs.siam.org/doi/abs/10.1137/1.9781611971521.ch6):
  curvature variation as a fairness objective under interpolation constraints.
- Raph Levien, [A new spline](https://raphlinus.github.io/curves/2018/12/21/new-spline.html):
  why low curvature variation alone can be too restrictive, and the importance
  of explicit tangents and curvature blending.

This memo is a recommendation and evidence handoff. It does not merge our
experimental branch, approve a design, or change either worktree's font sources.
