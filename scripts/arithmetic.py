"""The same arithmetic on any x86 machine: import before numpy loads.

One thread per process (make_bold's pool of JOBS does the stroking; numpy's
OpenBLAS would take every core for fair_arcs' small solves), and AVX2 at
most: fair_arcs' Levenberg-Marquardt solves end a little apart when the
arithmetic differs in its last bits, and GitHub's runners may have AVX-512
(numpy's X86_V4 paths, OpenBLAS's SkylakeX kernels) where the person's
machine has AVX2 (68 Bold Italic glyphs otherwise, 2026-10-28). OpenBLAS
reads OPENBLAS_CORETYPE (checked 2026-11-05: Prescott gives its Katmai
kernels); numpy names its AVX-512 targets X86_V4, AVX512_ICL, AVX512_SPR.

Every generator `make reproduce` runs imports this first: make_italic.py,
make_bold.py, smallcaps.py (numpy through composites and glyph_lint).
Setting a variable already set is left to the caller. Imported after numpy
(a test importing a generator as a library) the pins do nothing, which is
harmless there: only the generators' own runs make what is saved.
"""

import os

PINS = {
    "OPENBLAS_NUM_THREADS": "1",
    "OPENBLAS_CORETYPE": "Haswell",
    "NPY_DISABLE_CPU_FEATURES": "X86_V4 AVX512F AVX512_SKX AVX512_ICL AVX512_SPR",
}

for key, value in PINS.items():
    os.environ.setdefault(key, value)
