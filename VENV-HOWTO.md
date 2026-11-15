# Setting up a working copy on another computer

What this directory needs to build, generate, test and proof Myia Didot,
from a fresh machine. The Python side is pinned in `pyproject.toml` and
`uv.lock`; `uv sync` makes `.venv` from them exactly. The rest are system
tools.

## 1. System tools

| tool | for | check |
|---|---|---|
| git, make, `flock` (util-linux) | everything; `make test` / `make reproduce` take a lock with `flock` | `flock --version` |
| [uv](https://docs.astral.sh/uv/) | makes `.venv` (it fetches Python 3.12 itself if missing) | `uv --version` |
| FontForge **20251009** | only when an input of the Italic changes (Old Standard's SFD, a stale small-cap draft: `scripts/fontforge_inputs.py`), `make oldstand`, the upstream reference. Other versions draft small caps differently (Ubuntu's 20230101 leaves l.sc without ink at mid-height) | `fontforge -version` |
| TeX Live with XeLaTeX and LuaLaTeX (`fontspec`, `geometry`, `babel`, `xcolor`) | proofs and review sheets (`make proof`, `proofs/*.pdf`) | `xelatex --version` |
| poppler-utils (`pdfunite`, `pdftoppm`, `pdftotext`) | joining proofs, looking at them | `pdfunite -v` |
| librsvg (`rsvg-convert`) | `make proof-svg` and SVG sheets | `rsvg-convert --version` |

On Manjaro/Arch: `sudo pacman -S git make util-linux uv fontforge texlive-meta poppler librsvg`
(check that FontForge's version is 20251009, or build that release).
On Debian/Ubuntu: `apt install git make util-linux fontforge texlive-xetex texlive-luatex texlive-latex-extra poppler-utils librsvg2-bin`,
uv from its installer; Ubuntu's FontForge is older than 20251009 (see above).

The hinting tools (ttfautohint-py, afdko's otfautohint), fontmake,
fontbakery, diffenator2, uharfbuzz, skia-pathops, freetype-py and numpy
come with the Python environment; nothing to install for them.

## 2. The working copy and its environment

```sh
git clone git@github.com:ghschaden/MyiaDidot.git
cd MyiaDidot
make setup     # uv sync (Python 3.12 + every pinned package, ruff from the dev group) and the git hooks
```

`make setup` is `uv sync` plus `git config core.hooksPath tools/git-hooks`
(pre-commit runs the tests, post-commit rebuilds the proofs). Run Python as
`.venv/bin/python -I`, as the Makefile does.

**Python must be 3.12** (`.python-version`, `requires-python`): the
generated features and the regression baselines depend on its Unicode 15.0
character data; another minor version fails the tests. uv keeps to it.

After a `git pull` that changed `uv.lock`, run `uv sync` again.

## 3. What is fetched, not committed

- The reference fonts (`build/refs/`, about 40 files, SHA-256 pinned):
  `.venv/bin/python -I scripts/quality/fetch_refs.py`, or any target that
  needs them (`make pairs`, `make quality`). Without them the reference
  tests are skipped, not failed (`MYIA_REQUIRE_REFERENCES=1` makes them
  fail).
- The stroke cache: `~/.cache/myiadidot/strokes.sqlite`
  (`MYIA_STROKE_CACHE` puts it elsewhere). It starts empty, so the first
  `make generate` is slow (the Bold Italic several minutes); it is not
  needed for correct results.
- `build/` is all derived and is remade as needed; don't copy it over.

## 4. Check that it works

```sh
make otf                  # the four OTFs in fonts/otf
make test                 # the suite (a few minutes, 4 cores at most: JOBS)
make reproduce            # the generated styles match what the generators make
```

All three should pass on a clean checkout of `main`.

## 5. Per machine, outside the repository

- Git identity and commit signing: commits here are SSH-signed (through the
  1Password agent on the main machine); set `user.name`, `user.email`,
  `gpg.format ssh` and `user.signingkey` for the new machine.
- The Claude Code plugin (optional): `claude plugin install
  myia-didot@myia-didot` (CONTRIBUTING.md).
- Max 4 cores for generation and tests together (`JOBS`/`MYIA_JOBS`, 4 by
  default).
