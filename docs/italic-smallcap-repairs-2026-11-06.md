# Italic small-cap Ʀ, Ɓ and Ɗ repairs

The review approved the corrected Italic uni0280.sc, uni0253.sc and
uni0257.sc, including the cleanup of both upper stem edges on the two
hooked letters, on 2026-11-06. Their acceptance fingerprints are recorded
in the Italic UFO. The other 43 glyphs in the extended Latin batch have
not been marked accepted by this approval.

`scripts/italic_smallcap_repairs.py` constructs these local drawings from
the final, already accepted r.sc, b.sc and d.sc. It marks the Italic
drawings `org.myiadidot.italicSource=drawn`, so regeneration preserves
them. Shared construction and emboldening machinery are unchanged.

- **uni0280.sc:** the cut is placed just inside the actual stem, using
  stem measurements below and above the bowl's crossbar. The bowl and
  leg move down 145 units with a small overlap into the retained stem;
  a strip beneath the foot is removed so only the leg descends. The
  outline has one outer contour and a closed counter, replacing the
  old torn bowl and detached leg. Baseline, top, descender and advance
  remain unchanged.
- **uni0253.sc / uni0257.sc:** compact upright curls replace the large,
  low f-top grafts. The curl's centre-line radii are 155 × 109 units,
  with a 150-unit rising stroke and 44-unit top; a round end touches
  both ring edges without the dent left by intersecting a separate
  ball. Their tops are at 1074 against a body height of 1040. Advances
  remain unchanged.
- **Both hook stem edges:** short reversing curves from the old serif
  are removed. The outer straight stem flows tangentially into the curl;
  the counter's head bracket flows tangentially onto its straight side.
  This addresses the small nodges the review identified in the first
  compact-hook trial. The hook size and placement stay unchanged.

Bold Italic is regenerated from the repaired Italic. Local finishing
records the hook curves' true extremes and retains all three glyphs'
previous advances and horizontal body positions. The three Bold Italic
drawings are marked drawn with their Italic source fingerprints, so
later regeneration preserves this finishing and detects stale inputs.

Scratch sources and evidence: `build/glyph-review/italic-smallcap-repairs/`.
`before.ufo` and `bold-italic-before.ufo` preserve the actual before
states, including all earlier approved work. `join-before.ufo` preserves
the first compact-hook trial for the stem-edge comparison. `join-cleanup.svg`
shows that comparison. Final full-letter and shaped-text proofs are
`italic-final.svg` and `bold-italic-final.svg`; the final versions are
inspected after rebuilding, including the smoothed stem joins in both
weights. Retained evidence is in
`proofs/italic-smallcap-repairs-2026-11-06.svg`,
`proofs/bold-italic-smallcap-repairs-2026-11-06.svg` and
`proofs/italic-smallcap-stem-joins-2026-11-06.svg`.
These are outline and shaping proofs, not
screen-hinting proofs.

Validation of the approved Italic repair and first Bold Italic finishing
completed: **366 tests passed, 7 skipped**; `make reproduce` reported
Italic, Bold and Bold Italic **as generated**. The initial full run passed 363 tests and
failed only the Bold Italic golden shaping case because regeneration had
changed the two hooked small caps' advances by two units. Their original
spacing is retained in the final drawings; no shaping baseline was
updated. Quality exceptions only shrink: Italic uni0280.sc's kink count
falls from four to three, and its Bold Italic kink exception is removed.

Regression checks cover the lowered-r construction in both italic
weights, and tangent-continuous upper stem joins on both hooked Italic
small caps. All four focused regression checks pass. `scope.json` records
that only these three glyphs changed geometrically in each italic weight;
advances, features, kerning and groups were unchanged and acceptance
fingerprints remained valid.

A later review identified the old lower stem-to-serif shape in
the Bold Italic hooked b/d small caps, and questioned the upper joins too.
The separate local follow-up is recorded in
[Bold Italic hook stems](bold-italic-hook-stems-review-2026-11-06.md).
It leaves the approved Italic drawings unchanged.
