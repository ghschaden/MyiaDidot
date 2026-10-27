# A minimal working typographic vocabulary

For practical use, the [shape-consistency workflow](shape-consistency.md) now
builds on this study with explicit optical contexts, pinned donors, protected
scratch candidates and dependency/layout checks. Production consistency takes
priority over reducing the number of families.

**Six families are the best-supported working vocabulary in this study:**
straight stroke, shoulder, rounded return, bowl, serif and dot.

There is a precise, limited minimum behind that recommendation. For 180
anatomical samples across all four styles, all 4,140 partitions of eight starting
roles were searched. Six is the smallest family count whose mean fitting error
is within one percentage point of the eight-role baseline. The same answer
holds with budgets of 0.25, 0.5 and 2 percentage points.

This establishes a minimum **within the tested model**, not a universal minimum
for typography or a six-piece reconstruction of the entire font. The model uses
one measured silhouette per family per style, with specified geometric
normalisation. Its loss budgets are study choices, not visual acceptance limits.

## The vocabulary

| Family | Typographic function | Variations it must retain |
|---|---|---|
| **Straight stroke** | Stem, crossbar, diagonal, rule | Length, direction, thickness, taper; some italic edges also bow slightly |
| **Shoulder** | Asymmetric transition from a thin joining stroke into a thick stem; n/h/m and the reversed u connection | Span, rise, thick/thin transition, entry position, interior/exit context |
| **Rounded return** | Open rounded bend joining two substantial sides through a thin crown or bottom | Span, depth, side weights, crown weight, stress, asymmetry |
| **Bowl** | Closed enclosing stroke with a counter, as in o/O/0 | Outer proportions, counter proportions, contrast, stress, overshoot, upper/lower asymmetry |
| **Serif** | A lateral ending attached to a stem | Projection, thickness, bracket shape, taper, top/foot orientation |
| **Dot** | Compact solid mark, including punctuation dots | Size, aspect ratio, tilt and roundness |

The family descriptions name useful design parameters. This study **does not
fit a continuous generator for all those parameters**: it measures actual
silhouettes and tests which roles can reasonably share them. The supplied sample
geometry and selected representatives make that distinction inspectable.

The list removes redundant names rather than design decisions. A diagonal is
an oriented straight stroke; an isolated bar interior uses the same family.
Likewise, u's central return can be oriented as a shoulder. By contrast, an
o-like rounded return and an n-like shoulder have different weight transitions;
calling both simply “a curve” hides an important distinction.

[View the six families in all four styles](../build/glyph-review/typographic-vocabulary/vocabulary.svg).
These pictures are normalised to squares to compare shapes: their displayed
proportions and thicknesses are not font design recommendations.

The [exemplar library](../build/glyph-review/typographic-vocabulary/vocabulary.json)
contains the six named families, their selected representative per style, and
the measured variants needed by the 5% covering experiment. Each entry retains
its donor, crop, orientation and actual outline commands; it is a reusable
palette of measured parts, not an implemented continuous shape generator.

## A vocabulary needs joining rules

A serif is attached to a stem; a shoulder enters one stem and becomes another;
a counter is the white region enclosed by a bowl. Those relationships belong in
the grammar, not in an ever-growing list of primitive shapes.

The following are proposed assembly rules, not implemented full-glyph recipes:

```text
place(part, position, orientation, dimensions)
continue(part_A, part_B, tangent, weight)
branch(stem, arm, attachment_height, join_thinning)
terminate(stroke, cut | serif | dot_attachment)
attach(base, mark, anchors)
reserve(counter, clearance)
```

Each connection needs a location, tangent and local stroke weight. Entry,
interior and exit connections must remain distinct in Italic. This is where the
earlier attempt to build m by repeating n failed: it repeated the entry and exit
features at an interior connection.

Symbolically, H uses three straight strokes plus serif endings; n uses stems,
a shoulder and style-specific endings; ö uses a bowl and two placed dots. These
descriptions are useful design structure, but they do not establish exact
generation from six fixed silhouettes. Ball terminals, teardrops, ears, tails
and complex joins need further sampling before their status as compositions or
additional families can be decided.

## How the minimum was tested

Run:

```sh
.venv/bin/python -I scripts/typographic_vocabulary.py
.venv/bin/python -I -m pytest tests/test_typographic_vocabulary.py
```

[Open the study and all comparisons](../build/glyph-review/typographic-vocabulary/index.html).

The initial eight roles are stem, bar, diagonal, shoulder, return, bowl, serif
and dot. There are 45 samples per style, taken from 24 donor glyphs. Sample
selection is explicit and recorded in
[samples.json](../build/glyph-review/typographic-vocabulary/samples.json).

The extraction removes the style's slant, clips a named anatomical region, and
applies only recorded orientation changes, centreline straightening for shafts,
and independent axis scaling to a 1000 × 1000 box. It does not deform curves to
force a match. Bar interiors exclude their terminal quarters; an italic hyphen's
curved ends are not evidence that its central stroke is a different family.
The shoulder crop stops inside the receiving stem to avoid borrowing the next
shoulder from m. Crop choices remain part of the experimental assumptions.

