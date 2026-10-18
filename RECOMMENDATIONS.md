# Recommendations for Myia Didot

Myia Didot already has a strong engineering base: coverage and shaping tests,
composite and normalization checks, outline lint, design heuristics, and
FontBakery. The recommendations below focus on testing the built fonts,
making quality checks reproducible, and keeping visual review in the loop.

## Priorities

### 1. Build and validate every style in CI

The current workflow tests the UFOs but explicitly builds only the Regular
font artifact. Build OTFs for Regular, Italic, Bold, and Bold Italic in CI,
then run release checks against those artifacts. If hinted TTF and WOFF2 are
intended deliverables, build and check those formats too. Keep the required CI
job focused on core checks; publish larger proof and comparison reports as
artifacts.

### 2. Add rendered proofs and regression comparisons

Shaping tests show which glyphs HarfBuzz selects and where it places them, but
they do not show whether a paragraph looks good. Render fixed specimens for
each style, script, and size. Include small caps, italics, bold, ligatures,
figures, accents, punctuation, and text in several supported languages.

Compare rendered images with the last approved build and publish overlays or
difference images for review. Treat pixel differences as evidence to inspect,
not automatic failures: rendering can vary by platform, and intentional design
changes will also produce differences. The project already depends on
[`diffenator2`](https://github.com/googlefonts/diffenator2), which can compare
fonts visually and accepts custom wordlists. It is a useful starting point.

### 3. Broaden language and OpenType feature coverage

Maintain a curated corpus of real words and passages for target languages.
Cover supported OpenType features both individually and in common
combinations. Include the relevant script, language, and direction settings
in shaping cases. Word-based visual comparisons do not cover every abbreviation
or optional feature, so retain explicit feature tests as well.

### 4. Track spacing and kerning changes as diagnostics

The project already produces pair and spacing reports. Consider tracking
sidebearing distributions, selected kerning pairs, and measures such as text
length and average word width on the specimen corpus. These can flag large
shifts and regressions across styles. Keep thresholds broad and the results
reviewable: metrics can identify changes, but cannot decide whether a Didot
paragraph has good rhythm.

### 5. Make quality reports reproducible

`scripts/quality/fetch_refs.py` downloads reference fonts from a moving `main`
branch and caches them locally. Pin the reference files to specific revisions,
record their hashes and licenses, and have CI use those fixed inputs. This
prevents reference updates from changing quality reports independently of
changes to Myia Didot.

### 6. Add basic tooling checks

Add a Python formatter and linter to CI; consider type checking where it
provides clear value. Add a smoke check that builds and opens every output
format. Also make QA command failures visible: the current `make qa` recipe
uses `|| true`, so a failed FontBakery invocation can still leave the target
successful.

## What automation can check well

- **Source and build integrity:** UFO normalization, valid components and
  metadata, successful exports, output tables, and naming.
- **Coverage and shaping:** missing-codepoint ratchets, feature-specific
  shaping cases, NFC/NFD equivalence, and glyph or positioning changes against
  approved baselines.
- **Outline and metric diagnostics:** bounds, zero-width marks, anchors,
  alignment zones, stem consistency, spacing outliers, and suspicious kerning
  pairs.
- **Rendered regression evidence:** fixed specimens, image comparisons, and
  visual reports attached to CI.
- **Packaging checks:** FontBakery's universal profile checks broadly shared
  font best practices and complements the project's known-exception
  allowlists. See the
  [FontBakery universal profile](https://fontbakery.readthedocs.io/en/stable/fontbakery/profiles/universal.html).

## What still needs human review

Automation can find changed outlines, unusual metrics, broken shaping, and
technical faults. It cannot reliably decide whether contrast, spacing, joins,
small caps, or page texture look right. Use rendered proofs as review material
and keep a record of the approved specimen build. FontBakery's checks are
best-practice checks; they complement visual review rather than replace it.
See the [FontBakery documentation](https://fontbakery.readthedocs.io/en/latest/user/USAGE.html).

## Phase 3 progress and next steps

The first tooling milestone is now in place: CI builds all four OTF styles,
audits the expected OpenType feature tables, creates SVG specimen sheets, and
publishes per-style spacing and kerning comparisons. The comparison fonts are
SHA-256 pinned, and `make qa` no longer hides FontBakery command failures.

The pair-review pass corrected 13 frequent Bold Italic pairs, two Regular
pairs (`tt`, `tf`), and eight Bold pairs (`nt`, `at`, `as`, `au`, `kt`, `zt`,
`fs`, `Sm`). All four styles now have zero frequent pairs outside the
comparison tolerance. The intended advance changes are recorded in the
Regular, Bold, and Bold Italic shaping goldens and digests.
