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
At that point no additional recogniser or repair solver had been started. Production-side
provenance instrumentation remains the explicitly separate integration task.

## Stages 1–2 implementation status — 2026-10-30

Stage 1 is available as the guarded paired-boundary recogniser documented in
`docs/shape-relationships.md`. Stage 2 now adds source-pinned `stroke-copy`
declarations, verification of both transformed boundaries, and shared,
repeated-but-separate, similar-only and unresolved outcomes. Synthetic controls
exercise positive reuse and deliberately displaced/wrong-width claims; focused
Ɯ/U and m/n reports exist in all four styles under build.

This first Stage 2 implementation supports complete observed paired spans.
Partial overlaps, erased union boundaries, automatic component expansion and
unknown constituent ancestry remain unresolved. It does not establish historical
reuse in the real pilot from unverified generator records. All four pilot style proofs were inspected, and 61 focused tests pass. Broader
independent family evaluation is still needed before treating this recogniser as
repair guidance. A real Regular translation hypothesis verifies one constituent
span and rejects the other at the fixed endpoint tolerance; the pair correctly
remains unresolved. Stage 3 (arches and
returns, including neighbour roles) is not implemented.

## Reprioritisation after main review — 2026-10-30

Reviewed main `cef605f813e307acd419326bd6a4821cd5e10c64`, 15 commits
ahead of this branch's shared history. Main was clean at inspection. Frozen
sources, the inspected four-style comparison against Bold Italic `dc373511`,
and a fresh relationship run are under
`build/glyph-review/main-progress-2026-10-30/`; see `review.md` there.
Existing Stage 2 implementation work is preserved. This review does not merge
main or change production sources.

Main now contains stroke-aware Bold Italic construction, fairing, repaired
curve/line steps, a stronger per-finding repair gate, U-based Ɯ, redrawn u-family
knees, u-based ʉ and an open hooked ʋ. Earlier examples of these defects become
historical regression inputs, not a queue of outstanding production repairs.
The recorded user choices of knee width and ʋ terminal are constraints, not
parameters for an automatic recogniser to optimise away.

Next tasks, in order:

1. **Finish Stage 2 evaluation on current sources.** Pin main's revision and
   source hashes; regenerate declarations instead of carrying old span IDs over.
   Prioritise Bold Italic U/Ɯ and u/ʉ, with m/n as a role-confusion control.
   Explicitly report missed heavy stems and interrupted spans: the fresh overlay
   finds U/Ɯ stems but misses substantial heavy-stem coverage in ʉ and ʋ.
   The recipe documents intent; without verified declarations the current
   recogniser still cannot establish reuse. Do not loosen endpoint tolerances
   merely to turn this into a positive case.
2. **Make Stage 3's first pilot the lower returns.** Compare u/ų/и/ц/ш/щ/џ
   with their final same-style bases and Italic references. Distinguish interior
   and exit turns, preserve tail attachments, and measure counter clearance and
   turn direction. Then add n/h/m upper arches; they are not interchangeable
   with lower returns. Retain v/w and the historical bad m splice as negatives.
3. **Use refusal cases to evaluate explanations.** Start with љ, whose attempted
   knee repair is documented as introducing a wobble, then u.sc and f_h/f_f_h.
   Report unsupported geometry and competing findings; a production refusal is
   not itself proof of a visible defect or an instruction to repair it.
4. **Defer another repair solver and general smoothing.** Main already implements
   much of the earlier proposed gating. Future experiments must demonstrate a
   specific gap against that current gate. Keep bowls and terminals queued;
   use ʋ's before/after as an aperture/terminal evaluation case, not a demand
   for a closed curl. Promote additions only after base correspondence works.

Completion evidence remains independent-family evaluation and inspected overlays,
not the number of detected relationships. Historical Stage 1–2 proofs and their
61-test result above describe their original source state, not validation of
current main. This inspection ran no production build or test suite and makes
no new hinting, shaping, or design-acceptance claim.

## Current-source Stage 2 evaluation pass — 2026-10-30

