"""Pair spacing for every style and script in one table: the frequent pairs
outside the references' range (Latin: pairs.py; Greek and Cyrillic:
greek_pairs.py outside), and for Greek those where Charis and Libertinus
agree against Myia (greek_pairs.py agreeing_against, the test's rule), with
how many of those are on the known list (greek-pairs*.txt).

    python scripts/quality/pair_summary.py [STYLE ...]

Measures the built fonts (fonts/otf/: make otf first) against the
references (build/refs/, the installed Libertinus and Charis) on the UDHR
texts (make udhr). The styles run in parallel.
"""

import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT

STYLES = ["Regular", "Italic", "Bold", "BoldItalic"]


def listed(name, style):
    path = ROOT / "tests" / "data" / (name if style == "Regular" else name.replace(".txt", f"-{style}.txt"))
    if not path.exists():
        return set()
    return {line.split("#")[0].strip() for line in path.read_text(encoding="utf-8").splitlines()} - {""}


def latin(style):
    out = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "quality" / "pairs.py"), style],
                         capture_output=True, text=True, check=False, cwd=ROOT)
    m = re.search(r"outside the references' range by more than [\d.]+ n-gaps: (\d+):(.*)", out.stdout)
    if not m:
        return None, (out.stderr.strip().splitlines() or ["no output"])[-1]
    return int(m[1]), m[2].split()


def measure(style):
    from greek_pairs import agreeing_against, outside

    n, latin_pairs = latin(style)
    greek_out = outside(style, script="greek")
    greek_cl = agreeing_against(style) or {}
    cyr_out = outside(style, script="cyrillic")
    return {"style": style, "latin": (n, latin_pairs), "greek": greek_out, "greek_cl": greek_cl,
            "greek_known": listed("greek-pairs.txt", style), "cyrillic": cyr_out,
            "cyrillic_known": listed("cyrillic-pairs.txt", style)}


def pairs_text(found, known=frozenset()):
    return " ".join(f"{p}{'*' if p in known else ''} {off:+.2f}" for p, off in sorted(found.items(), key=lambda t: t[1]))


def main():
    styles = sys.argv[1:] or STYLES
    if not (ROOT / "build" / "udhr" / "udhr_eng.xml").exists():
        sys.exit("no UDHR texts: make udhr")
    with ProcessPoolExecutor(len(styles)) as pool:
        results = list(pool.map(measure, styles))
    print("frequent pairs outside the references' range (Greek C+L: Charis and Libertinus agree against "
          "Myia, the test's rule; * on the known list)\n")
    print(f"{'style':11} {'Latin':>6} {'Greek':>6} {'Greek C+L':>10} {'Cyrillic':>9}")
    for r in results:
        n = r["latin"][0]
        cl = f"{len(r['greek_cl'])} ({len(set(r['greek_cl']) - r['greek_known'])} new)"
        print(f"{r['style']:11} {'?' if n is None else n:>6} {len(r['greek']):>6} {cl:>10} {len(r['cyrillic']):>9}")
    for r in results:
        lines = []
        n, latin_pairs = r["latin"]
        if n is None:
            lines.append(f"  Latin: pairs.py failed: {latin_pairs}")
        elif n:
            lines.append(f"  Latin: {' '.join(latin_pairs)}")
        if r["greek"]:
            lines.append(f"  Greek: {pairs_text(r['greek'])}")
        if r["greek_cl"]:
            lines.append(f"  Greek C+L: {pairs_text(r['greek_cl'], r['greek_known'])}")
        if r["cyrillic"]:
            lines.append(f"  Cyrillic: {pairs_text(r['cyrillic'], r['cyrillic_known'])}")
        if lines:
            print(f"\n{r['style']} (offsets in n n gaps, negative = tighter than the references):")
            print("\n".join(lines))
    print("\ndetails: scripts/quality/pairs.py STYLE, scripts/quality/greek_pairs.py STYLE [--script cyrillic]")


if __name__ == "__main__":
    main()
