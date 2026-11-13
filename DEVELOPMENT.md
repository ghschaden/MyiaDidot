# Open development and publication work

Current backlog, consolidated 2026-10-26. Font drawing, spacing and hinting
belong in [FONT-DESIGN.md](FONT-DESIGN.md). Record completed work in
[FONTLOG.txt](FONTLOG.txt), with detailed evidence linked where needed.

## Publication preparation

These are proposals from the repository-structure review, not implemented
features or prerequisites already agreed for a particular distribution.

- README.md's download link, once the first release is published (the
  specimen: docs/specimen.svg, remade by scripts/specimen.py).
- Add human-facing contributor documentation for source authority,
  generated styles, regeneration, checks and visual acceptance. Have agent
  instructions reference the same maintained rules.
- Group dated reviews and historical proof PDFs separately from general
  documentation and specimen sources, with an index and updated links.
- Add `sources/README.md` describing incorporated upstream materials,
  revisions, credits and licenses, distinguishing comparison-only inputs.

- CI's `make reproduce` fails since cb9b7dac (2026-11-08) while it passes
  locally: on GitHub's runner the Bold Italic rerun rounds 12 glyphs a unit
  or a segment otherwise (K Κ Ķ Ǩ Ḱ Ḳ Ḵ at (1193, 1170); ae.sc, ǽ.sc, ǣ.sc
  one segment more; fl, ſl). Cause narrowed 2026-11-13 (TODO.md, F5): only
  AMD runners with AVX-512 (EPYC 9V74, 9V45) make it otherwise, Intel's
  with AVX-512 and AMD's without never; a library's own CPU dispatch past
  scripts/arithmetic.py's pins (OpenBLAS the likeliest). Not pursued
  further: the probe (scripts/arith_probe.py, workflow probe.yml) found no
  environment pin that helps, and a tolerance would not cover it. Since
  2026-11-13 CI's reproduce step reports without failing on those runners
  (a warning; .github/workflows/test.yml), and fails as before elsewhere.

## Shape-grammar studies (branch `shape-grammar`, not merged)

Codex's research branch (6 commits to f963d62e, about 15,000 lines of
studies, previews and tests; worktree `~/src/MyiaDidot-shapes`) changes no
glyph and is not part of a release (decided 2026-11-08). It stays
unmerged. Its handoff, docs/shape-grammar-handoff-2026-10-31.md, names
the one production step worth taking after 0.900: the generators writing a
construction manifest (base, transform and operations per derived
letter), U→Ɯ and u→ʉ first, built on `main` rather than merged from the
branch. Its studies are pinned to the sources of 2026-10-31 and must be
rerun before they say anything about later ones.

## Optional tooling follow-up

The earlier suggestion of a formatter/type checker was exploratory. Ruff
linting is implemented; current project policy deliberately avoids automatic
formatting of aligned recipe tables. Consider targeted type checking only
where it would catch useful errors, as a separate decision.

## Backlog maintenance

Keep only open tasks here. When closing one, move its outcome and relevant
validation to FONTLOG rather than accumulating progress reports. Detailed
review documents may retain historical evidence, clearly dated. Do not
reopen the completed pipeline recommendations from the former REC.md or
RECOMMENDATIONS.md without new evidence; their completion is logged.
