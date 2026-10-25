# To do

## Italic G/Cyrillic round-bottom hints reviewed (2026-10-25)

After acceptance of the current ν hints, reviewed G/Ɠ/Ǥ and
Є З Э Ю Ѳ Ѵ Ә Ө in both italic weights. At 29–32 ppem in v35
(Italic G family 30–32), the affected bottoms stay on baseline while
O extends half a pixel below. The older “one row off” wording overstated
the coordinate difference. v40 has no mismatch in this group; 28 ppem
also agrees in both interpreters. Recommend retaining the current curves
and hints, pending visual verdict. Exception annotations are clarified;
keys/counts, production fonts and baselines stay unchanged.
Proof: `proofs/italic-round-bottom-hinting-review-2026-10-25.pdf`.
Details: `docs/italic-round-bottom-hinting-review-2026-10-25.md`.
Next unreviewed group: r.sc/ɍ.sc and Cyrillic ж.sc/к.sc/я.sc bottoms.
The earlier small-cap V/W tip trial remains awaiting its own verdict.

## Italic ν current hints accepted (2026-10-25)

The person accepted the current ν hints on 2026-10-25 and requested
the next problem. Continued beyond the pending small-cap tip trial to ν
in both italic weights. Its outside bottom matches o's outline height, but v40 places it
about 0.5–0.8 pixels below at 16 Italic / 12 Bold Italic sizes; v35 passes.
A scratch half-pixel bottom-point control removes seven / six reports,
but lifts the original bottom above the baseline while neighbouring
points remain below. It also changes the passing v35 rasters. Recommend
retaining production hints; a future repair needs coherent curve handling.
Only ν's scratch glyph program changes; all coordinates, metrics, layout
and shared hint programs match. Raster changes are confined to targeted
sizes, and the trial adds no audit findings. Production and baselines stay.
Proof: `proofs/italic-nu-hinting-review-2026-10-25.pdf`.
Details: `docs/italic-nu-hinting-review-2026-10-25.md`.
Next: shared v35 round-bottom reports in G/Cyrillic capitals. The earlier
small-cap tip trial still awaits its separate visual verdict.

## Italic small-cap tip hinting trial prepared (2026-10-25)

After accepting the Þ/counter-audit review, continued to v.sc, w.sc,
ѵ.sc and ⱳ.sc bottom tips. The current mismatch occurs only at 30/32 ppem
(v35 flags 32; v40 both). A scratch +0.5 pixel bottom-point hint shift at
those sizes gives a steadier baseline. The proof includes native-size and
2× raster samples in both interpreters, with unchanged adjacent sizes.
Only the four intended glyph programs change; all coordinates, metrics,
layout and shared hint programs match. Raster verification across 8–32
ppem changes only 30/32 in each glyph/interpreter. Eight exception entries
would disappear, with no new findings. Production remains unchanged;
visual verdict and integration are pending.
Proof: `proofs/italic-smallcap-tip-hinting-review-2026-10-25.pdf`.
Details: `docs/italic-smallcap-tip-hinting-review-2026-10-25.md`.

## Counter edges excluded from hint alignment audit (2026-10-25)

The person accepted the review and correction on 2026-10-25. The red
dashed guide in the diagnostic marks the mistaken counter reference,
not an intended outside-edge alignment line.

Continued to the pending Italic Þ small-size review. The flagged edge is
its counter top, accidentally at o.sc's outer height, rather than an outer
alignment edge. The “7–11 px” below meant counts of affected sizes; the
actual difference was about one pixel. The false finding also generated
an unwanted -1 pixel counter touch at 27 ppem.

The checker now excludes opposite-winding counter holes, retaining all
outer contours and their original hint-control point indices. This also
resolves the Italic æ.sc and Regular ϐ counter false positives. Six obsolete
hint exceptions disappear; no other audit reports change or are added.
Only Italic Þ's hint program changes, with different raster output only
at 27 ppem in v35/v40. Outlines, metrics, layout, shared hint tables and
all other glyph programs match. All TTF/WOFF2 files rebuild; no UFO/OTF
or shaping changes. Six focused checks, Ruff and whitespace pass.
Proof: `proofs/italic-thorn-hinting-review-2026-10-25.pdf`.
Details: `docs/italic-thorn-hinting-review-2026-10-25.md`.

## Lighter Italic I approved and integrated (2026-10-25)

The person approved the lighter trial I, superseding the assistant's
overly numerical retention recommendation. Italic now loads the approved
fixed drawing in final spacing; Bold Italic inherits it at its weight.
Only I and its full-size component relatives change visible ink (33 per
style). Advances, anchors, kerning and feature source stay exact. Small
caps, barred I and r remain unchanged. The accepted optical weight adds
one stroke exception, plus two reference-comparison exceptions for the
unchanged barred I. No new construction findings. Both italic shaping
corpora (2,119,788 strings each) have zero changes; no baselines update.
All three generated styles reproduce, and all six italic font files
rebuild. Compiled layout and advances match; only the expected 33
charstrings per weight and their ink sidebearings change.
All 24 focused checks pass, including TrueType/CFF hinting, shaping,
composites, quality/lint and exact agreement with the approved I.
Review: `proofs/italic-ri-weight-review-2026-10-25.pdf`.
Production: `proofs/italic-i-production-review-2026-10-25.pdf`.
Details: `docs/italic-ri-weight-review-2026-10-25.md`.

## Roman ṫ dot-spacing approved and integrated (2026-10-25)

Continued to the remaining Regular/Bold dot-gap review. Raising ṫ's dot
by 59 units matches ż's clearance: Regular 139 → 198, Bold 135 → 194.
The person approved the more even spacing and requested continuation.
Regular/Bold production now carry the approved placement and matching
Dotaccent anchors on t's below-mark composites. Seven glyph objects
change per weight; only ṫ changes visible ink. Italic recipe anchors
retain their reviewed positions through an explicit generator adjustment.
Exactly ten corpus strings per Roman weight change, all dot positions
moving +59 vertically; two digest baselines update. Two obsolete accent
exceptions are removed. Metrics/layout match except the intended GPOS
anchors; only ṫ's CFF charstring changes. All six Roman font files rebuild.
All three generated styles reproduce exactly; all four CFF hinting checks pass.
The 49 focused checks are covered by the main run plus successful reruns
after removing stale quality entries and granting CFF helper-socket access.
The separate quality/t-dot rerun passes all nine checks; Ruff and whitespace pass.
Proof: `proofs/roman-t-dot-spacing-review-2026-10-25.pdf`.
Details: `docs/roman-t-dot-spacing-review-2026-10-25.md`.
Reproduce: `scripts/roman_t_dot_review.py`.

## Old-style figure sets accepted in all four styles (2026-10-25)

