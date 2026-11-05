# Open font-design work

Current backlog, consolidated 2026-10-26. Completed work belongs in
[FONTLOG.txt](FONTLOG.txt); detailed evidence stays in `docs/` and `proofs/`.
Tooling and publication tasks belong in [DEVELOPMENT.md](DEVELOPMENT.md).
A diagnostic finding is a candidate for review, not proof of a design fault.
The exception files in `tests/data/` are the current inventories; do not copy
counts here, where they quickly become stale. Every entry in
`hint-zones*.txt` and `glyph-lint-*.txt` carries a dated verdict
(2026-10-26); reopen one only on new evidence (a raster or a proof).
One awaits it: Fraktur 𝔖's CFF top in both italics after its curves were
split at their extremes (marked PENDING REVIEW in hint-zones-cff-*.txt).

## Construction and optical quality

- Shared parts compared across glyphs (2026-10-27, measured on the
  outlines; the drawn glyphs agree, the generators make these):
  - Hook endings: the curl recipes' balls were fixed numbers, 20-60 %
    under the drawn balls of c a f r y. Done for derive.py's recipes in
    the Regular and Bold (2026-10-27, derive.ball_for; ʋ ɻ keep theirs:
    no room in the Bold). The italic tails off a stem (retroflex,
    descender: ɳ ʈ ɭ ɖ Ɽ ң қ ...) keep their ball at half the hook's
    stroke, flush with the curl's end (the person's decision, 2026-10-27).
    The italics' curls over the top (2026-10-27): the Italic's take the
    case's ball (about 72; its curls too small for its drawn c's 94); the
    Bold Italic's drawn at its weight, wider (balls 80-126 for its c's
    121, J's 143: more closed the counters). Its ⱳ.sc, emboldened from
    the Italic's draft, still has kinks and a wobble at the curl; ɦ.sc a
    step where Ɦ's top serif is cut (both in quality-BoldItalic.txt).
    Left: whether the person wants the capitals' curls larger still, to
    carry balls as large as J's; Ⱳ keeps its number (its curl run on
    straight from W's arm, 2026-11-03); Bold Italic a's ball does not grow (68 -> 66).
  - Dots: in the Bold and Bold Italic they are widened three times as
    much as heightened (period about 1.36:1, ⸁ ⸄ ⸅ ⸇ ⸈ 271x182, Bold Italic
    ※ ⁜ ⸓ ⸖ 323x207); ※ ⁜ ⸓ ⸖ take the accent dot (248), not the
    period's (256), and in the Italic their dots differ within a glyph.
  - Serifs: consistent but where make_bold.part_serifs shortens them, also
    those with no neighbour: Bold ﬀb ﬀh ﬀt ﬄ ſſl reach 103 (f 141); Щ, Bold
    Italic Ш; Bold m.sc ɦ.sc ƭ.sc ʝ.sc, Bold Italic ƙ.sc ϗ.sc ы.sc about 100
    (135-152). Bold ɫ.sc's top serif has a 1-unit end face. At hairline
    stems (N M U) the Bold's serifs reach 250 against 196.
- Wobbles (checks.py `wobble`, 2026-10-27): the emboldening puts short
  reversals into curves its source glyph has not. In the Bold a fitted
  curve now keeps its source's bends (keep_bends: 169 -> 130 glyphs);
  the rest bend back across a node, between two curves, which the guard
  (one curve at a time) does not see. In the Bold Italic (about 350)
  the cause (2026-10-27): 309 come from embolden_by_weight itself (not
  the slant, the zones or the bridge); nodes moved by different weights
  leave a curve that bends back whatever its handles' lengths along the
  kept directions (the guard's fitted and plain handles both bend in
  most). Shortening the handles takes out a third (365 -> 238 glyphs,
  Bold 142 -> 80) but changes Ⱳ's approved curl: not committed.
