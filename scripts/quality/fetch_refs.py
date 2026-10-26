"""Fetch the pinned reference fonts used by quality reports.

    python scripts/quality/fetch_refs.py

Downloads Didots and EB Garamond (all OFL) from the Google Fonts
repository into build/refs/, verifies their SHA-256 pins, and makes static
instances of the variable ones (Bodoni Moda at its 11 pt optical size;
regular 400, bold 700).
"""

import hashlib
import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import REFDIR

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from build_support import atomic_output, json_digest
from reference_inputs import PINS, fetch, fetch_system_references

BASE = f"https://raw.githubusercontent.com/google/fonts/{PINS['google_fonts_commit']}/ofl/"
# SHA-256 pins for the raw comparison fonts below. The paths remain readable
# and the hashes make a changed upstream file fail clearly instead of silently
# changing the quality measurements.
RAW_SHA256 = {
    "bodonimoda/BodoniModa[opsz,wght].ttf": "550f5e34ee0a828d7941b1fe9bc58b34e5260d3f33a61532e6d0a0114e79a5cf",
    "bodonimoda/BodoniModa-Italic[opsz,wght].ttf": "dfff1619f8f6871c6372f8855b67211f9a73b4e93d45aca868cd8f46a48622de",
    "librebodoni/LibreBodoni[wght].ttf": "0d543665bd869819ffd7d46608804e245497ba835960832d44be89e561b0c717",
    "librebodoni/LibreBodoni-Italic[wght].ttf": "6a9b0c88764dcf6c094653e3c28da045fcebca48734254afdcbfec46b9ab4fcd",
    "ebgaramond/EBGaramond[wght].ttf": "ef9512f92f6d579e5dc75af59a5a4b1b8b47d2eda89e00b954d44520e5369027",
    "ebgaramond/EBGaramond-Italic[wght].ttf": "bba2c4499c93c9612b90b9825d32b07da52fce2fe57562a1eb6b833553f93c4e",
    "oldstandardtt/OldStandard-Regular.ttf": "42717a1280b523a506ca2b0285cca380e77fe214b1f6e3d75a8b925005f19eac",
    "oldstandardtt/OldStandard-Bold.ttf": "7d831e9d799ad23ee98e889381a9db2a283b2dac7f228dd5c06071decb9c54db",
    "oldstandardtt/OldStandard-Italic.ttf": "4b9522f4711317fc06e2413a58b4662c249cb707df193d682b9d640e365ef564",
    "gfsdidot/GFSDidot-Regular.ttf": "4fc784ab824e8866eeef8ad55976b93e7e170fb1b8237fd4f8781b5b4dd297f9",
}
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
        manifest = out.with_suffix(".json")
        import fontTools

        recipe = {"raw_sha256": RAW_SHA256[src], "axes": axes, "fonttools": fontTools.__version__}
        if out.exists() and manifest.exists():
            recorded = json.loads(manifest.read_text())
            if recorded.get("recipe") == recipe and recorded.get("output_sha256") == hashlib.sha256(out.read_bytes()).hexdigest():
                continue
        raw = cache / src.replace("/", "_").replace("[", "_").replace("]", "_").replace(",", "_")
        url = BASE + src.replace("[", "%5B").replace("]", "%5D").replace(",", "%2C")
        fetch(url, raw, RAW_SHA256[src])
        font = TTFont(raw)
        if axes:
            font = instantiateVariableFont(font, axes)
        # FontTools defaults to wall-clock timestamps when saving instances.
        font.recalcTimestamp = False
        with atomic_output(out) as temporary:
            font.save(temporary)
        with atomic_output(manifest) as temporary:
            temporary.write_text(json.dumps({"recipe": recipe, "recipe_sha256": json_digest(recipe),
                                             "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest()},
                                            indent=2) + "\n")
        print("made", out.name)
    fetch_system_references(REFDIR)


if __name__ == "__main__":
    main()