The person approved the redesigned set with the original curled 9.
`scripts/oldstyle_figures.py` loads the fixed reviewed Italic design inputs,
rebuilds the old-style slash and recenters tabular old-style components.
Bold Italic inherits the new drawings at its own weight, with local curve
finishing. Lining figures, kerning and layout features are unchanged.
Shaping baselines now include the approved narrower advances (8 Italic,
11 Bold Italic corpus strings, positions only). Obsolete quality entries
shrink; one fine-stroke exception records the accepted Italic 8.
Both italic styles reproduce exactly. Focused checks, quality/lint and
TrueType/CFF hinting pass; all six affected font formats rebuild.
Production/Bold Italic proof:
`proofs/oldstyle-production-bold-italic-review-2026-10-25.pdf`.

The person accepted the matching Roman proposal and requested commit/push.
Regular now loads its own reviewed design inputs during figure rebuilding;
Bold inherits its final bases. Both weights retain the Roman shapes and
curled 9, with the same height rhythm as the italic set.
Accepted Roman proof: `proofs/roman-oldstyle-redesign-2026-10-25.pdf`.
Production comparison: `proofs/roman-oldstyle-production-2026-10-25.pdf`.
Roman shaping changes are positions only: 8 Regular and 10 Bold strings.
Bold 3/5 retain a modest optical weight increase; 4 has balanced bearings.
Details: `docs/roman-oldstyle-redesign-2026-10-25.md`.

## Italic old-style set redesigned for review (2026-10-25)

The person requested more conventional old-style proportions: 4 was huge,
6 too fat, and the tall 3 differed strongly from 9. A new whole-set trial
supersedes the weight-only proposal. Figures 3/4/5/7/9 have x-height tops
and moderate descenders; 6/8 have shorter ascenders. The 4 is 25% narrower;
6 is narrower, shorter and measurably lighter. At the person's request,
the original curled ball-terminal 9 is restored, fitted to the new band
and lighter weight; the open-tail proposal is rejected.
Advances follow the reduced widths. The proof includes Libertinus at equal
x-height and text comparisons. All ten trial glyphs are construction/lint
clean. Production remains unchanged; no acceptance recorded yet.
Latest proof: `proofs/italic-oldstyle-redesign-restored-nine-2026-10-25.pdf`.
Details: `docs/italic-oldstyle-redesign-2026-10-25.md`.
Next: visual review, then generator integration, tabular/Bold Italic
review and production checks.

## Italic old-style figure weight proposal prepared (2026-10-25)

After approval of the integrated Ⱳ, continued to Italic old-style 3, 4,
5 and 9. A scratch trial reduces their thick strokes while retaining
hairlines, heights, advances, anchors and metadata. All four trial glyphs
are construction/lint clean. Current measured ratios fall from 1.35–1.52
to 1.06–1.19; 3 remains the heaviest and needs a visual verdict in text.
Other figures and production fonts remain unchanged. No acceptance yet.
Proof: `proofs/italic-oldstyle-figures-weight-2026-10-25.pdf`.
Details: `docs/italic-oldstyle-figures-weight-review-2026-10-25.md`.
The person found 9 too similar to g. A revised proposal keeps its lighter
bowl and uses a shorter open tail without the curled ball; it is
construction/lint clean. Latest 9 proof:
`proofs/italic-nine-open-tail-2026-10-25.pdf`. Production unchanged.
Next step: visual review, then integrate the chosen drawings and review
Bold Italic inheritance and tabular figures.

## Bold Italic ɸ and Ⱳ approved and integrated (2026-10-25)

The person approved the lighter through-stem, bowl 5% wider with stable
black thickness, and smoothed inner returns. The style writer rebuilds
this drawing from final o/l, with rounded and finished contours. Only
uni0278 changes; advances, anchors, kerning, features and metadata stay.
Bold Italic generation plus smallcaps reproduces exactly. 22 focused
checks pass, including shaping, quality/lint and TrueType/CFF hinting.
OTF/TTF/WOFF2 rebuild. Obsolete construction/notch exceptions are removed;
one base-overlap exception records the approved optical widening.
Production proof: `proofs/bold-italic-phi-production-2026-10-25.pdf`.
Details: `docs/bold-italic-phi-weight-review-2026-10-25.md`.

Bold Italic Ⱳ's curl proposal was subsequently approved (“go ahead”) and
integrated in `scripts/w_curl.py`. Both ledges are replaced by continuous
curves; the production outline equals the approved trial. Advances,
anchors and metadata are preserved; no exception or shaping-baseline
changes. Full generation plus smallcaps reproduces the normalized UFO.
26 focused checks pass, including shaping and TrueType/CFF hinting;
OTF/TTF/WOFF2 rebuild. Compiled metrics/layout match; only Ⱳ's
CFF charstring changes.
Proof: `proofs/w-curl-before-after-2026-10-25.pdf`.
Details: `docs/w-curl-review-2026-10-25.md`.

## Bold ˀ rounded drawing accepted; spacing reviewed (2026-10-25)

After approving the dollar, the person requested the next task. Bold ˀ
is now rebuilt from its final Bold ɂ base, with rounded outer bowl/terminal
and an even inner edge. The drawing retains its old ink bounds, 449 advance
and balanced 62/64 sidebearings. The automatic 380-unit recipe advance would
materially tighten it; the spacing proof supports retaining the existing
fit. The width exception is retained with a reviewed reason.

One obsolete extremum exception is removed. The inherited open counter
tip remains, with its existing notch key and refreshed measurements.
Only ˀ's outline/CFF charstring changes; all compiled metrics/layout tables
match. No new exceptions or shaping baseline changes. The person accepted
this drawing on 2026-10-25 and requested commit and push.

**55 focused checks pass**, including TrueType/CFF hinting. Bold reproduces
from a complete generation and small-cap rebuild; production OTF/TTF/WOFF2
builds pass.
Proof: `proofs/bold-glottal-drawing-before-after-2026-10-25.pdf`.
Details: `docs/bold-glottal-drawing-review-2026-10-25.md`.

Next drawing review: Bold Italic ɸ optical weight/style.

## Bold Italic dollar drawing proposal prepared (2026-10-25)

After accepting the symbol-join/trademark proposal, the person requested
continuation. The dollar's diagonal waist is now about 20% narrower, and
both ball entrances are continuous curves without the old backward neck
bumps. The balls are more compact. Straight through-bars retain their
15° slope, 86-unit widths and 95-unit gap; spacing/anchors stay unchanged.

The person approved this dollar drawing on 2026-10-25. Exactly dollar's
outline changes. No quality/lint exceptions or shaping baselines change; compiled metrics and
layout tables match. **32 focused checks pass**, including shaping and
TrueType/CFF hinting. Bold Italic reproduces; production OTF/TTF/WOFF2
builds pass.

