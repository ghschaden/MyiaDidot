# Upper-arch roles and historical splice diagnosis — 2026-10-30

Upper-counter discovery now resolves entry/interior/exit roles in the pinned
current Italic and Bold Italic n/m. The reconstructed bad m receives a local
interior-connection finding in both historical styles. This is a geometric
explanation of the misplaced lower curl, rather than the previous unresolved
similarity result. The extra upper entry projection remains undiagnosed.

## Evidence contract

`relationships/arches.py` and `--upper-arches` add a separate
`myiadidot-upper-arches-v1` report and `arches.svg` overlay. Candidate discovery
reflects the existing open-counter detector vertically, then discards its lower
roles. All reported arch geometry is restored to the deskewed font frame.
Reflection does not make upper and lower connections interchangeable.

Each counter arm is traced downward along its own contour. For each potential
left/right neighbour, horizontal sections are taken at 0.12, 0.16, 0.20, 0.24 and
0.28 em below the lower crown. First-hit, reverse-hit and ink checks must establish
an interval. At least three intervals must agree on **both endpoints** within
0.003 em to establish a shared band. Similar widths and proximity alone do not
establish sharing. Multiple neighbours leave the role unresolved.

These horizontal intervals are topology evidence, **not normal stroke-width
measurements**. The older near-crown normal-band statuses remain in the report;
failed normal checks are neither overridden nor converted into reusable geometry.
The upper report does not offer positive reuse matches or infer donor ancestry.

Roles require positive context:

- **Entry:** a bounded, verified left contour cap and a right shared-stem link.
- **Interior:** distinct shared-stem neighbours on both sides, without upper caps.
- **Exit:** a left shared-stem link and a right band linked to a lower capped
  return, with no following arch or observed below-floor context.

The lower link uses the same five heights, now measured above the lower turn.
Upper and lower arms are traced up to 0.6 em from their extrema; at least three
complete intervals must agree. This can establish the anatomical link while the
lower recogniser's stricter normal-width role remains unresolved. Its lower role,
cap verification and below-floor context are retained explicitly.

A lower return linked to a stem that also feeds a following arch produces a
`review-conflict`: `interior-terminal-conflict` when its cap verifies, otherwise
`interior-return-detour`. Neither requires pretending that the full upper role
is resolved. A normal final exit has no following arch and receives no conflict.
The finding identifies an interior terminal-like construction for inspection;
it is not a universal aesthetic rule, automatic repair or design rejection.

## Pinned evaluation and visual inspection

Current source revision remains `cef605f813e307acd419326bd6a4821cd5e10c64`.
The four previously verified frozen UFOs were read without modification. The
historical sources remain `e30747e339a18415e6a7c70fcb47ec7f13b55774`; candidate
UFOs are the prior pass's reconstructed artifacts, not the lost original JSON.
Their reconstruction and recipe hashes are recorded in
[the previous review](return-matching-review-2026-10-30.md).

Replay script, source/implementation hashes, reports and proofs are under
`build/glyph-review/upper-arches-2026-10-30/`. Run:

```sh
.venv/bin/python -I build/glyph-review/upper-arches-2026-10-30/evaluate.py
```

All six runs report `source_preserved=true`. The four current-style and both
historical PNG overlays were opened and inspected. Blue marks upper counter arms,
magenta counter clearances, green shared ink intervals, orange verified caps and
red the conflicting lower turn. These are source-outline proofs, not compiled
shaping or hinted rendering.

| Scope | Entry | Interior | Exit | Unresolved | Conflicts |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current Regular n/h/m/u/v/w | 0 | 0 | 0 | 4 | 0 |
| Current Italic n/h/m/u/v/w | 2 | 1 | 2 | 4 | 0 |
| Current Bold n/h/m/u/v/w | 0 | 0 | 0 | 4 | 0 |
| Current Bold Italic n/h/m/u/v/w | 2 | 1 | 2 | 4 | 0 |
| Historical Italic n/m/bad-m | 2 | 1 | 3 | 2 | 1 |
| Historical Bold Italic n/m/bad-m | 0 | 2 | 0 | 6 | 1 |

These are local observation counts, not a precision/recall evaluation.

- Current italic n has entry and exit arches; m adds a shared interior arch.
  Their observed lower exits occur on the final leg, with no interior conflict.
- Historical Italic bad-m has a lower capped curl on a stem feeding the following
  arch. Five common sections link that curl to the upper arm. Its other neighbour
  is missing, so the complete arch role stays unresolved even though the local
  conflict is diagnosed. The final exit is not flagged.
- Historical Bold Italic bad-m has a lower curl on the shared interior stem,
  also linked by five sections. The curl joins the following stroke and does not
  pass the bounded cap check. It is reported as an interior return detour, **not**
  a verified terminal cap. Normal historical m has the interior connection without
  this lower curl and receives no conflict.
- Upright m has a measured middle shared band, but serif entry/exit context is
  unsupported. h's ascender context is also unresolved even where its lower exit
  is observed. Those misses are retained.
- Italic u/v/w expose upper entry-like counter candidates, but no resolved roles
  or conflict findings. Upright u/v/w produce no upper candidates. This is not a
  proof of full anatomical coverage or an independent-family accuracy claim.

## Validation and limits

112 focused tests pass through `make test` with the shared six-worker lock.
Sixteen new tests cover contour reversal/start, deskewing and subdivision,
shared-band negatives, ink intervals stopping at counters, independent synthetic
entry/interior/exit constructions, capped and uncapped interior detours, a normal
final exit, missing geometry, read-only CLI output and glyph-scoped graph links.
Ruff and `git diff --check` pass.

The new detector is independent of glyph names, recipes and expected test labels.
However, these historical failures were development inputs; two explained
reconstructions do not qualify real-family precision. Intentional looping
interior constructions may need explicit context before interpreting a finding
as a defect. Closed counters, components, serif and ascender roles, upper-entry
projection diagnosis, lower-return interior coverage, tail attribution and a
held-out real-family corpus remain open. Stage 3 remains incomplete.

Production sources, generators, baselines and acceptance records were untouched.
No smoothing, repair, font build, full suite, reproduction, hinting or shaping run
was performed. No commit or publication was made.