Priority 1's evaluation pass is complete; see
[`stage2-current-source-evaluation-2026-10-30.md`](stage2-current-source-evaluation-2026-10-30.md).
All four source snapshots match main `cef605f8` file-for-file. Fresh declarations
and inspected overlays retain successes, failures and heavy-stem omissions.
Bold Italic verifies 6/14 fixed-transform span hypotheses, with no shared-stem
conclusion; ʉ and ʋ still lack heavy-stem observations. The tolerance is unchanged.
Independent curved-ribbon controls extend validation; 65 focused tests pass.
This is not a real-family precision/recall qualification or repair approval.
The next implementation priority is Stage 3's lower-return pilot, carrying those
missing-boundary limitations into its neighbour graph. Region-labelled real-family
evaluation remains required before using Stage 2 as repair guidance.

## Stage 3 lower-return pilot — 2026-10-30

Implemented lower-counter candidates, fixed-height clearance profiles, observed
paired-stem neighbours and shared-neighbour interior graph linkage. See
[`lower-return-pilot-2026-10-30.md`](lower-return-pilot-2026-10-30.md).
All four current-source style overlays were inspected; 77 focused tests pass.
Bold u/ų have supported local turns, but no real-font role is resolved yet.
Italic and Bold Italic expose the intended body counters while retaining missing,
competing or non-distinct neighbour evidence. Descenders and ogonek context remain
explicit omissions. Same-style and Italic comparisons are diagnostic only.

Stage 3 remains in progress. Next: local arm-to-stroke support and explicit
terminal/tail context before asserting exit/interior matches. Keep v/w unresolved
where rounded italic construction defeats a simple angular negative. Upper arches,
the historical bad-m-splice evaluation and independent-family accuracy remain
pending; do not move to repair solvers or smoothing.

## Local arm and terminal context — 2026-10-30

Implemented the next Stage 3 increment: direct five-section arm support,
shared-band comparison, bounded cap tracing back to a verified opposite boundary,
and explicit below-baseline context that withholds exit roles. Nested return
schema is v2. See
[`return-context-review-2026-10-30.md`](return-context-review-2026-10-30.md).
The pinned four-style run supports exits in Bold Italic u/и and Italic ш; real
interior roles remain unresolved. Refusal controls љ/u.sc/f_h/f_f_h retain their
limitations. Four focused overlays were inspected and 83 focused tests pass.

Next: same-role comparison using counter profiles, adjoining widths and terminal
context, excluding unresolved roles from positives. Include historical bad-splice
and v/w negatives and independent family evaluation. Tail attachment attribution
and upper arches remain unfinished; no repair solver or smoothing is authorised
by these observations.

## Same-role return retrieval — 2026-10-30

Implemented role-gated counter/arm/direction/cap comparisons with explicit
candidate, incompatible and unresolved decisions. See
[`return-matching-review-2026-10-30.md`](return-matching-review-2026-10-30.md).
The current four-style run finds one local candidate (Bold Italic u/и exits).
Reconstructed historical Italic/Bold Italic bad-m interior regions are withheld
as unresolved, not diagnosed as bad splices. Current v/w controls stay non-positive.
Inspected the current positive/control proof and both historical reconstructions;
96 focused tests pass, including a separately constructed rounded-cap family.

Next mechanism: upper arches with explicit entry/interior/exit neighbour context,
using the reconstructed bad-m case to test role diagnosis. Lower-return interior
coverage, tail attachment attribution and independent real-family evaluation
remain open. Stage 3 is not complete; retain these misses through reassessment
rather than advancing to bowls, repairs or general smoothing.

## Upper-arch roles and splice diagnosis — 2026-10-30

Implemented upper-counter candidates and shared horizontal ink-band topology,
with separate entry/interior/exit context and interior lower-return conflicts.
See [`upper-arch-review-2026-10-30.md`](upper-arch-review-2026-10-30.md).
Current Italic/Bold Italic n/m roles resolve; reconstructed historical bad-m now
has an explained middle-leg finding in both styles. Italic verifies a terminal
cap; Bold Italic instead has a return detour merging into the following stroke.
Normal n/m and u/v/w controls receive no conflict findings. Six overlays were
inspected and 112 focused tests pass.

