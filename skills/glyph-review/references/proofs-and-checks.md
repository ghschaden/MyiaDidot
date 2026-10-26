# Proofs and checks

Paths below are relative to the repository root. Run Python with
`.venv/bin/python -I`. Use a topic-specific directory under `build/glyph-review/`.

## Before and after sources

Use the requested revision, not the global visual-approval tag, for a local
before/after proof. For example, extract a committed Italic without changing the
working UFOs:

```sh
mkdir -p build/glyph-review/r-family/before
git archive HEAD sources/MyiaDidot-Italic.ufo | \
  tar -x -C build/glyph-review/r-family/before
.venv/bin/python -I skills/glyph-review/scripts/proof.py \
  --ufo sources/MyiaDidot-Italic.ufo \
  --before build/glyph-review/r-family/before/sources/MyiaDidot-Italic.ufo \
  --glyphs r uni027D n o --text 'rara aɽa' --language en \
  --out build/glyph-review/r-family/before-after.svg
```

Check both commands' exit status. A Git reference excludes uncommitted changes;
if those are the intended before state, copy the relevant UFO before editing.
Use separate proofs per style. A glyph absent from the baseline is labeled
missing, not silently shown using the current drawing.

The renderer normalizes em size across different UPMs, shows baseline/x-height/
cap-height guides, advances and bounds, and repeats each glyph at a smaller size.
`--anchors` overlays named anchor positions. Repeat `--text` for additional word
samples. For example, a discretionary ligature proof can use:

```sh
.venv/bin/python -I skills/glyph-review/scripts/proof.py \
  --ufo sources/MyiaDidot-Italic.ufo --glyphs c t c_t s_t \
  --text 'action lasting' --language en --features '{"dlig":true}' \
  --out build/glyph-review/ct-st/dlig-on.svg
```

Make a matching off proof with `--features '{"liga":false,"dlig":false}'`.
Text rows use the shared compiled-font cache and English unless a language is
specified. Direct glyph rows show source outlines, including unencoded glyphs.
They do not demonstrate language/feature selection or pixel hinting on their own.

If `rsvg-convert` is installed, convert the SVG for inspection or sharing:

```sh
rsvg-convert -f png build/glyph-review/r-family/before-after.svg \
  -o build/glyph-review/r-family/before-after.png
```

## Select checks by the concern

| Concern | Starting point |
| --- | --- |
| Outline defects in specific glyphs | `.venv/bin/python -I scripts/glyph_lint.py UFO GLYPH ...` (omit `--fix` for review) |
| Weight relative to the glyph's kind | `.venv/bin/python -I scripts/quality/strokes.py UFO GLYPH ... --sheet build/glyph-review/TOPIC/strokes.pdf` |
| Derived base, composites, anchors, small caps | `docs/claude/glyphs.md`; relevant tests in `tests/test_built_from.py`, `tests/test_composites.py`, `tests/test_styles_agree.py` |
| NFC/NFD discrepancy | `.venv/bin/python -I scripts/nfd_debug.py UFO CHARS` |
| Ligature/language/lookup behavior | `scripts/font_shaping.py` (`language=` and `script=` are keyword arguments); `tests/test_italic_ligatures.py`, `tests/test_lookups.py` |
| Hinting | `docs/claude/hinting.md`, `tests/test_hinting.py`; build the affected OTF/TTF first |
| Broader rendered side effects | `make visual VISUAL_REF=REV` → `build/visual/report/index.html` |
| Broader shaping/table/word side effects | `make regress REF=REV` (Regular); `make diffenator VISUAL_REF=REV` (all styles); exact style report from the baseline updater when updating baselines is authorized |
| Generated styles remain reproducible | `make reproduce` |

Use pytest node IDs or `-k` to select relevant styles/tests during iteration.
The standard `make test`/CI gates retain broad coverage. A missing reference,
skipped test or absent corpus case is a limit, not a pass. In environments where
CFF hinting fails because its helper cannot open a local socket, use the normal
environment permission flow; do not accept an incomplete font or bypass the check.

Check build freshness before using existing files under `fonts/`. Rebuild the
affected target, e.g. `make fonts/otf/MyiaDidot-Italic.otf`, rather than assuming
a previous proof or automatic background build reflects the current sources.
