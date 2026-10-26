---
name: glyph-review
description: Review Myia Didot glyph designs or proposed glyph changes with focused visual proofs, same-style comparisons, shaping checks and side-effect reports. Use for glyph drawing, spacing, ligature or hinting review, rather than ordinary build or infrastructure work.
---

# Glyph review

Produce evidence the person can use to judge a glyph in context. Distinguish
source geometry, compiled shaping and rendered hinting; a clean outline lint
result does not establish a good drawing.

This skill is shared by Codex and Claude. Run commands from the repository root.
Use the shared source and design rules in `CLAUDE.md` and read only the relevant
topic in `docs/claude/`. It needs no particular model, subagent, plugin or editor.
Explicit user instructions and existing authorization take precedence over this
workflow; adapt its depth to the requested review.

## Establish what is being reviewed

Identify the glyph names/code points, styles, intended change and comparison
state. Use the person's requested reference; otherwise use `HEAD` for a review
of uncommitted changes. For a review of the current design without a proposed
change, compare with its same-style bases and peers. Preserve unrelated working
changes. Save a before snapshot before an authorized edit if `HEAD` would not
represent the actual before state.

Review requests authorize inspection, measurements and proof generation. Change
drawings only when the person also requests a fix or design work. Work through
the Regular or the appropriate generator/design input for generated styles;
regenerate whole styles instead of transplanting individual glyphs. See
`docs/claude/styles.md` and `docs/claude/glyphs.md` when source ownership is unclear.

Keep scratch sources, logs and candidate proofs under a distinct
`build/glyph-review/<topic>/` directory. Existing one-off review scripts may
rewrite a tracked PDF or install a design: inspect their entry point before
running them. Preserve accepted proofs and recorded acceptance.

## Make a focused visual proof

Choose a few useful peers: the final same-style base, `n/o` for lowercase and
old-style figures, `H/O` for capitals and lining figures, or `h.sc/o.sc` for
small caps. Include the relevant accented/derived forms when a shared base moves.
Compare before and after at the same em scale, enlarged and at text size.

The bundled renderer makes a standalone SVG directly from source outlines and
optionally adds compiled, HarfBuzz-shaped text. It reads UFOs without saving them.
Read [references/proofs-and-checks.md](references/proofs-and-checks.md) for commands,
before-source extraction and check selection. For example:

```sh
.venv/bin/python -I skills/glyph-review/scripts/proof.py \
  --ufo sources/MyiaDidot-Italic.ufo --glyphs r uni027D n o \
  --text 'rara aɽa' --language en \
  --out build/glyph-review/r-family/current.svg
```

Open the rendered artifact with the available image/browser tools. Inspect
counters, joins, terminals, tangents, extrema, alignment, apparent weight and
spacing in words, plus clipping and labels in the proof itself. If visual
inspection is unavailable, label the proof as generated but uninspected.
Never infer visual acceptance from metrics or tests alone.

For ligatures compare separate letters and joined forms, features off/on, and
relevant language exclusions. For accents compare NFC/NFD, anchors and stacked
forms. For hinting or small-screen complaints use freshly built hinted OTF/TTF
fonts at the affected sizes; the source-outline SVG does not simulate hinting.
Reference fonts establish a calibrated range, not a shape to copy.

## Check the intended change and its consequences

Use the relevant checks in the reference, starting with the reviewed glyphs and
their direct dependants. Report which checks actually ran. Choose script,
language and features explicitly when shaping; keep settings identical across
the comparison. Separate intended differences from unexpected changes and from
cases the selected corpus did not exercise.

After an authorized source change, normalize changed UFOs, update win metrics
when extents require it, and check source synchronization after bulk generation.
For generator changes run `make reproduce`; use the existing full validation
gate before committing. Broaden visual/shaping comparison when shared geometry,
features, anchors or spacing could affect other glyphs. Do not rerun expensive
checks without a new change, failure or unresolved concern.

Do not update exception lists, shaping snapshots, draft/acceptance metadata or
the `proofs-approved` tag merely to make checks pass. Honor any acceptance the
person has already given. For an authorized shaping-baseline update, review the
complete JSON report and accept its digest as documented by
`scripts/update_test_data.py --help`.

## Deliver the review

Lead with the finding or recommendation. Identify each affected glyph/style,
describe the visible issue or improvement, and link to the relevant proof and
full report. Include measurements only when they explain the judgement.
State unexpected changes and validation limits, including missing references
or uninspected images. Distinguish a proposed drawing from one the person has
accepted; a review alone does not authorize commit, push or publication.

For a substantial review, record its reference revision/source state, scope,
proof paths, findings, checks and actual acceptance status in
`docs/<topic>-review-<date>.md`. Retain a proof under `proofs/` when requested or
when recording an accepted design. A short inspection can be reported directly.