This supplies topology evidence, not normal-width compatibility, ancestry or
positive upper-arch reuse recommendations. Upright serif roles, h's ascender
context and the extra upper entry projection remain unresolved. Next qualification
work is a region-labelled independent real-family corpus, retaining these misses
and lower-return/tail limitations. Stage 3 remains incomplete; no repair solver,
general smoothing or production changes follow from the two diagnosed cases.

## Independent-family evaluation pass — 2026-10-30

Completed a frozen-detector pass over 58 prelabelled regions in η/π/ω/ρ/r/s,
with π/ω/ρ/s held out from detector development and η/r treated as related
transfer probes. See
[`arch-family-evaluation-2026-10-30.md`](arch-family-evaluation-2026-10-30.md).
The held-out set has 10/12 detected turn regions, two misses, 18 candidate scope
mismatches and no splice-conflict warnings on its normal drawings. Italic π's exit
resolves; Bold Italic π's remains unresolved. Closed ρ bowls expose a missing
scope distinction. All labels and detector thresholds were held fixed.

Added region scoring with explicit misses, unresolved roles, ambiguous/unmatched
observations and stale-source/scope checks. 63 focused tests pass; four plain,
four labelled and eight detector proofs were inspected. This is a bounded
evaluation result, not qualification: independent positive upper roles and new
positive bad-splice examples remain absent.

Next: separate candidate extrema from supported anatomical scope, beginning with
closed-counter containment and then stem-versus-terminal context. Retain π's
sampling-window miss, tail/ascender/serif gaps and the upper-entry projection.
These inspected families become development evidence if used to tune the detector;
use fresh held-out families for the next accuracy claim. No repairs or smoothing.

2026-10-30 scope follow-up: closed-counter winding containment and explicit
terminal-versus-stem evidence now accompany raw candidates. All eight development
ρ observations are excluded from stem roles; terminal coverage remains partial.
See [counter scope review](counter-scope-review-2026-10-30.md). Next: extend terminal
evidence without treating failed stem support as terminal proof, and qualify on a
fresh holdout; existing family labels are development evidence now.

2026-10-30 terminal follow-up: reciprocal-cut closure now supplies terminal-scope
evidence without relaxing stem checks or changing roles. The fresh labelled c/e,
j and z evaluation retains 14 correct, two unresolved and six unobserved known-scope
regions; f/o are transfer controls. Component-only j is explicitly missed. See
[terminal evidence review](terminal-evidence-review-2026-10-30.md). Prioritize
component-aware observation with provenance; investigate heavy-terminal limits
separately. These evaluated families are development evidence for future tuning.

2026-10-30 component follow-up: counter reports now expand explicit components
with source-pinned contour/instance provenance and reject incomplete observation
fields. All six labelled j regions are observed; four resolve as terminal curves
and the two heavy lower hooks remain unresolved. Other replayed candidate records
are unchanged. See [component observation review](component-observation-review-2026-10-30.md).
Next: investigate heavy-terminal limits on development evidence, retaining close
negatives and positive closure requirements; fresh-family qualification remains open.

2026-10-30 heavy-terminal investigation: the eight reviewed heavy c/f/j/s arms
fail the 0.12 em span limit despite valid local closure. A 0.15 em trial admits
all eight but also the prior oversized-lobe control; no anatomical qualification
follows from this size sweep. Thresholds remain unchanged. Added explicit window
measurements and verified 213 existing cut contexts are otherwise identical;
93 focused tests pass. See [heavy-terminal limits](heavy-terminal-limits-review-2026-10-30.md).
Next: a region-labelled anatomical contrast set for broad terminal versus
nonterminal return/branch lobes, including attachment context and ambiguous cases,
before considering a larger or locally scaled window. Keep fresh families reserved
for qualification; no repair or smoothing.

2026-10-30 anatomical contrast pass: 54 prelabelled development regions now carry
108 left/right arm labels and separate attachment context. The 0.15 em trial
supports 23 labelled terminals versus 15 at baseline, with no promotions among
57 observed nonterminal arms; 16 absent arms, 12 ambiguous labels and 36 unlabelled
detections remain explicit. The historical Italic interior tongue stays locally
terminal, while Bold Italic's joined branch fails the opposing-contour check.
See [terminal anatomy contrast](terminal-anatomy-contrast-review-2026-10-30.md).
Next: pre-register that fixed morphology-only 0.15 em candidate and compare it
against baseline on fresh, provenance-separated base families, labelled before
exposure. Do not tune on the holdout or grant roles from terminal evidence. Current
thresholds remain unchanged; 107 focused tests pass. No repair/smoothing.

