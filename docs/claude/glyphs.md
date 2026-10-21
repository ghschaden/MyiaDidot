# Glyphs: composites, accents, small caps, derived letters, locl

Moved from CLAUDE.md (its ground rules apply).

- Composites are generated: `scripts/composites.py` (anchor-driven, follows
  upstream's accent conventions). After moving an anchor, rerun the builder
  for the affected composites rather than hand-editing offsets. Upstream's
  deliberate special designs are in `SPECIAL` there. Where a precomposed
  letter is drawn otherwise than its decomposition places the marks
  (polytonic Greek, the capital breve), `scripts/nfd_compose.py` composes
  the decomposed form back in ccmp (a generated block in the Regular's
  features.fea); rerun it when the NFD test reports a new mismatch. The
  combining cedilla and ogonek are marks (they were base glyphs, so they
  were never positioned).
- Accent conventions: spacing accents 880 wide centred at x=440; combining
  marks are those shifted −880; lowercase bases carry Top/Acute/Grave/
  Dotaccent (Acute/Grave = Top−20, Dotaccent = Top+20), Bottom/DotBelow,
  Cedilla; capitals carry TopCap and take `.cap` accents; stacking via
  TopMark/_TopMark, computed from ink (`--stack-anchors`).
- Small caps: `scripts/smallcaps.py UFO` rebuilds aliases, accented small
  caps, specials, scaled kerning and the generated smcp/c2sc block in
  features.fea (between BEGIN/END markers; never hand-edit it). It never
  overwrites outlines. Drafts from `smallcaps_draft.py` carry lib key
  `org.myiadidot.smallcapDraft`; clear it once a glyph is reviewed. Other
  drafted glyphs (ẞ) carry `org.myiadidot.draft`. Small-cap height is
  1040 (lib `org.myiadidot.smallcapHeight`, chosen by the person after
  comparing 960/1000/1040); small caps take the `.cap` accents at TopCap =
  height + 146. A capital before a small cap is kerned only where a style
  falls outside the references (CAP_SC_KERNING there, final values per
  style from `scripts/quality/capsc_pairs.py STYLE`). To redraft: `smallcaps_draft.py` then `smallcaps.py
  --drafts ... --redraft` (replaces only unreviewed drafts).
- New letters derived from existing ones (same shape, turned, mirrored, with a bar, slash or middle tilde merged in, the Ц tail added, enlarged to capital weight):
  recipes in `scripts/derive.py` (also their small caps, "ɔ.sc"); drafts
  carry `org.myiadidot.draft` and are reviewed in `drafts-review.pdf`.
  The Vietnamese hook and horn, and circumflex + tone marks set side by
  side (ccmp lookup ccmpVietnameseToneMarks; composites.py uses them):
  `scripts/draft_vietnamese_marks.py`; IPA
  diacritics and symbols: `scripts/draft_ipa_marks.py`; arrows, geometric
  shapes, circled letters, and the guillemets as Didot chevrons
  (`--guillemets`): `scripts/draft_symbols.py`; ℓ 𝑙 ℮ ℵ ℶ, and
  𝔐 𝔓 𝔖 𝔭 from Libertinus Math (OFL, credited in OFL.txt and the
  copyright notice): `scripts/draft_letterlike.py`; ligatures ct st
  (dlig), f-ligatures fb fh fk ft (liga) and long-s ligatures (own liga
  lookups): `scripts/draft_ligatures.py`. Hooks: `hook` (f top or ȷ tail
  scaled to the stem) and `curl` (an elliptical ring with a ball, at the
  stroke's own weight) in derive.py. Shaping in this shell defaults to
  German (locale), which has no f-ligatures: pass `--language=en`.
- Localized forms (locl): recipes in derive.py name them "б.loclSRB" (a
  character and its suffix; derive.variant/resolve), aliases of the plain
  letter where only the italic differs (make_italic ITALIC_RECIPES,
  ITALIC_LOCL, OS_LOCL: Old Standard's own), so all styles share one
  glyph set and features.fea. Cyrillic locl lookups stand after the small
  caps block (smcp sees the plain letters); Dutch's before ccmp (it adds
  a mark the dotless pass then handles). A new languagesystem must be
  added to every feature that lists its languages (test_lookups.py
  test_languages_keep_script_defaults); their groups: ALIKE in
  kern_groups.py, run after the styles have the glyphs (make generate,
  kern_groups.py, make generate).
- Inherited accents resized at the same weight (the Latin breve):
  `scripts/adjust_accents.py` (idempotent; then `composites.py
  --stack-anchors --rebuild-stacked`).
