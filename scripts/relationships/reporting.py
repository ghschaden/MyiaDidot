"""Read-only source proofs and searchable reports."""

import html
import json
import math

from fontTools.pens.svgPathPen import SVGPathPen

from .geometry import POLICY


def proof(font, names, records, path):
    em, width, row_height = font.info.unitsPerEm, 1100, 300
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{max(1,len(names))*row_height}">',
             '<rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">']
    slant = math.tan(math.radians(-(font.info.italicAngle or 0)))
    for i, name in enumerate(names):
        g = font[name]
        box = g.getBounds(font) or (0, 0, em, em)
        scale = min(210/max(em, box[3]-box[1]), 430/max(em, box[2]-box[0]))
        x, baseline = 25-box[0]*scale, i*row_height+55+box[3]*scale
        pen = SVGPathPen(font)
        g.draw(pen)
        lines.append(f'<text x="20" y="{i*row_height+25}" font-size="18">{html.escape(name)}</text>')
        lines.append(f'<path d="{pen.getCommands()}" transform="translate({x},{baseline}) scale({scale},{-scale})" fill="#333"/>')
        local = [r for r in records if r['glyph'] == name]
        for j, r in enumerate(local):
            if r['relationship'] in ('lower-return', 'upper-arch'):
                for turn_path in r['paths']:
                    pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in turn_path)
                    lines.append(f'<polyline points="{pts}" fill="none" stroke="#007c91" stroke-width="2"/>')
                for section in r['counter_sections']:
                    y = section['y']
                    lines.append(f'<line x1="{x+(section["left"]+slant*y)*scale}" y1="{baseline-y*scale}" x2="{x+(section["right"]+slant*y)*scale}" y2="{baseline-y*scale}" stroke="#b52a90" stroke-width=".7"/>')
                for context in r.get('arm_context', []):
                    for section in context['sections']:
                        a, b = section['p'], section['q']
                        lines.append(f'<line x1="{x+(a[0]+slant*a[1])*scale}" y1="{baseline-a[1]*scale}" x2="{x+(b[0]+slant*b[1])*scale}" y2="{baseline-b[1]*scale}" stroke="#23a05b" stroke-width=".9"/>')
                    if context['cap_status'] == 'short-contour-cap':
                        pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in context['cap_trace'])
                        lines.append(f'<polyline points="{pts}" fill="none" stroke="#d77a00" stroke-width="1.5"/>')
                if r['relationship'] == 'upper-arch':
                    bands = [n for side in r['neighbours'] for n in side] + r.get('lower_terminals', [])
                    for band in bands:
                        for section in band['sections']:
                            if section:
                                a, b = section['p'], section['q']
                                lines.append(f'<line x1="{x+(a[0]+slant*a[1])*scale}" y1="{baseline-a[1]*scale}" x2="{x+(b[0]+slant*b[1])*scale}" y2="{baseline-b[1]*scale}" stroke="#23a05b" stroke-width="1"/>')
                    cap_paths = r['cap_traces'] + [t['cap_trace'] for t in r.get('lower_terminals', []) if t['cap_verified']]
                    for cap_path in cap_paths:
                        pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in cap_path)
                        lines.append(f'<polyline points="{pts}" fill="none" stroke="#d77a00" stroke-width="1.5"/>')
                    for conflict in r['conflicts']:
                        px, py = conflict['terminal_bottom']
                        lines.append(f'<circle cx="{x+(px+slant*py)*scale}" cy="{baseline-py*scale}" r="9" fill="none" stroke="#c52d21" stroke-width="2"/>')
                terminal_contexts = r.get('terminal_context', []) or [c.get('terminal_context', {}) for c in r.get('arm_context', [])]
                for terminal in terminal_contexts:
                    if terminal.get('status') == 'verified-contour-terminal':
                        pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in terminal['trace'])
                        lines.append(f'<polyline points="{pts}" fill="none" stroke="#7141b5" stroke-width="1.5"/>')
                desc = f"{r['geometry_id'][:12]} {r['status']}; role {r['role']}; scope {r.get('anatomical_scope', {}).get('kind', 'unresolved')}"
                if r.get('conflicts'):
                    desc = f"{r['geometry_id'][:12]} {r['role']}: " + ', '.join(c['kind'] for c in r['conflicts'])
            elif r['relationship'] == 'curve-to-line':
                pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in r['span'])
                color = '#c52d21' if r['review_notice'] else '#007c91'
                lines.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
                desc = f"{r['id'][:12]} {r['family']}; reversal {r['metrics']['lateral_reversal_em']:.5f} em"
            elif r['relationship'] == 'paired-stroke-boundaries':
                for edge, color in zip(r['edges'], ('#007c91', '#ad3e00')):
                    pts = ' '.join(f'{x+(p[0]+slant*p[1])*scale},{baseline-p[1]*scale}' for p in edge)
                    lines.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
                for section in r['sections'][::2]:
                    a, b = section['p'], section['q']
                    lines.append(f'<line x1="{x+(a[0]+slant*a[1])*scale}" y1="{baseline-a[1]*scale}" x2="{x+(b[0]+slant*b[1])*scale}" y2="{baseline-b[1]*scale}" stroke="#23a05b" stroke-width=".7"/>')
                desc = f"{r['id'][:12]} paired; width {r['metrics']['median_width_em']:.4f} em; taper {r['metrics']['linear_taper']:+.3f}"
            else:
                desc = f"{r['id'][:12]} attachment: {r['status']} ({r.get('base') or 'unknown base'})"
                if r['status'] == 'confirmed':
                    for evidence in r['anchor_evidence']:
                        if evidence['distance_em'] <= POLICY['anchor_tolerance_em']:
                            px, py = evidence['base_position']
                            lines.append(f'<circle cx="{x+px*scale}" cy="{baseline-py*scale}" r="4" fill="#a50080"/>')
            if j < 10:
                lines.append(f'<text x="485" y="{i*row_height+50+j*21}" font-size="13">{html.escape(desc)}</text>')
        if not local:
            lines.append(f'<text x="485" y="{i*row_height+50}" font-size="13">No relationship reported; consult omissions and ancestry in JSON.</text>')
        if len(local) > 10:
            lines.append(f'<text x="485" y="{i*row_height+275}">More relationships in JSON report</text>')
    lines.append('</g></svg>')
    path.write_text('\n'.join(lines))



