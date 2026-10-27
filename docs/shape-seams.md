# Connected parts: seam design and fitting rules

`scripts/shape_seams.py` implements two connected-part recipes in Regular,
Italic, Bold and Bold Italic. They are source-protected experiments, not enabled
production rules. All generated artifacts stay under `build/`.

| Context | Donor → target | Seams | Fitting frame |
|---|---|---|---|
| Lowercase entry shoulder | n → h | Entry curve and exit stem | Deskewed |
| Capital foot serif | H → I | Stem above foot | Native |

These extend the [attachment vocabulary](shape-ports.md) with actual curve
fitting, scratch fonts and before/after proofs. The donors are the final
drawings in the **same style**. Production sources and generators are read-only.

## Seam contracts

For the shoulder, measure the two stems at half x-height in deskewed
coordinates. Put a vertical entry cut 15% of the counter width to the right
of the entry stem's inner edge, and a horizontal exit cut at 55% of x-height.
Extend the other crop edges beyond the exit stem and shoulder crown. Require
exactly one complete ink interval on each of the left and bottom cuts and
none on the other two sides. This avoids the previous crop's corner inside
the exit stem.

For the foot, cut horizontally at 8.5% of cap height. Extend the other edges
outside the foot, stopping before H's second stem. Require exactly one complete
ink interval on the top cut and none elsewhere.

These fractions are explicit experimental parameters, not universal typographic
constants. A source change that invalidates the declared attachment inventory
stops the fit. Vertex contacts, tangencies, coincident edges and ambiguous
correspondences are refused; no nearest-match fallback is allowed.

The shoulder has two outline arcs between its ports: outside and counter
edges. The foot has one arc returning to the same port. Correspondence uses
the ordered pair of attachment sides and contour direction. More complex
shapes sharing that key need named edge roles and are currently refused.

## Fitting rule

1. Split the original Bézier segments at the seams using de Casteljau
   subdivision. Retain every outside curve span.
2. Map the donor part's ink bounding box to the target part's box in the
   recipe's fitting frame.
3. Subdivide transition collars from the start and end of each mapped donor
   arc. The policy uses a 0.25 segment-parameter fraction, not arc length.
   When both collars lie on one segment, the second subdivision acts on the
   remainder.
4. Move each collar's seam endpoint to the original target endpoint. Align its
   adjacent handle with the target's original edge direction while retaining
   the mapped handle length. Keep the collar's interior endpoint and adjacent
   handle fixed, along with the donor core between collars.
5. Splice the fitted arcs into the untouched outside spans and restore native
   coordinates where necessary.

This enforces position and **G1 tangent continuity** at the seams. Edge
directions agree; parameter speeds and curvature are not promised to agree.
The collar's interior join retains the donor tangent relationship. Linear and
quadratic collar segments convert exactly to cubics before fitting.

The shoulder uses deskewed proportions. The foot uses native coordinates to
preserve its actual slanted overhang. Fitting the italic foot solely in the
deskewed frame produced a small native overhang change; visual-proof bounds
exposed it. Native fitting removes that change. Deskewed foot extrema may then
shift slightly (about 0.4 units in this experiment); those diagnostic extrema
are not the visible glyph bounding box.

Endpoint and handle corrections are separately limited to 25 font units.
The collars cannot silently absorb a large mismatch. These limits and the
collar fractions may need stricter contextual rules after visual review.

## Validation contract

Every fit checks:

- Exact identity of outside curve spans in the deskewed construction.
- Seam positions and edge direction vectors within numerical tolerance.
- At most 10% changed part ink and 2% changed whole-glyph ink.
- At most 0.1 square font units of outside-ink difference.
- At most 0.01 units of whole-glyph bounds drift in both the fitting frame
  and native coordinates.
- Unchanged filled-contour count and sampled horizontal clearance: 32
  scanlines, unchanged ink-interval counts, no gap reduced by more than 10%.

