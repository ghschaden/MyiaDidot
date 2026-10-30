# Lower-return arm and terminal context — 2026-10-30

The recogniser now supports local exit roles in Bold Italic u/и and Italic ш.
These are observed local construction roles, not acceptance of a drawing or proof
that one glyph can reuse another's geometry. Real-font interior turns remain
unresolved; the section failures are retained rather than bypassed.

## What changed

`relationships/return_context.py` checks five consecutive normal sections along
each counter arm, starting at the existing observation shoulder, 0.015 em apart.
It uses Stage 1's forward/reverse ink checks and unchanged tolerances. All five
sections must succeed; the sampled centerline must be predominantly vertical
and maximum width cannot exceed 1.25 times minimum width. An accepted local band
can support a turn even if the global detector has no complete stem observation.
This distinction is recorded: `neighbours` still holds the global candidates,
while `arm_context` contains independent local sections and failures.

For an interior role, opposing arm observations must agree on both endpoints of
at least three complete ink sections within 0.003 em. Merely similar widths or
nearby strokes do not establish a shared neighbour. Existing global paired-span
evidence is retained separately.

For an exit, both local bands must be supported and distinct. The right arm must
trace around a short cap on its own contour and return to the opposite boundary
verified by its first ink section, within 0.003 em. The trace is bounded to
0.35 em of contour length, 0.16 em rise and 0.12 em horizontal extent. A stem
continuing above that window is not an exit. Lack of a following turn is never
sufficient evidence by itself.

The context screen withholds exit when any outline extends more than 0.04 em
below the lower of the baseline and turn floor. This glyph-wide test is
intentionally conservative: it does **not** prove that a descender is attached
to this return. The actual threshold, depth, cap trace, return distance and
section failures remain in JSON. Tail attachment itself is still unresolved.

The nested report is now `myiadidot-lower-returns-v2`, including its context
policy. Proofs retain blue counter arms and magenta clearances, and now add green
ink sections and orange verified cap traces. Green sections can be individually
valid while the complete arm band remains unresolved; the labels and JSON make
that distinction.

## Pinned four-style evaluation

Main remains `cef605f813e307acd419326bd6a4821cd5e10c64`. The experiment reads the
same verified frozen sources as the preceding pilot. Reports retain source and
implementation hashes and all four runs have `source_preserved=true`.

Artifacts: `build/glyph-review/return-context-2026-10-30/`. `evaluate.py` replays
the four-style evaluation; `evaluation.json` gives per-glyph outcomes. Each style
has full JSON/HTML, paired-boundary and return proofs, plus a focused six-glyph
proof. The four focused PNGs and full Bold Italic return proof were opened and
inspected. This is source-outline inspection, not hinted or shaped output.

Scope: u/ų/и/ц/ш/щ/џ, n/h/m, v/w, plus refusal controls љ, u.sc, f_h and f_f_h.

| Style | Candidates | Supported local turns (global or local evidence) | Exit roles | Interior roles |
| --- | ---: | ---: | ---: | ---: |
| Regular | 4 | 1 | 0 | 0 |
| Italic | 27 | 2 | 1 | 0 |
| Bold | 4 | 3 | 0 | 0 |
| Bold Italic | 27 | 7 | 2 | 0 |

The scope is larger than the first pilot, so raw candidate totals are not a
before/after accuracy comparison.

- **Bold Italic u/и:** the final counter turn has five valid sections on both
  arms and a short cap returning to the verified opposite edge. Its local exit
  role is supported. The first turn still fails some near-floor sections.
- **Bold Italic ų/ц/щ/џ:** their final turns can have supported bands and a cap,
  but below-baseline geometry withholds exit classification. The drawings and
  accepted tail/knee choices are untouched.
- **Italic ш:** its final turn passes the exit checks. Italic u does not inherit
  that result: its local support remains incomplete. Style membership and overall
  resemblance are not evidence that the same relationship is supported.
- **Real middle turns:** no new interior role is claimed. Nonparallel-boundary
  and reverse-correspondence failures remain visible on the curved heavy arms.
  No threshold was loosened to label them.
- **љ:** its lower curl/bowl candidates retain failed or incomplete local
  sections and unresolved context. Recognition supplies no reason to repeat the
  previously refused repair or to declare a visible defect.
- **u.sc:** some styles have a supported counter turn through global or local
  evidence, but its arms continue upward. It is not an exit terminal.
- **f_h/f_f_h:** italic lower-exit candidates can show a cap while their heavy
  arm lacks a complete local band. They remain unresolved. A visible cap does
  not compensate for missing adjacent-stroke support.
- **v/w and n/h/m:** none gains an exit/interior role in this run. This is a
  conservative refusal result, not proof of absence of a real anatomical role.

## Validation and remaining limits

83 focused tests pass through `make test` and the shared six-worker lock.
Six additional cases cover local support without global paired-span records,
reversed cap tracing, a continuing stem, separate descender context, wrong
opposite-boundary reuse, and a single-contour twin-return construction recovering
an interior plus exit from geometry. Cap traces must return to their verified
opposite boundary. Ruff and `git diff --check` pass.

The new twin-return control is independent synthetic geometry; it is not a
real-font accuracy guarantee. The fixed sampling window can refuse valid curved
arms. Global below-baseline context can withhold a real exit because of an
unrelated descender. Attachment attribution, general terminal types, upper
arches, the historical bad-m-splice case and independent real-family evaluation
remain open. No production source, generator, baseline, acceptance record or
repair solver changed; no font build, full suite, shaping or hinting run was made.

The next Stage 3 step is same-role comparison using counter profiles, adjoining
widths and cap/tail context, with unresolved roles excluded from positive matches.
Retain historical bad-splice and v/w negatives; do not infer broad reuse from the
three observed exits or start smoothing the refused cases.
