# Arch and return family evaluation — 2026-10-30

The fixed detector finds useful new lower turns, but does not yet distinguish
open stem connections from closed bowls and terminal curves reliably at the
candidate stage. No bad-splice warnings were emitted on the normal drawings in
this corpus. That does not qualify bad-splice recall or general repair guidance.

## Corpus and independence

58 regions were labelled across η, π, ω, ρ, r and s in four styles, using the
same frozen main sources at `cef605f813e307acd419326bd6a4821cd5e10c64`.
Source hashes are the ones recorded in the earlier current-source evaluation.
Four plain source proofs were inspected and the region manifests written **before
running the detector**. Labels and their file hashes were retained unchanged
through scoring; no threshold or recogniser changes were made. The previous
upper-arch report's implementation files were checked against current files:
all hashes agree (`frozen-detector-verification.json`).

The four new anatomical families π/ω/ρ/s are held out from detector development
for this pass. η and r are conservatively grouped as n-like transfer probes,
not independent validation of the entry mechanism. Their component and builtFrom
records contain no ancestry, but missing metadata does not establish unrelated
outlines. The italic glyphs share the recorded Old Standard source. The four
styles are correlated observations, not four independent families.

These are single-reviewer anatomical labels made by the assistant, not user
acceptance or independently adjudicated ground truth. `present` means a target
local counter turn under the chosen anatomical scope; it does not promise that
the current sampling window can recognise it. `absent` means the region is a
scope control, not that the drawing is defective. ω's two open lower lobe floors
are positive turn candidates with no presumed stem-return roles. Closed ρ bowls
and s's bowl-to-terminal curves are scope negatives. This distinction is an
explicit anatomical hypothesis; counts are not universal precision estimates.

The corpus contains 12 positive and 32 negative held-out candidate regions,
plus 14 transfer regions. Only π's right return has a held-out gold exit role.
The upper positive roles are transfer cases: **independent positive upper-role
qualification remains open**. All 24 glyph/style drawings are labelled as having
no misplaced interior terminal. There are no new positive bad-splice examples,
so this pass measures false warning exposure, not defect recall.

## Results with fixed labels and policy

| Style | Held-out turns detected / labelled | Missed turns | Out-of-scope candidates / negative regions | π exit role |
| --- | ---: | ---: | ---: | --- |
| Regular | 2 / 3 | 1 | 4 / 8 | unobserved |
| Italic | 3 / 3 | 0 | 5 / 8 | correct |
| Bold | 2 / 3 | 1 | 4 / 8 | unobserved |
| Bold Italic | 3 / 3 | 0 | 5 / 8 | unresolved |

All 58 region assignments were unambiguous. No detections fell outside the
labelled boxes. That only describes this finite corpus; the evaluator retains
both cases instead of silently dropping them when they occur.

- **π:** Italic has a supported exit. Bold Italic finds the same anatomical
  turn and verifies a cap, but the fifth right-arm section encounters an opposite
  corner. Its role correctly remains unresolved under the existing policy.
  Regular and Bold miss the positive right return because both arms do not reach
  the fixed 0.08 em observation shoulders. The omission is explicit, not scored
  as successful refusal. The italic left end of the roof also yields an unresolved
  upper candidate: a bar/terminal scope mismatch, not a mistaken resolved role.
- **ω:** both lower floors are found in all four styles. Their roles remain
  unresolved and were not assigned a gold entry/interior/exit role. The intentional
  central loop produces no splice-conflict finding. No upper candidate is found
  in either top lobe.
- **ρ:** the closed bowl yields both an upper and a lower candidate in every
  style. Their roles remain unresolved. This exposes the missing closed-counter
  distinction in an implementation described as an open-counter pilot.
- **s:** both terminal-connected bowl regions yield unresolved candidates in
  every style. Local extrema and clearance samples are real, but do not establish
  the intended stem-connection anatomy. These eight observations are recorded as
  scope mismatches, not eight confident wrong role assignments.
- **η/r transfer probes:** eight of ten positive regions are detected; the two
  upright η entry regions are missed. Three labelled entry roles resolve correctly,
  one is unresolved and two are unobserved. Three of four r ball-terminal controls
  yield out-of-scope candidates. η's descender-bearing body arch stays unresolved;
  resemblance to n is not converted into a capped exit.

There are **zero splice-conflict findings** across these 24 normal glyph/style
observations, and no wrong resolved gold roles. There are nevertheless 18 held-out
candidate scope mismatches, two held-out misses and an unresolved held-out exit.
The absence of confident mistakes must not erase these coverage limitations.
No positive reuse recommendation is established by these candidate counts.

## Reusable evaluator and artifacts

`scripts/relationships/region_evaluation.py` scores source-pinned region manifests
against saved `upper_arches` and `lower_returns` reports. Boxes use original font
coordinates; deskewing is reversed before assigning crowns, floors and conflict
locations. It rejects stale/unpreserved sources, incomplete detector scope, invalid
labels/boxes, duplicate IDs and within-corpus family leakage. Missing, multiple,
ambiguous, unmatched and out-of-scope observations remain separate outcomes.
Unknown gold roles are excluded from role accuracy. Expected positive conflicts
that are not found remain explicit misses.

Artifacts are under `build/glyph-review/arch-family-evaluation-2026-10-30/`:
`index.html`, `inventory.json`, `evaluation.json`, the frozen implementation check,
and per-style `corpus.json`, `evaluation.json`, plain/labelled proofs and full
detector reports. Reports retain source and detector implementation hashes;
scored results additionally retain the evaluator hash and corpus digest.

Replay the detector and scoring, preserving the existing labels:

```sh
.venv/bin/python -I build/glyph-review/arch-family-evaluation-2026-10-30/evaluate.py
.venv/bin/python -I build/glyph-review/arch-family-evaluation-2026-10-30/score.py
```

`prepare.py` and `label.py` preserve the original preparation and annotation recipe;
they are not needed to rescore. `score.py` can independently rescore saved detector
reports. All four plain proofs, four labelled proofs and eight detector overlays
were opened and inspected. All four detector runs report `source_preserved=true`.
These are source-outline observations, not compiled shaping or hinted rendering.

63 focused tests pass through `make test` and the shared six-worker lock, including
16 new evaluator tests. They cover misses, unresolved versus wrong roles, scope
negatives, unlabelled and ambiguous assignments, coordinate restoration, false and
missed conflicts, stale sources, incomplete scope and family leakage. Ruff and
`git diff --check` pass. No full suite, reproduction or font build was run.
Production sources, generators, baselines and acceptance records are unchanged.

## Next mechanism

Before broadening role claims or adding repairs, distinguish **candidate geometry
from supported anatomical scope**. Start with closed-counter containment (ρ), then
explicit stem-versus-terminal support (s/r/π). Keep the raw candidate evidence and
unsupported reason visible. Separately retain π's fixed-window miss and heavy-arm
corner refusal; neither justifies loosening thresholds in this evaluation.

These families are now inspected development evidence for future changes. A
subsequent tuned detector needs a fresh independent holdout. Serif/ascender roles,
upper-entry projection diagnosis, tail attribution and positive independent
upper-role/defect cases remain open. Stage 3 is not qualified for repair guidance.
