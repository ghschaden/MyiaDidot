# Main Bold Italic stroke audit — 2026-10-28

Claude's new stroke construction improves the broad h/n/u shapes, but fewer
inflections do not mean curvature is continuous. The exit strokes are visibly
much thinner. Weight and join review should precede further automatic smoothing.

[Proof index](../build/glyph-review/main-stroke-audit/index.html) ·
[Full measurements](../build/glyph-review/main-stroke-audit/report.json).

`scripts/shape_main_audit.py` compares pinned committed main with a byte-verified
copy of the live Bold Italic UFO. The report records the revision and both UFO
hashes. Generator files are copied separately as provenance; their presence is
not proof that the uncommitted UFO reproduces from those files. All outputs stay
under build. Main was read only.

| Diagnostic | h | n | u | o |
|---|---:|---:|---:|---:|
| Interior inflections, committed → working | 6 → 3 | 10 → 5 | 8 → 6 | 2 → 2 |
| Largest near-smooth curvature jump, before | .04405 | .04307 | .04850 | .00175 |
| Largest near-smooth curvature jump, after | .04484 | .05476 | .07122 | .00228 |
| Resolved normal sections changing over 10% | 7/53 | 16/51 | 17/53 | 6/30 |
| Unresolved normal sections | 25 | 33 | 28 | 0 |
| Sampled clearance alerts | 8 | 14 | 14 | 1 |

Curvature jumps are in inverse font units, restricted to joins turning less
than 2 degrees; the table includes closing joins. No joins turn between 2 and
45 degrees in either version. Intentional corners and unresolved zero-length
edges are separately recorded. Counts exclude reversals across segment joins.
Thus tangent continuity looks good under this diagnostic, while curvature
continuity remains incomplete. The maxima are not necessarily at corresponding
locations in the two outlines.

The most extreme fixed-ray changes occur at the exit terminals near y=352:
h measures 176.4 → 86.7 units; n 177.8 → 48.2; u 177.7 → 44.6. These are fixed
sections through the old outline, not matched centreline thicknesses. Large
position changes and the many unresolved rays prohibit treating these figures
as exact percentage weight losses. The visible thinning in the proof is real,
but its optical desirability is a design decision. For o, all 30 rays resolve;
the largest change is 86.0 → 100.7 units near its lower outside curve.

The 32 deskewed scanlines flag gap reductions and changed interval counts.
Some large relative gap changes occur near closing counters or narrow crotches,
where small positional changes strongly affect the percentage. These are
locations to inspect, not evidence that counters have collapsed. No new outline
lint findings were found in the four glyphs and their component dependency
closures. A clean lint result does not override the weight or curvature findings.

Visually inspected the full before/after sheet with anchors, text-size repeats
and compiled English/Latin words, plus the enlarged n curvature comb. The new
n downstroke looks more regular; its entry and exit are appreciably lighter.
The words retain a coherent italic rhythm, with a changed distribution of dark
and light. The h/u/o comb sheets were generated but not separately inspected.

Recommended order of work:

1. Decide the intended weight of h/n/u exit terminals and n/u entry strokes.
   Confirm it at text size against the main downstrokes and o.
2. Inspect the remaining inner crowns and return joins. Control curvature over
   whole arcs after the desired weight is settled; preserve deliberate bends.
3. Recheck o's lower stroke and counter independently. Its unchanged count of
   two inflections alone is neither a success nor a rejection.

The former 10% local-change budget was for small repairs. It is useful here as
an alert threshold, not an acceptance gate for Claude's broader redesign.
No hinted rendering, full release suite or shaping-equality assertion was made;
width and anchor changes are intentional candidates for review. Ruff passes.
The end-to-end audit, compiled proof generation and lint sweep completed.

Reproduce with the shared lock:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  flock /home/gerhard/src/MyiaDidot/.git/myia-validate.lock \
  .venv/bin/python -I scripts/shape_main_audit.py
```
