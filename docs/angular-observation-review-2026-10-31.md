# Angular-boundary arm pilot — 2026-10-31

The separate angular observer retains all ten selected k/x regions. Nine have
both arms reaching the unchanged 0.08 em window and eight sampled clear counter
sections. Bold Italic x retains two partial arms and seven sections; its merge
remains unresolved at 0.07373 em. All eight labelled nonterminal regions have
visible arms. Italic x also has visible arms, but its anatomical labels remain
ambiguous. Arm visibility does not establish a branch, terminal or attachment role.

This completes the observation mechanism queued by the
[branch investigation](branch-observation-review-2026-10-31.md). Terminal closure
at angular arms remains a separate next task.

## Separate scope and implementation

`--angular-junctions` adds an optional `angular_junctions` report and `angular.svg`
proof to the existing read-only relationship CLI. It uses `--boundary-glyphs`
as its scope when supplied, otherwise all glyphs. Python callers can use
`run(..., angular=True)`, `angular_report(font, report, names)` or
`angular_observations(contours, em, slant=0)`. Normal runs have no extra report
field. The HTML index links the angular proof and its JSON evidence.

The observer consumes inward extrema whose bend exceeds the rounded-turn limit,
including seeds rejected before the bend gate by insufficient shoulder rise.
Diagnostic records now retain both contour paths, source arc starts/directions,
achieved rise and stop reasons even when a shoulder is missing. Upper reflection
restores points, paths, sections and containment probes to the deskewed font frame.
Source-pinned contour/component provenance and observation completeness accompany
the report. Components are expanded without Boolean union.

This channel keeps the existing 0.08 em rise, 0.003 em backtrack allowance,
0.015 em final opening and eight-section/nine-interior-sample clearance policy.
The angular channel bounds backtracking relative to the maximum rise reached by
the arm. This is separate from the rounded recognizer's existing per-edge test.
An enlarged proof exposed partial Bold Italic x paths travelling beyond the merge
toward free ends under that per-edge test; cumulative reversal now stops this
observer near the first turn. The rounded recognizer is unchanged. Both short
arms and their measured clearances remain in the angular report.

`visible-angular-arms` means full window reach, opening and sampled clearance
only. `unresolved` retains short, obstructed or narrow contexts and explicit
failure reasons. Closed-counter containment remains explicit even when its
angular arms are visible. Every reported role is unresolved and terminal evidence
is `not-evaluated`; there are no ancestry, reuse, repair or design conclusions.

## Pinned evaluation and inspected proofs

Used the unchanged a/t/k/x labels and four source snapshots from main
`cef605f813e307acd419326bd6a4821cd5e10c64`. Source and label hashes are verified
against the original inventories before analysis and sources checked afterward.
These families are development evidence. No boxes, attachment labels or ambiguous
anatomical judgements were changed; this is not fresh-family qualification.

| Style | Selected regions | Visible angular arms | Partial/unresolved |
| --- | ---: | ---: | ---: |
| Regular | 3 | 3 | 0 |
| Italic | 2 | 2 | 0 |
| Bold | 3 | 3 | 0 |
| Bold Italic | 2 | 1 | 1 |

The ten regions comprise eight interior-connection regions with sixteen
nonterminal arm labels and two uncertain x regions with four ambiguous arm
labels. No terminal/nonterminal prediction is made for any arm. Across the whole
a/t/k/x scope, 22 angular observations are retained, twelve outside these selected
branch boxes. They include the other sides of k junctions and a/x attachments;
they are not counted as branch successes or terminal-discrimination negatives.

Four enlarged branch proofs use equal em scale, showing the original frozen
boxes, cyan contour paths, pink clearance sections, green completed-window
endpoints and orange partial endpoints. All four and all four whole-scope proofs
were inspected. The final Bold Italic proof was inspected again after bounding
cumulative reversal:

- [Regular](../build/glyph-review/angular-observation-2026-10-31/Regular/focused.svg)
- [Italic](../build/glyph-review/angular-observation-2026-10-31/Italic/focused.svg)
- [Bold](../build/glyph-review/angular-observation-2026-10-31/Bold/focused.svg)
- [Bold Italic](../build/glyph-review/angular-observation-2026-10-31/BoldItalic/focused.svg)

The boxes label extrema, not the entire arm observation window; some paths extend
outside them. These are source-outline checks with no compiled shaping or hinted
rendering claim.

## Checks and artifacts

197 focused tests passed through `make test` and its shared six-worker lock.
Controls cover known V-arm positions/clearances, contour reversal/start changes,
shear, subdivision, reflection, short merges, interrupted white intervals,
closed angular counters, component provenance, incomplete fields and invalid
frames. A gradual-reversal control verifies that many individually small steps
cannot lead into a remote lobe. The optional CLI channel leaves all pre-existing
report fields exactly equal in a synthetic integration test.

Both terminal policies' forty archived lower/upper reports replay exactly across
the ten original development/former-holdout entries, including historical bad-m
reconstructions: all 216 terminal-arm contexts, roles, scope, conflicts, matches
and omissions remain unchanged. Ruff on changed Python files and
`git diff --check` pass. Initial tests exposed two fixture/assertion mistakes
(anisotropic scaling removed the intended angular seed; a point was compared as
a tuple rather than the report's list). Both were corrected without relaxing
observation requirements.

Artifacts are under `build/glyph-review/angular-observation-2026-10-31/`:
`evaluate.py`, `evaluation.log`, per-style reports/region records, `summary.json`,
`validation.json`, `proofs.py`, focused and whole-scope SVG/PNG proofs,
`replay.py`, `replay-validation.json`, `replay.log`, `tests.log` and implementation
hashes. Production sources, generators and test baselines are unchanged. No full
suite, production font build, shaping/hinting check, reproduction, commit or push
was performed.

## Next task

Test reciprocal terminal closure as explicitly separate morphology on the fully
observed angular arms. Preserve the fixed baseline and opt-in windows, source
arc direction and reflected coordinates. Withhold closure evaluation for short
or obstructed windows; retain uncertain x labels, closed counters and the known
broad-lobe synthetic control. Absence of terminal closure does not prove a
continuing branch. Do not grant roles or tune thresholds to turn these development
cases into successes. Any anatomical qualification needs new independent families;
repair solvers and smoothing remain deferred.
