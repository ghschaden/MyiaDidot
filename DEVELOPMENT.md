# Open development and publication work

Current backlog, consolidated 2026-10-26. Font drawing, spacing and hinting
belong in [FONT-DESIGN.md](FONT-DESIGN.md). Record completed work in
[FONTLOG.txt](FONTLOG.txt), with detailed evidence linked where needed.

## Publication preparation

These are proposals from the repository-structure review, not implemented
features or prerequisites already agreed for a particular distribution.

- Add a versioned release archive target containing all intended font
  formats/styles, OFL, FONTLOG, installation instructions, a specimen and
  checksums. Keep archive preparation separate from publication.
- Lead README with the font, specimen, downloads, installation, script and
  feature support, and known limitations. Move detailed tooling/plugin
  instructions into linked development documentation.
- Add human-facing contributor documentation for source authority,
  generated styles, regeneration, checks and visual acceptance. Have agent
  instructions reference the same maintained rules.
- Group dated reviews and historical proof PDFs separately from general
  documentation and specimen sources, with an index and updated links.
- Define the relationship between Python project version `0.1.0`, font
  version `0.100`, release tags and archive names; check consistency across
  all four styles during release preparation.
- Add `sources/README.md` describing incorporated upstream materials,
  revisions, credits and licenses, distinguishing comparison-only inputs.

## Optional tooling follow-up

- Refine the hint-zone audit's classification of unencoded letter names.
  `Horn`/`horn` currently pass as sequences of H/h, o, r and n and generate
  misleading baseline reports. Preserve coverage of real unencoded letters
  and ligatures; confirm that the change cannot alter production hints
  unexpectedly, since the hint-control builder also consumes this audit.
  [Evidence](docs/horn-hinting-review-2026-10-26.md).

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
