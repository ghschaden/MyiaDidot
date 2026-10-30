"""Read-only relationship discovery. Run with --help for CLI options."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_support import content_hash
from relationships.arches import arch_report
from relationships.discovery import analyse
from relationships.geometry import POLICY as POLICY
from relationships.geometry import Outline as Outline
from relationships.geometry import is_line as is_line
from relationships.geometry import split as split
from relationships.geometry import transition_metrics as transition_metrics
from relationships.matching import compare_relationships as compare_relationships
from relationships.matching import related as related
from relationships.provenance import fragment_evidence, verified_declarations
from relationships.provenance import provenance as provenance
from relationships.recognisers import anchor_candidates as anchor_candidates
from relationships.recognisers import attachments as attachments
from relationships.recognisers import transitions as transitions
from relationships.reporting import proof, write_html
from relationships.returns import return_report
from relationships.reuse import constituent_reuse

ROOT = Path(__file__).resolve().parents[1]



def safe_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to((ROOT/'build').resolve()) or path == (ROOT/'build').resolve():
        raise ValueError('Output must be a directory below this worktree build/')
    if path.exists() and any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Output tree contains symlinks')
    return path


def run(source, out, query=None, proof_names=None, *, span=None, limit=20, declarations=None, fragments=None, paired=False, boundary_glyphs=None, proof_relationship=None, reuse=False, returns=False, arches=False):
    source, out = Path(source).resolve(), safe_output(out)
    if source.is_relative_to(out) or out.is_relative_to(source):
        raise ValueError('Source and output must be disjoint')
    before = content_hash(source)
    font = ufoLib2.Font.open(source, lazy=False)
    report = analyse(font, before, paired=paired or reuse or returns or arches, boundary_glyphs=boundary_glyphs)
    report['source'] = {"path": str(source), "sha256": before}
    implementation = [Path(__file__), *sorted((ROOT/'scripts/relationships').glob('*.py'))]
    report['implementation_files'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in implementation}
    report['implementation_sha256'] = hashlib.sha256(json.dumps(report['implementation_files'], sort_keys=True).encode()).hexdigest()
    if declarations:
        declaration_bytes = Path(declarations).read_bytes()
        report['declarations'] = verified_declarations(json.loads(declaration_bytes), font, report, before)
        report['declarations_sha256'] = hashlib.sha256(declaration_bytes).hexdigest()
    if reuse:
        report['constituent_reuse'] = constituent_reuse(report, font.info.unitsPerEm)
    if returns:
        report['lower_returns'] = return_report(font, report, report['paired_boundary_scope'])
    if arches:
        report['upper_arches'] = arch_report(font, report, report['paired_boundary_scope'])
    if fragments:
        fragment_bytes = Path(fragments).read_bytes()
        report['fragment_evidence'] = fragment_evidence(json.loads(fragment_bytes), font, font.info.styleName)
        report['fragment_library_sha256'] = hashlib.sha256(fragment_bytes).hexdigest()
    if span and not query:
        raise ValueError('--span requires --related')
    if query:
        report['query'] = related(report, query, span=span, limit=limit)
    if content_hash(source) != before:
        raise RuntimeError('Source changed during analysis; rerun on a stable snapshot')
    names = proof_names or list(dict.fromkeys(([query] if query else []) +
            [r['glyph'] for r in report['relationships'] if r.get('review_notice')] +
            [r['glyph'] for r in report['relationships'] if r['status'] == 'confirmed']))[:16]
    missing = set(names)-set(font.keys())
    if missing:
        raise ValueError(f'Unknown proof glyphs: {sorted(missing)}')
    out.mkdir(parents=True, exist_ok=True)
    proof_records = [r for r in report['relationships'] if not span or r['glyph'] != query or span in (r['id'], r['geometry_id'])]
    if proof_relationship:
        proof_records = [r for r in proof_records if r['relationship'] == proof_relationship]
    proof(font, names, proof_records, out/'proof.svg')
    if returns:
        proof(font, names, [{**r, 'relationship': 'lower-return'} for r in report['lower_returns']['results']], out/'returns.svg')
    if arches:
        proof(font, names, [{**r, 'relationship': 'upper-arch'} for r in report['upper_arches']['results']], out/'arches.svg')
    report['proof_glyphs'] = names
    report['source_preserved'] = content_hash(source) == before
    if not report['source_preserved']:
        raise RuntimeError('Source changed while rendering')
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    write_html(report, out)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ufo', type=Path, default=ROOT/'sources/MyiaDidot-BoldItalic.ufo')
    parser.add_argument('--out', type=Path, default=ROOT/'build/glyph-review/shape-relationships')
    parser.add_argument('--related', help='Explain component ancestry and local structural peers of this glyph')
    parser.add_argument('--span', help='Select one source-pinned relationship ID or geometric ID')
    parser.add_argument('--limit', type=int, default=20, help='Number of ranked base families to display')
    parser.add_argument('--provenance', type=Path, help='Source-pinned declaration sidecar')
    parser.add_argument('--fragments', type=Path, help='Existing exact shape-grammar JSON, verified before use')
    parser.add_argument('--constituent-reuse', action='store_true', help='Compare verified constituent strokes; enables paired boundaries')
    parser.add_argument('--upper-arches', action='store_true', help='Upper-counter roles and interior return conflicts')
    parser.add_argument('--lower-returns', action='store_true', help='Pilot lower counter turns and observed stem neighbours; enables paired boundaries')
    parser.add_argument('--paired-boundaries', action='store_true', help='Enable sampled paired-boundary recognition')
    parser.add_argument('--boundary-glyphs', nargs='+', help='Enable paired boundaries only on these glyphs (scope is recorded)')
    parser.add_argument('--proof-relationship', choices=['curve-to-line', 'base-mark-attachment', 'paired-stroke-boundaries'])
    parser.add_argument('--proof-glyphs', nargs='+', help='Glyphs for focused source-outline proof')
    args = parser.parse_args()
    report = run(args.ufo, args.out, args.related, args.proof_glyphs, span=args.span, limit=args.limit, declarations=args.provenance, fragments=args.fragments, paired=args.paired_boundaries, boundary_glyphs=args.boundary_glyphs, proof_relationship=args.proof_relationship, reuse=args.constituent_reuse, returns=args.lower_returns, arches=args.upper_arches)
    print(json.dumps({'summary': report['summary'], 'relationships': len(report['relationships']),
                      'omissions': len(report['omissions']), 'source_preserved': report['source_preserved'],
                      'index': str(args.out/'index.html')}, indent=2))


if __name__ == '__main__':
    main()
