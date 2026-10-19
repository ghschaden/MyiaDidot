"""Render fixed specimens in two builds of the fonts and show what changed.

    python scripts/visual_diff.py BEFORE_DIR AFTER_DIR --out build/visual/report
        [--styles Regular Bold] [--label-before REF]

BEFORE_DIR and AFTER_DIR hold MyiaDidot-STYLE.otf. Every specimen (the
golden shaping corpus, proof_svg's feature samples and some running text)
is shaped with HarfBuzz and rasterized with Skia in both builds, on the
same canvas; a specimen whose pixels differ gets an image of the before,
the after and their overlay (before red, after blue, both black). The
report (index.html) lists the changed specimens per style, most changed
first. Differences are evidence to look at, not failures: the exit status
is 0 either way.
"""

import argparse
import html
import sys
from pathlib import Path

import numpy as np
import skia
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))
from proof_svg import SAMPLES
from shaping import golden_cases

STYLES = ["Regular", "Italic", "Bold", "BoldItalic"]
PX_PER_EM = 40
TOP, BOTTOM = 2300, -760  # font units: stacked accents above, descenders below
MARGIN = 12  # pixels
INK = 48  # a pixel differs when its grey changes by more than this

# Running text for texture, (text, features, language)
TEXT = [
    ("It is a truth universally acknowledged, that a single man in possession of a good fortune",
     {"onum": True}, "en"),
    ("Office affluent: fifty difficult offers, the official ﬁnal draft", {}, "en"),
    ("Le cœur a ses raisons que la raison ne connaît point ; « déjà » vu.", {}, "fr"),
    ("Größere Übungen für Schüler, die Straße hinauf zum Fluß.", {}, "de"),
    ("Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.", {}, "grc"),
    ("Все люди рождаются свободными и равными в своём достоинстве и правах.", {}, "ru"),
    ("Người người được sinh ra tự do và bình đẳng về nhân phẩm và quyền.", {}, "vi"),
    ("ROYAL ACADEMY · Royal Academy · royal academy", {"c2sc": True}, "en"),
]


def specimens():
    """(label, text, features, script, language), in a fixed order."""
    out = [(label, text, feats, script, lang) for label, text, feats, script, lang in SAMPLES]
    out += [("Running text", text, feats, None, lang) for text, feats, lang in TEXT]
    out += [("Shaping corpus", text, feats, None, lang) for text, feats, lang in golden_cases()]
    return out


class SkiaPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.path = skia.Path()

    def _moveTo(self, pt):
        self.path.moveTo(*pt)

    def _lineTo(self, pt):
        self.path.lineTo(*pt)

    def _curveToOne(self, p1, p2, p3):
        self.path.cubicTo(*p1, *p2, *p3)

    def _qCurveToOne(self, p1, p2):
        self.path.quadTo(*p1, *p2)

    def _closePath(self):
        self.path.close()


class Font:
    def __init__(self, path):
        self.ttfont = TTFont(path)
        self.glyphset = self.ttfont.getGlyphSet()
        self.order = self.ttfont.getGlyphOrder()
        self.upem = self.ttfont["head"].unitsPerEm
        self.hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def shape(self, text, features, script, language):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        if script:
            buf.script = script
        buf.language = language or "en"  # not the shell's locale
        hb.shape(self.hbfont, buf, features or {})
        run, x = [], 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            run.append((self.order[info.codepoint], x + pos.x_offset, pos.y_offset))
            x += pos.x_advance
        return run, x

    def paths(self, run):
        scale = PX_PER_EM / self.upem
        out = []
        for name, x, y in run:
            pen = SkiaPen(self.glyphset)
            self.glyphset[name].draw(TransformPen(pen, (scale, 0, 0, -scale,
                                                        MARGIN + x * scale, MARGIN + (TOP - y) * scale)))
            out.append(pen.path)
        return out


def raster(paths, width, height):
    surface = skia.Surface(width, height)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorWHITE)
    paint = skia.Paint(AntiAlias=True, Color=skia.ColorBLACK)
    for path in paths:
        canvas.drawPath(path, paint)
    return surface.makeImageSnapshot().toarray()[:, :, 0].astype(np.int16)  # grey: 255 paper, 0 ink


