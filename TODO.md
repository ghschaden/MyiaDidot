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
      `proofs/italic-kerning-2026-11-11.pdf`
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
      `proofs/bold-trial-2026-11-11.pdf`. Reviewed 2026-11-11: B1
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
      mends as rendered (proofs/bold-italic-followers-mended-2026-11-12.pdf,
      proofs/italic-followers-mended-2026-11-12.pdf: g.sc ǥ.sc ₵ ₿ ы.sc
      psi.sc у.sc Ʌ; their accepted marks withdrawn until seen); O and Q
      want drawing.
      The Bold Italic's hooks of Ƙ Ƴ Ʋ (and ƙ.sc ƴ.sc ʋ.sc) done
      2026-11-12, chosen on proofs/bold-italic-hook-arms-2026-11-12.pdf:
      Ƙ Ƴ version C, Ʋ version D (make_bold.CURL_ARM).
      O and Q drawn 2026-11-12 (`scripts/draw_oq.py`), approved and
      installed; not committed: small caps moved after it, the causes
      traced and the Italic's mended in the generator (`sc_late`,
      docs/claude/redraw.md, "O and Q drawn"); waiting for the
      designer's review of the late sheets, then baselines and commit.

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
      `proofs/bold-italic-m-family-2026-11-10.pdf`); let the hook finish.
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
      `proofs/kerning-phase2-2026-11-13.pdf`, last pages of each style):
      - spacing, not pairs: ' and ” are loose before every stem capital
        (H B D E N P, by about 0.1 of the rhythm), G is tight before every
        lowercase (n o a e i): sidebearings of ' ” and G, not D or i pairs;
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
      `proofs/kerning-phase2-2026-11-13.pdf`; `make diffenator` and
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
      `proofs/ascender-clearance-2026-11-13.pdf`. Open:
  - [x] the Regular's U b keeps 87 units (H b 120): the designer found it
        "not good" too; a looser ASCENDER_CLEAR (80-120) would reach it,
        and V W Y with it (see the sheet's candidates).
        Decided 2026-11-14: 87 stays, ASCENDER_CLEAR stays 60 (sheet of
        60/80/100/120: `proofs/ascender-clearance-regular-2026-11-14.pdf`).
  - [x] the italics' Į (Iogonek) stands about 160 units right of I at
        the same advance (bounds 131..1097 against -29..923): a glyph
        fault; the rule now gives it about +200 before every ascender.
        Done 2026-11-13: Old Standard's own Į stood 84 right of its I
        (the only precomposed letter so); make_italic sets it on I
        (data_italic.OS_SHIFT, I's anchors: TopCap 709 -> 680). Į b +36
        (I b +28), Bold Italic +18; į.sc with it. Sheet
        `proofs/iogonek-italics-2026-11-13.pdf`.
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
        `proofs/accent-clearance-2026-11-13.pdf`; the designer chose 40
        (2026-11-14). Left open, found on the way:
    - [x] f before accented i (fî in French "fît", fï fì fǐ): the hook
          meets the mark in the upright styles (0 units); Charis touches
          too, Libertinus substitutes f.short. A contextual f, not kerning.
          Done 2026-11-14 (the designer chose the contextual f): f.short
          ff.short, the hook x0.6 (0.7/0.5 looked the same at reading
          sizes: `proofs/f-short-candidates-2026-11-14.pdf`), calt
          caltShortF before every Latin lowercase letter f comes within
          40 of (î 184, ï 82, ľ 83 now); ǐ ĭ ȉ kerned apart (ȉ +146).
          Left: f.short takes f's glyph kerning only through kern_clear
          (t f -45 is not t f.short).
    - [x] pinyin ǖ ǚ ǜ Ǖ Ǚ Ǜ are missing (Ǘ ǘ are there): composites
          (not in scripts/coverage.py's TARGET, as it turned out). Done
          2026-11-14 with the batch of phase 11's composed letters.

- [~] `Wo` (the designer, 2026-11-13): the gap looks too big. W's own
      group (3017a0aa, W apart from V) set W o/e/c at -60 (Bold -62) from
      V's -192 (Wa -160 -> -20). Nearest ink, units at Myia's cap height:
      Regular W o 395 (V o 392; Libertinus 342, Charis 389, Old Standard
      396), Italic 439 (Libertinus 291, Charis 364: both tighter), Bold
      407 (353, 384), Bold Italic 437 (331, 363). The italics are loose by
      the reference rule; the upright's look is W's open area, which
      nearest ink does not see: a sheet of W o e a at -60/-100/-140 to
      choose on.
      Chosen 2026-11-14 on `proofs/w-lowercase-2026-11-14.pdf`: W c -140,
      W a -80, W u -80 (the Bold x1.04, the italics by the rule).

- [x] Qu (dlig Q_u), the tail below the O: a redesign asked of Fable
      (2026-11-14: steeper neck, the swash leaving level at the crotch,
      thinning to a hairline needle; with and without an upturned end),
      set beside the present one on `proofs/qu-tail-2026-11-14.pdf`. The
      designer kept the present tail (QU_TAIL unchanged).

## Phase 3: the italics' own kerning

Model: the mechanism is F2; after it Opus for the test, Sonnet for the sheets and exceptions.

The Italic carries the Regular's values unchanged (`Av` −128, `To` −108,
`Wa` −160, `Ye` −204 in both), the bolds the same x1.04, though the italic
letters are another design with other sidebearings and overhangs. Greek
and Cyrillic are already measured per style; Latin is not.

- [ ] Measure: `scripts/quality/pairs.py Italic` and `BoldItalic`
      calibrated by each style's own n n / H H, as `greek_pairs.py` does;
      list the Latin pairs outside the references' range.
- [x] Decide the mechanism before the values (one source of truth;
      decided 2026-11-11, F2: docs/claude/spacing.md; to carry out:
      the rule into make_italic.py and make_bold.py, K y by hand; done
      2026-11-12, K y -30, approved on
      proofs/italic-kerning-in-generators-2026-11-12.pdf): the
      Regular's kerning scaled per pair by the white the italic shapes
      actually leave (computed), with `ITALIC_KERNING` and
      `ITALIC_BOLD_KERNING` holding only reviewed exceptions. A design
      decision to settle on a sheet of 30-40 pairs first.
- [ ] Re-proof the Bold Italic's hand-set positive kerns in
      `ITALIC_BOLD_KERNING` (`scripts/make_bold.py`, about line 940): they
      predate or straddle the stroked outlines. `G r` +121 leaves a clear
      gap in "Größe"; look also at `g a` +89, `u f` +92, `i f` +75,
      `a y` +67, `a f` +66, `w a` +57, `v a` +50. Delete those the stroked
      letters no longer need.
- [x] Add a Latin pairs test like tests/test_greek_pairs.py: a listed
      pair may not get further off. Done 2026-11-12:
      tests/test_latin_pairs.py, the italics against five reference
      italics (italic_kerning.outside), lists latin-pairs-Italic.txt and
      -BoldItalic.txt (all too tight; `update_test_data.py --latin`).
- [ ] Sheets, `make diffenator`, baselines.

## Phase 4: figures

Model: Opus for the default's change in space_figures.py, Sonnet for the rest.

- [ ] Decide the default: today lining and tabular, so dates and numbers
      in running text set loose, most of all in the italics. Recommended:
      proportional lining by default, `tnum` for tables (a change in
      `scripts/space_figures.py`'s generated block and in README's feature
      table; old documents reflow, so before 0.900 or never).
- [ ] Italic lining figures against the italic capitals: `1` stem 188
      against `n` about 175 across; they read darker than the words
      around them in lowercase text. Compare with H's stems on a
      `make strokes` sheet; lining belongs to the capitals, so this may
      be right, but confirm by eye in text.
- [ ] Figure kerning under `pnum` (1 against the others, 7 4 before
      period and comma) with phase 2.

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
      syncing them, and `build/` is 4.7 GB in 429 entries.
      - [ ] everything pushed; the Codex worktree
            (`~/src/MyiaDidot-shapes`) and the shared validation lock
            thought of in the move;
      - [ ] the folder excluded from the sync (or moved), `build/`
            first if the move has to wait;
      - [ ] `sync_check.py` and the conflict check in `make generate`
            kept until a month has passed without a finding, then
            dropped, CLAUDE.md's rule with them.
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
- [ ] T10. The records in order (DEVELOPMENT.md's publication items,
      phase 10): FONT-DESIGN.md back to open tasks only (523 lines,
      mostly finished work, against its own rule), the history to
      FONTLOG; the dated proofs (about 130 in `proofs/`) and review
      documents (about 70 in `docs/`) into dated subfolders with an
      index, links updated; `build/` cleared of what no target makes
      any more, the agents' logs under one name.

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

To decide first: whether 0.900 waits for these phases. Recommended: ship
0.900 after phases 0-4 and 9 (every glyph is already accepted at text
size) and take phases 5-8 as the road to 1.000; a redrawn core changes
advances little but shaping baselines much, better between releases.

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
      `proofs/bold-italic-stems-counters-2026-11-10.pdf`,
      `proofs/italic-stems-counters-2026-11-10.pdf` (before | now,
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

- [ ] One sheet Regular beside Italic, measured and seen: ball terminals
      (c a f r y against the Regular's), serif length and thickness,
      hairlines, colour (about 5 % lighter) and width (about 5 %
      narrower), x-height overshoots. What reads as another typeface is
      changed in the core set; the italic capitals' contrast stays
      (declined 2026-10-21, 2026-11-02).
- [ ] The derived letters, once their bases are final: the kink, smooth
      and extreme entries left in quality-Italic.txt, by family (a
      recipe's fault in the recipe, a letter's in the letter).
- [ ] Design entries (W's diagonals, i/j dot gaps, ξ, 7) get a dated
      verdict in the list, so what remains are all real candidates.
- [ ] Zone and slant entries (123 and 66): sorted into families first; a
      family fault goes into the generator, single letters wait.

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

- [ ] Printed text pages (`proofs/textpages.tex`) at 9, 10, 11, 12 pt in
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
