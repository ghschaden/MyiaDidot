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
  Beside each raw draft, in the layer `fitted`, the same draft redrawn
  onto clean nodes (redraw.py, no spec) when it passed redraw's gate:
  fitted once, when it is drafted, and handed over in place of the raw
  one. FontForge's kinks stay out of the small caps so, before
  weight_thick and the finishing passes read their nodes (longtail.md,
  family 3; approved by the designer 2026-11-23). A draft that fails the
  gate is handed over raw; FIT_KEY records which, and why.
"""

import hashlib
import shutil
import subprocess
import sys
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
FIT_KEY = "org.myiadidot.draftFit"  # {name: "fitted" or "raw: why"}
FITTED_LAYER = "fitted"
# drafts handed over raw though the fit passes its gate, by decision
KEEP_RAW = {
    "psi.sc": "the Bold Italic's stroke closes the fitted arm onto the stem's top serif "
              "(a counter made a hole, the arm lost; 2026-11-23)",
}
# a run that may only read the drafts store: a draft it lacks ends the run
# instead of FontForge writing it (scratch_out.prepare no longer sets it: a
# scratch run drafts into its own copy, redirect_drafts)
READ_ONLY = False


def redirect_drafts(path):
    """this process's drafts store: a fresh copy of the committed one at path
    (a scratch run with --out drafts into it; sources/drafts stays as it is)"""
    global DRAFTS_UFO
    path = Path(path).resolve()
    if path.exists():
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if (DRAFTS_UFO / "metainfo.plist").exists():
        shutil.copytree(DRAFTS_UFO, path)
    DRAFTS_UFO = path
    return path


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


def fit_draft(glyph):
    """(the draft redrawn onto clean nodes, "fitted"), or (None, "raw: why")
    where redraw refuses it or its gate fails"""
    import redraw

    try:
        new, report = redraw.redraw(glyph)
    except Exception as e:  # refused by the tool
        return None, f"raw: {e}"
    fail, _look = redraw.gate(report)
    if fail:
        return None, "raw: " + "; ".join(fail)
    new.lib.clear()
    return new, "fitted"


def fit_store(store, names):
    """names' raw drafts in store fitted into its fitted layer, FIT_KEY set"""
    layer = (store.layers[FITTED_LAYER] if FITTED_LAYER in store.layers
             else store.layers.newLayer(FITTED_LAYER))
    status = dict(store.lib.get(FIT_KEY, {}))
    for name in names:
        if name in layer:
            del layer[name]
        status.pop(name, None)
        if name not in store:
            continue
        if name in KEEP_RAW:
            status[name] = "raw: " + KEEP_RAW[name]
            sys.stderr.write(f"small-cap draft {name}: {status[name]}\n")
            continue
        new, why = fit_draft(store[name])
        if new is not None:
            layer.insertGlyph(new, name)
        status[name] = why
        sys.stderr.write(f"small-cap draft {name}: {why}\n")
    store.lib[FIT_KEY] = {n: status[n] for n in sorted(status) if n in store}


def drafts(up, height, stem, redraft=False, keep=False):
    """{small cap name: draft} for up (the Italic in the upright frame):
    the stored drafts whose input is unchanged, the others drafted anew by
    FontForge and stored; other small caps up has, as they are (FontForge
    passes them through as well).
    keep: the stored drafts stay though their capitals changed, and are
    recorded as made from the capitals as they are now. For the run after
    capitals were redrawn onto new nodes (redraw.py: the shape kept within
    its gate): FontForge's small caps follow a capital's nodes, not its
    shape, and came 28 units wider (e.sc) or 46 units off in a bowl (d.sc)
    from capitals that had moved by 1-2 (the Italic's A-Z, 2026-11-11).
    Never for a capital given another shape."""
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
    changed = [name for name in wanted if redraft or stored.get(name) != keys[name]]
    # kept: only what has a stored input (a draft, or FontForge made none of it)
    held = [name for name in changed if keep and not redraft and name in stored]
    stale = [name for name in changed if name not in held]
    if held:
        sys.stderr.write(f"{len(held)} small-cap drafts kept though their capitals changed (--keep-drafts): "
                         + " ".join(sorted(held)) + "\n")
    if stale and READ_ONLY:
        names = " ".join(stale[:12]) + (" ..." if len(stale) > 12 else "")
        raise SystemExit(f"{len(stale)} small-cap drafts to make again ({names}): a scratch run (--out) "
                         f"does not write {DRAFTS_UFO.relative_to(ROOT)}; run make generate")
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
        if FITTED_LAYER in store.layers:
            layer = store.layers[FITTED_LAYER]
            for name in [n for n in layer.keys() if n not in store]:
                del layer[name]
        fit_store(store, stale)
        store.lib[INPUT_KEY] = {name: keys[name] for name in sorted(wanted)}
        store.lib[CONVERTED_KEY] = {"fontforge": fontforge_version()}
        store.glyphOrder = sorted(store.keys())
        DRAFTS_UFO.parent.mkdir(parents=True, exist_ok=True)
        store.save(DRAFTS_UFO, overwrite=True)
    elif held and not READ_ONLY:
        store.lib[INPUT_KEY] = {name: keys[name] for name in sorted(wanted)}
        store.save(DRAFTS_UFO, overwrite=True)
    unfitted = [name for name in wanted if name in store and name not in store.lib.get(FIT_KEY, {})]
    if unfitted and not READ_ONLY:
        fit_store(store, unfitted)
        store.save(DRAFTS_UFO, overwrite=True)
    fitted = store.layers[FITTED_LAYER] if FITTED_LAYER in store.layers else {}
    out = {g.name: g for g in up if g.name.endswith(".sc")}
    out.update({name: fitted[name] if name in fitted else store[name] for name in wanted if name in store})
    return out