2026-10-30 fixed-window holdout: pre-registered the morphology-only 0.15 em
candidate and froze labels for a/t/k/x before detector exposure. Across four
styles, supported terminals increase from 17 to 20, with no promotions among
32 observed nonterminal arms. Sixteen nonterminal and four ambiguous arms remain
unobserved, including the selected branch junctions. Available provenance shows
no development-family ancestry overlap; undocumented reuse remains unknown.
See [terminal holdout review](terminal-holdout-review-2026-10-30.md).
All sixteen plain/labelled/baseline/trial proofs were inspected; 102 focused tests
pass. Default threshold remains 0.12 em. Next: expose a separately named opt-in
reciprocal-terminal policy, with role/normal-cap invariance checks and frozen
corpus replay. Missing branch observation still prevents general qualification;
no repairs or smoothing.

2026-10-31 opt-in terminal policy: exposed `wide-morphology` (0.15 em) separately
from the default reciprocal-terminal and normal-cap windows (both 0.12 em).
Experimental contexts retain baseline scope status; roles, caps, conflicts and
matches remain baseline decisions. See [terminal policy replay](terminal-policy-review-2026-10-31.md).
Next: investigate observation limits at the previously labelled but unobserved
branch junctions, retaining ambiguous regions and provenance. The development and
former holdout families are development evidence now; new anatomical accuracy
claims need fresh families. Stage 3 role/context gaps remain open; no repairs or
smoothing follow from the opt-in morphology policy.

2026-10-31 branch-observation investigation: all ten selected k/x regions have
local extrema. Nine fail the rounded-turn bend gate; the ambiguous Bold Italic
x merge fails shoulder rise first (0.07373 versus 0.08 em). Added separate
source-pinned discovery diagnostics and inspected four overlays; labels and
thresholds stay fixed. See [branch observation review](branch-observation-review-2026-10-31.md).
Next: a separate angular-junction observation channel, keeping rounded-return
acceptance fixed and short/ambiguous merges explicit, before testing terminal
closure at branches. These seeds supply no new branch anatomy or role evidence;
keep fresh families reserved for qualification. No repair or smoothing.

2026-10-31 angular observation pilot: added an opt-in separate angular-boundary
channel, retaining both arm paths and sampled counter clearance. Nine selected
regions reach the unchanged 0.08 em window; ambiguous Bold Italic x retains two
short arms and seven sections. Angular paths stop at cumulative reversal without
altering the rounded recognizer. Four enlarged and four whole-scope proofs were
inspected; all forty archived rounded reports replay exactly. See
[angular observation review](angular-observation-review-2026-10-31.md).
Next: evaluate reciprocal terminal closure on fully observed angular arms in this
separate scope, retaining both fixed policies, short/obstructed windows, ambiguous
labels, closed counters and broad-lobe controls. Closure failure does not prove
branch continuation; no roles, repairs or smoothing follow from arm visibility.
Fresh-family qualification remains open.

2026-10-31 angular terminal evaluation: optional closure now uses traced source
occurrences on complete angular windows; short/obstructed contexts are withheld.
Both fixed policies verify a stem-foot closure on Italic k's labelled nonterminal
arm (1 mismatch, 15 nonterminal arms not promoted). Uncertain x labels remain
unscored; Bold Italic x remains withheld. One wide-policy promotion on Bold Italic
a is outside frozen angular boxes and stays unlabelled. The broad-lobe control
retains its known wide-policy acceptance. See
[angular terminal review](angular-terminal-review-2026-10-31.md).
Next: attachment-context contrast for stem-foot versus free-terminal closure,
with adjoining-stroke evidence before any classification gate. Preserve the
mismatches and uncertainty; do not tune closure windows to hide them. Rounded
reports/scores remain unchanged; fresh-family qualification, roles and repair
acceptance are still open. No repair or smoothing.