For each candidate family and style, its representative is the measured sample
with the lowest average ink difference to the other samples: a **medoid**. Ink
difference is symmetric-difference area divided by union area. The implementation
uses the equivalent identity `2 × union_area − area_A − area_B`, which avoids an
additional Boolean operation on almost coincident edges.

All set partitions of the eight roles are enumerated. The best partition at
each family count is selected by fitting error alone. Its held-out result is
then measured by excluding every region from the target's donor glyph, choosing
a new medoid from the remaining glyphs, and comparing the omitted sample.

### Exhaustive result

| Families | Lowest mean fitting error | Held-out donor-glyph error |
|---:|---:|---:|
| 1 | 25.92% | 25.98% |
| 2 | 19.71% | 25.07% |
| 3 | 14.58% | 15.45% |
| 4 | 10.69% | 11.50% |
| 5 | 6.89% | 8.09% |
| **6** | **3.73%** | **5.09%** |
| 7 | 3.70% | 4.93% |
| 8 | 3.70% | 4.93% |

The optimal six-family partition is exactly the proposed vocabulary: it merges
stem/bar/diagonal and retains the five remaining roles. Seven and eight buy
almost no further improvement. The best five-family partition merges dots with
straight strokes; it is numerically less bad than the other five-family options,
but visibly and typographically unpersuasive. A different five-family proposal
that merges shoulders with rounded returns is substantially worse: 8.20%
fitting error and 12.45% held-out error.

These are sample-weighted averages, not character-frequency-weighted or
role-balanced measures. There are more straight-stroke samples than bowls.
The exhaustive search proves the numerical result for this finite model; it
cannot remove choices made in selecting the corpus and allowed transformations.

## Why not make a bowl from two returns?

That reduction was tested separately as an actual composition:

```text
bowl_candidate = upper(return) + rotate180(upper(return))
```

The return comes from the bottom half of the target bowl, oriented upward. The
two copies are joined at the midpoint. Across o/O/0/o.sc in all four styles,
mean ink difference is **2.79%**, even using the target's own half. Using a return
from a different donor glyph raises it to **16.61%**. The former tests symmetry;
only the latter tests independent shape reuse.

Regular o is close at 0.064%; Bold o is closer at 0.0067%. Italic O differs by
6.76%, and Italic o.sc by 7.15%. Inspection shows upper/lower optical asymmetry,
not a serialization failure.

[Inspect the bowl reduction](../build/glyph-review/typographic-vocabulary/bowl-reduction.svg).

Two **independently parameterised** returns can of course describe a bowl, but
that moves the bowl's design information into the parameters and its closure
constraints. It does not demonstrate a smaller total design description. I
would therefore keep bowl as a first-class typographic family for now.

## Six families are not six templates

The study also greedily covers each family's samples with multiple measured
silhouettes. At a 5% normalised ink-difference allowance, the total selected
templates are:

| Style | Templates across the six families |
|---|---:|
| Regular | 14 |
| Italic | 15 |
| Bold | 16 |
| Bold Italic | 15 |

These are upper bounds from greedy covering, not proven minimum template counts.
They demonstrate why the type vocabulary must be separated from its stylistic
parameters and contextual variants. At this tolerance, each of the four sampled
bowl drawings still requires its own template in every style.

Visual inspection also finds real differences between the two m shoulders,
between italic punctuation dots and letter dots, and between capital and small
capital bowls. The worst six-family single-template residual is 38.68% in the
Italic shoulder group. An average near 4% does not make every proposed reuse
acceptable. None of these substitutions has been installed in a source font.

## Verification and scope

Study date: 2026-10-27. Source revision:
`e30747e339a18415e6a7c70fcb47ec7f13b55774`. Exact font-content fingerprints are
recorded in [report.json](../build/glyph-review/typographic-vocabulary/report.json).

- All 180 samples and all 4,140 partitions were evaluated.
- Five tests cover exhaustive partition enumeration, counter-aware area
  differences, normalisation, symmetric bowl assembly, exclusion of all parts
  of a held-out glyph, and recovery of a known six-cluster optimum.
- Ruff passes for the new script and tests.
- The four-style vocabulary atlas, bowl comparisons, contextual samples and
  selected detailed overlays were rendered and visually inspected.
- The source UFOs, generated styles, features, metrics and acceptance records
  remain unchanged. Full shaping or hinting regression tests are not relevant
  to this separate read-only anatomical study.

The corpus is Latin-focused. It does not establish a semantic decomposition of
all Greek, Cyrillic, IPA, mathematical, Fraktur or ornamental forms. Held-out
glyphs may still have related drawings or shared generator ancestry. Nor does
this test optimise continuously parameterised curves, allow arbitrary Boolean
composition in the merger search, or balance errors by text frequency.

The [complete geometric grammar](shape-grammar.md) still supplies exact coverage
of every glyph. The six-family vocabulary is a smaller, interpretable design
layer supported by this experiment. Extending its anatomical coverage and
fitting explicit family parameters are necessary before claiming a minimal
typographic grammar of the entire Myia Didot family.
