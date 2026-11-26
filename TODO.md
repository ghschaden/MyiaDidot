# Plan to the 0.900 release and after

Written 2026-11-10 from an assessment of the four styles (rendered from
`fonts/otf` of 2026-11-09, measured with fontTools and HarfBuzz). This file
holds the order of work and the steps; the detailed design backlog stays in
[FONT-DESIGN.md](FONT-DESIGN.md), publication work in [DEVELOPMENT.md](DEVELOPMENT.md),
finished work in [FONTLOG.txt](FONTLOG.txt). Tick a step when it is done and
logged; delete a phase when all of it is in FONTLOG.

The numbers quoted are the state on 2026-11-10 and are there to be checked
against, not kept up to date.

Ground rules as in CLAUDE.md: the Regular is the master, the other styles
change through their generators, `make reproduce` before every commit,
exception lists only shrink, every visible change goes on a PDF sheet for
review before its baseline is accepted.

## Done 2026-11-20: t's bar centred in all four styles (designer: "do 2"), step D's ƭ ⱦ

- Measured: the bar's centre stood right of the stem's by 27 (Regular), 44
  (Italic), 34 (Bold), 46 (Bold Italic) units; f's bar in the italics +7;
  references -3 .. +50 per mille em. Target +6 units. Method:
  `scripts/tbar_center.py`, only the bar's ends move (stem, tail, advance
  stay: a first attempt that kept the bar-end side bearings narrowed the
  Italic's t by 33 and spoiled the pairs tf tt). Regular t and Italic t by
  point, the stored ƭ ʈ ᵵ ⱦ by band (`--skip-t --glyphs`), the Regular's
  ligatures with t by coordinates (`--ligatures`); the Bold, Italic and
  Bold Italic follow in `make generate`; Bold ƭ (drawn) by centre_band, drawn
  again. Regular shaping unchanged over the full corpus (`make regress`).
- Bold Italic ƭ ⱦ: rebuilt from their recipes (data_bold_italic.py: ƭ hook cut
  1100; ⱦ slash right end 0.80, top 960, 0.88-0.95 left a 55-unit step), the
  join node smoothed (smooth_joins ⱦ and ƭ at 294,164), ƭ's 5.9 degree kink
  mended by hand (handle turned onto the line: drawn). Advances: ƭ 740 -> 791,
  ⱦ 640 -> 663 (their recipes' own spacing).
- Sheets approved by the designer: `proofs/2026-11/t-bar-centred-2026-11-20.pdf`,
  `proofs/2026-11/bolditalic-tbar-hook-2026-11-20.pdf`; baselines accepted
  with the reviewed shaping reports (Bold 3188 strings, Italic 15, Bold
  Italic 40466, all 1-2 units but ⱦ ƭ).
- Not done: `make diffenator` and the pairs sweeps on the three generated
  styles; the Regular's `make regress` is clean.

## Next session (set 2026-11-22, first on the list)

- [x] (committed 2026-11-22, proofs/2026-11/curl-normal-batch3-2026-11-22.pdf) **Start here (handover 2026-11-22, after 875945c8).** The third
      batch, all approved by the designer on sheets in build/pending/:
      the curl ball on the outer edge's normal (curl-normal.patch, to
      scripts/derive.py), ɾ's straight stem (straight_stem.patch, to
      make_italic.py), ɬ's belt edge (l_belt_flatten.patch, to l_belt.py),
      and two lines in data_italic.py: ITALIC_JOINS_SPLIT gains "ү":
      (-130, -30) and "ʔ": (540, 720); ɱ's cuts box (1360, -BIG, BIG, 450)
      becomes (1460, -BIG, BIG, 450). All five apply cleanly to 875945c8
      (tried). NOT the other ɱ patches (hook_cuts, hook_narrow: rejected).
      Still to do before `make generate`: the curl patch reaches the
      generated Bold (Ƭ and others) and Bold Italic (Ƙ Ʋ Ƴ ƴ ʋ Ɦ ɦ.sc and
      its curled IPA descenders), which the designer has not seen. Make a
      scratch run of all three styles from a worktree with the five
      changes (make_italic --out, make_bold Regular -> Bold --out,
      make_bold scratch Italic -> Bold Italic --out; Italic 2 min, Bold 1,
      Bold Italic 10-15), list the glyphs whose outlines differ from the
      committed sources, and put those on sheets for the designer first.
      The Regular is not reached (derive.py keeps reviewed glyphs). Then
      generate, `make regress` and `make diffenator` (every curl), the
      lists, baselines, commit. Also open: ʃ's left edge and tail join;
      the rest of the Italic's recipe singles (families.py --family
      recipe).
      Scratch runs done 2026-11-22 (worktree, all three styles, `--out`):
      the Italic and Bold sheets approved by the designer (Bold: Ƭ ʂ ʐ,
      the ball of ʂ ʐ smaller). The curl patch also reached the Cyrillic
      descenders (data_italic.descender draws them with derive.curl): a
      notch where the ball runs back into its stroke (Italic Җ Қ, Bold
      Italic Җ җ Қ ң, a spike in Җ) and a sharp tip on the Bold Italic's
      ʋ. The designer: keep the old ball there. derive.curl takes
      `normal=False` (the ball on the parametric angle, as before), set
      by descender() and by the Bold Italic's ʋ Қ Җ җ қ ң recipes. Checks
      on the scratch Italic: kinks 289 -> 274, smooth 72 -> 67, steps
      25 -> 22; new: ɽ.sc ʈ.sc 2.9 degrees at y -225 (expected), ʝ.sc
      1.4, ˁ Ɦ smooth 2.3-2.5, ү slant 19.5 -> 21.1, ɾ ᵳ one step of 55
      left at the foot (were two of 67-69 and kinks). ң's 4.3-degree
      kink in the first run was from the new ball: gone with normal=False
      (ң and every Italic descender as committed; ү ұ change by ү's band).
      The Bold Italic's sheet approved but Ɠ and Ƈ (the designer: the
      hook's stroke at the very edge of the terminal, as in the Italic):
      their stroke 60 and 70 further right (data_bold_italic.py; tried
      at 55-90 and 134: less left a shelf of the terminal beside the
      stroke, more a step on its left edge), which left a 6.5-degree kink
      where the stroke meets the curl (1500): ITALIC_BOLD_JOINS Ƈ
      1440-1520, Ɠ 1470-1520 (Ɠ at 1440 cut the curl off its stroke, and
      neither checks nor lint saw it: look at every faired join).
      Still open from this batch: ɽ.sc ʈ.sc's 2.9-degree corner at -225
      (3.9 in the Bold Italic), ɾ ᵳ's step of 52-55 at the foot, ү's
      slant 21.1, ʝ.sc ˁ Ɦ ƴ.sc small corners.

- [x] (committed 2026-11-22: ɓ ƙ ɦ ɰ ɗ ɠ ƴ ʃ Ƙ; Italic 12 quality lines off,
      Bold Italic 1, ɰ's slant listed; shaping: ɗ 11 narrower (its hook's
      right end, approved), Ƙ Ƴƙ pairs -6; Bold Italic shaping unchanged.
      Generated once, ɗ grew a kink from ɓ's new top, so ɗ ɠ ƴ ʃ Ƙ were
      added and generated again, the curl patch kept for its own batch)
      Uncommitted in the working copy, for the next batch (one `make
      generate`, then commit; CLAUDE.md "The cycle"):
      ɰ in data_italic.py (ɥ's piece at 480, not 493; ITALIC_JOINS
      250-650; tried with `make only`: the kink gone, lint clean; its
      "slant 17.7" is checks.slant reading the crotch diagonals, as m n u
      ɯ already listed: list it with that reason), and scripts/stale.py +
      docs/claude/tests.md (the proof reads the source without
      acceptances; nfd-exceptions.txt in PROOF_FILES). Sonnet's ɰ report:
      build/pending/turnedm-report.md.
- [x] (in 57ce3b2a) Approved by the designer 2026-11-22 on the full-letter sheet
      (build/pending/curl-normal-full.pdf): into the next batch with ɗ ɠ.
      derive.curl's ball on the outer edge's normal
      (build/pending/curl-normal.patch, sheet build/pending/c.png): Ʈ 7.4
      and Ɽ 4.3 degree corners gone, ɖ's hidden 4.1 too, but ɽ.sc ʈ.sc
      get a 2.9 degree corner; every curl in all styles: `make regress`,
      `make diffenator` first. Or left.
      Joined in the batch (2026-11-22): ɓ ƙ ɦ, f's top on the stem, a
      2.4-2.9 degree corner at about 950: ITALIC_JOINS_SPLIT 880-1020
      (the plain fair_joins thinned the stems from the foot); tried with
      `make only`, checks and lint clean, sheet build/only/Italic-ɓ.pdf.
- [x] Next family for Sonnet (read-only, as build/pending/attach-*.md):
      the Italic's remaining `recipe` singles (families.py --style Italic
      --family recipe; ɓ ƙ ɦ ɰ done in the batch above).
      Diagnosed 2026-11-22 (build/pending/recipe-singles-report.md,
      pictures in build/pending/singles/); the batch, approved by the
      designer on build/only/Italic-uni0267.pdf: derive.fair_joins takes
      the arriving tangent at the band's entry (ɧ's kink, ɳ's smooth;
      only these two of its 20 users change); ʃ a second split band at
      the tail (-110, -80; ITALIC_JOINS_SPLIT takes several); ƴ
      ITALIC_CORNERS (628, 40); в.loclBGR a handle 3 units; ₮'s bars
      centred on the Italic's stem (400-900; the designer: "not
      centered" at the Regular's 560); ɬ Ɬ out of POINT_REPAIRS (their
      extremes split); derive.relevel for data_italic.RELEVEL (ɧ Ɯ ƹ ʊ
      ˁ ɬ: rounding of short handles). Left: Ⱦ's shelf under the slash,
      ɾ's foot slab (a symmetric slab added a step to the Bold Italic's
      ɾ ᵳ), ʃ's two 1.5-degree seam nodes, ʝ (designed).
- [ ] Open, a decision for the designer with its own run and review:
      derive.relevel over the whole Italic (Sonnet's experiment,
      build/pending/singles/relevel_all_italic.py): smooth 67 -> 1, but
      464 nodes in 241 glyphs move 1-2 units and every Bold Italic glyph
      stroked from them; taken 2026-11-22 for six letters only.
- [x] (in the 2026-11-22 commit) Next batch, the same hook family: ɗ (line node 817,980 at the cut,
      5.0 degrees) and ɠ (784,800 at the cut, 1.7) into
      ITALIC_JOINS_SPLIT, bands kept above the bowl's join to the stem
      (837-884): about 940-1020 and 770-840. Try with `make only` first.
      Tried 2026-11-22 (build/pending/d-g-hook-trial.pdf): ɠ 770-840
      clean, the letter unchanged but the join. ɗ is built from ɓ
      (make_italic.build_own, DHOOK_CUT 1000): with ɓ's split alone its
      corner grew (6.0, and 3.6 at 989,1000); ɗ 940-1040 with it clean
      (900-1060 and 950-1010 too). --only must name ɓ with ɗ, or the run
      builds ɗ from the wrong top. ɗ's hook a few units fuller.
      Approved by the designer 2026-11-22: into the next batch.
- [x] (in the 2026-11-22 commit: ƴ ʃ, Ƙ at dir 48) With them, read from the checks (2026-11-22):
      Ƙ (1243,1251, 7.8 degrees) and ƴ (948,760, 7.5) break where the
      curl starts (`at` y 1250 / 760), not at the ball, so the curl
      patch leaves them: the arm's direction in the upright frame
      against the recipe's `dir` (51, 90), or a split band about
      1200-1300 / 710-810. ʃ: four corners of 1.1-3.3 degrees on both
      edges at 900-920, f's top on the stem as in ɓ (split band about
      860-960), and 158,-100 (4.3) where ȷ's tail is put on (cut -80).
      Tried 2026-11-22 (build/pending/curl-starts-esh-trial.pdf,
      approved by the designer): ƴ split 710-810 clean; ʃ split
      860-960 mends the right edge (left 280,900 / 286,920 and the tail's
      158,-100 stay). Into the next batch. Ƙ: split 1200-1300 mends the
      arm but straightens the stem's right edge and drops its serif
      bracket (same height): not taken; mend it by the recipe's `dir`
      (51) set to the arm's angle in the upright frame instead.
      Tried: dir 42/45/48 leave no finding (54: 5.4, 57: 3.4 degrees);
      48 on build/pending/K-hook-dir48.pdf: stem untouched, the curl
      turned a little down; the shoulder where arm meets curl (top
      edge) still visible on the sheet; approved by the designer
      2026-11-22 at 48: into the next batch.
- [x] (in 57ce3b2a) Approved by the designer 2026-11-22 (build/pending/ue-glottal-trial.pdf),
      for the batch with the curl patch: ITALIC_JOINS_SPLIT ү (-130, -30)
      (kink 423,-80 gone; slant reads 21.1 not 19.5, invisible) and
      ʔ (540, 720) (kink 610,687 and smooth 521,577 gone, 19 nodes to 16).
