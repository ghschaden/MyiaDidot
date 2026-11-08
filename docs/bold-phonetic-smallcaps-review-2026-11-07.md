# Bold phonetic and additional Latin small caps

The review reviewed the 15-form sheet at
build/glyph-review/bold-smallcaps-phonetic-2026-11-07/review.pdf and approved
13 unchanged forms, then the omega uppercase/sc and capital uniA7AA
aperture repairs, followed by the smoothed uni0266.sc hook. All 15 small
caps are approved. The four repaired drawings are installed in Bold and
marked drawn, tied to their Regular inputs. Approval date: 2026-11-07.

Retained proofs: proofs/bold-omega-hhook-2026-11-07.pdf and
proofs/bold-hhook-smooth-2026-11-07.pdf. The latter supersedes the former's
uni0266.sc drawing. Omega's lower opening is 120 units in the capital and
90 in the small cap. The hooked H forms have separate rounded terminals
and a gap before the right stem's upper serif. The final small-cap hook
arrives vertically at its stem and has no swelling on its inside edge.

Before/candidate/installed snapshots and geometry reports are under
build/glyph-review/bold-omega-hhook-2026-11-07/.
The four base edits also affect capital omega's aliases and accented forms:
24 decomposed outlines total (checks.json lists them). No advances or
anchors change. Outline lint passes for all four bases. All 51 small-cap
mappings passed with the first candidate compiled font (latn/en); the
subsequent change smooths only uni0266.sc without changing its mappings.
The proofs were visually inspected and represent source outlines rather
than hinted rendering. No commit or push has been made for this review.

Whole Bold regeneration followed by small-cap generation and normalization
preserved all four approved drawings exactly. One derived glyph changed:
uni01B1 (capital Latin upsilon), made by turning Omega. Its top opening
widens from 39 to 120 units; its bounds and advance stay the same. It is
included as a dependent comparison on the next review's second page and
has not been stamped as approved. No other decomposed glyph changes from
the installed snapshot. Acceptance/drawn-preservation checks pass (12 tests).