Proof: `proofs/bold-italic-dollar-drawing-before-after-2026-10-25.pdf`.
Details: `docs/bold-italic-dollar-drawing-review-2026-10-25.md`.

Next drawing candidate: Bold ˀ curve/weight and spacing. Bold Italic ɸ
optical weight remains open separately; dollar drawing is approved.

## Upper-left joins and trademark repaired after visual review (2026-10-25)

The person's review supersedes the earlier Regular-counter retention
recommendation. Fill the thin slits in Regular M, м, № and trademark's M
by joining their existing diagonals directly to the uprights. Raise the
M/middle tips to their feet. Bold inherits the roman repairs; aliases and
accented M forms follow their base. Bold № retains its old placement and
advance despite the generator's optical-fit change.

Bold Italic ™ has faired T shoulders and parallel outer M strokes
(15.18–15.36°); its middle diagonal is unchanged, as clarified by the person.
Regular/Italic/Bold Italic numeral drawings outside the requested joins
are retained. The complete upper-left serif joins are enlarged in the proof.
The person accepted this proposal on 2026-10-25.

Eight Regular lint entries are removed; two zone exceptions and one kink
exception disappear, and one extreme count shrinks. No new exceptions or
shaping baselines change in this pass. **95 focused checks pass, one skips**;
all **eight TrueType/CFF hinting checks pass**. Compiled metrics/layout
match, including hmtx; advances, anchors and kerning are preserved.

Proof: `proofs/symbol-joins-before-after-2026-10-25.pdf`.
Details: `docs/symbol-joins-review-2026-10-25.md`.

Next drawing task: Bold Italic dollar's heavy center and swollen endings.
Bold ˀ curve/weight/spacing and Bold Italic ɸ optical weight remain separate.

## Upright aleph integrated; Regular acute counters reviewed (2026-10-25)

The person accepted the upright italic-derived Regular/Bold ℵ at roman
height. Production now uses that drawing, with the smaller versions
available through smcp/c2sc. Existing roman advances and all anchors and
kerning are preserved; italic full-size outlines are unchanged. Fixed
reviewed design inputs avoid a generation cycle. This supersedes the
square-serif roman repair below.

The old roman ℵ lint entries are removed. Minor tangent/extremum finishing
has no new construction findings. The accepted optical weights are recorded
explicitly (three new stroke exceptions, one refreshed); no shaping
baselines change. All three styles reproduce and 83 focused checks pass;
all four CFF hinting checks pass with helper-socket access. Full suite:
183 passed, 3 skipped, plus the four CFF passes. All OTF/TTF/WOFF2 files rebuild.

Production proof: `proofs/upright-aleph-production-comparison-2026-10-25.pdf`.
Details: `docs/upright-aleph-production-2026-10-25.md`.

Continued to the next Regular lint group: eight entries represent four
inherited open counter constructions. Their flagged regions match Theano
exactly. Recommend retention, with annotations refreshed; no font changes
or final visual acceptance recorded for that review.
Proof: `proofs/regular-acute-counters-review-2026-10-25.pdf`.
Details: `docs/regular-acute-counters-review-2026-10-25.md`.

The unreviewed lint backlog is exhausted. Next drawing work: Bold Italic
dollar (heavy center and swollen endings). Bold ˀ curve/weight and spacing,
and Bold Italic ɸ optical weight remain separate.

## Bold ℵ square serif ends restored (2026-10-25)

Weighting tilted four rectangular serif ends; the lower-right foot gained
a backward undercut. The generator now restores the square ends with four
corner moves, retaining every body edge, overall bounds, advance and anchors.
The source is the local straight-stroke drawing, not Libertinus Math;
corrected that stale provenance comment. Earlier Bold Italic repairs remain
unchanged.

The Bold lint exception shrinks from four ledges to two inherited lips.
The proof compares all styles and every affected serif against Regular.
This does not record final visual acceptance of the repaired drawing or
the retained lips. Exactly one outline/CFF charstring changes; all compiled
metrics/layout tables match. No shaping or quality baselines change.

**26 focused checks pass**, including shaping and TrueType/CFF hinting.
All three generated styles reproduce. The production Bold OTF rebuilds
with hints and STAT metadata.

Proof: `proofs/bold-aleph-serif-before-after-2026-10-25.pdf`.
Details: `docs/bold-aleph-serif-review-2026-10-25.md`.

Next review: Regular acute counters in M/Mu and their Cyrillic/accented
relatives, trademark and №. Bold ˀ curve/weight and spacing, dollar drawing,
and ɸ optical weight remain open separately.

## Bold ˀ open counter reviewed; curve drawing remains open (2026-10-25)

The notch is the open upper counter tip where the ball terminal joins the
bowl. The same construction is present in Regular; a scratch rebuild from
the final Bold ɂ still reports one notch. Retain the exception key and
refresh its annotation. This is a review recommendation, not recorded
final visual acceptance.

Separately, Bold ˀ has angular outer bowl/ball corners and an uneven inner
edge. The scratch rebuild is smoother but changes the advance 449 → 380;
it is a drawing candidate, not an adopted repair. Carry that curve/weight
and spacing review forward. No font outlines or generator code change.

Proof: `proofs/bold-glottal-stop-review-2026-10-25.pdf`.
Details: `docs/bold-glottal-stop-review-2026-10-25.md`.

All four style lint checks pass; the 16 source-family spot checks find
only the existing Bold ˀ notch. No exception keys or baselines change.

Next unreviewed lint entry: Bold ℵ (`uni2135`), four ledges. Dollar drawing
and ɸ optical weight remain open separately.

## Italic belted-l attachments repaired; arch family reviewed (2026-10-25)

Italic ɬ's three lint findings were gaps separating its ring and bar from
the stem. Capital Ɬ had the same unflagged fault. The generated-style writer
now joins only their buried ends to the measured base stems. Bold Italic
inherits the connected source; piece extraction excludes rounding slivers
of the stem, and its established advances/anchors are preserved.

Exactly two outlines change per italic weight. Remove the Italic ɬ notch
exception. The nine m/arch entries are inherited open joins, retained for
visual review with refreshed annotations; this does not record the
person's final acceptance or resolve separate weight findings.

**51 focused checks pass**, including shaping and TrueType/CFF hinting.
All three styles reproduce; both affected OTFs rebuild. Advances, anchors
and layout tables match; only Bold Italic ɬ's outline bearing shifts one
unit. No shaping baselines or quality exceptions change.

The person accepted the connected belts after the Charis/Libertinus
comparison: “lets stay with connected belts then” (2026-10-25). This
acceptance concerns ɬ/Ɬ in the two italic weights; the arch-family review
remains separate.

Proof: `proofs/italic-l-belt-before-after-2026-10-25.pdf`.
Arch review: `proofs/italic-arches-review-2026-10-25.pdf`.
Details and Bold Italic proof: `docs/italic-arches-and-l-belt-review-2026-10-25.md`.

