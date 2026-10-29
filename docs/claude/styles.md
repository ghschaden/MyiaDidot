# Generated styles: Bold, Bold Italic, Italic

Moved from CLAUDE.md (its ground rules apply).

- The Italic, Bold and Bold Italic are generated: change them only through
  the Regular or their generators (a recipe, a constant in make_italic.py /
  make_bold.py), never by editing or scripting the generated UFO alone, or
  the next run undoes it. `make reproduce` (≈40 s) reruns the generators
  into build/reproduce/ and lists whatever would change; run it before
  committing changes to the generated styles. Hand-drawn exceptions in the
  Italic are marked "drawn" (org.myiadidot.italicSource), which a run keeps.
- **Bold** (`sources/MyiaDidot-Bold.ufo`) is generated from the Regular by
  `scripts/make_bold.py` (then `smallcaps.py` on it, `make normalize`):
  rerun it after changes to the Regular until the Bold has reviewed edits
  of its own. Tests and baselines are per style (`style_data` in
  tests/conftest.py: `shaping-golden-Bold.json` ...;
  `update_test_data.py --ufo sources/MyiaDidot-Bold.ufo`). Derived letters
  are made of the Bold's own base where the source letter is its base
  turned or mirrored, or keeps all of it (`follow_bases`): emboldened
  whole, their junctions thicken unlike the base's strokes. Letters that
  attach a scaled-down glyph (ɬ Ꞁ's ring, ⁂) take it at the weight of its
  scale (`attached_small`). Those that cut their base (hooks, Ц's tail)
  are made again by their recipe from the Bold's own glyphs (`rederive`;
  what recipes draw by number at the Bold's stems and hairlines,
  derive.STROKE_KEY), kept where the result stays close and clean; recipes
  that miss in the Bold are reviewed exceptions (BOLD_KEEP_WHOLE,
  ITALIC_BOLD_KEEP_WHOLE). A hook cut placed at the source's foot-serif
  top is raised to the Bold's taller serif (`serif_top`); a result close
  to the emboldened letter but set wider or narrower keeps that letter's
  side bearings around its new outline. Before it is judged, a rebuilt
  letter loses the specks its cut leaves apart (drop_specks) and has the
  pinholes filled where the emboldened letter has ink (fill_pinholes). The paragraphos ⸏ ⸐ ⸑ are emboldened as marks.
  Neighbouring serifs that emboldening brings into a partial join (a notch
  over a hair-thin joint: the Bold Italic's v.sc w.sc Π Ш, ʌ.sc's feet)
  are kept apart, their tips shortened in the source (part_serifs); serifs
  joined over their whole height (x.sc's inner feet, by bridge) stay joined.
  Letters are emboldened by stroke weight (`derive.embolden_by_weight`:
  thick strokes +AX across in any direction, hairlines only AY; a node's
  weight from its edge's thickness, junctions take the thick stroke's;
  corners between straight edges where the moved edges meet), so the
  contrast is a Didot bold's. Glyphs made small (superiors, numerators,
  modifier letters, ª º: `small_glyphs`) at their scale; marks plainly
  (MARK_AX). Each glyph's side space is then fitted optically to the white
  the earlier emboldening gave it (`optical_fit` against `embolden`'s
  result), so the spacing and kerning tuned on it hold; Greek/Cyrillic pairs
  still off go into BOLD_KERNING / ITALIC_BOLD_KERNING (final values: add to
  what the pair had). Where emboldening by weight leaves a slit, the
  weighted `embolden_simple` is taken if it has fewer faults. In the Bold
  only (the Bold Italic's not yet reviewed): that way keeps smooth nodes
  smooth (keep_smooth), and by weight a short edge running on into a curve
  takes the curve's weight (runs_on: ƒ's stem under its bar). In both: a
  fitted curve that bends both ways where its source bent one way has
  its handles moved toward its nodes' as far as takes that out
  (keep_bends; BOLD_FIT_AS_IS / ITALIC_BOLD_FIT_AS_IS opt a letter out).
  The closed rounds o O 0 (OVALS) are then refitted from the lighter
  style's curves to the emboldened box and ink area (`oval`).
  The slashed rounds Ø ø ø.sc (SLASHED) are their round so made plus
  their slash as one bar emboldened apart (`slashed`), spaced as the round.
- **Bold Italic** (`sources/MyiaDidot-BoldItalic.ufo`) is generated from the
  Italic by the same script: `make_bold.py sources/MyiaDidot-Italic.ufo
  sources/MyiaDidot-BoldItalic.ufo` (then `smallcaps.py` on it, `make
  normalize`); it works in the upright frame (deslanted by the italic
  angle). Rerun it after changes to the Italic. Its own tweaks:
  ITALIC_SIDEBEARINGS / ITALIC_ANCHOR_NUDGE in make_bold.py. Its letters
  are emboldened by their strokes, not by weight (`stroke_bold.py`,
  2026-10-28, the person's review): each stroke section's weight, smoothed
  along the outline between crotches, moves it out (ITALIC_AX across a
  stem, ITALIC_HAIR across a hairline, AY up and down; a shallow diagonal,
  z's spine, weighed nearer the horizontal and gaining up and down too,
  away from the zones), no side further than a quarter of the white in
  front of it (a loop's eye stays open); redrawn with the Italic's own
  segments (one cubic per curve, its extremes kept), so the curves are as
  few and round as the Italic's; two curves meeting smoothly share one
  curvature (G2, stroke_bold.G2: each within 3 units of its own fit, else
  left so; a curve into a line is not made straight there); serif brackets move whole, keeping their
  radius; a crotch between two lines is where the moved lines meet. A
  curve running smoothly into a line, split short just before it (the
  cleaning's cut at an extreme; under BLEND_SHORT, 40 units), takes on
  the line's weight towards it over BLEND (120) units where the two would
  move over BLEND_STEP (4) units apart (`Strokes.blend`, 2026-10-29,
  Codex's review: y's descender met its inner line in a sideways step,
  that line's mean weight lowered by the crotch above it; not short
  curves between two lines, no blend lines those up); in such a
  glyph the short piece is joined into its curve, and a leftover merged
  at a line's end leaves the curve along the line (`rejoined(short=)`:
  one curve into the line, as the Italic draws it). A glyph takes the
  blend only if it leaves fewer such steps (`steps`), no more bends
  (`bends`), as many contours and, slanted back and rounded, no more of
  the quality checks' findings (`findings`), else it stays exactly as
  drawn without (MYIA_BLEND=0 to compare; tests/test_stroke_steps.py). Last,
  each whole arc of the cleaned outline (corner to corner) is refitted
  fair (`fair_arcs.py`, 2026-10-28, the person's review; MYIA_FAIR=0 to
  compare): curvature continuous, changing gently (by its relative change,
  so tight inner turns stay tight), rising from nothing out of a line (the
  curve next to it split in two, only fading towards the line), no new
  bends; serif brackets (up to three curves under 120 units between
  lines) held as drawn; an arc taken only within LIMIT (6) units; the
  cleaning's leftover curves under 8 units merged first (`rejoined`).
  ITALIC_BOLD_ROOTS: letters whose hairline leaves its crotch heavier
  (k 0.7, the person's choice: its arm was a thin wedge at the stem).
  make_bold pins numpy and OpenBLAS to AVX2 (the solves the same on CI).
  Run in
  a pool of JOBS processes. Spaced as by weight (that letter's optical
  fit), so the stems stand where they did, then cut less than the Bold
  (BOLD_ITALIC_CUT: ITALIC_LOOSER, 10 units a side, looser; tests holding
  fixtures at the Bold's cut move them by conftest.respaced). ITALIC_BOLD_HEAVIER: letters
  given more gain (z). ITALIC_BOLD_BY_POINTS keeps by weight the letters
  whose later repairs match that outline's points (dollar, ℵ, ™); ø's
  slash bar too (`slashed`'s bar). The slashed letters (Ⱥ Ȼ Ⱦ ...) are
  rebuilt by their recipe on the stroked base (ITALIC_BOLD_REBUILD; Ɯ
  too, U twinned: its own stroked stem, unioned with U's, crossed it in
  a step), a
  rebuilt letter cleaned (glyph_lint.fix) before it is judged; Ⱳ is not
  joined to its W after (ITALIC_BOLD_UNJOINED). OVALS and r's shoulder
  roundings (by-weight repairs) are not applied to it.
- **Italic** (`sources/MyiaDidot-Italic.ufo`) is generated by
  `scripts/make_italic.py` from Old Standard Italic (Kryukov, OFL; source
  pinned in `sources/oldstand/`, converted once into
  `sources/oldstand/OldStandard-Italic.ufo`: `make oldstand`) plus the
  Regular: Old Standard's letters zone-scaled to Myia's metrics, Myia's
  marks and features sloped 15.2°, composites rebuilt; the letters' thick
  strokes made heavier (WEIGHT, CAP_WEIGHT: `weight_thick`) as they are
  taken, so all made of them is built from the weighted letter, never
  weighted whole (only a letter enlarged to the other case, made of the
  unweighted glyphs, gets its case's weight after: `enlarged`). Its W
  (uncrossed, of two narrowed Vs: `redraw_w`) and a (the bowl lighter:
  `lighten_a`) are redrawn from Old Standard's before anything is made of
  them. What Old Standard
  lacks is made in an upright frame (derive.py recipes, their drawn strokes
  at the weighted stems (`recipe_scale`), transplants from
  the Regular (the part at the Italic's stems,
  measured on n and H), FontForge small caps (raw drafts stored in
  `sources/drafts/Italic-smallcaps.ufo` with a hash of their inputs:
  only a changed capital is drafted again, `--redraft` drafts all; without
  FontForge, as in CI, a stale draft stops the run: `fontforge_inputs.py`),
  fitted old-style figures); the
  extra ligatures (fb ft ſt ct ...) are rebuilt from the final italic bases
  by italic_ligatures.py in the shared style writer. The same recipes run
  on Bold Italic's final bases; keep draft_ligatures.py for the Romans.
  The Italic generator runs smallcaps.py itself. It saves with smooth
  rounding (`round_smoothly`) but for ROUND_PLAIN, glyphs whose repairs
  match exact points or whose Bold Italic smoothing harms; check a new
  rounding change in both italic weights. Slanted letters (derived, sloped
  roman, the upright mathematical ones) are split at the extremes the
  slant moves (`shear(..., extremes=True)`, derive.with_extremes, more than
  EXTREME_PAST units past their points); the Bold Italic splits them again
  when it slants back (make_bold.slant_back, also its rederived letters);
  POINT_REPAIRS (ℵ ɬ Ɬ) keep
  their points for their repairs. Lib
  `org.myiadidot.italicSource` says where each glyph came from; a rerun
  keeps "drawn" glyphs (set it after hand-editing one) and reviewed drafts
  (draft key cleared). Then `make normalize`. Review sheets:
  `drafts-review-Italic.pdf`, `smallcaps-review-Italic.pdf` (and
  `-BoldItalic`), listing the drafts not yet accepted. A style's own
  fontbakery allowances: `tests/data/fontbakery-allow-Italic.txt`.
