# Bold Italic phonetic drafts

The person reviewed 57 phonetic forms and approved 47 unchanged, then
approved all ten local drawing repairs on 2026-11-08. All 57 approvals
are recorded in production Bold Italic. Final proof:
proofs/bold-italic-phonetic-repairs-2026-11-08.pdf.

The ten repairs:

- uni028D: two copies of final same-style uni028C (/ʌ/), replacing the
  turned cursive w. Advance 1463 → 1566; other advances are retained.
- uni025E: rounder upper and lower counters.
- uni0256: bowl/counter based on approved uni0257, with a rounded tail.
- uni0290: lighter hook, no root step, and a curved outer descending edge.
- uni025F: bar shifted right to balance its projections about the stem.
- uni0267 and uni0271: original softer legs retained, with the small knee
  smoothed locally; uni0271's middle stem also loses tiny extra segments.
- uni0273: original soft leg retained, with a smoother inside transition
  and one continuous outside curve flowing into the hook.
- uni028F and uni0299: stems run into the serifs without recesses;
  uni0299's upper counter is rounder.

M/m/n/h were inspected as references and remain unchanged. The lowercase
letters share the original shoulder construction; the capital M uses
straight diagonals. No global alphabet changes are included.

Finished drawings carry org.myiadidot.drawn with their Italic input
fingerprint. uni028D and uni025E also have truthful italicSource=drawn
provenance: these finished constructions replace the former turn/attach
recipes, so those obsolete recipe-base comparisons do not apply. All
independent geometry, stroke and zone checks remain in force.
The approved unchanged uni0284 is retained as a drawn glyph because
regenerating it from the newly centered uni025F would move its bar.

Installation cleanup splits new counter/hook extrema and rounds to whole
units. A single handle at uni0271's old shoulder join is aligned to remove
a small tangent mismatch, retaining the approved soft profile. These are
geometry refinements of the approved drawings; no design exception lists
are enlarged. Original approvals, revision snapshots and checks remain
under build/glyph-review/bold-italic-phonetic-repairs-2026-11-08/.
Final installation/regeneration and baseline-review evidence is under
build/glyph-review/phonetic-commit-2026-11-08/.

All 57 direct candidate shaping checks passed (latn/en). The full corpus
(2,119,735 strings) changes in 2,926: 2,862 for ʍ's wider advance alone,
62 marks on ʍ recentred with it, and ʐ before ) and ] kerned 26 units
tighter after its lighter hook. Nothing else shapes differently; the
golden and digest baselines were accepted from that exact report.
Before commit, Bold Italic was regenerated with its small caps so that it
reproduces exactly (the installation had left stale small-cap widths). Outline proofs
were visually inspected; they do not establish hinted rendering quality.
The commit gate runs the full suite and verifies style regeneration.
