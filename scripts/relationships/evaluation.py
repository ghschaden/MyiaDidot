"""Labelled retrieval evaluation, with base-family leakage checks."""

from collections import Counter, defaultdict

import ufoLib2
from fontTools.misc.transform import Transform
from ufoLib2.objects import Anchor, Component

from .discovery import analyse
from .identity import digest
from .matching import compare_relationships


def fixture_font(corpus):
    font = ufoLib2.Font()
    font.info.unitsPerEm = corpus.get('units_per_em', 1000)
    font.info.styleName = 'Evaluation'
    for name, data in corpus['glyphs'].items():
        glyph = font.newGlyph(name)
        glyph.unicodes = data.get('unicodes', [])
        glyph.anchors = [Anchor(name=a[0], x=a[1], y=a[2]) for a in data.get('anchors', [])]
        glyph.components = [Component(c[0], Transform(*c[1])) for c in data.get('components', [])]
        pen = glyph.getPen()
        for contour in data.get('contours', []):
            pen.moveTo(tuple(contour[0][0]))
            for segment in contour:
                if len(segment) == 2:
                    pen.lineTo(tuple(segment[-1]))
                elif len(segment) == 3:
                    pen.qCurveTo(*map(tuple, segment[1:]))
                elif len(segment) == 4:
                    pen.curveTo(*map(tuple, segment[1:]))
                else:
                    raise ValueError('Invalid corpus segment')
            pen.closePath()
    return font


def select(report, selector):
    rows = [r for r in report['relationships'] if r['glyph'] == selector['glyph'] and r['relationship'] == selector['relationship']]
    if 'geometry_id' in selector:
        rows = [r for r in rows if r['geometry_id'] == selector['geometry_id']]
    if 'junction' in selector:
        x, y = selector['junction']
        rows = [r for r in rows if 'junction' in r and abs(r['junction'][0]-x) < 1e-5 and abs(r['junction'][1]-y) < 1e-5]
    return rows


def evaluate(corpus, font=None, source_digest=None):
    if corpus.get('format') != 'myiadidot-relationship-corpus-v1':
        raise ValueError('Unsupported evaluation corpus')
    if font is None:
        font = fixture_font(corpus)
    elif corpus.get('source_sha256') != source_digest:
        raise ValueError('Stale evaluation corpus source')
    paired = any(c[side]['relationship'] == 'paired-stroke-boundaries' for c in corpus['cases'] for side in ('left', 'right') if side in c)
    report = analyse(font, source_digest, paired=paired)
    membership = corpus['membership']
    cases = corpus['cases']
    seen, splits = set(), defaultdict(set)
    children = defaultdict(list)
    for g in font:
        children[g.name] = [c.baseGlyph for c in g.components]
    for case in cases:
        if case['id'] in seen or case['split'] not in ('development', 'heldout'):
            raise ValueError('Duplicate case or invalid split')
        seen.add(case['id'])
        todo = [case['left']['glyph']]+([case['right']['glyph']] if 'right' in case else [])
        visited = set()
        while todo:
            name = todo.pop()
            if name in visited:
                continue
            visited.add(name)
            if name not in membership or name not in font:
                raise ValueError('Corpus glyph missing or not assigned to a base family')
            family = membership[name]
            if family != 'support':
                splits[family].add(case['split'])
            todo.extend(children[name])
    if any(len(v) > 1 for v in splits.values()):
        raise ValueError('Base-family leakage between development and heldout cases')
    results, totals = [], {}
    for case in cases:
        a = select(report, case['left'])
        if 'right' in case:
            b = select(report, case['right'])
            if len(a) != 1 or len(b) != 1:
                actual, reason = 'uncertain', 'selector missing or ambiguous'
            else:
                comparison = compare_relationships(a[0], b[0])
                actual = comparison.get('decision', 'compatible' if comparison['compatible'] else 'incompatible')
                reason = comparison['reason']
        else:
            actual = 'absent' if not a else 'uncertain' if len(a) != 1 else a[0]['status']
            reason = 'recogniser result'
        results.append({**case, 'actual': actual, 'passed': actual == case['expected'], 'reason': reason})
    for split in ('development', 'heldout'):
        subset = [r for r in results if r['split'] == split]
        confusion = Counter(f"{r['expected']} -> {r['actual']}" for r in subset)
        totals[split] = {'cases': len(subset), 'passed': sum(r['passed'] for r in subset),
                         'confusion': dict(sorted(confusion.items())),
                         'unexpected_positive': sum(r['actual'] in ('compatible', 'confirmed', 'structural-candidate') and not r['passed'] for r in subset),
                         'missed_or_uncertain': sum(not r['passed'] and r['actual'] in ('absent', 'uncertain', 'unresolved', 'boundary-uncertain', 'incompatible') for r in subset)}
    return {'format': 'myiadidot-relationship-evaluation-v1', 'corpus_sha256': digest(corpus),
            'source_identity': report['source_identity'], 'all_passed': all(r['passed'] for r in results),
            'splits': totals, 'cases': results,
            'scope': corpus.get('scope', 'Labelled retrieval evaluation; not aesthetic acceptance.')}
