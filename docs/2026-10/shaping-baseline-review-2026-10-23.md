# Shaping baseline review, 2026-10-23

The shaping snapshots now include the glyph redesigns committed in
`5cea3451`. This update changes test data only; the font sources, generators,
quality exceptions and upstream Cyrillic sign drawings are untouched.

## Reference and scope

For each affected style, the reference font was rebuilt from the last
revision that updated its digest. Its golden cases and full-corpus digest
both reproduce the recorded baseline exactly. These references were then
compared with the current masters over **2,119,788 strings per style**.

| Style | Baseline revision | Changed strings | Changed golden cases |
|---|---|---:|---:|
| Bold | `49370b21` | 2,854 | 1 |
| Italic | `403159a7` | 11,684 | 2 |
| BoldItalic | `403159a7` | 23,266 | 3 |

All changed strings retain exactly the same glyph sequence. Their advance
deltas equal the following glyph-width deltas, including repeated glyphs.
No kerning or feature source changes occur between either reference and
its current master; compiled cmap, GSUB and GDEF tables also match.

## Reviewed advances

| Style | Glyph | Before | After | Delta |
|---|---|---:|---:|---:|
| Bold | ₸ (`uni20B8`) | 1709 | 1697 | -12 |
| Italic | Қ (`uni049A`) | 1496 | 1366 | -130 |
| Italic | Җ (`uni0496`) | 2087 | 1956 | -131 |
| Italic | ɮ (`uni026E`) | 833 | 983 | +150 |
| Italic | ʑ (`uni0291`) | 839 | 880 | +41 |
| BoldItalic | Қ (`uni049A`) | 1558 | 1430 | -128 |
| BoldItalic | қ (`uni049B`) | 1025 | 1024 | -1 |
| BoldItalic | Җ (`uni0496`) | 2172 | 2030 | -142 |
| BoldItalic | җ (`uni0497`) | 1657 | 1652 | -5 |
| BoldItalic | ƈ (`uni0188`) | 847 | 808 | -39 |
| BoldItalic | ₸ (`uni20B8`) | 1518 | 1497 | -21 |
| BoldItalic | ʄ (`uni0284`) | 676 | 680 | +4 |
| BoldItalic | ɮ (`uni026E`) | 914 | 1072 | +158 |

These changes follow the accepted work: ₸'s extra bar moved above T;
ɮ's complete ʒ moved beside l; ʑ's smaller loop; the upright Cyrillic
curl descenders; and the hook/stem recipes for ƈ and ʄ. The Bold Italic
values include the generator's optical fitting at its weight. The later
local contour finishing pass introduced no further shaping changes.

## Mark placement

The full corpus also includes combining marks on the changed letters.
Every changed offset is horizontal, on a zero-advance mark. Accounting
for the base's changed advance leaves exactly its anchor's horizontal
shift; vertical placement is unchanged. The nonzero shifts below follow
the Bold Italic generator's repositioned bases. Italic's compiled GPOS is
identical to its reference; Bold/Bold Italic GPOS changes only the reviewed
bases' anchor x coordinates.

| Style | Base | Mark position delta relative to base origin | Changed mark positions |
|---|---|---:|---:|
| Italic | ɮ | +0 | 63 |
| Italic | ʑ | +0 | 63 |
| Italic | Җ | +0 | 44 |
| Italic | Қ | +0 | 44 |
| BoldItalic | ƈ | +0 | 64 |
| BoldItalic | ɮ | +5 | 63 |
| BoldItalic | ʄ | +2 | 35 |
| BoldItalic | Җ | -9 | 44 |
| BoldItalic | җ | +0 | 63 |
| BoldItalic | Қ | -1 | 44 |
| BoldItalic | қ | +0 | 63 |

For example, Italic ɮ gains 150 units of advance. In ɮ́, the mark's x offset
falls by 150, keeping it at the same anchor relative to the base origin.
Bold Italic ɮ gains 158 units while its anchors move five units right;
its acute offset falls by 153. These are the expected consequences of
the recorded advance and anchor changes.

## Baseline update and validation

Only `shaping-golden-{Bold,Italic,BoldItalic}.json` and the three matching
`shaping-digest-*.txt` files are updated. The six golden-case changes
contain only the advance values listed above. Each digest still covers
2,119,788 strings. Regular's baselines are unchanged.

The supported updater is run with `--golden --digest --expect-changes 0`:
the font changes are already committed, so there are zero differences
against HEAD. The historical reference review above checks the actual
changes represented by the stale baselines, rather than relying on that
zero-difference check alone.

Raw comparisons, all changed strings, compiled reference/current fonts,
summary JSON and updater logs are in `build/shaping-review/` in this working
copy. `pytest tests/test_regression.py -q` passes all 12 checks across the
four styles: coverage, golden shaping and full-corpus digests. The two
known quality-test failures remain outside this baseline task.
