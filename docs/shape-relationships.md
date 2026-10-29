# Discovering local structural relationships

`scripts/shape_relationships.py` is a read-only experimental system for two
relationships: **smooth curved runs meeting straight edges**, and **base-plus-mark
attachments**. It scans a UFO, writes a provenance graph and explainable families,
answers a related-glyph query, and generates an HTML report and highlighted SVG.
It does not change drawings or authorise a repair.

## Usage

Run from the shape-grammar worktree:

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --ufo sources/MyiaDidot-BoldItalic.ufo \
  --related y \
  --proof-glyphs y yacute n h u v w o \
  --out build/glyph-review/shape-relationships
```

`--related yacute` explains both component ancestry and attachment-role peers.
The default UFO is this worktree's Bold Italic, which may be older than main.
For main, use an explicitly extracted committed snapshot under build or a stable
read-only UFO path. The report pins the full source-content hash and implementation
hash, records all thresholds, and checks source preservation before completion.
Outputs must be physically below this worktree's build directory and disjoint from
the input. Existing output directories containing symlinks are refused.

Artifacts:

- `report.json`: every relationship, evidence, measurements, family membership,
  provenance edges, omissions, source identity, and optional query results.
- `index.html`: browsable explanation table and query results.
- `proof.svg`: selected glyphs, with curved runs highlighted in blue; red indicates
  a lateral-reversal notice. It is not an accepted drawing or hinted proof.

Use `--proof-glyphs` for a focused set. The exhaustive findings remain in JSON and
HTML; the default proof selects at most 16 glyphs. All dimensions used in matching
are em-normalised. Curves are measured in the deskewed frame; proofs map them back
to the original outlines.

## Relationship 1: curve to straight edge

The recogniser identifies a smooth boundary between a genuinely curved segment
and a straight segment. It walks backwards over the complete smooth curved run
until a corner or line, and forwards over collinear line pieces. It recognises
monotone collinear cubics/quadratics as straight edges. It treats either contour
orientation alike, including the closure boundary.

This avoids treating every Bézier subdivision as an anatomical landmark. The
report retains the original contour and segment indices for inspection, but
matching uses geometric spans rather than those indices.

An adaptive Bézier flattening supplies arc-distance samples. Each transition
records its junction, line direction/length, curve length, join angle, a local
trajectory profile, and a lateral-reversal measurement. A join close to the
smoothness threshold is marked uncertain and is excluded from peer matching.
Exactly zero-length pieces are ignored for geometric analysis and reported with
their original indices; the source is retained unchanged. Open contours are
omitted and reported. Such omissions are not passes.

Coarse families describe the line's axis (vertical, horizontal, oblique). A related
query further filters candidates using comparable curve and line lengths and the
RMS difference of local tangent-frame profiles. Thus membership of a broad axis
family alone does not establish that two shapes are useful peers. Each accepted
match has its measurements and rationale; rejected candidate counts are broken
down by reason.

The near-junction profile covers at most 0.08 em, sampled approximately every
0.002 em. Peer lengths must be within a factor of two and profile RMS within
0.008 em. These are transparent experimental retrieval thresholds, not optical
acceptance limits. They need calibration on broader held-out examples before
being used to guide production automation.

The lateral diagnostic measures excess side-to-side travel over net travel. It
can identify a reversal without relying on a short segment, but a monotonic
sideways step can escape it. It is explicitly **not a replacement for a step
regression detector**, a stroke-width check or a claim of ugliness. The recogniser
finds structural relationships whether or not they contain a defect. No offset
mismatch is inferred: that would require weight-stage provenance from the generator.

## Relationship 2: base plus attached mark

Canonical Unicode decomposition proposes a base and mark. The recogniser then
requires actual UFO component evidence; glyph names alone are insufficient.
The supported confirmed case has one identifiable base, one mark component and
no additional own contours.

The mark can be a spacing piece such as `acute`, referenced by a combining wrapper
such as `acutecomb`. The recogniser follows the wrapper's single-component chain,
composes affine transforms, and maps its underscore attachment anchors back into
the attached piece's coordinate frame. Both base and mark anchors are then mapped
through the composite's actual transforms. Exactly one matching named anchor pair
within tolerance establishes the attachment role.

Missing anchors, multiple matches, misplaced anchors, unsupported flattened or
stacked constructions and missing components remain unresolved with reasons.
Component ancestry is still recorded when attachment cannot be confirmed. The
system does not guess which anchor to use merely because two pieces look close.

Families are operation-specific anchor roles, such as `base-mark/Acute`. A query
can therefore find other letters using that attachment role without confusing
shared construction with similar overall silhouettes.

## Provenance and limits of generalisation

Every component reference is recorded with its index and affine transform.
Existing `org.myiadidot.builtFrom` entries are retained separately as unverified
records of generator inputs. They are not falsely promoted to evidence of a
particular copied span, and do not enter confirmed component ancestry queries.

The system does not alter generators to record new provenance. In particular,
flattened shared-stem constructions such as Ɯ are outside these two recognisers;
it will not claim that Ɯ inherits U merely because we know that from the recipe.
A future generator-side provenance API can supply that third relationship.

Query results separate component ancestors/dependants from compatible structural
peers. The latter are candidates for comparing a local operation, not a universal
classification of letters or permission to apply the same repair. A proposed
repair still needs an identified cause, independent geometry/width/clearance
checks, preservation rules and visual review. Ambiguous structure remains explicit.

No compiled shaping, hinting, paired-boundary thickness reconstruction or repair
solver is part of this module.

## Validation

```sh
PYTEST_ADDOPTS='tests/test_shape_relationships.py' make test
.venv/bin/ruff check scripts/shape_relationships.py tests/test_shape_relationships.py
```

Tests include independently constructed curves and known lateral excursions,
subdivision and straight-edge representation changes, cyclic contour starts,
orientation, scale and shear, degenerate cases, transformed combining wrappers,
ambiguous/missing attachment evidence, cycles, a real yacute attachment, structural
peer rejection, read-only operation and end-to-end artifact generation.

## Stage 0 infrastructure (implemented 2026-10-29)

The CLI remains `scripts/shape_relationships.py`. Its implementation is now split
under `scripts/relationships/`: shared geometry/policy, recognisers, discovery,
identity, matching, provenance verification, reporting and evaluation. Existing
Python imports through the CLI module remain available for compatibility.

Reports use `myiadidot-relationships-v2`. Each finding has:

- `geometry_id`: a locator based on the glyph, role and geometric landmarks,
  independent of report ordering and ordinary curve subdivision;
- `id`: that locator pinned to the source snapshot;
- original contour/segment references and a readable locator;
- `identity_status`: coincident locators are ambiguous, not silently conflated.

A geometric locator is not proof that interiors are unchanged between snapshots.
Source-pinned IDs prevent accidental reuse as though a changed source were the
same observation. Landmark coordinates are rounded to six decimal places for
identification; matching continues to use measured geometry. Duplicate locator
occurrences get distinct source IDs but remain ineligible for confident matching.

### Query one local span

First run the normal scan and select a relationship from `report.json`. Then:

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --ufo PATH/TO/SNAPSHOT.ufo --related y --span GEOMETRY_OR_SOURCE_ID \
  --limit 12 --out build/glyph-review/relationship-local-query
```

