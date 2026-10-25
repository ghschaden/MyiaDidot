"""Lookup order, as compiled, held to a baseline per style.

Lookups apply in the order of the LookupList, whatever feature they belong
to, and an order gone wrong fails silently (a ccmp composition after the
lookup that needed its result). Each style's compiled GSUB and GPOS are
summarised one lookup per line, in that order: table, the features that
use it, type, subtables, the first glyphs it covers; data/lookups.txt
(lookups-Italic.txt ...) holds what was accepted. A changed feature file
shows here as lines added, gone or moved: read them, then
scripts/update_test_data.py --lookups --ufo UFO.
"""

import difflib

from conftest import style_data

FIRST = 4  # glyphs named per lookup


def covered(sub):
    """The first glyphs a subtable works on."""
    for attr in ("Coverage", "BacktrackCoverage", "InputCoverage", "MarkCoverage"):
        cov = getattr(sub, attr, None)
        if isinstance(cov, list):
            cov = cov[0] if cov else None
        if cov is not None and getattr(cov, "glyphs", None):
            return list(cov.glyphs)
    for attr in ("mapping", "alternates", "ligatures"):
        found = getattr(sub, attr, None)
        if found:
            return list(found)
    return []


def lookup_summary(ttfont):
    lines = []
    for tag in ("GSUB", "GPOS"):
        if tag not in ttfont:
            continue
        table = ttfont[tag].table
        users = {}
        for rec in table.FeatureList.FeatureRecord:
            for i in rec.Feature.LookupListIndex:
                users.setdefault(i, set()).add(rec.FeatureTag)
        for i, lookup in enumerate(table.LookupList.Lookup):
            subs = lookup.SubTable
            kind = lookup.LookupType
            if kind in (7, 9) and subs:  # extension: what it holds
                kind = subs[0].ExtensionLookupType
                subs = [s.ExtSubTable for s in subs]
            glyphs = covered(subs[0]) if subs else []
            more = " ..." if len(glyphs) > FIRST else ""
            lines.append(f"{tag} {','.join(sorted(users.get(i, ['-'])))} type{kind} x{len(subs)}: "
                         f"{' '.join(glyphs[:FIRST])}{more}")
    return lines


def test_lookup_order(ttfont, ufo_path):
    path = style_data("lookups.txt", ufo_path)
    accepted = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    found = lookup_summary(ttfont)
    diff = list(difflib.unified_diff(accepted, found, "accepted", "compiled", n=1, lineterm=""))
    assert not diff, ("lookups added, gone or moved (if intended: update_test_data.py --lookups "
                      "--ufo UFO):\n" + "\n".join(diff[:60]))


# German keeps liga for long-s combinations in every style, while its
# lookup selection excludes the ordinary f-ligatures.
LANGUAGE_DROPS = set()


def test_languages_keep_script_defaults(ttfont):
    """Every language system has at least its script's default features.

    A language added to languagesystem but left out of a feature that lists
    its languages one by one gets none of that feature (text tagged nl
    would lose ccmp). Which lookups a language takes within a feature is
    its own (Turkish and German liga leave the f-ligatures out)."""
    missing = []
    for tag in ("GSUB", "GPOS"):
        table = ttfont[tag].table
        feats = table.FeatureList.FeatureRecord
        for rec in table.ScriptList.ScriptRecord:
            script = rec.Script
            if script.DefaultLangSys is None:
                continue
            base = {feats[i].FeatureTag for i in script.DefaultLangSys.FeatureIndex}
            for lang in script.LangSysRecord:
                have = {feats[i].FeatureTag for i in lang.LangSys.FeatureIndex}
                missing += [f"{tag} {rec.ScriptTag}/{lang.LangSysTag.strip()}: no {feat}"
                            for feat in sorted(base - have)
                            if (rec.ScriptTag, lang.LangSysTag.strip(), feat) not in LANGUAGE_DROPS]
    assert not missing, "\n".join(missing)
