# Regular prosgegrammeni hinting trial, 2026-10-26

[Before/after raster proof](../proofs/regular-prosgegrammeni-hinting-trial-2026-10-26.pdf)
shows x, iota, prosgegrammeni, Alpha and prosgegrammeni at 8, 10, 12, 14,
16 and 24 ppem. Each panel compares current and trial under both v35/v40,
at native size and 3× nearest-neighbour enlargement. The final PNG was
inspected, including rightmost glyphs, labels and baseline clearance.
These are direct glyph sequences, not a claim about contextual shaping.

## Finding before integration

Regular U+1FBE (`uni1FBE`) is a small serifed I with source bounds y=0..884.
Its advance is 668. Ordinary iota differs (y=−12..900, advance 538), so it
is a contextual peer rather than an identical source to copy. The font's
Greek capital case lookup substitutes iota with this adscript form.

The v35 top is 0.609375–0.6875 pixel above x at 8–14 and 16 ppem (eight
sizes); v40 has no alignment reports. The previous exception's claim that
it is hinted as a mark is not established: its GDEF class is base (1).

## Reviewed trial

A scratch ttfautohint control appends `latn dflt @ uni1FBE`, assigning only
this glyph to Latin zones. It is rebuilt from the same unhinted production
TTF and otherwise uses the production control file.

The trial removes all eight v35 reports with no new findings in either
interpreter across 8–32 ppem. The inspected v35 glyph has steadier alignment
beside x while retaining its serifed-I construction. Recommendation: adopt
the trial. The person accepted this recommendation on 2026-10-26;
production integration is recorded below.

The glyph's v35 raster changes at every audited size 8–32, including sizes
without an original audit report. The proof samples six sizes; all sizes
were audited numerically and compared as bitmaps. v40 rasters are byte-identical
across the entire range. This differs from an isolated point delta: it changes
the hinting assignment for the whole glyph and preserves continuous contours.

## Side effects and verification

Only `uni1FBE` differs among compiled glyf records. Its coordinates, contour
endpoints and flags match; its glyph program changes. Shared `fpgm`, `prep`
and `cvt ` tables match byte-for-byte, as do hmtx, cmap, GSUB, GPOS and GDEF.
Thus no outline, advance, substitution or positioning changes are introduced
by the scratch hinting assignment. No other glyph program changes.

Reference: HEAD `94fdcd462f9c6caf52341892d6947eda34aff735`, with existing
uncommitted pipeline changes. Make confirmed production Regular TTF current.
Full current/trial alignment audits cover 8–32 ppem in both interpreters;
only the existing Horn findings remain in the trial. At trial preparation, production exceptions were preserved with a corrected
prosgegrammeni comment. Integration below removes the resolved entry; shaping
baselines remain unchanged.

Scratch sources, control and font: `build/glyph-review/prosgegrammeni/`
(`trial.py`, `latin-control.txt`, `trial.ttf`). Evidence: `audit.json`,
`trial-audit.json`, `invariants.json`, `raster-changes.json`, `proof.py`.
These files are disposable. Trial preparation used current/trial audits to
establish the exact intended finding change; production checks are recorded
below.

## Approved production integration

Accepted and integrated on 2026-10-26. `scripts/hint_control.py` appends the
reviewed assignment after the normal controls for Regular only. Other
styles retain their previous hinting choices. Regular TTF and WOFF2 rebuilt;
the resolved `v35 uni1FBE:top884 8` exception was removed.

All production glyf records match the approved scratch trial, including the
new prosgegrammeni program. Against the saved production-before font, every
outline is unchanged and only `uni1FBE`'s glyph program changes. Shared hint
programs (`fpgm`, `prep`, `cvt `), layout, advances and font metadata tables
match. Decoded WOFF2 coordinates, hint programs, advances and layout match
production TTF. The accepted proof remains representative of the integrated
result. All four regenerated TrueType hint-zone tests pass, covering the
shared builder across styles. Ruff and `git diff --check` pass. Details: `build/glyph-review/prosgegrammeni/production-verification.json`.

Initial review of the listed hinting groups is complete. Remaining hinting
verdicts: small-cap V/W tip trial and G/Cyrillic round-bottom retention.

