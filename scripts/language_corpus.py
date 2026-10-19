"""Print the first sentence of UDHR Article 1 per language as shaping-corpus lines.

    python scripts/language_corpus.py build/udhr [build/udhr-extra ...]

Reads udhr_*.xml (the UDHR in Unicode project, as fetched by udhr_book.py)
and prints "text | | language" with the file's own BCP 47 tag, for the
Languages section of tests/data/shaping-corpus.txt. Run once and review:
the corpus file is the record, not this script's output.
"""

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://efele.net/udhr}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
LIMIT = 200


def first_sentence(text):
    text = " ".join(text.split())
    m = re.match(r"(.+?[.;:·;])(\s|$)", text)
    if m and len(m.group(1)) >= 40:  # not an abbreviation or a two-word clause
        text = m.group(1)
    if len(text) > LIMIT:
        text = text[:LIMIT].rsplit(" ", 1)[0]
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dirs", nargs="+", type=Path)
    args = ap.parse_args()
    for d in args.dirs:
        for path in sorted(d.glob("udhr_*.xml")):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                print(f"# {path.name}: not UDHR XML, skipped")
                continue
            article = root.find(f"{NS}article")
            para = article.find(f".//{NS}para") if article is not None else None
            if para is None or not para.text:
                continue
            lang = root.get(XML_LANG)
            print(f"# {root.get('n')}\n{first_sentence(para.text)} | | {lang}")


if __name__ == "__main__":
    main()
