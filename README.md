# Myia Didot

An extended fork of [Theano Didot](https://github.com/akryukov/theano) by
Alexey Kryukov: a Didot-style face for Greek (polytonic), Latin and Cyrillic.

Goals:

- complete coverage of Latin-script alphabets, Greek, and basic Cyrillic;
- Regular, Italic, Bold and Bold Italic;
- true small capitals (`smcp`, `c2sc`) in every style.

Status: **Phase 2** done: Regular, Italic (from Old Standard), Bold and Bold Italic (derived), each with small caps. **Phase 3:** spacing and kerning comparisons, feature-table audits, and specimen proofs run for all four styles; every frequent Latin, Greek and Cyrillic pair lies within the reference fonts' range, but four reviewed ones in the Bold Italic. **Phase 4 is underway:** a Didot bold's contrast, clean construction of the derived styles, and hinting. All drafted glyphs are reviewed. See FONTLOG.txt.

## Project records

- [FONTLOG.txt](FONTLOG.txt): completed changes and validation history.
- [FONT-DESIGN.md](FONT-DESIGN.md): open drawing, spacing and hinting reviews.
- [DEVELOPMENT.md](DEVELOPMENT.md): open tooling and publication work.

## Layout

```
sources/MyiaDidot-Regular.ufo   master source (edit this)
sources/glyph-renames.json      afii* -> uniXXXX names applied at import
sources/upstream/               pinned upstream SFD + license, for reference
scripts/                        import, reference build, shaping comparison
proofs/proof.tex                LuaLaTeX visual proof
fonts/                          build output (otf, ttf, webfonts)
```

## Building

Requirements: [uv](https://docs.astral.sh/uv/), FontForge (for generated styles, reproduction and the
upstream reference/import), and LuaLaTeX for proofs. The hinting tools
(ttfautohint-py, afdko's otfautohint) come with the Python toolchain.
Python 3.12 is required in `pyproject.toml`, `.python-version` and CI: generated features and
regression baselines depend on its Unicode 15.0 character data.

```sh
make setup            # Python toolchain in .venv + git pre-commit hook
make                  # fonts/otf, fonts/ttf, fonts/webfonts (all hinted)
make release          # build/release/MyiaDidot-VERSION.zip (fonts, OFL, FONTLOG, checksums)
make test             # the regression test suite (also run on every commit)
make regress          # shaping diff against the last commit (REF=...)
make proof            # PDF proofs in build/proofs/
make proof-svg        # rendered SVG specimen sheets for all four styles
make pairs            # spacing/kerning comparison reports against pinned fonts
make qa               # full fontbakery reports in build/qa/
```

`make reimport FORCE=1` regenerates the UFO from the upstream SFD and
**overwrites all edits**. It was only needed for the initial import.

## Tests

`make test` runs before every commit (against the staged snapshot) and on GitHub Actions. It checks the UFO's integrity, that composites follow
the anchor rules, that precomposed and decomposed text render identically,
that no character is ever lost, a golden shaping corpus, a digest over
more than 2 million shaped strings per style, and fontbakery's universal profile.

Known exceptions are listed in `tests/data/*.txt` with a reason; those lists
only shrink. When a change is intended, regenerate the baselines with
`scripts/update_test_data.py`; review `build/baseline-review.json` and use
`--accept-report SHA256` for a changed shaping baseline, then review
`git diff tests/data`. Reference fonts and UDHR texts are pinned in
`scripts/data/reference-inputs.json`. CI provisions them before running
Greek and Cyrillic comparison tests.

## Shared glyph review skill

The `glyph-review` skill has one maintained copy in
[`skills/glyph-review/SKILL.md`](skills/glyph-review/SKILL.md), discovered through
relative symlinks in `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code).
It uses the existing project rules and checks, with a focused SVG proof renderer
for selected glyphs, optional before/after sources, anchors and shaped text.
It adds no hooks, global settings or model requirements.

Invoke it in Codex with `$glyph-review`, or in Claude Code with `/glyph-review`,
for example: “Review Italic r and ɽ against HEAD, with n/o for weight context.”
The same workflow can also be requested in plain language. A newly added skill
may require a new session before it appears in the agent's skill list.

## Claude Code plugin

`tools/claude-plugin/myia-didot` adds a status line (glyphs, characters
still missing, last test run, built fonts out of date), guards for the
pinned upstream sources, the test baselines and the generated styles, a
check for sync leftovers after bulk UFO writes, and the commands
`/font-status`, `/font-test`, `/font-proof` and `/font-pairs`. Install it
from a local checkout (edits to the folder take effect with
`/reload-plugins`):

```sh
claude plugin marketplace add /path/to/MyiaDidot
claude plugin install myia-didot@myia-didot
```

or from GitHub, in a Claude Code session:

```
/plugin install myia-didot --marketplace ghschaden/MyiaDidot
```

## License

SIL Open Font License 1.1, see [OFL.txt](OFL.txt). "Theano" is a Reserved
Font Name of the upstream fonts, which is why this fork has its own name.
