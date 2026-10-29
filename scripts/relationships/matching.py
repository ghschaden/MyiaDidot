"""Operation-specific retrieval and explanation."""

import math
from collections import Counter, defaultdict

from .boundaries import compare_pairs
from .geometry import POLICY, dot, sub


def related(report, name, span=None, limit=20):
    if name not in report['glyphs']:
        raise ValueError(f"Unknown glyph: {name}")
    ancestors, descendants = {name}, {name}
    for selected, reverse in ((ancestors, False), (descendants, True)):
        changed = True
        while changed:
            changed = False
            for e in report['provenance']:
                if e['kind'] != 'component' or e['status'] != 'present':
                    continue
                a, b = (e['to'], e['from']) if reverse else (e['from'], e['to'])
                if a in selected and b not in selected:
                    selected.add(b)
                    changed = True
    families = {r['family'] for r in report['relationships'] if r['glyph'] == name and r['family']}
    local = [r for r in report['relationships'] if r['glyph'] == name and r['family']]
    if span:
        selected = [r for r in report['relationships'] if span in (r['id'], r.get('geometry_id')) and r['glyph'] == name]
        if len(selected) != 1:
            raise ValueError('Local span is missing, ambiguous or belongs to another glyph')
        local = selected
    matches = []
    rejected = Counter()
    for target in local:
        for candidate in report['relationships']:
            if candidate['glyph'] == name or candidate['family'] != target['family']:
                continue
            result = compare_relationships(target, candidate)
            if result['compatible']:
                matches.append({"target": target['id'], "peer": candidate['id'],
                                "glyph": candidate['glyph'], **result})
            else:
                rejected[result['reason']] += 1
    matches.sort(key=lambda r: (r.get('profile_rms_em', 0), r['glyph'], r['peer']))
    grouped = defaultdict(list)
    roots = derivative_roots(report)
    for match in matches:
        grouped[roots.get(match['glyph'], match['glyph'])].append(match)
    ranked = sorted(({'base_family': base, 'members': sorted({m['glyph'] for m in ms}),
                      'best_match': ms[0], 'matching_spans': len(ms)} for base, ms in grouped.items()),
                    key=lambda r: (r['best_match'].get('profile_rms_em', 0), r['base_family']))
    if limit < 1:
        raise ValueError('Query limit must be positive')
    return {"glyph": name, "component_ancestors": sorted(ancestors-{name}),
            "component_dependants": sorted(descendants-{name}), "structural_families": sorted(families),
            "structural_peers": sorted({r['glyph'] for r in matches}),
            "selected_span": span, "ranked_families": ranked[:limit], "total_matching_families": len(ranked),
            "matches": matches, "rejected_candidates": dict(rejected),
            "declared_evidence": [r for r in report.get('declarations', []) if name in (r['target'], r['base'])],
            "exact_fragment_peers": sorted({n for members in report.get('fragment_evidence', {}).get('shared_fragments', {}).values()
                                            if name in members for n in members if n != name}),
            "explanation": "Component ancestry is explicit. Peers pass local structural compatibility rules; no common defect or repair is established."}


def compare_relationships(a, b):
    """Operation-specific conservative matching, not a universal letter taxonomy."""
    if a.get('identity_status', 'unique') != 'unique' or b.get('identity_status', 'unique') != 'unique':
        return {'compatible': False, 'decision': 'uncertain', 'reason': 'ambiguous geometric identity'}
    if a['relationship'] == b['relationship'] and ('unresolved' in (a['status'], b['status'])):
        return {'compatible': False, 'decision': 'uncertain', 'reason': 'unresolved relationship evidence'}
    if a['relationship'] != b['relationship'] or a['family'] != b['family'] or not a['family']:
        return {"compatible": False, "reason": "different structural role"}
    if a['relationship'] == 'paired-stroke-boundaries':
        return compare_pairs(a, b)
    if a['relationship'] == 'base-mark-attachment':
        ok = a['status'] == b['status'] == 'confirmed'
        return {"compatible": ok, "decision": "compatible" if ok else "uncertain", "reason": "same confirmed anchor role" if ok else "unresolved attachment"}
    if a['status'] != 'structural-candidate' or b['status'] != 'structural-candidate':
        return {"compatible": False, "decision": "uncertain", "reason": "smoothness threshold uncertainty"}
    for key in ('line_length_em', 'curve_length_em'):
        x, y = a[key], b[key]
        if min(x, y) <= 0 or max(x, y)/min(x, y) > POLICY['peer_length_ratio']:
            return {"compatible": False, "reason": f"incompatible {key}"}
    x, y = a['metrics']['profile'], b['metrics']['profile']
    rms = math.sqrt(sum(dot(sub(p, q), sub(p, q)) for p, q in zip(x, y))/len(x))
    ok = rms <= POLICY['peer_profile_rms_em']
    return {"compatible": ok, "profile_rms_em": rms,
            "reason": "same axis family, comparable span lengths and local trajectory" if ok else "different local trajectory"}



def derivative_roots(report):
    """Collapse only established base ancestry, not similar outlines or input lists."""
    parents = defaultdict(set)
    for r in report['relationships']:
        if r['relationship'] == 'base-mark-attachment' and r['status'] == 'confirmed':
            parents[r['glyph']].add(r['base'])
    components = defaultdict(list)
    for e in report['provenance']:
        if e['kind'] == 'component' and e['status'] == 'present':
            components[e['from']].append(e)
    for name, edges in components.items():
        # Single component alone is insufficient: there may also be own contours.
        if len(edges) == 1 and report.get('glyph_metadata', {}).get(name, {}).get('own_contours') == 0:
            parents[name].add(edges[0]['to'])
    roots = {}
    for name in report['glyphs']:
        current, visited = name, set()
        while len(parents[current]) == 1 and current not in visited:
            visited.add(current)
            current = next(iter(parents[current]))
        roots[name] = name if current in visited or len(parents[current]) > 1 else current
    return roots
