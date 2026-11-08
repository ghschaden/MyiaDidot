# Italic ligatures, 2026-10-25

The review requested the missing Italic ligatures after the earlier work
was committed and pushed as `c5ea04cf`. The new drawings are installed in
the local Italic and Bold Italic masters and rebuilt fonts. The review accepted all these drawings and requested commit/push on
2026-10-25. Draft metadata is cleared in the generator and both masters.

[Four-page review proof](../proofs/italic-ligatures-review-2026-10-25.pdf)
shows all 19 additions beside separate letters, repeated at text size,
and in HarfBuzz-shaped English/historical text with ligatures off/on.
A German sample demonstrates the retained f-ligature exclusion. Final
rendered pages were inspected for shapes, spacing and page layout.
Reproduce with `.venv/bin/python -I scripts/italic_ligature_review.py`.

The additions in each weight are:

- fb, fh, fk, ft, ffb, ffh, ffk and fft;
- ſb, ſh, ſk, ſt, ſi, ſl, ſſ, ſſi and ſſl;
- ct and st.

`scripts/italic_ligatures.py` builds from final same-style bases in the
upright frame and returns the results to the existing 15.2° slant.
The f forms keep fl/ffl's joined heads and replace the lower l with the
matching b/h/k/t. The ft crossbar is joined across its full height.
Long-s forms use the same-style ſ stem beneath the joined heads. The ct/st
arches grow out of c/s into t, using t's stem and crossbar thickness to
set their contrast. Local tangent, extremum and tiny-step finishing keeps
all 38 new outlines construction- and glyph-lint clean.

The shared style writer calls this after final drawing repairs, so Bold
Italic rebuilds from its final weighted bases rather than emboldening the
combined ligatures. Advances follow the final letter placements. Caret
anchors follow the existing joined forms, with two carets for three-letter
ligatures. Categories, glyph order and b/k right-side kerning groups are
included. The former `drop_ligatures` stage is removed.

Existing Regular feature rules are retained through generation: ordinary
f and long-s combinations use liga; ct/st use dlig. Turkish keeps dotted-i
exclusions; German keeps long-s ligatures while excluding ordinary f
combinations by default. Existing fi/fl/ff/ffi/ffl and fj/ffj stay unchanged.
The three restored lookup-summary lines per italic weight represent two
long-s lookups and the ct/st lookup. The now-obsolete German missing-liga
allowance is removed from the language-default test.

Verification:

- Against `c5ea04cf`, each weight adds exactly the 19 named glyphs. Every
  existing glyph's decomposed outline, advance and anchors match exactly;
  existing kerning and font info also match. There are no Roman changes.
- Full-corpus comparisons cover 2,119,788 strings per italic weight.
  Exactly 16 strings change in each: fb/fh/fk/ft, the seven two-letter
  long-s combinations, the four encoded-ff-plus-letter combinations, and
  the dlig specimen. All changes select the requested ligatures. The two
  corresponding golden snapshots and digests are updated deliberately.
- Tests verify generation/idempotence, no unrelated glyph changes,
  propagation from an edited b, positive widths, caret counts, clean
  construction/lint and feature/language selection. Both italic weights
  pass. Style agreement, quality and glyph lint pass; 19 missing-glyph
  exceptions disappear per weight, with no new quality/lint exceptions.
- All eight lookup/language tests and all six italic shaping regression
  tests pass. The initial focused run caught the expected obsolete Bold
  Italic lookup snapshot before its reviewed update; the final lookup
  rerun passes all four styles.
- All four italic TrueType/CFF hint-zone checks pass without changing any
  hint exceptions. CFF checks/builds used helper-socket access after the
  sandboxed hinter failed.
- Italic, Bold and Bold Italic reproduce exactly from their generators.
  All six affected OTF/TTF/WOFF2 files rebuild successfully.
- Ruff, whitespace and source-sync checks pass.

Scratch logs, exact side-effect comparisons, old source archives, review
OTFs and rendered pages are in `build/italic-ligatures/`. The results above cover targeted validation before acceptance. The commit
hook additionally runs the complete suite and generation checks.
