# Italic remaining Latin and phonetic small caps

Reference: `f471c107`. Current-design review; no production sources changed.
The person approved all 15 forms unchanged on 2026-11-06. Acceptance
fingerprints are recorded in the Italic UFO. The accepted sheet is retained
as `proofs/italic-smallcaps-phonetic-2026-11-06.pdf`.

The next batch contains 15 unaccepted small caps reached from Latin or
phonetic inputs. omega.sc is shared with Greek; it is included because the
Latin omega maps to it. Greek-only and Cyrillic forms remain outside this
batch. Exact glyph names, fingerprints, lint findings and shaping records
are under `build/glyph-review/italic-smallcaps-phonetic/` in `glyphs.txt`
and `checks.json`; `prepare.py` repeats the preparation.

Proof: `build/glyph-review/italic-smallcaps-phonetic/review.pdf`, one page,
rendered to `review.png` and visually inspected. Each cell shows the
capital, small cap and lowercase at the same em scale, with height guides,
followed by n/small-cap/n and H/small-cap/H text contexts. A dash denotes
the absent capital for ɤ. Its small-cap form retains the lowercase design.
The strokes, bowls and attachments appear connected in these specimens;
the hooked and barred forms merit the person's close inspection. No
redrawing is proposed from this initial inspection.

All 51 explicit smcp/c2sc mappings pass using a font compiled from the
complete current Italic source (`script=latn`, `language=en`). Outline lint
reports no findings for the selected glyphs. The selection UFO is a scratch
copy used only to select proof cells; the compiled font uses the complete
source. The proof has minor TeX overfull-box warnings; visual inspection
confirms the labels and specimens are visible and separated. These are
outline/shaping specimens, not a screen-hinting review. No full test run
was needed for proof generation alone. After approval, UFO normalization
completed; all 15 fingerprints match the reviewed records and all Italic
acceptance records remain valid. No outlines or spacing changed.
