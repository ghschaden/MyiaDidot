"""Trial: the Italic's raw small-cap drafts fitted by redraw.py before the
generator takes them (docs/claude/longtail.md, family 3).

    python scripts/pilot/sc_draft_fit.py fit OUT.ufo OUT.json NAME ...
    python scripts/pilot/sc_draft_fit.py run OUT.ufo FITTED.ufo[,...] FITTED.json[,...] [--skip NAME ...]

fit: each stored draft named (sources/drafts/Italic-smallcaps.ufo, the
upright frame, as FontForge made it) through redraw.redraw and its gate,
no spec; the fitted ones into OUT.ufo, the reports with "fail" and "look"
into OUT.json. One core; split the names over several calls.

run: make_italic.py --out OUT.ufo (a scratch run: sources/ untouched), with
fontforge_inputs.drafts handing over the fitted draft in place of the
stored one for every name that passed the gate and is not skipped. So the
fit comes before weight_thick, as_capitals and the finishing passes, on
the raw draft. Compare OUT.ufo with the committed Italic afterwards
(redraw_sweep.py --against, quality/checks.py).

--skip lopsided leaves out the drafts whose fit has a curve with one handle
of LOP_SHORT units or less and the other of LOP_LONG or more that the raw
draft had not (the quarter-turn come out square, docs/claude/redraw.md).
"""

import json
import math
import os
import runpy
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ufoLib2  # noqa: E402

DRAFTS = ROOT / "sources/drafts/Italic-smallcaps.ufo"
LOP_SHORT, LOP_LONG = 6, 40


def lopsided(glyph):
    """the curves with one handle of LOP_SHORT or less and the other of
    LOP_LONG or more: (start x, start y, first handle, second handle)"""
    out = []
    for c in glyph.contours:
        pts = list(c.points)
        n = len(pts)
        on = [i for i, p in enumerate(pts) if p.type]
        for a, b in zip(on, on[1:] + [on[0] + n]):
            if b - a != 3:
                continue
            p0, p1, p2, p3 = (pts[(a + k) % n] for k in range(4))
            h1, h2 = math.hypot(p1.x - p0.x, p1.y - p0.y), math.hypot(p3.x - p2.x, p3.y - p2.y)
            if min(h1, h2) <= LOP_SHORT and max(h1, h2) >= LOP_LONG:
                out.append((round(p0.x), round(p0.y), round(h1), round(h2)))
    return out


def fit(out_path, json_path, names):
    import redraw

    store = ufoLib2.Font.open(DRAFTS, lazy=False)
    out, reports = ufoLib2.Font(), {}
    for name in names:
        try:
            new, report = redraw.redraw(store[name])
        except Exception as e:  # refused by the tool
            reports[name] = {"refused": str(e), "fail": [str(e)]}
            print(f"{name:16} refused: {e}", flush=True)
            continue
        fail, look = redraw.gate(report)
        report["fail"], report["look"] = fail, look
        report["lopsided"] = len(lopsided(new)) > len(lopsided(store[name]))
        reports[name] = json.loads(json.dumps(report, default=str))
        print(f"{name:16} {report['nodes_before']:3} -> {report['nodes_after']:3}  dev {report['dev']:4}  "
              f"jump {report['jump_before']}->{report['jump']}  "
              + ("FAIL: " + "; ".join(fail) if fail else "candidate")
              + (f"  [look: {'; '.join(look)}]" if look else ""), flush=True)
        new.lib.clear()
        out.layers.defaultLayer.insertGlyph(new, name)
    out.save(out_path, overwrite=True)
    Path(json_path).write_text(json.dumps(reports, indent=1))


def run(out, ufos, jsons, skip):
    import fontforge_inputs

    store = ufoLib2.Font.open(DRAFTS, lazy=False)
    fitted = {}
    for u, j in zip(ufos.split(","), jsons.split(",")):
        font = ufoLib2.Font.open(u, lazy=False)
        for name, r in json.loads(Path(j).read_text()).items():
            if r["fail"] or name in skip:
                continue
            if "lopsided" in skip and len(lopsided(font[name])) > len(lopsided(store[name])):
                continue
            fitted[name] = font[name]
    stored = fontforge_inputs.drafts

    def drafts(up, height, stem, redraft=False, keep=False):
        got = stored(up, height, stem, redraft=redraft, keep=keep)
        taken = [name for name in fitted if name in got]
        for name in taken:
            got[name] = fitted[name]
        sys.stderr.write(f"sc_draft_fit: {len(taken)} drafts taken as fitted\n")
        return got

    fontforge_inputs.drafts = drafts
    sys.argv = [str(ROOT / "scripts/make_italic.py"), "--out", out]
    runpy.run_path(sys.argv[0], run_name="__main__")


def main():
    if len(sys.argv) < 5 or sys.argv[1] not in ("fit", "run"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "fit":
        fit(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        rest = sys.argv[5:]
        run(sys.argv[2], sys.argv[3], sys.argv[4], set(rest[1:]) if rest[:1] == ["--skip"] else set())


if __name__ == "__main__":
    main()
