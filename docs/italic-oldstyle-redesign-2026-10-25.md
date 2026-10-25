# Italic old-style figure redesign proposal, 2026-10-25

The person requested a redesign closer to other old-style sets after
finding the height difference between 3 and 9 distracting, 4 huge and 6
too fat. [Redesign proof](../proofs/italic-oldstyle-redesign-2026-10-25.pdf)
shows the complete current and proposed sets, Libertinus Serif Italic
at equal lowercase x-height, enlarged comparisons and text specimens.

This supersedes the earlier weight-only proposal. The drawings retain
Myia's own numeral shapes and contrast, with new proportions informed
by the measured Libertinus bands. No Libertinus outlines are imported.

## Proposed bands and widths

- 0, 1, 2: tops at 905 (just above the 884 x-height), retaining their
  original widths; 0 retains its baseline overshoot.
- 3, 4, 5: tops at 905, bottoms at −380, replacing the tall baseline
  3/5 and oversized 4. Horizontal widths are 90%, 75% and 88% of their
  previous upright-frame widths respectively.
- 6 and 8: ascender tops at 1260 with baseline overshoot −23, rather than
  approximately 1500/1450. Horizontal widths are 88%/90% of their previous
  widths. The 6's thick stroke measures 179 versus 201 before (about 11%
  lighter), close to the lowercase reference after fitting.
- 7 and 9: tops at 905 and descenders around −380, with narrower widths
  (93%/95%). The 9 retains the previous open-tail redesign, avoiding the
  long curled ball that resembled g. The 7 retains its existing terminal.

The ascenders now reach about 1.43× x-height; descending figures extend
about 0.43× x-height below the baseline. These bands closely follow the
reference's vertical rhythm. The ten figures still vary optically in
shape, overshoot and stroke weight. They are not mechanically equalized.

After fitting, thick strokes above the lowercase band are reduced with
the existing thick-stroke-only tool. Rounding, true-extremum insertion
and near-tangent finishing leave all ten proposals free of construction
and glyph-lint findings. The lighter 3 and 5 are now drawn across the
baseline, so their weight measurements differ from the prior tall forms;
full numbers are in the scratch measurements JSON.

Advances are reduced with the narrower drawings so the smaller figures
do not retain oversized spacing. This is an intentional spacing proposal,
unlike the earlier weight-only trial. Proportional old-style forms alone
are changed in the scratch UFO. Tabular old-style figures and Bold Italic
inheritance remain to be rebuilt and reviewed during integration. Lining
figures and all production masters remain unchanged. User acceptance is
not yet recorded.

Scratch generator: `build/italic-figures-redesign/proposal.py`.
Candidate: `build/italic-figures-redesign/Proposal.ufo`.
SVG/PNG and measured bounds, advances, stroke results and construction/lint
reports are in that directory. This is a visual proposal; production
integration still requires generator and figure-family updates,
reproduction, quality/shaping/hinting checks and builds.

## Original 9 restored in the redesigned set

The person disliked the open-tail 9 and requested the old drawing back.
[Updated full-set proposal](../proofs/italic-oldstyle-redesign-restored-nine-2026-10-25.pdf)
restores the original curled ball-terminal 9, fitted to the new −380..905
band and 95% horizontal width, with its thick stroke adjusted to the new
set (measured 180, ratio 1.05). All other proposed figures are unchanged.
All ten remain construction/lint clean. This supersedes the open-tail 9
in the current proposal. Production remains unchanged pending review.

Scratch generator: `build/italic-figures-redesign/restored_nine.py`;
candidate: `Restored-nine.ufo` in that directory.

## Approved and integrated in the italic weights

The person approved the restored-nine whole-set proposal and requested
continuation. The ten approved proportional Italic drawings and advances
are now fixed design inputs in `scripts/data/oldstyle-italic/`, loaded by
`scripts/oldstyle_figures.py` in the shared generated-style writer.
Keeping the accepted design separate from generated output prevents
repeated fitting from shrinking the drawings on each run.

The old-style slashed zero is regenerated from the final zero and the
old-style tabular components are recentered in their existing uniform
lining-figure cell. Lining figures are independent and unchanged. Glyph
anchors, Unicode mappings and live metadata are retained. Font libraries,
kerning, groups and feature text match before this step.

Bold Italic inherits the new figure sources through its normal weighting
and spacing generator. A local final pass splits substantial inherited
extrema and fairs shallow joins only when construction findings require
it, leaving clean glyphs alone on repeated runs. Its optical result is
presented for separate visual review, not recorded as accepted.
[Production and Bold Italic comparison](../proofs/oldstyle-production-bold-italic-review-2026-10-25.pdf).

The proportional/tabular old-style family alone changes. Updated shaping
baselines account for eight affected corpus strings in Italic and eleven
in Bold Italic; all are positioning-only changes from the new advances,
with no changed glyph selection. Each full corpus contains 2,119,788
strings. Removed twelve obsolete Italic quality entries and thirteen Bold
Italic entries. One new Italic stroke exception records the approved
fine 8 (137 against the 167-unit reference). Existing style contrast
findings remain; construction and lint findings for the figure family
are clear. No new lint exceptions are introduced.

The person then asked about Regular. It and Bold have not been changed;
the matching Roman proposal is documented in
`docs/roman-oldstyle-redesign-2026-10-25.md`.

Both italic styles reproduce exactly from complete generation (with the
style's existing reviewed-source copy supplied for Italic) and small-cap
rebuilding. Compiled `GPOS`, `GSUB`, `GDEF`, `cmap` and `hhea` match before
this step. Changed CFF charstrings and `hmtx` entries are confined to the
old-style family, including tabular/slashed variants. `OS/2` average
character width is recalculated from the narrower advances. Lining
figures and the rest of the glyph repertoire are unchanged.

Focused structural/composite/shaping/lookup and repair tests, both-style
quality/lint checks, and TrueType/CFF hinting pass. All six Italic/Bold
Italic OTF/TTF/WOFF2 outputs rebuild with STAT metadata. Ruff and whitespace
checks pass. Logs, before masters, fresh regenerated masters and compiled
comparisons are under `build/oldstyle-production/`.
