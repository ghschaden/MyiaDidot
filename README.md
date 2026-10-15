# Myia Didot

An extended fork of [Theano Didot](https://github.com/akryukov/theano) by
Alexey Kryukov: a Didot-style face for Greek (polytonic), Latin and Cyrillic.

Goals:

- complete coverage of Latin-script alphabets, Greek, and basic Cyrillic;
- Regular, Italic, Bold and Bold Italic;
- true small capitals (`smcp`, `c2sc`) in every style.

Status: **Phase 2** (Bold derived, Italic from Old Standard; Bold Italic next). See FONTLOG.txt.

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

Requirements: [uv](https://docs.astral.sh/uv/), FontForge (only for the
upstream reference/import), ttfautohint, and LuaLaTeX for proofs.

```sh
make setup            # Python toolchain in .venv + git pre-commit hook
make                  # fonts/otf, fonts/ttf (hinted), fonts/webfonts
make test             # the regression test suite (also run on every commit)
make regress          # shaping diff against the last commit (REF=...)
make proof            # PDF proofs in build/proofs/
make qa               # full fontbakery reports in build/qa/
```

`make reimport FORCE=1` regenerates the UFO from the upstream SFD and
**overwrites all edits**. It was only needed for the initial import.

## Tests

`make test` runs in about 12 seconds, before every commit (pre-commit hook)
and on GitHub Actions. It checks the UFO's integrity, that composites follow
the anchor rules, that precomposed and decomposed text render identically,
that no character is ever lost, a golden shaping corpus, a digest over
~1.2 million shaped strings, and fontbakery's universal profile.

Known exceptions are listed in `tests/data/*.txt` with a reason; those lists
only shrink. When a change is intended, regenerate the baselines with
`scripts/update_test_data.py` and review `git diff tests/data`.

## Claude Code plugin

`tools/claude-plugin/myia-didot` adds a status line (glyphs, characters
still missing, last test run), guards for the pinned upstream sources and
the test baselines, and the commands `/font-status`, `/font-test` and
`/font-proof`. Install it from a local checkout (edits to the folder take
effect with `/reload-plugins`):

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
