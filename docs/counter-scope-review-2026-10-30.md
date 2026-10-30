# Counter and terminal scope — 2026-10-30

Raw upper/lower curve candidates now carry a separate `anatomical_scope` record:
`closed-counter`, `terminal-curve`, `supported-stem-connection`, or `unresolved`.
This is observed construction evidence, not drawing acceptance or repair advice.

A white probe just inside the candidate floor is tested against the candidate
contour's winding region. Nonzero winding establishes enclosure independently
of contour direction. Upper candidates use the reflected test and restore probe
coordinates. A closed counter retains its paths, sections and neighbour evidence,
but cannot acquire a lower role, join the upper stem graph, or supply a terminal
conflict. The check does not establish that every other white region is open:
complex multi-contour enclosure and ambiguous topology remain unresolved.

A terminal curve requires the existing verified same-contour cap, with incomplete
stem-connection support. Failed section checks alone never imply a terminal.
Supported lower connections retain the existing global paired-stem or complete
local-band evidence. Upper connections use the existing shared-band/role evidence.
An observed terminal cap can coexist with a supported connection (an exit is the
obvious example); cap evidence remains separately visible. Neither scope support
nor a cap alone resolves a role or permits return matching.

Lower reports are now v3 and upper reports v2, with scope policy recorded. SVG
candidate labels display scope, JSON retains reasons and evidence, and region
evaluation preserves scope alongside its existing raw candidate outcomes. No
candidate thresholds, section tolerances or cap windows were loosened.

## Existing development corpus replay

Artifacts: `build/counter-scope/`, with `evaluate.py`, `summary.json`, and per-style
JSON/HTML/SVG reports. Sources remain the frozen main snapshot used by the earlier
family evaluation; all four reports have `source_preserved=true`.

- All eight upper/lower ρ candidates are `closed-counter`.
- Italic s has one `terminal-curve`; its other candidate remains unresolved.
- Bold Italic r has one `terminal-curve`.
- The other s/r terminal controls remain unresolved: the fixed cap window and
  required opposite-edge verification do not establish their terminal anatomy.
- ω floors remain unresolved. No new stem-role inference follows from their shape.
- π retains the upright fixed-window misses and Bold Italic unresolved exit role.
  A supported local turn is distinct from a resolved exit role.

This is a development replay, not a new independent holdout or a visual design
review. The raw scope mismatches in the earlier evaluation are not erased by
classifying candidates. Broad terminal recognition remains incomplete.

## Validation

68 focused tests pass through `make test` and its shared six-worker lock. New
controls cover closed bowls under reversed winding and shear, upper reflection,
closed-counter refusal despite nearby paired stems, and a verified short terminal
with insufficient stem-band support. Existing entry/interior/exit and bad-splice
controls continue to pass. Ruff and `git diff --check` pass.

No production sources, generators, baselines, acceptance records or repair solver
changed. No font build, full suite, reproduction, shaping or hinting run was needed
for this report-layer recognition change.
