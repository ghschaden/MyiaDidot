# Italic small-cap tip hinting review refreshed, 2026-10-26

[Refreshed before/after proof](../proofs/italic-smallcap-tip-hinting-review-2026-10-26.pdf)
revisits the [2026-10-25 trial](italic-smallcap-tip-hinting-review-2026-10-25.md)
against current production. It shows h.sc/v.sc/w.sc/o.sc and ѵ.sc/ⱳ.sc
at 24, 28, 29, 30, 31 and 32 ppem, with current/trial rows under v35/v40.
Each cell includes 2× nearest-neighbour enlargement and native-size HVWO.
The final PNG was inspected, including the rightmost 32 ppem column and
all four comparison rows; no specimens are clipped.

## Recommendation

The review accepted the half-pixel tip adjustment on 2026-10-26. At 30/32 ppem
the trial gives the pointed bottoms a steadier baseline beside h.sc/o.sc
while retaining their continuous diagonal construction. Production
integration is recorded below.

The proposal affects only Italic v.sc, w.sc, uni0475.sc and uni2C73.sc.
Their on-curve bottom points at source y=−35 receive `yshift 0.5` at 30 and
32 ppem. It removes four v35 glyph/size reports (32 ppem) and eight v40
reports (30/32), represented by eight exception entries. No new alignment
findings appear. Bold Italic has no corresponding listed tip reports and
is outside this proposal.

v35 also changes at 30 ppem, where the original displacement was just below
the audit threshold. This is part of the proposed visual adjustment, not an
additional resolved exception. Control sizes 24/28/29/31 are unchanged.

## Verification and scope

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes, including the accepted Regular prosgegrammeni
hint rule. Make rebuilt both italic production TTF targets after that shared
script change; the Regular-only rule does not apply to either style.

A new scratch trial uses current unhinted Italic and its current production
control file, discovering the four bottom-point sets from the outlines.
Full current/trial audits cover 8–32 ppem in both interpreters:

- Exactly the four intended glyph programs change.
- All glyph coordinates, contour endpoints and flags match.
- cmap, hmtx, GSUB, GPOS, GDEF, OS/2, hhea, fpgm and prep match.
- Each target's raster changes only at 30 and 32 ppem in each interpreter.
- Twelve glyph/size findings disappear, with no added findings.

At trial preparation, no UFO, generator rule, production hint program,
exception key/count or shaping baseline changed. Integration is recorded below. Scratch evidence is under
`build/glyph-review/smallcap-tips/`: `trial.py`, `verify.py`, `proof.py`,
`Before.ttf`, `Before.txt`, `Trial.ttf`, `Trial.txt`, `audit.json` and
`verification.json`. Those files are disposable; the PDF preserves the
reviewed rasters. After approval, integrate a point-discovering rule for
Italic only, rebuild TTF/WOFF2, rerun the all-style TrueType hint checks,
verify production against this trial and remove the eight resolved entries.

## Approved production integration

Accepted and integrated on 2026-10-26. The shared hint-control builder applies
the rule only when the style is exactly Italic. It discovers on-curve indices
at O's bottom zone; no fixed point numbers are stored. A missing matching tip
fails clearly so future outline changes cannot silently use stale indices.
Bold Italic and all other styles retain their existing rules.

Italic TTF and WOFF2 are rebuilt. The eight resolved exception entries are
removed; no other exception keys/counts or shaping baselines change. The
before font was saved under `build/glyph-review/smallcap-tips/production-before/`.
The accepted comparison proof remains the visual reference.

All production glyf records match the approved trial. Against the saved
before font, all coordinates remain exact and only the four intended glyph
programs change. Shared fpgm/prep/cvt, layout, advances and metadata tables
match. Decoded WOFF2 coordinates, programs, advances and layout match the
TTF. Details: `build/glyph-review/smallcap-tips/production-verification.json`.
All four regenerated TrueType hint-zone tests pass, covering the shared
builder across styles. Ruff and `git diff --check` pass.
