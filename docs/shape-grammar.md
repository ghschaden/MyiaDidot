# Complete shape grammar for Myia Didot

The executable grammar covers **every current glyph in Regular, Italic, Bold
and Bold Italic**: 2,185 per style, 8,740 glyph/style combinations. It reconstructs
the existing designs exactly without a whole-outline fallback. Production UFOs
are unchanged.

The follow-up [typographic vocabulary study](typographic-vocabulary.md) tests
an interpretable six-family layer above this geometric description, including
an exhaustive search of 4,140 mergers of eight anatomical roles.

This is a **geometric construction grammar**, with an extracted library of
shared contour fragments. It is not a claim that all letters are combinations
of a few identical stems, bowls and serifs. The small vocabulary is parameterised;
the optical design remains in those parameters. The earlier
[typographic-parts experiment](shape-grammar-review-2026-10-26.md) records why
unqualified reuse of n's shoulder or o's bowl fails.

## Use it

```sh
# Extract from all four current UFOs, factor shared parts, validate everything,
# export reconstructed UFOs and create the searchable catalogue.
.venv/bin/python -I scripts/shape_grammar_full.py

# Reconstruct and validate using ONLY the saved grammar, without source UFOs.
.venv/bin/python -I scripts/shape_grammar_full.py replay \
  build/glyph-review/shape-grammar/complete/grammar.json \
  --out build/glyph-review/shape-grammar/replayed

# Focused tests for both the initial experiment and complete grammar.
.venv/bin/python -I -m pytest tests/test_shape_grammar.py tests/test_shape_grammar_full.py
```

[Open the complete catalogue](../build/glyph-review/shape-grammar/complete/index.html).
Each style page contains all glyphs, searchable by name, character or Unicode
code point. Expand a construction recipe or select a fragment to inspect its
boundary and parameters. The pages are standalone HTML: no server, network or
installed font is required.

- [Same-scale four-style specimen](../build/glyph-review/shape-grammar/complete/specimen.svg)
- [Shared fragment atlas](../build/glyph-review/shape-grammar/complete/fragments.svg)
- [Executable grammar JSON](../build/glyph-review/shape-grammar/complete/grammar.json)
- [Full validation report](../build/glyph-review/shape-grammar/complete/validation.json)
- [Reuse statistics](../build/glyph-review/shape-grammar/complete/statistics.json)

Generated artifacts and reconstructed UFOs live under `build/`; they are
reproducible outputs, not replacements for the master sources. Replay checks
the font-content fingerprints recorded during extraction. Build additionally
compares the complete decoded objects with the actual source objects.

## The grammar

Two primitive families suffice for the existing outlines:

```text
L(dx, dy)
C(dx1, dy1, dx2, dy2, dx3, dy3)
```

`L` draws a straight segment from the current point. `C` draws a cubic Bézier
segment: two control points and an endpoint. All coordinate pairs are offsets
from the segment's starting point. The cursor advances to the endpoint.

They describe **ink boundaries**, not centreline strokes. Stroke contrast,
serifs, counters, terminals and joins emerge from the boundaries. This avoids
assuming that a Didot bowl is a stroked ellipse or that a shared centreline can
preserve both its inner and outer curves.

The complete construction hierarchy is:

```text
primitive   := L(parameters) | C(parameters)
fragment    := primitive | join(fragment, fragment)
contour     := start(x, y), fragment*, close | end
component   := glyph_reference, affine_transform, metadata
glyph       := contour*, component*, metrics_and_metadata
style       := glyph_dictionary, font_metadata
family      := shared_fragment_dictionary, style_dictionary
```

`join` concatenates directed boundary segments at the current cursor. It is
**not Boolean union**: the original contours, winding, overlaps and counters
survive intact. `close` preserves a closed contour and its implicit closing
edge. `end` preserves an open contour, including the existing move-only Regular
`uni0434` contour. An empty glyph has no contours or components but retains its
advance and other metadata.

Components use UFO's full six-number affine transform: translation, scaling,
reflection and shear are supported. They may reference other composites, and
the decoder validates the resulting dependency graph. Missing references and
cycles fail explicitly.

For example, the complete recipe for ö follows the source's o and dieresis
component references. Their contours resolve into fragment productions, which
resolve into L/C primitives. The same resolution works for ligatures, small
caps, Greek, Cyrillic, combining marks, mathematical signs and unencoded forms.
The formerly unresolved a/g/S/α/б have complete boundary recipes too.

### Exactness and metadata

