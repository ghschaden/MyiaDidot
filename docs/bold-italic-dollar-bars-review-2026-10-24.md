# Bold Italic dollar bar correction, 2026-10-24

[Before/after proof](../proofs/bold-italic-dollar-bars-before-after-2026-10-24.pdf)
shows the whole dollar and an enlarged lower ball/through-stroke clearance.

The user identified that the two bars were not straight. Whole emboldening
had moved the bar edges by different amounts at their intersections with
the bowls: the top-right and bottom-left protrusions were almost vertical,
and the space between the bars narrowed sharply near the bowls. The earlier
[terminal review](dollar-terminal-review-2026-10-24.md) inspected only the
lower ball's open channel and missed these wider construction errors.

`scripts/dollar_bars.py`, called by the Bold generator's final writer,
aligns all sixteen exposed edge segments to four common 15-degree lines.
The angle follows the inherited terminal positions. Both bars are 86
units wide horizontally, separated by a 95-unit clear gap. The four line
origins are ten units right of the previous bottom terminals: retaining
those terminals exactly would bring the newly straight left edge too close
to the lower ball. The proof shows the chosen placement preserves the
open channel.

The small bowl arcs between bar edges expand with their endpoints. Where
a bar meets a longer bowl curve, only the adjoining handle follows the
endpoint; the rest of that curve stays in place. The two ball terminals,
all vertical coordinates, five-contour topology, advance of 1290, anchors,
Unicode and glyph metadata are preserved. No other style is processed.

Validation:

- Every exposed edge endpoint lies within half a font unit of its common
  line after integer rounding. Four segments belong to each edge; both
  bar widths and the clear gap remain constant. The saved previous glyph
  fails this measurement, and the repaired glyph passes.
- The helper reproduces the checked-in dollar from the previous outline,
  is idempotent and leaves Regular, Bold and Italic unchanged. Regression
  tests also check the untouched ball curves, vertical coordinates and
  metadata.
- Dollar now has no glyph-lint findings. The obsolete `dollar notch 1`
  exception was removed; no checker thresholds changed.
- Compiling before and after changes only the dollar CFF charstring.
  `hmtx`, `cmap`, `GSUB`, `GPOS` and `GDEF` are byte-identical.
- The two focused regression tests and all sixteen Bold Italic quality,
  glyph-lint, UFO integrity and shaping regression checks pass. Ruff and
  whitespace checks pass.
- A complete Bold Italic generation from the current Italic, followed by
  `smallcaps.py`, matches the checked-in font exactly: outlines, advances,
  anchors, glyph metadata, kerning, groups, features and font library.
- Bold Italic TrueType hinting and all four styles' CFF hinting checks
  pass. The CFF check was rerun outside the sandbox because the autohinter
  requires a local multiprocessing socket; its initial blocked run did
  not report a font defect.

The historical terminal proof remains as a record of the earlier drawing;
the linked before/after proof above records the repaired bars.
