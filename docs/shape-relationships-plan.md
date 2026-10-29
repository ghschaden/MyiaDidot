# Plan: extend structural relationship discovery

Date: 2026-10-29. Starting point: the two recognisers in
`scripts/shape_relationships.py` (curve-to-straight transitions and base/mark
attachments). This is an implementation plan, not authorisation to change
production generators or outlines.

## Proposed scope: six more relationship families

Eight families in total are a useful first target, not a proven complete or
minimal vocabulary. Implement three additions first and reassess their usefulness
before committing to the remaining three. Structural roles may have subtypes;
adding a subtype does not automatically require another recogniser.

| Addition | Relationship | Initial examples / controls | Main question |
| --- | --- | --- | --- |
| 1 | Paired boundaries of one stroke | Straight spans in H/n; slanted stems in h/y; tapering diagonals as controls | Do these two edges bound the same stroke, with a coherent width profile? |
| 2 | Repeated or shared stem between constituent parts | Ɯ/U; m/n interior legs; independent adjacent stems as controls | Are two parts genuinely sharing a stroke, or merely standing nearby? |
| 3 | Stem–arch–stem connections and rounded returns | n/h/m shoulders; u returns; v/w as distinct comparison cases | Are the connections entry, interior or exit roles, and are their neighbours compatible? |
| 4 | Inner and outer boundaries of a bowl | o/O; bowl regions in b/d/p/q; a/e as harder cases | Which boundaries form one bowl and counter, and where do attachments interrupt them? |
| 5 | Stem-to-terminal connections | Bracketed serifs, italic exits, ball terminals | Does the terminal have the same attachment, direction and weight role? |
| 6 | Added stroke intersecting or joining a base | Bars, slashes and hooks; Ø, barred letters, hooked letters | Which geometry belongs to the final base, which to the addition, and how is their junction resolved? |

These are relationships between parts, not a demand that all letters use a small
set of interchangeable outlines. Prior shape-grammar experiments already showed
that n's entry/exit pieces do not automatically belong inside m, and that a bowl
plus a plain stem does not establish a convincing phi.

## Stage 0 — strengthen the common foundation

Do this before adding more coarse families.

1. Split the existing implementation into a small shared geometry/provenance
   layer, individual recognisers, matching policy, and reporting. Preserve the
   current CLI and version the report schema if necessary.
2. Give each recognised span a source-pinned geometric identity; retain original
   point/segment references for inspection without making matching depend on them.
3. Add queries for a particular local relationship, not just all relationships in
   a glyph. Rank matches, collapse repeated derivatives into their base families,
   and show direct evidence separately from inferred similarity. The current y
   query's 169 glyph peers illustrate why this is needed.
4. Introduce a validated optional sidecar declaration for known construction
   relationships: source style/hash, base, part, transform, operation, protected
   landmarks and evidence origin. Reject stale declarations. A declared recipe is
   evidence of intent; verify that the observed geometry supports its claims.
5. Reuse existing exact-fragment data, component references and builtFrom records
   as evidence sources. Do not treat a recorded generator input as proof that its
   outline was copied. Do not infer new production provenance by parsing arbitrary
   Python generator code as though it were a declarative recipe.
6. Build a small labelled evaluation corpus: clear positives, close negatives,
   ambiguous examples and historical failures. Hold out independent base families,
   rather than distributing y and its accents between training and evaluation.

Output: versioned evidence schema, local-span query, readable uncertainty and
rejection explanations, and evaluation harness. Production provenance instrumentation
is a later integration task for Claude/the main-worktree owner; this stage uses
read-only inputs and sidecars under build.

## Stage 1 — paired stroke boundaries

Start with straight and gently curved, unbranched spans. Use opposing boundary
normals, consistent ink intervals and agreement along successive sections to
establish correspondence. Check both directions. Stop or mark uncertainty at
junctions, ambiguous crossings and multiple competing partners; do not force a
complete skeleton.

Measure width, taper, width variation, lateral trajectory and the confidence of
section correspondence. Preserve explicit intended taper. Use normalised metrics
but retain actual font-unit measurements for inspection.

Acceptance: independent rectangles, tapered strokes and curved ribbons have known
answers; rotated/reflected/subdivided versions agree within declared numerical
bounds. Nearby unrelated strokes, counters and junctions must not be confidently
paired. Real proofs show the matched edges and sections, not just a numerical score.

## Stage 2 — shared stems and constituent reuse

First establish constituent correspondence using explicit provenance or verified
transformed spans. Then use Stage 1 to check whether both constituents refer to
the same stroke region and share compatible thickness, axis and endpoints.