Only that span contributes matching evidence, and only that span of y is
highlighted in its proof. Results retain all individual matches but display ranked
base families. Confirmed mark/base ancestry and pure single-component aliases can
be grouped; similar silhouettes and unverified generator-input records cannot.
Missing, ambiguous and wrong-glyph selectors fail explicitly. The limit changes
presentation only; it does not discard the full evidence in JSON.

### Optional provenance declarations

Pass `--provenance build/.../provenance.json`. A minimal component declaration is:

```json
{
  "format": "myiadidot-provenance-v1",
  "source": {"sha256": "FULL_SOURCE_CONTENT_HASH", "style": "Bold Italic"},
  "declarations": [{
    "id": "yacute-base",
    "target": "yacute", "base": "y", "operation": "component",
    "part": {"component_index": 0},
    "evidence_origin": "Observed component in the pinned source",
    "transform": [1, 0, 0, 1, 0, 0],
    "protected_landmarks": [{"base_anchor": "DotBelow", "target_anchor": "DotBelow"}]
  }]
}
```

Use the actual `font.info.styleName`, not a filename-derived spelling. Stale
source hashes/styles and malformed declarations fail the run. Geometrically false
claims remain in the report as rejected with reasons. Verified declarations remain
separate from inferred similarity and do not grant permission to edit.

