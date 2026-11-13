# One mark for "drawn and kept" (T6's specification)

Written 2026-11-13 (F6) from a reading of the code at 840665d7 and a count
of the four UFOs at that commit (nothing changed, no generator run). For
the session that carries it out (Opus). Line numbers are those of
840665d7.

## Today: three ways a generated glyph is kept

| style | what keeps a glyph | where it is decided |
|---|---|---|
| Italic | `org.myiadidot.italicSource` = `"drawn"` (110 glyphs, 98 of them redrawn by redraw.py, beside its record `org.myiadidot.redrawn`) | `make_italic.reviewed` (132-138), `kept` (2758-2761) |
| Italic | a draft (italicSource `derived`, `figure draft`, `small cap draft`) whose `org.myiadidot.draft` and `org.myiadidot.smallcapDraft` are both cleared, **as long as `MADE_WITH` is unchanged** (4 glyphs: o.sc q.sc zero.zero zerooldstyle.zero) | the same |
| Bold, Bold Italic | `org.myiadidot.drawn` = {date, why, source} (Bold 24, Bold Italic 57), written by `scripts/drawn.py` | `drawn.saved` in make_bold.main (2590-2594), make_bold.write (1918-1928), smallcaps.main (722-743) |

Beside them, marks that keep nothing and are not touched by T6:
`org.myiadidot.accepted` (a review's stamp, accepted.py: carried over,
the glyph made anew), `org.myiadidot.redrawn` (redraw.py's record),
`org.myiadidot.keptDraft` (on o.sc q.sc only, a note that no code reads),
the Regular's draft flags (derive.py keeps every existing Regular glyph
unless `--redraft` and a draft: the Regular is the master, not
generated).

What goes wrong with three:

- The Bold Italic begins as the Italic's glyphs, lib and all, so it
  carries the Italic's italicSource: 105 of its glyphs say `"drawn"`
  there, of which 14 also carry the Bold Italic's own mark and 43 carry
  only that. "drawn" in the Bold Italic's italicSource means "drawn in
  the Italic", and `stem_joins.hand_drawn` (120-133) reads it so, with a
  third case for redrawn letters. Each new reader has to know this.
- Clearing a draft flag (in Fontra, by hand) freezes an Italic glyph
  silently, but only until the weights change; in the bold styles the
  same act freezes nothing.
- `drawn.py` refuses the Italic (main, `"only the generated Bold and
  Bold Italic"`), so the Italic's drawn glyphs have no date, no reason
  and no record of the Regular letter they were drawn against: nothing
  tells when the Regular's letter changed under one (`drawn.stale`).

## The decision

1. **One key, `org.myiadidot.drawn`** = {`date`, `why`, `source`}, in the
   Italic, the Bold and the Bold Italic; `source` is
   `built_from.fingerprint` of the same glyph in the style it is made from
   (Italic → Regular, Bold → Regular, Bold Italic → Italic), "" where that
   style has no such glyph. A glyph carrying it is kept as saved by every
   generator that writes its style; nothing else keeps a glyph.
