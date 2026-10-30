# Terminal closure evidence and fresh-set evaluation — 2026-10-30

Terminal scope now accepts a bounded contour closure through a reciprocal
horizontal ink interval. It recognizes curved/angled terminals that cannot supply
parallel-boundary stem sections. It does not grant stem support or change
entry/interior/exit roles. Existing cap windows and stem thresholds are unchanged.

## Mechanism and evidence

At each candidate shoulder, `relationships/terminal_context.py` finds the unique
horizontal ink side and its first opposite boundary. Both boundaries must belong
to the same contour, have unique opposite ink sides, and agree under a reverse
first-hit check. Interior samples must remain ink. The directed arm contour must
reach that exact opposite boundary within the existing 0.35 em trace, 0.16 em
height and 0.12 em width limits, rising at least 0.005 em above the cut. Every
flattened vertex is checked; the route may not drop below its cut. A long route
around the glyph, an unrelated contour, or failed stem checks is insufficient.

This evidence is recorded as `terminal_context`, including the cut, exact return
endpoint, trace, dimensions and refusal reason. Upper-arch coordinates are restored
from reflection. `terminal_policy` documents that the check is **not used for
roles**. Existing normal-section caps continue to govern role and splice checks;
the new closure only contributes to `anatomical_scope`. Closed-counter precedence
is unchanged. Purple traces and orange cuts show the new evidence on the focused
proofs; raw candidate paths remain blue.

This is a flattened-outline, bounded-lobe test. It does not recognize every
terminal type, attribute tails, infer ancestry or assess drawing quality.

## Development replay

The previous η/π/ω/ρ/r/s corpus was replayed against the frozen sources at
`cef605f813e307acd419326bd6a4821cd5e10c64`. All four runs preserve source hashes,
and their raw candidate identities, role assignments and conflict findings match
the prior counter-scope reports exactly.

- Both s curves now have terminal scope in Regular, Italic and Bold: six of eight
  candidates, compared with one previously. Bold Italic's two exceed the existing
  terminal-width limit and remain unresolved.
- The r ball-terminal candidates in Regular, Italic and Bold are now classified
  as terminal curves. Bold Italic's previously observed candidate is its entry
  curve, not its ball; no new ball candidate was manufactured.
- Closed ρ counters remain excluded. π's upright observation-window omissions and
  Bold Italic unresolved exit remain separate, unchanged limitations.

## Fresh labels and frozen detector

Plain proofs of c/e/f/j/o/z in all four styles were inspected before implementation.
44 region labels were then saved and hashed, with source identities and inventory.
The detector was frozen after development tests; every evaluation run verifies
its implementation hashes and the original label digests. Neither labels nor
thresholds were tuned after seeing these results.

The 32 held-out regions group c/e into one bowl family, j as a hook family and z
as an ornamental/diagonal control. Only 22 have a known anatomical-scope label;
upright j tops and z scope are intentionally unscored. The 12 f/o regions are
transfer controls: f was exposed through previous ligature work, and o tests the
existing closed-bowl mechanism. Styles are correlated. These are single-reviewer
assistant labels, not independently adjudicated ground truth or user acceptance.
In particular, the successful new positive terminal results are concentrated in
one c/e family; they do not establish broad family accuracy.

| Style | Held-out correct scope | Unresolved | Unobserved labelled region | Wrong resolved scope | Transfer correct / unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Regular | 4 | 0 | 1 | 0 | 3 / 0 |
| Italic | 4 | 0 | 2 | 0 | 3 / 0 |
| Bold | 3 | 1 | 1 | 0 | 2 / 1 |
| Bold Italic | 3 | 1 | 2 | 0 | 2 / 1 |

All c/e lower terminals resolve correctly. Regular/Italic c tops also resolve;
Bold/Bold Italic c tops exceed the width window. All four e eyes and eight o
observations are closed counters. The f transfer hooks follow the same light/heavy
split as c tops. All six labelled j regions are unobserved because j has component
outlines, which this detector explicitly does not expand. They remain coverage
misses, not successful refusals. Italic z yields additional terminal/unresolved
observations, but its scope labels were deliberately unknown and are not counted
as correct scope classifications.

The evaluator now scores optional anatomical-scope labels separately from raw
candidate outcomes. Correct classification of an out-of-scope curve does not erase
its raw candidate observation. Unknown labels, multiple observations, unobserved
regions and unresolved classifications remain distinct. No conflict findings were
emitted on the 24 normal glyph/style drawings; this does not measure defect recall.

## Artifacts and validation

All artifacts are under `build/glyph-review/terminal-evidence-2026-10-30/`:

- `plain.svg/png`, `inventory.json`, per-style `corpus.json`, `label-digests.json`.
- `frozen-implementation.json`, per-style `report/` and `evaluation.json`, aggregate
  `evaluation.json`; `evaluate.py` verifies hashes and replays scoring.
- `development-summary.json`, `development/`, `development.py` for the old corpus.
- `holdout-overlay.svg/png`, `development-overlay.svg/png`, and `render.py`.

The corrected plain proof and both focused overlays were opened and inspected.
They show source outlines, not compiled shaping or hinting. All eight detector
runs report source preservation. 80 focused tests pass through `make test` and
the shared six-worker lock, including the existing upper/lower role, bad-splice,
return matching and closed-counter controls. New tests cover angled terminal
closure, reversed winding, reflected evidence, excessive extent, wrong contour
direction, wrong reverse boundary, another contour, and separate scope scoring.
Ruff and `git diff --check` pass.

No production source, generator, baseline, acceptance record or repair solver
changed. No font build, full suite or reproduction was run. Next work should
address component-aware observation with preserved provenance, and separately
investigate heavy-terminal scale limits on development evidence. A new holdout
would be needed after tuning. Repair guidance remains unqualified.