`span-copy` is also supported, with `part.base_geometry_id` and
`part.target_geometry_id` referring to unique recognised curved spans. The declared
native-frame affine transform is checked using symmetric vertex-to-polyline
measurements, with a fixed 0.001 em tolerance, plus named protected anchors. This is
sampled geometric agreement, not an exact Hausdorff bound, topology proof or proof
of historical authorship. It does not claim verification of arbitrary clipping,
union or nonlinear operations; these require later recognisers.

### Existing exact-fragment evidence

`--fragments PATH/TO/grammar.json` consumes the existing complete shape grammar.
The selected style is reconstructed through its existing decoder and compared
with the current font-content fingerprint, including metadata. Stale or internally
inconsistent libraries fail. Verified shared compound boundary fragments are
reported separately from semantic relationships. A shared serif edge does not by
itself establish interchangeable shoulders.

### Evaluation corpus and harness

```sh
flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/relationship_evaluate.py
PYTEST_ADDOPTS='tests/test_shape_relationships.py tests/test_relationship_infrastructure.py' make test
```

The default authored corpus is `scripts/data/relationship-evaluation.json`, not a
production test baseline. Its 16 synthetic cases include positive detections,
equivalent constructions, incompatible spans, corners, threshold uncertainty,
correct attachments, misplaced anchors and ambiguous anchors. Eight development
cases and eight held-out cases use different base families, including cubic and
quadratic constructions. A common mark is explicitly support geometry.

The harness checks family separation through component ancestry, reports each
case and confusion counts per split, and exits nonzero on any failed expectation.
This corpus evaluates geometric reasoning and retrieval, not aesthetic quality or
font-wide accuracy. Family membership in flattened sources still requires authored
labels; the harness cannot infer missing construction history.

For a real-font corpus, supply `--ufo` and a corpus with `source_sha256`. Cases
select a glyph/relationship plus a geometric locator or junction where necessary.
External source mismatches fail before evaluation. Each case declares its expected
result and development/heldout split; all referenced glyphs need family membership.

The implementation manifest now hashes the CLI and every infrastructure module,
rather than only the original monolithic script. Declaration and fragment-library
hashes are also recorded when supplied.

Validation at implementation: 37 focused tests passed through the shared lock;
the 16 labelled corpus cases passed. A source-pinned main 10ddbcdc report under
`build/glyph-review/shape-relationships-infrastructure/` focuses on y's inner
curve/line transition and independently verifies yacute's component and DotBelow
anchor declaration. No production generator, outline or acceptance record changed.

Historical evaluation additionally covers the pre-repair and repaired y outlines
as structural positives, plus o as a no-straight-transition control. All 19 cases
pass in `build/glyph-review/relationship-evaluation/historical-evaluation.json`;
the accompanying corpus pins its historical source hashes. These cases do not
assert that the old y drawing was good.

## Experimental paired stroke boundaries

Enable the third recogniser with `--paired-boundaries`, or restrict its scope:

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --boundary-glyphs H n h y --proof-glyphs H n h y \
  --proof-relationship paired-stroke-boundaries \
  --out build/glyph-review/paired-boundaries
```

The report records the scope and thresholds. Widths are normal-section lengths
in the deskewed design frame, not native-screen pixel widths. Each section casts
through ink to the first boundary and checks reverse correspondence. White-space
crossings, ambiguous sides, corners and failed correspondence are excluded with
reasons. Abrupt partner/width changes break a run; short or broad regions lacking
longitudinal support are withheld. No full skeleton or global topology guarantee
is inferred. Curves use adaptive polyline approximation.

Accepted runs expose both edges, section endpoints and source indices, minimum/
median/maximum width, linear taper and residual width variation. Taper is measured,
not automatically judged defective. Matching compares axis families, span lengths
and width profiles. Duplicate observations from opposite sides are collapsed only
when their sampled centerlines substantially cover each other. Degenerate contours
and partial observations remain subject to the report's stated limitations.

The proofs show opposite edges in blue/orange and sampled sections in green.
Synthetic tests cover rectangles, taper, a curved ribbon, separate neighbouring
strokes, counters, branching, and reversed/subdivided/rotated/sheared geometry.
This is experimental discovery; it neither repairs nor installs font outlines.
