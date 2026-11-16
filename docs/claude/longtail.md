# The long tail: the quality lists by family

Written 2026-11-15 on Fable, for phases 6, 7 and 8 (TODO.md), which all
say "by family" of what is left in `tests/data/quality-*.txt` and nowhere
what the families are. The lists hold 1,980 lines (Regular 256, Italic
624, Bold 487, Bold Italic 613). Worked line by line that is months;
sorted by where a line is mended it is about twenty pieces of work, half
of which need no drawing. `scripts/quality/families.py` does the sort
and is run again whenever the lists have moved; this page says what
each family's mend is, which are checked and which only proposed, and
the order.

Nothing in the sources was changed for this page. Two things were
mended on the way because the sort showed them: the zone check's
reference in the italics (below, "The check's own"), and the redraw
gate's name for a step (`docs/claude/redraw.md`).

## The sort

    .venv/bin/python -I scripts/quality/families.py                       the four tables
    .venv/bin/python -I scripts/quality/families.py --style Italic --family smallcap --names
    .venv/bin/python -I scripts/quality/families.py --clusters --names    the design kinds by what they say

Each line gets one family, the first of these that applies:

| family | the line is | mended |
|---|---|---|
| `parent` | on the same glyph with the same kind in the list of the style this one is made from (the Regular for the Italic and the Bold, the Italic for the Bold Italic) | there; here nothing |
| `base` | on a glyph built from one that has the kind in this list (the recipe's `builtFrom`, components, a small cap's letter and capital, a ligature's letters) | in the base; the line falls when the style is generated again |
| `verdict` | of a design kind (stroke, slant, zone, weight, width, accent, base, stem, advance, style) | not an outline fault: a decision, by cluster |
| `kept` | of a construction kind (kink, smooth, extreme, step, wobble) on a glyph marked drawn in this style | on the letter (`scripts/drawn.py` lists them) |
| `marks` | ... on a mark the Italic slopes from the Regular | in the slanting |
| `smallcap` | ... on a small cap | in the drafting |
| `recipe` | ... on a derived letter; the table names the operation | in the operation or the recipe |
| `ligature` | ... on a ligature or other draft | `draft_ligatures.py`, `italic_ligatures.py` |
| `letter` | ... on a letter taken as it comes: Old Standard's, the Regular's own or sloped, an emboldened or stroked one | redrawn (the italics), phases 7 and 8 (the bolds) |

The numbers of 2026-11-15, lines:

| | Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|
| parent | | 106 | 176 | 358 |
| base | 70 | 163 | 96 | 50 |
| verdict | 87 | 135 | 43 | 22 |
| letter | 28 | 79 | 82 | 83 |
| recipe | 53 | 44 | 64 | 67 |
| smallcap | 14 | 57 | 15 | 15 |
| marks | | 35 | | 5 |
| ligature | 4 | | 5 | 7 |
| kept | | 5 | 6 | 6 |

What the sort is and is not:

- **A family is where to look first, not a proof.** `base` says only
  that a base has a line of the same kind, not that it is the same
  fault: ƥ.sc has kinks and so has o.sc, yet ƥ.sc's may sit in its hook.
  Before a base is mended for its followers' sake, look at one
  follower's places (the list's reason gives them: "913,902 6.4
  degrees") against the base's.
- **A line that outlives its family's mend moves to the next family.**
  After the base is clean a follower's kink is its recipe's; the sort
  says so by itself on the next run.
- **More than half of the three generated lists is not theirs.** Of the
  Bold Italic's 613 lines 358 stand in the Italic's too and 50 more on
  a base: 205 are its own. Of the Bold's 487, 215 are its own; of the
  Italic's 624, 355. No session should open a `parent` line in the
  style it was found in.
- The `parent` rule compares glyph and kind, not the place. For the
  Bold Italic's glyphs marked drawn that is too generous (a drawn
  glyph does not follow the Italic): read those by hand, there are 59.

## The check's own (mended 2026-11-15)

Three clusters of the design kinds said the same thing in 25 Italic and
25 Bold Italic lines: `zone bottom +23 from -23`, on r and every letter
with a flat serifed foot (ɪ ʀ ʁ ʏ ʙ ʜ ʟ, the turned letters). The check
took the lowercase's flat bottom from x's lowest point, and the
italics' x n u l end in exit hooks as deep as o's overshoot (-23): the
letters standing on the baseline were measured as 23 off. `checks.zones`
measures the lowercase from the baseline now (0, as the capitals and
small caps always were); 23 lines gone from each italic list, 4
shortened by one finding, nothing new, the Regular and the Bold
unchanged. One line went that was not wrong: ʘ, O's overshoot at -35 in
the lowercase, is further than the check's 30 units from the baseline
now; the Regular and the Bold keep its line, where the decision is
recorded.

