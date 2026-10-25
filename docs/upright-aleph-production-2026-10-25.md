# Upright aleph integrated, 2026-10-25

The person accepted the vertically fitted upright italic drawings and
requested production integration. Regular and Bold ℵ now use those
drawings. The [production proof](../proofs/upright-aleph-production-comparison-2026-10-25.pdf)
shows the replaced romans, final outlines and retained smaller forms.
This supersedes the earlier square-serif roman repair.

`scripts/upright_aleph.py` reads fixed reviewed GLIF design inputs under
`scripts/data/aleph/`. These preserve the two italic drawings as approved,
including the previous Bold Italic join repairs. It removes the 15.2°
shear and maps the original ink bounds −23..1099 vertically to 0..1434
(1.278075×), leaving the horizontal dimensions unchanged. The results
are centered in the established 1380/1477-unit roman advances.

Minor finishing aligns inherited near-tangent handles after rounding;
one inherited Bold curve overshoot receives an explicit extremum. No
new construction defects are accepted. The existing roman ℵ lint keys
are removed. The accepted optical weight retains the Regular stroke
exception and introduces three explicit stroke exceptions: Bold ℵ and
the two upright smaller alternates. Their measured strokes are 303/310
units for full size and 279/358 for small size. These reflect the approved
design, rather than smoothing defects hidden in the quality baseline.

The smaller upright versions are `uni2135.sc`. Both `smcp` and `c2sc`
select them explicitly: Unicode ℵ is uncased (Lo), so it needs this
explicit mapping. All styles carry the alternate and feature rules.
Italic alternates reference their existing ℵ, raised 23 units along the
slant to place the small-cap bottom on the baseline. Full-size Italic
and Bold Italic outlines are unchanged. The retained smaller height is
the approved mathematical-symbol size, not a redraft to the font's
1040-unit alphabetic small-cap height.

The generated-style writer installs Bold's accepted drawing, and the
small-cap builder installs all alternates and writes the features.
`draft_letterlike.alef` uses the same source for Regular redrafting.
The fixed design inputs avoid depending on generated Italic output or
creating a roman/italic generation cycle.

Scope comparison against the pre-integration masters confirms only ℵ's
outline changes in each roman; the italic outlines are identical. Each
style gains one alternate. Every pre-existing advance, anchor, and kerning
pair matches. Existing shaping goldens and complete corpus digests match;
no shaping baselines change. Tests also exercise both small-cap features,
their combination, height fit and repeatable installation.

`make reproduce` passes for all three generated styles. The 83 focused
geometry/quality/lint/UFO/composite/shaping checks pass. All four CFF
hinting checks pass with the hinter's required local helper-socket access.
The sandboxed hint run's only failures were those socket restrictions.
Production OTFs and TTFs rebuild with hints and STAT metadata; all four
WOFF2 files rebuild. Actual HarfBuzz checks on all twelve deliverables
confirm the full-size and both small-cap feature selections and advances. Ruff, sync checks,
and whitespace checks pass. Full suite: 183 passed, 3 skipped, with the four CFF checks run separately
and all passing (187 total passes). Logs are in `build/aleph-production/`.

After integration the next Regular acute-counter review was completed
separately: [review](regular-acute-counters-review-2026-10-25.md).