Reference check requested by the person: installed Charis SIL 6.200 joins
both belts in both italic weights; Libertinus Serif 7.051 Italic joins ɬ
(the other compared forms are missing). The interior white counter is
retained. The person subsequently accepted the connected belts. The
reference comparison does not establish the original drawing’s intent. Comparison:
`proofs/l-belt-charis-libertinus-comparison-2026-10-25.pdf`.

Next unreviewed lint entry: Bold ˀ (`uni02C0`). Dollar drawing and ɸ optical
weight remain open separately.

## ℵ upper-right terminal join corrected (2026-10-24)

The person accepted the central and lower-left shapes and identified the
remaining upper-right join issue. Removed the reverse spur under that
terminal and the S-shaped wiggle on its connector. The central diagonal,
all lower points and the earlier tip repair are unchanged. The generator
applies both local repairs independently and repeatably.

Only ℵ’s outline changes; advances, anchors and compiled metrics/layout
tables match. One existing quality exception shrinks (four extrema to
three); no new exceptions or shaping baseline changes. **31 focused checks
pass**, including TrueType/CFF hinting and shaping. Bold Italic reproduces
and its production OTF rebuilds.

Proof: `proofs/bold-italic-aleph-upper-join-before-after-2026-10-24.pdf`.
Details: `docs/remaining-bold-italic-lint-review-2026-10-24.md`.

## Remaining Bold Italic lint reviewed; ℵ return repaired (2026-10-24)

Reviewed the seven remaining unreviewed entries with an independent Astra
inspection. Two small backward returns in ℵ's lower tip came from weighting,
not the Old Standard Italic source. The generator now replaces their run
with one smooth curve, preserving its surroundings, advance and anchors.
One lint exception is removed. No quality or shaping baselines change.

The ʸ ң ᵍ ᶤ ₡ ⱥ.sc findings are tapered open counters or stroke crossings.
Recommend retaining those drawings and existing exception keys; the proofs
are ready for the person's review. This does not record visual acceptance
or resolve separate optical-weight findings. Eight Bold Italic glyphs
retain known lint findings, including the earlier ɸ and ɽ.sc reviews.

Proofs: `proofs/remaining-bold-italic-lint-review-2026-10-24.pdf` and
`proofs/bold-italic-aleph-before-after-2026-10-24.pdf`.
Details: `docs/remaining-bold-italic-lint-review-2026-10-24.md`.

Validation: **30 focused checks pass**, including shaping, TrueType and CFF
hinting. Bold Italic reproduces; only ℵ’s CFF charstring changes, with
metrics/layout tables identical. The production Bold Italic OTF rebuilds.

Next unreviewed group: Italic m/arch family and ɬ. Dollar drawing and ɸ
optical weight remain open separately.

## r shoulders and retroflex hooks redrawn (2026-10-24)

At the person's request, both italic r shoulders now have a continuous
rounded inner return, shared with their derived letters. Lowercase ɽ
uses the final r body and a deeper U-shaped hook with a rounded upright
terminal, calibrated from Regular/Bold at its own stem weight. The hook
depth is -420, matching the romans; advances and anchors are retained.
The small-cap narrow leg/swash gap remains unchanged and awaits visual
review. This is a drawing proposal, not recorded final visual acceptance.

The Bold r and ɽ inner stem bumps are smoothed; Bold Italic r’s left
shoulder is rounded as requested in the subsequent visual review.

Proof: `proofs/r-shoulders-hooks-before-after-2026-10-24.pdf`.
Details and validation: `docs/r-hook-review-2026-10-24.md`.

Validation: **175 passed, 3 skipped**, including the separate CFF rerun.
All three styles reproduce; production fonts/proofs rebuild. Compiled
metrics/layout tables match and no shaping baselines change.
Next unreviewed lint entry: Bold Italic ʸ.

## Bold Italic dollar still needs a drawing pass

The person reviewed the straightened bars and found the central part
too thick. Both endings have swellings that should not be there.
These faults remain to be repaired; the bar correction below does not
complete the dollar's design review.

## Bold Italic dollar bars straightened (2026-10-24)

The person identified that dollar's through-strokes were not straight.
All sixteen exposed segments now follow four common parallel 15-degree
edge lines: two 86-unit bars with a 95-unit gap. The generator applies
the repair after rounding. Ball terminals, vertical coordinates,
advance and anchors are preserved. Only dollar changes, and its old
notch finding disappears; removed that exception. No shaping baselines
changed. This supersedes the earlier terminal-only review.

Two repair tests and 16 Bold Italic quality/lint/UFO/shaping checks pass.
Bold Italic TrueType and all four styles' CFF hinting checks pass (CFF
rerun with local helper-socket access after the sandbox blocked it).
Bold Italic reproduces; compiled metrics/layout tables match, with only
dollar's CFF charstring changed.
Proof: `proofs/bold-italic-dollar-bars-before-after-2026-10-24.pdf`.
Details: `docs/bold-italic-dollar-bars-review-2026-10-24.md`.
Next unreviewed lint entry: Bold Italic ɽ. The ɸ optical weight/style
review remains open separately.

## Bold Italic ɉ right bar extended (2026-10-24)

The person found the reviewed bar too short. Its right arm now extends
80 units past the stem at both edges, with a slanted terminal. Only two
corners change; advance, anchors and layout are preserved. The generator
applies the extension. Removed the two-ledge lint exception. A documented
stroke exception records a sampling/classification change in the unchanged
stem; no shaping baselines change.

Regression, lint, quality, 15 composite/UFO checks and TrueType/CFF hinting
pass. Bold Italic reproduces; compiled metrics/layout tables match.
Proof: `proofs/bold-italic-j-bar-before-after-2026-10-24.pdf`.
Details: `docs/j-bar-extension-review-2026-10-24.md`.

## Bold Italic ɸ counter cusps reviewed (2026-10-24)

The two notches are the narrow counter tips where the stem crosses the
bowl. A scratch same-weight o-plus-l-stem rebuild still has two notches,
so it was discarded. Retain the current counters for this lint pass;
the glyph's optical weight and existing style-quality finding remain
open. No font changes or user acceptance recorded.

Proof: `proofs/phi-counter-review-2026-10-24.pdf`.
Details: `docs/phi-counter-review-2026-10-24.md`.
Next unreviewed lint entry: Bold Italic ɽ. The person's dollar-bar
correction is implemented above.

## ɉ bar ledges reviewed (2026-10-24)

The two Bold Italic ledges are the intentional short projections of the
bar past the stem. All four styles share this construction, and the
generator's existing `LEDGE_KEEP` rule explicitly preserves it. Retain
the drawings and exceptions; corrected the misleading italic lint notes
and refreshed the measurements. No font or shaping-baseline changes.

