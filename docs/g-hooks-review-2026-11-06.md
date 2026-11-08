# Bold Italic Ɠ, ɠ and ɠ.sc

Reference: `3d692354`. The review requested a thicker, correctly attached
Ɠ hook, a smoother ɠ downstroke, and a ɠ.sc hook resembling the uppercase
and Italic forms. The review approved all three revised drawings on
2026-11-06; their acceptance fingerprints are recorded in the UFO.

`scripts/g_hook_review.py` makes local drawings on the final same-style
bases and marks them drawn, so regeneration preserves them. No shared
emboldening machinery changes.

- Ɠ: the rising stroke is 110 units rather than 53, the top of the curl
  70 rather than 45. The stroke reaches into G's terminal and replaces
  the ledge at the old attachment. The curl's radii are 185 × 165 and its
  ball radius 95, leaving its counter open.
- ɠ: one cubic replaces the three curves between the counter and the
  descender's lower turn. Its endpoints and the rest of the glyph stay
  in place; the two changes in direction along that edge are removed.
- ɠ.sc: an upright rising curl replaces the hook beside the bowl. Its
  shoulder turns continuously out of g.sc's upper bowl into the hook.
  The rising stroke is 108 units, the top 55, radii 145 × 125 and ball
  radius 75. Its previous acceptance is withdrawn for the requested
  revision. The component alias ʛ follows this drawing.

All three advances stay unchanged. The uppercase and small-cap hooks
extend further right. The inspected English text rows include ƓaƓnƓH,
ɠaɠnɠh and, with smcp, ɠaɠnɠh / ɠHɠL / ɠɠ. No collisions were visible
in these samples; they do not establish spacing for all neighbours.

Scratch evidence is under `build/glyph-review/g-hooks/`. `before/sources/`
contains the reference UFO. The candidate-v2 source-outline proof was
visually inspected at enlarged and text sizes before installation and
whole-unit rounding. The final installed, rounded outlines were inspected
in `final.png` (before/after, enlarged, text-size repeats and compiled
HarfBuzz-shaped text). `smallcap-context.png` compares the Italic and Bold
Italic hooks and includes compiled smcp text. These are outline/shaping
proofs, not screen-hinting proofs.

To repeat the drawing from the saved reference:

```sh
.venv/bin/python -I scripts/g_hook_review.py \
  --source build/glyph-review/g-hooks/before/sources/MyiaDidot-BoldItalic.ufo \
  --out build/glyph-review/g-hooks/repeated.ufo
```

Validation:

- Final `make test`: **362 passed, 7 skipped**; one dependency deprecation
  warning. This run had normal socket/cache permissions: the sandboxed
  run could not start CFF autohinting's local socket or write LuaLaTeX's
  font cache. After inspection the two newly introduced shallow corners
  were removed, and the small cap's lower bowl retained exactly.
- Focused outline lint: no findings. Ruff and `git diff --check` pass.
- UFO normalization complete; Windows metrics remain 2248/630.
- No test baselines, shaping features, kerning or advances changed.
- `make reproduce`: Italic, Bold and Bold Italic all **as generated**.
  The sandboxed attempt could not write the shared stroke cache; the
  completed run had the required cache access.

Accepted proofs are retained as
`proofs/bold-italic-g-hooks-2026-11-06.svg` and
`proofs/bold-italic-g-hooks-context-2026-11-06.svg`. All three acceptance
fingerprints were stamped after approval; the focused acceptance suite
passes (10 tests). Work complete.
