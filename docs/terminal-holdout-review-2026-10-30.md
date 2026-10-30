# Fixed terminal-window holdout — 2026-10-30

The pre-registered 0.15 em morphology-only trial supports 20/20 labelled terminal
arms, compared with 17/20 at 0.12 em. Neither policy promotes any of the 32
observed nonterminal arms. Sixteen nonterminal arms and four ambiguously labelled
arms are unobserved, including the selected branch junctions. This supports a
bounded terminal-morphology improvement, not general branch discrimination or
role qualification. The installed threshold remains 0.12 em.

## Frozen experiment

Sources are the four frozen UFOs from main
`cef605f813e307acd419326bd6a4821cd5e10c64`. Selected a/t/k/x in all four
styles: four base families, sixteen drawings, 36 regions and 72 arm labels.
Styles remain grouped by base family, not counted as independent samples.

Inspected all four plain proofs, wrote labels, inspected all four labelled proofs,
then froze their digests, the source inventory, evaluator and detector code in
`preregistration.json` before running the detector on these families. The sole
trial change is reciprocal-terminal `cap_width_em` from 0.12 to 0.15. All other
closure guards remain fixed. Normal caps, candidate geometry, roles, conflicts
and whole-candidate scope classifications remain baseline values; terminal
evidence does not grant roles. No labels or thresholds were tuned after exposure.

Labels are one assistant reviewer's anatomical judgements, not independent
adjudication or design acceptance. These families were held out from the terminal
tuning sequence; this does not claim that no repository tool has ever examined
their outlines. Component and `builtFrom` ancestry checks find no overlap with
development families. A supplementary check against the actual glyph names in
all preceding region corpora also finds no overlap. Missing provenance cannot
exclude undocumented historical reuse; the italic drawings share the Old Standard
source designation, and all styles share construction infrastructure.

## Results and inspected evidence

| Arm outcome | Baseline 0.12 em | Trial 0.15 em |
| --- | ---: | ---: |
| Supported labelled terminal | 17 | 20 |
| Unresolved labelled terminal | 3 | 0 |
| Observed nonterminal not promoted | 32 | 32 |
| Terminal evidence on labelled nonterminal | 0 | 0 |
| Unobserved labelled nonterminal | 16 | 16 |
| Unobserved ambiguously labelled arm | 4 | 4 |

The three changes are Bold a's upper left ball and Bold Italic x's upper right
and lower left balls. All eight baseline/trial overlays were inspected. The new
purple closure traces follow these free balls; the corresponding continuing arms
remain non-positive. Regular and Italic results are unchanged. There are no
unmatched detections or ambiguous region assignments in this selected scope.

The observed negative evidence covers continuing arms, including closed a bowls
and the continuing sides of the t/k/x turns. Upright k/x junctions, italic k's
central branch and italic x's ambiguously labelled central merging region are
unobserved. Their absence is not successful terminal discrimination. Thus this
pass does not independently resolve the broad-lobe-versus-branch concern exposed
by the earlier oversized synthetic lobe. The historical interior tongue also
remains a reminder that valid terminal morphology need not be a valid exit.

## Artifacts and checks

All generated files are under
`build/glyph-review/terminal-holdout-2026-10-30/`:

- `prepare.py`, `plain.py`, source inventory and `provenance-audit.json`.
- `label.py`, four `corpus.json` files, `label-digests.json`, plain/labelled proofs.
- `preregister.py`, `preregistration.json`, `evaluate.py`, `evaluation.log`.
- Per-style baseline reports, trial reports and both arm evaluations;
  aggregate `summary.json` and eight baseline/trial overlays.
- `validate.py`, `validation.json` and `tests.log`.

All 39 eligible reciprocal contexts replay exactly at baseline before widening.
Final validation checks frozen hashes, source preservation and exact equality of
every report field other than reciprocal-terminal contexts. An initial test
command named a nonexistent region-test file and collected no tests; after
correcting the filename, 102 focused tests passed through `make test` and its
shared six-worker lock. `git diff --check` passed. No detector code, source,
generator, baseline or installed threshold changed in this pass. No font build,
shaping/hinting test, full suite, reproduction, commit or push was performed.

## Next task

Separate reciprocal-terminal policy from normal-cap policy explicitly, exposing
the reviewed 0.15 em choice as an opt-in morphology-only experiment. Preserve the
0.12 default, add checks that selecting the experiment cannot change roles or
normal-cap acceptance, and replay the pinned development and holdout corpora.
Keep the missing branch observations explicit; investigate their observation
limits separately before claiming branch discrimination. These holdout results
must not be reused as fresh evidence after tuning on them. Stage 3 role coverage,
tail/ascender/serif context and repair qualification remain unfinished.