Focused lint confirms exactly two known ledges in ɉ per style, with no
other findings. Proof: `proofs/j-bar-ledges-review-2026-10-24.pdf`.
Details: `docs/j-bar-ledges-review-2026-10-24.md`.
Next: Bold Italic ɸ's two notches in the inherited glyph-lint backlog.

## Bold Italic Ⱦ foot counter repaired (2026-10-24)

Filled the 402-square-unit residual counter where the slash crosses the
foot serif. Only one outline changes; the outer contour, upper counter,
advances, anchors and layout data are preserved. The generated-style
writer applies the repair after rounding. Removed one lint exception
and reduced the known smooth-break count by one. No shaping baselines
changed.

Validation: focused regression, all-style glyph-lint and quality checks,
68 structural checks, and Bold Italic TrueType/CFF hinting pass. All three
regenerated styles match after restoring six sync-renamed scratch files
for comparison in `/tmp`; source sync, Ruff and whitespace checks pass.
Compiled metrics and layout tables match the pre-repair font.

Proof: `proofs/bold-italic-t-slash-before-after-2026-10-24.pdf`.
Details: `docs/bold-italic-t-slash-review-2026-10-24.md`.
Next: Bold Italic ɉ's bar ledges in the inherited glyph-lint backlog.

## Bold Italic dollar notch reviewed (2026-10-24)

The first remaining lint entry is the open channel between dollar's lower
ball and diagonal. The Italic has the same construction; boldening narrows
it enough to trigger the checker (one notch, 34 pixels). Visual review
recommends retaining the terminal and its existing exception. No font
changes or baseline changes. This recommendation has not been reviewed
by the person.

Proof: `proofs/dollar-terminal-review-2026-10-24.pdf`.
Details: `docs/dollar-terminal-review-2026-10-24.md`.
Focused glyph lint: Italic dollar clean; Bold Italic only the known notch.
Next: continue the inherited glyph-lint backlog with Bold Italic Ⱦ.

## Italic ỵ collision repaired (2026-10-24)

The person accepted the dot beside the descender and requested a little
less space. Both italic generators now derive y's DotBelow anchor from
their weighted ink, with a 25-unit gap rather than the trial's 50. The
dot keeps its height and clears the descender in both weights. Precomposed
and combining text follow the same anchor. Only ỵ changes visible ink;
eight related glyphs per style carry the corrected anchor.

Removed the Italic notch exception. Shaping over 2,119,788 strings per
weight changes exactly eight below-mark positions, with no changed glyph
selection or advances; only the two corpus digests are updated.

Validation: **163 passed, 3 skipped** across the full run and separate CFF
rerun (four sandbox helper-socket failures all pass with socket access).
All three styles reproduce; proofs, Ruff and source sync checks pass.

Proof: `proofs/italic-y-dot-before-after-2026-10-24.pdf`.
Details: `docs/italic-y-dot-review-2026-10-24.md`.

Next: continue the inherited glyph-lint backlog below.

## Italic ṫ dot collision repaired (2026-10-24)

The Bold Italic ṫ step came from its dot overlapping the top of t;
Italic had the same collision without a lint finding. The Italic generator
now derives t's Dotaccent anchor from z's clearance and the two ink tops.
Bold Italic inherits the correction. The dot moves 269 units up along the
slant, leaving the same gap as ż (198 / 194 units in the two weights).
Base and mark outlines, advances and kerning are preserved.

Only ṫ's visible placement changes in each italic weight. Six related
glyphs carry the corrected anchor so decomposed text follows it. One
obsolete glyph-lint entry is removed. Shaping over 2,119,788 strings per
style changes exactly ten dot positions above t with a below mark;
only the two corpus digests are updated for these intended changes.

Validation: **161 passed, 3 skipped**, including TrueType/CFF hinting.
All three styles reproduce; proofs, lint and sync checks pass. Diffenator
confirms the intended scope.

Proof: `proofs/italic-t-dot-before-after-2026-10-24.pdf`.
Details: `docs/italic-t-dot-review-2026-10-24.md`.

Next: continue the inherited glyph-lint backlog below. The Regular/Bold
ṫ dot-gap review remains under quality findings; this pass repairs the
italic collision.

## Cedilla attachment steps repaired (2026-10-24)

Shortened the buried tip of the shared capital cedilla in Bold, Italic
and Bold Italic, through `scripts/cedilla.py` in the generated-style writer.
This removes the steps inside Bold Ç Ş ç.sc and Italic Ç ç.sc without
moving attachment anchors or composite offsets. Exactly one master glyph
changes per generated style; the lowercase mark and Regular are unchanged.
Five glyph-lint exceptions are removed. No shaping baselines changed.

Validation: **158 passed, 3 skipped**, including TrueType/CFF hinting.
Before/after shaping of 2,119,788 strings per generated style has zero
differences; compiled metrics and layout tables match. `make proof` passes.
All three generated styles reproduce. Diffenator confirms the intended
scope, including the earlier Greek stack work when compared against HEAD.

Proof: `proofs/cedilla-attachments-before-after-2026-10-24.pdf`.
Details: `docs/cedilla-attachment-review-2026-10-24.md`.

Next: continue the inherited glyph-lint backlog below. The cedilla proof
is ready for visual review.

## Greek breve/grave stack ledges repaired (2026-10-24)

Started the inherited glyph-lint backlog with the two Greek breve +
breathing + grave stacks in Bold and Bold Italic. The grave touched the
breve's right tip. The Bold generator now raises the complete upper pair
to the existing lowercase stacking gap, measured after rounding. Component
outlines, attachment anchors, advances, kerning and features are preserved.
Exactly two glyphs change per bold style; four lint exceptions are removed.
Regular and Italic are unchanged. No shaping baselines changed.

Before/after shaping of 2,119,788 strings per bold style has zero
differences. Diffenator confirms only the intended two changed outlines
per style, with no changed words or layout data. `make reproduce` passes
for all three generated styles.

Validation: **155 passed, 3 skipped** across the full run and the separate
CFF rerun. The sandboxed full run has 151 passes and four CFF helper-socket
failures; all four pass with socket access allowed. `make proof` passes.

Proof: `proofs/greek-breve-grave-before-after-2026-10-24.pdf`.
Details: `docs/greek-breve-grave-review-2026-10-24.md`.

Next: continue the inherited glyph-lint backlog below, beginning with
the cedilla attachment steps in Bold and Italic. The new stack placement
is available in the proof for visual review.


## Bold Italic ʄ recipe review finished (2026-10-23)

ʄ now uses its own Bold Italic recipe, retaining ɟ's descender and lower
stem and drawing the extension, bar and hook at that weight. The former
light recipe's coordinates cut through the heavier base, so the generator
had left ʄ emboldened whole. The final drawing preserves its advance,
anchors and kerning. After visual rejection of the first redraw, the hook
was redrawn with the older open counter and rounded terminal, removing
the pinched inner return.

