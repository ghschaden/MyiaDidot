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

## Stage 2: declared constituent reuse

`--constituent-reuse` enables paired-boundary detection and adds a separately
versioned `constituent_reuse` evidence section to JSON and HTML. Use
`--boundary-glyphs uni019C U m n` to keep the pilot focused. The existing paired
proof displays both observed boundaries and normal sections. Production sources
remain read-only.

The optional provenance sidecar now accepts `operation: "stroke-copy"`. Its
`part` contains `base_geometry_id` and `target_geometry_id` selecting unique
paired-boundary findings. Add a nonempty `constituent` instance label, such as
`left-U` or `right-U`; retain the existing source hash/style, transform,
protected landmarks and evidence origin fields. Each declared native-frame affine
transform must map **both** base stroke boundaries to the observed target edges
within 0.001 em, symmetrically, including endpoints. Edge order and traversal
orientation are immaterial. The declaration verifies sampled geometric support
for intent, not historical authorship. It does not assert that an entire U survives
when only a stem was checked.

Pairs of distinct constituent labels in one target are classified as:

- `shared`: both declarations verify and both observed stroke edges coincide
  within 0.001 em, including their supported endpoints.
- `repeated-but-separate`: both declarations verify, but their observed stroke
  regions have disjoint bounding boxes.
- `unresolved`: a claim fails verification, regions overlap only partly, or
  constituent correspondence is absent. Recorded generator inputs alone cannot
  resolve ancestry, including after a Boolean union erases the evidence.
- `similar-only`: observed spans have compatible axis families and width profiles,
  without verified constituent correspondence. This never establishes that m can
  reuse n's entry/exit role.

Shared/separate comparisons retain declaration and target-span IDs, boundary
agreement and a bidirectional sampled boundary clearance in font units. This
clearance is a local diagnostic, not a certified global counter minimum. The
bounding-box separation rule deliberately leaves some rotated or curved separate
regions unresolved. Partial-span correspondence and automatic component expansion
are not implemented; supply verified complete paired-span declarations instead.

Validation: 61 focused tests through `make test` cover the existing recognisers
and new shared/separate cases, reflections, explicit taper, stale declarations,
displaced endpoints, wrong width, missing evidence and read-only CLI artifacts.
These are synthetic controls, not a measured real-font precision guarantee.
A runnable generated sidecar and positive proof are under
`build/glyph-review/constituent-reuse/synthetic/`. Four-style Ɯ/U/m/n reports are
under `build/glyph-review/constituent-reuse/{Regular,Italic,Bold,BoldItalic}/`.
They retain unresolved ancestry for every pilot glyph without declarations.
The Regular overlay was visually inspected: it shows the middle stem and curved
returns in Ɯ, and stops m/n stem sections below the shoulder junctions. All four style overlays were inspected; Italic m/n have less supported heavy-stem
coverage, so those omissions must not be read as successful constituent checks.
No design acceptance or repair is implied.

A source-pinned Regular U-to-Ɯ hypothesis is under
`build/glyph-review/constituent-reuse/Regular-declared/`: identity and an 800-unit
horizontal translation were checked against the surviving heavy stem spans.
The first verifies at 0.403 units; the translated span differs by 2.134 units
against a 2.048-unit tolerance and is rejected. The combined reuse result remains
unresolved. This can include different detector trimming at endpoints; it is not
a finding of a defective outline or proof against historical reuse. The threshold
was not relaxed to accept this case.

Current-main evaluation is recorded in
[`stage2-current-source-evaluation-2026-10-30.md`](stage2-current-source-evaluation-2026-10-30.md).
It replaces the historical pilot as the current-source evidence: four freshly
pinned sidecars and inspected overlays, explicit missed/interrupted spans, and
65 passing focused tests including an independent radial-ribbon family. Local
verified copies do not establish complete base coverage or a shared Ɯ middle stem.

## Stage 3 pilot: lower returns