The rule this gives: **when a cluster of a design kind holds many
letters with the same offset, suspect the reference before the
letters.** `--clusters` exists to show that.

## The families, with their mends

In the order of "lines removed for the work it takes". "Checked" means
the cause was read from the code or measured on 2026-11-15; "proposed"
means it follows from the sort and wants its trial.

### 1. The italics' marks without their extremes (checked; Opus, small)

Italic `marks extreme` 33 lines, 58 findings; the Bold Italic's 32
lines are their `parent` lines. Cedilla, ogonek, hook, horn, ring,
breve, the Greek breathings: curves 5 to 13 units past their ends with
no node there. `make_italic` slants a letter with `shear(...,
extremes=True)`, which splits the curves the slant moves past their
points (`derive.with_extremes`, since 2026-10-26); the marks are sloped
by a plain transformation (`sloped(0)`, with ITALIC_HORN's and
ITALIC_MARK_SCALE's scaling: the block under "Myia's accents, sloped
about the height they sit at") and never pass through it.

Mend: the sloped mark through `with_extremes(..., past=EXTREME_PAST)`
as the letters. The outline does not move, only nodes are added, so
anchors, composites and the NFD forms stay; proofs: `make reproduce`
lists the marks and what holds them as components and nothing else,
`redraw_sweep.py` shows 0 units for all of them, `make diffenator`
empty. Then the 33 and 32 lines deleted. The marks also pass the redraw
gate as they are (Cedilla 17 -> 12 nodes, Hook, Ogonek, Ring, breve,
horn fitted dry), but a generator's fault is mended in the generator.

### 2. The Italic's Old Standard letters not yet redrawn (checked; Sonnet)

Italic `letter` kink 36, smooth 32, extreme 10, step 1: 79 lines on 68
glyphs. 33 of them are in the core set and fall with phase 5's
remaining batches, which were fitted dry on 2026-11-15 (redraw.md, "The
rest of the core set fitted dry": 104 of 107 candidates as they are).
The other 35 are Old Standard's letters outside the core set:

    Aogonek Aringacute Iogonek Oogonek Eng eng Tbar florin cent infinity trademark
    twosuperior fivesuperior sevensuperior eightsuperior ninesuperior
    uni0374 uni03DD uni03DF uni1FBE u1D510 u1D513 uni2135
    uni0409 uni040F uni0452 uni0459 uni045A uni045B uni045F uni0462 uni046B uni0474 uni0475 uni0491

They are redrawn by the same method in two batches after the core set
(Latin and signs; Cyrillic: Љ Џ ђ љ њ ћ џ Ѣ ѫ Ѵ ѵ ґ). A decision
first for Ą Į Ǫ: they are Old Standard's letter and ogonek in one
outline, while the A I O beside them are redrawn; fitted as they stand
they keep the old letter (hand back: made of the redrawn letter and the
ogonek, or fitted). 𝔐 𝔓 ℵ are upright mathematical letters: last, and
only if the designer wants them touched.

The Bold Italic's lines on the same glyphs are `parent` lines and fall
with them.

### 3. The italic small caps: FontForge's drafts (checked; trial proposed, Opus)

Italic `smallcap` kink 28 lines (88 findings), smooth 27, extreme 2,
and most of `base smallcap` (kink 37 lines, 112 findings: accented and
derived small caps on those). The largest family of the four lists.
The capitals they are drafted from are clean since 2026-11-12; the
kinks are FontForge's: the stored raw drafts
(`sources/drafts/Italic-smallcaps.ufo`) hold them as smooth nodes that
break by 2 to 9 degrees (ψ.sc 13 of them, ω.sc 10), and the weighting
and rounding after (`weight_thick`, `as_capitals`) keep the nodes.

Tried dry on twelve of the Italic's small caps as they stand (a c ψ ω
v r x y з e k b): ten pass the redraw gate with no spec entry, e.sc
fails by a quarter of a unit (4.25 at 723,658) and b.sc by a bend-back
in a 28-unit curve (from 327,931). So the fit holds for the family.
Two ways, to be decided on a trial:

- **In the generator** (preferred: 142 drafts, and a redrawn small cap
  marked drawn would stop following its capital): the raw draft fitted
  once when it is drafted, where `fontforge_inputs.drafts` stores it
  with the hash of its inputs, so the 12 s a glyph are paid only when a
  capital changes. A draft that fails the gate is stored as FontForge
  made it and named in the log. Trial: the twelve above through that
  path into a scratch UFO (`make_italic --out`), the sheet before |
  after at 144 pt and in a line of small caps at 12 pt, the quality
  lines that fall counted. What to watch: `as_capitals` weights after
  the draft, and `bowl_counters`, `stem_joins` and `sc_feet` finish the
  small caps later; the fit has to come before all of them, on the raw
  draft, or it fits their repairs away.
- **As batches** (`redraw.py --install` on the final small caps, marked
  drawn): only for the few the generator's fit refuses.

The Regular's and the Bold's small caps are another matter (14 and 15
lines, `smallcaps_draft.py`'s own drafts): too few for a family mend,
by letter.

### 4. The Bold's curves past their ends (checked; trial proposed, Opus)

Bold `letter extreme` 28 lines, `base` 19 more, `recipe` 6,
`smallcap` 3: 56 lines, none in the Regular (its list has no `extreme`
line at all). The emboldening moves a curve's two ends by different
amounts (the thick side by AX, the hairline by AY: f's and ſ's hook 9
units, r's ball 8, β η φ ψ, Ж К Л and their lowercase 6 to 10), and
unlike the italics' slant nothing splits the curve after.

Mend proposed: `with_extremes` on the emboldened outline where a curve
stands more than EXTREME_PAST beyond its points, as `slant_back` does
for the Bold Italic. To weigh before it is taken: phase 7 keeps the
Bold on the Regular's node structure "point for point comparable", and
this adds a node to each such curve (about 60 glyphs, one or two
nodes). The designer's or Opus's call; the alternative is to accept the
family as designed (T9's status word) since a curve 5 to 10 units past
its ends renders the same.

### 5. The design kinds, by cluster (the designer; Sonnet makes the sheets)

`verdict` and the design lines under `parent` and `base`: 434 lines in
the Regular and the Italic (129 and 305), which decide for most of the
bolds' 439. `--clusters
--names` groups them by what they say; a cluster is one question for
the designer, answered once for all its letters and recorded with T9's
status word (`designed`, `accepted`, `candidate`) on each line. The
clusters with five lines and more:

| cluster | lines | reading (to be confirmed on a sheet) |
|---|---|---|
| Italic `stroke Latin lc lighter` with `weight` b d k l p q | 46 + 6 | the Italic's ascender and descender stems are lighter than n's: l 149 against 195 at half the x-height, k 162, b 161, p 168, d q 171; f ſ t 150 to 160 against 183. Not in italic.md's first run: its stem is the median of i l n m h u, which the x-height letters decide. **For phase 6's sheet**, before any single line is judged |
| Regular `stroke Greek lc lighter` | 19 | the Greek lowercase is drawn lighter than n (α δ γ ι π ρ τ ...): one decision |
| Italic and Bold Italic `slant past the angle` | 39 | n u m ı and what is made of them (19.7 degrees for 15.2), и п т ц ш щ, v w y: the entry strokes and diagonals read as stems by the measure; the family is the letter n's, see redraw.md's hand-back list |
| Italic `slant upright of the angle` | 28 | C G S, c.sc g.sc s.sc and their followers (11.7 to 13.1 degrees): rounds, measured on what the check takes for a stem |
| small caps `zone top +3` / `+4 from 1040` | 14 in every style | j.sc u.sc v.sc w.sc and their kin a little over the height: one decision, the Regular's |
| Italic `zone bottom -23 from 0` | 8 | M R Ж К Я: capitals with a hooked leg as deep as the lowercase's hooks: Old Standard's, one decision |
| Italic `zone top -24 from 884` | 8 | ι μ л м љ ѫ: entry strokes starting under the x-height: the same |
| Italic `zone top +23 from 884` | 6 | ɐ ɒ ɥ ɯ ɰ ʍ: turned letters, their hooks now on top: designed by construction |
| Bold `width` | 27 | punctuation and small signs (. , ! ' ‘ ’ ʼ ː ′) narrower than the Bold's usual gain: one decision |
| Regular `stroke Latin lc lighter` | 13 | ǀ ǁ ǂ ʔ ʕ ʡ ʢ and g ƒ: the click and glottal letters' thin strokes |
| `stroke other lc` / `uc lighter` | 6 + 4 | the old-style 3 5 7 8 and the lining 1 2 4 7 (with ℓ ℶ): with phase 4's review |

The singles (about 20 a style) are judged with the letter they stand
on.

### 6. The derived letters, by operation (proposed; Opus for an operation, Sonnet for a recipe)

`recipe`: Regular 53, Italic 44, Bold 64, Bold Italic 67 lines. The
table names the recipe's operation. Read it by this rule: **five lines
or more of one kind on one operation in one style is the operation's
question** (derive.py, allowed by the rule of 2026-11-03 since a whole
family shares it); fewer is the single recipe's numbers. The
operations that reach five:

| style | operation, kind | lines | where to look |
|---|---|---|---|
| Regular | `enlarge` smooth 7, kink 6 | 13 | a letter scaled to the other case and weighted (Ɣ Ɩ ɂ ɢ ɤ ɶ ʛ): the Bold and both italics inherit by `parent` and `base` |
| Regular | `attach` kink 7, smooth 5 | 12 | where the piece meets the letter (Ɲ Ʈ ɞ ʑ Ϗ Ʝ ⁂) |
| Regular | `hook` smooth 5 | 5 | Ɓ Ɗ Ƒ Ƥ Ɦ: one hook on five capitals |
| Italic | `attach` kink 12 | 12 | ƃ Ƈ Ɠ ɭ ɰ ɺ ʈ ң ҷ Ɽ Ⱳ Ꞵ |
| Italic | `curl` kink 5, `hook` kink 5 | 10 | Ɓ Ɗ Ƙ Ƥ ƴ, ƙ ƭ ɓ ɠ ɦ |
| Bold | `slash` kink 5, smooth 3, wobble 3 | 11 | ȼ Ⱦ ⱦ ⱥ ∅ ƛ Ȼ: the slash on the emboldened letter |
| Bold | `superior` wobble 6 | 6 | small glyphs emboldened at their scale |
| Bold | `attach` kink 7, `hook` kink 6 | 13 | as the Regular's |
| Bold Italic | `bar` kink 5, wobble 5, smooth 4 | 15 | Ǥ ǥ ғ ө ᵽ ɍ ʢ ұ ꟈ: the bar on the stroked letter (ITALIC_BOLD_REBUILD) |
| Bold Italic | `attach` wobble 8, `superior` wobble 7 | 15 | the stroker on pieces and small glyphs |

For each: three of its letters rendered at the places the list names;
if they show one thing, the operation is mended and the family
regenerated; if three things, the lines go back to their recipes.

### 7. The bolds' own letters (phases 7 and 8)

- Bold `letter wobble` 42, with 62 more on bases (21 of them the
  f-ligatures on f): the emboldening's bulges. In the core set: a f g r η þ and ſ; Ж К Л Љ ж к л љ (one
  leg, eight glyphs: look at one); ξ ζ ϵ; the Fraktur and ℓ. Phase 7's
  batches for the core letters; a rule only if the leg is one fault.
- Bold Italic `letter wobble` 39: G J Q h ı fi fl and г к л н п ц ю є
  are stroked from letters redrawn onto clean nodes, so these 15 are
  the answer to phase 8's "what the clean input alone gives": the
  stroker's, on clean input. The other 24 are stroked from Old
  Standard's nodes and are judged after family 2.
- Bold Italic `letter extreme` 24: J ц щ, ff ffi ffl: the stroked hook
  past its end (redraw.md, "After the six Greek letters": χ's was
  mended on the letter). Seven glyphs with one fault: the stroker's
  hooks want their extreme's node, in `stroke_bold` or as family 4
  does it.

### 8. What is left

`kept` (17 lines: the Italic's λ.sc o.sc q.sc θ.sc ƥ, drawn and still
kinked: on the letter), `ligature` (16: the Regular's ſſb ſſh ſſk and
Th, a few in the bolds), the Regular's own `letter` lines (28: kinks on
the f-ligatures with ascenders fb fh fk ffb ffh ffk ſb ſh ſk, on the
Fraktur 𝔐 𝔓 𝔖 and ℓ 𝑙; smooth nodes that break on 6 9 φ ϑ ẞ and a few
signs). The Regular's are worth a session before the release: it is
the master, and its lines come back in the other three as `parent`
lines.

## The order

1. Family 1 (marks): Opus, an hour, 65 lines, no shape moves.
2. Family 2 with phase 5's batches: Sonnet, as planned.
3. Family 5's sheets for the designer, the Italic's stems first, since
   it belongs to phase 6's review that is waiting anyway.
4. Family 3's trial (small caps): Opus; about 150 lines in the Italic
   and what follows in the Bold Italic.
5. The Regular's own lines (8) and its operations (6): Opus.
6. Family 4 (the Bold's extremes): after the designer's word on the
   node structure.
7. Family 7 with phases 7 and 8.

## How a session works one family

1. `families.py --style S --family F --kind K --names`: the glyphs.
2. Three of them rendered small at the places their lines name (the
   reason's coordinates); for a design cluster the sheet
   (`scripts/quality/strokes.py --sheet`, `make proof` pages).
3. One cause: mend it at the family's place, `make generate`
   (font-runner), `make reproduce`, the sweep for side effects
   (`redraw_sweep.py`, `make diffenator`, `make regress`) before any
   list is touched.
4. The lines that fell deleted with `update_test_data.py --quality`
   and a reason naming the family; the count before and after into
   TODO.md under the phase.
5. Lines that did not fall are left, and the sort run again says where
   they now belong. No line is deleted because its family was
   "handled".

## For T9

T9's status word belongs to the `verdict` lines first: a cluster
answered by the designer gets `designed` or `accepted` on each of its
lines in one edit, and what `scripts/status.py` then counts as open is
the construction families above. `families.sort()` returns the rows
(style, glyph, kind, family, lineage, operation, script) for it to
read.