- [x] (in 57ce3b2a) Tried 2026-11-22, to the designer (build/pending/fishhook-r-trial.pdf):
      ɾ ITALIC_JOINS_SPLIT (100, 300): kinks 272,157 (3.0) and 140,254
      (7.9) gone, 20 nodes to 19; its two steps are the foot slab's ends
      (design, to be listed so). The designer: the stem still jogs (the
      crossbar's band redrawn), make it straighter. So instead, no band:
      make_italic.straight_stem at the end of fishhook (build/pending/straight_stem.patch;
      re-made from this note if lost): each edge from
      the foot (y 50) straight up on the tangent of the first smooth node
      or curve above, the redraw's line nodes dropped; foot 68 -> 83 and
      237 -> 251, 20 nodes to 15, kinks gone, one slab-end step left.
      Sheet build/pending/fishhook-r-straight.pdf, approved by the
      designer 2026-11-22: into the batch with the curl patch.
      ɬ: a split band 720-800 changes nothing. The cause: l_belt.finish's
      union leaves the ring's arc 3 units past the l's right edge between
      bar and ring (smooth 390,760, 4.4 degrees). Tried: l_belt.flatten_stem
      (build/pending/l_belt_flatten.patch), nodes between two on the l's
      edge dropped, within attachment_band only (without it, it also
      flattened the l's own curve at its top, 1407-1431): 6 nodes on the
      right edge 724-796 become a line, Ɬ unchanged, checks and lint
      clean. Sheet build/pending/l-belt-trial.pdf, approved by the
      designer 2026-11-22: into the batch with the curl patch.

## Next session (set 2026-11-19)

- [x] (mended 2026-11-20: smooth_joins.hook_ball; the second ball's leftmost node was missing, a corner and lobe; ff ffi ffl f_f_j, followers refit) The Bold Italic's `f_f_i` ligature (glyph `ffi`) has a
      strange lower hook in its second f. Look at it on a sheet beside `ffl`, `ffj` and the
      single `fi` in the Bold Italic and the Italic; where `ffi` is made in this style is not
      yet looked up (draft_ligatures' f ligatures, or the Italic's carried through
      make_bold). `make only STYLE=BoldItalic GLYPHS="ffi" PARTIAL=1` makes a trial in
      seconds. Part of the Bold Italic's review (build/bi-review/).
- [x] (approved by the designer 2026-11-20) The Bold Italic's review sheet, `build/bi-review/bi-sheet.pdf` (`scripts/quality/bi_sheet.py`; the colour table beside it, `bi_colour.py`): no more candidates. Bold Italic review done.
- [x] (built 2026-11-20 as scripts/only_glyph.py, docs/claude/only.md; Ƈ Ɠ checked, other families not) `generate(glyph)`: make the throwaway `scripts/only_glyph_draft.py` (2026-11-19) a
      tool, `scripts/only_glyph.py`: `generate(name, style,
      recipe_overrides=None)` builds one recipe glyph (attach, bar, curl,
      hook) on the finished base of its style in seconds, with its sheet,
      to a scratch UFO. It is stage B of `docs/claude/only.md`, the
      common case only: no stroker, no whole-font passes. What it must
      do as make_bold's `rederive` does: set `make_bold.SLANT` from the
      Italic's angle (a global that main() sets, else the base is not
      deslanted), deslant a copy of the style, `derive.build`,
      `drop_specks`, `fix`, `slant_back`. A test that it gives the
      full run's outline for known glyphs (Ƈ Ɠ ƈ and others) decides
      whether a family may use it. A dependency table says which
      glyphs a recipe needs (its base, the strokes' reference o).
      Why: the full Bold Italic run takes 10-15 minutes, a trial of
      Ƈ Ɠ's cut took 1.5 seconds this way.
- [x] (done 2026-11-20, 932e1c4f) Ƈ Ɠ in the Bold Italic (step D): recipe moved to the wider C G
      (x +145/+148, cut from x - 10 above 1320, stroke from 1290,
      data_bold_italic.py), drawn marks dropped; regenerating and the
      tests were the open step at the end of 2026-11-19 (uncommitted):
      test_quality (Ɠ smooth 2.2 degrees at 1242,111, Ƈ's step),
      test_accepted, golden and digest baselines to accept with a
      review. Then step D's rest: u m, the BI's drawn letters. (ɖ ɳ ɠ ɧ looked at 2026-11-20 against their bases, saved and regenerated by only_glyph.py: the saved drawn ones match the wider d n ɡ ɦ and are cleaner; the regenerated recipes notch at the stem/leg joins. Left as they stand, nothing installed; the designer's eye to confirm.)

## Assessment in short

- Regular: release quality. Lowercase stems 164, hairlines 48 (of 2048):
  a text Didot. Even colour at 9-12 pt.
- Italic: sound, about 5 % lighter and 5 % narrower than the Regular; the
  longest quality list (735 entries, 215 kinks, 126 unsmooth joins), mostly
  inherited from Old Standard, and all of it passes on to the Bold Italic.
- Bold: sound. Stems x1.59, hairlines x1.15.
- Bold Italic: usable at text size, the weakest above about 48 pt (638
  entries: 115 wobbles, 88 kinks).
- The faults a reader meets first are not in the drawing: kerning copied
  from the upright into the italics, common pairs unkerned, punctuation
  collisions, loose tabular figures in running text.

## While Fable is available

Access to Fable ends soon (noted 2026-11-10); after that the work is done
on Opus and Sonnet, with the Haiku agents for the loops. So Fable's
sessions go, in this order, to what the later phases cannot do without
and a smaller model is least likely to get right: the methods, their
tools, and written specifications exact enough to be carried out
without it. Each item ends in a file in the repository, not in a
conversation. Nothing here waits for phases 0-4; those run beside it on
the other models. One item per session.

- [x] F1. Phase 5's method and tool (the pilot). The fitter that redraws
      an outline onto a given node structure; n a e o s g on the sheet
      (Old Standard | today | redrawn, node views, 144 and 12 pt); the
      review. Left behind: the tool with its tests, and
      `docs/claude/redraw.md`: the method step by step, how the node
      structure is chosen for a letter with no Regular counterpart
      (italic a e f g k v w y z, Greek, Cyrillic), the gate as numbers,
      the faults seen in the pilot and their fixes, what to hand back to
      the designer rather than fit. Written so that a batch of 20 is a
      Sonnet session.
      Done 2026-11-10: tool (`scripts/redraw.py`, `redraw_sheet.py`,
      `redraw_sweep.py`, tests/test_redraw.py), method
      (`docs/claude/redraw.md`, with "What may move after an install"
      and the pilot's faults). n a e o s g installed in the Italic,
      marked drawn; the Bold Italic's six and what followed approved by
      the designer on the sheets (the Bold Italic n's shallower crotch
      with them), accepted anew, the quality lists and shaping
      baselines taken with their reports' digests. Left open: the
      Bold Italic's hint zones for G and Ɠ at 35 ppem moved by 4/64 px
      though neither outline did; taken into the baseline, the cause
      not traced. The node counts quoted under phases 5-8 include
      handles, see redraw.md.
- [x] F2. Phase 3's mechanism: italic kerning from the white the italic
      shapes leave. The measure (which heights, how overhangs and
      entries count), the prototype, the sheet of 30-40 pairs against
      today's and the references, the decision. Left behind: the script,
      its test, the rule in docs/claude/spacing.md, and the list of
      what stays a hand exception and why.
      Done 2026-11-11: measure, rule, prototype and test
      (`scripts/italic_kerning.py`, tests/test_italic_kerning.py); the
      rule, the count against the references and the hand exceptions
      in docs/claude/spacing.md ("The italics' Latin kerning"). The
      computed values approved by the designer on
      `proofs/2026-11/italic-kerning-2026-11-11.pdf`
      (`scripts/italic_kerning_sheet.py`), nothing tightened past the
      upright; one wish: K y slightly tighter in the italics, a hand
      exception (spacing.md says why the rule cannot give it). Left for
      phase 3 (Opus): the rule into the generators as spacing.md
      describes, K y on its sheet, the Latin pairs test.
- [x] F3. A map of the stroking for those who change it later:
      `docs/claude/stroking.md` on `stroke_bold.py` and `fair_arcs.py`:
      the stages in order, what each constant does and what moved when
      it was changed (from FONT-DESIGN.md's record), the invariants a
      change must keep, how to test one (which sheets, which counts),
      the known dead ends not to try again. With it T4 decided switch
      by switch (settled or experiment), so that carrying it out is
      Opus work.
      Done 2026-11-11, reading and writing only (nothing run, no
      source changed): `docs/claude/stroking.md`. T4 decided there:
      ten switches settled (deleted, their values constants; with them
      make_bold's `MYIA_STROKE_OUT`, which T4's list left out), two
      kept as diagnostic arguments (the fairing, one way), the logs as
      environment; the order of carrying out and its proofs. Open
      points left there for T4's session: why `CORNER_OWN` ships at 2
      though its comment argues for 1 (γ's loop to be looked at), the
      first stroking pass that only finds knees, the stroking's work
      of 2026-10-29 missing from FONT-DESIGN.md and FONTLOG.txt.
- [x] F4. Phase 7's analysis, ahead of its drawing: the core set
      measured Regular | Bold | Old Standard Bold (counter area,
      aperture, join thickness, ball size, width gain), and from it
      what the Bold should change, per family, as numbers and as a
      trial on a e s g n o for review. Left behind: the measuring
      script, the table, the family rules proposed for make_bold, and
      in the same document how those measures carry to the Bold Italic
      (phase 8's fourth step), which cannot be tried until then.
      Written 2026-11-11, the trial open: `docs/claude/bold.md`
      (`scripts/quality/bold_targets.py`). The Bold lies inside the
      references' range in most measures and on the open side where
      it leaves it: proposed are B1 (serif gaps keep their share of
      the counter: n m h v w X Y K M), B2 (KX 1.04 | 1.02 | 1.00 to be
      seen), B3 (capital rounds inward), B4 (r's ball); joins not
      thinned. The Bold Italic's arches are the reverse: counters 24 %
      narrow. The trial sheet is made (B1 at KX 1.04, B1 with KX
      1.00, beside today's and Old Standard Bold):
      `proofs/2026-11/bold-trial-2026-11-11.pdf`. Reviewed 2026-11-11: B1
      taken and carried out (make_bold.keep_gaps); B2, B3, B4 not.
- [x] F5. T3's cause: why the runner splits ae.sc ǽ.sc ǣ.sc fl ſl
      otherwise and lands K's point on the other side of .5; the fix
      made, or specified to the line if it needs a run on the runner to
      confirm.
      Narrowed 2026-11-13, then stopped by the designer (not worth more
      time): it is not rounding at .5 nor our code. The rerun differs on
      every AMD runner with AVX-512 visible (EPYC 9V74, 9V45: 20 of 20)
      and on no other (EPYC 7763, Intel Xeons with AVX-512: 22 of 22), so
      a library picks its code by vendor and AVX-512 past arithmetic.py's
      pins; OpenBLAS (or its libgfortran) the likeliest, the stroking's
      numbers pass through it. A tolerance would not cover it (w 3 units,
      segment counts). `scripts/arith_probe.py` and the by-hand workflow
      probe.yml compare 15 stroking jobs under five pin settings. Its run
      of 2026-11-13 (43431515933): on the Intel runners and the 7763 all
      four pinned settings match this machine 15/15; on the 9V74 and 9V45
      every setting 1/15, OpenBLAS's generic kernels, numpy at its
      baseline and glibc without AVX-512 included. So no environment pin
      can fix it; what is left (libgfortran, OpenBLAS's LAPACK, the
      hardware itself) is not worth the chase. CI's reproduce step now
      only warns on AMD runners with AVX-512 and fails as before on the
      others (test.yml). Closed.
- [x] F6. Specifications for the engineering Opus will do, one page
      each in DEVELOPMENT.md or beside the code: T2 (`--only`: how the
      dependency closure is taken from builtFrom, what state a partial
      run may not touch, the equivalence test), T5 (which tables move
      where, in which order, the proof that nothing changed), T6 (the
      one key, the migration of the three present marks, what the
      generators read), phase 1's sweep (the pair sets, the measure of
      white, the list's format).
      T2's page written 2026-11-11: `docs/claude/only.md` (the
      closure from six sources, builtFrom being one and only in the
      Regular; measures such as o refused; the state; the check each
      run makes; the tests in tiers). Read from the code, nothing run:
      the timing it asks for first was not taken. T5, T6 and phase
      1's sweep are still to write (Opus, as below).
      Phase 1's sweep written 2026-11-11: `docs/claude/collisions.md`
      (the pair sets taken from the font, white measured as kern_clear
      measures it, the list's format and its test, the order). Read
      from the code, nothing run.
      T6's page written 2026-11-13: `docs/claude/drawn.md` (the key
      `org.myiadidot.drawn` in all three styles, italicSource kept as
      provenance only, draft flags review status only, make_bold
      stripping the source's marks, the four commits and the
      equivalence check). Read from the code and the UFOs, nothing
      changed.
      T5's page written 2026-11-13: `docs/claude/tables.md` (four data
      modules by style, what moves by kind and what stays, the
      generators re-exporting for the pilots and shape-grammar, the
      four commits, each proven by every line moved, every value equal
      and `make reproduce`). Read from the code, nothing changed.
      With it F6 is complete.
- [ ] Tried 2026-11-22, to the designer (build/pending/m-hook-trial.pdf):
      ɱ's step 1278,200 (35 units): derive.hook_path measured the leg at
      the cut before the recipe's `cuts` box took m's exit flare off, so
      ȷ's descender was set 35 wider than the leg (44 at cut 250, 52 at
      300). build/pending/hook_cuts.patch measures after the boxes (only
      ɱ passes boxes: no other letter can change). Step gone, edge runs
      on smoothly; but the whole tail is scaled across with it, so the
      descender and its curl come out narrower than before.
      Second option (build/pending/m-hook-keepwidth.pdf,
      build/pending/hook_narrow.patch): the piece placed as before, then
      drawn in to the leg's width at the cut and widening back to its
      own over 300 units below (smoothstep); the step gone, the curl and
      tail exactly as committed. NARROW_RUN 150 also clean, 220 left a
      4.4 kink at 1265,89. The designer: both very bad, steps in the
      stroke. The real fault: the `cuts` box (1360, -BIG, BIG, 450) sliced
      the leg flat at 450 (a 37-77 unit shoulder) and left it about 100
      wide below (m's stem ~165), the 35 at 200 only its consequence.
      Mend: the box moved clear of the leg, x0 1460 (the exit stroke's tip
      lies 1493-1600, the leg at most 1423 at 450 in the box's frame); the
      hook code unchanged, no patch. One contour, checks and lint clean,
      advance 1532 kept. build/pending/m-hook-fullleg.pdf, approved by the
      designer 2026-11-22: into the batch with the curl patch.
- [ ] F7. If sessions remain: phase 5's first two batches done on Fable
      (the rest of a-z, then A-Z), to find the cases redraw.md does not
      yet cover while the model that wrote it is still there; and the
      Italic against the Regular measured for phase 6's sheet.
      First batch (the rest of a-z) done 2026-11-11 and committed: b c d
      h ı ȷ k l m p q r t u v w x y z redrawn, f with a hook below and its
      ligatures; the faults the tests found mended (docs/claude/redraw.md,
      "After the batch of 2026-11-11": ỵ, the drawn k x m's widths, the
      repair scripts' fixtures, u's knee and entry by hand, v w out of the
      controls, ɱ joined through its leg), the five sheets rendered anew,
      baselines accepted. Open from it, for the designer: the sheets as
      rendered after the mends; the Bold Italic's ff-ligatures at 100 not
      yet seen; ſſj to look at again; ƴ's dot below now beside its
      descender as y's; 73 Italic and 76 Bold Italic glyphs accepted as
      followers of the redrawn letters without a sheet of their own (lists
      in the commit); the Bold Italic's ɱ's two doubled nodes (older).
      Second batch (A-Z) done 2026-11-12 and committed: 23 capitals
      redrawn (I O Q not: redraw.md), ⱳ's arm, the Bold Italic's capitals
      accepted, the followers' faults mended (redraw.md, "The second
      sheets, seen 2026-11-12"). Open from it, for the designer: the
      mends as rendered (proofs/2026-11/bold-italic-followers-mended-2026-11-12.pdf,
      proofs/2026-11/italic-followers-mended-2026-11-12.pdf: g.sc ǥ.sc ₵ ₿ ы.sc
      psi.sc у.sc Ʌ; their accepted marks withdrawn until seen); O and Q
      want drawing.
      The Bold Italic's hooks of Ƙ Ƴ Ʋ (and ƙ.sc ƴ.sc ʋ.sc) done
      2026-11-12, chosen on proofs/2026-11/bold-italic-hook-arms-2026-11-12.pdf:
      Ƙ Ƴ version C, Ʋ version D (make_bold.CURL_ARM).
      O and Q drawn 2026-11-12 (`scripts/draw_oq.py`), approved and
      installed; not committed: small caps moved after it, the causes
      traced and the Italic's mended in the generator (`sc_late`,
      docs/claude/redraw.md, "O and Q drawn"); waiting for the
      designer's review of the late sheets, then baselines and commit.
      (Approved and committed 2026-11-12, 4fc4b058.)
      The open reviews closed 2026-11-14: the mended followers accepted
      (Ʌ in both italics; the Bold Italic's ₵ ₿ ы.sc psi.sc ǥ.sc) but the
      Italic's ₿, back to the Regular's sloped (its own recipe withdrawn);
      on `proofs/2026-11/f7-open-reviews-2026-11-14.pdf` the Bold Italic's
      ff-ligatures, ſſj and ƴ's dot below approved, у.sc's right arm
      drawn straight into its serif; the Bold Italic's ɱ given ŋ's right
      stroke and hook (`proofs/2026-11/bold-italic-m-hook-2026-11-14.pdf`, B).

- [x] F8. Outside the plan, 2026-11-15, after the brief's three items
      (redraw's gaps, phase 6's measure, the kerning measure: all in
      their documents):
      the rest of the Italic's core set fitted dry (107 glyphs: 104
      candidates as they are, the old-style 7 and ъ with one spec entry
      each, the Euro handed back for a step of its own, which the gate
      now names: `docs/claude/redraw.md`, "The rest of the core set
      fitted dry"); so phase 5's remaining batches are Sonnet's.
      The quality lists sorted by where each line is mended
      (`scripts/quality/families.py`, `docs/claude/longtail.md`): the
      families for phases 6-8 with their mends and the order. Mended on
      the way: the zone check measured the italics' lowercase from x's
      exit hook (23 lines gone from each italic list). Left by it, in
      longtail.md's order: the marks' extremes in make_italic (Opus, 65
      lines), the Italic's lighter ascender stems onto phase 6's sheet,
      the small caps' fit at drafting as a trial, the Bold's extremes
      after the designer's word.
      2026-11-16: the first two done. The marks pass through
      `with_extremes` in make_italic (quality-Italic.txt 624 -> 592
      lines, quality-BoldItalic.txt 613 -> 584; the Bold Italic's marks
      moved by up to 2 units, its Hook lost a stray node: longtail.md,
      family 1). The long stems are measured (`italic_measures.py`,
      `long stem` rows; italic.md, "The long stems"): Old Standard's
      drawing, inside the range, a question for the sheet.
      2026-11-23: the small caps' fit done (longtail.md, family 3):
      redraw holds a handle's share at smooth nodes, the Italic's
      small caps come from their fitted drafts (139 of 146), approved
      on the movers' sheets; the Bold Italic's new wobbles (19 small
      caps) wait for phase 8.

Budget (2026-11-12): F1 to F4 are done, of F6 the pages for T2 and
phase 1's sweep, of F7 both batches. The limits now:

- The week's Fable allowance: 91 % used, 9 % left, renewed Sunday
  2026-11-15 10:00. After the renewal there is one 5-hour window on
  Fable, on that Sunday, and then access ends.
- The weekly limit over all models: 49 % used; the 51 % left lapse on
  Sunday 10:00.
- The full reset is taken and used.

So the plan has three parts.

Thursday to Saturday, on Opus and Sonnet: what Fable wrote is carried
out, to find where its specifications and methods fail while Fable can
still mend them. Each session writes its gaps to
`docs/claude/open-for-fable.md`: the case, what the document said,
what was missing. In this order:

- Sonnet: one batch of phase 5 outside a-z and A-Z (Greek or Cyrillic
  italics, where no Regular counterpart gives the node structure), by
  `docs/claude/redraw.md`. The test of whether a batch is a Sonnet
  session.
- Opus: phase 3, the rule into the generators as
  `docs/claude/spacing.md` describes, K y, the Latin pairs test (done
  2026-11-12; the gap found, the guard lost with a dropped pair, in
  spacing.md and open-for-fable.md).
- Opus: T4 by `docs/claude/stroking.md`, with its three open points
  (done 2026-11-12: the open points answered there).
- Opus: T2 by `docs/claude/only.md` or phase 1's sweep by
  `docs/claude/collisions.md`; both were read from the code with
  nothing run, so they are the likeliest to be wrong somewhere
  (the sweep done 2026-11-13; its two gaps in open-for-fable.md).
- Opus, after these: F5 (with the runner, or the tolerance alone and
  the split glyphs listed as known), F6's pages for T5 and T6. Neither
  needs Fable.

Before Sunday, the designer's review of what is open under F7, since
what is rejected after Sunday goes to Opus: the two sheets of mended
followers of 2026-11-12, the Bold Italic's ff-ligatures at 100, ſſj,
ƴ's dot below, and whether O and Q are drawn by hand or by Fable.

On Fable:

- With the 9 % of this week, one item at most, reading and writing
  only, nothing run and no sheet: the specification of phase 6's
  measure (the Italic against the Regular: what is measured, the
  sheet, the gate), the last part of F7 and the only method still
  without a document. Opus writes the script from it.
- The window on Sunday, in this order: the methods mended from
  `docs/claude/open-for-fable.md`; what the designer's review
  rejected; O and Q, if they are Fable's.

How these sessions are run, so that they do not go the way of F1's:

1. Files before sheets: the rule and the script are written and
   committed before a sheet is rendered, so that a session that runs
   out leaves the mechanism behind.
2. The loops off Fable: pair measurements, the reference fonts'
   numbers, rendering the sheets, `make test` and `make reproduce` go
   to font-measure and font-runner. Before a session an Explore agent
   gathers what it needs from the sources and the history into one
   file, and Fable reads that.
3. One review round per item: what is rejected after it is written
   down as an open point for Opus, not worked through on Fable.

### Which model after that

- Opus: engineering across files with the design settled, and anything
  in the generators' shared machinery: T2, T4-T6, T8, phases 1 and 3's
  tools and tests, phase 7's family rules, phase 8's parameters, a
  letter the method refuses.
- Sonnet: bounded work against a written method and a check: phase 2's
  pairs, the batches of phases 5-8 (fit, sheet, mark, lists), T7's
  inventory, T9, T10, README and release.
- Haiku (font-runner, font-measure): every run and every report.
- A session starts on the smaller model and moves up only when the
  method does not cover the case; then the method's document gets the
  case added, so the next one does not need to.

## Phase 0: close the present state

Model: Sonnet; the CI step with F5.

- [x] Commit the staged Bold Italic m-family work (m т ɯ ᵯ ɰ ɱ ſh, proof
      `proofs/2026-11/bold-italic-m-family-2026-11-10.pdf`); let the hook finish.
      (In 120800ac.)
- [x] `scripts/sync_check.py`: no "(conflicted)" copies, no lost glyphs.
      (Clean 2026-11-13, before and after the rebuild.)
- [x] CI green (T3 in the tooling track): `make reproduce` fails on GitHub's runner since cb9b7dac
      (12 Bold Italic glyphs: K Κ Ķ Ǩ Ḱ Ḳ Ḵ at (1193, 1170), ae.sc ǽ.sc
      ǣ.sc, fl, ſl). First choice: make the rounding deterministic where a
      point lands on .5 and where the segment splits; second: a one-unit
      tolerance in `scripts/check_reproducible.py`. (DEVELOPMENT.md)
      Closed with F5 (a078bce4): neither, the cause is AMD runners with
      AVX-512; CI's reproduce step only warns there.
- [x] Rebuild all formats (`make fonts`): `fonts/ttf` and `fonts/webfonts`
      are of 2026-10-26, the OTFs of 2026-11-09. Rebuilt 2026-11-13.
- [x] `make test` and `make qa` on the rebuilt fonts; note the state here
      as the starting line for the phases below.
      Starting line, 2026-11-13 (at 1ad1969e): `make test` 466 passed,
      9 skipped. `make qa` failed first on fontbakery's
      transformed-components in the italic TTFs: т.loclSRB's bar is the
      macron stretched x1.84 (make_italic.serbian_bars), the TTFs of
      10-26 predated it. Mended in the build, not the UFO: the unhinted
      TTF decomposes transformed components (fontmake's
      DecomposeTransformedComponentsFilter; only that glyph changes, the
      same outline). Then fontbakery 0 FAIL; WARN, OTF and TTF alike:
      ligature carets (2), unreachable glyphs (4), spacing marks in the
      mark class (4), post.italicAngle (1), math sign widths (2), no soft
      hyphen (4); TTF only: contour counts (4). Reports
      `build/qa/fontbakery-{otf,ttf}.md`.

## Phase 2: missing kerning

Model: Sonnet, the measuring by font-measure.

Unkerned today in every style (advance difference 0): `Ty` `Tw` `A“` `“A`
`L“` `7.` `’s` `Kr` `Ra` `Gi` `»W`. `Ty` `Tw` `A“` leave visible holes.

- [x] Inventory (2026-11-13): 336 requested pairs measured against Charis
      and Libertinus (gap over n n, a scratch script after pairs.py:
      build/quality/pairs-requested-Regular.txt) and again with
      italic_kerning's share (white over the case's own rhythm, the
      measure of the italic rule and test_latin_pairs). The two disagree
      in direction for R v w y, R O Q, A“ A", 7. 1. 1, and W v w: no pair
      was set on one measure alone.
- [~] Set in the Regular by group (2026-11-13), absolute values, where both
      measures and the references agree: A ’ ” -272 to -132; V a -160 to
      -112, V o c e d -192 to -162 (V à V è with them), V v w -40 (new);
      W given its own left group (public.kern1.W, split from V's, V's pairs
      copied): W a -20, W o c e d -60, W à 0, W è -36, W u -22, W g -80;
      Y v w -170 to -110, Y y -152 to -105. The italics follow by the rule,
      no hand exception needed. Left open for the designer (sheet:
      `proofs/2026-11/kerning-phase2-2026-11-13.pdf`, last pages of each style):
      - spacing, not pairs: ' and ” are loose before every stem capital
        (H B D E N P, by about 0.1 of the rhythm), G is tight before every
        lowercase (n o a e i): sidebearings of ' ” and G, not D or i pairs;
      - (which measure decides: spacing.md, "One measure for Latin
        kerning", 2026-11-15: the share, confirmed the same day by
        `scripts/quality/pair_measures.py`; its tools are Opus's, then
        these are Sonnet's)
      - the measures disagree: R v w y, R O Q, A“ A", L“ “A, 7. 1. 1,
        W v w p q m (gap measure: too loose; share: in range or tight);
      - T y w v (T's x-height serif on its right arm), T u p z m n r (the
        gap measure asks +250 to +400, which is T's bar, not the pair);
      - guillemets: «A »W T» «T «V »V «Y »Y (Charis and Libertinus differ);
      - W before capitals and punctuation, measured for the first time
        once W had its own group: W, WA WJ WO WÆ Wj tight in the Regular
        and the italics (tests/data/latin-pairs-*.txt list them); the share
        asks 140-340 units, too much to set unseen;
      - 41 pairs without shared ink height (quote before or after a round
        lowercase, ’ s): need an ink-to-ink measure;
      - K R X before rounds and v w y beyond the R ones: not set.
- [x] Sheet of words per family, four styles:
      `proofs/2026-11/kerning-phase2-2026-11-13.pdf`; `make diffenator` and
      `make regress` read, shaping baselines accepted with the report's
      digest (2026-11-13).

- [x] `Üb` (the designer, 2026-11-13, on the pangram page of samples.pdf,
      "Falsches Üben von Xylophonmusik"): looks bad in almost any style;
      the diaeresis touches the b's ascender in the italics, and it is not
      good in the Regular and Bold either. Look at Ü and the other
      capitals with diaeresis, acute and the like before an ascender
      (Üb Üd Üf Üh Ük Ül Ó… and the Greek and Cyrillic kin), by
      `make collisions`' measure and by eye, in all four styles; mend
      through the guard/kern_clear route, not by hand in a generated style.
      Done 2026-11-13: not the accent but U's top serif before b's (Ub as
      Üb), and every capital with a top serif before an ascender: the
      italics' serifs met (U J N V W Y b: 1-3 units), the Bold's U b had
      28 (H b 96). kern_clear.ascender_entries + ASCENDER_CLEAR 60, measured
      every way above the x-height (spacing.md); Italic U b +72, V +82,
      Y +98, Bold U b +34, N +40, the Regular only V W Y +2 (its U b keeps
      87). Before | after and candidates 30/40/60:
      `proofs/2026-11/ascender-clearance-2026-11-13.pdf`. Open:
  - [x] the Regular's U b keeps 87 units (H b 120): the designer found it
        "not good" too; a looser ASCENDER_CLEAR (80-120) would reach it,
        and V W Y with it (see the sheet's candidates).
        Decided 2026-11-14: 87 stays, ASCENDER_CLEAR stays 60 (sheet of
        60/80/100/120: `proofs/2026-11/ascender-clearance-regular-2026-11-14.pdf`).
  - [x] the italics' Į (Iogonek) stands about 160 units right of I at
        the same advance (bounds 131..1097 against -29..923): a glyph
        fault; the rule now gives it about +200 before every ascender.
        Done 2026-11-13: Old Standard's own Į stood 84 right of its I
        (the only precomposed letter so); make_italic sets it on I
        (data_italic.OS_SHIFT, I's anchors: TopCap 709 -> 680). Į b +36
        (I b +28), Bold Italic +18; į.sc with it. Sheet
        `proofs/2026-11/iogonek-italics-2026-11-13.pdf`.
  - [x] the same family below: capitals before accented lowercase (U ȉ,
        T ï, Ví): the lowercase accent over the capital's serif, which
        neither this rule nor the sweep measures.
        Done 2026-11-13: about 550 pairs a style came within 20 units,
        nearly all a narrow i/ι under a wide mark (ȉ ǐ ĭ ῖ ἶ ϊ ΐ);
        against Charis and Libertinus Myia is in range but for the
        Bold's N ǐ 8, U ǐ 0 (both 90-130). kern_clear.accent_entries,
        ACCENT_CLEAR 40 (GUARD's white), measured every way above the
        x-height: Regular N ǐ +32, H ȉ +104, Γ ῖ +22; Bold U ǐ +72.
        Sheet with candidates 20/40/60:
        `proofs/2026-11/accent-clearance-2026-11-13.pdf`; the designer chose 40
        (2026-11-14). Left open, found on the way:
    - [x] f before accented i (fî in French "fît", fï fì fǐ): the hook
          meets the mark in the upright styles (0 units); Charis touches
          too, Libertinus substitutes f.short. A contextual f, not kerning.
          Done 2026-11-14 (the designer chose the contextual f): f.short
          ff.short, the hook x0.6 (0.7/0.5 looked the same at reading
          sizes: `proofs/2026-11/f-short-candidates-2026-11-14.pdf`), calt
          caltShortF before every Latin lowercase letter f comes within
          40 of (î 184, ï 82, ľ 83 now); ǐ ĭ ȉ kerned apart (ȉ +146).
          Left: f.short takes f's glyph kerning only through kern_clear
          (t f -45 is not t f.short).
    - [x] pinyin ǖ ǚ ǜ Ǖ Ǚ Ǜ are missing (Ǘ ǘ are there): composites
          (not in scripts/coverage.py's TARGET, as it turned out). Done
          2026-11-14 with the batch of phase 11's composed letters.

- [x] `Wo` (the designer, 2026-11-13): the gap looks too big. W's own
      group (3017a0aa, W apart from V) set W o/e/c at -60 (Bold -62) from
      V's -192 (Wa -160 -> -20). Nearest ink, units at Myia's cap height:
      Regular W o 395 (V o 392; Libertinus 342, Charis 389, Old Standard
      396), Italic 439 (Libertinus 291, Charis 364: both tighter), Bold
      407 (353, 384), Bold Italic 437 (331, 363). The italics are loose by
      the reference rule; the upright's look is W's open area, which
      nearest ink does not see: a sheet of W o e a at -60/-100/-140 to
      choose on.
      Chosen 2026-11-14 on `proofs/2026-11/w-lowercase-2026-11-14.pdf`: W c -140,
      W a -80, W u -80 (the Bold x1.04, the italics by the rule).
      The italics keep the rule's values though W u (and the Bold Italic's
      W c) come out tighter than the five reference italics
      (proofs/2026-11/w-italics-2026-11-14.pdf; latin-pairs lists).

- [x] Qu (dlig Q_u), the tail below the O: a redesign asked of Fable
      (2026-11-14: steeper neck, the swash leaving level at the crotch,
      thinning to a hairline needle; with and without an upturned end),
      set beside the present one on `proofs/2026-11/qu-tail-2026-11-14.pdf`. The
      designer kept the present tail (QU_TAIL unchanged).

## Phase 3: the italics' own kerning

Model: the mechanism is F2; after it Opus for the test, Sonnet for the sheets and exceptions.

The Italic carries the Regular's values unchanged (`Av` −128, `To` −108,
`Wa` −160, `Ye` −204 in both), the bolds the same x1.04, though the italic
letters are another design with other sidebearings and overhangs. Greek
and Cyrillic are already measured per style; Latin is not.

- [x] Measure: `scripts/quality/pairs.py Italic` and `BoldItalic`
      calibrated by each style's own n n / H H, as `greek_pairs.py` does;
      list the Latin pairs outside the references' range.
      Done 2026-11-14 (`make pairs` on fonts rebuilt from a694d018's
      sources; every pair outside the range, with its distance:
      build/quality/pairs-rows-STYLE.txt). 294 frequent lowercase pairs.
      What it shows is spacing, not missing kerns:
      - Italic: nothing past 0.15 n-gaps. About 100 pairs (o e p r w v
        against stems and rounds) sit 0.00-0.05 under the references'
        lowest, all in one direction: n n is a little loose for the
        rest of the lowercase, a matter of sidebearings, not pairs.
      - Bold Italic: the same uniform tightness, deeper (to -0.11), and
        three letters of their own: t sits right in its advance (left
        tight: it dt -0.16, nt mt lt -0.12; right loose: tn +0.15, tr
        +0.10, tu ti +0.08); f's left is tight (df -0.29, nf -0.23, of
        -0.18); r's right is tight (rh -0.17, ra -0.10). Th (-0.85) is
        the measure's blind spot (T's stem, not its bar), as in phase 2.
      - Bold, and the Regular it comes from: t's right loose (Bold tn
        +0.15, tu ty +0.13, tt +0.14; Regular among the loosest: kt tM
        at ty tw tz tr tn).
      Proposed, for a sheet before any change: t's sidebearings in the
      Regular (the Bold follows), and t f r in the Bold Italic's
      generator data; the italics' n against the rest of the lowercase
      left for phase 6 (the Italic's harmonisation).
- [x] Decide the mechanism before the values (one source of truth;
      decided 2026-11-11, F2: docs/claude/spacing.md; to carry out:
      the rule into make_italic.py and make_bold.py, K y by hand; done
      2026-11-12, K y -30, approved on
      proofs/2026-11/italic-kerning-in-generators-2026-11-12.pdf): the
      Regular's kerning scaled per pair by the white the italic shapes
      actually leave (computed), with `ITALIC_KERNING` and
      `ITALIC_BOLD_KERNING` holding only reviewed exceptions. A design
      decision to settle on a sheet of 30-40 pairs first.
- [x] Re-proof the Bold Italic's hand-set positive kerns in
      `ITALIC_BOLD_KERNING` (`scripts/make_bold.py`, about line 940): they
      predate or straddle the stroked outlines. `G r` +121 leaves a clear
      gap in "Größe"; look also at `g a` +89, `u f` +92, `i f` +75,
      `a y` +67, `a f` +66, `w a` +57, `v a` +50. Delete those the stroked
      letters no longer need.
      Done 2026-11-14: each measured with and without its value (share
      against five reference italics, pairs.py's gap against three); the
      designer chose on `proofs/2026-11/bold-italic-hand-kerns-2026-11-14.pdf`:
      G r 90, a y dropped, f t -30, u t 60. Kept: w a g a i f a f v a u f
      R e (still needed on both measures), g h +43 (still a little tight),
      f r -95 (the measures disagree).
- [x] Add a Latin pairs test like tests/test_greek_pairs.py: a listed
      pair may not get further off. Done 2026-11-12:
      tests/test_latin_pairs.py, the italics against five reference
      italics (italic_kerning.outside), lists latin-pairs-Italic.txt and
      -BoldItalic.txt (all too tight; `update_test_data.py --latin`).
- [ ] Sheets, `make diffenator`, baselines.

## Phase 4: figures

Model: Opus for the default's change in space_figures.py, Sonnet for the rest.

- [x] Decide the default: today lining and tabular, so dates and numbers
      in running text set loose, most of all in the italics. Recommended:
      proportional lining by default, `tnum` for tables (a change in
      `scripts/space_figures.py`'s generated block and in README's feature
      table; old documents reflow, so before 0.900 or never).
      Decided 2026-11-14 by the designer: proportional, as the Didot kin
      (GFS Didot, Bodoni Moda, Libre Bodoni; Charis, Libertinus, EB
      Garamond and Old Standard default to tabular). The default glyphs
      are the proportional ones (the .pf gone), zero.tf ... the tabular
      ones, centred in the 0's width (the Regular's tabular 1 7 5 moved
      15-27 units from where they were drawn in the cell). The optical fit
      left the 1's and 4's foot serifs outside the advance (11 41 fused,
      H1 touched; so under pnum since it was made): a floor across the
      foot band, I's mean side, chosen on
      `proofs/2026-11/figures-feet-2026-11-14.pdf` (Regular 1 629 -> 876, 4 852 ->
      936, 2 +32). Sheet of the change: `proofs/2026-11/figures-proportional-2026-11-14.pdf`.
- [x] Italic lining figures against the italic capitals: `1` stem 188
      against `n` about 175 across; they read darker than the words
      around them in lowercase text. Measured 2026-11-14 (deslanted, at
      mid-height): the italic n is 191 now, the 1 188, H 183 (1/H 1.03,
      references 0.94-1.00; 1/n 0.99, references 0.96-1.25); the Bold
      Italic's 1/H 1.00 as every reference. The 1 stands with the
      capitals at their weight; nothing to change. What read as dark was
      where it stood: right of the letters (next item).
- [x] The lining figures' sides (2026-11-14): measured as pairs against
      seven references (`scripts/quality/figure_pairs.py STYLE`), what
      looked like missing kerning was spacing: equal optical sides set
      the figures 0.2 H-gaps tighter than every reference and the open
      sides (4's left, 7) too close. Each side now the 0's base plus
      `data_regular.FIGURE_SIDES`, chosen on
      `proofs/2026-11/figures-sides-2026-11-14.pdf` (Regular: rhythm 0.90 ->
      1.09, references' median 1.10; every side within 20 units). The
      Bold's drawn 4 refitted by hand to the same rule.
- [x] Per-style figure sides (2026-11-14): the Regular's table, over
      the 0's, left the italics' figures about 95 units right of their
      letters (judged upright the italic letters stand left in their
      advance; Italic 0 o 0.46 H-gaps, references' median 0.75, 1 H 0.78
      against 1.21, H 1 1.36 against 1.19), which figure-figure pairs
      cannot see. `figure_pairs.py` has an absolute fit now (pair gaps
      over the cap height, figures beside H O n o too); the italics take
      a table each over the H's (`data_italic.ITALIC_FIGURE_SIDES`,
      `data_bold_italic.BOLD_ITALIC_FIGURE_SIDES`), every side within 2
      units of the fit. "Bold Italic tighter than every reference" was
      its loose capitals (H H 0.32 of the cap height, references
      0.22-0.25): over the cap height its figures were in range. The foot
      floor dropped for these tables (the designer, on
      `proofs/2026-11/figures-italics-2026-11-14.pdf`): it held the 1 and 4
      23-58 units wider than the fit; the feet stay 125 units or more
      apart. Left: the Bold Italic's capitals' own spacing (H H 0.32)
      for phase 3's or a later look; the Regular and Bold could take the
      same over-the-H rule (it would move the Bold's 2, whose foot the
      per-side floor would push 22).
- [x] Figure kerning after the sides (2026-11-14), in the Regular (the
      Bold x KX, the italics by their rule): 5 1 -65, 5 7 -60, 5 2 -45,
      7 1 -50, 7 3 -40, 7 before . , -70, 2 before . , -35 (`figure_pairs.py`'s
      rest, the period's against the other figures': Myia's period
      stands looser after every figure, -38 to -57 of the references'
      median, a matter of its own). The Italic's 7 1 (-47 by the rule)
      and 2 , (-35) fell just outside the reference italics: hand values
      -5 and -38 in ITALIC_KERNING; the Bold Italic's 7 1, unkerned, is
      listed in latin-pairs-BoldItalic.txt (tight only over its loose
      H H). The en dash before 3 and 5 measures
      near but looks as GFS Didot's: left. Old-style figures (`--osf`):
      no case, the references' own forms disagree; the Regular's are
      reviewed drawings (2026-11-09).

## Tooling track

Beside the phases, from a reading of the tooling on 2026-11-10 (not
timed anew: durations are the project's own notes). What stays as it is:
reproduction on every commit, exception lists that only shrink,
baselines accepted by a reviewed report's digest, acceptance with
fingerprints, pinned references and Unicode data. T1-T4 before phase 5,
whose hundreds of small iterations they make cheap and safe; T5-T10
alongside, each when the phase that needs it comes up.

### Before phase 5

- [ ] T1. The working copy out of the synced folder: git is the sync. A
      UFO is thousands of small files; the "(conflicted)" copies and
      lost glyph files `scripts/sync_check.py` looks for come from
      syncing them.
      - [x] everything pushed; no git worktree left; the validation
            lock unaffected (the working copy did not move). Done
            2026-11-22.
      - [x] the folder excluded from the sync, in place (2026-11-22).
            The leftover "(conflicted)" copies outside the UFOs (one in
            `.git`, four in `.ruff_cache`) deleted; `sync_check.py`
            clean, `git fsck` sound.
      - [ ] `sync_check.py` and the conflict check in `make generate`
            kept until a month has passed without a finding
            (2026-12-22), then dropped, CLAUDE.md's rule with them.
- [x] T2. A fast loop for single glyphs: `make_bold.py` and
      `make_italic.py` take whole UFOs only (the Bold Italic about 5 min
      40 s).
      Specified 2026-11-11 (F6): `docs/claude/only.md`, to carry out
      in its order. Its step 0 comes first: the runs timed with the
      stroke cache warm, which this figure predates; under a minute
      each, `--out` (the whole run into scratch) and the sheet are all
      of T2, and the closure below is not built.
      Step 0 and stage A done 2026-11-13. Timed on copies, cache warm,
      with the validation lock held (seconds; "changed": one node of n
      moved in the Regular and the Italic):

      | run | warm | changed |
      |---|---|---|
      | make_italic (with its smallcaps.py) | 58 | 59 |
      | make_bold Regular → Bold, smallcaps.py | 40 + 5 | 40 + 5 |
      | make_bold Italic → Bold Italic, smallcaps.py | 65 + 22 | 71 + 22 |

      The Bold Italic over a minute, so profiled (cProfile, 95 s
      under it): `kern_clear.clear` 30 s (16 of them redrawing each
      glyph's path for every pair), make_bold's slit check
      (`glyph_lint.notch_findings`) 19 s, `write` 12 s, `optical_fit`
      7 s, `space_figures` 6.5 s, `rederive` 6 s; no stroking (cached).
      kern_clear now draws each glyph once and only moves it:
      20 → 12 s in each italic generator, the kerning and its record
      identical in all four styles to HEAD's. Stage A built: `--out`,
      `make only`, `scripts/only_sheet.py`, tests/test_only.py; `make
      only STYLE=Bold` 45 s and the Bold Italic's run, both 0
      differences from sources/. Stage B (the closure) not begun: the
      Bold Italic's ~80 s are a whole-font pass each (the slit check,
      smallcaps.py's 22 s, write), not one glyph's work, so caching
      those passes is likely the smaller step; for the designer to
      decide whether 80 s is fast enough.
      Decided 2026-11-13 by the designer: fast enough for now; T2 ends
      at stage A, the closure (stage B, `--only`) and the passes'
      caches not built unless the loop becomes the bottleneck.
      - [ ] `--only GLYPH ...`: those glyphs and what is built from them
            (lib `org.myiadidot.builtFrom` names the dependencies),
            written to a scratch UFO under `build/`, never to
            `sources/`;
      - [ ] a sheet straight from it (source style | committed | new,
            with node views, 144 pt and words at 12 pt), one command;
      - [ ] a test that `--only` gives the same outlines as the whole
            run for a sample of glyphs, so the preview cannot drift from
            the build.
      - [x] (built 2026-11-21: fontforge_inputs.redirect_drafts,
            scratch_out.drafts_for; `--only Ƥ` redrafts ƥ.sc into the
            scratch store, sources/drafts untouched) (found 2026-11-21, phase 6 step D) `make_italic.py --only
            --out` stops when a glyph asked for has small caps drafted
            from it (fontforge_inputs.READ_ONLY: "small-cap drafts to
            make again ... a scratch run does not write
            sources/drafts/Italic-smallcaps.ufo"). Ɓ Ɗ Ƥ (ɓ.sc ɗ.sc
            ƥ.sc) and Ƈ Ɠ (ƈ.sc ɠ.sc) each took a full `make generate`
            for what `--only` does in seconds. Let a scratch run draft
            into a scratch copy of the drafts store (under `--out`),
            sources/drafts untouched, so these letters can be tried
            with `--only` as well.
      - [x] (built 2026-11-21 per style, not per glyph: the hook makes
            again only the styles without a proof, stale.py unproven,
            check_reproducible.py STYLE ...; per glyph not begun)
            (2026-11-21) The commit's `make reproduce` for a small
            change: check only the glyphs whose dependencies changed
            (`org.myiadidot.builtFrom`, built_from.py), once a test
            shows such a partial check finds what the full run finds;
            the full run stays for generator-wide changes and before a
            release. Until then the full run is the safe one. (The hook
            already skips docs-only commits and runs `make reproduce`
            only for sources/ and scripts/.) On a machine with more
            cores, MYIA_JOBS set per machine above 4.
      - [ ] (not built, 2026-11-21: make_bold reads data_italic's tables
            itself, so every data_italic change reaches the Bold Italic
            anyway; it would help only for a Regular change the Italic
            does not pass on) (2026-11-21) `make generate` skips the Bold Italic when
            nothing it reads changed: after the Italic's stage,
            `stale.py` compares the Italic's fingerprints and the bold
            generator's files with the last stamp. The stamp covers
            neither kerning nor features, which make_bold also reads:
            put them in it first, or a changed kerning always runs the
            stage. (Phase 6 step D, Ɓ Ɗ Ƥ: the Bold Italic came out
            unchanged after its whole stage.)
      - [x] (built 2026-11-21: `make generate STYLES=auto`, stale.py's
            per-style stamp and REACHES, tests/test_stale.py;
            docs/claude/commands.md) `make generate STYLES=...`, chosen from what
            changed: data_italic.py or make_italic.py → Italic and Bold
            Italic; data_bold.py → Bold; data_bold_italic.py → Bold
            Italic; derive.py, shared modules or a Regular glyph → all.
            Every step D run rebuilt the upright Bold, which none of its
            changes could reach, sharing the cores with the Italic.
      - [x] (built 2026-11-21: stale.py's proof and `proven`, the hook's
            run-checks; docs/claude/tests.md; the designer took the
            trade) (2026-11-21) The commit's `make reproduce` right after a
            `make generate` on the same inputs: `generate` records a
            hash of the UFOs it wrote beside its stamp; when sources,
            generator files and the generated UFOs all still match, the
            hook takes that run as the proof instead of making the
            styles again. Lost: the check that two runs agree (nearly
            always so on one machine); kept by a full reproduce before
            a push or on another machine (T3).
- [ ] T3. Reproduction across machines (phase 0's CI step, here in
      full). Recommended: a one-unit tolerance on point coordinates in
      `scripts/check_reproducible.py` (a unit is 1/2048 em), node
      counts and structure still exact; the segment split of ae.sc
      ǽ.sc ǣ.sc fl ſl made deterministic, since a tolerance cannot
      cover a differing node count. The alternative, the generators in
      a pinned container locally and in CI, only if the tolerance
      hides a real difference.
- [x] T4. The experiment switches out of `scripts/stroke_bold.py` (14
      environment reads: `MYIA_G2`, `MYIA_G2_LINES`, `MYIA_FAIR`,
      `MYIA_ONE_WAY`, `MYIA_BLEND`, `MYIA_SPLIT`, `MYIA_CORNER_*` ...):
      a variable left set in a shell changes the generated font
      silently. Decided switch by switch 2026-11-11 (F3):
      `docs/claude/stroking.md`, "T4: the switches, decided", with
      the code change for each and the order; to carry out as written.
      - [x] each one: settled (delete the switch and the dead branch)
            or still an experiment (an explicit argument of the
            function, set by a pilot script);
      - [x] kept as environment: only what does not change outlines
            (`MYIA_JOBS`, `MYIA_STROKE_CACHE`, the logs);
      - [x] `check_reproducible.py` refuses to run with an unknown
            `MYIA_*` variable set.
      Done 2026-11-12: ten switches and make_bold's `MYIA_STROKE_OUT`
      deleted, `fair` and `one_way` keyword-only arguments of
      `embolden_by_strokes`, `stroke_cache.KNOWN` the one list, `make
      reproduce` unchanged; `tests/test_stroke_switches.py`.

### Alongside the phases

- [ ] One sheet of the 36 italic composites whose parts keep the
      Regular's vertical offsets (`: ;`, `÷ ±`, inferiors, denominators)
      for the designer (`docs/claude/collisions.md`, its last section);
      nothing moves without it. The low quotes `„ ‚`, found with them,
      are done (2026-11-16: `ITALIC_STANDS_AS`, FONTLOG).
- [x] The guard's result held by a test (specified 2026-11-16:
      `docs/claude/collisions.md`, its last section). Opus or Sonnet:
      the kept-keys and held-white assertions in
      `tests/test_collisions.py` (no font change), then `guard`
      measuring positive pairs too (kerning changes: its own commit).
      The unkerned pairs under GUARD are counted there by kind; the
      families among them wait for the designer to name them.
      The two assertions done 2026-11-16 (`test_guard_keys_kept`,
      `test_guard_white_held`; strict, no list: the pairs short of
      GUARD were kern_clear's Ink entries, collisions.md). The positive
      pairs done 2026-11-16 (collisions.md: ogonek before j's kind, ζ
      before the breathing capitals, loosened only). The families of
      point 2 wait for the designer.
- [x] T5. Data apart from machinery in `derive.py`, `make_italic.py`,
      `make_bold.py` (about 2,900 lines each; make_bold 62 module-level
      tables beside 40 functions, a dozen imports inside functions
      around circular dependencies). Recipes, kerning tables,
      sidebearings, keep-whole and rebuild lists into data modules per
      style (Python, the aligned tables kept by hand as now), the
      machinery importing them. One generator at a time, each move a
      commit that `make reproduce` shows changes nothing. Before
      phase 3 for the kerning tables, before phase 7 for make_bold's
      recipes.
      Specified 2026-11-13 (F6): `docs/claude/tables.md`, to carry out
      in its order (after T6, whose page cites these files by line).
      Left by it for later: the cycle of functions between make_italic
      and make_bold (a module of what both use, its own proof).
      Done 2026-11-13 in four commits (make_bold, derive, make_italic,
      the imports and pointers): `scripts/data_regular.py`,
      `data_italic.py`, `data_bold.py`, `data_bold_italic.py`, each move
      proven by every line moved, every value equal and `make reproduce`;
      `tests/test_data_modules.py`. derive went before make_italic (its
      BIG); what else differed is at the end of tables.md.
- [ ] T5b. The cycle of functions between the generators: make_italic's
      top-level import of make_bold's `mark_like`, `redraw`, `write`,
      `WHOLE_KEY`, make_bold's function-local imports of make_italic's
      functions (`round_corner`, `straighten_run`, `build_own`,
      `level_gain`, `capital_width`, `uncrossed`, `recipe_scale`,
      `serbian_bars`, `serbian_gje`). A module of what both use, a
      machinery move with its own proof (docs/claude/tables.md).
- [x] T6. One mark for "drawn and kept": today the Italic's
      `org.myiadidot.italicSource` = "drawn", the bolds'
      `org.myiadidot.drawn`, and a cleared draft flag freezes an Italic
      glyph too. With about 250 drawn core glyphs a style: one key, one
      tool (`scripts/drawn.py` for all three styles, date and reason),
      the generators reading only that; docs/claude/quality.md and
      CLAUDE.md follow. Before phase 5's first batch is marked.
      Specified 2026-11-13: `docs/claude/drawn.md`. Done 2026-11-13:
      the Italic's 114 kept glyphs carry `org.myiadidot.drawn`,
      make_bold strips the source's marks, every reader goes through
      `drawn.is_drawn`; what differed from the page is at its end.
- [ ] T7. The repair scripts retired as their glyphs are drawn: about
      25 scripts patch single generated glyphs at fixed points
      (`dollar_bars` `dollar_drawing` `j_bar` `l_belt` `t_slash`
      `y_dot` `phi_drawing` `r_hook` `aleph` `p_hook_join` `cedilla`
      ...), each with its test. When a glyph they repair is drawn and
      accepted in a style, the repair for that style goes, and script
      and test when no style needs them. A list of them with the glyphs
      and styles each serves comes first (from make_bold's and
      make_italic's call order).
- [ ] T8. Checks in tiers, once T3 has CI green and trusted: the
      pre-commit hook a fast tier (ruff, UFO integrity, reproduction
      and tests of the styles the staged files touch), the full suite
      before push and in CI. Not before: today the hook is the only
      run that counts.
- [ ] T9. A status word per line in `tests/data/quality-*.txt`,
      `glyph-lint-*.txt`, `hint-zones*.txt` (about 2,100 entries):
      `designed`, `accepted`, `candidate`, before the free-text reason;
      `scripts/status.py` reports the open count per style and kind.
      With phase 6's verdicts, which fill it in.
- [x] T11. (built 2026-11-22: tools/git-hooks/rerun_plan.py, docs/claude/tests.md; pytest without -x) The hook re-checks baselines only: a commit whose tree
      differs from one that passed only in `tests/data/*` runs the
      baseline tests (quality, lint, accepted, golden shaping, digest,
      hint zones), not the whole suite and `make reproduce` again
      (2026-11-22: accepting baselines after `make test` made the hook
      run everything a second time, some 15 minutes a cycle). Before T8,
      and much smaller.
- [ ] T10. The records in order (DEVELOPMENT.md's publication items,
      phase 10): FONT-DESIGN.md back to open tasks only (done 2026-11-15: 529 -> 96
      lines, the history in FONTLOG's appendix); the dated proofs (185) now in `proofs/2026-10/` and `proofs/2026-11/`
      with `proofs/INDEX.md`, links updated (2026-11-15); still to do: the review
      documents (about 70 in `docs/`) into dated subfolders with an
      index, links updated; `build/` cleared of what no target makes
      any more, the agents' logs under one name.
- [ ] T11. Forms against the references, systematically (asked by the
      designer 2026-11-24, after Ɦ's hook was found curled the wrong way,
      right over the counter onto the right stem, where Charis, Noto Serif,
      DejaVu, Fira and our own italics curl it left). A tool,
      `scripts/quality/reference_sides.py`, that lists candidates for a
      sheet; the designer decides each one (the reference rule: Charis and
      Libertinus agreeing against Myia = change, with the memory's
      exceptions).
      Prototype (2026-11-24, build/pending/refside.py and its output
      refside.txt; re-made from this note if lost): each derived letter
      with a one-character base in data_regular.RECIPES (Ɦ from H), in
      Myia and in Charis, Libertinus and Noto Serif: the ink's growth past
      the base's ink box on each side (left/right over the base's width,
      top/bottom over its height; "grown" past 6 %), and the lean of its
      centre of mass (StatisticsPen meanX) against the base's, over the
      width. Flagged when all references that have the letter (two at
      least) grow on a side Myia does not, or the reverse, or all lean
      the other way. First run, Regular from fonts/otf (old Ɦ): 19
      candidates: bar/stroke ɉ ᵽ ⱦ Ⱦ (the references' bar or stroke
      reaches out right, Ⱦ's above), middle tilde ɫ ᵭ ᵮ ᵱ ᵲ ᵵ ᵳ (out to
      the left; ᵭ ᵱ ours out on the other side), Ɦ Ɠ (hook out right
      of G) ƈ (leans right), Ʝ (our tail far lower) ɬ ɞ, ₦ ₿ (lean left).
      Ɦ was caught on the right side for a muddy reason (Charis's Ɦ wider
      both ways): the box is coarse.
      To build: all four styles against the matching reference style; the
      small caps through the references' smcp; for letters without a
      recipe base (Greek, Cyrillic, symbols, the core set) a raster test,
      the glyph at 32x32 in its own box against each reference and its
      mirror image (flag where Myia matches every reference's mirror
      better than the reference itself), and the same upside down; a
      PDF sheet per candidate, Myia beside the references, large and
      filled. Then the candidates sorted with the designer: design
      (dated verdict, kept), or mended in the recipe.

### Tools the phases need (made in their phase, listed here to see them together)

- [x] Collision sweep over unkerned pairs, with its test: phase 1
      (2026-11-13).
- [x] Latin pairs test per style, as Greek and Cyrillic have: phase 3
      (the italics; 2026-11-12).
- [x] Italic kerning computed from the white the italic shapes leave:
      phase 3 (2026-11-12).
- [ ] The fitter that redraws an outline onto a given node structure:
      phase 5's pilot.
- [ ] Node-economy check for the core sets: a core letter's node count
      against its counterpart's (the Regular's; for the Bold Italic the
      Italic's), nodes off extremes and corners listed; a test with a
      list that only shrinks, once the first batch has passed: phase 5.
- [ ] Display-size sheets (72 and 144 pt, style beside its source, node
      views): T2's sheet, used in phases 5-8.

## Phases 5-8: the three other styles to the Regular's standard

Why they lag (measured 2026-11-10, nodes of a-z / A-Z): Regular 924 / 816;
Bold 922 / 816, the same count as the Regular in 51 of 52 letters; Italic
1410 / 1172; Bold Italic 1506 / 1247, the same count as the Italic in 18
of 52. The Bold has the Regular's structure and lacks a drawn bold's
decisions; the Italic's Old Standard outlines carry half as many nodes
again, and the kinks and unsmooth joins sit at those; the Bold Italic
inherits that and adds its own. Marked drawn today: Italic 12, Bold 24,
Bold Italic 53 glyphs, of a-z and A-Z two (Bold Italic).

The way: in each style the core set is drawn and kept (marked drawn,
accepted), the generators make the long tail from those final bases.
Core set, about 250 glyphs a style: a-z, A-Z, lining and old-style
figures, basic punctuation, the f-ligatures, Greek and Cyrillic lowercase
and capitals of the basic alphabets.

The gate for a core letter: nodes only at extremes and true corners, the
count within a few of the Regular's counterpart (where the design has
one); no entry in the style's quality list; accepted at 144 pt beside the
Regular and in words at text size.

Decided by the designer 2026-11-22: 0.900 waits for these phases, and
the font is proofed once, complete (phase 9 after phase 8). No one but
the designer uses it yet, so the reflow a redrawn core brings costs
nothing outside, and a printed proof made before 5-8 would have to be
read again. Two things are taken early instead: the Italic's colour
(phase 9's first step, as a small print sample, before phase 5 redraws
the Italic on a weight that might change) and phase 9's automated parts
(`make qa`, `make udhr`, the screen checks) run along the way, to catch
regressions while the styles are redrawn. (The earlier recommendation,
0.900 after phases 0-4 and 9, set aside.)

## Phase 5: the Italic's core set redrawn

Model: pilot and tool are F1; batches Sonnet by docs/claude/redraw.md, Opus where it refuses a letter.

Everything fixed here is fixed twice (the Bold Italic is made from it), so
it comes before any further hand work on the Bold Italic.

- [ ] Pilot (F1): n a e o s g redrawn to the gate (shape kept, nodes rebuilt:
      extremes, corners, one curve per quadrant where the Regular has
      one), on a sheet Old Standard | today | redrawn, with node views
      and at 144 and 12 pt. Go on only if the redrawn are preferred.
- [ ] Settle the tool on the pilot: a fitter that takes today's outline
      as the target and the Regular's node placement as the structure
      (as `scripts/pilot/strokes_fit.py` does for strokes), its output a
      candidate for the hand, not the result.
- [ ] Batches of about 20, by frequency: the rest of a-z; A-Z; figures
      and punctuation; Greek lowercase; Cyrillic lowercase; the
      capitals of both. Each batch: sheet, corrections, mark drawn
      (italicSource "drawn"), `accepted.py`.
- [ ] After each batch: `make generate` so the derived letters and small
      caps follow; `make reproduce`; `make diffenator`; delete the lines
      that fall away from quality-Italic.txt and quality-BoldItalic.txt;
      shaping baselines with the report's digest.
- [ ] Spacing kept: a redrawn letter keeps its advance and optical sides
      unless the review says otherwise (derived_spacing.py to check).

## Stems and bowls (the designer's two rules of 2026-11-10)

"A straight line of the same thickness from the top to the bottom in
the stem, in B, in D, in T, in all letters that have such a stem", no
stem stepping in where it meets the serif, "not in D, not ever"; and
"the insides of curves, e.g. in D, are not good. Redo this."
docs/claude/quality.md has both rules with what enforces them.

- [x] Stems. `scripts/stem_joins.py`: a join (curves between a serif's
      flat and a stem's edge) retreats when the outline goes more than 2
      units into the ink past the edge run on; `mend` redraws it as one
      fillet (sc_feet.fillets). Found 2026-11-10: Regular 0, Bold 0,
      Italic 12 glyphs (13 joins, to 10 units), Bold Italic 39 (57
      joins, to 27: ы.sc all eight, ᴅ, ɶ, oe.sc, the old-style 1 and
      4, A, d). Now the last-but-one finishing pass of the three
      generated styles; the two drawn Bold Italic glyphs (ʏ, Ҳ) mended
      where they are. All four styles at none
      (tests/test_stem_joins.py, no list).
- [x] Bowls. `scripts/bowl_counters.py`: a counter's run of curves
      between two level flats redone as two curves through its widest
      point, the handle lengths fitted to the run as it was, no handle
      further than 0.9 of the way to the corner. The last finishing
      pass of the Italic (43 glyphs, 1-6 units) and the Bold Italic (37,
      to 11); the drawn ones by name (Italic ɓ.sc ɗ.sc ʀ.sc; Bold
      Italic b.sc d.sc ƥ.sc ɓ.sc ɗ.sc ʀ.sc ʙ ꟈ.sc, to 10 units).
      A bowl's outside is redone the same way only where it is broken
      (a corner between two of its curves, a curve bending back): ы.sc's
      came to a point of 15 degrees at its widest, and the Italic's
      small-cap bowls (d.sc ᴅ ь.sc ъ.sc б.sc ѣ.sc p.sc þ.sc ф.sc, 17
      glyphs, 1.5-5 units) had corners where FontForge drafted them.
      Outsides that run smoothly into Old Standard's diagonal are left.
- [x] The designer's eye on both (approved 2026-11-10):
      `proofs/2026-11/bold-italic-stems-counters-2026-11-10.pdf`,
      `proofs/2026-11/italic-stems-counters-2026-11-10.pdf` (before | now,
      node views, overlay, 144 pt). To say there: whether the bowls
      are round enough (the shoulder's squareness is the 0.9), and
      whether the outsides that still run into a diagonal at the lower
      right as Old Standard's do (D, the Bold Italic's drawn d.sc) are
      to be made round as well. ы.sc's bowl overlaps the second stem
      by a few units at its widest, as before: a spacing matter.
- [ ] Left as they are, named by the tool: Д and д.sc (the counter no
      bowl: 27-53 units from any two curves). Not looked at: bowls with
      a corner at one end (B's two, P's and R's against the stem are
      taken only where both ends are flats), and the Regular and Bold
      (the tool would move the Regular's P by 3.6 units, the Bold's
      r.sc p.sc by 4-5: not asked for, not done).
- [ ] Where the stems' brackets are lost (derive.embolden moving an
      edge off its bracket, enlarge with `stems`, small_cap_stems) is
      not mended at the source: the pass repairs the result. Worth
      doing when T5 takes derive.py apart.
- [x] The acceptances and baselines, with F1's (2026-11-10).

## Phase 6: the Italic harmonised with the Regular, and its long tail

Model: Opus for the comparison and family faults, Sonnet for the lists.

- [ ] (Specified and measured: `docs/claude/italic.md`, 2026-11-15,
      `scripts/quality/italic_measures.py`; its first run's findings
      are there, nearly all of them the Regular's side. The sheet is
      Opus's, the choice among the five proposals the designer's;
      with them the question of the long stems, 2026-11-16: l t f and
      the ascenders and descenders an eighth lighter than n's stem, as
      Old Standard's, or brought to it.)
      The sheet built 2026-11-17 (`scripts/italic_sheet.py`,
      `proofs/2026-11/italic-against-regular-2026-11-17.pdf`): the
      measures unchanged since the first run. The designer's round
      the same day: all five proposals taken, and the long stems
      brought to n's, as one family across Latin, Greek and Cyrillic.
      The order of work (A balls, thin strokes, overshoots; B the
      bowls; C ascenders and long stems together; D what follows):
      `docs/claude/italic.md`, "The designer's round".
- [ ] A. r c balls, v w thin strokes (italic.md): candidates on
      proofs/2026-11/italic-harmonise-a-2026-11-17.pdf, for the
      designer; then install, generate, sweep, second sheet. The
      overshoots moved to C (a zone the whole Italic shares).
      Rebuilt on the Italic after B and C, approved and installed
      2026-11-26 (proofs/2026-11/italic-step-a-2026-11-26.pdf; r 819 ->
      804, c 808 -> 800, v w thinner, all four marked drawn). The
      followers mended (ɻ ɺ moved with ɹ's stem; the Bold Italic's ү on
      its own v, ұ smoothed: italic.md, "Step A installed"); sheet
      proofs/2026-11/italic-step-a-followers-2026-11-26.pdf. ɻ's tail
      straight-sided and its hook rounder in both italics (the
      designer's round; proofs/2026-11/bolditalic-rhook-round-2026-11-26.pdf).
      Left: ɺ's Italic kink, 3.4 degrees at 481,764: r's redrawn neck,
      turned, leans ɹ's stem below the cut 17.7 degrees against l's
      15.3, and no offset of l's top takes it (italic.md). Mended in r's
      neck (italic_harmonise.py's blend) or by a taper from ɹ's stem
      into l's, as ɻ's was; not visible at text sizes.
- [ ] The Bold Italic's `bar` family (docs/claude/longtail.md family 6:
      Ǥ ǥ ғ ө ᵽ ɍ ʢ ұ ꟈ, 15 lines; read 2026-11-26 on HEAD 3eb2cc78):
      not one cause. ɍ's 11-degree wobble at 323,810 sits on a run of
      short curves (334,787 -> 321,810) as ұ's did, which
      ITALIC_BOLD_SMOOTH_CURVES (derive.smooth_curves after the rebuild)
      mended: try ɍ there first. ǥ ꟈ ө have short curves, but not at
      their listed places (splits at extremes on the x-height and
      baseline); ᵽ ʢ have none. Render the nine at their places and
      sort the lines back to their recipes.
      Done 2026-11-26 (sheets proofs/2026-11/bolditalic-bar-family-,
      bolditalic-gbar-longer-, bolditalic-ue-descender-2026-11-26.pdf,
      approved): the one cause was that ɍ Ǥ ǥ ғ ө ꟈ were stroked whole
      from the Italic's barred letter; now the bar on the Bold Italic's
      own base (ITALIC_BOLD_REBUILD), ғ's bar join smoothed
      (ITALIC_BOLD_SMOOTH_CURVES), ǥ's bar 40 longer on the right (its
      own recipe, the designer). ұ's kink was ү's: ү's descender
      split-faired (ITALIC_BOLD_JOINS), p's foot serif 40 shorter on the
      right under ү (derive.descend's `shorten`, the designer). ʢ had no
      line left; ᵽ's 3-degree wobble is on p's own node, left. Left:
      ꟈ's 11-degree wobble (the union cuts d's curve into three 20-40
      unit curves, longer than smooth_curves merges); ү's 2.4-degree
      smooth at 523,496 (fair_joins redraws the glyph rounded in the
      upright frame: a handle moved a unit); the Bold Italic's p keeps
      its long right serif.
- [ ] The Italic's recipe singles, 2026-11-26 (families.py --style Italic
      --family recipe: 11 lines). Done (sheets
      proofs/2026-11/italic-J-crossed-tail-2026-11-26.pdf and
      italic-upsilon-curl-edges-2026-11-26.pdf, approved): Ʝ's stem line
      ended at -250 where its curl starts, not 12 past it (6.3-degree
      kink at 597,-262 gone); ʋ by derive.curl's new `edges` (each edge
      of the ring its own ellipse, tangent to its own edge of the stem:
      u's stem is 148 wide there and narrows upward, the recipe's
      120-unit ring started 14 inside each edge, the redraw pulled the
      stem in 4-6 and left a 4.5-degree kink; tried and refused: a split
      band 650-760 thickened the stem to 201, `dir` 85 left a 62-unit
      hairline spur, 88 small curves and a smooth). The other curls (Ɽ Ʈ
      ɦ ƴ ...) might take `edges` where their stems narrow: measure first.
      Left: ɮ's 3.2-degree kink at 335,600 and 1.2 at 237,260: the
      recipe's own stem is right (edge 304 -> 301 in the recipe frame,
      l's 301), but the final glyph's right edge stands 12-16 further in
      below 600 (288 at the foot, 286 at 250, 292 at 600), so a later
      pass trims it (the draft fit or the stem-to-serif pass: find which).
      ʛ (enlarge, 737,63 3.7 degrees) left: the family looked at
      2026-11-24. ɺ ɾ ʃ Ⱦ ʝ ƹ Ɦ: known, see above.
- [ ] B. The bowls of n o d p q (b a g h m u) and O wider (italic.md):
      scripts/italic_bowls.py, proofs/2026-11/italic-bowls-b-2026-11-17.pdf
      and its running-text page; approved and installed 2026-11-17 with
      C G Q D. Generated, followers placed (italic.md, "What
      followed"); the second sheet (the Bold Italic, the followers)
      approved 2026-11-18, baselines accepted. `redraw_sweep.py`,
      `make diffenator`, `make pairs`, italic_sheet.py run again
      2026-11-18 (sheet approved). Ø ø widened with O o, installed
      2026-11-18 (italic.md, "What followed"). Left, to phase 8: o.sc q.sc
      ø.sc widened with the Bold Italic's o.sc (italic.md; the script
      is `scripts/italic_round_sc.py`).
- [ ] C. The long stems measured across the three scripts, then
      weighted to n's stem, with the ascenders raised to the
      Regular's 4 % over the capitals and the overshoots set to the
      Regular's (lowercase -16, capitals -28 and 1462), in one install.
- [ ] D. The ligatures, derived letters and drawn Bold Italic glyphs
      on the moved bases; the Italic's ą ǫ ų Ǫ (ǭ Ǭ) not yet widened
      with a o u O, ď's caron and advance not moved with d (italic.md,
      "What followed"); the Italic's ø.sc (Ø's small cap) is kept as drawn beside the
      narrow o.sc (Ø ø themselves are done).
      Done 2026-11-21 (italic.md, "ſ and the f-ligatures"): ſ and the drawn
      f-ligatures raised and weighted as f was in step C, the Bold Italic's k
      on the new Italic k; a sweep of every glyph whose base moved in B or C
      while it did not (6eecb101^ against HEAD) found nothing else but marks
      below, which hang from anchors. The tail joins of ɭ ʈ ң ҷ and the cap-height
      curl of Ɓ Ɗ Ƥ, the joins of ƃ Ƈ Ɠ mended 2026-11-21
      (italic.md). Left of D: the derived letters'
      entries below.
      One sheet Regular beside Italic, measured and seen: ball terminals
      (c a f r y against the Regular's), serif length and thickness,
      hairlines, colour (about 5 % lighter) and width (about 5 %
      narrower), x-height overshoots. What reads as another typeface is
      changed in the core set; the italic capitals' contrast stays
      (declined 2026-10-21, 2026-11-02).
- [ ] The derived letters, once their bases are final: the kink, smooth
      and extreme entries left in quality-Italic.txt, by family (a
      recipe's fault in the recipe, a letter's in the letter).
      `superior` smooth done 2026-11-22 (italic.md, "The superiors
      rounded smoothly"): 9 lines gone; the Bold Italic's ʷ ᵒ ᵘ ᶶ ⁿ, stroked from them, refitted (no finding, ʷ ᵒ ±1). Left
      (families.py --style Italic --family recipe): `attach` kink 6 (ɭ ɰ
      ʈ Ɽ Ⱳ Ꞵ, Ɽ's 7.4 degrees the largest), `attach` step 5 (ƃ ɖ ɧ ɳ
      ʝ), and singles by recipe (Sonnet).
      The Regular's `enlarge` family looked at 2026-11-24 (039bd942): no
      fault shared in the operation itself; ɢ ʛ's smooth node at 710,23
      (2.6 degrees, from enlarge's scaling of g.sc's 0.6) made smooth in
      the Regular's glyphs by smooth_joins.align (not in JOINS: that list
      runs on the Bold Italic only), Bold follows; 251 -> 249 lines. Left
      of the family: ɢ ʛ's step at 701,304 (design), and the lines that
      are the bases' own (Ɛ ɣ ɩ ɤ ʊ: one-letter faults, kinks and
      strokes of the 2026-10-16 start list). only_glyph.generate now
      applies ITALIC_JOINS/ITALIC_BOLD_JOINS/RUNS/CORNERS as rederive
      does (the Ƈ Ɠ test failed on a fresh frame dump without it).
      The t-bar sweep (diffenator + pairs, 2026-11-24, against 3b88d906,
      mixed with 23 later commits): t-family as expected in all four. The
      t-bar commit alone (c461b1de against its parent, by the sources): only
      t, its ligatures (c_t f_t f_f_t longs_t longs_longs_t s_t t_h t_t),
      ƭ ʈ ᵵ ṫ ⱦ and, in the Bold Italic, tcaron tcommaaccent ț ṭ ṱ ẗ and s_p
      (advance +1, an outline change: looked at when the Bold Italic's
      ligatures are next; not the t-bar's design); Italic and Bold Italic
      kerning.plist (19 and 168 values: the t pairs, and the Greek group
      pair sigma-mugreek -21 -> -22, the whole of σμ -1). ʐm +11/+14 is
      ʐ's advance (Italic 785->796, Bold 775->789; no kern pair in either);
      the Bold Italic's GDEF carets (+1..+4) follow its ligatures' advances.
      The Regular's `attach` family done 2026-11-24
      (`scripts/regular_attach.py`, sheet
      proofs/2026-11/regular-attach-2026-11-24.pdf, approved): no shared
      cause, a node each. Ʈ and ⁂ made again (Ʈ's ball by today's curl;
      ⁂ from the asterisk, whose four 2.3-degree seams were aligned), Ɲ's
      tail top moved onto N's edge lines, the rest smooth_joins.align
      (ʑ Ʝ ɮ Ϗ ɞ ʐ, Ʈ's stem into the curl); ɲ.sc ʝ.sc ϗ.sc, enlarged from
      Ɲ Ʝ Ϗ, made again on them (ɲ.sc ʝ.sc clean, ϗ.sc 3 lines to 2: a
      1.9-degree join of two lines at 677,541 and 935,-293's 2.6, which
      align does not move); ʐ's kerning against b h k l 24 -> 26
      (check-regular's kern step, its tail moved). Lines: Regular 18 gone,
      2 new (count keys); Bold 4 gone, 3 new; Italic 1 gone; Bold Italic 1
      and 1. The Bold's ʝ.sc: its smooth 2.5 at 111,-377 now a kink 3.8
      (113,-377; width 900 -> 904): the Regular's join there is now in
      line, the emboldening turns line and handle apart (HEAD's 1.7 off
      the other way hid it); left for phase 7. Re-deriving alone (a scratch
      run) mended only Ʈ's ball. Left: ɮ 828,540 (1.0, two lines), the
      steps of ɝ ₹ Ɑ (design), ɞ's zone and base lines. **ɮ's recipe is
      stale**: run again, it sets ʒ apart from the l (ʒ moved since); the
      kept glyph is right, the recipe to be brought to it before ɮ is
      ever made again.
      The Regular's `hook` family done 2026-11-24
      (`scripts/regular_hook.py`, sheets proofs/2026-11/regular-hook-2026-11-24.pdf
      and H-hook-left-trial-2026-11-24.pdf, approved): two shared causes,
      mended in the kept glyphs (ɓ ɗ ƙ ɦ ɧ no longer match their recipes:
      ɓ re-derived would be 1865 wide, not 1110). The join: hook_path takes
      the hook from f above 954, where f's straight stem ends, a 2.1-3.2
      degree corner on the stem (ɓ ɗ ƙ ɦ ɧ ɖ); f's 22-unit handles at
      648,1334 (1.2 degrees by rounding) scaled to 2.4 (Ɓ Ɗ Ƥ Ƒ). Ɦ turned
      the other way (the designer): its hook curled right onto the right
      stem and read "HA"; every reference and our italics curl it left; now
      Ɗ's recipe, the serif's right half kept (advance 1540 -> 1880, ɦ.sc
      1161 -> 1430). Quality: 8 lines gone, 7 hidden corners mended.
      Found on the way: **checks.construction skips a node beside a
      duplicate** (a zero-length line, `if not la or not lb`): 7 corners
      in the Regular's hook letters were hidden so, 3 more elsewhere
      (Italic ƙ 611,207 1.5; Bold Italic ж.sc 1185,321 smooth 2.6, ө.sc
      807,800 smooth 4.8). Collapse duplicates in the check (new lines,
      dated), or glyph_lint flags duplicates.
      Left in the Bold, the next batch (not approved 2026-11-24): the
      Bold's Ɦ ɦ.sc keep their drawn marks of 2026-11-07 (an aperture
      repair for the old right-curling hook), so they still curl right.
      Made from the new Regular (marks released, build/pending/bold-H-hook-left.pdf)
      the designer saw two faults, both of the Bold's hook family, not of
      Ɦ: (1) the inner curve: the Bold f's neck under its ball has a handle
      38 units past it (703,1456; the Regular's 646,1464), f's listed wobble
      663,1365 and extreme 665,1383, carried by rederive into Ɓ Ɗ Ƥ Ɦ ɓ ɗ ƙ
      ɦ ɧ ƥ.sc (their wobble and extreme lines): mend the Bold f's neck by
      hand (drawn), sheet of the whole family; (2) the stem not straight:
      f's stem widening into its top, mirrored, leans the stem's outer edge
      out from y 1000 (627 -> 572 by 1300; the Regular 634 -> 540, seen and
      approved there): keep the stem's edge straight up to where the hook
      turns, as make_italic.straight_stem for ɾ, on Ɓ Ɗ Ƥ Ɦ alike. Then
      release the two marks and generate. Also open: hook_path itself
      starting the piece no higher than f's straight top (the Bold's ɓ ɗ ɦ
      join kinks of 3.7-5.2 degrees, made by rederive; it changes the
      italics' hooks too: its own trial).
      Done 2026-11-24 (sheet proofs/2026-11/bold-hook-neck-stem-2026-11-24.pdf,
      approved by the designer): (1) the neck, in f, longs and ʃ alike
      (each emboldened on its own, the same fault), by hand
      (`scripts/bold_neck.py`, drawn): the node at the ball's side 5
      left, the arch's inner top at the Regular's share (621 -> 602), its
      handles at the Regular's shares; extreme and wobble gone, carried
      into the f/ſ ligatures and the hook letters. (2) the stem: make_bold
      straight_hook_stem, data_bold.BOLD_STRAIGHT_HOOK (Ɓ Ɗ Ƥ Ɦ straight to
      1100; 1050 and 1150 shown, the designer saw no difference in weight
      and took the middle). Ɦ ɦ.sc released (hook left, from the Regular).
      Found in the generate: ƥ.sc ɦ.sc, emboldened from the Regular's,
      brought the neck fault back (ɦ.sc 13 past): now enlarged from the
      Bold's Ƥ Ɦ (BOLD_REBUILD), ƥ.sc left with a 2.7-degree smooth at
      930,970 (a 23-unit handle's rounding, listed); f_b f_h f_k and their
      ff/ſ/ſſ forms: draft_ligatures.f_ligature cut the letter in at 1250,
      above fl's straight stem (1168): a 1.9-degree corner, 2.4 with the
      rounder arch; the Bold's now cut at FL_ARCH in_foot. Left: f.short's
      own smaller neck wobble (562,1398; a reviewed draft). hook_path
      starting no higher than f's straight top (the Bold's ɓ ɗ ɦ joins)
      still open.
      The Regular's `curl` family done 2026-11-24 (`scripts/regular_curl.py`,
      sheet proofs/2026-11/regular-curl-2026-11-24.pdf, approved): one
      shared cause, mended in the kept glyphs. On a diagonal stroke the
      ring meets edges not parallel to `dir`: the outer join's first
      handle 2-5 degrees off the edge line (Ƙ Ƴ ƴ Ⱳ ⱳ, Ƴ's a corner of
      4.8), the inner join crumbs of 4-13 units turning 10-27 degrees,
      hidden from checks.construction by their shortness (Ƴ ƴ Ⱳ ⱳ), and
      on Ƙ a 14-unit notch on the arm's upper edge (the ring starting 10
      inside it). Handles put in line, crumbs dropped, Ƙ's ring start
      moved onto the arm's line. ʋ's stem edge bent in 3 units below 60:
      straight at 926. ƙ.sc ƴ.sc ⱳ.sc made again. Scratch: Regular 7
      lines gone (with ƴ.sc's 3.6 kink), none new. derive.curl itself
      unchanged: a recipe made again would bring the joins back (the
      italics' curls are their recipes', not touched). Like the
      duplicates above, **checks.construction does not see corners
      between segments under about 12 units**. ⱳ.sc made again came out
      with a 3.1-degree corner beside its ball (1725,837, an 11-unit
      handle: hidden in the Regular, a wobble in the Bold): aligned in
      the script's small-caps step.
      The Bold: Ƴ followed (its 5.0 kink gone, with ƴ.sc's 3.5); its ƴ ʋ
      are drawn, its Ƙ Ⱳ ⱳ made by the Bold's own curl recipes: the same
      join faults there (Ƙ 1401,1111, Ⱳ 1943,1120, ⱳ 1318,700 and
      1671,715), for phase 7.
      Left of the family, older and also hidden (short segments): where
      the ball meets the ring's outer edge, 3-5 degree corners on Ƙ
      (1329,1111), ƴ (1164,714), ⱳ (1591,714), ƴ.sc (1163,807): their
      balls are from before derive.curl put the ball on the edge's normal
      (2026-11-22). Made again on today's curl (as Ʈ was) they would
      lose them but bring back the joins mended here: re-derive, then
      regular_curl.py on the new coordinates, on a sheet. ʋ's own ball
      (drawn 2026-10-27) has corners of 8-14 degrees at 550,661 and
      410,727-418,742: a look by the designer first.
      Next of the Regular's operations: see families.py (`ezh`, `bar`,
      `superior`, `stretch`).
      The joins batch done 2026-11-22 (italic.md, "The recipe joins"):
      ɭ ʈ Ⱳ Ꞵ ƃ ɳ ɧ ɖ. Left: ɰ (ɥ's descender 2.3 degrees past the slant:
      set it at the slant, then fair), Ɽ Ʈ ɖ's curl balls (derive.curl
      places the ball on the ring's parametric angle, not the outer edge's
      normal: a 4-7 degree corner with unequal radii in every style; a
      shared change, `make regress` and `make diffenator` first, or left),
      ɱ's ledge (made by `hook`, which has no taper), ʝ designed (its
      crossbar's square end), ɧ's 271,955 from ɦ.
- [x] (2026-11-24, scripts/regular_signs.py) ! looked much fatter and
      darker than ?, ¡ than ¿ (the designer). ink(!)/ink(?) is 0.72-0.88 in
      every reference and 0.78/0.77 in our italics (their signs from Old
      Standard, 2026-11-16); the Regular had 1.04, the Bold 1.08: Theano's
      ? a round head on a hairline stem (239k against the Didots'
      281-332k). Option B of build/pending/exclam-question-options-2026-11-24.pdf
      chosen (proofs/2026-11/exclam-question-B-2026-11-24.pdf): ! ? ¡ ¿
      from Old Standard Regular's OTF, scaled to the cap height (2.014),
      its side bearings and own ¡ ¿, turned to the Regular's clockwise
      contours, redrawn onto clean nodes (redraw.py, dev 2.5-3.0); ratio
      0.75. Their kerning is kern_clear's own (undone and measured again).
- [x] (2026-11-24, same batch) ʔ made on the new ?: by `nodot` it ended
      in Old Standard's teardrop. Now derive.glottal_stem: the ?'s head
      lifted to O's top (every reference's ʔ reaches its H or above; ɂ
      ɂ.sc then on their zones), cut where the stroke heads down, a neck
      of two curves continuing its edges into a straight stem; in the
      Regular ı's stem and foot serif (Charis, Libertinus, Noto Serif,
      DejaVu, Cambria have one), in the Italic a plain stem at the same
      weight (164, was 112; the designer: no serif in the italic), the
      Bold from its own ? and ı (BOLD_REBUILD). Followers made again: Ɂ ʕ
      ʡ ʢ ɂ ɂ.sc ˀ ˁ; ˀ now from ʔ as ˁ from ʕ (from ɂ it stood at 1149
      against ˁ's 1469). The foot serifs (the designer asked whether they
      are of one kind): the Regular's are flat hairline slabs, one size per
      kind (capitals 592 wide, 192 over, 53 thick; lowercase 448, 142, 49;
      small caps 398, 117, 48; superiors 273, 79, 37); ʔ ʕ ʡ ʢ have the
      lowercase's and ˀ the superiors' to the unit; ɂ ɂ.sc, scaled from
      ʔ, had 85 and 103 over and lighter stems: now ʔ's head scaled and
      seated on ı's and ɪ's own stem and serif (glottal with enlarge). Sheets: proofs/2026-11/glottal-serif-trial-2026-11-24.pdf,
      proofs/2026-11/glottal-batch-2026-11-24.pdf (approved but ʢ, whose
      stem the bar interrupted: the contour direction, below).
- [x] Contour direction: nothing checks it. The Regular winds every glyph
      clockwise; Old Standard's CFF outlines wind the other way, and the
      new ? took that direction until ʡ ʢ's bar, merged across ʔ's stem
      (derive.merged: one path, nonzero winding), cancelled against it and
      left a hole (2026-11-24, mended in regular_signs.py). The generated
      styles already hold glyphs winding counter-clockwise (2026-11-24,
      before this batch): Italic 20 (the old-style figures, n.sc s.sc ɴ
      ...), Bold 73 (ƃ Ɔ Ǝ ƛ Ɯ Ɲ Ʈ Ʊ Ƹ ƹ ǝ ...), Bold Italic 90. One cause
      found: make_bold's TRANSFORMS (a mirrored letter moved from its
      Bold base: ʕ Ɔ Ǝ ...) mirror the base without turning its contours
      (the Bold's and Bold Italic's ʕ wind counter-clockwise; the Bold
      Italic's ʢ, its bar merged across that ʕ, had a hole). For the
      batch, derive.merged turns a piece that winds against its letter
      (no change where they agree).
      Done 2026-11-24: `scripts/winding.py` (the check, each contour by
      its depth; tests/test_winding.py, every style) and its orient(),
      called last before saving in make_bold.write (the Italic's writer
      too) and smallcaps. The second cause, the larger: pathops' simplify
      and op return counter-clockwise outers by default, so every
      pathops result saved without draw_path's turn wound the other way
      (Ⱥ Ȼ ∅ ⊗ ฿ ...; Bold ʝ and Bold Italic ɨ ᶤ wound both ways, the
      body made, the dot kept). One place for all, not each site turned.
      Side effect: the Bold Italic, stroked from Italic glyphs now wound
      clockwise, came out a few units otherwise (the old-style figures,
      s.sc, ϟ.sc, є.sc); ж ж.loclBGR җ worse (the middle stem narrowing
      into its foot): kept as at 522505e2, turned, and marked drawn.
- [x] (2026-11-25: lines meeting straight one edge, a6395703; ж ж.loclBGR
      җ released, stroked with an even middle stem, approved on
      proofs/2026-11/zhe-released-2026-11-25.pdf; the rest below.)
      The Bold Italic's stroker depends on contour direction: the same
      Italic letter wound the other way strokes a few units otherwise
      (its passes walk the contour in order: crotches, rigid, one_way,
      blend). Now that every input winds clockwise this no longer varies
      between runs, but ж's middle stem (wound clockwise) narrows into its
      foot. Find the pass that does it; then release ж ж.loclBGR җ
      (drawn.py --release) in the Bold Italic.
      **In progress (2026-11-24 night, uncommitted in the working copy:
      scripts/stroke_bold.py; `make generate` run, log build/gen_edges.log).**
      Found: stage i, the node positions. A node between two lines turning
      under CORNER (28) was moved by the leaving line's weight, so the
      arriving line became a wedge, which one by the contour's direction.
      ж: its middle stem's left edge is two lines 0.4 degrees apart at
      595,36 (a 36-unit line at the foot): as wound now a flare 221 -> 230
      at the foot, reversed (the saved ж) a taper 232 -> 220. Fairing,
      one_way, blend play no part. Change: `edges()` and EDGE_TURN 3:
      lines under 3 degrees are one edge, one weight (samples' mean);
      turning more, each line parallel by its own weight, the node where
      they cross (mitre), unless the crossing takes more than EDGE_KEEP
      0.5 of either line (it would fold: λ), then the two weights' mean.
      Scratch trial (scratchpad edge_trial.py, against the old module):
      ж even 222 -> 220; W's thin diagonal no longer a wedge thickening into
      its serif (today up to ~25 units at its top); λ's thick diagonal less
      thinned at its top (mean at the guarded node); Z ʈ small; Y ф ү n h o
      unchanged. Sheet for the designer:
      build/pending/bolditalic-line-edges-trial-2026-11-24.pdf (Italic |
      today | new; W and λ were approved as they are on 2026-11-20: the
      designer decides). Next: what moved in the generate (git diff
      --stat sources/, `make diffenator`, the Bold Italic counts before |
      after as docs/claude/stroking.md "How to test a change"), a sheet of
      every letter that moved, then the designer; ж ж.loclBGR җ released
      only after (still marked drawn, so the generate keeps them). Also
      add a test (tests/test_stroke_steps.py): ж's stem stroked both
      ways the same, edges() on a toy contour.
      Generated 2026-11-25 (exit 0; only ɂ's known recipe failure): the
      Bold Italic alone moved, 35 glyphs and kerning.plist: W Z ʒ ƛ Ɲ ǆ.sc
      ǳ.sc ɭ ɮ ɲ.sc ɺ ɻ ʃ я җ.sc қ.sc ү ұ ᵘ ᶶ ẑ.sc ẓ.sc ẕ.sc ₡ ₩ ₹ Ɀ ⱳ.sc
      Ʞ w.sc z.sc ź.sc ž.sc ż.sc ζ (uni1D52D, uni1D58, uni1DB6: see
      the names). λ and ʈ not among them (drawn or rebuilt in this style).
      Left after it: n h o ф still differ by direction by 785-3260 units²
      of area (another stage, likely the sampling along each segment from
      its start node, as the wobble check had).
      Checked 2026-11-25: `make reproduce` clean; stroke tests pass, with
      two new ones in tests/test_stroke_steps.py (edges() on a toy
      contour; ж W Z stroked from the Italic either way differ at most
      1000/1650/250 units², was 3194/13185/1236: a ratchet, only shrinks).
      Counts before | after (Bold Italic): kink 79|80 (gone ɻ 2, Ʝ;
      new ү ұ ᵘ ᶶ, 1.0-2.5 degrees), wobble 138|139 (new я 623,265 5 deg;
      ұ's two became one at 178,-375 49 deg), smooth 58|56 (ұ's two gone),
      extreme, step, corners, lint, strokes unchanged; g2 jumps 1092|1090
      (ɻ's 32 gone). Largest moves: W Ⱳ 52 (the thin diagonal's top now
      turns at 1047,1190 into its bracket), ɮ 75 (handles), ₡ 43,
      z.sc and its composites 25 (the diagonal's foot node). Sheet of all
      35: build/pending/bolditalic-line-edges-moved-2026-11-25.pdf
      (Italic | HEAD | new, zoom on the nodes moved). Waiting for the
      designer; ұ's 49-degree wobble and я's new one to look at first.
      Not run: make diffenator (git diff of sources/ already lists all
      that moved: the Bold Italic's 35 glyphs and 2 kerning pairs).
      Designer 2026-11-25: all approved but ɻ, "a big step in the downward
      stroke": the Italic's too (ɹ's stem flares into its bowl, 50 wider
      than the tail at the cut). Mended in data_italic's ɻ recipe: a left
      "taper" piece. Generated with it (only ɻ moved in the Italic; the
      Bold Italic the same 35 and „ɻ's kern dropped); ɻ Bold Italic: kinks
      3.7+2.1 -> 1.2 deg, a new smooth 2.5 deg at 485,-136 (tail into
      curl). Sheet build/pending/rhook-taper-2026-11-25.pdf; then
      baselines, commit, release ж ж.loclBGR җ.
- [ ] (Shelved 2026-11-25 with the designer: every glyph winds the same
      way since 2026-11-24, so the direction does not vary between runs;
      ᵽ's descender, the rejoin guard's wobble family and the phase 6/7
      letters first. Taken up again only if the tipping points below cost
      time in other work.)
      The Bold Italic's stroker still depends on contour direction off
      lines: n h o stroked from the Italic wound the other way differ by
      3259/1814/785 units² (ж W Z, the lines, by 959/1584/226 now;
      tests/test_stroke_steps.py test_stroked_the_same_either_way holds
      those). Likely the sampling along each segment from its start node
      (as the wobble check had). Measure with the scratch trial (stroke a
      glyph and its reverse, XOR area) per stage before changing any.
      Found 2026-11-25 (not the sampling: the samples are the same points
      either way; every cause is a node's own sample taken by one side):
      A one_way walked back started a sample into the curve (`aside`
      carried the 2-unit step); B a node turning under CORNER offset on
      the leaving segment's normal (Italic o 231,8, an 8-degree corner no
      list names); C a crotch's leaving side weighed by the node's sample,
      crossing() one sample short on it; D a line's mean took its start
      node's sample; E the crotch's sample smoothed with the leaving run
      only; F rigid/crotches gated on sample tangents (W's left bracket
      0.991 | 1.005 of its limit: 22 units); G join_curvature node by node
      and fit_g2's start order. A-F with E for every corner (sample out of
      smoothing and cap) and G: n 10.2 -> 0.6 units, W 22 -> 0.25, m 3.7 ->
      0.8, ж 2.9 -> 0.25, o 1.1 -> 0.26 apart by direction; y 2.5 left, its
      blend gate flipping (steps() and findings() read by direction).
      Kept aside (git stash "stroker direction fixes A-F", patch
      build/pending/stroker-direction-AF.patch; with E for every corner and
      G: stroker-direction-full.patch): they moved 1495 glyphs,
      π 92 ı 47 by D's 0.001 change of weight tipping rejoined (below) and
      fair_arcs' LIMIT. Next, after the rejoin guard: apply A-F, scratch
      run, list moves (they should be fractions now), sheet; then G.
      Tried 2026-11-25 on the guard (stash "stroker direction fixes A-F on
      the rejoin guard", build/pending/stroker-direction-AF-on-guard.patch;
      the test's ratchet line there still says PENDING): W 20.6 -> 0.59
      units, n 10.2 -> 0.88 by direction, but still 1480 glyphs moved, 65
      by 10+. Tipping points found and mended (committed): ᵽ's union with
      p (a shared counter came out of no area, the cleaning dropped it:
      make_bold.gained) and sc_clearance.psi's splice (cut ψ.sc's left
      arm on an outline stroked a little otherwise: LOST_MAX). Left: ı and
      its family (the cleaning's node structure, 49 | 52 points, so the
      fairing fits other nodes: 5442 units² from 35 before fairing), и
      (the blend gate's `guarded` flips: "swollen 289 -> 568"), and the
      rest of the 65 (ᵽ 272 was the union, ψ.sc 440 the splice).
- [x] (2026-11-25) rejoined merged the cleaning's pieces into one cubic
      unchecked: π's left leg 91 units off what was stroked (a straight
      wedge for the Italic's curved foot), д.sc 39, į 34, and a node's
      anchor 0.02 units further flipped it. REJOIN_ERR 2: a run is merged
      only within 2 units of its pieces, else cut at its middle and each
      half tried. Bold Italic: 439 glyphs moved (40 by 10+ units), sheet
      build/pending/bolditalic-rejoin-guard-2026-11-25.pdf; the designer
      chose this (option 1) over a 12-unit guard for the gross ones only.
      Quality: 20 lines gone (t.sc kink and smooth, ʈ.sc ⱦ.sc ꟈ kinks, π
      extreme, 12 wobbles), 37 new: the merge had smoothed over small
      bends in the stroked pieces. The joins blend asks for (its short
      curves, `asked`) are merged as before (else м's step came back).
      ө.sc's bar union needed wider nudges (make_bold, ±0.4 x, ±0.6 y).
      test_stroked_the_same_either_way now measures the largest distance
      in units (XOR read ж 9866 units² for 0.97 units).
- [x] Bold Italic ᵽ's descender (designer, 2026-11-25, on
      proofs/2026-11/bolditalic-p-bar-bowl-2026-11-25.pdf): the foot serif
      does not look good (its left bracket gone, a flat corner where p has
      a round one), a knee on the stem's left edge just above the serif,
      and the bar not centred on the stem (longer to the left). All three
      in HEAD's too; the Bold Italic's p is clean, so it is ᵽ's making:
      the bar low (Regular recipe ("ᵽ", "bar", "p", ("x", -290)), as
      sloped in the Italic) comes so near the foot serif at this weight
      that the union with p loses the bracket. Look at the Italic's ᵽ as
      well (its bar also longer left); then the bar's height and centre
      in the recipe or the italic's band, ᵽ.sc alike; sheet.
      (2026-11-26: the bracket and the knee mended, not by the bar: the
      bracket is drawn by stem_joins at finalize, which took a stem's
      edge only as one line STEM 200 long, and ᵽ's below the bar is 45;
      a stem cut by a bar now counts (stem_joins._through_bar), ᵽ's
      foot is p's, Ң mended alike; sheet
      proofs/2026-11/bolditalic-barred-stem-feet-2026-11-26.pdf.
      Left for the designer: the centre. Along the bar, from the stem's
      edges at the same height, the Bold Italic's is 143 left, 154
      right; the Italic's 168 | 168 (the Regular's 142 | 168, cut at p's
      ink on the left). Against the foot serif, which stands out further
      right than left, the bar's centre is 19 units left of the serif's
      (Italic 17): the likely "longer to the left". Move the bar right
      to the serif's centre, or keep it on the stem? ᵽ.sc not measured
      (its bar on the bowl, at 260). ұ (uni04B1) loses ү's left foot
      bracket the same way but is not mended by this: its stem's edge
      above the bar stands 5 units out of line with the edge below (a
      step at the bar itself); see ұ apart.)
      (Done 2026-11-26, the designer: move the bar. The Italic's recipe
      centres it over the serif, (150, 185) out; the Bold Italic's ᵽ and
      ұ are their bar on the finished p and ү (ITALIC_BOLD_REBUILD), as
      ʉ ɉ: ᵽ joined to p had its bowl's curve split by the union (a
      2.5-degree kink), ұ stroked whole its step at the bar. stem_joins
      reads a barred edge's pieces against their chord (ұ's 90 and 136
      units, a degree apart by rounding): ұ.sc and the superior 4 mended
      with it. Sheet
      proofs/2026-11/bolditalic-p-bar-centred-u-bar-feet-2026-11-26.pdf.
      The upright ᵽ left as it is, its bar 142 | 168.)
- [x] (2026-11-26: not in the pieces: the guard itself. apart's fixed
      sample counts left gaps of 8-13 units on a long curve and read
      sound merges as strays (α's, 0.7 units off, as 6.7), so the
      cleaning's cuts at inflections and extremes were kept and fair_arcs
      bent the curve there. rejoined now measures with strays, about one
      unit between samples, point to polyline; REJOIN_ERR 2 still refuses
      π's 91 and д.sc's 38. 35 of the guard's 36 quality lines gone, 178
      glyphs moved, n.sc ɴ's left foot on the Italic's diagonal again, ɶ
      ƭ.sc cleaner; new lines in ꟈ ʞ.sc ө.sc җ.sc ſh ﬀb n.sc ʽ я ᵳ; ж
      stroked 2.93 units apart by direction, as with no guard. ʝ's tail
      bar run on 90 to the right in the same batch. Sheets
      proofs/2026-11/bolditalic-rejoin-dense-2026-11-26.pdf,
      bolditalic-jcrossedtail-2026-11-26.pdf. Left: ʲ's and ч's wobbles,
      in the stroked pieces.)
      The 25 wobbles (4-6 degrees) and 9 smooth lines the rejoin guard
      showed in the Bold Italic (α ψ ɐ ʈ.sc Ʊ м ф ч щ ʔ ʕ ɶ џ ɦ @ ...,
      quality-BoldItalic.txt dated 2026-11-25): bends in the stroked
      pieces themselves, one family; find the stage that makes them (the
      pieces before the cleaning, then fair_arcs) and mend it there.
- [x] (2026-11-24: each contour read clockwise, by its area, and its
      lobes grouped round from a break or a change of sign;
      tests/test_quality.py test_wobbles_read_either_way. All four styles:
      the same findings with every contour reversed or begun elsewhere.
      Bold +ɮ ѳ.sc ∅ ⸎, -a ą ɐ ʉ; Bold Italic +‛ u.sc.horn ә.sc Ө ө, -ß ᵃ;
      ѳ.sc ∅ u.sc.horn Ө were missed either way, their lobe split at the
      start; the gone ones were 3.1-4.9 degrees, one way only)
      The wobble check depends on contour direction
      (scripts/quality/checks.py, reversals): it samples a contour at
      fixed steps from its start, in its direction, and groups the turns
      into lobes without wrapping round, so the same outline read
      backwards finds other wobbles near the thresholds (2026-11-24: the
      Bold's quality list gained 6 wobbles and lost 1 with only its
      directions turned; HEAD's Bold Italic 7 read backwards had two).
      Make it the same either way (e.g. sample from a fixed point, wrap
      the lobes round, or take both directions), then accept the lists
      once with that as the reason.
- [x] (2026-11-25: ɂ's own Italic band; the Bold Italic's kept whole as
      ʔ, approved) make_italic prints "recipe failed: ɂ (glottal): glottal_stem:
      uni0294 crosses 967 4 times, not 2" (make generate, 2026-11-24,
      after 522505e2); the Italic's ɂ stays as saved. Find why the
      Italic ʔ is crossed four times at 967 (the head's cut height) and
      make the recipe run again.
      Found 2026-11-25: not ʔ's shape. make_italic.build_own took every
      `glottal` op as the Italic's ʔ (ITALIC_GLOTTAL on its source), so
      the Regular's new ɂ recipe ran ʔ's cut on ʔ itself. Now build_own
      leaves a banded glottal to derive.build, and data_italic gives ɂ
      its own band (ITALIC_GLOTTAL_SMALL: ʔ scaled to o, its head lifted
      to 884, a plain stem of 164 as ʔ's, no serif). The committed ɂ was
      still the sloped Regular's, with ı's foot serif. `make only`:
      checks and lint clean, 22 nodes to 15. Sheet
      build/pending/italic-glottal-small-2026-11-25.pdf, approved by the
      designer. Generated: only ɂ moved (Italic 645 -> 644, Bold Italic
      715 -> 720). The Bold Italic's rebuild from its own ʔ strays (the
      band's stem is the Italic's 164): kept whole as its ʔ
      (ITALIC_BOLD_KEEP_WHOLE, one line more in emboldened-whole,
      accepted by the designer). Open: a Bold Italic band for ɂ (and ʔ)
      at its own stem weight, to build both from the Bold Italic's ?.
- [ ] Design entries (W's diagonals, i/j dot gaps, ξ, 7) get a dated
      verdict in the list, so what remains are all real candidates.
- [ ] Zone and slant entries (123 and 66): sorted into families first; a
      family fault goes into the generator, single letters wait.
      (Sorted 2026-11-15: `docs/claude/longtail.md`, family 5's
      clusters; the same page for the kinks and smooth entries above.)

## Phase 7: the Bold's core set finished by hand

Model: the analysis is F4; Opus for family rules in make_bold, Sonnet for batches.

Its outlines are the Regular's, moved: the work is the decisions, not the
nodes. Old Standard Bold (`make oldstand`) is Kryukov's own emboldening
and the calibrated reference; the Regular's node structure is kept, so
the Bold stays point for point comparable.

- [ ] Sheet Regular | Bold | Old Standard Bold for the core set, and
      measure per letter: counter area, aperture, join thickness where
      arches and bowls meet stems, ball size, width gain (rounds against
      straights).
- [ ] Pilot on a e s g n o: counters and apertures opened, joins
      thinned, balls in proportion; review at 144 and 12 pt against
      today's.
- [ ] If a correction recurs in a family (all arch joins, all balls), it
      goes into make_bold as a rule for that family; what is one
      letter's stays a hand fix marked drawn.
- [ ] Batches as in phase 5; then the long tail: wobbles (134) and kinks
      (78) by family, the 11 letters still emboldened whole
      (`emboldened-whole-Bold.txt`) each a recipe at the Bold's weight
      or a recorded decision.
- [ ] Marked "to review" in FONT-DESIGN.md: the hooks' inner corners
      after stem_handles (J ȷ ɽ ɳ Œ), the middle tildes' weight.

## Phase 8: the Bold Italic

Model: Opus by F3's map and F4's measures; Sonnet for batches and the drawn glyphs' comparison.

No further hand fixes before phase 5 is through: a glyph marked drawn
does not follow the Italic, so each would be redone.

- [ ] Before phase 5 changes the Italic: list the 53 drawn Bold Italic
      glyphs with what was fixed in each (FONTLOG, the review documents),
      so each can be judged again against its regenerated version.
- [ ] After each phase-5 batch: regenerate, and compare stroked-from-
      clean against today's on a sheet; checks.py counts (wobble, kink,
      smooth) per batch, to see what the clean input alone gives.
- [ ] For each drawn glyph whose Italic base changed: regenerated beside
      drawn; keep the better, redo the fix on the new outline if still
      needed, or drop the mark.
- [ ] What the Bold decided in phase 7 carried over as measures, not
      outlines: counter and aperture gain, join thinning, ball size,
      width gain, set as the stroking's parameters or family rules where
      they are a family's.
- [ ] Core set finished by hand to the gate (against the Italic's node
      counts), batches as in phase 5, at 72 and 144 pt beside the Italic.
- [ ] The exits and entries: Codex's audit found the stroked exits much
      lighter than the by-weight ones (n's 178 -> 48); settle their
      weight in words at text size on the clean letters.
- [ ] Its own spacing after the letters are final: sides by
      derived_spacing.py and evenness.py, then phase 3's kerning for
      this style again.
- [ ] Open from FONT-DESIGN.md if still there after regeneration: ⱳ.sc's
      kinks at the curl; ᵘ ⁿ's 32-degree corner; 𝑙 to smooth; the 8
      letters emboldened whole; the step candidates (₿ ǥ ɉ bar ends, ₡ ₹
      ₮, ꞁ ɑ.sc ⱦ.sc) and the 2026-11-09 verdicts not yet carried out
      (ɉ's bar, ɝ's hook, Italic Ⱦ's top, ₮'s bars, Bold ǥ ₿).

## Phase 9: screen and print proof

Model: Sonnet and the agents; the reading is the designer's.

- [ ] Before phase 5 (decided 2026-11-22): the Italic's colour alone,
      a small printed sample of Regular and Italic paragraphs at 9-12 pt
      (from `proofs/textpages.tex`): accept the Italic about 5 % lighter
      or raise `make_italic.py` WEIGHT a step, so that phase 5 redraws
      on the final weight.
- [ ] Along phases 5-8: `make qa`, `make udhr` and the screen checks
      below rerun now and then, new findings only (no reading).
- [ ] After phase 8, once: printed text pages (`proofs/textpages.tex`) at 9, 10, 11, 12 pt in
      the four styles, mixed roman/italic/bold paragraphs, in German,
      French, Greek, Russian, Vietnamese; read for colour between styles
      (the Italic about 5 % lighter than the Regular: accept or raise
      `make_italic.py` WEIGHT a step, on this evidence only).
- [ ] Screen: `scripts/quality/smallsize.py` and hint_zones at 9-16 px
      on Windows (ClearType/DirectWrite) and FreeType; the remaining
      `hint-zones*.txt` entries have verdicts, so only new findings count.
- [ ] `make udhr` read through once per script for stray pairs.
- [ ] `make qa` (fontbakery) clean but for the allow-lists.

## Phase 10: release 0.900

Model: Sonnet.

- [ ] README: status paragraph, known limitations rewritten to what is
      true after the phases before it, download link.
- [ ] DEVELOPMENT.md's publication items: contributor documentation,
      `sources/README.md`, dated reviews and proofs grouped with an index.
- [ ] `make release`; install the archive on a clean machine (OTF in
      LuaLaTeX and LibreOffice, TTF on Windows, WOFF2 in a browser);
      features table of README tested line by line.
- [ ] Tag v0.900, publish, FONTLOG entry.

## Phase 11: coverage (after the release, FONT-DESIGN.md's order)

Model: Sonnet for composed letters, Opus for new recipes and the manifest.

Aim: full IPA and Latin as wide as Charis SIL's (Latin 654 of 980 code
points, IPA and phonetic 133 of 368).

- [ ] Add the next set to `scripts/coverage.py` TARGET before drawing.
- [x] Letters that compose from existing glyphs: Ẁ ẁ Ẃ ẃ Ẅ ẅ Ỳ ỳ, the
      Irish dotted Ḃ ḃ Ḟ ḟ Ṁ ṁ Ṗ ṗ, Ǆ-ǌ, ḁ ḉ ḝ.
      Done 2026-11-14, before the release at the designer's wish: 86 of the
      88 Latin letters Charis has that compose from Myia's glyphs (Ǖ-ǜ Ǟ-ǡ
      Ǵ ǵ, the inverted breve and double grave ones, Ḃ-ẙ, ẛ on ſ with f's
      anchors) and the 12 digraphs Ǆ-ǌ Ǳ-ǳ (composites.DIGRAPHS: two
      letters at their kerning; kern_groups.ALIKE; smallcaps ǆ.sc ...).
      Left: the 32 Cyrillic ones (ӑ ӓ ӛ ...: outside basic Cyrillic).
- [ ] ḑ (Livonian; U+1E11) left out of that batch (the designer,
      2026-11-14): on d's Bottom anchor (between bowl and stem) the
      cedilla's square top steps out of the bowl's thin bottom (5-23 units
      in every style); a Cedilla anchor at the bowl's lowest point mends
      the Regular, but the Italic takes its anchors from Old Standard's
      Bottom (data_italic.ANCHOR_SOURCES) and the Bold's bowl still lets
      the corner out. Needs d's own Cedilla anchor in every style and the
      cedilla's top fitted to the bowl. Ḑ waits with it (fontbakery's
      case_mapping: a capital without its lowercase).
- [ ] kern_clear's guard: a guarded letter's exception to a group is set by
      the group's tightest member, so a new tall member loosens all of it:
      with ǟ ǡ in a's group the italics' Ɐ a went from -112 to -78 (Ɐ á æ
      ą ... with it; accepted by the designer 2026-11-14, Ɐ is rare). The
      tall member should take its own exception instead.
- [ ] Letters derived like ɢ ʙ: the Uralic small capitals ᴀ ᴄ ᴆ ᴇ ...;
      then the rest of IPA, extIPA and the phonetic blocks, in the
      Regular first, each style from its own final base.
- [ ] Latin Extended-D and -E (medievalist, Germanist): new drawing,
      last.
- [ ] The construction manifest (base, transform, operations per derived
      letter) named in the shape-grammar handoff, built on `main`, before
      the large derived batches: it makes them checkable.
- [ ] Each batch passes phases 1-3's tests (collisions, kerning groups,
      pairs) as it comes in: that is what those tests are for.

## Not planned

- Thinner hairlines in the italic capitals (declined 2026-10-21 and
  2026-11-02).
- A variable font; non-Slavic Cyrillic; other scripts.
- The four Bold Italic pairs `of` `Wh` `it` `ba` (kept 2026-10-20):
  reopen only on visual evidence.