2. **`italicSource` is provenance only**: where the outline came from,
   read by the generators to decide *how* to make or finish a glyph
   (make_bold 2018, 2183, 2428 on `"derived"`; make_italic 1424 through
   `origin`; quality/derived.py, quality/outlines.py), never *whether to
   keep* it. Its value `"drawn"` stays as provenance ("the outline is a
   drawing made in the Italic"), so that none of those readers changes
   behaviour; it is written only together with the key (rule 4).
   Invariant, tested: in the Italic, italicSource `"drawn"` ⇒ the key.
   (Not the converse: the four glyphs of rule 3 keep their provenance.)
3. **Draft flags are review status only.** `draft` and `smallcapDraft`
   say "not yet looked at" and feed `accepted.py --drafts` and the review
   sheets; clearing one keeps nothing. The four Italic glyphs kept that
   way today are marked drawn in the migration (below), their
   italicSource unchanged (zero.zero stays `"derived"`: make_bold reads
   that).
4. **One tool, `scripts/drawn.py`, for the three styles.** For the
   Italic it also sets italicSource to `"drawn"` (what marking meant
   there until now, so `origin` and the provenance readers see what
   they saw); `--release` removes only the key, and the next
   make_italic run, which builds every unkept glyph from the Regular and
   Old Standard afresh (main, 2636), writes its provenance anew.
5. **A style's mark never travels to the style made from it.** The Bold
   Italic is made from the Italic's glyphs; make_bold drops the key from
   every glyph it takes from its source before anything else, as
   `accepted.carry` already does for acceptances. Only `drawn.saved` of
   the style being written decides what that style keeps.
6. **A change of `MADE_WITH`** no longer drops anything: the drawn
   glyphs are kept whatever the settings (as the 110 are today), and
   make_italic prints them, under "kept though the weights or cuts
   changed: look again", when `previous.lib[MADE_WITH_KEY] != MADE_WITH`.
   Of the four glyphs that today would come back as drafts then, o.sc
   and q.sc were kept deliberately for this case (keptDraft's note),
   zero.zero and zerooldstyle.zero follow zero; the listing is the
   prompt to look.

## The code, file by file

`scripts/drawn.py`

- `source_of`: Italic → Regular (today it returns the Italic itself for
  an Italic path); the rest unchanged.
- `mark(font, name, date, why, source_font)`: the one writer, used by
  main and by every script that marks; sets the key, and italicSource =
  `"drawn"` when `font.info.italicAngle` is set and the font is not bold
  (`openTypeOS2WeightClass` < 600, as stem_joins tells them).
- `release(font, name)`; `is_drawn(glyph)` (= `KEY in glyph.lib`), the
  one reader every other script imports.
- `strip(font)`: the key off every glyph (rule 5).
- main: the Italic accepted; the listing with `stale` against its
  Regular.

`scripts/make_italic.py`

- `reviewed` (132-138) → `drawn.is_drawn(g)`; `kept` (2758-2761):
  `[g.name for g in previous if is_drawn(g) and (g.name in font or
  g.name.endswith(".sc"))]`; `same_settings` used only for rule 6's
  listing.
- 2448 (`missing_anchors`' skip) and 2889 (`glyph_lint.fix`'s skip):
  `is_drawn` instead of `SOURCE_KEY == "drawn"` (the same set by the
  invariant; one reader).
- `origin` (122-129) unchanged: provenance.
- The docstring (27-31): one sentence for the key and drawn.py.

`scripts/make_bold.py`

- main, right after `font = ufoLib2.Font.open(args.regular)` (2596):
  `drawn.strip(font)`. Without it the Bold Italic's next save carries
  the Italic's 114 keys and the run after keeps all of them as its own.
  This line goes in **the same commit** as the Italic's migration.

`scripts/stem_joins.py` `hand_drawn` (120-133): in the Italic,
`is_drawn(glyph)`; in the bold styles their own key, then the Italic's
provenance as today (italicSource `"drawn"` and not redrawn: 12 letters,
delta.sc florin.sc lambda.sc theta.sc uni0191 uni01A5 uni0242.sc
uni0253.sc uni0257.sc uni0263.sc uni0280.sc uni044E.sc). Its docstring
says which is which. `bowl_counters` reads it and follows.

`scripts/sc_clearance.py` `_drawn` (44-45), `scripts/turned_v.py` (48):
`is_drawn`. They now also see the Italic's marks; neither of their
glyphs (uni044B.sc, psi.sc, uni0245) is drawn in the Italic today, so
nothing moves, but the reproduction run is what says so.

`scripts/smallcaps.py` (722-743): unchanged, but on the Italic its
`saved(args.ufo)` now finds the Italic's drawn glyphs and puts them back
after building the accented small caps. Where smallcaps rebuilds a glyph
that the Italic keeps as drawn (a drawn `.sc` it also composes), today's
Italic has smallcaps' version and the new run keeps the drawn one: the
reproduction run of step 2 lists any such glyph; each is a decision
(the drawn one kept, or released), not a code change.

`scripts/redraw.py` install (1011-1017) and `scripts/draw_oq.py` (249):
through `drawn.mark` and `is_drawn`; the redraw record stays, its
`source` field still read by `origin`.

The one-off scripts that set italicSource `"drawn"` (no generator runs
them, T7 retires them): hook_reference_candidates, italic_smallcap_repairs,
italic_yu_smallcap_repair, p_hook_join, italic_gamma_glottal_smallcaps,
italic_greek_smallcap_repairs; bold_italic_b_q_smallcaps writes the key
directly. All through `drawn.mark`, so that one run again marks as the
generators read.

Tests that set the old mark: test_redraw.py 144 and 239,
test_italic_contours.py 75 and 77; to the key.

## The migration and the order of commits

Each commit with `make reproduce` "as generated" for all three styles
and `make test` through; none changes an outline, a width, a kern or a
feature line.

1. **drawn.py for the three styles** (source_of, mark, release,
   is_drawn, strip) and its tests. Nothing reads the new functions yet.
2. **The Italic's marks, with make_bold's strip.** A one-off script
   (scratchpad, not committed) writes the key on:
   - the 110 glyphs with italicSource `"drawn"`: `date` and `why` from
     the redraw record where there is one (`"redrawn onto clean nodes,
     " + review`), else `date` "before 2026-11-13" and `why` "marked
     drawn in italicSource before T6" (git log -S on the glyph's file
     finds the real date for whoever wants it); `source` the Regular's
     fingerprint today, so that `drawn.stale` starts from now;
   - o.sc q.sc: why from keptDraft, which is then deleted;
     zero.zero zerooldstyle.zero: why "draft flag cleared (reviewed)
     before T6".
   `make normalize`. The Italic is unchanged by the next run (a kept
   glyph is restored with its lib), the Bold Italic is unchanged
   because of the strip. Check, beside reproduce:
   `drawn.py sources/MyiaDidot-Italic.ufo` lists 114.
3. **The readers and writers switched** (the files above), keptDraft
   gone from redraw.md's text. Before committing, the equivalence check:
   the old `reviewed`/`kept` and the new, evaluated on the committed
   Italic with the current MADE_WITH, give the same 114 names; the skip
   lists at 2448 and 2889 the same 110; `hand_drawn` the same verdict for
   every glyph of the three styles (a scratch script comparing old and
   new functions side by side, its output in the commit message).
4. **The documents**: CLAUDE.md's ground rule ("Hand-drawn Italic
   exceptions are marked 'drawn' ... in the Bold and Bold Italic,
   `scripts/drawn.py` ...") becomes one sentence for all three;
   docs/claude/styles.md 10-15 and 220-222; quality.md where it names
   the marks; accepted.py's docstring ("unlike clearing an Italic
   draft's flag"); drawn.py's ("The Italic's own mark is make_italic's
   'drawn' source").

Steps 2 and 3 may be one commit if the session is short; never step 3
before step 2 (the Italic would keep nothing).

## The tests (tests/test_drawn.py, beside the three there)

- `source_of`: Italic → Regular, Bold → Regular, Bold Italic → Italic.
- `mark` on an Italic font sets italicSource `"drawn"`, on a Bold Italic
  font not; `release` leaves italicSource.
- `strip` leaves no key; a glyph made from a marked source glyph and not
  in `saved` carries none after make_bold's opening (a unit test on the
  two calls, not a run).
- `make_italic.reviewed` on a synthetic draft with both flags cleared and
  no key: not kept.
- On the committed sources: Italic italicSource `"drawn"` ⇒ key; every
  key has `date`, `why`, `source`; in the Bold Italic no key whose
  (date, why) equals the Italic's for the same glyph (the strip held).

## Left out on purpose

- The Italic's provenance cleaned of `"drawn"` (italicSource =
  `origin(g)` for the 98 redrawn): it would change make_bold's
  `!= "derived"` readers for redrawn letters whose origin is `derived`
  and so the Bold Italic's outlines. A design change, if anyone wants it,
  with its own sheet.
- `accepted` merged into `drawn`: one says "looked at and approved, still
  generated", the other "no longer generated"; both are wanted.
- The Regular's draft flags: the Regular is edited, not generated.
