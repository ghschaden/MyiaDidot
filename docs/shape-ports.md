# Attachment vocabulary for connected shapes

The production objective is repeatable construction with deliberate optical
variants. A shape needs both an outline and a contract for how it connects.
Reducing the number of shape names is secondary to preserving those contracts.

`scripts/shape_ports.py` adds a read-only attachment audit to the existing
[consistency policy](shape-consistency.md). It measures the **original outline**
at every crop boundary of the anatomical study, rather than measuring the
artificial straight edges created by clipping. It does not replace any ink,
edit a generator, or claim that the study's crops are usable assembly seams.

## Vocabulary and construction contract

Keep the anatomical terms **stem, bar, diagonal, shoulder, return, bowl, serif,
dot**. These describe function rather than a fixed inventory of templates.
The 25 existing comparison contexts separate optical roles within these terms.
Additional terms and contexts will be needed for unsampled designs; this is
not yet an anatomical decomposition of every glyph.

For production, a reusable connected part needs these explicit fields:

| Field | Purpose | Current state |
|---|---|---|
| Role and optical context | Distinguish case, size, weight, entry/interior/exit and script where necessary | Existing sampled comparison policy |
| Same-style donor | Keep one stable design reference, after weight/slant decisions | Existing explicit donors |
| Local coordinate frame | Preserve the relation between deskewed and native outlines | Measured shear and coordinates |
| Attachment boundary | Identify a cut through ink and its original curve segments | Measured for study crops |
| Attachment interval | Record both ink edges, center and width along the cut | Measured on unambiguous sides |
| Edge tangents | Constrain the direction of both sides of a join | Analytic derivatives, both frames |
| Thickness normal to the stroke | Control apparent weight independently of cut angle | Not inferred from cut width |
| Blend region | Specify exactly where fitting may alter the outline | Requires a design recipe |
| Counter clearance and outside-ink invariants | Prevent a join from closing a counter or changing a neighbouring part | Requires candidate construction and validation |
| Intentional exceptions | Retain useful local optical adjustments | Must be explicit design decisions |

An attachment interval is a pair of outline crossings with ink between them.
It is not a spacing anchor or a declaration that a donor can be pasted there.
The two edge tangents matter: matching only the centerline would miss a kink
on either edge. The measured width is **along the cut**, not stroke-normal
thickness. Coordinate frames and widths must be retained even when normalised
shape comparisons report identical silhouettes.

The eventual construction rule should therefore be: select a part in its
optical context, fit its declared attachments within a permitted blend region,
then validate the resulting ink and its dependent constructions. No such
connected-part replacement is enabled by this audit.

## Run and inspect

```sh
.venv/bin/python -I scripts/shape_ports.py
PYTEST_ADDOPTS='tests/test_shape_ports.py tests/test_shape_consistency.py' make test
```

Outputs stay under `build/glyph-review/shape-ports/`:

- [Review sheet](../build/glyph-review/shape-ports/index.html): donor comparisons
  and one SVG per measured sample.
- [Machine-readable measurements](../build/glyph-review/shape-ports/ports.json):
  curve intersections, segment parameters, tangents, attachment intervals,
  unresolved contacts, donor differences, source and implementation identities.

Positions use deskewed font units; native positions and tangent vectors are
also included. Segment identifiers refer to the decomposed path used by the
audit, not stable UFO point identifiers. No rotation, reflection or independent
axis scaling is applied to the donor comparison. Consequently differences
describe actual cut constraints, not a verdict on shape similarity.

The algorithm solves line/quadratic/cubic intersections analytically, checks
ink using the nonzero winding rule, and refuses to interpret sides containing
vertex hits, tangencies, corner contacts or coincident outline edges. Ink
reaching the end of a cut is also unresolved. This conservative treatment
leaves some usable seams unclassified; it avoids silently treating a counter
as a stroke or inventing an attachment at a crop corner.

## Findings in this worktree — 2026-10-27

Across Regular, Italic, Bold and Bold Italic:

- 132 connected samples, with 528 crop sides.
- 199 sides have measurable attachment intervals.
- 104 sides are ambiguous; 225 have no attachment.
- 82 sample-to-donor comparisons have measurable constraints, including
  reference-to-self comparisons. This is not 82 approved reusable parts.
- 48 comparisons require seam design, and two have different cut topology.

Straight stem interiors often agree already. Regular H's two stems and I's
sampled stem have matching cut widths and edge directions. In Bold, m's exit
stem is one unit narrower than n's at both sampled cuts. Bold Italic has larger
context-dependent differences: I's stem is about 20–22 units narrower than
the H donor at the sampled cuts. These are observations, not proposed fixes.

The existing shoulder crops demonstrate why shape matching alone is
insufficient: the lower-right crop corner falls inside a stem, splitting a
connection across two rectangle sides. They need a deliberately designed
seam, possibly nonrectangular, before a shared shoulder rule can be assessed.
The proof distinguishes this from a clean transverse cut through a stem.

Visually inspected representative proofs: Regular n shoulder, Italic n
shoulder, Bold H foot and Bold Italic m last shoulder. These show original
deskewed outlines and measurement overlays, not changed drawings. The other
128 individual proofs were generated but not individually inspected.

Seven analytic tests cover counter exclusion, coincident edges/crop corners,
italic coordinate recovery, a cubic with three known intersections, tangent
contact, open-contour rejection and donor-topology refusal. Together with the
nine existing consistency tests, all 16 pass through `make test` and its shared
lock. Ruff passes. All four source UFO byte hashes remain unchanged.

## Scope of completion

The existing [complete geometric grammar](shape-grammar.md) reconstructs every
glyph, including residual geometry; it does not establish that every glyph is
built from reusable typographic parts. The anatomical vocabulary, donor policy
and attachment audit are successive production-preparation layers. This new
audit makes the missing join contracts visible and machine-readable. A
production-ready, all-glyph anatomical grammar still requires broader role
coverage, explicit seams, fitting rules and whole-family generator validation.

The [connected seam experiments](shape-seams.md) now implement explicit
entry-shoulder and capital-foot contracts, bounded fitting and scratch-font
validation in all four styles. Other contexts remain measurement-only.
