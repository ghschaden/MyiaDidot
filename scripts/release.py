"""release.py [OUT_DIR]: the release archive, prepared, not published.

    make release   (builds the fonts first)

Writes OUT_DIR/MyiaDidot-VERSION.zip (default build/release), its one
folder holding the fonts by format (otf, ttf, webfonts), OFL.txt,
FONTLOG.txt, INSTALL.txt, the specimen (build/proofs/samples.pdf, from
`make proof`, when built) and SHA256SUMS over all of them. VERSION is the
fonts' own (fontinfo versionMajor.versionMinor, 0.100), and every style's
UFO and built font must state the same, or nothing is written. The archive
is reproducible: entries sorted, timestamps fixed (SOURCE_DATE_EPOCH, or
the newest source's).
"""

import hashlib
import os
import sys
import time
import zipfile
from pathlib import Path

import ufoLib2
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "MyiaDidot"
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")
FORMATS = (("otf", "otf"), ("ttf", "ttf"), ("webfonts", "woff2"))
SPECIMEN = ROOT / "build/proofs/samples.pdf"
INSTALL = """Myia Didot {version}

Install the fonts for your system from one folder:

  otf/       OpenType (CFF) fonts: desktop use, most applications
  ttf/       TrueType fonts, hinted for screens: Windows, older software
  webfonts/  WOFF2, for websites (@font-face)

Install one format only; two formats of the same family side by side can
confuse applications.

  Windows  select the files, right-click, Install (or Install for all users)
  macOS    double-click a file and choose Install Font (Font Book)
  Linux    copy the files to ~/.local/share/fonts and run fc-cache -f

Myia Didot is licensed under the SIL Open Font License 1.1 (OFL.txt).
FONTLOG.txt records its sources, credits and changes. SHA256SUMS lists
the checksum of every file in this archive.
"""


def ufo_version(style):
    info = ufoLib2.Font.open(ROOT / f"sources/{FAMILY}-{style}.ufo").info
    return f"{info.versionMajor}.{info.versionMinor:03d}"


def font_version(path):
    """The version the built font states: its head revision, as in name ID 5."""
    return f"{TTFont(path, lazy=True)['head'].fontRevision:.3f}"


def check(fonts):
    """The one version all styles and their built fonts state, or SystemExit
    naming what is missing or disagrees."""
    missing = [str(p.relative_to(ROOT)) for p in fonts if not p.exists()]
    if missing:
        sys.exit("release: not built (make fonts): " + ", ".join(missing))
    versions = {f"sources/{FAMILY}-{s}.ufo": ufo_version(s) for s in STYLES}
    versions.update({str(p.relative_to(ROOT)): font_version(p) for p in fonts})
    if len(set(versions.values())) != 1:
        sys.exit("release: versions disagree: " + ", ".join(f"{k} {v}" for k, v in sorted(versions.items())))
    return next(iter(versions.values()))


def members(version, fonts):
    """{archive path: bytes}, the checksums last."""
    top = f"{FAMILY}-{version}"
    out = {f"{top}/{p.parent.name}/{p.name}": p.read_bytes() for p in fonts}
    for name in ("OFL.txt", "FONTLOG.txt"):
        out[f"{top}/{name}"] = (ROOT / name).read_bytes()
    out[f"{top}/INSTALL.txt"] = INSTALL.format(version=version).encode()
    if SPECIMEN.exists():
        out[f"{top}/specimen.pdf"] = SPECIMEN.read_bytes()
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {path.split('/', 1)[1]}\n"
                   for path, data in sorted(out.items()))
    out[f"{top}/SHA256SUMS"] = sums.encode()
    return out


def write(path, files, epoch):
    stamp = time.gmtime(max(epoch, 315532800))[:6]  # zip dates start in 1980
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build/release"
    fonts = [ROOT / f"fonts/{folder}/{FAMILY}-{s}.{ext}" for folder, ext in FORMATS for s in STYLES]
    version = check(fonts)
    files = members(version, fonts)
    sources = fonts + [ROOT / "OFL.txt", ROOT / "FONTLOG.txt"]
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", max(p.stat().st_mtime for p in sources)))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{FAMILY}-{version}.zip"
    write(path, files, epoch)
    print(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {len(files)} files"
          + ("" if SPECIMEN.exists() else " (no specimen: make proof first to include it)"))


if __name__ == "__main__":
    main()
