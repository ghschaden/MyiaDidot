# Branch-observation limits — 2026-10-31

All ten previously unobserved k/x branch regions contain local extrema. Nine
fail the existing 25° rounded-turn angle gate. Bold Italic x's ambiguously labelled
central merge fails earlier: its two arms rise only 151 units (0.07373 em), below
the 163.84 units (0.08 em) required for observation shoulders. This is a candidate
scope limitation before terminal evidence is evaluated. Widening the reciprocal
terminal window cannot recover these observations.

## Pinned scope and visual review

Used the original a/t/k/x corpus and the four frozen UFO snapshots from main
`cef605f813e307acd419326bd6a4821cd5e10c64`, with the source and label hashes from
`terminal-holdout-2026-10-30/inventory.json` and `label-digests.json`. No boxes,
labels, policy thresholds or source outlines changed. The former holdout is now
development evidence; this is an explanation of its omissions, not fresh accuracy
qualification.

The selected subset is eight interior-connection regions (sixteen nonterminal
arm labels) and two uncertain x regions (four ambiguous arm labels). Four source
outline proofs show the original boxes and numbered rejected extrema, with focused
glyph panels. All four were inspected:

- [Regular branches](../build/glyph-review/branch-observation-2026-10-31/Regular/branches.svg)
- [Italic branches](../build/glyph-review/branch-observation-2026-10-31/Italic/branches.svg)
- [Bold branches](../build/glyph-review/branch-observation-2026-10-31/Bold/branches.svg)
- [Bold Italic branches](../build/glyph-review/branch-observation-2026-10-31/BoldItalic/branches.svg)

The upright x markers lie at opposing angular crossing boundaries; k markers
lie where the lower leg meets the stem. Italic k has a similar angular junction
below its ball-bearing upper branch. The italic x boxes contain merging central
arms, as originally labelled; neither is reclassified as nonterminal. These are
source-outline observations, with no new shaping, hinting or design-acceptance
claim.

| Style | Region | First failed gate | Deskewed bend |
| --- | --- | --- | ---: |
| Regular | k-branch | Rounded bend | 90.00° |
| Regular | x-upper | Rounded bend | 112.12° |
| Regular | x-lower | Rounded bend | 111.89° |
| Italic | k-branch | Rounded bend | 88.95° |
| Italic | x-branch (ambiguous) | Rounded bend | 106.46° |
| Bold | k-branch | Rounded bend | 90.00° |
| Bold | x-upper | Rounded bend | 109.65° |
| Bold | x-lower | Rounded bend | 109.37° |
| Bold Italic | k-branch | Rounded bend | 88.93° |
| Bold Italic | x-branch (ambiguous) | Shoulder rise | 111.67° measured; angle gate not reached |

Every angular rejection reaches both observation shoulders. Bold Italic x's
measured bend also exceeds 25°, but this is not its executed rejection gate.
Later opening, clearance and terminal tests were not reached. Bend is the local
change of direction on the flattened, deskewed boundary, not a claim about
anatomical branch angle or a width-normal measurement.

## Diagnostic implementation

`lower_returns(..., diagnostics=list)` and `upper_arches(..., diagnostics=list)`
optionally retain all plateau/point extrema examined by discovery, including
ink-side refusals omitted from the ordinary relationship report. Records contain
the first failed gate, position, contour, and measured bend, partial arm rise,
opening or completed clearance-section count when available. Upper observations
restore positions from reflection to the deskewed font frame.

`relationships.candidate_diagnostics.candidate_diagnostics(font, names,
source_sha256)` wraps these traces with source-pinned contour/component origins,
seed IDs, observation completeness, policy and coordinate metadata. Its caller
must verify the source snapshot. It produces a separate diagnostics v1 sidecar;
rejected seeds are never promoted into relationship results or terminal-arm
evidence. A local box without an extremum remains unobserved. Incomplete component
fields withhold traces and retain their issues.

## Validation and artifacts

All generated artifacts are under
`build/glyph-review/branch-observation-2026-10-31/`: `investigate.py`, source-pinned
`validation.json`, `summary.json`, per-style diagnostics and region explanations,
four SVG/PNG proofs, and test logs. Source hashes and frozen label hashes are
checked before analysis and source preservation afterward.

`replay.py`, `replay.log` and `replay-validation.json` additionally verify exact
equality of all forty nested reports across both policies and all ten original
development/former-holdout corpus/style entries, including historical bad-splice
reconstructions. Every field remains unchanged, including all 216 terminal-arm
contexts, roles, conflicts, scope, matches and omissions.

182 focused tests passed through `make test` and its shared six-worker lock.
New controls cover angular rejection, partial shoulder rises, interrupted
clearances, reflected coordinates, component provenance, incomplete observation,
and equality with tracing on/off under both terminal policies and geometric
transformations. Ruff on the touched Python files and `git diff --check` pass.
The initial investigation comparison omitted paired-stem inputs and exposed a
scope difference in Italic t; replay now supplies the archived pairs, matching the
actual report layer. No threshold change was needed.

Production UFOs, generators and test baselines remain unchanged. No production
font build, shaping/hinting check, full suite, reproduction, commit or push ran.

## Next mechanism

A separate angular-junction observation channel is needed to test terminal versus
continuing-arm evidence at these branches. Keep rounded-return acceptance fixed;
retain branch traces as a distinct scope with their attachment context. Establish
arm observation at angular corners and short merges before evaluating reciprocal
closure there, keeping uncertain x labels and synthetic broad-lobe controls.
An angular seed alone proves neither branch anatomy nor a valid stem role. Any
anatomical accuracy claim after development needs fresh, provenance-separated
families. Repairs and smoothing remain outside this task.
