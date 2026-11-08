# Building and contributing

For the font itself, see [README.md](README.md). Open work:
[FONT-DESIGN.md](FONT-DESIGN.md) (drawing, spacing, hinting) and
[DEVELOPMENT.md](DEVELOPMENT.md) (tooling, publication). Completed work is
logged in [FONTLOG.txt](FONTLOG.txt).

## Layout

```
sources/MyiaDidot-Regular.ufo   master source (edit this)
sources/MyiaDidot-Italic.ufo    generated from the Regular and Old Standard Italic
sources/MyiaDidot-Bold*.ufo     generated from the Regular and the Italic
sources/glyph-renames.json      afii* -> uniXXXX names applied at import
sources/upstream/               pinned upstream SFD + license, for reference
scripts/                        generators, checks, import, proofs
proofs/                         LuaLaTeX proof sources and review proofs
fonts/                          build output (otf, ttf, webfonts)
```

The Italic, Bold and Bold Italic are generated (`make generate`). Change
them through the Regular or through their generators
(`scripts/make_italic.py`, `scripts/make_bold.py`), never in the generated
UFOs, or the next run undoes the change. `make reproduce` lists what a
regeneration would change.

## Building

Requirements: [uv](https://docs.astral.sh/uv/), FontForge (for generated
styles, reproduction and the upstream reference/import), and LuaLaTeX for
proofs. The hinting tools (ttfautohint-py, afdko's otfautohint) come with
the Python toolchain. Python 3.12 is required in `pyproject.toml`,
`.python-version` and CI: generated features and regression baselines
depend on its Unicode 15.0 character data.

```sh
make setup            # Python toolchain in .venv + git pre-commit hook
make                  # fonts/otf, fonts/ttf, fonts/webfonts (all hinted)
make generate         # regenerate Italic, Bold and Bold Italic
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

`make test` runs before every commit (against the staged snapshot) and on
GitHub Actions. It checks the UFO's integrity, that composites follow the
anchor rules, that precomposed and decomposed text render identically,
that no character is ever lost, a golden shaping corpus, a digest over
more than 2 million shaped strings per style, and fontbakery's universal
profile.

Known exceptions are listed in `tests/data/*.txt` with a reason; those
lists only shrink. When a change is intended, regenerate the baselines
with `scripts/update_test_data.py`; review `build/baseline-review.json`
and use `--accept-report SHA256` for a changed shaping baseline, then
review `git diff tests/data`. Reference fonts and UDHR texts are pinned in
`scripts/data/reference-inputs.json`. CI provisions them before running
Greek and Cyrillic comparison tests.

## Shared glyph review skill

The `glyph-review` skill has one maintained copy in
[`skills/glyph-review/SKILL.md`](skills/glyph-review/SKILL.md), discovered
through relative symlinks in `.agents/skills/` (Codex) and
`.claude/skills/` (Claude Code). It uses the existing project rules and
checks, with a focused SVG proof renderer for selected glyphs, optional
before/after sources, anchors and shaped text. It adds no hooks, global
settings or model requirements.

Invoke it in Codex with `$glyph-review`, or in Claude Code with
`/glyph-review`, for example: “Review Italic r and ɽ against HEAD, with
n/o for weight context.” The same workflow can also be requested in plain
language. A newly added skill may require a new session before it appears
in the agent's skill list.

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
