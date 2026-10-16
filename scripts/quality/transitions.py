"""transitions.py STYLE: the stroke's thickness traced round each round
letter's outer outline; counts the wobbles (local ups and downs of more
than 4% of the stem beyond the expected thick-thin rhythm) and the
steepest change, against Didot references."""
import math
import statistics
import sys
from pathlib import Path

import numpy as np
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MYIA, REFS, Face, runs

CHARS = "ocebdpqgsaOCGQDBPRSUJοσερωоседэяюбвзЭЯЮСОЗВ"
style = sys.argv[1]
refs = [p for p in REFS[style] if any(k in p for k in ("Bodoni", "OldStandard", "GFSDidot"))]


def polyline(path):
    rec = RecordingPen()
    path.draw(rec)
    contours, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op == "curveTo":
            p0 = cur[-1]; p1, p2, p3 = args
            for k in range(1, 13):
                t = k / 12; u = 1 - t
                cur.append((u**3 * p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                            u**3 * p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
        elif op == "qCurveTo":
            from fontTools.pens.basePen import decomposeQuadraticSegment
            pts = list(args)
            if pts[-1] is None:  # an all-off-curve contour: rare, skip its curve
                continue
            p0 = cur[-1]
            for q1, q2 in decomposeQuadraticSegment(pts):
                for k in range(1, 9):
                    t = k / 8; u = 1 - t
                    cur.append((u*u*p0[0] + 2*u*t*q1[0] + t*t*q2[0], u*u*p0[1] + 2*u*t*q1[1] + t*t*q2[1]))
                p0 = q2
        elif op in ("closePath", "endPath"):
            contours.append(cur)
    return contours


def profile(face, ch):
    path = face.path(ch)
    cs = [c for c in polyline(path) if len(c) >= 3]
    if not cs:
        return None
    segs = [(c[i], c[(i + 1) % len(c)]) for c in cs for i in range(len(c))]
    A = np.array([s[0] for s in segs]); Dd = np.array([s[1] for s in segs]) - A
    outer = max(cs, key=lambda c: abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(c, c[1:] + c[:1]))))
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(outer, outer[1:] + outer[:1]))
    sgn = 1 if area > 0 else -1  # ccw: inside is to the left
    # resample the outer outline evenly
    pts = np.array(outer + [outer[0]])
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    N = 300
    ts = np.linspace(0, s[-1], N, endpoint=False)
    xs = np.interp(ts, s, pts[:, 0]); ys = np.interp(ts, s, pts[:, 1])
    th = []
    for i in range(N):
        dx = xs[(i + 1) % N] - xs[i - 1]; dy = ys[(i + 1) % N] - ys[i - 1]
        L = math.hypot(dx, dy) or 1
        ux, uy = -dy / L * sgn, dx / L * sgn  # inward
        den = Dd[:, 0] * uy - Dd[:, 1] * ux
        ok = np.abs(den) > 1e-9
        wx, wy = A[:, 0] - xs[i], A[:, 1] - ys[i]
        t = np.where(ok, (Dd[:, 0] * wy - Dd[:, 1] * wx) / np.where(ok, den, 1), -1)
        u = np.where(ok, (ux * wy - uy * wx) / np.where(ok, den, 1), -1)
        hit = ok & (t > 2) & (u >= 0) & (u <= 1)
        th.append(t[hit].min() if hit.any() else np.nan)
    th = np.array(th)
    return th, s[-1] / N


def wobbles(th, stem):
    # extrema of the profile (circular), small ones that reverse within 4% of the stem
    v = np.nan_to_num(th, nan=0)
    k = np.ones(5) / 5
    v = np.convolve(np.concatenate([v[-2:], v, v[:2]]), k, mode="valid")
    ext = [i for i in range(len(v)) if (v[i] - v[i - 1]) * (v[(i + 1) % len(v)] - v[i]) < 0]
    small = 0
    for a, b in zip(ext, ext[1:] + ext[:1]):
        if abs(v[b] - v[a]) < 0.04 * stem:
            small += 1
    jump = np.nanmax(np.abs(np.diff(np.concatenate([v, v[:1]])))) / stem
    return len(ext), small, jump


faces = [Face(MYIA.format(style))] + [Face(p) for p in refs]
print(f"{style}: extrema of the thickness round the outline / small wobbles / steepest step (x stem per sample)")
rows = {}
for face in faces:
    r = runs(face.path("n"), face.xh * 0.4)
    stem = r[0][1] - r[0][0] if r else 150
    for ch in CHARS:
        if not face.has(ch):
            continue
        pr = profile(face, ch)
        if pr is None:
            continue
        rows.setdefault(ch, {})[face.name] = wobbles(pr[0], stem)
myia = faces[0].name
bad = []
for ch, vals in rows.items():
    if myia not in vals:
        continue
    m = vals[myia]
    others = [v for k, v in vals.items() if k != myia]
    if not others:
        continue
    rs = statistics.median(v[1] for v in others); rj = statistics.median(v[2] for v in others)
    line = f"  {ch}  myia {m[0]:3} ext {m[1]:3} wobbles  step {m[2]:.2f}   refs: wobbles {rs:4.1f} step {rj:.2f}"
    if m[1] > rs + 2 or m[2] > 1.5 * rj + 0.05:
        bad.append((m[1] - rs + 10 * (m[2] - rj), line + "   <--"))
    else:
        bad.append((-99, line))
bad.sort(reverse=True)
for _, l in bad:
    print(l)
