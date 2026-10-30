"""Read-only component expansion for local counter observations.

Expansion preserves winding and instance paths; it does not union overlaps or
claim that generated outlines inherited any unrecorded construction recipe.
"""

import math

from fontTools.misc.transform import Identity, Transform

from .geometry import Outline


def observed_outline(font, name, source_sha256):
    contours, origins, issues = [], [], []

    def visit(glyph_name, transform, path, ancestors):
        if glyph_name in ancestors or glyph_name not in font:
            issues.append({'reason': 'Component cycle' if glyph_name in ancestors else 'Missing component',
                           'component_path': path, 'source_glyph': glyph_name})
            return
        if len(path) > 64:
            issues.append({'reason': 'Component nesting exceeds observation limit', 'component_path': path})
            return
        glyph = font[glyph_name]
        # Draw contours individually so omitted/open contours cannot shift source indices.
        for index, contour in enumerate(glyph.contours):
            pen = Outline()
            contour.draw(pen)
            if pen.issues:
                issues.append({'reason': 'Open contour prevents complete observation',
                               'source_glyph': glyph_name, 'source_contour': index, 'component_path': path})
            for segments in pen.contours:
                if not segments:
                    continue
                contours.append([tuple(transform.transformPoint(p) for p in segment) for segment in segments])
                origins.append({'source_glyph': glyph_name, 'source_contour': index,
                                'component_path': path, 'transform': list(transform),
                                'source_sha256': source_sha256})
        for index, component in enumerate(glyph.components):
            values = tuple(component.transformation)
            if (not all(math.isfinite(v) for v in values)
                    or abs(values[0]*values[3]-values[1]*values[2]) < 1e-12):
                issues.append({'reason': 'Non-finite or singular component transform',
                               'source_glyph': glyph_name, 'component_path': path+[index]})
                continue
            combined = transform.transform(Transform(*values))
            if not all(math.isfinite(v) for v in combined):
                issues.append({'reason': 'Non-finite composed component transform', 'component_path': path+[index]})
                continue
            visit(component.baseGlyph, combined, path+[index], ancestors+(glyph_name,))

    visit(name, Identity, [], ())
    # A partial ink field can manufacture counters and terminal closures.
    return {'status': 'unresolved' if issues else 'complete',
            'contours': [] if issues else contours, 'origins': [] if issues else origins,
            'issues': issues, 'source_sha256': source_sha256}
