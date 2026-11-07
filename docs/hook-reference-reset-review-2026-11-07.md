# Florin and P-hook reference reset — accepted 2026-11-07

The new drawings replace the rejected ellipse-and-ball construction with
curves taken from finished letters in the same style. The person accepted
the final proposals and requested commit/push on 2026-11-07. The five drawings
and 13 local small-cap kerning values are installed, marked drawn and accepted.
Reference: working sources on `7eb071e0`, including the
already accepted small-cap, gamma and glottal changes present on 2026-11-07.

## Drawing decisions

The rejected v8 Florin had a visible shoulder below its straight stem and a
horizontal, shoe-like curl. The new capital and small-cap Florins use their
final same-style `F` / `f.sc` bodies and the continuous descending gesture of
that style's lowercase `florin`. The terminal alone is reduced optically to
78% about its inner return; the main descending stroke retains its full
weight. Clipping seams are removed, and the tail's initial handles follow the
F stem. Capital depth remains -292 and small-cap depth -224. These are local
drawings, with no shared fitting changes.

Bold Italic `uni01A5.sc` uses the final `p.sc` body and counter, with the
already approved `uni0253.sc` upper-left head fitted to its stem. This gives
an open eye, compact terminal and continuous head, retaining the P's stem
weight. Italic `uni01A5.sc` is exactly unchanged, as requested.

## Review artifacts

All artifacts below are under `build/glyph-review/hooks-reference-reset/`:

- `bold-final.svg` / `.png`: enlarged before/after, including capital Florin,
  Florin small cap and P-hook small cap.
- `italic-final.svg` / `.png`: the matching Italic comparison.
- `bold-context.svg` / `.png`, `italic-context.svg` / `.png`: compiled English
  Latin shaping with `smcp`, including H/O/A/Q neighbours and repeated hooks.
- `bold-final.ufo`, `italic-final.ufo`: the candidates used in those proofs.
- `checks-final.json`, `check_candidates.py`: focused checks and reproducible
  checks script.
- **Use `bold-spaced-context.svg` / `.png` and `italic-spaced-context.svg` /
  `.png` for the final review.** These show the same outlines with the local
  pair corrections described below; `bold-spaced.ufo` / `italic-spaced.ufo`
  are their sources.
- `spacing-adjustments.json`, `space_candidates.py`: exact original overlap
  areas/boxes and the pair correction calculations.
- `spaced-context-checks.json`, `check_spacing.py`: the final 110-pair check.

The final enlarged and context PNGs were inspected. The reset improves the
continuity of Florin's descent and avoids the pasted-on terminal of the v8
P-hook. Accepted before/after proofs are retained at
`proofs/bold-italic-hooks-reference-repair-2026-11-07.svg` and
`proofs/italic-hooks-reference-repair-2026-11-07.svg`.

Recreate candidates with `scripts/hook_reference_candidates.py --source UFO
--out build/.../candidate.ufo`, adding `--bold` for Bold Italic. The script
refuses scratch outputs outside `build/`. `--install --source REVIEWED.ufo`
installs only these hooks, marks them drawn, records acceptance, and applies
the generator-owned local small-cap kerning. Install Italic before Bold
Italic so the latter's drawn records fingerprint the final Italic sources.
It does not touch gamma/glottal or invoke the previous rejected hook script.

## Checks and limitations

Only three Bold Italic glyphs and two Italic glyphs differ from current
production sources: `uni0191`, `florin.sc`, and Bold Italic `uni01A5.sc`.
All advances are retained. Italic P-hook and both styles' approved gamma and
glottal are exactly unchanged. Focused outline lint is clean on all six
reviewed glyph/style combinations.

Construction diagnostics find no defects in the newly joined tail curves.
Installation projects one short handle by one unit in each of Italic
`florin.sc` and Bold Italic `uni01A5.sc` to align inherited base-stem tangents
(2.4 and 2.7 degrees respectively). These are whole-unit rounding repairs
inside the new drawings; the underlying `f.sc` and `p.sc` are unchanged.
The unchanged Italic P retains its existing findings.