def grey(g):
    return np.repeat(g[:, :, None], 3, axis=-1)


def overlay(before, after):
    """Before, after and overlay stacked: before red, after blue, both black."""
    b, a = 255 - before, 255 - after  # ink
    over = np.stack([255 - a, 255 - np.maximum(a, b), 255 - b], axis=-1)
    gap = np.full((6, before.shape[1], 3), 230, dtype=np.int16)
    return np.concatenate([grey(before), gap, grey(after), gap, over]).clip(0, 255).astype(np.uint8)


def save_png(rgb, path):
    h, w, _ = rgb.shape
    rgba = np.concatenate([rgb, np.full((h, w, 1), 255, dtype=np.uint8)], axis=-1)
    skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType).save(
        str(path), skia.kPNG)


def compare(before, after, out, style):
    changed = []
    total = 0
    for i, (label, text, feats, script, lang) in enumerate(specimens()):
        total += 1
        run_b, adv_b = before.shape(text, feats, script, lang)
        run_a, adv_a = after.shape(text, feats, script, lang)
        if run_b == run_a and same_outlines(before, after, run_b):
            continue
        scale = PX_PER_EM / before.upem
        width = int(max(adv_b, adv_a) * scale) + 2 * MARGIN + PX_PER_EM
        height = int((TOP - BOTTOM) * scale) + 2 * MARGIN
        img_b = raster(before.paths(run_b), width, height)
        img_a = raster(after.paths(run_a), width, height)
        diff = int((np.abs(img_b - img_a) > INK).sum())
        if not diff:
            continue
        name = f"{style}-{i:03d}.png"
        save_png(overlay(img_b, img_a), out / name)
        changed.append((diff, label, text, feats, lang, name, adv_a - adv_b))
    changed.sort(key=lambda c: -c[0])
    return changed, total


def same_outlines(before, after, run):
    """The same glyphs at the same places: are their outlines the same too?"""
    for name in {g[0] for g in run}:
        pb, pa = SkiaPen(before.glyphset), SkiaPen(after.glyphset)
        before.glyphset[name].draw(pb)
        after.glyphset[name].draw(pa)
        if pb.path != pa.path:
            return False
    return True


def report(results, out, label_before):
    rows = []
    for style, (changed, total) in results.items():
        rows.append(f"<h2>{style}: {len(changed)} of {total} specimens changed</h2>")
        for diff, label, text, feats, lang, name, dadv in changed:
            f = ", ".join(("" if v else "-") + k for k, v in sorted(feats.items()))
            meta = " · ".join(x for x in (label, f, lang or "", f"{diff} px",
                                          f"width {dadv:+d} units" if dadv else "") if x)
            rows.append(f'<figure><figcaption>{html.escape(text)}<br><small>{html.escape(meta)}</small>'
                        f'</figcaption><img src="{name}" alt=""></figure>')
    (out / "index.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Myia Didot visual diff</title>
<style>body{{font:14px sans-serif;margin:24px;background:#fff;color:#222}}
figure{{margin:0 0 28px}}img{{display:block;max-width:100%;border:1px solid #ddd}}
small{{color:#777}}</style>
<h1>Myia Didot: {html.escape(label_before)} → working tree</h1>
<p>Each image: before, after, overlay (before red, after blue, both black). Most changed first.</p>
{chr(10).join(rows)}
""", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "visual" / "report")
    ap.add_argument("--styles", nargs="+", default=STYLES)
    ap.add_argument("--label-before", default=None)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.png"):
        old.unlink()
    results = {}
    for style in args.styles:
        fb, fa = (d / f"MyiaDidot-{style}.otf" for d in (args.before, args.after))
        if not (fb.exists() and fa.exists()):
            print(f"{style}: missing {fb if not fb.exists() else fa}, skipped")
            continue
        changed, total = compare(Font(fb), Font(fa), args.out, style)
        results[style] = (changed, total)
        print(f"{style}: {len(changed)} of {total} specimens changed")
        for diff, label, text, *_ in changed[:5]:
            print(f"  {diff:6d} px  {text[:60]}  ({label})")
    report(results, args.out, args.label_before or str(args.before))
    print(f"report: {args.out / 'index.html'}")


if __name__ == "__main__":
    main()