Relative coordinates are calculated with decimal arithmetic and stored as
decimal strings. They are converted to UFO numeric values only after summing
the offsets. This avoids accumulating binary floating-point subtraction errors.
The full inventory is checked for exact coordinate equality, not merely a small
ink-area tolerance.

Point smoothness, names and identifiers, contour identifiers, anchors, widths,
Unicode mappings, components, glyph libraries, groups, kerning, feature code,
font info and the other serialised UFO data are preserved. Point metadata carries
no backup coordinates. Font metadata contains empty glyph dictionaries; the
decoder must populate those through the grammar. There is no `path`, original
outline, target patch or unresolved-glyph operation.

Numeric fingerprints treat `12` and `12.0` as the same value. They do not round
fractional coordinates or permit a geometric tolerance. Saving and reopening
each reconstructed UFO is also verified against the recorded fingerprint.

## Shared rules and minimality

Identical relative segments share parameter sets, regardless of their absolute
position or source glyph/style. Deterministic greedy factoring then replaces
frequent, non-overlapping adjacent pairs by shared `join` productions. Repeating
this builds longer fragments, including serif edges, stem-and-foot boundaries,
curved returns and closed dot boundaries visible in the atlas.

The default has no arbitrary fragment limit. Factoring stops when no pair occurs
at least four times: under the stated symbol-count model, four replacements save
more references than the new rule's name and two children cost. Ties are resolved
lexicographically. `--max-fragments` is available for controlled experiments.

This establishes a local stopping condition for this particular factoring
method, **not a globally minimal grammar**. A straight line could itself be
expressed as a degenerate cubic; the two-family vocabulary retains the source's
native segment structure without extra control points. Neither vocabulary size
nor fragment count alone measures total design complexity.

## Verified results — 2026-10-27

Source revision: `e30747e339a18415e6a7c70fcb47ec7f13b55774`; source UFOs were clean.
The generated JSON records content fingerprints for the precise working inputs,
so a revision label alone is not the verification basis.

| Style | Glyphs | Direct contours | Component instances | Contour points | Round trip |
|---|---:|---:|---:|---:|---|
| Regular | 2,185 | 1,417 | 2,380 | 37,472 | Exact |
| Italic | 2,185 | 1,410 | 2,387 | 46,765 | Exact |
| Bold | 2,185 | 1,427 | 2,382 | 38,577 | Exact |
| Bold Italic | 2,185 | 1,435 | 2,387 | 50,564 | Exact |

The four styles contain 81,748 explicitly drawn line/cubic segment occurrences.
They share 44,225 distinct primitive parameter sets and 1,647 factored fragment
rules. Final contour recipes contain 69,111 rule references; the fragment
definitions add 3,294 child references. There are 4,977 distinct relative contour
recipes among 5,689 contour instances. Composite reuse is additional to these
direct-contour statistics.

The raw relative segments require 340,576 coordinate parameters; the shared
primitive dictionary stores 217,882. These figures exclude contour origins,
transforms, rule identifiers and metadata. They therefore show coordinate reuse,
not a 36% reduction in total font file size. The JSON is designed for inspection
and exact interchange rather than compact binary storage.

Validation performed:

- Exact full-object reconstruction of all 8,740 glyph/style combinations and
  all serialised font data, after the JSON encode/decode boundary.
- All four reconstructed UFOs saved and reopened with matching fingerprints.
- Separate CLI replay using only the grammar; the decoder accepts no source path.
- Thirteen focused tests passed, including decimal coordinates, counters and
  reflections in the initial engine, shared fragments, smooth flags and IDs,
  transformed components, empty and move-only glyphs, missing references, cycles,
  unsupported primitives, non-finite parameters and deliberately corrupted ink.
- Ruff passed for both scripts and their tests.
- All four catalogue pages contain 2,185 glyph cards; every fragment button
  resolves to a rule, local overview links resolve, and embedded JavaScript
  passes Node's syntax check. Browser interactions were not automated.
- The same-scale reconstructed specimen and shared-fragment atlas were rendered
  and visually inspected. The per-glyph catalogue covers the full inventory;
  individual visual acceptance of 8,740 drawings is not claimed or needed to
  establish an exact reconstruction.

No production font generation, shaping baseline, exception list or acceptance
record was changed. The reconstructed sources are identical in content, so this
work does not introduce new drawing decisions or require their visual acceptance.

## What this gives us

The grammar is a complete, source-independent description of the current family
and a concrete basis for further design-level abstraction. A named `bowl`,
`serif` or `interior-shoulder` family can be introduced above it and checked
against exact boundary recipes. Such a family should replace existing parameters
only when its constraints genuinely reduce the description while preserving the
accepted forms. Completeness no longer depends on postponing difficult glyphs.
