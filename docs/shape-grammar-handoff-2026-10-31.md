# Shape-grammar handoff to Claude — 2026-10-31

We have enough evidence to recommend construction provenance and stronger review
contracts. We do not yet have evidence supporting new production outline repairs.
The most useful next production task is an opt-in construction-manifest export
for U→Ɯ and u→ʉ, preserving current drawings and generation behavior.

This note was placed in the main worktree at the user's explicit request. It is a
handoff for the main-worktree owner, not a request to merge the experimental branch
or replace production repair gates.

## Reference state

- Evaluated production snapshot: main `cef605f813e307acd419326bd6a4821cd5e10c64`,
  still the local main tip when this note was written.
- Experimental tools and reviews: `shape-grammar`, pushed commit
  `f963d62e7e4696b0bfef1cee5e0728c2d1d839fb`.
- Local study worktree: `../MyiaDidot-shapes/`.
- At commit, the required full test suite passed and Italic, Bold and Bold Italic
  reproduced exactly. The latest focused run passed 222 tests. Both terminal
  policies' forty archived lower/upper reports and arm scores replayed exactly;
  all 216 existing terminal-arm contexts were unchanged.

These checks validate implementation/regression behavior. They do not establish
anatomical accuracy, design acceptance or a new shaping/hinting result. The
formerly held-out families are development evidence now. Pin fresh source hashes
and rerun affected studies if the production sources change.

## 1. Export construction provenance for U→Ɯ and u→ʉ

Start with these two explicit construction relationships, prioritizing Bold Italic.
Emit a sidecar under `build/` from the generator's actual construction decisions.
Do not infer the recipe by parsing Python or by fitting the final outline to an
expected donor. Use the final same-style base, rather than an earlier intermediate
or another style's outline.

A useful manifest should record:

- Source revision, style, final base/target identities and content hashes. If a
  generator uses an intermediate, identify and hash it separately.
- Each constituent, its exact affine transform and actual operation sequence:
  copy, intersection, subtraction, union, clipping, redraw or subsequent fairing.
- Retained versus intentionally changed regions, and protected landmarks already
  present in the recipe or accepted design decisions. Record unknowns explicitly.
- Evidence origin: generator-declared intent, explicit UFO component or observed
  geometry. A declared input is not proof that its outline survives unchanged.
- A versioned schema and sufficient final-output identity to reject stale data.
  Avoid making correspondence depend on transient point numbering or old span IDs.

The shape worktree can then regenerate span declarations against those pinned
outputs and check their geometry independently. Keep declarations of intent and
verified inheritance as separate outcomes; Boolean union can erase the evidence
needed to establish a shared stroke.

Why this is useful: the current-source study verifies some U/Ɯ spans, but does not
establish the complete shared middle stem. In Bold Italic u/ʉ, the bar interrupts
base boundaries and the recognizer misses heavy-stem correspondence. The fixed
transform study also uses evaluation hypotheses rather than authoritative recipe
transforms. Production manifests would remove that uncertainty without pretending
the remaining observation gaps are solved.

Suggested acceptance for this first task: opt-in export, unchanged generated font
content, deterministic manifests for identical inputs, stale-source rejection and
at least one geometric consumer/replay. Keep the existing reproduction and full
validation gates. This note is not authorization to change production drawings
or test baselines merely to obtain positive correspondence.

## 2. Keep local terminal closure separate from attachment role

The concrete counterexample is Italic k's left arm at the selected branch region.
Both the 0.12 em baseline and 0.15 em morphology policy verify closure around the
plain stem foot. The frozen anatomical label is nonterminal at that junction.

The closure itself is geometrically explainable: its span is 0.07136 em, its
vertical extent from the cut is 0.13387 em and its contour route is 0.33660 em.
All baseline limits pass. This is not evidence that k needs redrawing, and the
wider window is not the cause of this mismatch.

For review/repair decisions, require adjoining-stroke and attachment context
before treating closure as a free exit or terminal. Keep entry, interior and exit
roles distinct. The reconstructed historical bad-m cases show why terminal-like
geometry inside an interior connection deserves inspection; they do not establish
a universal aesthetic rejection rule.

Do not widen or shrink closure windows to make the k case disappear. Preserve it
as a regression/contrast example while studying stem-foot versus free-terminal
attachment. No new automatic attachment gate is qualified by the present corpus.

## 3. Treat missing observations as unresolved

An interrupted heavy stroke, insufficient shoulder rise or missing boundary is
an observation limitation. It is not evidence of bad drawing, lost inheritance,
a safe repair, or a successful negative classification.

The separate angular channel recovers arm observations outside the rounded-turn
scope. Nine selected regions reach the fixed 0.08 em window with sampled clear
counter intervals. Bold Italic x reaches only 0.07373 em and remains partial;
closure is withheld. The two uncertain italic x regions retain their ambiguous
labels. Cumulative-reversal bounds keep partial angular paths near their local
turn instead of following them toward remote free ends.

Keep these distinctions in any production-facing explanation: observed,
unresolved, withheld, ambiguous and outside scope. Do not loosen correspondence
or endpoint tolerances merely to promote an expected construction relationship.

## 4. Use the diagnostics for targeted review; preserve current defaults

The experiment supports focused source-outline proofs and explicit refusal
explanations. It is not ready to replace the existing production repair gate or
recommend general smoothing.

- Baseline reciprocal-terminal span remains 0.12 em; 0.15 em is a separately named
  opt-in morphology experiment. Normal-cap acceptance and role decisions stay
  separate.
- The known 0.14 em broad-lobe control is refused at baseline and admitted by the
  wider policy. That limitation remains visible.
- Among sixteen labelled nonterminal arms in the selected angular branch subset,
  fifteen receive no closure evidence and one produces the k mismatch under both
  policies. Four ambiguous arm labels remain unscored. The subset contains no
  labelled positive terminals, so it cannot qualify terminal recall.
- A wide-policy promotion on a Bold Italic a boundary is outside the frozen angular
  boxes and remains unlabelled. Do not count it as an anatomical success.
- Reference historical repairs as regression cases. Preserve the user's accepted
  knee-width and open-hook choices; the recognizer should not optimize them away.

## Evidence and practical next step

The committed reviews are in the shape worktree, not yet merged into main:

- [Current-source constituent evaluation](../../MyiaDidot-shapes/docs/stage2-current-source-evaluation-2026-10-30.md)
- [Historical upper-arch/splice diagnosis](../../MyiaDidot-shapes/docs/upper-arch-review-2026-10-30.md)
- [Independent-family evaluation](../../MyiaDidot-shapes/docs/arch-family-evaluation-2026-10-30.md)
- [Fixed-window terminal evaluation](../../MyiaDidot-shapes/docs/terminal-holdout-review-2026-10-30.md)
- [Angular arm observation](../../MyiaDidot-shapes/docs/angular-observation-review-2026-10-31.md)
- [Angular terminal findings and proofs](../../MyiaDidot-shapes/docs/angular-terminal-review-2026-10-31.md)

Generated proof and replay artifacts are under the shape worktree's
`build/glyph-review/`; those build artifacts are local
and were not included in the pushed commit. Tracked review/code links on GitHub
can instead use commit `f963d62e` on `shape-grammar`.

Recommended first Claude task: implement the opt-in U→Ɯ and u→ʉ construction
manifests, with unchanged production font output, then hand their schema and
sample artifacts back to the shape worktree for source-pinned verification.
Attachment-context qualification remains the next research task here.
