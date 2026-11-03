# Myia Didot — notes for Codex

Two agents work on this repository at the same time, each in its own
working copy (git worktree) of the same repository:

| folder | branch | who |
|---|---|---|
| `~/src/MyiaDidot` | `main` | Claude (font sources, generators, tests) |
| `~/src/MyiaDidot-shapes` | `shape-grammar` | Codex (the shape grammar) |

If you are in `~/src/MyiaDidot` (branch `main`), stop and work in
`~/src/MyiaDidot-shapes` instead.

## Rules for the shape-grammar worktree

- Work and commit only on branch `shape-grammar`, only in
  `~/src/MyiaDidot-shapes`. Never check out, commit to, rebase, reset or
  push `main`, and never write into `~/src/MyiaDidot`.
- The shape grammar is experimental: production sources are read-only
  inputs. Do not change `sources/*.ufo`, `sources/upstream/`, the
  generators (`scripts/make_*.py`, `derive.py`, ...) or test baselines in
  `tests/data/`. Write outputs under `build/` only.
- Bringing work into `main` is the person's decision: they merge, or ask
  Claude to. To pick up new work from `main`, `git merge main` on your
  branch (not rebase of shared history).
- At most 4 CPU cores (the person, 2026-11-03), for both agents together. Run the suite with
  `make test` and reproduction with `make reproduce`: both take a lock
  shared by both working copies, so only one runs at a time, on 4
  workers. Do not run `pytest -n auto`, or several test runs at once.
- Commits run the pre-commit checks (`tools/git-hooks`): they take the same
  lock, and may wait for a run in the other working copy. Do not commit
  with `--no-verify`.
- `.venv` is shared with `~/src/MyiaDidot` (a link): do not install,
  upgrade or remove packages in it; ask the person.
- Project rules otherwise as in `CLAUDE.md` and `docs/claude/` (Python as
  `.venv/bin/python -I`, `make normalize` after any UFO change).
