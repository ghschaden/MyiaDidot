# Open development and publication work

Current backlog, consolidated 2026-10-26. Font drawing, spacing and hinting
belong in [FONT-DESIGN.md](FONT-DESIGN.md). Record completed work in
[FONTLOG.txt](FONTLOG.txt), with detailed evidence linked where needed.

## Publication preparation

These are proposals from the repository-structure review, not implemented
features or prerequisites already agreed for a particular distribution.

- A specimen image for README.md (from `make proof-svg`), and its download
  link once the first release is published.
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
  one segment more; fl, ſl). Make that step deterministic across machines
  (the rounding where K's point lands on .5, the segment split) or accept a
  one-unit tolerance in scripts/check_reproducible.py; CI green before the
  0.900 release.

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
