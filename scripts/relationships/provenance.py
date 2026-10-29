"""Recorded evidence and checked external declarations."""

def provenance(font):
    edges = []
    for g in sorted(font, key=lambda g: g.name):
        for i, c in enumerate(g.components):
            edges.append({"from": g.name, "to": c.baseGlyph, "kind": "component",
                          "component": i, "transform": list(c.transformation),
                          "status": "present" if c.baseGlyph in font else "missing"})
        for base, fingerprint in sorted(g.lib.get('org.myiadidot.builtFrom', {}).items()):
            # This is recorded generator input, not proof of a copied region.
            edges.append({"from": g.name, "to": base, "kind": "recorded-generator-input",
                          "recorded_fingerprint": fingerprint, "status": "unverified-record"})
    return edges



def verified_declarations(manifest, font, report, source_digest):
    """Fail stale/malformed manifests; retain geometrically false claims as rejected.

    Supports exact component claims and sampled affine copies of recognised spans.
    A verified span claim is geometric agreement, not proof of historical authorship.
    """
    import math

    from fontTools.misc.transform import Transform

    from .geometry import length, sub

    if not isinstance(manifest, dict):
        raise ValueError('Provenance must be an object')
    if manifest.get('format') != 'myiadidot-provenance-v1':
        raise ValueError('Unsupported provenance format')
    source = manifest.get('source', {})
    if not isinstance(source, dict):
        raise ValueError('Provenance source must be an object')
    if source.get('sha256') != source_digest or source.get('style') != font.info.styleName:
        raise ValueError('Stale provenance: source hash or style differs')
    declarations = manifest.get('declarations')
    if not isinstance(declarations, list):
        raise ValueError('Provenance declarations must be a list')
    by_geometry = {}
    for r in report['relationships']:
        if r['identity_status'] == 'unique':
            by_geometry[r['geometry_id']] = r
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    result, ids = [], set()
    for declaration in declarations:
        if not isinstance(declaration, dict):
            raise ValueError('Each declaration must be an object')
        required = {'id', 'target', 'base', 'operation', 'evidence_origin', 'transform', 'protected_landmarks', 'part'}
        if not required <= declaration.keys():
            raise ValueError('Incomplete provenance declaration')
        identifier = declaration['id']
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError('Duplicate or invalid declaration id')
        ids.add(identifier)
        if not isinstance(declaration['evidence_origin'], str) or not declaration['evidence_origin'].strip():
            raise ValueError('An evidence origin is required')
        values = declaration['transform']
        if not isinstance(values, list) or len(values) != 6 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            raise ValueError('Invalid affine transform')
        transform = Transform(*values)
        if abs(transform.xx*transform.yy-transform.xy*transform.yx) < 1e-12:
            raise ValueError('Singular provenance transform')
        target, base = declaration['target'], declaration['base']
        if not isinstance(target, str) or not isinstance(base, str):
            raise ValueError('Provenance glyph names must be strings')
        if target not in font or base not in font:
            raise ValueError('Unknown glyph in provenance declaration')
        if declaration['operation'] not in ('component', 'span-copy'):
            raise ValueError('Unsupported provenance operation')
        landmarks = declaration['protected_landmarks']
        if not isinstance(landmarks, list):
            raise ValueError('Protected landmarks must be a list')
        errors = []
        for landmark in landmarks:
            if not isinstance(landmark, dict) or set(landmark) != {'base_anchor', 'target_anchor'}:
                raise ValueError('Landmarks must name base_anchor and target_anchor')
            aa = [(a.x, a.y) for a in font[base].anchors if a.name == landmark['base_anchor']]
            bb = [(a.x, a.y) for a in font[target].anchors if a.name == landmark['target_anchor']]
            if len(aa) != 1 or len(bb) != 1 or length(sub(transform.transformPoint(aa[0]), bb[0])) > 1e-6:
                errors.append('protected anchor missing, ambiguous or displaced')
        part = declaration['part']
        if not isinstance(part, dict):
            raise ValueError('Provenance part must be an object')
        expected_part = {'component_index'} if declaration['operation'] == 'component' else {'base_geometry_id', 'target_geometry_id'}
        if set(part) != expected_part:
            raise ValueError('Part fields do not match the declared operation')
        measurements = {}
        if declaration['operation'] == 'component':
            index = part.get('component_index')
            components = font[target].components
            if not isinstance(index, int) or index < 0 or index >= len(components):
                errors.append('component index not present')
            elif components[index].baseGlyph != base or any(abs(a-b) > 1e-9 for a, b in zip(components[index].transformation, values)):
                errors.append('component or transform differs from declaration')
        else:
            a = by_geometry.get(part.get('base_geometry_id'))
            b = by_geometry.get(part.get('target_geometry_id'))
            if not a or not b or a['glyph'] != base or b['glyph'] != target or a['relationship'] != 'curve-to-line' or b['relationship'] != 'curve-to-line':
                errors.append('span absent, ambiguous or not in the declared glyph')
            else:
                pa = [transform.transformPoint((x+slant*y, y)) for x, y in a['span']]
                pb = [(x+slant*y, y) for x, y in b['span']]
                error = polyline_distance(pa, pb)
                measurements['bidirectional_sample_distance_units'] = error
                measurements['tolerance_units'] = font.info.unitsPerEm*0.001
                if error > measurements['tolerance_units']:
                    errors.append('transformed span does not match observed geometry')
        result.append({**declaration, 'status': 'rejected' if errors else 'verified',
                       'errors': errors, 'measurements': measurements,
                       'verification_scope': 'observed geometry; declared design intent is not inferred history'})
    return result


def polyline_distance(a, b):
    """Symmetric vertex-to-polyline distance; a sampled diagnostic, not exact Hausdorff."""
    from .geometry import dot, length, sub

    def distance(p, line):
        best = float('inf')
        for x, y in zip(line, line[1:]):
            d = sub(y, x)
            t = max(0, min(1, dot(sub(p, x), d)/dot(d, d))) if dot(d, d) else 0
            best = min(best, length(sub(p, (x[0]+t*d[0], x[1]+t*d[1]))))
        return best
    return max(max(distance(p, b) for p in a), max(distance(p, a) for p in b))


def fragment_evidence(grammar, font, style):
    """Use the existing exact grammar only after reconstructing and verifying it."""
    import json

    import shape_grammar_full as grammar_engine

    decoder = grammar_engine.Decoder(grammar)
    if style not in grammar.get('styles', {}):
        raise ValueError('Style not present in fragment library')
    wanted = grammar_engine.digest(json.loads(font.json_dumps()))
    actual = grammar_engine.digest(json.loads(decoder.font(style).json_dumps()))
    if actual != wanted or grammar['styles'][style]['source_sha256'] != wanted:
        raise ValueError('Stale or inconsistent fragment library')
    groups = {}
    def walk(rule, found):
        if rule in found:
            return
        if 'join' in grammar['rules'][rule]:
            found.add(rule)
            for child in grammar['rules'][rule]['join']:
                walk(child, found)
    layers = grammar['styles'][style]['layers']
    layer = next(x for x in layers if x['name'] == font.layers.defaultLayer.name)
    for name, recipe in layer['glyphs'].items():
        found = set()
        for contour in recipe['contours']:
            for rule in contour['rules']:
                walk(rule, found)
        for rule in found:
            groups.setdefault(rule, []).append(name)
    return {'status': 'verified-exact-reconstruction', 'style': style,
            'shared_fragments': {k: sorted(v) for k, v in sorted(groups.items()) if len(v) > 1},
            'scope': 'Exact directed boundary fragments; sharing does not establish a common anatomical role.'}
