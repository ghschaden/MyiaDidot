"""Compile, postprocess and validate a font before publishing its final name."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_support import atomic_output, content_hash, file_lock, publish_files, toolchain

ROOT = Path(__file__).resolve().parent.parent


def sidecar(destination, kind):
    """build/manifests/fonts/otf/X.otf.json, build/locks/...: kept out of the
    output folders, which hold only what is distributed."""
    destination, root = Path(destination).resolve(), ROOT.resolve()
    try:
        relative = destination.relative_to(root)
    except ValueError:
        relative = Path(destination.name)
    folder, suffix = {"manifest": ("manifests", ".json"), "lock": ("locks", ".lock")}[kind]
    return root / "build" / folder / relative.parent / (relative.name + suffix)


def build(kind, source, destination, *, run=subprocess.run):
    def command(*args):
        run(list(map(str, args)), check=True)

    def python(script, *args):
        command(sys.executable, "-I", ROOT / "scripts" / script, *args)

    with atomic_output(destination) as temporary:
        if kind in ("otf", "unhinted", "compare"):
            command(Path(sys.executable).parent / "fontmake", "-u", source,
                    "-o", "ttf" if kind == "unhinted" else "otf",
                    *(["--flatten-components"] if kind == "unhinted" else
                      ["--no-production-names"] if kind == "compare" else []),
                    "--output-path", temporary)
            if kind == "otf":
                python("ps_hints.py", temporary)
                python("add_stat.py", temporary)
        elif kind == "ttf":
            python("hint_control.py", source, temporary, "--control",
                   ROOT / "build/hinting" / f"{Path(destination).stem}.txt")
            python("add_stat.py", temporary)
        else:
            command(sys.executable, "-I", "-m", "fontTools.ttLib.woff2", "compress",
                    "-o", temporary, source)
        with TTFont(temporary, checkChecksums=2) as font:
            font.ensureDecompiled()
            if kind in ("otf", "ttf") and "STAT" not in font:
                raise ValueError("final font has no STAT table")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("otf", "compare", "unhinted", "ttf", "woff2"))
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    # Compiler inputs belong to this invocation. A GUI/editor changing the UFO
    # afterwards cannot change what this artifact or its manifest describes.
    with tempfile.TemporaryDirectory(prefix="myia-font-") as directory:
        work = Path(directory)
        source = work / "input" / args.source.name
        source.parent.mkdir()
        if args.source.is_dir():
            shutil.copytree(args.source, source)
        else:
            shutil.copyfile(args.source, source)
        expected = content_hash(source)
        if expected != content_hash(args.source):
            raise RuntimeError("source changed while taking the build snapshot; retry")
        output = work / args.destination.name
        build(args.kind, source, output)
        revision = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=False)
        manifest = {"commit": revision.stdout.strip(), "format": args.kind,
                    "source": str(args.source), "source_sha256": expected,
                    "scripts_sha256": content_hash(ROOT / "scripts"),
                    "lock_sha256": content_hash(ROOT / "uv.lock"), "toolchain": toolchain(),
                    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        with file_lock(sidecar(args.destination, "lock")):
            publish_files({args.destination: output.read_bytes(),
                           sidecar(args.destination, "manifest"): json.dumps(manifest, indent=2) + "\n"})


if __name__ == "__main__":
    main()
