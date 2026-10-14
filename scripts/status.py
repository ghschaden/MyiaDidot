"""One-line (or --long) project status, fast enough for an editor status line.

    python scripts/status.py [--long] [--json]

Reads the source UFOs directly (no build): glyph count, characters still
missing from the coverage target, and the last test run recorded in
build/test-status.json by the test suite.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import ufoLib2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CACHE = ROOT / "build" / "target-unicodes.json"


def target_unicodes():
    """The coverage target's code points, cached (glyphsets is slow to load)."""
    from coverage import TARGET

    if CACHE.exists():
        data = json.loads(CACHE.read_text())
        if data.get("sets") == TARGET:
            return data["sets"], {k: set(v) for k, v in data["unicodes"].items()}
    import glyphsets

    sets = {gs: sorted(glyphsets.unicodes_per_glyphset(gs)) for gs in TARGET}
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps({"sets": TARGET, "unicodes": sets}))
    return TARGET, {k: set(v) for k, v in sets.items()}


def ago(t):
    s = int(time.time() - t)
    if s < 90:
        return f"{s}s ago"
    if s < 5400:
        return f"{s // 60}m ago"
    if s < 172800:
        return f"{s // 3600}h ago"
    return f"{s // 86400}d ago"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    order, sets = target_unicodes()
    fonts = []
    for path in sorted((ROOT / "sources").glob("*.ufo")):
        ufo = ufoLib2.Font.open(path, lazy=True)
        cmap = {u for g in ufo for u in g.unicodes}
        seen, per_set = set(), []
        for gs in order:
            wanted = sets[gs] - seen
            seen |= wanted
            per_set.append((gs, len(wanted), len(wanted - cmap)))
        drafts = sum(1 for g in ufo if g.lib.get("org.myiadidot.smallcapDraft"))
        other_drafts = sum(1 for g in ufo if g.lib.get("org.myiadidot.draft"))
        fonts.append({
            "name": path.stem,
            "drafts": drafts,
            "other_drafts": other_drafts,
            "glyphs": len(ufo),
            "chars": len(cmap),
            "missing": len(seen - cmap),
            "sets": per_set,
        })

    tests = None
    status_file = ROOT / "build" / "test-status.json"
    if status_file.exists():
        tests = json.loads(status_file.read_text())

    if args.json:
        print(json.dumps({"fonts": fonts, "tests": tests}))
        return

    parts = []
    for f in fonts:
        style = f["name"].split("-", 1)[-1]
        part = f"{style}: {f['glyphs']} glyphs, {f['missing']} to go"
        if f["drafts"]:
            part += f", {f['drafts']} sc drafts to review"
        if f["other_drafts"]:
            part += f", {f['other_drafts']} other draft{'s' if f['other_drafts'] > 1 else ''}"
        parts.append(part)
    line = "Myia Didot · " + " · ".join(parts)
    if tests:
        mark = "✓" if tests["failed"] == 0 else f"✗ {tests['failed']} failing"
        line += f" · tests {mark} ({ago(tests['time'])})"
    else:
        line += " · tests not run"
    print(line)

    if args.long:
        for f in fonts:
            print(f"\n{f['name']}: {f['glyphs']} glyphs, {f['chars']} characters")
            for gs, n, miss in f["sets"]:
                bar = "done" if miss == 0 else f"{miss} missing"
                print(f"  {gs:26} {n - miss:4}/{n:<4} {bar}")
        if tests and tests["failures"]:
            print("\nfailing tests:")
            for t in tests["failures"]:
                print("  " + t)


if __name__ == "__main__":
    main()
