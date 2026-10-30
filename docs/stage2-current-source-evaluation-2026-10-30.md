# Stage 2 current-source evaluation — 2026-10-30

The current recogniser verifies some surviving constituent spans, but does not
establish the shared middle stem of Ɯ or complete u inheritance in ʉ. Missing
heavy-stem observations are a detector limitation, not evidence of bad drawing.
The fixed 0.001 em tolerance was retained (2.048 units in these sources).

## Source and method

Main revision: `cef605f813e307acd419326bd6a4821cd5e10c64`. No merge was made.
The four frozen UFOs under
`build/glyph-review/main-progress-2026-10-30/current/sources/` were checked against
every Git blob at that revision: 2,193 files per style, with no missing or extra
files. All relationship runs report `source_preserved=true`.

| Style | Source content SHA-256 |
| --- | --- |
| Regular | `b04ef014a80dd54488618609f895678b44dc1a05e41e228cdcdb7dd6882e2d51` |
| Italic | `a1babcae4771b87287ae939e9f524f942d82d2ed43934bd1f9d4b86eb1224b5c` |
| Bold | `aac58ae1771eb8a5f027aa5a22a03879307a58cd07e4aa20f31928149d2a5144` |
| Bold Italic | `64a0a62697120dbcca3f2672a306ef92e0a2ec871ed493b22a782a79fb8a3040` |

Generated artifacts are in `build/glyph-review/stage2-current-2026-10-30/`:
`evaluation.json`, `snapshot-verification.json`, and one directory per style with
fresh `declarations.json`, `report.json`, `index.html`, `proof.svg`, and `proof.png`.
The retained `evaluate.py` replays the experiment with:

```sh
.venv/bin/python -I build/glyph-review/stage2-current-2026-10-30/evaluate.py
```

The U/Ɯ experiment tests identity and horizontal translation by their advance
width difference: 800, 811, 832 and 807 units respectively. The u/ʉ experiment
tests identity. These are explicitly labelled evaluation hypotheses, not exported
production provenance. In particular, the advance difference is rounded and does
not establish the exact recipe transform. The recipe was read as context; no
Python recipe parser or best-fit transformation was used.

For every observed base span, retain all target candidate distances and declare
the closest candidate under the fixed transform. Run the existing symmetric
boundary verifier on that candidate. Retain failures, including candidates that
are plainly the wrong stroke after an expected boundary was removed. Do not
interpret nearest-candidate selection as a correspondence claim that has passed.
All geometry IDs were regenerated from the pinned sources. Source hashes and
implementation hashes are in each report; sidecar hashes are also recorded.

## Results and inspected overlays

| Style | Verified / tested span declarations | Shared comparisons | Repeated-but-separate comparisons |
| --- | ---: | ---: | ---: |
| Regular | 3 / 24 | 0 | 0 |
| Italic | 9 / 22 | 0 | 15 |
| Bold | 4 / 25 | 0 | 0 |
| Bold Italic | 6 / 14 | 0 | 6 |

Comparisons are combinations of declarations, not independent examples or whole
glyphs. These counts are not precision, recall, or coverage measurements. In Bold,
only right-U claims verify, so there are no verified comparisons between distinct
constituents despite four successful local declarations.

All four style PNG overlays were opened and inspected. Findings:

- **Bold Italic U/Ɯ:** the left heavy stem agrees at 0.201 units. The translated
  heavy stem differs by 3.503 units and is rejected; translated thin-stroke and
  return spans can verify. The first U's right boundary is changed by twinning,
  so its failed identity claim does not contradict the construction recipe.
  No pair establishes a shared complete middle stroke. The repeated-separate
  outcomes concern supported disjoint regions only.
- **Bold Italic u/ʉ:** one thin exit span verifies at 0.828 units. The detector
  finds a roughly 252-unit-wide span in u, but all five ʉ observations are only
  59–65 units wide. The nearest target to the heavy base span is 533.230 units
  away: a missing corresponding observation, not a measured outline displacement.
  The bar interrupts the base boundaries. Other rejected thin-span hypotheses
  have endpoint/geometry disagreements; the experiment does not diagnose their
  cause or adjust the tolerance to accommodate them.
- **Bold Italic ʋ:** all five observations are roughly 59–65 units wide; neither
  heavy stem is adequately covered. Its open terminal is preserved as an existing
  design choice, not judged against an imagined closed curl.
- **Regular:** U/Ɯ have useful stem coverage, while the bar splits ʉ's observed
  heavy stems into shorter runs. Complete-span verification therefore does not
  check all the surviving portions. No partial-span ancestry was invented.
- **Italic:** lowercase u/ʉ/ʋ and m have no substantial heavy-stem coverage;
  n has a short heavy observation. Verified thin-span reuse cannot compensate
  for that omission. U/Ɯ have much stronger coverage.
- **Bold:** u has two approximately 261-unit-wide observations, but ʉ has only
  two thin observations (63–64 units), on its bar and lower return. ʋ has one
  heavy observation; the other stem is missed.
- **m/n controls in every style:** no constituent declarations were supplied.
  Similar-only observations remain distinct from verified ancestry; no shared or
  repeated-separate conclusion is made for these controls. The recogniser still
  does not know entry/interior/exit roles and cannot approve n-to-m shoulder reuse.

Every glyph's span inventory, measured widths/lengths/y-ranges and omission
reasons are in `evaluation.json`. Coverage is explicitly marked unmeasured.
Unobserved regions must remain in the evaluation account; counting only accepted
spans would conceal these misses.

## Validation and next work

Added an independent radial-ribbon family to the straight/tapered constituent
controls: separated copies, coincident declared constituents, a displaced copy,
and reversed traversal. All four pass through discovery and declaration
verification before reuse classification. They test the conservative geometry
contract, not a claim that declarations prove historical authorship.

65 focused tests passed through `make test` and the shared six-worker lock:
`test_constituent_reuse.py`, `test_shape_relationships.py`,
`test_paired_boundaries.py`, and `test_relationship_infrastructure.py`.
Ruff passed for the touched Stage 2 Python files and `git diff --check` passed.
No production build, full suite, reproduction, hinting or shaping run was needed
for this read-only experiment. Sources, generators and acceptance records were
not changed.

This completes the planned current-source evaluation pass, not the recogniser's
qualification for repair guidance. A labelled independent real-family corpus
with region-level coverage remains necessary before reporting recall or design
reliability. U/Ɯ and u/ʉ are evaluated separately, but neither is a blind held-out
real-family test; both were already inspected during development.

Next is the first Stage 3 pilot: lower returns in u/ų/и/ц/ш/щ/џ, compared with
final same-style bases and Italic references. It must expose missing paired-stem
support rather than manufacture a complete neighbour graph. Distinguish interior
and exit turns and retain tail attachments and counter clearances. The current
experiment adds no smoothing, repair solver, outline acceptance or publication.
