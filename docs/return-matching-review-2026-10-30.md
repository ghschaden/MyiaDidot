# Same-role return matching — 2026-10-30

The lower-return report now compares supported same-style roles. Current-source
retrieval finds one local candidate: the final exits of Bold Italic u and и.
The reconstructed historical bad-m interior regions and the v/w controls remain
non-positive. The historical failures are withheld as unresolved, not diagnosed
as incorrect interior splices by this lower-return recogniser.

## Matching contract

`relationships/return_matching.py` adds `matches` to the existing
`lower_returns` report, with the separate format `myiadidot-return-matches-v1`.
The existing `--lower-returns` CLI produces it in JSON and the HTML evidence.
Every cross-glyph local pair retains geometric IDs, source hashes, a decision
and reasons; supported comparisons also retain the measurements. Comparisons
within a glyph are excluded from retrieval, without changing its topology graph.

Decisions are `candidate`, `incompatible`, or `unresolved`. A candidate is a local
retrieval result, not ancestry, interchangeable whole outlines, design acceptance
or permission to repair. Both glyphs must have supported local geometry and the
same resolved interior/exit role and turn direction. Cross-style comparisons,
unknown roles, incomplete arm support and unresolved descender context cannot
become positive. Both exit caps must already have passed contour verification.

The geometric gate checks all of the following, preserving left/right sides:

| Measurement | Initial limit |
| --- | ---: |
| Eight counter-section widths, RMS difference | 0.008 em |
| Largest counter-section width difference | 0.015 em |
| Five local widths on each arm, RMS difference | 0.008 em |
| Largest relative arm-width difference | 15% |
| Each arm's attachment direction difference | 12 degrees |
| Exit-cap trace, 17 arc-fraction samples, RMS distance | 0.010 em |

Widths and cap coordinates are normalized by units per em, not fitted to each
other. Cap traces are translated to their observation shoulders, preserving
handedness and direction. No rotation, reflection, arbitrary width scaling or
best-fit outline transformation is used to turn a failure into a match. Limits
are reported as policy and are experimental retrieval thresholds, not design
acceptance criteria.

## Current-source evaluation

Main revision is `cef605f813e307acd419326bd6a4821cd5e10c64`. The four pinned
snapshots and 16-glyph scope are unchanged from the arm/context review. Every run
reports `source_preserved=true`; source and implementation hashes are in JSON.
Artifacts and the replay script are under
`build/glyph-review/return-matching-2026-10-30/`.

| Style | Candidate comparisons | Incompatible comparisons | Unresolved comparisons |
| --- | ---: | ---: | ---: |
| Regular | 0 | 0 | 6 |
| Italic | 0 | 0 | 338 |
| Bold | 0 | 0 | 6 |
| Bold Italic | 1 | 0 | 337 |

These are local cross-glyph pair counts, not independent labelled samples. The
many unresolved results reflect the preceding detector's coverage limitations;
they are not successful negative classifications. In particular, positive u/и
is within a related construction family and cannot establish independent-family
precision. No real-font recall or precision estimate is claimed.

The current Bold Italic u/и/n/m/v/w return overlay was opened and inspected.
Its matching exits show the same counter, adjacent strokes and short cap. The
n/m and v/w candidates retain missing local support or unresolved roles. Their
non-positive comparison results do not prove absence of an anatomical relation.

## Reconstructed historical negative

The original generated `Italic.json` and `BoldItalic.json` from the first grammar
trial are no longer present in this worktree. The original review records source
revision `e30747e339a18415e6a7c70fcb47ec7f13b55774`; those two UFOs were extracted
under this experiment's `historical/` directory. The retained `shape_grammar.py`
recipe fits n's shoulders and legs to m's stem positions. It was evaluated against
these old sources with the current geometry helpers to reconstruct `m.bad-splice`.
This is a reconstruction, not a claim of byte identity with the lost artifact.

The experiment retains the recipe JSON/hash, old source hash and generated
candidate UFO/hash. Neither old source snapshot nor production sources were
modified. The generated UFO is a separate build artifact, containing original n/m
and the additional unaccepted candidate glyph.

Both historical return overlays were opened and inspected. They reproduce the
misplaced n exit curl at m's middle leg and the inappropriate second-entry
projection described in the 2026-10-26 review. The experiment labels only the
left-of-final copied lower turn as an interior-placement negative; the final
exit is not automatically a negative because another region is bad.

| Historical style | Negative region comparisons | Result |
| --- | ---: | --- |
| Italic | 1 | unresolved; no positive recommendation |
| Bold Italic | 1 | unresolved; no positive recommendation |

The role gate therefore prevents a false positive on these two reconstructed
regions, but does **not** explain their wrong interior role from geometry alone.
Upper entry/arch reuse is outside this lower-return implementation. The controlled
role-mismatch test separately checks that a resolved exit cannot match an interior.
Do not report the two unresolved cases as correctly diagnosed bad splices.

## Validation and remaining work

96 focused tests pass through `make test` and the shared lock. Thirteen new cases
cover translated same-role geometry, counter/weight/direction/cap disagreement,
role mismatch, missing support/tail/cap evidence, cross-style refusal, em
normalization, and a separately constructed rounded-cap family held out from the
flat-cap development controls. The rounded-cap geometry is detected before
matching; both its positive translation and interior-role negative pass without
retuning the limits. It is a synthetic terminal family, not a blind real-font
family benchmark. Ruff and `git diff --check` pass.

Stage 3 remains experimental and incomplete. The next mechanism is upper arches
with entry/interior/exit neighbour context, using the reconstructed bad-m case
to test actual role diagnosis. Lower-return interior coverage, explicit tail
attachment attribution and independent real-family accuracy remain open. Keep
these omissions in the evaluation rather than lowering the support thresholds.
No production sources, generators, baselines, acceptance records or fonts were
changed. No smoothing, repair solver, production build, shaping or hinting run
was performed.
