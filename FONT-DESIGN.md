# Open font-design work

Current backlog, consolidated 2026-10-26. Completed work belongs in
[FONTLOG.txt](FONTLOG.txt); detailed evidence stays in `docs/` and `proofs/`.
Tooling and publication tasks belong in [DEVELOPMENT.md](DEVELOPMENT.md).
A diagnostic finding is a candidate for review, not proof of a design fault.
The exception files in `tests/data/` are the current inventories; do not copy
counts here, where they quickly become stale. Every entry in
`hint-zones*.txt` and `glyph-lint-*.txt` carries a dated verdict
(2026-10-26, the last pending ones 2026-11-08); reopen one only on new
evidence (a raster or a proof).

## Construction and optical quality

- Shared parts compared across glyphs (2026-10-27, measured on the
  outlines; the drawn glyphs agree, the generators make these):
  - Hook endings: the curl recipes' balls were fixed numbers, 20-60 %
    under the drawn balls of c a f r y. Done for derive.py's recipes in
    the Regular and Bold (2026-10-27, derive.ball_for; ʋ ɻ keep theirs:
    no room in the Bold). The italic tails off a stem (retroflex,
    descender: ɳ ʈ ɭ ɖ Ɽ ң қ ...) keep their ball at half the hook's
    stroke, flush with the curl's end (decided 2026-10-27).
    The italics' curls over the top (2026-10-27): the Italic's take the
    case's ball (about 72; its curls too small for its drawn c's 94); the
    Bold Italic's drawn at its weight, wider (balls 80-126 for its c's
    121, J's 143: more closed the counters). Its ⱳ.sc, emboldened from
    the Italic's draft, still has kinks and a wobble at the curl (in
    quality-BoldItalic.txt; ɦ.sc's steps done 2026-11-05, FONTLOG).
    The Italic's Ƙ Ƴ Ʋ curls 1.25 times larger, as Ƈ Ɠ's (2026-11-08,
    FONTLOG); Ⱳ keeps its number (its curl run on
    straight from W's arm, 2026-11-03); Bold Italic a's ball does not grow (68 -> 66).
  - Dots: done 2026-11-09, round in both bold styles (bold_dots.py; FONTLOG).
    The Italic's ※ ⁜ ⸓ ⸖ dots still differ within a glyph (216 x 201-219),
    and those four take the accent dot (248), not the period's (256).
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
- **Bold Italic from strokes (chosen 2026-10-27; in make_bold since 2026-10-28, scripts/stroke_bold.py).**
  The verdict: the Italic reads as drawn with a pen, the Bold
  Italic as pieced together, its curves unround. Cause: it offsets the
  Italic's nodes, each by the weight measured there, and patches the
  symptoms (keep_bends, oval, recipes). Tried 2026-10-27, not enough:
  - Thin ends (scripts/pilot/thin-ends.patch): a stroke's cut end (n's
    exit) is weighed across its length, a stem's weight, a wedge; left
    out of the measure, 320 Bold Italic glyphs change (n u i up to 28
    narrower), ℵ kept as it was; the ends thin, but review: "still
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
    cleaned (pathops) and refitted. Review: n's right downstroke
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
  are as few and as smooth as the Italic's; (3) settle in review
  what hairlines and ends gain; (4) a sheet of about 20 lowercase (n m h
  u a e c o s г ...) against the Italic and today's Bold Italic before
  anything goes into make_bold; then a full sweep and baselines.
  Render with node views (Italic | now | pilot); smoothness is judged
  by eye, the reversal count is only a check.
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
  hairlines and ends of step (3) are still to be settled in review.
  Seen, still to look at: r's ball join keeps a small hook.
  Step (3), measured (2026-10-28, horizontal cuts at 0.3 and 0.8 x-height,
  per 1000 units): the lightness is in the entry and exit hairlines,
  which today's Bold Italic triples (Italic 23 -> 68, measured as wedges
  from a stem); Bodoni Moda's hairlines gain nothing (22 -> 22, stems
  x1.6), Libre Bodoni's a quarter (25 -> 31, stems x1.3); the fit 23 -> 24,
  stems x1.6 as today. strokes_fit's HAIR (env) adds a hairline gain
  across fading into AX: 0 / 12 / 24 give hairlines 24 / 30 / 36 and
  0.96 / 0.98 / 1.00 of today's weight. +12 was chosen (Libre
  Bodoni's quarter), now HAIR's default. The ends as the strokes give
  them (2026-10-28): raising a cut end's weight (at least 0.5
  or 0.8, falling off over 60 or 160 units) made a knob with a waist
  behind it, not today's straight wedge; tried and dropped.
  r's ball-join hook: the Italic rounds the join with a 12-unit curve of
  radius 10, under half the offset there, which turns inside out when
  moved; such a round is now drawn as a line between corners and the
  cleaning cuts a crotch (s's, radius 34 against 35, is left a curve).
  Step (4), the review sheet (Italic | today | fit, the 20 lowercase,
  hairlines +12): approved, "looks better, continue" (2026-10-28).
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
  The choices after the sweep (2026-10-28): г's spine had a knee
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
  Then (review: z s still light; 2 7 kinked; κ's leg not joined):
  FULL 0.75, ACROSS 0.45, the gain up and down for shallow strokes only
  (SHALLOW: under about 33 degrees, so κ's 45-degree arm pulls no waist
  where its hairline leg leaves it) and fading out within ZONE_NEAR of the
  zones (else v w y z α ... rose past their overshoots); 2's and 7's kinks
  were 3-unit lines the overlap removal leaves (TINY 4). z s г 2 now
  +11-15 % on today's ink, o +7 %, stems -5 %. z's bottom loop closes to a
  slit. Then (review: "minimum noticeably blacker"; z's loop to stay
  open): the blackness was the spacing, not the ink (n m 5 % lighter than
  today's): fitted to the stroked letter's own white, the thinner entries
  and exits drew every letter about 23 units closer; now spaced as by
  weight (the by-weight letter's optical fit, so the stems stand where
  today's do; advances as today's but 65 glyphs). z's loop: no side moves
  more than CLEAR (a quarter) of the white in front of it, and hairline
  curls are not weighed as diagonals; z needs no exception. z still light
 : its waves are shallow and near the zones, so gain little;
  ITALIC_BOLD_HEAVIER gives it 1.15 of the gain (+15 % on today's ink,
  ʐ ʑ ž follow). Letting the zone-facing fade spare inner edges added
  only 2 % to z and pulled counters off their zones: dropped.
  Derived letters (review: the problem is in the letters put together):
  the slashed ones (Ⱥ ⱥ Ȼ ȼ Ⱦ and ⱥ ȼ ⱦ .sc) rebuilt by their recipe on the
  stroked base (Ȼ 51 -> 28 nodes); a rebuilt letter is cleaned
  (glyph_lint.fix) before it is judged, so Ƴ ʄ ҳ, steps of 1-3 units where
  the piece meets the base, are rebuilt again; Ⱳ by strokes and not joined
  to W after (53 -> 43 nodes, w_curl.py's repair no longer needed); Ⱦ's
  foot counter, larger now, closed by t_slash.py (limits widened); Greek
  ωρ ωμ ρω γα αδ and Cyrillic шт ін corrected in ITALIC_BOLD_KERNING.
  The middle tildes (ɫ Ɫ ᵬ-ᵶ, ɫ.sc) rebuilt by their recipe too: the tilde
  at the slashes' weight, lighter (preferred the new slashes),
  ᵭ's upper counter round again (emboldened whole, small and tight, it
  came out a triangle). The Bold Italic spaced 10 units a side looser
  ("a bit narrow"; BOLD_ITALIC_CUT, Greek alike): aleph.py's repair finds
  its points at any offset; Cyrillic ин лн back in range.
  For the review before the baselines: the accepted glyphs that
  changed (I ɬ ɸ ʈ.sc Ɽ Ⱳ Ꞁ) and the lint candidates (Ɠ's curl notch, Ƙ
  ᵭ steps of 1-2 units, the slash wedges of Ⱥ ⱥ.sc, ⊗'s cross wedges). The order is
  agreed with Codex: exit weight, derived letters, a G2 trial
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
  towards it (else a swell before n's outer stem). Combs compared
  (today | faired): the faired found better; at 72 and 260 px per
  em they cannot be told apart. Bold Italic: curve joins over 1/250 1236
  -> 860; curves leaving lines over 1/250, brackets aside, 826 -> 585 (the
  rest mostly capital serif curves over 120 units, refused: straight ends
  would move them 12-18 units); n m h 8-11 nodes more. make_bold for the
  Bold Italic 3 min 10 s -> 5 min 40 s. Arcs holding the cleaning's
  leftovers (1-unit cubics, a handle doubling back: d k r z) are left as
  they are, faults for later. Ɠ's hook stroke now starts at 1310 (from
  1320 it left a notch on the faired G and the recipe was refused).
  k's arm, q's tail, s, y's tail: accepted as they are (2026-11-09).
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
  Bold ɝ's hook join designed; ɾ ᵳ keep r's foot slab in every style (and since 2026-11-04 end at f's hook, r's stem above it cut away, review: to read apart from r);
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
- Bold Italic capitals against H (2026-11-08): H H is in the references'
  range (H H / n n 1.00); the rounds and bowls were tight (O O 0.80 of
  H H, references 0.87-0.95). Given the Italic's white per side
  (make_bold ITALIC_CAPITAL_ROUNDS: O Q C G D B P S); left as the Italic
  has them: B against H, C and R against O. Bold N and n.sc spaced as the Regular's (2026-11-08,
  FONTLOG). The lining figures are tabular again in both bold
  styles (2026-11-05, FONTLOG).
- Italic small caps at their capitals' weight (as_capitals, 2026-11-05):
  s.sc n.sc є.sc ϟ.sc made from their capitals (done 2026-11-05, FONTLOG).
  Bold Italic s.sc stands 0.82 of h.sc (S 0.91), accepted; the Bold Italic
  n.sc and ɴ keep small wobbles where their brackets meet the stems, as
  the Bold Italic N's node clusters there.
- Bold Italic rounds' counters: done 2026-11-05 (the Italic's counter,
  make_bold italic_counter; FONTLOG). o's counter is as round as the
  Italic's, narrow with fairly straight sides: rounder only if the Italic's
  o changes. The open rounds c C G c.sc g.sc take the Italic's inside
  (italic_inside, 2026-11-06); e ɔ є and the others keep their stroked ones.
- ſ ſſ before the round letters (c d e o g q œ and their accents) kerned
  −60, the Bold Italic −80 (from proofs, 2026-11-05); the
  accented ones guarded against ſ only (kern_clear.GUARDED_AGAINST). The
  full guard would also loosen 12 other pairs (A.sc before ö.sc ō.sc õ.sc
  ǭ.sc č.sc ḡ.sc ..., −78 → −13 for ö.sc; F ỡ; V Y ě): left as they
  were, the dieresis near A.sc's apex without touching.
- kern_clear.guard by member: done 2026-11-08 (FONTLOG).
- Bold Italic, seen in print (2026-10-27), reviewed 2026-11-02: ʋ (its
  own recipe) and Ɯ (U twinned) done 2026-10-29; ʷ ʸ ʰ ʲ ⁱ ᶤ ᶶ and the
  other modifier letters the Italic derives are made small from the Bold
  Italic's own letters (make_bold ITALIC_BOLD_REBUILD_OPS): the entry
  hook's curl no longer squeezed into a corner (32 degrees, now 11, as w's
  own). Still open: ᵘ ⁿ, refused by the gate (made small, n's arch crotch
  is a notch at that size), keep their 32 degree corner; г's inner curves
  stand upright from the stroking itself (the fit follows its samples
  within 2 units; s з 3 2 alike), not a fault of г's; still to decide
  whether the counters should keep rounder. A sweep of Bold Italic
  corners where the Italic is smooth (scripts/quality/corners.py) was
  reviewed from its sheet and the flagged ones smoothed (2026-11-09,
  smooth_joins.py; FONTLOG). Limiting the
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
  UFO --drafts`. Acceptance is recorded with accepted.py, not by clearing draft flags
  (docs/claude/quality.md). `make proof` writes the review sheets of
  exactly those (drafts-review-STYLE.pdf, smallcaps-review-STYLE.pdf):
  the next step is the pass through them. 2026-11-05: the
  Regular's and the Italic's drafts sheets accepted but for these, sent
  back: Ƭ (the right turn into the hook uneven) and ʂ (the turn into its
  hook still not good) in the Regular, the italic ɉ (its bar not
  centred); the Regular's ɹ ɺ ɻ to be rebuilt as r turned, as in the
  italics (review: the drawn hook looks very different from r's).
  2026-11-06: those reworked and accepted (FONTLOG), the Regular
  small-caps sheet accepted, ƈ.sc ɠ.sc redrawn (curls on c.sc g.sc) and
  accepted in the Regular, Italic and Bold, Ƭ in the Regular and Bold; the
  italics' Ƭ ƭ.sc (left arm 0.65 of the right) and the Bold Italic c C G g
  c.sc g.sc ƈ.sc ɠ.sc Ǥ ɔ.sc (insides from the Italic's, italic_inside)
  accepted from proofs. The Bold Italic Ɠ, ɠ and revised ɠ.sc also
  accepted (2026-11-06): Ɠ's hook thicker and joined without the ledge,
  ɠ's inner downstroke a continuous curve, ɠ.sc's hook rising as the
  capital's. Marked drawn and accepted. See
  [G-hook review](docs/g-hooks-review-2026-11-06.md).
  ʛ is ɠ.sc's alias, so at the small caps'
  height (1060), where ɢ and the other IPA small capitals stand at the
  x-height (884, 2026-11-01). Decided 2026-11-08: ʛ follows them (ɠ.sc
  scaled as ɢ from g.sc), a draft to review.
  2026-11-08: Bold small caps and all remaining Bold drafts accepted, with
  local drawing repairs and retained proofs (docs/bold-*-review-2026-11-07.md).
  Bold Italic's 39 extended Latin drafts through U+024F are accepted:
  [extended Latin draft review](docs/bold-italic-extended-latin-drafts-review-2026-11-08.md).
  The next 57 Bold Italic phonetic drafts are accepted (2026-11-08):
  [phonetic review](docs/bold-italic-phonetic-drafts-review-2026-11-08.md).
  The 49 Latin and modifier-letter drafts are accepted (2026-11-08):
  [Latin and modifier review](docs/bold-italic-latin-modifier-drafts-review-2026-11-08.md).
  The 20 currency signs are accepted (2026-11-08):
  [currency review](docs/bold-italic-currency-drafts-review-2026-11-08.md).
  14 Cyrillic letters and the Serbian italic forms (both italics, the bar
  free above as in Charis and Libertinus) are accepted (2026-11-08):
  [Cyrillic review](docs/bold-italic-cyrillic-drafts-review-2026-11-08.md).
  Ҳ (tail unified with Ң Ҷ) accepted. The last drafts (old-style figures,
  U.horn, u.sc.horn, Bulgarian forms) are accepted, and the italics' ж has
  its left c mirrored (2026-11-08):
  [final review](docs/bold-italic-final-drafts-review-2026-11-08.md).
  No Italic or Bold Italic drafts remain unaccepted. The Bold Italic's remaining
  72 phonetic, Greek and Cyrillic small caps and lowercase қ/ҳ/ҷ repairs are
  accepted (2026-11-07), including the final straight inner қ leg:
  [completed Bold Italic review](docs/bold-italic-smallcaps-completion-2026-11-07.md).
  The Italic's 26 basic Latin small caps
  are accepted unchanged (2026-11-06):
  [Italic Latin small-cap review](docs/italic-smallcaps-latin-review-2026-11-06.md).
  The next 46 extended Latin Italic small caps have a two-page proof.
  Sent back after the review: uni0280.sc has a torn bowl and
  detached leg (the lower recipe cuts through the bowl); uni0253.sc and
  uni0257.sc have oversized, low hooks unlike their capitals. Those three
  are now locally reconstructed and accepted (2026-11-06), including
  smoothing the small nodges on both sides of the hook stems:
  [small-cap repairs](docs/italic-smallcap-repairs-2026-11-06.md).
  Bold Italic follow-up: the hooked b/d small caps' lower serif joins and
  upper stem transitions are locally redrawn and both are accepted. The b's
  approved upper counter is rounder like its lower counter:
  [Bold Italic hook stems](docs/bold-italic-hook-stems-review-2026-11-06.md).
  The other 43 glyphs in this batch are accepted unchanged (2026-11-06):
  [extended Latin small-cap review](docs/italic-smallcaps-extended-latin-review-2026-11-06.md).
  Italic ƥ (uni01A5) reopened by review: swelling at the hook/stem
  join removed locally and accepted (2026-11-06). Bold Italic regenerated
  and finished with its spacing retained; its fuller hook and smooth stem
  transition are also accepted (2026-11-06):
  [ƥ join review](docs/italic-p-hook-join-review-2026-11-06.md).
  The next 15 Latin/phonetic Italic small caps are accepted unchanged
  (2026-11-06), including omega.sc shared with Greek:
  [Latin/phonetic small-cap review](docs/italic-smallcaps-phonetic-review-2026-11-06.md).
  The next 17 Greek forms are accepted: 14 unchanged, delta.sc and
  lambda.sc after matching their capitals' diagonal angles, theta.sc
  after rounding its counter from o.sc. Bold Italic regenerated:
  [Greek small-cap review](docs/italic-smallcaps-greek-review-2026-11-06.md).
  The final 40 Italic small-cap drafts, all Cyrillic, are accepted: 39
  unchanged, Ю.sc (uni044E.sc) after rebuilding from i.sc/o.sc with a
  lighter stem, fuller bowl and smooth lower-right join. This completes
  the Italic small-cap review:
  [Cyrillic small-cap review](docs/italic-smallcaps-cyrillic-review-2026-11-06.md).
  Bold Italic a.sc–z.sc are now accepted (2026-11-06): b.sc/q.sc's upper
  counters rounded, b.sc/d.sc's stems and serif brackets straightened
  locally; the rest unchanged:
  [Bold Italic Latin small-cap review](docs/bold-italic-smallcaps-latin-review-2026-11-06.md).
  The next 42 extended Latin forms are accepted: 38 unchanged, gamma and
  glottal small caps after paired Italic repairs, then Florin and ƥ.sc
  after the same-style reference reconstruction (2026-11-07):
  [Bold Italic extended Latin review](docs/bold-italic-smallcaps-extended-latin-review-2026-11-06.md).
  Both italic weights' full capital/small-cap Florin hooks and the Bold
  Italic ƥ.sc are approved, with local spacing corrections; Italic ƥ.sc
  retains its earlier approved drawing:
  [Astra hook review](docs/hook-reference-reset-review-2026-11-07.md).
  a.ipa, formerly on no sheet, now has
  a focused four-style review and proofs: [IPA a review](docs/ipa-a-review-2026-11-06.md).
  Accepted unchanged in all four styles (2026-11-06). The old-style
  figures now all have a recorded acceptance: the Bold Italic's
  2026-11-08, the Regular's 3 5 and the Bold's ten 2026-11-09 (the Bold
  4s' stems made upright: [old-style figures review](docs/oldstyle-figures-review-2026-11-09.md)).

## Review of the open items, 2026-11-09 (sheets in build/glyph-review/open-items/)

Verdicts given on the sheets; the fixes still to make:
- Bold Italic entry strokes: the inner turn of the entry hook into the
  left downstroke reverses its curvature, one shape in every letter
  that has it: u v w y ı ц ш щ и at (342, 685) only in the Bold Italic
  (the stroking's), n m r ŋ п т ɲ near (291-315, 600-665), doubling
  Old Standard's own at (314, 609). A fault of the family: in
  stroke_bold, not letter by letter. k q s z y (but for the entry) and
  г accepted as they are (2026-11-09). Done 2026-11-09 (FONTLOG):
  stroke_bold.one_way, the edge kept turning one way from the stem's
  line; the feet's exit hooks with it. Accepted from
  build/glyph-review/entry-strokes/family-plain.pdf and flagged-plain.pdf
  ("massive improvement"), but for: ſh (longs_h, not sure about the trace
  of the ball), ɯ ᵯ ɰ (uni026F uni1D6F uni0270: need further smoothing),
  their acceptance withdrawn. To do next (2026-11-10): those four.
- Bold f-ligatures (ff fi fl ffi ffl and those made of them, ﬀb ﬀh ...):
  "the fs are drawn not well, especially over the bar"; the stem after
  the arch leans (wider at its foot); ﬀh's shoulder kinked. Cause: the
  Regular's drawn ligatures emboldened whole. Decided 2026-11-09: drafted
  from the Bold's own f (draft_ligatures): ff fi ffi the Bold f side by
  side, fl ffl its arch at the Bold's weight into a straight stem, those
  before b h k t by f_ligature, the long-s ones as now; drafted 2026-11-09
  (FONTLOG), for review; fi fj ffi ffj's crossbar joined to the serif in
  the Regular and Bold (2026-11-09). All 30, the f- and long-s
  ligatures, approved 2026-11-09 (accepted.py).
- Steps: Regular 𝑙 (U+1D459) to smooth; ɉ's bar too short on the right;
  ɝ's hook badly attached; Italic Ⱦ not flat on top; ₮'s bars too short
  on the right, off centre; ⱦ.sc a step on top. Bold: ɉ's bar off
  centre; 𝑙 to smooth; ǥ's bar too short; ₿'s bars unequal, the right
  one odd at its top and bottom. Bold Italic: 𝑙 to smooth. 𝑙 in every
  style (draft_letterlike.py italic_l), ɉ in the Regular and Bold.
Seen and settled (2026-11-09): the Bold's serifs (ﬀb ﬀh ﬀt ſſl, Щ, m.sc
ɦ.sc, N M U against H) but for the f-ligatures; the Bold's hooks after
stem_handles (J ȷ ɽ ɳ Œ) and its middle tildes (ᵰ ᵭ's ends rounder
and tapered, done 2026-11-09, FONTLOG); the other
step candidates.

## Coverage: the end aim (2026-11-09)

Full IPA (with extIPA and the phonetic blocks) and Latin as wide as
Charis SIL's: then 980 Latin code points against Myia's 654, IPA and
phonetic 368 against 133 (Greek stays ahead: 333 against 23). First the
open review work above on what the font has; then the letters that
compose from existing glyphs (the Irish dotted Ḃ ḃ Ḟ ḟ Ṁ ṁ Ṗ ṗ, Ǆ ǅ ǆ
Ǉ-ǌ, ḁ ḉ ḝ), those derived like ɢ ʙ (the Uralic small capitals ᴀ ᴄ ᴆ ᴇ
...), and last the medievalist and Germanist blocks (Latin Extended-D,
-E), which need new drawing. `scripts/coverage.py` holds the current
target (TARGET); a new set goes in there when it is taken up.

## Ligatures still to make (2026-11-08)

None. Dropped 2026-11-09 after drafts: ch ck tz (from Fraktur, as in
Linux Libertine) and ſs. Reproducing Fraktur ligatures in a Didot did not
seem useful.

Done 2026-11-08 (FONTLOG): Th th tt, ſſb ſſh ſſk ſſt ſj ſſj, U+FB05
U+FB06; 2026-11-09: sp, Qu.

## Spacing: revisit only if specimens warrant it

Four Bold Italic pairs (`of`, `Wh`, `it`, `ba`) were reviewed on 2026-10-20
and retained despite tight measurements against references. They are not
unresolved repair tasks; reopen only on visual evidence.
