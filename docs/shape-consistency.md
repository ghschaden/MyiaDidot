# Shared shapes: production preparation

The objective is **consistent, maintainable construction with deliberate optical
variants**, not the fewest possible shapes. The typographic vocabulary provides
names for parts; production policy decides which instances should agree.

`scripts/shape_consistency.py` now provides a read-only audit and an isolated
preview workflow. **It has no apply or install command and does not modify font
sources.** Its candidates are complete scratch font snapshots under `build/`.

## What is implemented

- A declarative [comparison policy](../scripts/data/shape-consistency.json) with
  25 contexts covering all 180 anatomical samples from the vocabulary study.
- Explicit same-style donors, rather than selecting a new statistical prototype
  every time the font changes.
- Separate capital/lowercase/small-cap/figure bowls, thick/thin diagonals,
  entry/interior/exit connections, head/foot serifs, and letter/punctuation dots.
- Measurements and review findings for connected parts, without cutting new
  pieces into their outlines.
- A bounded, repeatable handler for a shared **isolated contour profile**.
- Source-, policy-, implementation- and toolchain-pinned preview plans.
- Whole-font metadata and dependency checks, outline lint, compiled shaping
  comparisons, before/after proofs and byte-level source preservation checks.

The initial editable case is deliberately small: fit the final same-style
`dotaccent` contour profile into each `dieresis` dot's existing bounding box.
This tests the rule pipeline. It is **not an accepted drawing change or a claim
that the new dots look better**. Different optical sizes retain their own
dimensions, and punctuation/letter-dot comparison groups remain separate.

## Run and review

```sh
.venv/bin/python -I scripts/shape_consistency.py audit
.venv/bin/python -I scripts/shape_consistency.py preview \
  --plan build/glyph-review/shape-consistency/plan.json
.venv/bin/python -I -m pytest tests/test_shape_consistency.py
```

[Open the audit and candidate proofs](../build/glyph-review/shape-consistency/index.html).

The output includes:

- `audit.json`: all comparison groups, donors, dimensions and shape differences.
- `plan.json`: the exact source, policy and implementation identities and the
  supported preview recipes. A stale or modified plan fails before generation.
- `preview.json`: actual changes, dependent glyphs, validation results, source
  hashes and the paths of the corresponding candidate artifacts.
- `runs/<plan-id>-<run-id>/`: before/candidate UFOs, enlarged mark overlays,
  and source-outline proofs with anchors, text-size repeats and shaped text.

Every preview gets a fresh run directory. Failed attempts cannot overwrite
the candidates linked from a previous successful report. The index publishes
new proof links only after the whole preview succeeds. Output paths must resolve
inside this repository's `build/`; source paths and symlink escapes are rejected.

After changing source files, policy, relevant scripts or compiler dependencies,
run `audit` again. This intentionally prevents an old plan being silently applied
to a new design. Preview generation still does not approve or install anything.

## Rules preserve context

The policy assigns every sampled part to exactly one comparison group. These
groups are allowed to multiply as design distinctions become clear. There is
no cost or penalty for adding an intentional optical variant.

For example:

| Context | Reference | Treatment |
|---|---|---|
| Capital stem interiors | H's left stem | Compare normalised shape; preserve each width |
| Lowercase entry stems | n's entry stem | Keep separate from interior and exit stems |
| Entry shoulders | n's shoulder | Compare h; m's first/last shoulders stay independent |
| Capital foot serifs | H's foot | Keep head serifs and arm-connected feet separate |
| Capital, lowercase, figure and small-cap bowls | Their own drawings | No forced scaling or symmetry |
| Letter dots | i's dot | Check j; existing components already share their base |
| Punctuation dots | period | Check colon; do not borrow an italic letter dot |
| Round accent dots | dotaccent | Experimental dieresis profile preview only |

An audit finding means “inspect this difference,” not “normalise this glyph.”
The 0.25% audit threshold is a diagnostic threshold, not a design acceptance
criterion. Dimensions are reported separately from normalised shape, since a
correct common profile can legitimately occur at different sizes and weights.

## Candidate construction contract

`contour_profile()` is a pure in-memory operation: it returns a replacement
contour without writing any font. It fits a same-style donor to the target's
native-coordinate bounding box and retains the target's point/contour metadata.
The preview handler requires matching point topology and winding, closed
contours, and spatial separation from every other target contour.

It refuses components, counters, touching/overlapping parts and changed contour
inventories. In particular, it cannot replace a clipped shoulder or serif. That
would require an attachment-aware recipe, not a larger crop.

The configured experiment allows at most 2% ink difference per part and glyph,
and 0.01 font-unit bounding-box drift. These are guard limits for this preview,
not universal font quality thresholds. It also verifies that the candidate
converges to its declared profile and that a second application changes nothing.

