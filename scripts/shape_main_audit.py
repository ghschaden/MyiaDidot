"""Read-only snapshot audit of the new Bold Italic construction in main."""

import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from uuid import uuid4

import ufoLib2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shape_fairing as fair

NAMES = ('h', 'n', 'u', 'o')


def curve_report(font, name):
    contours = fair.native_contours(font, name)
    audits, closing = [], []
    for contour in contours:
        audits.append(fair.curvature.audit(contour))
        closing.extend(fair.curvature.audit([contour[-1], contour[0]])['joins'])
    joins = [j for a in audits for j in a['joins']] + closing
    near = [j for j in joins if j['tangent_angle_degrees'] is not None and j['tangent_angle_degrees'] < 2]
    return {'contours': audits, 'closing_joins': closing,
            'segments': sum(map(len, contours)),
            'interior_inflections': sum(a['interior_inflection_count'] for a in audits),
            'joins_2_to_45_degrees': sum(2 <= j['tangent_angle_degrees'] < 45 for j in joins if j['tangent_angle_degrees'] is not None),
            'unresolved_joins': sum(j['tangent_angle_degrees'] is None for j in joins),
            'largest_near_smooth_curvature_jump': max((abs(j['curvature_jump_inverse_units']) for j in near if j['curvature_jump_inverse_units'] is not None), default=0),
            'advance': font[name].width, 'bounds': font[name].getBounds(font)}


def main():
    c = fair.seams.consistency
    out = c.safe_output(c.ROOT/'build/glyph-review/main-stroke-audit')
    run = out/'runs'/uuid4().hex[:12]
    run.mkdir(parents=True)
    main_root = Path('/home/gerhard/src/MyiaDidot')
    revision = subprocess.check_output(['git', 'rev-parse', 'main'], text=True).strip()
    relative = 'sources/MyiaDidot-BoldItalic.ufo'
    archive = subprocess.check_output(['git', 'archive', revision, relative])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(run/'committed', filter='data')
    committed = run/'committed'/relative
    working = run/'working.ufo'
    live = main_root/relative
    before_hash = c.content_hash(live)
    shutil.copytree(live, working)
    if before_hash != c.content_hash(live) or before_hash != c.content_hash(working):
        raise RuntimeError('Live UFO changed during snapshot; rerun')
    # Preserve construction inputs for identifying this uncommitted state.
    inputs = {}
    for name in ('scripts/stroke_bold.py', 'scripts/make_bold.py', 'docs/claude/styles.md', 'FONT-DESIGN.md'):
        source = main_root/name
        if source.exists():
            target = run/'implementation'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            inputs[name] = c.content_hash(target)
    fonts = {'committed': ufoLib2.Font.open(committed, lazy=False), 'working': ufoLib2.Font.open(working, lazy=False)}
    report = {'main_revision': revision, 'working_ufo_sha256': before_hash,
              'committed_ufo_sha256': c.content_hash(committed), 'implementation_snapshot_sha256': inputs,
              'working_state': 'uncommitted snapshot; generator files are provenance, not a reproduction claim',
              'glyphs': {}, 'release_ready': False}
    for name in NAMES:
        a, b = fonts['committed'], fonts['working']
        old_curves, _ = fair.seams.deskew(a, name)
        new_curves, _ = fair.seams.deskew(b, name)
        pa, pb = fair.seams.path_for(old_curves), fair.seams.path_for(new_curves)
        clearance = fair.seams.clearance(pa, pb, pa.bounds)
        normals = fair.sections(a, b, name)
        normals['rays_over_10_percent'] = sum(bool(abs(r['change_percent']) > 10) for r in normals['rays'])
        normals['largest_changes'] = sorted(normals['rays'], key=lambda r: abs(r['change_percent']), reverse=True)[:5]
        gaps = clearance['gaps']
        clearance['max_gap_reduction_percent'] = max((100*(1-r['after_units']/r['before_units']) for r in gaps), default=0)
        report['glyphs'][name] = {'committed': curve_report(a, name), 'working': curve_report(b, name),
                                  'normal_sections': normals, 'clearance': clearance}
        fair.seams.curvature_proof(a, b, {'target': name}, run/f'{name}-curvature.svg', 'Committed main → working snapshot')
        print(name, report['glyphs'][name]['working']['interior_inflections'], 'inflections;',
              normals['rays_over_10_percent'], 'sections over 10%;', len(clearance['failures']), 'clearance alerts', flush=True)
    for label, font in fonts.items():
        affected = sorted(c.component_dependants(font, set(NAMES)))
        report.setdefault('lint', {})[label] = fair.seams.glyph_lint.lint(font, affected)
    report['new_lint'] = {n: [x for x in xs if x not in report['lint']['committed'].get(n, [])]
                          for n, xs in report['lint']['working'].items()}
    report['new_lint'] = {n: xs for n, xs in report['new_lint'].items() if xs}
    c.proof_renderer()(working, list(NAMES), run/'before-after.svg', before=committed,
                       texts=('minimum honour home', 'hoho noon high oh', 'h\u0302 o\u0308'), language='en', script='latn', anchors=True)
    report['limitations'] = ['Source outlines and unhinted compiled proof; no hinting or full release suite',
                             'Fixed original rays can confound shifted stroke positions with thickness; unresolved rays remain explicit',
                             '10% alerts reuse exploratory budgets and are not acceptance gates for a new design',
                             'Within-segment inflections and near-smooth join jumps are diagnostics, not defect counts']
    c.write_json(run/'report.json', report)
    c.write_json(out/'report.json', report)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><h1>Main Bold Italic stroke audit</h1>'
                                 '<p>Committed main versus an uncommitted snapshot. Diagnostic alerts are not acceptance decisions.</p>'
                                 f'<p><a href="{(run/"before-after.svg").relative_to(out)}">Before/after with peers and shaped words</a></p>'
                                 + ''.join(f'<p><a href="{(run/(n+"-curvature.svg")).relative_to(out)}">{n}: curvature comb</a></p>' for n in NAMES)
                                 + '<p><a href="report.json">Full measurements and source identities</a></p>')
    print('new lint', report['new_lint'], 'output', run, flush=True)


if __name__ == '__main__':
    main()
