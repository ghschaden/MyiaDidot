# Paired Italic extended small-cap repairs

Reference: `7eb071e0` with the approved Bold Italic basic Latin repairs
installed. The review sent back Bold Italic Ƒ, florin.sc, uni01A5.sc,
uni0263.sc and uni0242.sc, and requested consistent non-bold Italic
counterparts. uni0263.sc explicitly means the middle small-cap form in
the review row, not lowercase ɣ or uppercase Ɣ.

Scratch evidence and before sources are in
`build/glyph-review/bold-italic-extended-queries/`. The paired candidate
approved gamma/glottal script is `scripts/italic_gamma_glottal_smallcaps.py`. It uses each
style's own final bases and stroke weights, with no shared generator
changes. These are outline/shaping candidates, not hinted raster proofs.

## Approved glottal small caps

The review approved uni0242.sc in Italic and Bold Italic on 2026-11-06.
The inner arc is fitted from the same-style full capital's inner arc,
with a rounder right side and open head. The outside, stem and terminal
are retained, as are the advance and anchors. Both drawings are installed,
marked drawn and accepted. Proofs were rendered and visually inspected:
`proofs/italic-glottal-smallcap-repair-2026-11-06.svg` and
`proofs/bold-glottal-smallcap-repair-2026-11-06.svg`.

## Approved gamma small caps

The review approved uni0263.sc in both italic styles on 2026-11-06.
The new construction scales the same-style Ɣ to small-cap height, keeping
its loop below the baseline (about −364/−365 rather than zero). Its main
stroke is fitted to the same proportion of h.sc as Ɣ has to H; the old
Bold Italic draft's main stroke was 300 against Ɣ's 134. The first candidate
retained its old advance; spacing was subsequently corrected as below.
Lowercase ɣ and the full capital Ɣ are unchanged.

The before/after gamma proofs in the scratch directory were rendered
and visually inspected in both styles. Both approved drawings are installed,
marked drawn and accepted. Retained evidence is in
`proofs/italic-gamma-smallcap-repair-2026-11-06.svg` and
`proofs/bold-gamma-smallcap-repair-2026-11-06.svg`.

Compiled outline-intersection checks found the wider gammas touching in
doubled small-cap pairs at the old advance. Final placement preserves both
former side bearings, increasing advances by the added ink width: Italic
876→1040, Bold Italic 958→1094. The approved curves are translated intact;
anchor x positions follow the ink centre's change. All 12 checked contexts
(nɣn, HɣH, ɣɣ, ɣa, ɣo, aɣ in both styles, with smcp) have no outline
intersections. Records: `gamma-spacing.json` and `gamma-spacing-final.json`.

## Hooks still in review

Ƒ/florin.sc tails are rebuilt from each style's F/f.sc with a continuous
stem and elliptical curl, the terminal ball half the stem's width.
uni01A5.sc is rebuilt from the final same-style p.sc with a compact curl
leaving the left part of its head; the right part continues into P's bowl.
An initial whole-stem curl left a gap at P's head and was discarded.
The hook candidates are not installed or accepted yet. The review found
the Italic Florin tails only "ok-ish" and preferred the old Italic ƥ.sc;
that already accepted production drawing remains unchanged and is
excluded from further Italic repair candidates. Bold Italic ƥ.sc remains
in review. Consistency does not override the preferred drawing.

## Hook refinements, 2026-11-07

The first Bold Italic ƥ.sc hook was too light. Its full stem-width stroke
is restored, with a larger radius to retain its eye. The short root jog
is removed; adjacent curves at the terminal are fitted to common curvature
within eight units, retaining endpoints and tangents. This is local to
the drawing; the shared fitter is unchanged.

Florin tails were initially too bulbous; a lighter trial was too thin and
small. The latest tail retains a broader swing beginning higher on the
stem, tapers to 82% of the main stroke, and ends in a ball half that tail
stroke's width. Both italic weights use the same construction at their
own weight. Italic ƥ.sc remains exactly as previously accepted.

Latest candidates: `italic-candidate-v8.ufo` / `bold-candidate-v8.ufo`.
Proofs: `italic-hooks-v8.svg` / `bold-hooks-v8.svg`, before left and
candidate right, enlarged and in compiled English smcp text. Both were
rendered and visually inspected. `hooks-v8-checks.json` records clean
outline lint and construction checks for all five revised hooks, unchanged
hook advances, and exact retention of Italic ƥ.sc. These hooks await
visual acceptance and are not installed. Full validation remains due
after the final hook choice.

The v8 hook proposals were rejected. Their trial script is retained only
under the scratch directory as `rejected_hook_trials.py`. The accepted
replacement uses finished same-style reference curves instead; see
[Astra hook review](hook-reference-reset-review-2026-11-07.md).
That replacement was approved and installed on 2026-11-07. The pending
status above applies to the discarded v8 trial, not the final drawings.

The approved gamma small caps record `org.myiadidot.caseReference` as
`uni0194`: their stroke proportion and overshoot are checked against the
same-style Ɣ construction. This is an explicit correspondence, validated
against the Unicode case pair; it does not suppress findings. Regression
checks include an overweight mutation and a misplaced top, both of which
must still be reported. Other small caps retain the generic diagnostic.
The eight case-reference regression cases pass, including those mutations.
