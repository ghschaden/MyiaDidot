# Component-aware counter observation — 2026-10-30

Upper-arch and lower-return reports now expand explicit UFO components before
measuring the combined ink field. This closes the component-only j coverage gap
without changing thresholds, terminal windows or role policy. Production sources
and generators remain unchanged.

The read-only observation layer recursively composes affine transforms, preserves
winding, and records each contour's original glyph/index, component-instance index
path, composed transform and source hash. Nested report formats advance to lower
returns v4 and upper arches v3. Each report has an `observations` inventory; each
candidate has `contour_origin`. Indices refer to the expanded contour inventory.
Component lower-return neighbours are measured on that same expanded ink field;
`observed_strokes` retains their source-pinned records so graph references remain
inspectable. Core transition/reuse discovery retains its previous direct-outline
scope; this does not expand Stage 2 construction claims.

Missing references, cycles, excessive nesting, singular/nonfinite transforms and
open contours withhold the whole glyph observation with a reason. Otherwise a
partial ink field could manufacture a counter or a terminal closure. Expansion
uses the existing nonzero winding field, not Boolean union; coincident boundaries
and overlapping components can still produce unresolved correspondence. Explicit
component lineage establishes source geometry, not design compatibility or
unrecorded generator ancestry.

## Development replay

Replayed the existing c/e/f/j/o/z labels without edits against the frozen four-style
sources from main `cef605f813e307acd419326bd6a4821cd5e10c64`. Reports record source
and implementation hashes; label hashes are retained in `summary.json`. This is
now development evidence, not a fresh holdout or an independent accuracy claim.

| Style | j lower hook scope | j upper entry scope |
| --- | --- | --- |
| Regular | Terminal curve | No candidate; unscored upright serif |
| Italic | Terminal curve | Terminal curve |
| Bold | Unresolved | No candidate; unscored upright serif |
| Bold Italic | Unresolved | Terminal curve |

All six previously unobserved known-scope j regions are observed: four correctly
resolve as terminal curves, two remain unresolved. No j role is asserted. The
other glyphs' complete candidate records are identical to the previous replay,
apart from added provenance. All four source trees remain hash-identical.

The eight j overlays were opened and inspected in one combined proof. They show
the intended hook/entry regions; the heavy lower terminals remain unresolved.
The dot remains separate and receives no turn candidate. These are source-outline
observations, not compiled shaping, hinting or drawing acceptance.

Artifacts: `build/glyph-review/component-observation-2026-10-30/`, including
`evaluate.py`, `summary.json`, per-style reports and evaluations, `j-overlay.svg`
and `j-overlay.png`, and `tests.log`.

## Validation and next task

90 focused tests pass through `make test` and the shared six-worker lock. Controls
compare nested, translated, reflected and sheared component geometry against
explicitly drawn geometry, retain repeated/mixed instance paths, and withhold
incomplete observations. Existing counter, terminal, matching, upper/lower role
and region-scoring tests pass. Ruff and diff whitespace checks pass. No full
suite, reproduction or font build was run.

Next: investigate heavy-terminal limits separately on development evidence, with
positive closure evidence and close negatives before any threshold change. Tail,
ascender and serif context, paired-stem gaps and fresh-family qualification remain
open. No repair or smoothing follows from this observation increment.