For every candidate, the tool checks:

1. Only the named direct glyph outlines changed.
2. Glyph widths, anchors, components, Unicode mappings, point metadata, feature
   code, kerning, groups and other serialised font metadata remain unchanged.
3. Changed decomposed outlines match exactly the direct changes plus their
   transitive component dependants.
4. Recorded `builtFrom` dependencies and existing acceptance records affected
   by the change are reported; neither is updated or cleared.
5. Saving and reopening the candidate preserves its content.
6. No new `glyph_lint` findings are introduced in the affected glyphs.
7. Compiled glyph sequences, advances and offsets agree on the selected shaping
   corpus, including affected encoded forms and their NFD forms.
8. The production source UFOs remain byte-identical before and after the command.

## First preview results — 2026-10-27

| Style | Dieresis ink change | Direct changes | Component dependants | Shaping comparisons |
|---|---:|---:|---:|---:|
| Regular | 1.008% | 1 | 15 | 34 |
| Italic | 0.867% | 1 | 15 | 34 |
| Bold | 0.886% | 1 | 15 | 34 |
| Bold Italic | 0.848% | 1 | 15 | 34 |

All 136 shaping comparisons preserve glyph sequences, advances and offsets.
Cases include Latin umlauts, decomposed accents, Greek dialytika, Cyrillic ё,
Turkish and small-cap text, with explicit scripts/languages. This checks layout
behaviour, not equivalence of the intentionally changed ink.

The candidate profile residual is at most approximately 0.00013% after fitting.
The largest measured dot bounding-box drift is approximately 0.000061 font
units, within the numerical precision of the path operations. No new outline
lint findings occur; baseline and candidate findings are empty for the affected
glyphs. No recorded flattened dependency or accepted glyph is affected in this
particular example. Unrecorded generator dependencies are not inferred from
that absence.

The direct change in each style is `dieresis`; its 15 component dependants are
listed by name in `preview.json`. Other glyphs, including i/j and punctuation,
remain unchanged. The enlarged overlays show a subtle profile adjustment;
normal text is visually very similar. The proof is useful evidence for judging
whether sharing the rule is worth doing, not a demonstration of a necessary fix.

Nine focused tests pass, covering bounded/idempotent fitting, metadata,
dependencies, stale plans, ambiguous groups, topology, counters/components,
and output-path protection. Ruff passes for the tool and tests. Source hashes
match for all four production UFOs. No font source, acceptance record or
production baseline was edited.

## What remains before production use

This is a tested **review path**, not an enabled production normaliser. The
candidate snapshots have not been generated through the full style pipeline,
and they are explicitly marked not release-ready.

1. **Choose the intended design.** Review the candidate in enlarged and normal
   text, retaining the existing drawing if the proposed uniformity is not useful.
   Record intentional exceptions with a reason and context rather than hiding
   them behind a global tolerance.
2. **Make the rule authoritative at the right stage.** For an accepted rule,
   maintain one design definition and use the final same-style donor after its
   weight and slant decisions. Integrate before downstream composites/derived
   forms are built. Route Regular through its source/design input and the other
   styles through `make_italic.py` / `make_bold.py`; never copy these scratch
   candidates over generated UFOs.
3. **Review all generation dependencies.** Component closure is checked now;
   flattened variants, case forms, small caps and dependencies encoded only in
   generator code need a separate integration audit. The `builtFrom` graph is
   useful but not a complete description of that code.
4. **Use the existing finishing pipeline.** Integer rounding, extrema,
   smoothness, source normalisation and hinting must be checked in the final
   generators. Current previews retain fitted fractional coordinates and use
   unhinted compilation for layout checks.
5. **Validate a whole regenerated family.** Run reproduction, affected composite
   and derived-glyph checks, broad visual/shaping comparisons and the normal
   release gates. Accept drawing/baseline changes only after their review.

For connected shapes, the next implementation should define attachment ports:
position, tangent, local thickness and permitted blending region. Entry,
interior and exit variants should be explicit. It should preserve outside ink
and counter clearance and report every dependent construction. This work is
more useful for production than continuing to reduce the vocabulary count.

The [attachment audit](shape-ports.md) now measures original-curve crossings,
ink intervals and edge tangents for all 132 connected study regions across the
four styles. It records ambiguous crop contacts explicitly and compares cut
constraints with each declared donor. This supplies the measurement layer;
connected-part fitting and replacement remain disabled.

A separate [seam-fitting experiment](shape-seams.md) now constructs n-to-h
shoulders and H-to-I feet with explicit attachment constraints in all four
styles. It produces isolated scratch candidates; the original consistency
policy and production generators remain unchanged.