`--lower-returns` enables the observed-stem graph and emits `returns.svg` plus
`lower_returns` evidence in JSON/HTML. Use `--boundary-glyphs` to restrict the
scope. The initial pilot measures lower-counter profiles and reports missing or
competing neighbours; exit and tail roles remain unresolved. See
[`lower-return-pilot-2026-10-30.md`](lower-return-pilot-2026-10-30.md) for the
four-style inspected results, controls, and limitations. This is not a complete
Stage 3 recogniser or a source of repair approval.

The subsequent [arm/context increment](return-context-review-2026-10-30.md)
uses `myiadidot-lower-returns-v2`. It adds `arm_context` section evidence, bounded
cap traces and below-baseline refusal context. A few real exits are now supported;
real interior roles and tail attribution remain unresolved. Green proof marks
show individual valid sections; only five consecutive sections with compatible
axis/width establish a complete local band. Orange traces show verified short
caps. The existing global `neighbours` evidence is preserved separately.

Same-style, same-role retrieval is now included under `lower_returns.matches`
(`myiadidot-return-matches-v1`). It gates on resolved roles and local support,
then compares counter profiles, both adjoining width profiles, attachment
directions and verified cap traces. `candidate` is not design or repair approval;
unresolved contexts remain non-positive. See the
[matching evaluation](return-matching-review-2026-10-30.md), including reconstructed
historical bad-m regions and the distinction between refusal and diagnosis.

## Upper arches and interior return conflicts

`--upper-arches` enables `upper_arches` (`myiadidot-upper-arches-v1`) and an
`arches.svg` proof. Scope uses `--boundary-glyphs`; JSON/HTML retain source hashes,
policies, counter clearances, traced arms, local normal-band statuses, verified
caps, shared horizontal sections, unresolved roles and local conflict findings.

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --ufo build/glyph-review/main-progress-2026-10-30/current/sources/MyiaDidot-BoldItalic.ufo \
  --upper-arches --boundary-glyphs n h m u v w --proof-glyphs n h m u v w \
  --out build/glyph-review/upper-arches-example
