"""Source-pinned identities with segmentation-independent geometric locators."""

import hashlib
import json
from collections import defaultdict


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def rounded(value):
    if isinstance(value, (tuple, list)):
        return [rounded(v) for v in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


def identify(records, source_digest):
    groups = defaultdict(list)
    for row in records:
        if row['relationship'] == 'curve-to-line':
            geometry = {k: rounded(row[k]) for k in ('junction', 'line_direction')}
            geometry['curve_start'] = rounded(row['span'][0])
        elif row['relationship'] == 'paired-stroke-boundaries':
            ends = [sorted([rounded(edge[0]), rounded(edge[-1])]) for edge in row['edges']]
            geometry = {'edge_endpoints': sorted(ends)}
        else:
            geometry = {k: rounded(row.get(k)) for k in ('unicode', 'base', 'mark', 'transforms')}
        locator = {'glyph': row['glyph'], 'relationship': row['relationship'], 'geometry': geometry}
        row['locator'] = locator
        row['geometry_id'] = 'g-'+digest(locator)[:24]
        row['source_sha256'] = source_digest
        groups[row['geometry_id']].append(row)
    for key, rows in groups.items():
        for i, row in enumerate(rows):
            row['identity_status'] = 'unique' if len(rows) == 1 else 'ambiguous-coincident-locators'
            row['id'] = 'r-'+digest([source_digest, key])[:24]+(f'-{i+1}' if len(rows) > 1 else '')
    return records
