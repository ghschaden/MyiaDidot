# Bold Italic comparison with main — 2026-10-28

Claude's work supersedes the planned repair of the old h return. Committed
main at 411eae10 already changes its lower-return handles, enables Bold Italic
keep_bends and rebuilds the o/O/zero ovals. The main working copy additionally
contains an uncommitted stroke-based construction, including changed h/n/u/o.
Its style notes describe stroke-section weights smoothed along outlines.
The committed and uncommitted states must not be conflated.

[Comparison sheets](../build/glyph-review/main-comparison/index.html) and
[measurement report](../build/glyph-review/main-comparison/report.json).
The report pins the byte hashes of each UFO read; hashes were checked before
and after loading. No main files were written and no branch was merged.

| Whole-glyph interior inflections | Our baseline | Committed main | Main working copy | Our scratch |
|---|---:|---:|---:|---:|
| h | 7 | 6 | 3 | 6 |
| o | 4 | 2 | 2 | 0 |
| n | 10 | 10 | 5 | 10 |
| u | 10 | 8 | 6 | 10 |

Counts are analytic within-segment sign changes, not visual defect counts or
cross-join reversal counts. They differ from the earlier study's counts over
only the replaced arc. Our scratch o uses 28 total segments against 10 in
both versions of main; its lower count of inflections does not establish a
better production construction.

The working h is materially different: advance 1064 versus 1076 in our baseline,
and right bound 1019 versus 1067. Its outline uses 24 segments versus our
baseline's 26 and scratch's 30. Working n/u advances are 1175 rather than1198.
Working o advances 978 rather than our baseline's 967 (committed main: 966).
These width changes need contextual review; they are not automatically defects.

Visually inspected the working-h comparison. The downstroke and lower return
have changed substantially, making another fit to our old return obsolete.
Other comparison sheets are generated but not individually inspected. No
compiled shaping, hinting or full regression tests were run on Claude's live
working sources. The worktree may continue changing after the recorded snapshot.

The next useful experiment is to assess the new stroke-based h/n/u construction
with our curvature-continuity, local thickness and clearance checks. Retain
our h/o scratch work as comparative evidence, rather than transplanting its
old-baseline curves into the newer drawing. This comparison resolves the
planned old-return task by identifying its replacement in ongoing main work;
it does not claim that all new curves have been accepted or validated.
