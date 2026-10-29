"""Evaluate relationship discovery against a labelled, family-separated corpus."""

import argparse
import json
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_support import content_hash
from relationships.evaluation import evaluate
from shape_relationships import ROOT, safe_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=ROOT/'scripts/data/relationship-evaluation.json')
    parser.add_argument('--ufo', type=Path, help='For a source-hash-pinned real-font corpus')
    parser.add_argument('--out', type=Path, default=ROOT/'build/glyph-review/relationship-evaluation')
    args = parser.parse_args()
    out = safe_output(args.out)
    if args.ufo and (out.is_relative_to(args.ufo.resolve()) or args.ufo.resolve().is_relative_to(out)):
        parser.error('Source and output must be disjoint')
    before = content_hash(args.ufo) if args.ufo else None
    font = ufoLib2.Font.open(args.ufo, lazy=False) if args.ufo else None
    report = evaluate(json.loads(args.corpus.read_text()), font, before)
    if args.ufo and content_hash(args.ufo) != before:
        raise RuntimeError('Source changed during evaluation')
    out.mkdir(parents=True, exist_ok=True)
    (out/'evaluation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['splits'], indent=2))
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
