# Remaining Bold Italic lint entries, 2026-10-24

Reviewed the seven entries after ɽ and its small cap. The
[four-style sheet](../proofs/remaining-bold-italic-lint-review-2026-10-24.pdf)
shows the drawings before this pass's aleph repair, with enlarged marked
regions. This continues the lint review, not the separate ɸ weight or
dollar drawing work.

## Aleph repair

The [aleph before/after sheet](../proofs/bold-italic-aleph-before-after-2026-10-24.pdf)
shows two small backward turns in the weighted lower tip. The original
Italic has a continuous curve here. In Bold Italic, weighting introduced
both a three-unit straight return at 749,19 → 746,18 and another curved
return near 748,57 → 740,59. Removing only the straight edge left the
second irregularity; the final drawing replaces the complete local run
from 719,-6 to 740,59 with one cubic.

`scripts/aleph.py` keeps the first handle at 721,3 and places the second
at 729,22. The final join follows the existing outgoing tangent (11,37).
The lower-tip pass preserves all points outside that run. The generated-style writer
applies the repair after rounding. An independent Astra review checked
the actual Italic construction and the full enlarged terminal, including
the second return that the first small repair left behind.

The checker preserves ℵ through `LEDGE_KEEP`; its generic comment refers
to the roman mathematical reference. The Italic glyph is from Old Standard,
so this rule alone does not establish that its weighted local returns are
deliberate. The independent review compares the actual Italic source.
Regular and Bold terminal findings remain outside this repair. Removed
the single Bold Italic ledge exception. The lower-tip pass needed no
quality or shaping baseline changes.

Comparison against a snapshot immediately before this task (including the
completed r-family work) finds exactly one changed outline and CFF
charstring: `uni2135`. All advances, anchors, kerning, groups, feature text,
and compiled `hmtx`, `GPOS`, `GSUB`, `GDEF`, `cmap`, `OS/2` and `hhea` tables
are identical. Other styles are unchanged.

## Upper-right join follow-up

The person accepted the central and lower-left drawing and identified a
remaining fault where the lower edge of the upper-right terminal joins
the stem. The [follow-up proof](../proofs/bold-italic-aleph-upper-join-before-after-2026-10-24.pdf)
compares this local correction against the already repaired lower-tip
version.

The outline reversed left from 978,588 to 919,596, then right to 929,606
before turning left again. This formed a visible spur. Below it, two
short curves through 855,574 produced an inward S-shaped wiggle on the
connector edge. The revised join replaces the reversal with a smooth
cubic to 929,606 and the connector with a single fair curve ending at
850,478. The final handle at 864,514 and the following central line to
883,424 are preserved, as are all points outside this upper local run.
The central and lower-left shapes, previous lower-tip correction,
advances and anchors remain unchanged.

Astra compared a spur-only trial, a version retaining every interior node,
and a merged connector. The merged version avoids both the old wiggle and
the angular turn forced by the redundant interior node.

The upper change is confined to x843.33–978, y478–606, and overall glyph
bounds remain identical. Only `uni2135` changes relative to the previously
accepted lower-tip version; all metrics/layout tables match. The 7-unit
neck bulge at 855,574 disappears, so the existing quality exception shrinks
from four extrema to three. No new exceptions or shaping baselines change.

Follow-up validation: **31 focused checks pass**, including three repair
regressions, the prior r-family regressions, Bold Italic lint/quality/UFO,
composites, shaping goldens/full digest, and TrueType/CFF hinting. CFF runs
with required helper-socket access. Independent full Bold Italic generation
and smallcaps match the master; the production hinted OTF rebuild passes.
Ruff, source sync and whitespace checks pass. Logs and the new proof source:
`build/aleph-upper-join-review/`.

## Other six entries

| Glyph | Finding | Observed construction |
| --- | --- | --- |
| ʸ | 527,619; 30 pixels | Narrow open lower crotch of the italic y construction. |
| ң | 514,-151; 43 pixels | Tapered open counter between the descender curl and stem. |
| ᵍ | 476,595; 36 pixels | Open lower bowl/stem crotch of the italic single-storey g. |
| ᶤ | 498,773; 32 pixels | Open slot beside the bar where it crosses the curved stem. |
| ₡ | 1256,836; 50 pixels | Tapered counter between the slash and the upper C terminal. |
| ⱥ.sc | 269,164; 31 pixels | Tapered lower counter where the slash crosses the small-cap A foot. |

The four-style comparison distinguishes these open counters from residual
pinholes or small attachment steps. Modifier letters ʸ, ᵍ and ᶤ use the
superior-letter recipes based on y, ɡ and ɨ, calibrated to the superior
figures. The Cyrillic descender is the explicit hooked construction used
in this italic family. The currency and small-cap counters are formed by
crossing strokes. Filling these white wedges would change the intended
negative space rather than remove a stray point.

Recommendation: retain these six drawings and their existing exception
keys for this lint pass. Refreshed the annotations and measurements without
adding exceptions. These are review recommendations, not recorded user
acceptance or resolution of separate optical-weight/quality findings.

Independent Astra inspection supports retaining the six open joins for
this pass and identified the second aleph return, which the final repair
removes. The repaired ink stays within x719–749, y−6–59; overall glyph
bounds are unchanged.

Validation: **30 focused checks pass**, including the two repair tests,
six prior r-family regressions, Bold Italic lint/quality/UFO/composites,
shaping goldens and full corpus digest, and TrueType/CFF hinting. CFF was
run separately with helper-socket access after the sandbox blocked it on
the first proposal. The final candidate passes both runs. A fresh full
Bold Italic generation plus smallcaps matches the master exactly. The
production Bold Italic OTF rebuild succeeds with hints and STAT metadata.
Compiled comparison, Ruff, source sync and whitespace checks pass.
Working sources, renders and logs: `build/remaining-lint-review/`.
