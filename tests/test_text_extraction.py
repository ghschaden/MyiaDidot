"""Text set in the fonts comes back out of a PDF as typed.

No glyph has a Private Use code point: the old-style figures (onum), the
capital accents (components of the accented capitals) and the Greek
letters with marks Unicode has no character for (ligatures in ccmp) are
reached by their features alone, so a PDF maps them back to the text they
came from, not to U+F731 and the like (2026-11-03; the code points were
Theano's, from the Adobe convention). Their compiled names read as their
digits too (one.osf: oldstyle_figures.production_name). The extraction
test sets a line of each in LuaLaTeX and reads it back with pdftotext.
"""

import shutil
import subprocess

import pytest

TEXT = [
    (r"1450 AD, 0123456789", "1450 AD, 0123456789"),
    (r"\textsc{Small Capitals 1789}", "Small Capitals 1789"),
    (r"office affluent fjord flat", "office affluent fjord flat"),
    (r"{\addfontfeatures{Numbers={OldStyle,Monospaced}}2026}", "2026"),
]


def test_no_private_use_code_points(ufo):
    pua = sorted(f"{g.name} U+{u:04X}" for g in ufo for u in g.unicodes if 0xE000 <= u <= 0xF8FF)
    assert not pua, f"Private Use code points: {pua}"


def test_oldstyle_production_names(ufo):
    """the compiled figures are named one.osf, one.osf.tf (oldstyle_figures):
    the source's oneoldstyle is the Glyph List's U+F731, and a PDF reader
    naming text by glyph (LuaLaTeX for the tabular ones) gave that"""
    from oldstyle_figures import NAMES_KEY, production_names

    assert ufo.lib.get(NAMES_KEY) == production_names(ufo)
    assert len(production_names(ufo)) == 22


@pytest.mark.skipif(not (shutil.which("lualatex") and shutil.which("pdftotext")),
                    reason="needs lualatex and pdftotext")
def test_pdf_text_extraction(ufo_path, tmp_path):
    from font_builds import compiled_variant

    otf = compiled_variant(ufo_path, "release_otf")
    font = tmp_path / otf.name
    shutil.copyfile(otf, font)
    lines = "\n\n".join(src for src, _ in TEXT)
    (tmp_path / "t.tex").write_text(
        "\\documentclass{article}\n\\usepackage{fontspec}\n"
        f"\\setmainfont{{{font.name}}}[Path=./, Numbers=OldStyle]\n"
        "\\pagestyle{empty}\n\\begin{document}\n" + lines + "\n\\end{document}\n")
    run = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"],
                         cwd=tmp_path, capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stdout[-2000:]
    out = subprocess.run(["pdftotext", "t.pdf", "-"], cwd=tmp_path, capture_output=True,
                         text=True, check=True).stdout
    got = [line.strip() for line in out.splitlines() if line.strip()]
    assert got == [want for _, want in TEXT]
