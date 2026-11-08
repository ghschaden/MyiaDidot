# Bold modifier glottal stop drawing proposal, 2026-10-25

After the dollar was approved, the review requested the next task: Bold ˀ's
angular outer bowl/terminal and uneven inner edge. The
[before/after proof](../proofs/bold-glottal-drawing-before-after-2026-10-25.pdf)
shows the actual outlines at equal size, enlarged upper curves, the Regular
reference and modifier-letter text. The review accepted this drawing on
2026-10-25 and requested commit and push. The earlier dollar approval is
recorded separately.

## Rounded drawing from the final base

`scripts/glottal_modifier.py` applies the existing superior recipe to
final Bold ɂ (`uni0242`) using the final zero/zerosuperior calibration.
It operates on a local glyph, creating no extra font glyph, Unicode
mapping, category or glyph-order entry. This replaces the angular result
of weighting the combined Regular modifier with a rounded drawing from
its own final Bold base.

The automatic superior recipe produces a 380-unit advance, with ink
bounds 23..345 × 636..1160. The new drawing is fitted to the existing
62..385 × 639..1161 ink bounds: approximately 1.0031× horizontally and
0.9962× vertically, then translated. Its established advance remains 449.
Near-tangent handles are aligned after whole-unit rounding, and handles
at bounding extrema are kept on their tangent so a fractional overshoot
does not alter the compiled sidebearing. No construction findings remain.

The inherited open counter tip at the ball/bowl join remains. Its one
notch finding is now 223,1096; 52 pixels. It is not an enclosed pinhole
or a detached part; the earlier lint review still describes the same
construction. The existing exception key is retained and annotated with
the new measurements. The obsolete one-extremum exception is removed.

## Spacing review

The old and proposed Bold drawings both have a 323-unit ink width and
62/64-unit sidebearings. Regular has 257 units of ink and 53/53 bearings.
Thus the existing Bold spacing tracks its increased ink width rather than
adding disproportionate empty margins. For comparison, Bold superior zero
has 54/53 bearings and modifier l has 53/48.

The unmodified scratch recipe's 380-unit advance would leave only 23/35
units at its sides, materially tightening the modifier against neighbouring
letters. The proposal retains the existing balanced spacing and shows it
in context. The width-quality exception remains, with a reviewed reason;
its generic ratio warning alone is not evidence for narrowing this glyph.
No spacing or shaping-baseline change is adopted for this drawing pass.

## Validation

**53 focused checks pass**: the new repair regressions and prior dollar,
symbol-join and aleph regressions, plus Bold/Bold Italic quality, lint,
UFO/composite and shaping goldens/full corpus digests. Regression checks
verify clean construction, identical ink bounds/metadata, no added glyphs
or font-library changes, repeatability, and actual dependence on the final
base outline. Other styles are unchanged.

A complete fresh Bold generation and small-cap rebuild reproduce the
master. Master comparison finds exactly `uni02C0: outline`; only that CFF
charstring changes. Advances and anchors match, and compiled `hmtx`,
`GPOS`, `GSUB`, `GDEF`, `cmap`, `OS/2` and `hhea` tables are byte-identical.
No new quality/lint exceptions or shaping baselines are introduced.

Proof source, snapshots and validation/build logs:
`build/bold-glottal-drawing/`.

Next drawing review: Bold Italic ɸ optical weight/style, separate from its
previously reviewed counter-tip lint findings.

Both Bold TrueType and CFF hinting checks pass (55 focused passes total);
the CFF check uses the required local helper socket. Ruff, source sync
and whitespace checks pass.
Production OTF/TTF/WOFF2 builds pass; all three Bold formats retain the
449-unit advance, 62-unit left bearing and STAT metadata.
