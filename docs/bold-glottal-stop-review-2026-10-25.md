# Bold modifier glottal stop, 2026-10-25

The next unreviewed lint entry was Bold ˀ (`uni02C0`, U+02C0 MODIFIER
LETTER GLOTTAL STOP). The [actual-outline comparison](../proofs/bold-glottal-stop-review-2026-10-25.pdf)
shows its Regular/Bold source family, enlarged modifier outlines, upper
join details and a scratch rebuild from the final Bold base.

## Retain the open-cusp finding

The current finding is `notch 222,1097 47 px`. It falls at the upper end
of the open counter, where the ball terminal joins the bowl. Regular has
the same construction, with a wider opening that does not trigger the
notch detector. The surrounding ink belongs to one contour; this is not
a detached part, enclosed pinhole or failed attachment.

The derivation chain in `scripts/derive.py` is question → ʔ (remove dot
and extend stem) → ɂ (resize to lowercase) → ˀ (superior recipe, calibrated
against zero/zerosuperior). The Bold generator weights modifier letters
at their own scale. This acute white counter tip is inherited from that
ball-and-bowl construction and becomes narrower under weighting.

As a diagnostic, the existing superior recipe was applied in memory to
the final Bold ɂ. This scratch outline has a rounded outer bowl and ball,
but still has one notch: `184,1093 55 px`. Simply rebuilding the base does
not eliminate the open cusp. The scratch glyph was never saved into a
master or production font.

Recommendation: retain the existing `uni02C0 notch 1` key and its open
counter. Refreshed the comment and measurement only. This records a
review recommendation, not the person's final visual acceptance.

## Separate drawing candidate remains open

The current Bold modifier's outer bowl and ball have sharp corners, and
its inner bowl edge wavers. The enlarged proof exposes these differences
from Regular, the full-size Bold base and the smoother scratch outline.
They are distinct from the inherited upper counter tip and should receive
a separate drawing/weight pass through the generator.

The scratch rebuild is a comparison, not a finished repair: its advance
is 380 units versus the current 449 (Regular is 363). A repair must address
curve quality and optical weight while deliberately preserving or
reviewing spacing. The existing Bold quality findings for an extremum
and width are unchanged. No outline or generator edits were made here.

## Validation

All four style cases in `tests/test_glyph_lint.py` pass. `git diff --check`
passes, and the generated one-page PDF was visually inspected.

Direct lint checks cover question, ʔ, ɂ and ˀ in all four styles: only
the current Bold modifier has a finding. The scratch recipe also retains
one notch, as described above. No exception keys, font outlines,
advances, anchors, shaping baselines or production fonts were changed.

Proof source and full spot measurements:
`build/bold-glottal-review/proof.py` and
`build/bold-glottal-review/measurements.txt`.

Next unreviewed lint entry: Bold ℵ (`uni2135`), four ledges. The modifier
drawing candidate, dollar drawing and ɸ optical weight remain separate.
