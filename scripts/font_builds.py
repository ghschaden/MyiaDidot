"""Lazy compiler variants shared by baseline tools and tests."""

import shutil
import tempfile
from functools import cached_property
from pathlib import Path

import ufo2ft
import ufoLib2
from build_support import atomic_output, content_hash, file_lock, json_digest, toolchain
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OPTIONS = {
    "test_otf": ("otf", {"useProductionNames": False, "optimizeCFF": 0}),
    "release_otf": ("otf", {}),
    "cff_otf": ("otf", {"removeOverlaps": True}),
    "hint_ttf": ("ttf", {"flattenComponents": True, "removeOverlaps": True}),
}


def compiled_variant(source, variant):
    """Share only identical compilation settings and source/toolchain bytes."""
    source = Path(source)
    kind, options = OPTIONS[variant]
    digest = content_hash(source)
    key = json_digest({"source": digest, "variant": variant, "options": options,
                       "toolchain": toolchain(), "compiler_helper": content_hash(Path(__file__))})
    path = ROOT / "build/cache/compiled" / f"{key}.{kind}"
    with file_lock(path.with_suffix(path.suffix + ".lock")):
        if path.exists():
            try:
                with TTFont(path, checkChecksums=2) as font:
                    font.ensureDecompiled()
                return path
            except Exception:
                pass  # a truncated cache entry is rebuilt below
        with tempfile.TemporaryDirectory(prefix="myia-compile-") as directory:
            copy = Path(directory) / source.name
            shutil.copytree(source, copy)
            if content_hash(copy) != digest:
                raise RuntimeError("source changed during compilation snapshot; retry")
            font = ufoLib2.Font.open(copy)
            with atomic_output(path) as temporary:
                compiler = ufo2ft.compileOTF if kind == "otf" else ufo2ft.compileTTF
                compiler(font, **options).save(temporary)
                with TTFont(temporary, checkChecksums=2) as built:
                    built.ensureDecompiled()
    return path


class Builds:
    """Only compile the variants selected update flags actually consume."""

    def __init__(self, source, directory):
        self.source, self.directory = source, directory

    @cached_property
    def font(self):
        return ufoLib2.Font.open(self.source)

    @cached_property
    def otf(self):
        return compiled_variant(self.source, "test_otf")

    @cached_property
    def release(self):
        return compiled_variant(self.source, "release_otf")

    @cached_property
    def decomposed(self):
        import unicodedata

        path = self.directory / "decomposed.otf"
        with TTFont(self.otf) as font:
            for table in font["cmap"].tables:
                for cp in list(table.cmap):
                    if len(unicodedata.normalize("NFD", chr(cp))) > 1:
                        del table.cmap[cp]
            font.save(path)
        return path

