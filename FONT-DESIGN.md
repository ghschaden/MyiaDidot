# Open font-design work

Current backlog, consolidated 2026-10-26. Completed work belongs in
[FONTLOG.txt](FONTLOG.txt); detailed evidence stays in `docs/` and `proofs/`.
Tooling and publication tasks belong in [DEVELOPMENT.md](DEVELOPMENT.md).
A diagnostic finding is a candidate for review, not proof of a design fault.
The exception files in `tests/data/` are the current inventories; do not copy
counts here, where they quickly become stale.

## Hinting: prepared reviews awaiting a verdict

- **Italic G/Ɠ/Ǥ and Cyrillic Є З Э Ю Ѳ Ѵ Ә Ө, both weights.** Current
  bottoms stay at baseline while O extends half a pixel below at the
  affected 29–32 ppem v35 sizes (G family 30–32). v40 agrees, as does
  28 ppem. Recommendation: retain current curves and hints; final visual
  verdict remains pending. [Review](docs/italic-round-bottom-hinting-review-2026-10-25.md),
  [proof](proofs/italic-round-bottom-hinting-review-2026-10-25.pdf).

## Hinting: remaining review

- Initial review of listed TrueType/CFF groups is complete. Resolve the
  pending verdicts above before integrating their proposed changes.
- Review remaining TrueType and CFF alignment findings in
  `tests/data/hint-zones*.txt`. Some are intentional constructions
  (Fraktur 𝔖, horns, Ʋ); inspect the raster before changing outlines or hints.
  ν's current hints were accepted. Þ/æ.sc/ϐ counter false positives are
  resolved and should not be reopened as alignment defects.

## Drawing reviews awaiting a verdict

- **Italic arch family** m and relatives: inherited narrow open joins are
  retained with refreshed lint annotations; final acceptance remains open.
  Connected ɬ/Ɬ belts were separately accepted.
  [Review](docs/italic-arches-and-l-belt-review-2026-10-25.md),
  [proof](proofs/italic-arches-review-2026-10-25.pdf).
- **Bold Italic ɽ.sc:** review the retained narrow gap between the curled
  leg and swash. The r-family shoulder/lowercase hook work is implemented,
  but its earlier proposal does not itself establish final acceptance of
  every changed drawing. The later r/I review retained r.
  [Review](docs/r-hook-review-2026-10-24.md),
  [proof](proofs/r-shoulders-hooks-before-after-2026-10-24.pdf).
- **Bold Italic ʸ ң ᵍ ᶤ ₡ ⱥ.sc:** recommendation is to retain tapered
  open counters/stroke crossings and their exceptions; final visual
  acceptance is not recorded. Separate optical-weight findings remain.
  [Review](docs/remaining-bold-italic-lint-review-2026-10-24.md),
  [proof](proofs/remaining-bold-italic-lint-review-2026-10-24.pdf).
- **Greek breve/grave stacks and capital cedilla attachments:** repairs
  are implemented and verified; their comparison proofs were still marked
  ready for visual review in the old backlog.
  [Greek review](docs/greek-breve-grave-review-2026-10-24.md),
  [cedilla review](docs/cedilla-attachment-review-2026-10-24.md).

## Construction and optical quality

- Review remaining `tests/data/glyph-lint-*.txt` exceptions using the
  existing proofs first. The initial lint triage is complete; remaining
  entries include intentional open constructions and pending verdicts above.
  The old Regular acute-counter report predates the accepted M/м/№/™ join
  repairs: reassess only surviving findings, not its superseded proposal.
- Review derived letters still emboldened whole in
  `tests/data/emboldened-whole-*.txt`. Hooks, attachments and curls may need
  recipes drawn at the final weight when rederivation strays or misses.
  Include Bulgarian forms and rhotic letters where still listed; the
  repaired Bold Italic ʄ is complete.
- Work through `tests/data/quality-*.txt`: extrema, kinks, smooth joins,
  stroke weight, zones, slant, width and accent gaps. Many italic findings
  are inherited from Old Standard and propagate to Bold Italic. Keep broad
  contour cleanup separate from individual drawing changes and inspect
  `make diffenator` results. Use `make strokes` for optical-weight proofs.
  W-family diagonal slant and i/j dot gaps can be intentional.
- Reconcile any remaining Italic draft metadata with actual acceptance;
  use `make proof` and the draft/small-cap review sheets. The old blanket
  claim that all derived letters, figures and small caps are unreviewed is
  stale: old-style figures, I, Ⱳ, ɸ and italic ligatures have accepted work.
- **Bold Italic ɺ:** inspect the arm bracket's six-unit overshoot and
  foot's nine-unit overshoot against the intended italic construction;
  these may be natural curves rather than defects.
- **Italic smooth rounding:** evaluate enabling smooth rounding together
  with Bold Italic inheritance. An earlier experiment reduced Italic
  smooth breaks but moved about fourteen Bold Italic glyphs across audit
  thresholds. Review both weights before adopting it.

## Spacing: revisit only if specimens warrant it

Four Bold Italic pairs (`of`, `Wh`, `it`, `ba`) were reviewed on 2026-10-20
and retained despite tight measurements against references. They are not
unresolved repair tasks; reopen only on visual evidence.
