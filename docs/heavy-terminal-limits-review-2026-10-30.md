# Heavy-terminal window investigation — 2026-10-30

The heavy-terminal omissions are explained by the fixed horizontal extent limit,
not missing contour closure. Raising that limit from 0.12 to 0.15 em admits eight
reviewed terminal arms, but also the existing oversized-lobe control. The control
is a size-policy negative, not independently established anatomical ground truth.
This investigation therefore leaves all detector thresholds and role rules intact.

Reports now provide `terminal_context.window_checks`: measured font units and em,
maximum em, ratio to that maximum, excess units and maximum-pass status for each
measured trace length, rise and horizontal span. Rise additionally records its
strict minimum and minimum-pass status. Unmeasured checks are absent, not passes:
a failed reciprocal cut has none; a trace-window refusal has only trace evidence.
The policy identifies this additive diagnostic contract as
`terminal-window-checks-v1`. Reflection preserves these scalar diagnostics.

## Pinned development experiment

The current sources are the unchanged frozen snapshots from main
`cef605f813e307acd419326bd6a4821cd5e10c64`. The two historical bad-m reconstructions
are the same artifacts used by the upper-arch review, from historical revision
`e30747e339a18415e6a7c70fcb47ec7f13b55774`; no reconstruction was regenerated.
Source and implementation hashes are stored per run.

Scope: c/e/f/j/o/z/s/r/n/h/m/u/v/w in four styles, plus n/m/m.bad-splice in the
two historical italic styles: 62 glyph/style drawings and 242 observed arms.
These are development examples. No fresh holdout or new accuracy claim is made.

Only the reciprocal-cut terminal function's horizontal span limit was varied:
0.12, 0.135, 0.15 and 0.18 em. Trace, rise, contour direction, ink/reverse checks
and normal stem/cap policy stayed fixed. Trials were direct per-arm replays;
they did not replace reports' baseline roles, scope classifications or conflicts.
Stored source arc positions and directed distances reproduce each baseline
terminal status and reason before evaluating the alternate limits.

| Style / terminal | Observed span (em) | Excess over 0.12 em |
| --- | ---: | ---: |
| Bold f upper | 0.13080 | 9.0% |
| Bold j lower | 0.13281 | 10.7% |
| Bold c upper | 0.13916 | 16.0% |
| Bold Italic f upper | 0.13014 | 8.5% |
| Bold Italic s lower | 0.14124 | 17.7% |
| Bold Italic s upper | 0.14223 | 18.5% |
| Bold Italic j lower | 0.14443 | 20.4% |
| Bold Italic c upper | 0.14593 | 21.6% |

At 0.135 em, three additional arms close: Bold f/j and Bold Italic f.
At 0.15 em, all eight close. At 0.18 em, there are no further changes in this
scope. All eight already meet the trace-length and rise windows. Their glyphs'
other arm often traces around much of the outline and remains refused by the
trace-length window.

No additional closures appear in Regular/Italic or in the historical runs.
The other sampled current controls, including n/h/m/u/v/w and e/o counters, gain
no new terminal closures. This is limited observed stability, not proof that
broader widths cannot confuse anatomical roles elsewhere. Existing closed-counter
precedence and the separation between terminal evidence and roles remain essential.

The synthetic angled 0.14 em lobe changes from unresolved to verified at 0.15 em.
The ordinary terminal stays verified; tall-lobe and wrong-direction controls stay
unresolved throughout. The wide-lobe result shows that increasing the size bound
changes the intended supported domain. It is not evidence that the lobe is
anatomically nonterminal, nor sufficient reason to calibrate a new rule around it.
A width-to-cut ratio would likewise need independent evidence, not post-hoc tuning
on these eight positive examples.

## Inspection and validation

The combined four-style j/c/f/s overlay and synthetic control proof were opened
and inspected. Orange traces show the experimental 0.15 em closures and purple
traces the existing closures. The eight new traces follow the expected terminal
lobes in these drawings; no font design was changed or accepted. These are source
outlines, not compiled shaping or hinting proofs.

All six report runs preserve their source hashes. Comparing the current function
with its committed predecessor gives exact equality for all 213 contexts with
verified cuts after removing the new `window_checks` field. The remaining 29
presection refusals are explicitly counted, not claimed as part of that equality
check. Baseline replay also checks status/reason equality before every sweep.

93 focused tests pass through `make test` and the shared six-worker lock. Added
checks cover quantitative width refusal, absent dimensions after early trace
refusal, preclosure refusal and scalar diagnostic preservation under reflection.
Existing nested-component, counter, terminal, role, matching and scoring controls
pass. Ruff and `git diff --check` pass. No full suite, reproduction or font build
was run; production sources, generators and acceptance records remain untouched.

Artifacts are under `build/glyph-review/heavy-terminal-limits-2026-10-30/`:
`evaluate.py`, per-run baseline reports and `sweep.json`, `summary.json`,
`controls.json`, `check_replay.py`, `prior-comparison.json`, `tests.log`, and
`terminal-sweep.svg/png` plus `controls.svg/png`. The saved predecessor function
supports the exact replay comparison.

## Next task

Build a region-labelled anatomical contrast set for broad terminal lobes versus
nonterminal return/branch lobes, with attachment context and explicit ambiguous
labels. Keep current examples as development evidence. Establish which positive
context distinguishes them before proposing a larger or locally scaled window;
reserve independent base families for later qualification. The 0.12 em omissions
remain documented until then. Tail/ascender/serif context and repair qualification
remain open; no smoothing or repair solver follows from this investigation.
