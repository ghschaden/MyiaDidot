"""Build a review-only Roman t-dot clearance proposal; leave masters untouched."""
import json
import subprocess
import tarfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import ufoLib2
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path("build/roman-t-dot-review")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    # Pin the accepted before-state so this proof remains reproducible after integration.
    reference = ROOT / "reference"
    reference.mkdir(exist_ok=True)
    archive = subprocess.run(
        ["git", "archive", "7b2a1117", "sources/MyiaDidot-Regular.ufo", "sources/MyiaDidot-Bold.ufo"],
        check=True, capture_output=True,
    )
    with tarfile.open(fileobj=BytesIO(archive.stdout)) as files:
        files.extractall(reference, filter="data")
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1100">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="sans-serif" fill="black">',
           '<text x="30" y="35" font-size="24">Roman ṫ — dot clearance proposal</text>',
           '<text x="30" y="65" font-size="15">2026-10-25 · Match ż clearance; preserve horizontal placement and base drawings</text>']
    report = {}
    for si, style in enumerate(("Regular", "Bold")):
        font = ufoLib2.Font.open(reference / f"sources/MyiaDidot-{style}.ufo")
        trial = deepcopy(font)
        mark_bounds = font["dotaccent"].getBounds(font)
        gap_z = (font["zdotaccent"].getBounds(font).yMax
                 - (mark_bounds.yMax - mark_bounds.yMin) - font["z"].getBounds(font).yMax)
        dot = next(c for c in trial["uni1E6B"].components if c.baseGlyph == "dotaccent")
        gap_t = font["dotaccent"].getBounds(font).yMin + dot.transformation[5] - font["t"].getBounds(font).yMax
        dy = round(gap_z - gap_t)
        dot.transformation = (*dot.transformation[:5], dot.transformation[5] + dy)
        assert trial["uni1E6B"].width == font["uni1E6B"].width
        assert trial["uni1E6B"].getBounds(trial).yMax == font["uni1E6B"].getBounds(font).yMax + dy
        report[style] = {"current_gap": gap_t, "proposal_gap": gap_z, "dot_shift_y": dy}
        trial.save(ROOT / f"Trial-{style}.ufo", overwrite=True)
        for vi, (label, f) in enumerate((("Current", font), ("Proposal", trial))):
            x = 30 + vi * 550
            y = 110 + si * 485
            svg.append(f'<text x="{x}" y="{y}" font-size="20">{style} / {label}</text>')
            svg.append(f'<text x="{x}" y="{y+28}" font-size="14">Dot gap: {gap_t if vi == 0 else gap_z:g} units</text>')

            def row(names, baseline, scale, x=x, f=f):
                pos = x
                for name in names:
                    pen = SVGPathPen(f)
                    f[name].draw(pen)
                    svg.append(f'<path d="{pen.getCommands()}" transform="translate({pos},{baseline}) scale({scale},{-scale})"/>')
                    pos += f[name].width * scale

            row(["t", "uni1E6B", "zdotaccent"], y + 240, .115)
            cmap = {g.unicode: g.name for g in f if g.unicode is not None}
            for j, scale in enumerate((.018, .024, .032)):
                row([cmap[ord(c)] for c in "t ṫ ż  ṫa ṫe ṫi aṫa"], y + 300 + j * 58, scale)
    svg.append('<text x="30" y="1080" font-size="14">Review proposal only. Production sources and fonts unchanged.</text></g></svg>')
    source = ROOT / "comparison.svg"
    source.write_text("\n".join(svg))
    (ROOT / "measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    for fmt, target in (("png", ROOT / "comparison.png"),
                        ("pdf", Path("proofs/roman-t-dot-spacing-review-2026-10-25.pdf"))):
        subprocess.run(["rsvg-convert", "-f", fmt, str(source), "-o", str(target)], check=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