- **Bold Italic from strokes (next, the person's choice 2026-10-27).**
  The person's verdict: the Italic reads as drawn with a pen, the Bold
  Italic as pieced together, its curves unround. Cause: it offsets the
  Italic's nodes, each by the weight measured there, and patches the
  symptoms (keep_bends, oval, recipes). Tried 2026-10-27, not enough:
  - Thin ends (scripts/pilot/thin-ends.patch): a stroke's cut end (n's
    exit) is weighed across its length, a stem's weight, a wedge; left
    out of the measure, 320 Bold Italic glyphs change (n u i up to 28
    narrower), ℵ kept as it was; the ends thin, but the person: "still
    edgy, not smooth". In the Bold the same rule moves 212 glyphs
    (parentheses) and breaks ℵ's repair.
  - Runs redrawn (scripts/pilot/fair_runs.py): each run between corners
    and extremes as the fewest one-way cubics within 5 units. e's stem
    below its bar and s lose their wobbles; n a c h barely change: n's
    wobbles (inner crowns, the S above the foot) come from where nodes
    sit (the foot's extreme further left than one-way curves reach).
  - Stroke pilot (scripts/pilot/strokes_pilot.py): the Italic sampled
    every 2 units, each section's weight (ray to the facing side) shared
    by both its sides and smoothed along the outline (sigma 45), moved by
    make_bold's gain (AX*k across, AY up/down), mitred at corners,
    cleaned (pathops) and refitted. The person: n's right downstroke
    "definitely much better"; e and г no different. Its faults: about a
    third more nodes, kinks (г's spine, e's bar join, n's stem under the
    crotch), o's counter keeps its slight S, n a up to 8 % lighter (ends
    and hairlines gain only AY). Swapping in fair_runs' fitter made it
    worse (91 nodes in n, e's counter filled): not the way.
  Plan: (1) weights as the pilot's (paired, smoothed; ends thin by
  construction); (2) the structure from the Italic: fit the stroke
  outline with as many curves as the Italic glyph has, its nodes where
  the Italic's fall along each stroke (mapped by arc length per stroke
  side), tangents from the target outline, extremes kept, so the curves
  are as few and as smooth as the Italic's; (3) settle with the person
  what hairlines and ends gain; (4) a sheet of about 20 lowercase (n m h
  u a e c o s г ...) against the Italic and today's Bold Italic before
  anything goes into make_bold; then a full sweep and baselines.
  Render with node views (Italic | now | pilot); the person judges
  smoothness by eye, the reversal count is only a check.
  Step (2) done as a study (2026-10-28, scripts/pilot/strokes_fit.py,
  sheets by scripts/pilot/node_sheet.py): every sample keeps the Italic
  segment it came from, so each Italic curve is redrawn as one cubic and
  each line as one line (moved parallel by its mean weight); an extreme's
  node slides along the moved outline to where its tangent is again
  level or upright (the offset is wider across than up and down: left
  fixed, the inner crowns bent back); a line running smoothly into a
  curve gives the curve its direction; the cleaning's splits are joined
  again. On n m h u a e c o s г b d p q g r t v y f: nodes as the Italic
  (a crotch's pair becomes its one meeting point: a 20/23), reversals 2
  (today's Bold Italic 38, the pilot 16), weight within 1 % of the
  pilot's, so 0-10 % lighter than today's Bold Italic (n u r 9 %): the
  hairlines and ends of step (3) are still to settle with the person.
  Seen, still to look at: r's ball join keeps a small hook.
  Step (3), measured (2026-10-28, horizontal cuts at 0.3 and 0.8 x-height,
  per 1000 units): the lightness is in the entry and exit hairlines,
  which today's Bold Italic triples (Italic 23 -> 68, measured as wedges
  from a stem); Bodoni Moda's hairlines gain nothing (22 -> 22, stems
  x1.6), Libre Bodoni's a quarter (25 -> 31, stems x1.3); the fit 23 -> 24,
  stems x1.6 as today. strokes_fit's HAIR (env) adds a hairline gain
  across fading into AX: 0 / 12 / 24 give hairlines 24 / 30 / 36 and
  0.96 / 0.98 / 1.00 of today's weight. The person chose +12 (Libre
  Bodoni's quarter), now HAIR's default. The ends as the strokes give
  them (the person, 2026-10-28): raising a cut end's weight (at least 0.5
  or 0.8, falling off over 60 or 160 units) made a knob with a waist
  behind it, not today's straight wedge; tried and dropped.
  r's ball-join hook: the Italic rounds the join with a 12-unit curve of
  radius 10, under half the offset there, which turns inside out when
  moved; such a round is now drawn as a line between corners and the
  cleaning cuts a crotch (s's, radius 34 against 35, is left a curve).
  Step (4), the review sheet (Italic | today | fit, the 20 lowercase,
  hairlines +12): the person, "looks better, continue" (2026-10-28).
  In make_bold (2026-10-28, scripts/stroke_bold.py, the study's code made
  exact and fast: about 90 s for the style on 6 cores). Found in the sweep
  and fixed: the capitals' serif brackets (radius 40-65, under the stem's
  offset) folded into a corner and a jog: a bracket between two lines now
  moves whole; a crotch between two lines (K's arm) is where the moved
  lines meet; the oval refit of o O 0 gave the stroked counter cusps (not
  needed: Bold only); ø's slash by weight; r's shoulder roundings and ɺ's
  top graft (repairs of the by-weight outline) dropped. Kept by weight:
  ITALIC_BOLD_BY_POINTS (dollar ℵ ™ Ⱳ, repairs matching their points).
  checks.py against HEAD: kink 495 -> 108, wobble 352 -> 193, extreme 173
  -> 135, smooth 145 -> 102, step 30 -> 49; glyph_lint 5 -> 1 (Ⱥ notch).
  Still to do: the tests holding the by-weight outlines' coordinates (Ⱦ Ɉ
  ɸ repairs, ɬ Ꞁ belts, accepted glyphs), the new steps, К's kink, Ⱥ's
  notch, the shaping and hinting baselines (advances shift a few units).
  The person's choices after the sweep (2026-10-28): г's spine had a knee
  where the weight rose within one curve: SIGMA 45 -> 90; z s г too light
  beside the stems: a shallow diagonal is weighed by its width nearer the
  horizontal (ACROSS 0.6, faded out below 20 degrees so serifs and bars
  stay as measured) and a heavy diagonal gains half its offset up and down
  too (FULL 0.5; 1, today's rule, made the rounds dark), that weight from
  the section's own measure (diagonal sections only, smoothed), so serifs,
  feet and cut ends do not gain from the stem beside them. z s г about
  +11-13 % on today's ink, rounds +5-9 %, stems -3 %. Tried and dropped:
  the slashed letters (Ⱥ Ȼ Ⱦ ...) as base plus bar like ø (the derived
  letter's base is not exactly its glyph: the "bar" took half the letter).
  Then (the person: z s still light; 2 7 kinked; κ's leg not joined):
  FULL 0.75, ACROSS 0.45, the gain up and down for shallow strokes only
  (SHALLOW: under about 33 degrees, so κ's 45-degree arm pulls no waist
  where its hairline leg leaves it) and fading out within ZONE_NEAR of the
  zones (else v w y z α ... rose past their overshoots); 2's and 7's kinks
  were 3-unit lines the overlap removal leaves (TINY 4). z s г 2 now
  +11-15 % on today's ink, o +7 %, stems -5 %. z's bottom loop closes to a
  slit. Then (the person: "minimum noticeably blacker"; z's loop to stay
  open): the blackness was the spacing, not the ink (n m 5 % lighter than
  today's): fitted to the stroked letter's own white, the thinner entries
  and exits drew every letter about 23 units closer; now spaced as by
  weight (the by-weight letter's optical fit, so the stems stand where
  today's do; advances as today's but 65 glyphs). z's loop: no side moves
  more than CLEAR (a quarter) of the white in front of it, and hairline
  curls are not weighed as diagonals; z needs no exception. z still light
  (the person): its waves are shallow and near the zones, so gain little;
  ITALIC_BOLD_HEAVIER gives it 1.15 of the gain (+15 % on today's ink,
  ʐ ʑ ž follow). Letting the zone-facing fade spare inner edges added
  only 2 % to z and pulled counters off their zones: dropped.
  Derived letters (the person: the problem is in the letters put together):
  the slashed ones (Ⱥ ⱥ Ȼ ȼ Ⱦ and ⱥ ȼ ⱦ .sc) rebuilt by their recipe on the
  stroked base (Ȼ 51 -> 28 nodes); a rebuilt letter is cleaned
  (glyph_lint.fix) before it is judged, so Ƴ ʄ ҳ, steps of 1-3 units where
  the piece meets the base, are rebuilt again; Ⱳ by strokes and not joined
  to W after (53 -> 43 nodes, w_curl.py's repair no longer needed); Ⱦ's
  foot counter, larger now, closed by t_slash.py (limits widened); Greek
  ωρ ωμ ρω γα αδ and Cyrillic шт ін corrected in ITALIC_BOLD_KERNING.
  The middle tildes (ɫ Ɫ ᵬ-ᵶ, ɫ.sc) rebuilt by their recipe too: the tilde
  at the slashes' weight, lighter (the person preferred the new slashes),
  ᵭ's upper counter round again (emboldened whole, small and tight, it
  came out a triangle). The Bold Italic spaced 10 units a side looser
  ("a bit narrow"; BOLD_ITALIC_CUT, Greek alike): aleph.py's repair finds
  its points at any offset; Cyrillic ин лн back in range.
  For the person's review before the baselines: the accepted glyphs that
  changed (I ɬ ɸ ʈ.sc Ɽ Ⱳ Ꞁ) and the lint candidates (Ɠ's curl notch, Ƙ
  ᵭ steps of 1-2 units, the slash wedges of Ⱥ ⱥ.sc, ⊗'s cross wedges). The person
  and Codex agree on the order: exit weight, derived letters, a G2 trial
  in the fitter, paired fitting of a stroke's two sides where thickness
  problems remain.
  The G2 trial (2026-10-28, stroke_bold.py; on in the build since, MYIA_G2=0 to compare):
  at each smooth node between two curves both take one curvature, chosen
  between their own where the larger move is least (a short tight curve
  bends, a long one hardly), handle lengths solved for it; no curve moves
  more than G2_ERR (3 units) from its G1 fit, else that node stays G1. The
  rejoin keeps a merged run's end curvatures. Measured
  (scripts/pilot/g2_measure.py; joins turning under 2 degrees, handles of
  10 units or more, jumps over 1/250): Bold Italic 1999 -> 1236, a-z 84 ->
  33; 12 glyphs move over 5 units; ⊗ now falls back to the rounder way, ᵯ
  no longer does; the strokes take half as long again (n m s a g 2.0 ->
  3.1 s; make_bold for the Bold Italic 3 min 10 s). Found on
  the way: bounding by the samples let a curve move 40-65 units where the
  samples are far from any cubic (Ә's counter, q.sc's tail). Joins where
  3 units do not suffice (p g a) stay G1.
  Curves straight where they run on from a line (MYIA_G2_LINES=1, limit
  MYIA_G2_LINE_ERR): within 3 units only the gentle joins go straight
  (n's shoulder needs about 7, its tightest joins have no cubic at all);
  at 8 units n m h's stem joins are straight, but one cubic must then
  raise its curvature all at once: a spike on n's and h's right shoulders
  and a blob in the inner bowl, worse than today's step, and the curve
  joins at the cubics' other ends get worse (1236 -> 1313). Dropped as a
  fitter setting: a stem join needs a transition curve (an added node),
  the fairing of whole arcs. At text size (28 and 72 px per em) today, G2
  and G2 with straight ends cannot be told apart.
  Codex's audit of the stroked h n u o (MyiaDidot-shapes,
  docs/main-stroke-audit-2026-10-28.md): exit strokes much lighter than
  today's (n's at y 352 178 -> 48), curvature not continuous at smooth
  joins (tangents are); its order: settle the exits' weight at text size,
  then fair whole arcs (its shape_fairing.py), then o's lower stroke.
  Whole arcs faired (2026-10-28, scripts/fair_arcs.py, on in stroke_bold
  since, MYIA_FAIR=0 to compare): each arc between corners refitted at
  once, nodes and handles together. Tried and dropped: the squared change
  of curvature (rounds the tight inner turns at n's and h's counter tops
  by up to 9 units, a Didot mark lost; weighting the fit by curvature only
  moved the change elsewhere); without the one-way rule the transitions
  bent back (S-bends). Kept: the change of log |k| (scale-free), curves
  may not bend back, a curve next to a line split in two and only fading
  towards it (else a swell before n's outer stem). The person compared
  combs (today | faired) and found the faired better; at 72 and 260 px per
  em they cannot be told apart. Bold Italic: curve joins over 1/250 1236
  -> 860; curves leaving lines over 1/250, brackets aside, 826 -> 585 (the
  rest mostly capital serif curves over 120 units, refused: straight ends
  would move them 12-18 units); n m h 8-11 nodes more. make_bold for the
  Bold Italic 3 min 10 s -> 5 min 40 s. Arcs holding the cleaning's
  leftovers (1-unit cubics, a handle doubling back: d k r z) are left as
  they are, faults for later. Ɠ's hook stroke now starts at 1310 (from
  1320 it left a notch on the faired G and the recipe was refused).
  Still to do: k's arm (12 units), q's tail, s, y's tail refused at 6.
  The cleaning's leftovers (2026-10-28, stroke_bold.rejoined): curves under
  8 units merged into their neighbours, at the piece's sharper end (a
  crotch stays where the cleaning cut it) or at a line's end (€'s bar
  stays level); not lines (ɉ's bar end is a 4-unit line). The Bold
  Italic's flagged pieces 386 -> 234; r's zigzag and d's pieces gone, z's
  knob at the top of its spine. Tried and dropped: ending a curve where its
  moved samples run backwards into a corner (k's arm became a straight
  chord), an end doubling back taking its samples' direction (fixed k's
  and z's hooks, but notched ξ, which then went the rounder way), the
  merged join made smooth (joined ɕ's slit into one arc; the fairing closed
  it). Left: k's hook where arm meets leg, z's bottom-left curl. The
  fairing: no curve under 16 units split, a result with a piece under 8
  refused, a contour crossing itself once faired kept as fitted (k's
  crotch). CI's make reproduce found 68, then 49 glyphs otherwise: make_bold
  pins numpy and OpenBLAS to AVX2, and the solve uses no sine, cosine,
  exponential or logarithm (the C library's differ between systems), runs
  until settled with central differences, kinks rounded off, ties broken
  alike. k's upper arm (51 units across at the bar, 67 above): thicker
  roots tried 2026-11-04, no difference seen; its turn into the ball
  redrawn round instead (k kept as drawn).
- Step candidates (checks.py `step`, in `tests/data/quality-*.txt`):
  reviewed 2026-11-04 those named as likely faults: ʝ's crossbar end and
  Bold ɝ's hook join designed; ɾ ᵳ keep r's foot slab in every style (and since 2026-11-04 end at f's hook, r's stem above it cut away, the person: to read apart from r);
  Serbian г made from ū's first stem (its stem had bent where ı met ū);
  Bold Italic п т's short bar overhang taken as is. The rest still marked
  "a candidate to review" (₿ ǥ ɉ bar ends, ₡ ₹ ₮, ꞁ ɑ.sc ⱦ.sc ...).
- Bold middle-tilde letters (ᵬ ᵭ ᵮ ᵯ ᵰ ᵱ ᵲ ᵳ): the left end of the
  foot serif cut at a slant, and the stem's left edge swelling about 8
  units at the tilde (seen 2026-11-04 on ᵲ ᵳ ᵰ); the Bold Italic's are
  drawn by strokes and do not have it. Done 2026-11-04: the tilde drawn
  on the Bold's own base (BOLD_REBUILD, as the Bold Italic's), the
  stems now the base's to a unit outside the tilde; ᵲ ᵳ (and ɍ) made of
  r once its inner stem is faired (fair_bold_stem had not run before
  the derived letters: the style not yet named Bold, its points not
  yet rounded); ᵰ's notches under the tilde's ends filled along the
  stem (make_bold.fill_stem_notches), not cleaned as ledges that
  pulled the stem aside. The tilde the Bold's own, likely lighter than
  emboldened: to review. Its right end now near ɉ's bar: kern_clear's
  guard loosened the b group + ɉ from −44 to +21 (and gave ᵬ + j 21).
- Bold curves into a straight stem (2026-11-04): emboldened by weight, a
  curve running into a vertical stem had a handle past the stem's edge,
  a dent in the stem (n 24 units, m 32; the Regular none): arches into
  n m h ŋ ħ's stem, u ų ɯ ɰ ɥ ц щ's bowls at the foot, the hooks of J ȷ
  ʃ ɉ ɽ ɳ, Œ's counter into E's stem, ®; 49 glyphs and those made of
  them. scripts/stem_handles.py (make_bold before the derived letters
  and finalization after rounding) puts the stem's handle back on the
  edge and shortens the far one along its own direction to it. The
  hooks' inner corners (J ȷ ɽ ɳ, Œ) turn a little tighter: to review.
- Italic small caps stand taller at their rounds (the person, samples.pdf
  BOXKÄMPFER, 2026-11-05): FontForge's drafts (make_italic
  smallcaps_stage) keep the capitals' overshoot in units, 39 past 0 and
  1040 (3.7 %; the Italic's capitals 2.7 %, the Regular's small caps
  2.2 %). Scaling it with the letter (o.sc 1077 → 1067) was tried and
  set aside: the small caps derived from them by recipes moved (ɦ.sc's
  H 20 units, steps of 65 and 45 units at ƈ.sc's and ɦ.sc's hooks, the
  IPA small capitals ɢ ɪ ʟ ʀ ʙ rescaled by o.sc's extent), about 25 new
  quality findings. To do as its own change, the derived ones checked
  one by one (the patch tried: after weight_thick in smallcaps_stage, a
  contour whose top or bottom lies within 60 units past the zone has its
  points past it brought nearer by smallcaps.SCALE; tails further out
  left alone).
- Bold Italic small caps: the round sides stand 30-60 units tighter
  against the straight ones than in the Regular and the references
  (b.sc h.sc 0.94 of h.sc h.sc against 1.12-1.23, h.sc o.sc 1.02 against
  1.05-1.24, e.sc's right 0.87 against 0.93-1.34; 2026-11-05, measured
  with capsc_pairs.Font's gap): b.sc o.sc in BOXKÄMPFER packed. To sweep
  all small caps' sides against the references, after the overshoot.
- ſ ſſ before the round letters (c d e o g q œ and their accents) kerned
  −60, the Bold Italic −80 (the person, from proofs, 2026-11-05); the
  accented ones guarded against ſ only (kern_clear.GUARDED_AGAINST). The
  full guard would also loosen 12 other pairs (A.sc before ö.sc ō.sc õ.sc
  ǭ.sc č.sc ḡ.sc ..., −78 → −13 for ö.sc; F ỡ; V Y ě): left as they
  were (the person), the dieresis near A.sc's apex without touching.
- kern_clear.guard: a guarded right letter's exception to a left group
  (ɉ against b o p ...) is measured over every member, also one guarded
  on the left with an exception of its own that wins anyway (ᵬ), so one
  member's accent or tilde loosens the whole group. Done in order (left
  letters first, those with their own exception not measured), about
  850 pairs in Bold, Italic and Bold Italic tighten to GUARD (Bold U+ǎ
  −29 → −92, Italic V+ǒ −151 → −186): tried 2026-11-04, set aside for
  the person's decision and a visual sweep.
- Bold Italic, seen in print (2026-10-27), reviewed 2026-11-02: ʋ (its
  own recipe) and Ɯ (U twinned) done 2026-10-29; ʷ ʸ ʰ ʲ ⁱ ᶤ ᶶ and the
  other modifier letters the Italic derives are made small from the Bold
  Italic's own letters (make_bold ITALIC_BOLD_REBUILD_OPS): the entry
  hook's curl no longer squeezed into a corner (32 degrees, now 11, as w's
  own). Still open: ᵘ ⁿ, refused by the gate (made small, n's arch crotch
  is a notch at that size), keep their 32 degree corner; г's inner curves
  stand upright from the stroking itself (the fit follows its samples
  within 2 units; s з 3 2 alike), not a fault of г's; the person to say
  whether the counters should keep rounder. A sweep of Bold Italic
  corners where the Italic is smooth found about 190 candidates (many
  designed: crotches, ligature joins, ⁂), not yet reviewed. Limiting the
  stroke gain on tight inner turns (tried 2026-11-02) only moved the bend
  and added corners (k r c W J): the strokes gain 34 across but 4 up and
  down, so a curl's upright side moves in far more than its top.
  2026-11-03: γ & ξ ү ұ Q q.sc crotches meet where the strokes cross
  (stroke_bold Strokes.crossing; FONTLOG). q.sc's bowl inside bent just
  above its small loop, where the room cap (Strokes.weights, min of the
  weight and CLEAR of the white in front) took over as the counter
  narrowed: lifted within 300 units of its crotch (make_bold
  ITALIC_BOLD_CAP_FREE). For every letter that broke the oldstyle 2 and
  filled q's crotch; a larger CLEAR alone left an S. &'s stem foot: 9
  units (was 19, the Italic's 7), the glyph kept as drawn (drawn.py,
  2026-11-03); q.sc's small loop keeps its point where the tail crosses
  itself, as the Italic's.
- Bold Italic: keep_bends is on (2026-10-27); still to try the Bold's two
  other repairs (make_bold: keep_smooth for the rounder way, runs_on by
  weight; keep_smooth adds inflections there, Codex's study). Tried
  there they smooth § 3 ₵ ø.sc Θ ẞ but add side space (3 +21, § +13),
  notch ẞ, move ɽ's advance and ƙ.sc's CFF top, and runs_on kinks ð ɨ ђ
  ћ љ ˁ: each needs review before switching them on.
- Review derived letters still emboldened whole in
  `tests/data/emboldened-whole-*.txt`. Hooks, attachments and curls may need
  recipes drawn at the final weight when rederivation strays or misses.
  Include Bulgarian forms and rhotic letters where still listed; the
  repaired Bold Italic ʄ is complete. Every remaining entry now has a
  reviewed reason in BOLD_KEEP_WHOLE / ITALIC_BOLD_KEEP_WHOLE (2026-10-26):
  the generic rederive fixes are spent, what is left needs a recipe drawn
  at the style's weight (BOLD_RECIPES, ITALIC_BOLD_RECIPES) or a
  landmark-placed cut, letter by letter.
- Work through `tests/data/quality-*.txt`: extrema, kinks, smooth joins,
  stroke weight, zones, slant, width and accent gaps. Many italic findings
  are inherited from Old Standard and propagate to Bold Italic. Keep broad
  contour cleanup separate from individual drawing changes and inspect
  `make diffenator` results. Use `make strokes` for optical-weight proofs.
  W-family diagonal slant and i/j dot gaps can be intentional.
  Extremes lost to a slant or turn are split by the generators now
  (2026-10-26), the rederived Bold Italic letters too (2026-10-27); none
  left runs more than about 20 units past (Bold Ʒ ℓ, Bold Italic ѫ ® л @).
- Accept, or send back, the drafts not yet accepted: `scripts/accepted.py
  UFO --drafts` (about 350 in each italic weight, ₸ ct st in the Romans).
  Acceptance is recorded with accepted.py, not by clearing draft flags
  (docs/claude/quality.md). `make proof` writes the review sheets of
  exactly those (drafts-review-STYLE.pdf, smallcaps-review-STYLE.pdf):
  the next step is the person's pass through them. Bold and Bold Italic
  old-style figures (not drafts, so not on the sheets) have no recorded
  acceptance; Regular old-style 3 and 5 changed after theirs.

## Spacing: revisit only if specimens warrant it

Four Bold Italic pairs (`of`, `Wh`, `it`, `ba`) were reviewed on 2026-10-20
and retained despite tight measurements against references. They are not
unresolved repair tasks; reopen only on visual evidence.
