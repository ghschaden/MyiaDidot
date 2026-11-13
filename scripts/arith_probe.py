"""Which machine arithmetic the Bold Italic's stroking depends on (T3).

CI's `make reproduce` makes a dozen Bold Italic glyphs otherwise on AMD
runners with AVX-512 (EPYC 9V74, 9V45), never on Intel's with AVX-512 or
AMD's without (2026-11-13): something chooses its code by vendor and
AVX-512 past arithmetic.py's pins. This strokes a few of make_bold's own
jobs (scripts/data/arith_probe_jobs.json: w Q K fl ɲ ʀ ʷ ae.sc ... and
controls, captured from a run on the designer's machine) under several
settings of the environment, each in a fresh process, and prints a hash
of each result with the hash the designer's machine gives.

    python -I scripts/arith_probe.py          # the table
    python -I scripts/arith_probe.py --record # store this machine's hashes

A setting whose hashes all match the stored ones on a failing runner is
the pin that is missing; one that matches nowhere says the stroking is
not where the runs part (the difference comes after it).
"""

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts/data/arith_probe_jobs.json"
HASHES = ROOT / "scripts/data/arith_probe_hashes.json"

PINS = {
    "OPENBLAS_NUM_THREADS": "1",
    "OPENBLAS_CORETYPE": "Haswell",
    "NPY_DISABLE_CPU_FEATURES": "X86_V4 AVX512_ICL AVX512_SPR",
}
# glibc's own dispatch (libm, libc) told there is no AVX-512
NO_AVX512 = "glibc.cpu.hwcaps=-AVX512F,-AVX512CD,-AVX512BW,-AVX512DQ,-AVX512VL,-AVX512_VBMI,-AVX512_IFMA"
SETTINGS = {
    "pins": PINS,
    "pins+glibc": {**PINS, "GLIBC_TUNABLES": NO_AVX512},
    "pins+npy-v2": {**PINS, "NPY_DISABLE_CPU_FEATURES": "X86_V3 X86_V4 AVX512_ICL AVX512_SPR"},
    "pins+blas-generic": {**PINS, "OPENBLAS_CORETYPE": "Prescott"},
    "threads only": {"OPENBLAS_NUM_THREADS": "1"},
}
CLEAR = ("OPENBLAS_CORETYPE", "NPY_DISABLE_CPU_FEATURES", "GLIBC_TUNABLES")


def child():
    """in the probe's process: the jobs stroked, a hash each, as JSON"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import ctypes

    import numpy
    from stroke_bold import emboldened

    jobs = json.loads(DATA.read_text())
    out = {}
    for name, job in jobs.items():
        result = emboldened(ast.literal_eval(job))[1]
        out[name] = hashlib.sha256(repr(result).encode()).hexdigest()[:12]
    lib = next((Path(numpy.__file__).parent.parent / "numpy.libs").glob("libscipy_openblas64_*.so"))
    blas = ctypes.CDLL(str(lib))
    blas.scipy_openblas_get_corename64_.restype = ctypes.c_char_p
    from numpy._core._multiarray_umath import __cpu_features__ as feats

    out["#blas"] = blas.scipy_openblas_get_corename64_().decode()
    out["#numpy"] = " ".join(k for k in ("X86_V3", "X86_V4", "AVX512_ICL") if feats.get(k))
    print(json.dumps(out))


def run(setting):
    env = {k: v for k, v in os.environ.items() if k not in CLEAR and not k.startswith("MYIA_")}
    env.update(SETTINGS[setting])
    done = subprocess.run([sys.executable, "-I", __file__, "--child"], env=env, capture_output=True, text=True,
                          check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


def main():
    if "--child" in sys.argv:
        return child()
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(min(4, int(os.environ.get("MYIA_JOBS", "4")))) as pool:
        results = dict(zip(SETTINGS, pool.map(run, SETTINGS)))
    if "--record" in sys.argv:
        HASHES.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
        print(f"recorded {HASHES.relative_to(ROOT)}")
        return
    stored = json.loads(HASHES.read_text())
    names = sorted(k for k in results["pins"] if not k.startswith("#"))
    for setting, got in results.items():
        want = stored.get(setting, {})
        same = [n for n in names if got[n] == want.get(n)]
        print(f"{setting:18} {len(same):2}/{len(names)} as stored   openblas {got['#blas']:10} numpy {got['#numpy']}")
        for n in names:
            if got[n] != want.get(n):
                print(f"    {n:16} {got[n]} (stored {want.get(n)})")


if __name__ == "__main__":
    main()
