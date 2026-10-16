"""colour.py STYLE: per character, zone colour (ink in the main zone over
advance x zone height) and optical side space, each relative to the
script's n/H, Myia against the references; flags where Myia is outside the
references' range by more than a tolerance."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, OUT, REF_CHAR, REFS, SETS, Face, band, side, zone_of

style = sys.argv[1]
faces = [Face(MYIA.format(style))] + [Face(p) for p in REFS[style]]


def measure(face, ch, setname):
    if not face.has(ch):
        return None
    h = face.top("0") if setname == "figures" else zone_of(setname, face)
    p = face.path(ch)
    w = face.width(ch)
    ink = band(p, 0, h).area
    L, R = side(p, w, h, "L"), side(p, w, h, "R")
    return {"colour": abs(ink) / (w * h), "L": L / h if L is not None else None, "R": R / h if R is not None else None}


out = {}
for setname, chars in SETS.items():
    ref = REF_CHAR[setname]
    for face in faces:
        if not face.has(ref):
            continue
        base = measure(face, ref, setname)
        for ch in chars:
            m = measure(face, ch, setname)
            if not m:
                continue
            rel = {"colour": m["colour"] / base["colour"]}
            for k in "LR":
                if m[k] is not None:
                    rel[k] = m[k] - (base["L"] + base["R"]) / 2  # side space beyond n's/H's, per zone height
            out.setdefault(setname, {}).setdefault(ch, {})[face.name] = rel
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / f"colour-{style}.json", "w") as fh:
    json.dump(out, fh)
myia = faces[0].name
flags = []
for setname, chars in out.items():
    for ch, vals in chars.items():
        if myia not in vals:
            continue
        refs = {k: v for k, v in vals.items() if k != myia}
        if len(refs) < 3:
            continue
        for metric, tol in (("colour", 0.08), ("L", 0.025), ("R", 0.025)):
            rv = [v[metric] for v in refs.values() if metric in v]
            if metric not in vals[myia] or len(rv) < 3:
                continue
            mv = vals[myia][metric]
            lo, hi, med = min(rv), max(rv), statistics.median(rv)
            off = (mv - hi) if mv > hi else (mv - lo) if mv < lo else 0
            if abs(off) > tol:
                flags.append((setname, ch, metric, round(mv, 3), round(med, 3), round(lo, 3), round(hi, 3), round(off, 3)))
flags.sort(key=lambda f: -abs(f[-1]) / (0.08 if f[2] == "colour" else 0.025))
print(f"{style}: {len(flags)} flags (outside the references' range by more than 8% colour / 2.5% of the zone in side space)")
for f in flags:
    print("  {:9} {} {:6} myia {:7} refs median {:7} range {}..{}  off {}".format(*f))
