# Hinting

Moved from CLAUDE.md (its ground rules apply).

- Hinting is generated at build time, nothing in the UFOs: TTF by
  `scripts/hint_control.py` (ttfautohint-py with a control file per style,
  kept in build/hinting/: tips that join the serif edge at their height,
  Greek on the Latin zones where that is better, Bulgarian ascenders as
  Latin, Regular prosgegrammeni explicitly on Latin x-height zones, whole-pixel deltas onto the zone; ttfautohint drops what does not
  fit in a control line silently, so lists are cut short); CFF by
  `scripts/ps_hints.py` (zones and stems measured per style, then
  otfautohint). `scripts/quality/hint_zones.py TTF` lists letters hinted
  off their zone (reference glyphs x o H O l p h.sc o.sc, 8–32 px, FreeType
  v40 and v35; an OTF by whole glyphs with FreeType's CFF engine, to the
  exact row); tests/test_hinting.py holds them to `hint-zones*.txt` and
  `hint-zones-cff*.txt` (`update_test_data.py --hinting`). The test fonts
  must be built like fontmake's (overlaps removed): TTF point indices depend
  on it, and otfautohint leaves hundreds of letters off their zones in a
  font with overlaps.


- The Italic v.sc/w.sc/ѵ.sc/ⱳ.sc tip correction (half a pixel at 30/32
  ppem, accepted 2026-10-26 for tips at -35) was dropped on 2026-11-05: with
  the small caps' overshoot scaled (tips at -25) they sit on h.sc's and
  o.sc's baseline row at 24-32 ppem without it; with it they stopped a
  pixel above the line at 30/32 ppem.
  Review: `docs/italic-smallcap-tip-hinting-review-2026-10-26.md`.
