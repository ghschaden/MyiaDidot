# Opt-in reciprocal-terminal policy — 2026-10-31

The reviewed 0.15 em reciprocal-terminal span window is available as
`--reciprocal-terminal-policy wide-morphology`. The default remains `baseline`
at 0.12 em. Normal caps retain their separate 0.12 em window. This completes the
implementation task following the
[fixed-window evaluation](terminal-holdout-review-2026-10-30.md).

## Behavior and boundaries

Named policies now carry explicit reciprocal-terminal limits, independent of
`CONTEXT_POLICY`. Both keep the existing trace/rise limits and closure guards.
The Python report and observation APIs accept `terminal_policy`; invalid names
fail before observation, including empty scopes. Each nested report records its
selected policy name and limits.

Experimental terminal contexts also retain `baseline_status`. Whole-candidate
anatomical scope uses this baseline evidence, preserving the morphology-only
experiment evaluated previously. Roles, normal-cap acceptance, conflicts and
return matching use their existing evidence. The terminal-arm evaluator and
purple terminal traces consume the selected reciprocal morphology. New terminal
support therefore does not create an exit, interior connection or reuse match.

The known oversized synthetic lobe is accepted by the wider window, as in the
original size sweep. Missing observation of labelled branch junctions remains
an unresolved coverage limitation. This implementation provides no new anatomical
qualification, repair recommendation or design acceptance.

## Frozen replay

Replayed the existing development anatomical contrast and former holdout corpora
on their original source snapshots, including both historical bad-m reconstructions.
Source revision is main `cef605f813e307acd419326bd6a4821cd5e10c64` for the four
current styles; historical reconstruction hashes are retained in the inventory.
Labels and source hashes are checked against the original inventories. No labels,
thresholds or family selections were changed. These families are now development
evidence; this replay is regression verification, not another held-out accuracy
claim.

For every replayed drawing, baseline terminal contexts reproduce the archived
contexts exactly. Opt-in terminal contexts reproduce the archived 0.15 em trial
exactly after removing the new `baseline_status` metadata. Baseline and opt-in
terminal-arm scores reproduce the original evaluations. All other fields in both
nested reports match baseline and archived reports, except selected policy
metadata: candidate geometry, observation provenance, omissions, normal caps,
roles, scope, conflicts and matches remain identical.

All 216 arm contexts across ten corpus/style entries replay exactly. Aggregate
terminal-arm outcomes reproduce the previous results:

| Outcome | Development baseline / opt-in | Former holdout baseline / opt-in |
| --- | ---: | ---: |
| Supported labelled terminal | 15 / 23 | 17 / 20 |
| Unresolved labelled terminal | 8 / 0 | 3 / 0 |
| Observed nonterminal not promoted | 57 / 57 | 32 / 32 |
| Terminal evidence on labelled nonterminal | 0 / 0 | 0 / 0 |
| Unobserved arms | 16 / 16 | 20 / 20 |
| Unscored ambiguous anatomy | 12 / 12 | 0 / 0 |

The former holdout's unobserved arms include sixteen nonterminal and four
ambiguous labels. Development retains 36 unlabelled detections. These omissions
and unscored cases do not count as successful discrimination.

## Validation and artifacts

Artifacts are under `build/glyph-review/terminal-policy-2026-10-31/`:
`replay.py`, `replay.log`, `validation.json`, `summary.json`, per-style baseline
and opt-in reports, evaluations and generated proofs. The replay asserts source
preservation and frozen label hashes. Existing inspected proofs remain the visual
evidence; this implementation pass makes no new visual design judgement.

165 focused tests passed via `make test` and its shared six-worker lock. Tests
cover reversed terminal contours, retained closure limits, rejected unknown
policies, and upper/lower invariance across normal, detoured, uncapped and exit
contexts with reversal, shear and subdivision controls. The first test invocation
included nonexistent filenames and collected no tests; the corrected run and
expanded related checks passed. Ruff on the changed Python files and
`git diff --check` pass. No full suite, production build, reproduction, commit or
push was performed. Production UFOs, generators and test baselines are unchanged.

Next work is observation at the previously labelled but unobserved branch
junctions, with attachment context and ambiguity retained. Stage 3's role,
tail/ascender/serif coverage and repair qualification remain unfinished.
