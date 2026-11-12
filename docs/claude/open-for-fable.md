# Gaps found carrying out redraw.md

## Italic Greek lowercase batch (Sonnet, 2026-11-12)

Fit of 25 letters: 14 candidates at once, 5 more after one spec entry each,
6 still failing the gate (beta eta phi chi psi mugreek).

- **`bent_back` at an inflection extra node (eta 777,-302 and 765,229; psi
  778,576 and 563,-409).** redraw.md covers a stem edge drawn as a curve
  (`line`), but here the flagged node is an inflection the tool put on an
  S-shaped descender; `line` is refused ("no node within 15 units", the
  node is not an old one) and `extra` at the same place changes nothing.
  Missing: what to do with a bend-back at a node the tool itself made.
- **`line` refused for beta 192,-531 (6.5 units off its chord) and phi
  517,-47 (136 units)**: those are real curves; the doc's "look for the
  same in descenders (ρ φ р ф)" does not say what next. ρ passed untouched.
- **chi**: 622,-309 is 6.3 units off; an `extra` there brings it to 4.2
  (limit 4) at another place (541,-389), and the bend-back at 510,58
  (1.22 degrees, a corner next to a short line) stays. No entry found.
- **mugreek**: fails `extreme 731,-23 5 units past`; the doc has no entry
  for an extreme the gate wants a node at.
- **A spec point on an off-curve point crashes** ("operands could not be
  broadcast together with shapes (201,1) (4,2)") instead of being refused
  as "no node there". Tool bug, cheap to mend; the bend-back messages
  give the curve's start node, but beta/phi/mugreek spec points I tried
  were handles.
- alpha and lambda pass only with the tolerance widened by the tool itself
  (2.8): the doc says not to raise `tol` for one glyph, yet the tool does
  it unasked and reports it only as a remark.
