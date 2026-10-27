# Shape grammar experiment — 2026-10-26

Follow-up: the [complete geometric grammar](shape-grammar.md) now covers every
glyph in all four styles with exact reconstruction. This document retains the
findings from the initial, deliberately approximate typographic-parts trial.

The first prototype demonstrates useful reuse, but **does not establish a
minimal vocabulary or coverage of every glyph**. A shared structural grammar
needs distinct entry, interior and exit joins, particularly in Italic.

Reference: working sources at `e30747e339a18415e6a7c70fcb47ec7f13b55774`, clean
before the experiment. All four UFOs were read without modification. No font
was rebuilt, no candidate installed, and no design accepted.

## Run and inspect

```sh
.venv/bin/python -I scripts/shape_grammar.py
.venv/bin/python -I scripts/shape_grammar.py \
  --replay build/glyph-review/shape-grammar/Italic.json
.venv/bin/python -I -m pytest tests/test_shape_grammar.py
```

- [Overview and measurements](../build/glyph-review/shape-grammar/index.html)
- [Regular proof](../build/glyph-review/shape-grammar/Regular.svg)
- [Italic proof](../build/glyph-review/shape-grammar/Italic.svg)
- [Bold proof](../build/glyph-review/shape-grammar/Bold.svg)
- [Bold Italic proof](../build/glyph-review/shape-grammar/BoldItalic.svg)
- [Full metrics](../build/glyph-review/shape-grammar/metrics.json)

The outputs live under `build/` and are reproducible, not tracked acceptance
artifacts. Each JSON includes the extracted palette, recipes, calibration
measurements and reference outlines. Replay needs no UFO. The SVGs show original
ink, coloured pieces, overlays and a 24 px/em outline comparison. They do not
represent compiled shaping or hinted rasterisation.

## What the grammar actually contains

The executable expression language is:

```text
shape := path(commands)
       | rect(x0, y0, x1, y1)
       | ref(name)
       | transform(affine_matrix, shape)
       | union(shape, ...)
```

`path` uses the fontTools pen command representation, including contour closure
and curve control points. Counter direction is retained. Boolean union resolves
overlaps. Named references may refer to other expressions; cycles are rejected.

The structural palette has ten stored pieces **per style**:

| Parts | Source and limitation |
|---|---|
| Left and right capital stems | H, including serifs; extracted separately |
| Crossbar | H; its thickness is measured through its centre |
| Left and right lowercase legs | Lower 60% of n, including feet or exit strokes |
| Shoulder | Upper 40% of n, including the entry serif/stroke |
| Lowercase and capital bowls | Complete o and O contours, not a single scaled bowl |
| Two accent dots | The two dieresis contours, independently preserved |

A rectangle supplies new straight strokes. Italic extraction takes place in an
upright coordinate frame and the result is slanted back. This is a geometric
coordinate change, not a claim that Italic is slanted Roman: each style supplies
its own palette.

The examples are:

```text
H  = capital_left + crossbar + capital_right
n  = lowercase_left + shoulder + lowercase_right
m  = lowercase_left + shoulder + middle_leg + shoulder + lowercase_right
ö  = lowercase_bowl + placed(dot_left, dot_right)
Π  = placed(capital_left, capital_right) + top_bar
Н  = H's construction
П  = Π's construction
ɸ  = lowercase_bowl + descending_rectangle
```

Placement and horizontal fitting are explicit transforms in the JSON. The m
recipe measures the target's stem centres; Π measures its stem centres; ɸ
measures its vertical extent. Accent placement comes from the existing
components, and advances are copied. Thus the trials test **reuse of ink**, not
automatic character design, inferred spacing or a complete anchor grammar.

H and n are partition/reassembly controls. O and o retain their whole drawings.
The five difficult examples a, g, S, α and б remain explicitly labelled
`unresolved`: their whole outlines are stored as fallbacks. Their zero error is
not counted as structural success. No new decomposition of those forms is claimed.

## Results

Ink difference is `area(original XOR candidate) / area(original UNION candidate)`.
It is a geometric diagnostic, not a perceptual quality score or acceptance limit.

| Reuse trial | Regular | Italic | Bold | Bold Italic |
|---|---:|---:|---:|---:|
| m from n parts | 5.314% | 16.612% | 4.126% | 15.098% |
| ö from o and accent dots | 0.000% | 0.000% | 0.000% | 0.000% |
| Π from H stems and a top bar | 0.000% | 1.855% | 0.521% | 1.244% |
| Н from H parts | 0.000% | 0.000% | 0.000% | 0.000% |
| П from the Π recipe | 0.000% | 1.855% | 0.521% | 1.244% |
| ɸ from o and a plain stem | 3.814% | 14.429% | 6.976% | 19.680% |

Regular Π/П are particularly useful evidence: the shared cap stems and measured
bar reproduce the existing ink within displayed precision. Cross-script Н reuse
and accent composition also work, though these are already natural component
relationships in the font.

Visual inspection of all four rendered sheets confirms the limitations:

- In Roman m the repeated n entry introduces a serif-like projection at the
  interior shoulder; fitted shoulders also differ in curvature from the original.
- In Italic m the middle leg inherits n's exit curl, and the second shoulder
  inherits its entry stroke. These create visibly incorrect interior joins.
  A distinct interior leg/arch connection is necessary.
- The plain ɸ stem omits Roman terminal serifs, and especially in Bold Italic
  the unchanged o bowl leaves the wrong counters and joins. This agrees with
  the need for the existing specialised `phi_drawing.py` construction.
- Π shares a structure across styles but its stems are not exactly H's stems
  in every style. The small residual differences should remain visible rather
  than being silently erased by target-outline patches.

## Validation and limits

- All 60 examples generated and survived JSON serialisation/replay.
- Each style's partition controls, retained bowls and explicit fallbacks stayed
  below 0.01% symmetric ink difference; the script fails otherwise.
- Standalone Italic replay produced a byte-identical SVG.
- Three focused tests passed: overlapping union area, preservation of a counter
  through JSON and reflection/scaling, and rejection of cyclic references.
- Ruff passed for the new script and tests.
- Source UFOs, generators, metrics, feature tables and acceptance records are
  unchanged. No production shaping, hinting or full font regression checks were
  needed for this separate experiment.

Stored paths include complete bowls, compound stems and arbitrary fallback
curves. Counting ten named pieces is therefore **not** a compression result.
The comparison references in the JSON are proof data, not construction inputs
during replay. No whole-font inventory, coordinate-count reduction, minimum
proof, or universal sign coverage has been established.

## Next refinement supported by this experiment

Separate entry, interior and exit connections first, using n/m as the test pair.
Then separate serif and terminal geometry from stems, and fit bowl outlines with
explicit counter and contrast constraints. Keep residual differences measurable;
do not add unrestricted corrections and call the grammar minimal.

Only after those rules work across the four styles should the experiment expand
to a/g/S and the unresolved Greek/Cyrillic forms, with the same before/after
evidence. A useful optimisation target is total stored geometry plus recipe
parameters plus exceptions, subject to preserving accepted drawings.
