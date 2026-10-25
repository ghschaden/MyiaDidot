# Bold Italic Ⱳ curl connection proposal, 2026-10-25

After approval of ɸ, continued to the queued Ⱳ drawing concern.
[Before/proposal](../proofs/w-curl-before-after-2026-10-25.pdf) shows
actual outlines at equal scale and the enlarged curl connection.
[Italic comparison](../proofs/w-curl-review-2026-10-25.pdf) supplies context.

The old TODO describes a middle serif running into the curl. The current
middle serif is separated from it. The visible fault is instead at the
curl's own connection to the diagonal: two 48-unit horizontal ledges at
upright y=1150, where the heavy stroke meets the narrower curl.

The scratch proposal replaces these two ledges and their approach curves
with continuous cubic transitions. The outer return joins the existing
curl crown; the inner return meets the existing diagonal at y=1050 with
its tangent. The crown, ball terminal, W body, second contour, advance,
anchors and metadata remain. Only this full-size Bold Italic glyph is
changed in the scratch UFO; production remains unchanged for Ⱳ.

Rounded and finished candidate has no construction or glyph-lint
findings. This does not record user acceptance or finish production
integration. Source/candidate: `build/w-curl-review/trial.py`, `Trial.ufo`.

## Approved and integrated

The person approved the proposal (“go ahead”). `scripts/w_curl.py` now
applies the same repair in the Bold style writer after rounding. It
recognizes the two ledges and replaces only their approaches; a second
pass leaves the finished drawing unchanged. The production outline equals
the approved trial exactly. Tangent finishing also makes small handle
adjustments elsewhere in the glyph (up to two units); retained body and
ball on-curve nodes stay fixed.

The Bold Italic master changes only `uni2C72` in this step. Advances,
anchors, metadata, kerning and layout are preserved; no exception or
shaping-baseline changes are needed. Complete generation plus small-cap
rebuilding reproduces the normalized UFO exactly. The existing approved
before/after proof shows the production result.

Regression tests rebuild the old GLIF, compare it to production, check
retained body nodes and metadata, clean construction/lint and repeatability,
and verify other styles remain unchanged. Validation/build logs and the
before/rebuilt masters are in `build/w-curl-production/`.

All 26 focused checks pass (24 repair/quality/lint/structural/shaping,
plus TrueType and CFF hinting). Production OTF, TTF and WOFF2 rebuild with
hinting and STAT metadata. Compiled `hmtx`, `GPOS`, `GSUB`, `GDEF`, `cmap`,
`OS/2` and `hhea` match; only `uni2C72`'s CFF charstring changes.
Ruff and whitespace checks pass.
