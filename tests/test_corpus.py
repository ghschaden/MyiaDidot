"""The golden corpus covers every feature and language system the fonts offer.

A feature or a language added to the fonts without a case in
data/shaping-corpus.txt would change nothing the golden test or the visual
diff (scripts/visual_diff.py) can see. Features that are always on and only
structural are left out: their effect shows in every case.
"""

import uharfbuzz as hb
from shaping import golden_cases

STRUCTURAL = {"aalt", "ccmp", "locl", "mark", "mkmk", "calt", "rlig"}


def font_features(ttfont):
    return {rec.FeatureTag for tag in ("GSUB", "GPOS") if tag in ttfont
            for rec in ttfont[tag].table.FeatureList.FeatureRecord}


def font_languages(ttfont):
    return {lang.LangSysTag.strip() for tag in ("GSUB", "GPOS") if tag in ttfont
            for rec in ttfont[tag].table.ScriptList.ScriptRecord
            for lang in rec.Script.LangSysRecord}


def test_every_feature_has_a_case(ttfont):
    used = {feat for _, feats, _ in golden_cases() for feat in feats}
    missing = sorted(font_features(ttfont) - STRUCTURAL - used)
    assert not missing, f"no case in shaping-corpus.txt switches on or off: {', '.join(missing)}"


def test_every_language_system_has_a_case(ttfont):
    langs = {lang.lower() for _, _, lang in golden_cases() if lang}
    missing = []
    for ot in sorted(font_languages(ttfont)):
        bcp = hb.ot_tag_to_language(ot).split("-x-")[0].lower()  # GAG: gag-x-hbot-...
        if bcp not in langs and not any(lang.startswith(bcp + "-") for lang in langs):
            missing.append(f"{ot} ({bcp})")
    assert not missing, f"no case in shaping-corpus.txt is tagged for: {', '.join(missing)}"