The initial focused contexts found three contacts at existing small-cap spacing:
Bold Italic `a.sc + florin.sc` (831 square units of overlap), Bold Italic
`q.sc + florin.sc` (1876), and Italic `q.sc + florin.sc` (5577). All three
pairs were clear before. A full basic Latin small-cap predecessor sweep also
found Bold Italic `e/h/i/k/l/m/r/x/z + florin.sc`, and Italic
`r.sc + florin.sc`. All 13 pairs were clear before; the narrow contacts in
most Bold pairs occur where the terminal rises 11 units above the baseline
and meets the preceding foot serif. Capital Q + Florin and repeated Florins are clear.
Italic `n.sc + uni01A5.sc` has the same pre-existing 274-square-unit contact
before and after; its requested original drawing was preserved. These are
exact source-ink intersections positioned with compiled HarfBuzz advances
and offsets, not a raster estimate. The context images also show the Q
contacts. The `*-final.ufo` sources retain production spacing for diagnosis.

A separate `*-spaced.ufo` pair corrects these 13 contacts without changing
any glyph outline, advance or anchor. Each pair uses the first integer shift
that removes the intersection, plus 16 units of clearance. Bold Italic adds
116/54/52/52/101/72/56/44/56/86/31 units after `a/e/h/i/k/l/m/q/r/x/z.sc`;
Italic adds 73/29 after `q/r.sc`. All those pairs previously had effective
kerning zero. Their production owner is the style-keyed `SMALLCAP_KERNING`
dictionary in `scripts/smallcaps.py`, applied after capital-pair scaling.
The earlier style-generator dictionaries are unsuitable because the
small-cap scaling stage erases and rebuilds all `.sc` pairs. There are no
global spacing or group changes.

The final spaced context proofs were rendered and inspected. The full basic
Latin small-cap alphabet before and after `florin.sc`, repeated small-cap
and capital Florins, and capital Q + Florin produce no outline intersections:
55 compiled pairs per style, 110 total. Italic's unchanged P contact is
reported separately above and is not part of that Florin clearance claim.

Whole Italic and Bold Italic styles are regenerated with the shared lock
and at most four workers, then normalized. The final broad test,
reproduction and commit checks are handled in the parent integration task.
This subtask does not commit or push.

## Final integration

The parent completed whole-style regeneration and inspected the installed
proofs after normalization. Those final proofs replace the candidate copies
under `proofs/`. The Bold capital Florin's short clipping remnant is merged
with its preceding tail curve, preserving endpoint tangents and staying within
2.41 units of the approved arc; this removes a six-degree local reversal.
No shared fitting rule changes. The approved outlines otherwise remain as
reviewed, with the one-unit inherited-handle alignments described above.

The barred-D small cap is rebuilt from the final approved d.sc. Its bar
intersection introduced three rounding diagnostics; a local finishing pass
removes a collinear fragment and aligns two joins, without changing its
advance. It is kept drawn, with both its Italic source fingerprint and its
same-style d.sc dependency recorded. A regression checks the D stem and bowl
against its final base at four heights clear of the bar, within two units.

Fifteen focused case-reference/small-cap regressions pass. The final quality
audit reports no new or stale findings in either italic weight; eight resolved
quality exceptions are removed and none added. Ruff, whitespace and source-sync
checks pass. Full tests and reproduction run as mandatory pre-commit gates on
the exact staged tree. `commit-scope.json` in the scratch folder records the
complete change scope against the preceding commit: only the reviewed glyphs
and their component dependants, the two gamma advances, and 13 local kerns.
Features and kerning groups are unchanged.

The baseline updater reviewed 2,119,735 corpus strings per italic weight with
zero differences from HEAD; both full-corpus digests remain unchanged. The
golden small-cap sample changes only its two gamma advances: 876 to 1040 in
Italic, and 958 to 1094 in Bold Italic. These are the approved spacing repair.
The complete reports are retained in the scratch folder as
`italic-baseline-review.json` and `bold-italic-baseline-review.json`, with report
digests `01168e1124ebadad4f46030d0bdbd66b467fd50a857ae338e4a502af74f557e2`
and `4fea14171768d63b1fe192c1aaf490739742867227af45da1e3fca3da3172aea`.
