"""Shaping corpora shared by the tests and scripts/update_test_data.py."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from compare_shaping import corpus as full_corpus


def golden_cases():
    """(text, features, language) triples from data/shaping-corpus.txt."""
    cases = []
    for line in (HERE / "data" / "shaping-corpus.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        text = parts[0]
        feats = {}
        if len(parts) > 1 and parts[1]:
            for tag in parts[1].split(","):
                tag = tag.strip()
                feats[tag.lstrip("-")] = not tag.startswith("-")
        lang = parts[2] if len(parts) > 2 and parts[2] else None
        cases.append((text, feats, lang))
    return cases


def case_key(text, feats, lang):
    f = ",".join(f"{'' if v else '-'}{k}" for k, v in sorted(feats.items()))
    return f"{text} | {f} | {lang or ''}"


def shape_golden(shaper):
    return {case_key(*c): [list(g) for g in shaper.shape(c[0], c[1], c[2])] for c in golden_cases()}


def full_digest(shaper, cmap):
    """sha256 over the shaping of compare_shaping's ~850k-string corpus."""
    h = hashlib.sha256()
    n = 0
    lang_map = {"TRK": "tr", "ROM": "ro", "DEU": "de"}
    for text, feats, script, lang in full_corpus(cmap):
        run = shaper.shape(text, feats, lang_map.get(lang, lang), script)
        h.update(json.dumps([text, run], ensure_ascii=False).encode())
        n += 1
    return h.hexdigest(), n
