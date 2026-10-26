"""What the Italic generator takes from FontForge, kept in the repository.

FontForge converts Old Standard's SFD and drafts the Italic's small caps
(addSmallCaps). Its output changes between versions (Ubuntu's 20230101
drafts l.sc without ink at mid-height, the 20251009 used here does not), so
the generator reads both from sources/ and needs FontForge only when an
input changed:

- sources/oldstand/OldStandard-Italic.ufo: the converted SFD, with the SFD's
  SHA-256 it was made from (`make oldstand` converts it again);
- sources/drafts/Italic-smallcaps.ufo: each small cap's raw draft, with a
  hash of what it was drafted from (its capital's outline in the upright
  frame, the small caps' height and stems, smallcaps_draft.py). A stale or
  missing one is drafted again where FontForge is installed; elsewhere (CI)
  the generator stops and names it. make_italic.py --redraft drafts all.
"""

import hashlib
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import ufoLib2

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SFD = ROOT / "sources/oldstand/OldStandard-Italic.sfd"
SOURCE_UFO = ROOT / "sources/oldstand/OldStandard-Italic.ufo"
DRAFTS_UFO = ROOT / "sources/drafts/Italic-smallcaps.ufo"
DRAFT_SCRIPT = ROOT / "scripts/smallcaps_draft.py"
CONVERTED_KEY = "org.myiadidot.convertedFrom"
INPUT_KEY = "org.myiadidot.draftInputs"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fontforge_version():
    if not shutil.which("fontforge"):
        return None
    out = subprocess.run(["fontforge", "-version"], capture_output=True, text=True, check=False)
    lines = [line.strip() for line in (out.stdout + out.stderr).splitlines() if "Version" in line]
    return lines[0] if lines else "unknown"


def convert_source():
    """Old Standard's SFD converted into SOURCE_UFO (make oldstand)."""
    with tempfile.TemporaryDirectory(prefix="myia-oldstand-") as temporary:
        out = Path(temporary) / "OldStandard-Italic.ufo"
        subprocess.run(["fontforge", "-quiet", "-lang=py", "-c",
                        f"import fontforge; fontforge.open({str(SOURCE_SFD)!r}).generate({str(out)!r})"],
                       check=True)
        font = ufoLib2.Font.open(out, lazy=False)
    font.lib[CONVERTED_KEY] = {"sfd": SOURCE_SFD.name, "sha256": sha256(SOURCE_SFD),
                               "fontforge": fontforge_version()}
    font.save(SOURCE_UFO, overwrite=True)


def source_font():
    """Old Standard Italic as converted, refused if the SFD changed since."""
    font = ufoLib2.Font.open(SOURCE_UFO, lazy=False)
    made = font.lib.pop(CONVERTED_KEY, {})
    if made.get("sha256") != sha256(SOURCE_SFD):
        raise SystemExit(f"{SOURCE_UFO.relative_to(ROOT)} is not converted from the current "
                         f"{SOURCE_SFD.name}: run make oldstand")
    return font


def capitals(up):
    """the capitals smallcaps_draft.py drafts by default: encoded uppercase
    letters drawn without components"""
    return [g.name for g in up if g.unicode is not None and unicodedata.category(chr(g.unicode)) == "Lu"
            and not g.components and g.contours]


def input_key(glyphs, params):
    """what a small cap is drafted from: its capitals (Θ and ϴ both make
    theta.sc, the later one kept), the height and stems, the script"""
    h = hashlib.sha256()
    h.update(repr(params).encode())
    h.update(sha256(DRAFT_SCRIPT).encode())
    for glyph in glyphs:
        h.update(f"{glyph.name} {glyph.width!r}".encode())
        for c in glyph.contours:
            h.update(repr([(round(p.x, 6), round(p.y, 6), p.type, p.smooth) for p in c.points]).encode())
    return h.hexdigest()


def drafts(up, height, stem, redraft=False):
    """{small cap name: draft} for up (the Italic in the upright frame):
    the stored drafts whose input is unchanged, the others drafted anew by
    FontForge and stored; other small caps up has, as they are (FontForge
    passes them through as well)."""
    import smallcaps as sc

    b = sc.Builder(up)
    params = (round(height, 6), stem)
    store = ufoLib2.Font.open(DRAFTS_UFO, lazy=False) if (DRAFTS_UFO / "metainfo.plist").exists() else ufoLib2.Font()
    wanted = {}
    for cap in capitals(up):
        wanted.setdefault(sc.sc_name(b, cap), []).append(cap)
    keys = {name: input_key([up[c] for c in caps], params) for name, caps in wanted.items()}
    # each name's input, also where FontForge made no draft of it
    stored = store.lib.get(INPUT_KEY, {})
    stale = [name for name in wanted if redraft or stored.get(name) != keys[name]]
    if stale:
        if not shutil.which("fontforge"):
            names = " ".join(stale[:12]) + (" ..." if len(stale) > 12 else "")
            raise SystemExit(f"{len(stale)} small-cap drafts to make again ({names}) and no FontForge: "
                             "run make_italic.py where it is installed and commit "
                             f"{DRAFTS_UFO.relative_to(ROOT)}")
        with tempfile.TemporaryDirectory(prefix="myia-italic-") as temporary:
            work = Path(temporary)
            up.save(work / "upright.ufo", overwrite=True)
            subprocess.run(["fontforge", "-quiet", "-lang=py", "-script", str(DRAFT_SCRIPT),
                            str(work / "upright.ufo"), str(work / "smallcaps.ufo"), str(height), stem,
                            *[cap for name in stale for cap in wanted[name]]],
                           check=True)
            made = ufoLib2.Font.open(work / "smallcaps.ufo", lazy=False)
        for name in stale:
            if name in store:
                del store[name]
            if name in made:
                g = made[name]
                g.lib.clear()
                store.layers.defaultLayer.insertGlyph(g, name)
        for name in [n for n in store.keys() if n not in wanted]:
            del store[name]
        store.lib[INPUT_KEY] = {name: keys[name] for name in sorted(wanted)}
        store.lib[CONVERTED_KEY] = {"fontforge": fontforge_version()}
        store.glyphOrder = sorted(store.keys())
        DRAFTS_UFO.parent.mkdir(parents=True, exist_ok=True)
        store.save(DRAFTS_UFO, overwrite=True)
    out = {g.name: g for g in up if g.name.endswith(".sc")}
    out.update({name: store[name] for name in wanted if name in store})
    return out
