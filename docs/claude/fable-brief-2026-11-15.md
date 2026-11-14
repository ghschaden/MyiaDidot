# Fable, Sunday 2026-11-15: the brief

One 5-hour window, perhaps two; after it there is no more Fable. Written
on Opus (2026-11-14) so that the window starts writing, not searching.
The same rules as TODO.md's "How these sessions are run": files before
sheets, the loops to font-runner and font-measure, one review round per
item, what is left over written down for Opus.

## The order

1. **The redraw method's gaps from the Greek batch** (about 2-3 h). This
   decides whether phases 5-8's batches can be done on Sonnet at all.
2. **Phase 6's measure, specified** (about 1.5 h, reading and writing only).
   The only method still without a document.
3. **If there is a second window: one measure for upright kerning**
   (open-for-fable.md, "Phase 2": the gap and the share measures disagree
   in direction for R v w y, R O Q, A“, 7. 1. 1, W v w, and on the Bold
   Italic's f r on 2026-11-14).

Not for Fable (Opus has them, or the designer): the other entries of
`docs/claude/open-for-fable.md` (T2's, T5's, phase 3's, the collision
sweep's are records with the method already mended; the italics' `„`,
the italic t as an ascender, "spacing or pair" are the designer's).

## 1. The redraw method: β η φ χ ψ μ

Read: `docs/claude/redraw.md` (the method; "Faults seen and their
fixes", "When the method does not cover a case"), the first section of
`docs/claude/open-for-fable.md` (Sonnet's notes on the six), and the gate
output of the six as they stand today: `docs/claude/fable/greek-gate-2026-11-14.txt`.
The tool: `scripts/redraw.py` (spec entries in
`scripts/data/redraw-Italic.json`: extra, drop, corner, smooth, keep,
line, tol; none set yet for these six). The Italic's other 18 Greek
lowercase were redrawn and approved on
`proofs/italic-greek-lowercase-redraw-2026-11-12.pdf` (commit 6e3e0859).

What is missing, as Sonnet found it:

- a bend-back at a node the tool made itself (an inflection on an
  S-shaped descender: η, ψ); `line` is refused there and `extra` changes
  nothing;
- `line` refused on real curves (β's descender 6.5 units off its chord,
  φ's 136): the doc's "look for the same in descenders" has no next step;
- χ: an `extra` moves the excess to another place (4.2 for a limit of 4),
  and a 1.2-degree bend-back by a short line stays;
- μ: an extreme the gate wants a node at, with no entry in the doc;
- the tool widens `tol` by itself for α and λ (to 2.8) though the doc
  says not to raise it for one glyph.

Mended on Opus before Sunday (so not Fable's): the crash Sonnet saw was
an `extra` on a node the structure already has (β's 192,-531, where the
gate names the bend-back), not a handle; it is refused by name now. So
the gate's bend-back message points at a node an extra cannot help:
part of the first gap above.

The gate output's JSON (every report in full) is in
`build/fable/greek-gate-2026-11-14.json` (not in git; made again by the
command in the .txt's first line).

Wanted at the end: redraw.md's entries for these cases (what to do, in
the order a Sonnet session would try them), any change to the tool they
need (with a test in tests/test_redraw.py), and the six fitted on a sheet
for the designer. If one of them is better handed back to the designer
than fitted, the doc's "Hand back" section says so with the reason.

## 2. Phase 6's measure: the Italic against the Regular

TODO.md, phase 6, first step: "One sheet Regular beside Italic, measured
and seen: ball terminals (c a f r y against the Regular's), serif length
and thickness, hairlines, colour (about 5 % lighter) and width (about 5 %
narrower), x-height overshoots. What reads as another typeface is changed
in the core set; the italic capitals' contrast stays (declined 2026-10-21,
2026-11-02)."

Wanted: `docs/claude/italic.md` (or a section of redraw.md), as F4's
`docs/claude/bold.md` did for the Bold: what is measured and on which
letters, against which references (the italics in build/refs/: Old
Standard, Bodoni Moda, Libre Bodoni, EB Garamond; Libertinus and Charis),
on what scale (lengths over the style's own stem, as bold_targets.py
does), what counts as "another typeface" as a number (the gate), the
sheet's layout, and which of the faults go to the core set's recipes and
which to make_italic's shared machinery. Opus writes the script from it.

What already measures part of it (read the docstrings, not the code):

| tool | measures | note |
|---|---|---|
| `scripts/quality/bold_measures.py` | counter area, aperture, join, ball, width gain of a regular and its bold, against the references' pairs | F4's; `--italic` pairs Italic and Bold Italic. A Regular → Italic pairing is the likeliest base. |
| `scripts/quality/bold_targets.py` | each measure on the font's own scale, the references' range | F4's table |
| `scripts/quality/strokes.py` | each glyph's main stroke against its kind | per style |
| `scripts/quality/colour.py` | zone colour and side space per character against the references | per style |
| `scripts/quality/evenness.py` | grey along lines of text | per style |
| `scripts/quality/zones.py` | overshoots against the zones | per UFO |
| `scripts/quality/transitions.py` | thick-thin rhythm round the round letters | per style, Didot references |

Known numbers (TODO.md's assessment, 2026-11-10): Regular lowercase stems
164, hairlines 48 (of 2048); the Italic about 5 % lighter and 5 % narrower.
The Italic's core set is redrawn on clean nodes since 2026-11-10 to 12
(a-z, A-Z, O Q, Greek and Cyrillic lowercase but for β η φ χ ψ μ).

Keep: the italic capitals' Old Standard contrast (thinner hairlines
declined twice). Reference fonts are a calibrated range, not a target.

## 3. One measure for upright kerning (second window only)

Read: `docs/claude/open-for-fable.md`, "Phase 2"; `docs/claude/spacing.md`,
"The italics' Latin kerning"; `scripts/italic_kerning.py` (share: white
over the case's rhythm) and `scripts/quality/pairs.py` (gap over n n, the
x-height band). The case of 2026-11-14 (TODO.md phase 3, the Bold
Italic's hand kerns): f r -95 is in range by one, too tight by the other.
Wanted: which measure decides, or how the two combine, written into
spacing.md, so that phase 2's open pairs can be set on Sonnet.