Exactly one outline changes. The base-retention and light-stroke findings
are resolved, with no new quality or glyph-lint findings. Removed one
whole-emboldening and two quality exceptions. No shaping baselines changed;
before/after shaping over 2,119,788 strings has zero differences.

Validation: **153 passed, 3 skipped**, including TrueType/CFF hinting.
The revised Bold Italic master matches its generator; `make proof` passes.
Master and compiled-font comparisons confirm one changed outline with
unchanged advances and layout rules.

Proof: `proofs/bold-italic-j-hook-before-after-2026-10-23.pdf`.
Details: `docs/bold-italic-j-hook-review-2026-10-23.md`.

Next: the inherited outline-fault backlog below (glyph lint).

## К/к base contour review finished (2026-10-23)

Finished К/к and к.sc in both italic weights, with Қ/қ and the Ќ/ќ
composites following their bases. Five glyph files change per style;
18 construction findings disappear, with no increased quality findings.
Removed ten obsolete quality entries. No shaping baselines changed.

The earlier eight-unit advance change came from the Bold generator
switching its temporary optical-spacing reference when К's unflagged
upper joins were smoothed. Restricting К's repair to its lower leg keeps
the existing spacing calculation. All advances, anchors, kerning,
features and the accepted upstream signs are preserved. Before/after
shaping of 2,119,788 strings per italic weight has zero differences.

Validation: full suite **152 passed, 3 skipped**. `make reproduce` passes
for all three generated styles; `make proof` succeeds.
Diffenator confirms only the five intended outlines per style, with no
changed words, metrics or layout rules.

Proof: `proofs/italic-ka-before-after-2026-10-23.pdf`.
Details: `docs/italic-ka-review-2026-10-23.md`.

Bold Italic ʄ's whole-emboldening/base-retention recipe review is now
finished above.

CI's 2026-10-23 failure was a runtime mismatch: `ubuntu-latest` selected
Python 3.14, whose newer Unicode data changed casing, the shaping corpus
and generated features (11 failures). Python 3.12 is now pinned locally
and in the workflow, matching the verified Unicode 15.0 baselines.

## Inherited italic contours and ɮ check finished (2026-10-23)

Finished Ж/ж, Bulgarian ж, ж.sc and җ.sc in both italic weights, with
bases repaired before derivation and final rebuilding/rounding artifacts
finished locally. Also cleaned the inherited bodies of ʑ Җ җ Қ қ.
Exactly ten outlines change per style; 95 construction findings disappear
(55 Italic, 40 Bold Italic), and no quality finding increases. All advances,
anchors, kerning, features and the accepted upstream signs are preserved.
Forty obsolete quality entries were removed, including stale entries from
the earlier ʄ/₸ work. No quality exceptions were added.

ɮ's style check now compares its declared l-and-ʒ construction with the
same-style recipe. A regression test confirms that substituting a sloped
Roman ɮ still fails; base-retention and stem checks remain active.

The full suite passes: **150 passed, 3 skipped**, including both formerly
failing quality checks and TrueType/CFF hinting. `make reproduce` passes
for all three generated styles. Before/after shaping of 2,119,788 strings
per italic weight has zero differences. The diffenator word-list sweep
confirms only the intended outlines and small left-sidebearing changes;
no changed words, advances or layout rules.
Proof: `proofs/italic-base-contours-before-after-2026-10-23.pdf`.
Details: `docs/italic-base-contour-review-2026-10-23.md`.

Next: review the weight-sensitive К/к base cleanup. The discarded trial
changed Bold К's ink by about 3.7% and the К/Ќ/Қ advances by eight units;
those base drawings remain unchanged. Bold Italic ʄ's older
whole-emboldening/base-retention recipe task also remains open.

## Shaping baselines reconciled (2026-10-23)

Reviewed the outstanding Bold/Italic/Bold Italic shaping differences
against the revisions that produced their recorded baselines. Those
reference fonts reproduce the old golden cases and digests exactly.
Across 2,119,788 strings per style, all differences follow the committed
₸, ƈ, ʄ, ɮ, ʑ and Cyrillic descender advance/anchor changes. Glyph
selection, kerning and feature rules are unchanged.

Updated only the three affected golden snapshots and full-corpus digests;
Regular is unchanged. All 12 regression checks pass across the four
styles (coverage, golden shaping and full-corpus digests). The six prior
shaping failures are resolved; the two quality failures left at that stage
are now resolved by the contour/checker work above.
Review, counts and metric deltas:
`docs/shaping-baseline-review-2026-10-23.md`.

The Ж/ж family and ɮ's style heuristic are now finished above. The К/к
weight-sensitive base review and Bold Italic ʄ's recipe review remain open.

## Italic contour finishing implemented (2026-10-23)

The eight reviewed letters ƈ ʑ ɮ ʄ Җ җ Қ қ are finished in both italic
weights through `scripts/italic_contours.py`, called by both generators.
The pass repairs local tangent breaks, eases ƈ's shoulder, and adds missing
extrema after slanting. The light қ keeps its original leg weight.

Exactly eight outlines change per style, with advances, anchors, kerning,
features and other glyphs preserved. Construction findings fall by 24
(14 Italic, 10 Bold Italic); no quality finding increases. Fourteen obsolete
quality entries were removed and six remaining counts tightened. Shaping
baselines are unchanged.

Validation: `make reproduce` passes for all three generated styles. The
focused structural, contour and quality run has 83 passes, one skip and
two failures from the remaining inherited quality findings. Both italic
weights pass TrueType and CFF hinting (four tests). Before/after shaping
of 2,119,788 strings per italic weight has zero differences; final cmap,
hmtx, GPOS, GSUB and GDEF tables match that comparison. All ten accepted
upstream Cyrillic sign files remain byte-identical to upstream. The full
suite was not rerun; earlier shaping-baseline failures remain separate.

Proof: `proofs/italic-contours-before-after-2026-10-23.pdf`.
Details: `docs/italic-contour-review-2026-10-23.md`.
The shaping snapshots have since been reconciled above. Remaining work:
the inherited base-letter findings and ɮ's style heuristic. Bold Italic ʄ's old
whole-emboldening/base-retention issue remains a separate recipe task.

## Verification before contour finishing (2026-10-23, after upstream pull)

`make reproduce` passes for Italic, Bold and Bold Italic in this
environment, including the uncommitted italic fixes. The previously
reported FontForge `l.sc` collapse and Bold small-cap/kerning drift did
not recur. No master outlines were changed during this check.

Removed five obsolete test exceptions: Regular/Bold ₸'s kink findings,
and Bold Italic ƈ җ қ's emboldened-whole entries. The latter now use
their own recipes. No shaping baselines or new quality exceptions were
accepted.

