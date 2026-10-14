# Myia Didot

An extended fork of [Theano Didot](https://github.com/akryukov/theano) by
Alexey Kryukov: a Didot-style face for Greek (polytonic), Latin and Cyrillic.

Goals:

- complete coverage of Latin-script alphabets, Greek, and basic Cyrillic;
- Regular, Italic, Bold and Bold Italic;
- true small capitals (`smcp`, `c2sc`) in every style.

Status: **Phase 0**. The upstream Regular has been converted to a UFO source
with a fontmake build, and shapes the same as the original.

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
uv sync               # Python toolchain in .venv
make                  # fonts/otf, fonts/ttf (hinted), fonts/webfonts
make compare          # shaping diff against the FontForge-built upstream
make qa               # fontbakery reports in build/qa/
lualatex --output-directory=build/proofs proofs/proof.tex
```

`make reimport FORCE=1` regenerates the UFO from the upstream SFD and
**overwrites all edits**. It was only needed for the initial import.

## License

SIL Open Font License 1.1, see [OFL.txt](OFL.txt). "Theano" is a Reserved
Font Name of the upstream fonts, which is why this fork has its own name.
