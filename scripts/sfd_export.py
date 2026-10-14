"""Stage A of the upstream import: dump a FontForge SFD to raw UFO + JSON.

Run with FontForge's Python, not the project venv:

    fontforge -quiet -lang=py -script scripts/sfd_export.py SRC.sfd OUTDIR

Writes OUTDIR/raw.ufo (outlines from the cubic "Fore" layer, anchors,
FontForge-generated features.fea), OUTDIR/raw.fea (the same feature file)
and OUTDIR/meta.json (kerning classes, GDEF glyph classes, ligature carets
and the vertical metrics FontForge would compute), which the venv-side
postprocess_import.py turns into a clean source UFO.
"""

import json
import os
import sys

import fontforge


def kerning_subtables(font):
    out = []
    for lookup in font.gpos_lookups:
        ltype, _flags, _feats = font.getLookupInfo(lookup)
        if ltype != "gpos_pair":
            continue
        for sub in font.getLookupSubtables(lookup):
            if not font.isKerningClass(sub):
                continue
            first, second, offsets = font.getKerningClass(sub)
            out.append(
                {
                    "lookup": lookup,
                    "subtable": sub,
                    "first": [list(c) if c else [] for c in first],
                    "second": [list(c) if c else [] for c in second],
                    "offsets": list(offsets),
                }
            )
    return out


def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    font = fontforge.open(src)

    font.generate(os.path.join(outdir, "raw.ufo"), layer="Fore", flags=("opentype",))
    font.generateFeatureFile(os.path.join(outdir, "raw.fea"))

    glyph_classes = {}
    carets = {}
    for g in font.glyphs():
        glyph_classes[g.glyphname] = g.glyphclass
        lcarets = [p for p in (g.lcarets or ()) if p]
        if lcarets:
            carets[g.glyphname] = list(lcarets)

    meta = {
        "kerning": kerning_subtables(font),
        "glyphclass": glyph_classes,
        "carets": carets,
        "metrics": {
            "os2_typoascent": font.os2_typoascent,
            "os2_typoascent_add": font.os2_typoascent_add,
            "os2_typodescent": font.os2_typodescent,
            "os2_typodescent_add": font.os2_typodescent_add,
            "os2_typolinegap": font.os2_typolinegap,
            "os2_winascent": font.os2_winascent,
            "os2_winascent_add": font.os2_winascent_add,
            "os2_windescent": font.os2_windescent,
            "os2_windescent_add": font.os2_windescent_add,
            "hhea_ascent": font.hhea_ascent,
            "hhea_ascent_add": font.hhea_ascent_add,
            "hhea_descent": font.hhea_descent,
            "hhea_descent_add": font.hhea_descent_add,
            "hhea_linegap": font.hhea_linegap,
            "use_typo_metrics": font.os2_use_typo_metrics,
        },
    }
    with open(os.path.join(outdir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
    font.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