Validation: full suite 133 passed, 3 skipped, 13 failed. One failure was
the obsolete Bold ₸ quality entry removed above; the focused cleanup
checks now pass (3 tests). Four CFF hinting tests failed because the
sandbox blocked the hinter's helper socket; all four pass outside it.
Eight failures remain: quality in Italic/Bold Italic, and golden shaping
plus full-corpus digests in Bold/Italic/Bold Italic. Glyph lint and
Cyrillic pairs passed. The full suite was not rerun after the focused fixes.

The fresh quality audit reports new findings on Italic ɮ ʑ Җ җ Қ and
Bold Italic ƈ ʑ Җ җ Қ қ. Most are smooth-node, kink or extreme findings;
ɮ's style finding is the intended move of ʒ beside l's stem, described
below. Review the geometry before accepting any new quality entries.

Contour review is recorded in
`docs/italic-contour-review-2026-10-23.md`, with context and detail sheets
in `proofs/italic-contour-review-2026-10-23.pdf`. The overall constructions
are worth retaining. That review led to the implemented local finishing
pass above; several remaining flags are inherited from the bases.
The accepted upstream Cyrillic sign
drawings supersede the earlier hand-edited ь ы ъ and rejected Bold Italic
versions; preserve those upstream drawings.

## Cyrillic italic redesign accepted (2026-10-23)

New drawings for ь ы ъ and Bulgarian ь/ъ in both Italic weights are in
`scripts/cyrillic_signs.py`, called by both style generators. The five
glyphs share the bowl construction; ы shares ь's complete outline. The
Bold Italic is drawn at its weight, with continuous ascender joins rather
than emboldened splices. Advances and anchors are preserved explicitly.
Only these five outlines per style changed; small caps are unchanged.

The drawings have no glyph-lint or design-quality findings. Removed the
resolved exceptions, including Bold Italic ъ's CFF hinting exception; no
shaping baselines were changed. The person accepted the comparison in
`proofs/cyrillic-before-after.png` for publication. The earlier rejected
Bold Italic verdict below describes the old outlines.

Focused regeneration: `.venv/bin/python -I scripts/cyrillic_signs.py UFO`,
then normalize. This updates the complete master in place using the same
drawings as the full generators and does not rerun unrelated small caps.
`tests/test_cyrillic_signs.py` verifies regeneration, metrics and idempotence.
The original check reported a FontForge small-cap failure (italic l.sc
collapsed to height 130, then smallcaps.py failed in beside_l), plus Bold
small-cap/kerning drift. A fresh full `make reproduce` after the upstream
pull passes for all three generated styles; see current verification above.

## Historical: Italic glyph fixes (2026-10-22)

The person's list of italic faults, worked through in one session. These
changes and the contour finishing pass are committed in `5cea3451`; the
shaping snapshots are reconciled above. The notes below record that older
session's state, including its then-open failures. See the newer sections
above for their resolution; the Cyrillic sign redesign was accepted upstream.

Done (in the generators unless noted):
- ƈ: a speck (rest of c's ball) cut away (make_italic ITALIC_RECIPES).
- ʄ: the recipe's stem/bar/curl numbers set to ɟ's current stem (350-495
  in the derive frame; it was tuned before the reweighting).
- җ: descender upright like қ ң ҷ (it leaned with the leg).
- Қ Җ: Ц's wedge tail replaced by the lowercase construction (exit stroke
  cut, make_italic.descender); both added to NO_TRANSPLANT.
- ʑ: rebuilt as the Regular's: bottom stroke runs on and thins (poly) into
  a small loop at its end, upright tail through the loop's left side. The
  person rejected the first version (big ɕ-like loop) as worse.
- ɮ: ʒ set whole beside l's stem as in the Regular (ZH_DX = 150 right, its
  top bar run on to the stem by a rect), stem rect matched to l's (no step).
  quality check now says "closer to the Regular's ɮ than to l": intended.
- ₫: line fitted to the italic d (ITALIC_RECIPES). ₸ (person said 20B6,
  meant 20B8): second line moved ABOVE the T in all styles (derive.py,
  as Charis/Libertinus); the Regular's ₸ rebuilt by derive.py (a draft now).
- ь ы ъ: Old Standard's outlines edited in the Italic and marked "drawn"
  (kept by reruns, but no longer follow weight changes). ь/ы: stem's
  outer edge one curve from bowl to hook, counter corner (19.5°) smoothed.
  ъ: Old Standard's design kept, its curled ear at the stem top replaced
  by one rise from the wave, the flag terminal's wobble smoothed. Scripts
  that made the edits (re-runnable on Old Standard's original points
  only): `build/italic-fixes-2026-10-22/redraw_{soft,hard}_sign.py`.
  Tried and dropped: ъ built from ь plus a flag (reads as ь, or the ear
  comes back).
- Bold Italic (make_bold.py): own recipes at its weight (ITALIC_BOLD_RECIPES
  + ITALIC_BOLD_REBUILD) for ʑ, ƈ, Қ Җ җ қ (descender balls 0.48 of the
  stroke so the curl ends without a step; Җ sweep 155 so the ball clears
  the middle stem's foot); ь pinned to ITALIC_BOLD_BY_WEIGHT (the rounder
  way came out light, 0.82).

**The person's verdict on the Bold Italic: bad before, bad after (only
differently).** The emboldened Cyrillic soft signs and their kin (ь ы ъ,
the Bulgarian ь ъ with a spur/notch where bowl meets the raised stem, ы's
dented stem) need a real pass of their own, not more patching: likely
recipes drawn at the Bold Italic's weight or a different emboldening for
these letters. Look at `sg2.png`-style before/after sheets (render tool
below) with the person.

Still failing in `make test` (all from the changes above):
- golden shaping + full-corpus digest: Italic, Bold, Bold Italic (₸, ʄ
  widths etc.): `update_test_data.py --golden --digest` once accepted.
- quality lists: Regular/Bold `uni20B8 kink` fixed (remove); new small
  kinks/smooth/extremes on ʑ Қ Җ җ ɮ ƈ ь (2-8°); `--quality`.
- emboldened-whole Bold Italic: ƈ җ қ no longer whole (list shrinks).
- glyph lint Bold Italic: new notches uni044A.loclBGR, uni044C.loclBGR
  (the Bulgarian forms, see verdict above).
- Cyrillic pairs Bold Italic: ль at 0.175 outside the references (ь's
  left side moved): an ITALIC_BOLD_KERNING entry, or wait for the pass.
Then `make reproduce` (expected clean), commit with the attribution line.

Not done from the list: nothing; everything the person named was
addressed, Bold Italic quality open as above.

