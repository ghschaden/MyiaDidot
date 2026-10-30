# Lower-return pilot — 2026-10-30

Stage 3 now has a read-only lower-counter detector, sampled clearance profiles,
and a conservative graph of observed paired-stroke neighbours. It does not yet
establish real-font interior/exit roles or authorise reusable shoulders. Missing
stem support remains visible instead of being filled by an assumed skeleton.

## Implementation

`--lower-returns` on `scripts/shape_relationships.py` enables paired boundaries
and adds a separately versioned `lower_returns` section to the report. Restrict
work with `--boundary-glyphs`. `returns.svg` overlays the counter paths in blue
and eight sampled clear cross-sections in magenta; the normal `proof.svg` can
show the paired-stroke evidence alongside it. HTML links to both artifacts.

The pilot deskews source contours, finds local counter minima with ink below and
white space above, and follows both arms to 0.08 em above the floor. Angular
junctions, interrupted sections and arms that cannot reach the observation height
are withheld with reasons. Horizontal clearance is measured at eight heights;
it is not a global counter minimum. Nonzero winding and sampled interior probes
are used, not a certified topology solver.

Each shoulder seeks nearby observed, predominantly vertical paired strokes.
Both neighbours must be unique and distinct for `supported-local-turn`. Competing
or missing observations yield `unresolved`. A turn is `interior` only when its
right observed stroke also supports a following turn's left side. An unmatched
end of this graph remains role-unresolved: terminal and tail attachment context
has not been established. Attachment vectors, original contour references,
geometric locators, source hashes and all neighbour candidates remain in JSON.
Components are explicitly omitted rather than silently treated as empty shapes.

## Current-source pilot

Revision: main `cef605f813e307acd419326bd6a4821cd5e10c64`, using the frozen,
file-for-file verified UFOs from the preceding Stage 2 evaluation. Per-style
source and implementation hashes are in the reports. No sources were changed.
Artifacts: `build/glyph-review/lower-returns-2026-10-30/`.

Scoped glyphs: u/ų/и/ц/ш/щ/џ, plus n/h/m and v/w controls. All four style return
overlays were opened and inspected. The italic styles expose lower counters in
this Cyrillic set; the upright styles have different construction and must not
be assigned italic return ancestry.

| Style | Lower-turn candidates | With two unique distinct stem neighbours | Resolved roles |
| --- | ---: | ---: | ---: |
| Regular | 2 | 0 | 0 |
| Italic | 22 | 0 | 0 |
| Bold | 2 | 2 | 0 |
| Bold Italic | 22 | 0 | 0 |

The upright candidates are u and ų. In the italic styles, the overlays locate
two turns in u/ų/и/ц/џ, three in ш/щ, one lower exit in each of n/h/m, one in v
and two in w. These are geometric candidates, not confirmed anatomical matches.
Rounded v/w in italic cannot be rejected merely because upright v/w are angular.
Their neighbour/role evidence remains unresolved. Upper arches are not identified
as lower returns; the n/h/m candidates are their actual lower exits.

The descender floors in ц/щ/џ and the ogonek in ų fail the two-shoulder observation
window and are explicitly listed as omissions. This preserves them as separate,
unresolved attachment context; it does not claim to have recognised their roles.
The main body counters remain measurable. No user-selected knee widths or tail
geometry were changed.

`comparisons.json` records same-style comparisons (ų/u, и/u, ц/и, щ/ш, џ/и)
and each non-Italic style against Italic. These use left-to-right ordinal pairing
only when candidate counts agree; they are explicitly unresolved diagnostics,
not verified base inheritance or cross-style matching. In Bold Italic:

- и/u and џ/и have identical sampled opening profiles.
- ų/u differs by −0.295 and −3.073 units at the two observation openings.
- ц/и differs by 0 and −2.751 units.
- щ/ш differs by 0, −0.443 and −2.191 units across its three openings.

These describe the fixed-height sections, not a judgement that any difference
should be removed. Different candidate counts are retained instead of forcing
correspondence. The comparison script is retained beside the JSON.

## Validation and remaining work

77 focused tests pass through `make test` and the shared lock. Twelve new pilot
cases cover a rounded counter, reversed traversal, contour start, cubic
subdivision, deskewing, upper-arch and angular-V controls, missing and competing
neighbours, genuine shared-neighbour interior linkage, interrupted counters,
component-only input and read-only CLI output. Ruff and `git diff --check` pass.
The shared-neighbour control supplies independently known stem observations;
it checks graph logic, not detector accuracy on unioned real glyphs.

Stage 3 is **not complete**. The real-font role graph is still limited by Stage 1
coverage and by strokes spanning more than one turn arm. Next work is to establish
local arm-to-stroke support and explicit terminal/tail context, preserving the
refusal cases. Only then can same-role matching, upper-arch expansion, the
historical bad-m-splice negative, and independent-family accuracy evaluation be
meaningful. No smoothing, repair solver, production build, shaping, hinting or
acceptance update was performed.
