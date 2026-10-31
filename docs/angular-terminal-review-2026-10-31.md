# Terminal closure on angular arms — 2026-10-31

Both fixed policies verify closure on one of the sixteen frozen nonterminal arm
labels: the left arm of Italic k's branch region. Inspection shows the route
closing around the plain stem foot. It satisfies the local geometric window,
but does not establish a free terminal at the branch. The other fifteen labelled
nonterminal arms receive no closure evidence. This is an explicit morphology versus
anatomy mismatch, not qualification of terminal/branch discrimination.

The two uncertain x regions retain their four ambiguous arm labels. Italic x's
arms verify local closure but remain unscored anatomically; Bold Italic x's short
window withholds both tests. No roles, repairs or source changes follow.

## Opt-in implementation

`--angular-terminal-closure` enables angular observation and reciprocal closure
on complete windows. It uses `--reciprocal-terminal-policy baseline` (default,
0.12 em span) or `wide-morphology` (0.15 em); both keep the existing trace/rise
limits and all correspondence guards. For example:

```sh
.venv/bin/python -I scripts/shape_relationships.py \
  --angular-terminal-closure --reciprocal-terminal-policy baseline \
  --boundary-glyphs a k x --proof-glyphs a k x \
  --out build/glyph-review/angular-terminal-example
```

Python callers use `run(..., angular_terminals=True)` or supply
`terminal_policy='baseline'` / `'wide-morphology'` to `angular_report` or
`angular_observations`. Without a policy, angular observation v1 remains exactly
unchanged. Closure-enabled reports use `myiadidot-angular-observations-v2`,
recording the selected policy and per-arm `terminal_context`.

Only rows with complete arm reach, opening and sampled clearance are eligible.
Short, obstructed or narrow windows retain `not-evaluated` contexts and no window
pass claims. Eligible shoulders use the traced source arc occurrence plus signed
path length and the retained contour direction, rather than projection onto a
nearby outline. A source-occurrence inconsistency withholds evaluation. Upper
reflection restores section endpoints and full closure traces to the deskewed
font frame. Purple proof traces display verified closures.

The closure flag leaves angular candidate geometry, arm visibility, containment,
source identities and unresolved roles unchanged. Closed angular counters retain
containment; the synthetic counter refuses closure to a different contour. Normal
caps are not evaluated or combined with this evidence. Rounded observations and
scores remain separate.

`evaluate_angular_terminal_arms(corpus, report, em, slant)` reuses frozen region
validation and assignment accounting through a local angular-only projection.
Its output format is `myiadidot-angular-terminal-arm-evaluation-v1`. Source/scope
checks, ambiguous assignments, absent observations and unreported/withheld evidence
remain explicit. `terminal-on-nonterminal` retains the k mismatch; `not-promoted`
means no positive closure evidence, not proven branch continuation. The original
rounded evaluator is unchanged in behavior.

## Frozen development results and inspection

Used all four original a/t/k/x corpora and source snapshots from main
`cef605f813e307acd419326bd6a4821cd5e10c64`. Checked original label/source hashes
before analysis and source preservation afterward. Labels, boxes, thresholds and
attachment contexts were not changed. These families are development evidence;
there is no new held-out accuracy claim.

| Selected branch-arm outcome | Baseline | Wide morphology |
| --- | ---: | ---: |
| Closure on labelled nonterminal | 1 | 1 |
| Labelled nonterminal not promoted | 15 | 15 |
| Ambiguous arm label, unscored | 4 | 4 |

Of the ambiguous arms, two have verified closure and two are withheld for the
short window. The latter remain unscored rather than being counted as successful
negative discrimination. There are no labelled positive terminals in this selected
branch subset, so it cannot qualify terminal recall.

Italic k's stem-foot closure spans 0.07136 em, descends 0.13387 em from the
shoulder in the source frame, and follows a 0.33660 em contour route. All limits
pass at baseline; widening is not the cause of the mismatch. The inspected trace
uses both sides of the stem and its baseline edge, rather than the upper ball.

Across the whole a/t/k/x scope, all 22 angular observations remain: ten match the
selected branch regions and twelve are unmatched to the frozen boxes. One extra
policy promotion occurs outside those boxes: Bold Italic a's upper-oriented
boundary at y=188, left arm, has a 0.13389 em closure span. The baseline refuses
it and the wide policy verifies it. It remains unlabelled in this angular scope,
with no anatomical success/failure score. The evaluator also retains 52 original
arm labels with no angular observation; the separate rounded results are not
replaced by these angular scores.

Inspected all four enlarged branch proofs and five distinct whole-scope policy
proofs. Regular, Italic and Bold baseline/wide SVGs are byte-identical; Bold Italic
has the extra a closure. The enlarged proofs show the k mismatch and preserve both
uncertain x labels:

- [Regular](../build/glyph-review/angular-terminal-2026-10-31/Regular/focused.svg)
- [Italic k and x](../build/glyph-review/angular-terminal-2026-10-31/Italic/focused.svg)
- [Bold](../build/glyph-review/angular-terminal-2026-10-31/Bold/focused.svg)
- [Bold Italic](../build/glyph-review/angular-terminal-2026-10-31/BoldItalic/focused.svg)
- [Bold Italic wide policy, including a](../build/glyph-review/angular-terminal-2026-10-31/BoldItalic/wide-morphology.svg)

These are source-outline inspections, not compiled shaping, hinting or design
acceptance.

## Validation and artifacts

222 focused tests passed via `make test` and its shared six-worker lock. New
controls cover source-direction/arc correspondence under reversal, start changes,
subdivision, shear and reflection; verified closure on a known angular terminal;
withheld short/obstructed windows; closed counters; source-arc inconsistency;
independent arm scoring, ambiguity and stale-source rejection; and CLI/report
integration. Closure comparisons remain strict at window boundaries; positive
transformation controls use a width margin rather than claiming stable acceptance
exactly at a floating-point threshold.

The historical 0.14 em broad-lobe transfer control remains refused at baseline
and admitted by the wide policy, including reverse contours. This is a low-level
closure control, not a labelled anatomical branch. No guard or threshold was
loosened to reject or accept the k example.

All forty archived lower/upper reports and their arm scores replay exactly across
both policies and all ten original development/former-holdout entries, including
historical bad-m reconstructions. All 216 existing terminal-arm contexts remain
unchanged. Observation-only angular reports also replay exactly. Ruff on changed
Python files and `git diff --check` pass.

Artifacts are under `build/glyph-review/angular-terminal-2026-10-31/`:
`evaluate.py`, `evaluation.log`, implementation hashes, per-style/policy reports
and evaluations, `summary.json`, `validation.json`, focused and policy SVG/PNG
proofs, `proofs.py`, `replay.py`, `replay-validation.json`, `replay.log` and
`tests.log`. No full suite, production font build, shaping/hinting check,
reproduction, commit or push ran. Production UFOs, generators and test baselines
remain unchanged.

## Next element

Build an attachment-context contrast set separating stem-foot closure from a free
terminal at the observed junction. Keep the k mismatch, both uncertain x merges,
closed counters, the unlabelled a policy difference and the broad-lobe control
explicit. Establish the relevant adjoining stroke/attachment evidence before
adding a classification gate; failed closure does not prove continuation. Do not
adjust window thresholds to hide the mismatch. Fresh provenance-separated families
are required for later anatomical qualification. Repairs and smoothing remain
deferred.
