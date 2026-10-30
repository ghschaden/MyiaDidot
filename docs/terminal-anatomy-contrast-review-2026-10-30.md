# Terminal anatomy and attachment contrast — 2026-10-30

Built a source-pinned development corpus with 54 regions and 108 arm labels.
It distinguishes local terminal morphology from attachment function. The existing
0.15 em trial supports all 23 labelled terminal arms, without promoting any of
57 observed labelled nonterminal arms. It also supports the free tongue in the
historical Italic middle-leg splice: terminal appearance does not establish a
valid exit connection. The installed experimental detector remains at 0.12 em.

## Labels and source scope

Plain source proofs were rendered and inspected before writing this pass's labels.
The labelled proofs were then inspected, and label-file digests fixed before the
replay. These families and their previous detector results were already exposed
during development: this is neither a blind study nor an independent holdout.
All labels are assistant judgements from one reviewer, not user acceptance or
independent adjudication. No labels or detector thresholds were changed after
seeing this replay's results.

Current sources remain the four frozen UFOs from main
`cef605f813e307acd419326bd6a4821cd5e10c64`. The two historical source sets are the
previously reconstructed bad-m artifacts based on
`e30747e339a18415e6a7c70fcb47ec7f13b55774`, not new reconstructions.

Current glyphs: c/f/j/s/n/m/u/v/w in all four styles. Historical glyphs: normal m
and m.bad-splice in Italic/Bold Italic. This is 40 glyph/source drawings, with
n/m grouped together and u/v/w conservatively grouped together for family
accounting. No fresh families were consumed for qualification.

Each region specifies an upper-arch or lower-return extremum box in original font
coordinates and two labels, `terminal_arms.left/right`:

- `terminal`: a local free-ending lobe, not merely a distant endpoint somewhere
  along the same stem.
- `nonterminal`: a continuing stem, body connection or branch in the local region.
- `ambiguous`: local extent or anatomy deliberately left unadjudicated.

The separate `attachment_context` label is free-end, stem-connection,
interior-connection or uncertain. It describes the labelled construction context;
it is not a detector-predicted role. Italic v/w lower regions carry ambiguous arm
labels. Upright angular v/w regions and normal historical middle stems deliberately
have no expected rounded-return observation.

There are 23 terminal, 73 nonterminal and 12 ambiguous arm labels. The positive
lobes cover the heavy c/f/j/s cases and lighter counterparts, italic u exits and
the historical Italic interior tongue. The negatives include opposite continuing
arms, n/m body arches, u body returns and the joined historical Bold Italic curl.
Many arms and styles are correlated; these counts are not independent samples.

## Scoring without converting omissions into successes

Added `relationships/terminal_evaluation.py`. `evaluate_terminal_arms` reuses the
existing region scorer's source hashes, scope/split checks, coordinate restoration
and ambiguous-assignment handling. It then scores the two arms independently.
Normal verified caps and reciprocal-cut closures remain distinct evidence fields;
either can supply positive local terminal evidence. Attachment labels never become
predicted entry/interior/exit roles.

| Arm outcome | Baseline 0.12 em | Trial 0.15 em |
| --- | ---: | ---: |
| Supported labelled terminal | 15 | 23 |
| Unresolved labelled terminal | 8 | 0 |
| Observed nonterminal not promoted | 57 | 57 |
| Terminal evidence on labelled nonterminal | 0 | 0 |
| Unobserved labelled arm | 16 | 16 |
| Ambiguous anatomy, unscored | 12 | 12 |

The 16 unobserved arms are the twelve arms of upright angular v/w controls and
four arms of normal historical middle-stem controls. Their absence is retained;
it is not counted as successful terminal discrimination. `not-promoted` likewise
means no positive terminal evidence, not proof of nonterminal anatomy.
Thirty-six detections outside the selected regions remain in the nested region
evaluations. They are not counted as correctly classified or silently discarded.
There were no ambiguous region assignments in this replay.

The trial replays the previous pinned per-arm 0.15 em sweep, after verifying
source identity and exact baseline terminal contexts. It does not recompute or
replace baseline role, conflict or whole-candidate scope classifications. The
trial evaluation explicitly records that restricted policy and purpose.

## What the attachment contrast establishes

The historical Italic middle curl has a short free tongue and positive local
closure at both limits (span 0.03369 em). Its labelled attachment is nevertheless
interior. A width cutoff cannot distinguish this from legitimate exit morphology;
role compatibility must remain a separate graph/context check. This agrees with
the earlier upper-arch conflict finding and does not invent a new repair target.

The Bold Italic historical tongue merges into the following stroke. Both local
arms remain unresolved because the opposing boundary belongs to another contour,
not because the width is too large. Increasing the terminal-width allowance does
not bypass that contour check. The plain and overlay proofs support this local
free-tongue versus joined-branch distinction in these two examples only.

The eight broad positive lobes are the same development examples used to choose
the 0.15 em trial. Their recovery is therefore expected and cannot qualify the
new threshold. This corpus adds explicit anatomical contrasts and accounting;
it does not establish general accuracy or authorize positive reuse/repair claims.

## Artifacts and validation

All files are under `build/glyph-review/terminal-anatomy-contrast-2026-10-30/`:

- `prepare.py`, `inventory.json`, six plain proofs.
- `label.py`, per-source `corpus.json`, `label-digests.json`, six labelled proofs.
- `frozen-implementation.json`, `evaluate.py`, six baseline reports and baseline/
  trial arm evaluations, aggregate `summary.json`.
- `label_proof.py`, `overlay.py`, six detector overlays, `tests.log`.

All six corrected plain proofs, six labelled proofs and six detector overlays
were opened and inspected. The initial plain proof scale clipped long descenders;
that rendering was corrected before label creation. These are source-outline
proofs, not compiled shaping/hinting or design acceptance.

All six runs preserve source hashes and verify frozen label/implementation hashes.
107 focused tests pass through `make test` and the shared six-worker lock.
Fourteen new scorer controls cover positive morphology at an interior attachment,
nonterminal promotion, missing/ambiguous/unreported evidence, normal-cap evidence,
stale sources, incomplete scope and invalid labels. Ruff and `git diff --check`
pass. No full suite, reproduction, font build, source edit, commit or push occurred.

## Next task

Pre-register the fixed 0.15 em reciprocal-terminal-only candidate, retaining all
other guards and the prohibition on using it for roles. Evaluate it against 0.12
em on fresh base families labelled before detector exposure, with independent
family assignment checked against available provenance. Include local branch and
return negatives, preserve ambiguous cases and do not tune on that holdout. This
is the next qualification experiment; the installed threshold stays unchanged
until that evidence has been reviewed. Tail/ascender/serif context, Stage 3 role
coverage and repair qualification remain incomplete.
