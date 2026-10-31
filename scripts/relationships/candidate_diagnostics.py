"""Explain counter-discovery gates without promoting rejected geometry."""

import math

from .arches import upper_arches
from .identity import digest
from .observation import observed_outline
from .returns import RETURN_POLICY, lower_returns


def candidate_diagnostics(font, names, source_sha256):
    """Trace existing extrema in the deskewed font frame, retaining provenance.

    The caller must pin and verify the source snapshot. A rejected seed is not a
    terminal, a branch classification, or a relationship candidate. No extrema
    inside a labelled box means no local observation, not anatomical absence.
    """
    em = font.info.unitsPerEm
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    traces, observations = [], {}
    for name in sorted(names):
        outline = observed_outline(font, name, source_sha256)
        observations[name] = {k: v for k, v in outline.items() if k != 'contours'}
        for detector in ('lower_returns', 'upper_arches'):
            local = []
            if detector == 'lower_returns':
                lower_returns(outline['contours'], [], em, slant, diagnostics=local)
            else:
                upper_arches(outline['contours'], em, slant, diagnostics=local)
            for trace in local:
                trace.pop('geometry_id', None)
                origin = outline['origins'][trace['contour']]
                traces.append({**trace, 'glyph': name, 'detector': detector,
                               'source_sha256': source_sha256, 'contour_origin': origin,
                               'id': 'seed-'+digest([source_sha256, name, detector, origin,
                                                   trace['point']])[:24]})
    return {'format': 'myiadidot-counter-diagnostics-v1', 'source_sha256': source_sha256,
            'policy': dict(RETURN_POLICY), 'scope': sorted(names),
            'coordinate_frame': 'deskewed font units', 'units_per_em': em, 'slant': slant,
            'traces': traces, 'observations': observations,
            'limitations': ['First failed discovery gate only; later gates were not evaluated.',
                            'Rejected seeds do not supply arm-level terminal evidence or branch anatomy.',
                            'Missing extrema and incomplete outlines remain unobserved.']}
