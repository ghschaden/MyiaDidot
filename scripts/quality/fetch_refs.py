"""Fetch the reference fonts the quality scripts compare with, once.

    python scripts/quality/fetch_refs.py

Downloads Didots and EB Garamond (all OFL) from the Google Fonts
repository into build/refs/, and makes static instances of the variable
ones (Bodoni Moda at its 11 pt optical size; regular 400, bold 700).
Libertinus and Charis are taken from the system when installed.
"""

import sys
import urllib.request

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import REFDIR

BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
# saved as: (source path in google/fonts, axis locations or None for a static font)
FONTS = {
    "BodoniModa-11-Regular": ("bodonimoda/BodoniModa[opsz,wght].ttf", {"opsz": 11, "wght": 400}),
    "BodoniModa-11-Bold": ("bodonimoda/BodoniModa[opsz,wght].ttf", {"opsz": 11, "wght": 700}),
    "BodoniModa-11-Italic": ("bodonimoda/BodoniModa-Italic[opsz,wght].ttf", {"opsz": 11, "wght": 400}),
    "LibreBodoni-Regular": ("librebodoni/LibreBodoni[wght].ttf", {"wght": 400}),
    "LibreBodoni-Bold": ("librebodoni/LibreBodoni[wght].ttf", {"wght": 700}),
    "LibreBodoni-Italic": ("librebodoni/LibreBodoni-Italic[wght].ttf", {"wght": 400}),
    "EBGaramond-Regular": ("ebgaramond/EBGaramond[wght].ttf", {"wght": 400}),
    "EBGaramond-Bold": ("ebgaramond/EBGaramond[wght].ttf", {"wght": 700}),
    "EBGaramond-Italic": ("ebgaramond/EBGaramond-Italic[wght].ttf", {"wght": 400}),
    "BodoniModa-11-BoldItalic": ("bodonimoda/BodoniModa-Italic[opsz,wght].ttf", {"opsz": 11, "wght": 700}),
    "LibreBodoni-BoldItalic": ("librebodoni/LibreBodoni-Italic[wght].ttf", {"wght": 700}),
    "EBGaramond-BoldItalic": ("ebgaramond/EBGaramond-Italic[wght].ttf", {"wght": 700}),
    "OldStandard-Regular": ("oldstandardtt/OldStandard-Regular.ttf", None),
    "OldStandard-Bold": ("oldstandardtt/OldStandard-Bold.ttf", None),
    "OldStandard-Italic": ("oldstandardtt/OldStandard-Italic.ttf", None),
    "GFSDidot-Regular": ("gfsdidot/GFSDidot-Regular.ttf", None),
}


def main():
    REFDIR.mkdir(parents=True, exist_ok=True)
    cache = REFDIR / "downloads"
    cache.mkdir(exist_ok=True)
    for name, (src, axes) in FONTS.items():
        out = REFDIR / f"{name}.ttf"
        if out.exists():
            continue
        raw = cache / src.replace("/", "_").replace("[", "_").replace("]", "_").replace(",", "_")
        if not raw.exists():
            url = BASE + src.replace("[", "%5B").replace("]", "%5D").replace(",", "%2C")
            print("fetching", url)
            urllib.request.urlretrieve(url, raw)
        font = TTFont(raw)
        if axes:
            font = instantiateVariableFont(font, axes)
        font.save(out)
        print("made", out.name)


if __name__ == "__main__":
    main()