```

Entry/interior/exit are local topology roles established by shared ink intervals
and verified terminal context. They do not override failed normal-width checks
or establish reusable geometry. An interior stem also feeding a lower return is
reported as `interior-terminal-conflict` if its cap verifies, otherwise
`interior-return-detour`; both are review findings, not automatic design rejection.
The final exit is excluded by its lack of a following arch. See
[the upper-arch review](upper-arch-review-2026-10-30.md) for the pinned four-style
results, both historical diagnoses and remaining omissions.

## Region-level evaluation

`relationships.region_evaluation.evaluate_regions(corpus, report, em, slant)`
scores `myiadidot-region-corpus-v1` annotations against saved arch/return reports.
Each source-pinned region names its glyph, anatomical family, split, detector,
original-font-coordinate box, candidate expectation and optional role expectation.
Conflict regions separately label expected findings at the lower-turn location.
Output preserves missed candidates, unresolved/wrong roles, out-of-scope candidates,
ambiguous assignments, unlabelled detections and missed/false conflicts. Stale or
unpreserved sources, incomplete detector scope and within-corpus family leakage
are rejected. It does not infer labels from detector output.

The [first real-family evaluation](arch-family-evaluation-2026-10-30.md) covers
58 regions with fixed labels and thresholds. It exposes closed-counter/terminal
scope mismatches and fixed-window misses despite zero false splice warnings on
those normal drawings. These results do not establish general repair reliability.

### Counter scope (2026-10-30)

Upper/lower candidates retain raw geometry separately from `anatomical_scope`:
closed counters, verified terminal curves, supported stem connections and unresolved
context. Closed counters are excluded from role graphs and terminal conflicts;
missing stem support alone never establishes a terminal. See
[counter scope review](counter-scope-review-2026-10-30.md) for evidence and remaining
s/r coverage limits. Lower report schema is v3; upper schema is v2.

### Terminal closure evidence (2026-10-30)

Terminal scope additionally accepts a reciprocal horizontal ink cut whose directed
contour closes on its verified opposite boundary within the existing cap window.
This evidence is separate from normal-width bands and is not used to grant roles
or splice findings. Optional anatomical-scope labels are scored separately from raw
candidate outcomes. See [terminal evidence review](terminal-evidence-review-2026-10-30.md)
for the frozen-detector evaluation and explicit component/heavy-terminal misses.

### Component observations in counter reports

Lower-return v4 and upper-arch v3 reports expand explicit components without
mutating sources. `observations[glyph]` records completeness, issues and contour
origins (source glyph/index, component path, composed transform, source hash).
Candidates carry `contour_origin`; contour indices address that expanded inventory.
Lower-return `observed_strokes` stores locally measured component stroke records
used by neighbour references. These records do not extend core Stage 2 ancestry
claims. Missing/cyclic references, invalid transforms and open contours withhold
the full observation rather than using partial geometry. Overlaps are not Boolean
unioned. See [the component replay](component-observation-review-2026-10-30.md).

### Terminal-window diagnostics

`terminal_context.window_checks` records measured units/em, maximum em,
ratio/excess and maximum-pass status for trace, rise and span when measured.
Rise also has `minimum_em` and `passes_minimum`; its `passes` field covers the
maximum only. Missing checks mean unmeasured, not accepted. The diagnostic policy
is `terminal-window-checks-v1`. These additive measurements do not change
thresholds or grant stem/role evidence. The [heavy-terminal investigation](heavy-terminal-limits-review-2026-10-30.md)
records the width sweep and the remaining qualification gap.

### Per-arm terminal anatomy evaluation

`relationships.terminal_evaluation.evaluate_terminal_arms(corpus, report, em,
slant)` accepts the existing region-corpus v1 format with optional
`terminal_arms: {left, right}` labels (`terminal`, `nonterminal`, `ambiguous`) and
`attachment_context` (`free-end`, `stem-connection`, `interior-connection`,
`uncertain`). Regions still match extrema in original source coordinates; sides
refer to the deskewed arms. The output is `myiadidot-terminal-arm-evaluation-v1`.

Normal caps and reciprocal closure evidence are reported separately. Missing
observations, ambiguous assignment, unreported evidence, unscored anatomy and
unresolved terminals remain distinct. `not-promoted` does not prove nonterminal
anatomy. Attachment labels are retained as reviewer context, never inferred roles.
The full region evaluation retains unmatched detections and coverage accounting.
See [the development contrast](terminal-anatomy-contrast-review-2026-10-30.md).

### Opt-in reciprocal-terminal policy

`--reciprocal-terminal-policy baseline` (the default) uses an independent
0.12 em reciprocal-terminal span window. `wide-morphology` selects the reviewed
0.15 em window. Both retain the same 0.35 em trace and 0.16 em rise limits,
minimum rise, same-contour and reciprocal-cut checks. Normal caps continue to use
`CONTEXT_POLICY`, including its 0.12 em width window.

For example:

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --lower-returns --upper-arches --boundary-glyphs a t k x \
  --proof-glyphs a t k x --reciprocal-terminal-policy wide-morphology \
  --out build/glyph-review/wide-terminal-policy
```

The Python `run`, `return_report`, `arch_report`, `lower_returns` and
`upper_arches` functions accept keyword `terminal_policy='wide-morphology'`.
Unknown names fail even for empty observation scopes. Nested `terminal_policy`
metadata records the selected name and explicit limits. Experimental terminal
contexts include `baseline_status`; anatomical scope consumes that baseline
status. The experiment changes reciprocal-terminal evidence and its overlays,
while roles, normal caps, conflicts, matches and whole-candidate scope remain
baseline decisions. Terminal-arm evaluation consumes the selected morphology.

