"""Compose recognisers without mutating the font."""

import json
import math
from collections import Counter, defaultdict

from .boundaries import BOUNDARY_POLICY, paired_boundaries
from .geometry import POLICY, Outline
from .identity import digest, identify
from .provenance import provenance
from .recognisers import attachments, transitions


def analyse(font, source_digest=None, *, paired=False, boundary_glyphs=None):
    em = font.info.unitsPerEm
    if not em or not math.isfinite(em) or em <= 0:
        raise ValueError('A finite positive unitsPerEm is required')
    if boundary_glyphs is not None and set(boundary_glyphs)-set(font.keys()):
        raise ValueError('Unknown glyph in paired-boundary scope')
    paired = paired or boundary_glyphs is not None
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    records, omissions = attachments(font), []
    for g in sorted(font, key=lambda g: g.name):
        pen = Outline()
        g.draw(pen)
        rows, issues = transitions(pen.contours, em, slant)
        if paired and (boundary_glyphs is None or g.name in boundary_glyphs):
            pairs, pair_notes = paired_boundaries(pen.contours, em, slant)
            rows.extend(pairs)
            issues.extend(pair_notes)
        for row in rows:
            row['glyph'] = g.name
        records.extend(rows)
        omissions.extend({"glyph": g.name, "reason": issue} for issue in pen.issues)
        omissions.extend({"glyph": g.name, **issue} for issue in issues)
    source_digest = source_digest or digest(json.loads(font.json_dumps()))
    identify(records, source_digest)
    groups = defaultdict(list)
    for r in records:
        if r['family']:
            groups[r['family']].append(r['id'])
    return {"format": "myiadidot-relationships-v2", "policy": dict(POLICY),
            "paired_boundary_policy": dict(BOUNDARY_POLICY) if paired else None,
            "paired_boundary_scope": sorted(boundary_glyphs if boundary_glyphs is not None else font.keys()) if paired else [],
            "source_identity": source_digest, "glyphs": sorted(font.keys()),
            "glyph_metadata": {g.name: {"own_contours": len(g.contours)} for g in font}, "provenance": provenance(font),
            "relationships": records, "families": dict(sorted(groups.items())), "omissions": omissions,
            "summary": dict(Counter(r['status'] for r in records)),
            "limitations": ["No repair or aesthetic acceptance is performed.",
                            "Curve and paired-section metrics are sampled source-outline diagnostics, not global topology or hinting guarantees.",
                            "Composite geometry is represented by ancestry, not redundantly analysed.",
                            "Flattened unrecorded derivations and shared stems are not inferred.",
                            "Only single-mark canonical decompositions with explicit components can be confirmed.",
                            "Recorded generator inputs are not verified part-level provenance."]}