Filled ink is simplified before area comparison. Raw areas double-count
overlapping contours in generated styles and can conceal real differences.
The outside-ink check uses XOR. These budgets are experimental guard limits,
not design acceptance criteria. Sampled clearance and equal contour counts
supplement outline lint; they are not a continuous clearance or topology proof.

Whole-font checks preserve unrelated outlines, glyph/font metadata, widths,
anchors, components and features. They verify the component-dependency closure,
report affected acceptance records and recorded flattened dependencies, verify
save/reopen content, run affected outline lint and compare compiled shaping.

**Contour metadata is an explicit exception:** reconstructed scratch contours
have new point topology and do not preserve point identifiers or smooth flags.
An eventual generator must assign them deliberately and check the geometry
after integer rounding, extrema and hinting work. No scratch UFO is suitable
for copying over a master.

The recipes rebuild deterministically from original inputs. They are not
iterative normalisers: fitted candidates contain deliberately inserted seam
vertices and are not fresh inputs to automatic seam discovery. A production
rule belongs at a defined generator stage with stable input geometry.

## Run and review

```sh
# Same cross-worktree lock as tests and reproduction.
flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/shape_seams.py

PYTEST_ADDOPTS='tests/test_shape_seams.py tests/test_shape_ports.py tests/test_shape_consistency.py' make test
```

[Open the candidate proofs](../build/glyph-review/shape-seams/index.html).
The [report](../build/glyph-review/shape-seams/report.json) records policy,
source and implementation identities, seams, fitting measurements, dependency
effects, lint and shaping checks. Every run uses a fresh directory. Source and
implementation identities must still agree before the report is published.

Rejected geometric candidates remain visible for diagnosis. Passing checks
does not install or accept a drawing. Differences below 0.0001% of part ink
retain the original target without rewriting its contours.

## Findings — 2026-10-27

| Style | h shoulder: changed part ink | I foot: changed part ink |
|---|---:|---:|
| Regular | Already consistent | Already consistent |
| Italic | 0.156% | 0.922% |
| Bold | 0.038% | Already consistent |
| Bold Italic | 0.923% | 0.603% |

All eight fits pass the geometric budgets. Whole-glyph changes are below
0.15%. No measured ink escapes the permitted region; native glyph bounds are
preserved. These small differences make useful construction-rule experiments,
but do not establish a visible defect in the originals.

Nine seam tests cover independent curve subdivision, endpoint/tangent fitting,
unchanged donor core, excessive correction refusal, split/reassembly identity,
metadata protection and repeatable bounded fits in all four styles. Together
with attachment and consistency tests, 25 tests pass through the shared lock.
Ruff passes. The preview additionally compares compiled shaping and affected
outline lint; those results are recorded with the particular candidate run.
The completed run passes all 184 shaping comparisons and introduces no new
outline-lint findings. All four production UFO byte hashes remain unchanged.

The eight enlarged before/after overlays were inspected, along with the full
Italic and Bold Italic proofs containing peers, anchors, text-size repeats and
shaped words. No obvious broken seam or new spacing change was visible; the
differences remain subtle. The native-coordinate foot revision was re-rendered
and inspected. This is a source-outline review, not hinted rendering or visual
acceptance of a changed design.

The component closure covers 39 glyphs in each italic style and six in Bold;
Regular requires no direct outline change. The italic I drawings already have
acceptance records: the report identifies them as affected, and this experiment
does not replace that acceptance or approve the new feet. Recorded flattened
dependencies are empty here; dependencies encoded only in generator code have
not been inferred or rebuilt.

## Production boundary

These two contexts now have executable seams and fitting rules in every style.
The m interior/exit shoulders, u returns, bowls, diagonal junctions and
arm-connected serifs need distinct contracts. Similar silhouettes alone do not
justify applying n's entry recipe to them.

Production integration still requires drawing review, stable construction
points, finishing rules, clearance/curvature checks after rounding, rebuilding
flattened dependants and whole styles through the authoritative generators,
and the family's release checks. None of this experiment changes masters.
