# Approved Bold drawings and Bold Italic C hooks

The person approved all Bold small-cap and remaining draft review batches,
and the first 39 Bold Italic extended Latin drafts. This change installs
those drawings, records 178 new Bold and 39 new Bold Italic acceptances,
and retains the final PDF proofs and individual review documents.

Compared with 26eca0dd: Regular and Italic outlines are unchanged. Bold has
23 directly changed outlines and 49 changed decomposed outlines, including
accented/aliased J and omega forms and capital Latin upsilon. Bold Italic
has two changed outlines, uni0187 and uni0188. No anchors, kerning, groups
or feature code changes. The only advance change is Bold uni0187, 1411 to
1507 units, accommodating its approved larger hook.

Broad shaping comparison covers 2,119,735 strings per affected style.
Bold Italic has no changed shaping. Bold has 2,924 changed strings, all
with the approved Ƈ advance increase; attached marks compensate their
relative x offsets by -96, preserving their absolute positions on Ƈ.
The complete Bold JSON report was checked and accepted using its SHA-256
through update_test_data.py; only Bold's golden/digest baselines change.
The exact review identity is recorded with the final validation log under
build/glyph-review/approved-fonts-commit-2026-11-08/.

Final geometry cleanup splits theta's inner oval at extrema and rounds
it to whole units, aligns a two-unit jog and tangent in derived barred J,
and aligns two small handles at Bold Italic Ƈ's hook attachment. The
before/after proof is proofs/bold-final-outline-cleanup-2026-11-08.pdf.
It was visually inspected against the approved drawings. Extents and
advances are retained. Acceptance fingerprints match the installed forms.

Quality inventories shrink: 12 Bold and two Bold Italic entries removed,
four existing Bold counts reduced, and four obsolete whole-emboldening
entries removed. No new diagnostic exceptions are added. Local finished
drawings are marked drawn and tied to the relevant Regular/Italic input.

Three sync-renamed Bold files (c_t, delta.sc, gamma.sc) were preserved in
a scratch backup and restored to their listed filenames before checking.
The synchronization check passes. Full tests and regeneration are enforced
by the commit hook; logs and the four-style scope audit remain under
build/glyph-review/approved-fonts-commit-2026-11-08/.
