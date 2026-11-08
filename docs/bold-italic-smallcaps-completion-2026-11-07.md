# Bold Italic phonetic, Greek and Cyrillic small caps

Reference: `4fd217498c688aae1155924743684021da54876b`. The review approved
the remaining 15 Latin/phonetic, 17 Greek and 40 Cyrillic small caps, plus
the accompanying lowercase қ, ҳ and ҷ repairs, on 2026-11-07. All 75
acceptances are recorded by glyph fingerprint in the production Bold Italic
UFO. Eleven local drawings are marked drawn against their Italic source
fingerprints so regeneration preserves the approved shapes.

## Accepted drawings

- omega.sc: rounder inner and outer bowl. Its feet use the accepted middle
  weight between the heavy and light trials: about 139 units at the plate,
  with clearance beneath the bowl. Advance and anchors retained.
- uni0264.sc: rebuilt from the final same-style capital ramshorn, preserving
  its curve shapes and capital-relative stroke weight. It remains near the
  baseline, with a 25-unit overshoot. Charis SIL 6.200 and DejaVu Serif 2.37
  Bold Italic likewise keep U+0264 near the baseline while U+0263 descends;
  Libertinus Serif 7.051 Bold Italic lacks U+0264. These are lowercase
  references, not evidence of a reference-font small-cap substitution.
- uni029D.sc: rebuilt lower crossed tail, retaining the original approved
  head and upper stem. The former top proposal was rejected. The upper
  outline above y=330 is identical to the original.
- uni0444.sc and Greek phi.sc: the same round outer ring from final o.sc,
  preserving the counters and central stem. The upper-right serif joins
  the stem through an outward bracket instead of the inherited reverse turn.
  Both scripts' drawings were reviewed together and remain identical.
- uni0452.sc: rounder outside of the lower-right bowl, tangent upper/foot
  brackets, and a continuous inner foot return around its terminal.
- uni0473.sc: reopened after the initial sheet, then approved with its
  counter from the final o.sc, divided by the existing bar at y=480–552.
  Its outside points, crossbar height/thickness and advance are retained.
  This is the historical Cyrillic Fita; the distinct barred-O uni04E9.sc
  retains its previously approved drawing.
- uni04B3.sc: the final x.sc body and its serif transitions, retaining the
  original descending serif piece. The base x.sc is unchanged.
- uni049B: a lighter, even lower leg with an open curl and a half-stroke
  terminal ball. The final accepted left boundary is one straight segment
  from the shoulder to the foot, not a smoothed swelling. In the slanted
  outline it runs directly from (624,393) to (479,-140).
- uni04B3: a fuller diagonal hook, constructed as one stem/curl before
  rotation, with a flowing root attachment. The final root repair retains
  every approved hook point below the baseline exactly.
- uni04B7: a straight, even right leg and a clearer open curl at its own
  weight, with a half-stroke terminal ball.

The proposed hooked-H small-cap replacement and extended barred-P bar were
rejected. uni0266.sc and uni1D7D.sc retain their original approved drawings.
All remaining drawings in these batches are approved unchanged. u.sc.horn
is a separate, still-unaccepted draft outside these three batches.

uni0264.sc's advance changes from 977 to 1207 to retain the original side
bearings around its wider reconstruction; its anchors follow the wider ink
centre by 115 units. The other ten repaired drawings retain their advances
and anchors. No kerning, feature, group or source drawing in another style
was changed. Newly recorded acceptances reference this
document rather than scratch paths.

## Evidence and integration

The accepted candidates were developed under distinct `build/glyph-review/`
directories: `bold-italic-phonetic-repairs-2026-11-07/`,
`bold-italic-smallcaps-greek-2026-11-07/`,
`bold-italic-smallcaps-cyrillic-2026-11-07/` and
`bold-italic-cyrillic-repairs-2026-11-07/`. Its `candidate-v4.ufo` was followed
by `bold-italic-fita-counter-2026-11-07/candidate.ufo` after the review reopened
and then approved Fita. The whole font was installed after checking
that exactly the eleven named drawings differed from production. Installation
and baseline reports are under
`build/glyph-review/bold-italic-final-integration-2026-11-07/`.

Focused outline lint and construction checks pass for the final Ka. The
Cyrillic review passed all 80 smcp/c2sc mappings and 24 paired text contexts,
with unchanged glyph positions, retained contour counts and no outline
intersections in those contexts. Those checks do not establish hinted
screen rendering. The user approved every final drawing visually and
explicitly authorized production installation, commit and push on main,
overriding the earlier worktree restrictions for this task.

Retained final sheets:

- [Latin/phonetic small caps](../proofs/bold-italic-phonetic-smallcaps-2026-11-07.pdf)
- [Greek small caps](../proofs/bold-italic-greek-smallcaps-2026-11-07.pdf)
- [Cyrillic small caps](../proofs/bold-italic-cyrillic-smallcaps-2026-11-07.pdf)
- [Lowercase repairs](../proofs/bold-italic-cyrillic-lowercase-2026-11-07.pdf)
- [Accepted Omega feet](../proofs/bold-italic-omega-feet-2026-11-07.pdf)
- [Final straight Ka leg](../proofs/bold-italic-ka-foot-2026-11-07.pdf)
- [Reopened Fita counter](../proofs/bold-italic-fita-counter-2026-11-07.pdf)

Integration removes seven resolved quality entries and the obsolete
whole-emboldening exception/metadata for drawn uni04B7. The review explicitly
authorized one new quality exception for the approved lighter uni049B leg
(235 versus the 269-unit reference, ratio 0.87), overriding the shrink-only
exception rule for this drawing. Its shape is not changed to silence that
diagnostic. One golden smcp/c2sc case records the approved ramshorn advance;
the broad 2,119,735-string shaping corpus otherwise remains unchanged.

The integration gate runs the complete tests and regeneration check on the
staged tree. Scratch logs retain the baseline review and its exact approval
digest, source-preservation checks, and the Bold Italic diffenator sweep
against the reference commit. The other three styles' sources are unchanged.
The final sweep finds exactly the eleven listed outline changes and the
one approved advance change, with no unrelated glyph/advance changes.
The final broad shaping report has zero differences and approval digest
`47b056419ac35d306c40d27fe2929e7e0015a7d5437ee95df88d9b35fcf8f823`;
the complete golden-case diff changes only uni0264.sc's advance 977→1207.