The wider window admits the previously documented oversized synthetic lobe as
well as real terminals. Missing branch observations still prevent general
anatomical qualification. See [the policy replay](terminal-policy-review-2026-10-31.md)
for the frozen development and former-holdout comparisons.

### Discovery-gate diagnostics

`lower_returns` and `upper_arches` accept an optional `diagnostics=[]` sink.
It records each examined local extremum as `accepted` at `candidate` or `rejected`
at the first failed gate: `ink-side`, `shoulders`, `bend`, `opening` or `clearance`.
`point` is in deskewed font units for both observers; upper reflection is restored.
Available `measurements` report bend degrees, required and achieved arm rise in
em, opening in em, or the count of clear sections. Later gates are not implied to
have passed. These traces do not change returned candidates or omissions.

`relationships.candidate_diagnostics.candidate_diagnostics(font, names,
source_sha256)` produces a separate `myiadidot-counter-diagnostics-v1` sidecar,
including pinned contour/component provenance, seed IDs, policy, coordinate frame
and incomplete-observation issues. The caller must verify the source hash.
Rejected seeds are not terminal evidence or branch classifications. The
[branch observation review](branch-observation-review-2026-10-31.md) traces the
former holdout's ten unobserved branch regions without changing frozen labels.

### Angular-boundary arm observations

`--angular-junctions` / `run(..., angular=True)` adds a separate
`myiadidot-angular-observations-v1` report under `angular_junctions`, using the
existing `--boundary-glyphs` scope when specified. `angular.svg` and the HTML
index show its arm paths and sampled clearances. The Python APIs are
`relationships.angular.angular_observations(contours, em, slant=0)` and
`angular_report(font, report, names)`.

Angular seeds exceed the unchanged rounded-turn bend limit; they stay outside
rounded-return results. The observer preserves both complete and partial paths,
fixed 0.08 em reach, sampled clearance and closed-counter containment. It bounds
reversal from the maximum rise reached by each arm using 0.003 em; this leaves
the rounded recognizer's per-edge test unchanged. `visible-angular-arms` requires
both arms to reach the fixed window, all eight clear sections and the existing
minimum opening. Other cases remain `unresolved`, with partial measurements.

All output geometry is deskewed; upper reflection is restored. Each report carries
source-pinned contour/component origins and incomplete-observation issues.
`role` remains unresolved and `terminal_evidence` is `not-evaluated`, including
visible angular arms. Existing terminal-arm evaluation does not consume this new
scope. See [the angular pilot](angular-observation-review-2026-10-31.md).

### Opt-in terminal closure in angular scope

`--angular-terminal-closure` enables the angular channel and tests reciprocal
closure only for complete angular windows, using the selected
`--reciprocal-terminal-policy`. The Python equivalents are
`run(..., angular_terminals=True)` and `terminal_policy='baseline'` or
`'wide-morphology'` on the angular observation/report functions. Leaving the policy
unset preserves observation-only v1 output. Closure-enabled output is angular v2.

Each row retains its arm-visibility status and unresolved role. Per-arm
`terminal_context` reports verified/unresolved closure, or `not-evaluated` with
empty measurements for an incomplete window. The shoulder's source occurrence
is reconstructed from its retained arc, directed path length and contour direction;
an inconsistent occurrence is withheld. Reflected upper traces and sections are
restored to deskewed font coordinates. Existing purple proof traces show verified
closure. Closed-counter containment is retained.

`relationships.terminal_evaluation.evaluate_angular_terminal_arms` scores this
scope independently against the original region boxes. Normal caps are unreported,
withheld closure remains unknown, and ambiguous labels/assignments and unmatched
angular observations are retained. Neither positive closure nor failure supplies
a branch or attachment role. The [angular terminal review](angular-terminal-review-2026-10-31.md)
records the stem-foot mismatch in Italic k under both fixed policies.