def write_html(report, out):
    rows = ''.join(f'<tr id="{r["id"]}"><td>{r["id"]}</td><td>{html.escape(r["glyph"])}</td><td>{html.escape(r["relationship"])}</td>'
                   f'<td>{html.escape(r["status"])}</td><td>{html.escape(r.get("family") or "—")}</td>'
                   f'<td>{html.escape(r.get("reason", r.get("explanation", "")))}</td></tr>'
                   for r in report['relationships'])
    ranked = ''.join('<tr><td>'+html.escape(r['base_family'])+'</td><td>'+html.escape(', '.join(r['members']))+
                     '</td><td>'+html.escape(r['best_match']['reason'])+'</td><td>'+str(r['matching_spans'])+'</td></tr>'
                     for r in report.get('query', {}).get('ranked_families', []))
    page = ('<!doctype html><meta charset="utf-8"><title>Shape relationships</title>'
            '<style>body{font:16px system-ui;max-width:1400px;margin:2em auto}td,th{padding:.5em;text-align:left;border-bottom:1px solid #ddd}</style>'
            f'<h1>Shape relationships</h1><p>Source: {html.escape(report['source']['path'])}<br>SHA-256: {report['source']['sha256']}</p><p>Read-only structural discovery. Groups are review candidates, not repair authorisations.</p>'
            '<p><a href="report.json">Full evidence and provenance graph</a> · <a href="proof.svg">Focused visual proof</a></p>'
            f'<p>{html.escape(json.dumps(report["summary"]))}</p>'
            f'<details><summary>Related-glyph query and matching evidence</summary><pre>{html.escape(json.dumps(report.get("query", {}), ensure_ascii=False, indent=2))}</pre></details>'
            f'<details open><summary>Constituent reuse</summary><pre>{html.escape(json.dumps(report.get("constituent_reuse", {}), ensure_ascii=False, indent=2))}</pre></details>'
            '<h2>Ranked base families</h2><p>Explicit derivative ancestry is grouped; inferred peers remain candidates.</p>'
            '<table><tr><th>Base family</th><th>Members</th><th>Matching evidence</th><th>Spans</th></tr>'+ranked+'</table>'
            '<p><label>Filter relationships <input id="filter" type="search" placeholder="glyph, family, or status"></label></p>'
            '<table class="findings"><tr><th>ID</th><th>Glyph</th><th>Relationship</th><th>Status</th><th>Family</th><th>Why</th></tr>'+rows+'</table>'
            '<script>document.getElementById("filter").addEventListener("input",function(){const q=this.value.toLowerCase();document.querySelectorAll(".findings tr").forEach((r,i)=>{if(i)r.hidden=!r.textContent.toLowerCase().includes(q)});});</script>')
    if 'lower_returns' in report:
        page += ('<h2>Lower returns</h2><p><a href="returns.svg">Counter-turn overlay</a></p>'
                 '<pre>'+html.escape(json.dumps(report['lower_returns'], ensure_ascii=False, indent=2))+'</pre>')
    if 'upper_arches' in report:
        page += ('<h2>Upper arches</h2><p><a href="arches.svg">Arch and conflict overlay</a></p>'
                 '<pre>'+html.escape(json.dumps(report['upper_arches'], ensure_ascii=False, indent=2))+'</pre>')
    (out/'index.html').write_text(page)
