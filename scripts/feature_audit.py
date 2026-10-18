"""Check that built fonts expose Myia Didot's intended OpenType features.

    python scripts/feature_audit.py fonts/otf/*.otf

This is a structural check: the shaping regression corpus checks feature
behavior, while this script catches missing feature records and invalid
lookup references in release binaries.
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont


REQUIRED = {
    "GSUB": {
        "aalt", "c2sc", "calt", "case", "ccmp", "dlig", "dnom", "frac",
        "liga", "locl", "numr", "onum", "rlig", "salt", "smcp", "ss01",
        "ss02", "ss11", "subs", "sups", "tnum",
    },
    "GPOS": {"kern", "mark", "mkmk"},
}


def audit(path):
    errors = []
    font = TTFont(path, lazy=True)
    for table_tag, expected in REQUIRED.items():
        if table_tag not in font:
            errors.append(f"missing {table_tag} table")
            continue
        table = font[table_tag].table
        if table.FeatureList is None or table.LookupList is None:
            errors.append(f"{table_tag} has no feature or lookup list")
            continue
        records = table.FeatureList.FeatureRecord
        found = {record.FeatureTag for record in records}
        referenced = set()
        for script_record in table.ScriptList.ScriptRecord:
            script = script_record.Script
            lang_systems = [record.LangSys for record in script.LangSysRecord]
            if script.DefaultLangSys is not None:
                lang_systems.append(script.DefaultLangSys)
            for lang_system in lang_systems:
                if lang_system.FeatureIndex:
                    referenced.update(lang_system.FeatureIndex)
                required = lang_system.ReqFeatureIndex
                if required != 0xFFFF:
                    referenced.add(required)
        for tag in sorted(expected - found):
            errors.append(f"{table_tag} missing {tag} feature")
        for index, record in enumerate(records):
            feature = record.Feature
            if index not in referenced:
                errors.append(f"{table_tag} {record.FeatureTag} is not attached to a script/language system")
            if not feature.LookupListIndex:
                errors.append(f"{table_tag} {record.FeatureTag} has no lookups")
            for index in feature.LookupListIndex:
                if index >= len(table.LookupList.Lookup):
                    errors.append(
                        f"{table_tag} {record.FeatureTag} references missing lookup {index}"
                    )
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.fonts:
        errors = audit(path)
        if errors:
            failed = True
            print(f"{path}: FAIL")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"{path}: OpenType feature tables OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