Tools for this kind of work (in `build/italic-fixes-2026-10-22/`, copy
out before `make clean`): `render.py UFO OUT.png GLYPH|U+XXXX ...`
(outline + points; INK=1 solid; SCALE TOP BOTTOM env), `up.py UFO OUT
GLYPH...` (upright copy + render), `try.py OUT CH...` (rebuild a derive
recipe in the current Italic: frame lacks the generator's ~16-unit
respace offset). For exact results: copy the Italic UFO to scratch and
run `make_italic.py REGULAR COPY` (~22 s) or `make_bold.py ITALIC COPY`.
Lessons: curl `t` is (across vertical parts, across horizontal parts), not
start/end; curl radius must exceed half the stroke or the counter slits;
recipe coordinates are in the derive frame (final + ~16 in the Italic).

## Outline faults left (glyph lint, `tests/data/glyph-lint-*.txt`)

- Notches are measured at four raster phases now (2026-10-21), so the
  lists hold what stays a notch. **Bold Italic** 8 glyphs (ɸ
  ɽ.sc ʸ ң ᵍ ᶤ ₡ ⱥ.sc; updated 2026-10-24 after the Cyrillic sign,
  Greek stack, ṫ dot, Ⱦ foot counter, ɉ bar, dollar bar, r-family and aleph repairs). ᶤ ⱥ.sc
  ℵ came with the weighting change (near-threshold notches at joins, for
  the eye). **Italic** 10: ɉ and the
  narrow arch crotch of m ḿ ṃ т ш ɯ at exactly the threshold (Old
  Standard's design).
- Regular 10, Bold 5 (see the lists; Greek stack ledges and cedilla steps
  repaired 2026-10-24).

## Derived letters still emboldened whole (junctions thicken)

`tests/data/emboldened-whole-*.txt`: Bold 37, Bold Italic 28, Italic 0
(2026-10-23: the Italic is weighted as its letters are taken, so nothing
in it is weighted whole any more).
Mostly hooks, attached pieces and curls whose recipe, rerun on the Bold,
"strays" from the emboldened letter or "misses". Candidates for recipes
drawn at the Bold's weight (`BOLD_RECIPES` / `ITALIC_BOLD_RECIPES`) or a
fixed rederive; the Bulgarian forms (в г ж ъ ь ю) and two rhotic letters
in the Bold Italic too.

## Quality findings backlog (`tests/data/quality-*.txt`)

| | Regular | Bold | Italic | Bold Italic |
|---|---|---|---|---|
| extreme (curve past its ends, no point there) | 15 | 157 | 281 | 527 |
| kink (corner meant smooth) | 101 | 208 | 569 | 609 |
| smooth (smooth node broken > 2°) | 74 | 65 | 487 | 209 |
| stroke (darker/lighter than its kind ±10 %) | 78 | 69 | 127 | 111 |
| zone (flat edge near a zone) | 58 | 59 | 143 | 139 |
| slant | | | 64 | 71 |
| width | | 27 | | |
| accent gaps | 3 | 3 | 2 | 2 |

(Counts of points, 2026-10-21. The italics' slant includes W Ⱳ w.sc
ⱳ.sc: the uncrossed W's thick diagonal leans 5°, inside the check's
window for stems.)

- Most of the Italic's are Old Standard's own outlines ("known at the
  start"); the Bold Italic inherits them. A cleanup pass on the Italic's
  sources (extremes added, near-smooth nodes made smooth) would lower both,
  but changes many glyphs: do it as its own step, with `make diffenator`.
- **stroke:** review with `make strokes` (`build/quality/strokes-STYLE.pdf`);
  designed exceptions go on the known lists.
- **Italic reweighted (2026-10-21, done):** lighter, more even, 13 tighter;
  then weighted as its letters are taken (nothing weighted whole), the W
  uncrossed (1.25 cap heights, of two narrowed Vs; w.sc of v.sc, Ⱳ ⱳ.sc
  ₩ refitted) and a's bowl 40 lighter (FONTLOG). Left from it:
  - Review the Italic's drafts (all derived letters, small caps and
    figures are drafts): `drafts-review-Italic.pdf`,
    `smallcaps-review-Italic.pdf` (`make proof`).
  - r/I reviewed 2026-10-25: the lighter I trial is approved and integrated;
    r is retained. See the current entry above.
  - Old-style figure redesigns are accepted in all four styles; see above.
  - Bold Italic Ⱳ: approved curl-connection repair integrated 2026-10-25;
    see the current entry above.
- **accent gaps (2026-10-21, done for the Greek capitals):** the breathings
  and tonos beside Ὀ Ὁ Ό … sit at one height, as Libertinus's do; the
  check measured the capitals' overshoot. It skips marks set beside a
  letter now, and counts from the flat zone a round edge overshoots (dots
  below and hooks sit at one height in Libertinus and Charis too). Left:
  i j (their own dot, designed). Regular/Bold ṫ's gap was approved and
  matched to ż on 2026-10-25; see the current integrated entry above.

## Hinting

- Letters still off their zone (glyphs): TrueType Regular 3, Italic 10,
  Bold Italic 3; CFF Regular 1, Bold 1, Italic 4, Bold Italic 3
  (`tests/data/hint-zones*.txt`). Most are designed (𝔖 Fraktur, the horn,
  Ʋ); a few round bottoms one row off O's in the v35 interpreter only.
  New in the Italic (2026-10-21): v.sc w.sc ѵ.sc ⱳ.sc bottoms and ae.sc's
  top a pixel or two off. The Þ/æ.sc reports were counter false positives,
  resolved by the 2026-10-25 review above; Þ's unnecessary 27 ppem counter
  correction is removed. Remaining small-cap tip reports stay open.

## Features

- The italics lack the Regular's extra ligatures (ct st, fb fh fk ft and
  their ff forms, the long-s ligatures), left out with their rules
  (`make_italic.drop_ligatures`, styles-agree-Italic.txt). Italic forms
  would have to be drawn.

## Small leftovers

- **ɺ, Bold Italic:** the arm's bracket bulges 6 units past its end (the
  extreme check allows 5), at 617,1384, where the italic stem leans back
  past the end point. Its foot has the same at HEAD (9 units, 191,66).
  Likely the italic's natural shape rather than a fault.
- **Smooth rounding in the Italic:** `make_italic.py` saves with
  `write(..., smooth=False)`. With `make_bold.round_smoothly` the Italic's
  smooth breaks would go 678 → 540, but the Bold Italic is made of the
  Italic's outlines, and the unit shifts move about 14 Bold Italic glyphs
  across the checks' thresholds (new smooth breaks and extremes there).
  Turn it on only together with a look at those.
- **Four Bold Italic pairs** (of Wh it ba) measure tight against the
  references; reviewed 2026-10-20 and left (they look right beside Bodoni
  Moda). Nothing to do unless the proofs say otherwise.
- **Git stash `batch2-wip`** (91 files, older work): check whether anything
  in it is still wanted, then drop it.
