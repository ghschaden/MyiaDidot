# Italic ƥ hook/stem join — 2026-11-06

The review reported a slight swelling where lowercase ƥ's hook meets the
stem and clarified that the style was Italic. Reference: `6e0fba21`, with
the subsequent acceptance metadata for 43 extended Latin small caps.
Before snapshots are under `build/glyph-review/p-hook-join/`.

The short joining curves made the upright stem widen from about 111 units
to 119 at y=1150. The local repair continues both straight stem sides to
the curl and aligns its handles with them. The join is now 111 units wide.
The Italic bowl counter, curl terminal, advance (1037), and overall extents
are retained. `scripts/p_hook_join.py` records the construction; the glyph
is marked drawn so regeneration preserves it.

The dependent Bold Italic was regenerated as a whole style. Only uni01A5
changed geometrically; its former hook/stem step is gone. Local tangent
and extrema finishing is marked drawn with the new Italic fingerprint.
Its advance (1064) and attachment anchors are retained; the regenerated
hook rises 21 units higher. Features, kerning and groups are unchanged.
An initial validation found a one-unit anchor shift caused by positioning
the outline; that shift was corrected without changing a shaping baseline.
The obsolete Bold Italic quality exception for the join step was removed.

Proofs:

- [Accepted Italic before/after](../proofs/italic-p-hook-join-2026-11-06.pdf).
- [Enlarged upright join](../build/glyph-review/p-hook-join/join-closeup.png).
- [Dependent Bold Italic](../build/glyph-review/p-hook-join/bold-italic-dependent.png).

The source proofs were visually inspected at enlarged and text sizes.
They are outline proofs, not pixel hinting proofs. The scope report at
`build/glyph-review/p-hook-join/scope.json` confirms that only uni01A5
changed in each italic weight, both advances are retained, the Italic
counter is identical, and all recorded acceptance fingerprints are valid.
The focused join test verifies continuous width and retention of the curl.
The final full suite passed: 369 passed, 7 skipped. Outline lint found no
issues in either revised glyph; Ruff and the source sync check also passed.
Final `make reproduce`: Italic, Bold and Bold Italic all as generated.

The review accepted the new Italic ƥ on 2026-11-06 (“new p is accepted”);
its acceptance stamp refers to this review. The dependent Bold Italic
was subsequently accepted after the weight follow-up below. The 43 small-cap approvals are recorded
separately in the extended Latin review; their drawings did not change.

## Bold Italic weight follow-up

The review found the hook lighter than the p stem and authorized either
smoothing the transition or thickening the hook. The rising stroke is now
about 218–220 units wide (formerly about 174–176) and its outer edge runs
continuously from the p stem. The short shoulder at y=698 is removed.
The curl ball, bowl counter, advance, anchors and overall bounds are
retained. The accepted Italic remains unchanged. The review approved this
Bold Italic revision on 2026-11-06; its acceptance stamp refers to this review.

[Updated before/after with same-style p](../build/glyph-review/p-hook-join/bold-italic-weight.png)
was visually inspected at enlarged and text sizes. Construction checks
report no smoothness, kink, step, grid or extrema findings.
After this follow-up, `make test` passed (369 passed, 7 skipped), and
`make reproduce` reports all three generated styles as generated.
The [accepted Bold Italic proof](../proofs/bold-italic-p-hook-weight-2026-11-06.pdf)
is retained with the review.