Pilot Ɯ/U, with separate cases for repeated parts and the shared middle region.
Use m/n to test whether repeated appearance is insufficient when connection roles
differ. Include two adjacent, nonshared stems as negative examples. Where Boolean
union has erased the evidence, report unresolved instead of inventing ancestry.

Acceptance: distinguish shared, repeated-but-separate, similar-only and unresolved
relationships. Known transforms and deliberately misaligned unions must produce
the expected results. Show overlays and counter clearances.

## Stage 3 — arches and returns

Build a local graph of paired stems, curved connections and open counter regions.
Classify connection role from both neighbours: entry, interior or exit. Preserve
arch/return distinctions, stroke direction and terminal context.

Pilot n/h/m and u, then independently test v/w and relevant non-Latin examples.
Compare counter opening, crown/turn position, attachment directions and width
profiles. Do not presume that rotating u makes it a reusable n shoulder.

Acceptance: recover useful same-role matches while rejecting the erroneous reuse
of n's entry or exit inside m documented in the earlier grammar experiment.
Counter width and adjoining strokes must contribute to matching.

Reassessment milestone: after Stages 1–3, there are five relationship families.
Review precision, uncertainty, independent family coverage and usefulness for
actual repairs. Adjust the remaining scope based on missed mechanisms, not merely
on the number of unclassified glyphs.

## Stage 4 — bowls and counters

Begin with complete o/O-style bowls. Establish contour containment and paired
boundary correspondence; then extend to interrupted bowls and stem attachments.
Record opening/attachment locations, contrast and overshoots. Explicitly defer
complex a/e cases until their topology is supported.

Acceptance: distinguish two nearby contours from a real bowl/counter pair; retain
orientation and winding information; identify changes in counter clearance rather
than relying on total ink area. Do not force different letters to use o's curves.

## Stage 5 — terminals and additions

Implement these as two separate recognisers sharing the preceding infrastructure.

Terminals: locate a terminal region and its connection to a known stroke. Use
bracketed serif, italic exit and ball as distinct subtypes. Match attachment role,
direction and local weight before silhouette. Test genuine corners as controls
against over-smoothing.

Additions: use known base geometry/provenance to identify bars, slashes and hooks.
Separate joined additions from crossings and detached marks. Measure each
junction's clearance and accumulated ink; report base correspondence failures.
Pilot one addition subtype at a time. Whole-glyph resemblance cannot establish
base inheritance when the relevant part has been redrawn.

Acceptance: the correct final same-style base is recoverable in supported cases;
wrong-weight donors and misaligned intersections are rejected or unresolved.
Protect intentional optical corrections as explicit deviations, not hidden errors.

## Shared validation and definition of done

For each recogniser:

- Produce positive, negative and unresolved results with the evidence needed to
  inspect each conclusion. A similarity threshold is not design acceptance.
- Test subdivision, contour-start and orientation invariance; apply scale/shear
  normalisation only where meaningful, preserving handedness and role where needed.
- Test detector accuracy independently of any later repair algorithm. Evaluate on
  held-out base families and report false positives, missed cases and uncertainty
  separately. Aim for no unexplained high-confidence false positive in the reviewed
  corpus; do not convert that finite result into a universal guarantee.
- Inspect focused overlays and same-style peers in all four styles as scope grows.
  A relationship found in one style is only a hypothesis for another until checked.
- Keep source identities, deterministic reports, read-only operation and explicit
  handling of stale provenance. Write all generated artifacts under build.
- Run focused tests through `make test` and the shared lock; observe the six-core
  combined limit. Do not change sources, production generators, test baselines or
  acceptance records in this worktree.

A recogniser is complete when it supplies useful, explainable matches, rejects
its close negatives, reports its unsupported cases, and has inspected proofs and
independent tests. It is not complete merely because it labels every glyph.

## Subsequent repair integration — separate milestone

Once a relationship has earned trust, attach an operation-specific experimental
repair to it. Require improvement of the target defect, preservation of protected
geometry, no new unrelated findings, and final-output width/clearance/topology
checks. Keep discovery, repair proposal and acceptance separate in the API.

Do not build six repair solvers as part of these six recognisers. Begin with one
mechanism for which the relationship evidence is strong and compare its outcome
against the current conservative production repair. Installation into main stays
with the person or Claude under explicit production authorisation.

## Stage 0 implementation status — 2026-10-29

Implemented: module separation with compatible CLI; source-pinned geometric
locators; local-span retrieval; ranked families based on explicit ancestry;
validated component/span sidecars; verified reuse of the existing exact grammar;
and a labelled evaluation harness with family separation and per-case outcomes.
See `docs/shape-relationships.md` for schemas, commands, evidence scopes and limits.
No additional recogniser or repair solver has been started. Production-side
provenance instrumentation remains the explicitly separate integration task.
