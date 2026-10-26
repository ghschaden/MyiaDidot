"""Publish both upstream reference formats only after FontForge succeeds."""

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
from build_support import content_hash, publish_files, toolchain

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="myia-upstream-") as directory:
        work = Path(directory)
        source = work / args.source.name
        shutil.copyfile(args.source, source)
        if content_hash(source) != content_hash(args.source):
            raise RuntimeError("upstream source changed while taking the build snapshot")
        subprocess.run(["fontforge", "-quiet", "-lang=py", "-script", str(ROOT / "scripts/sfd_reference.py"),
                        str(source), str(work)], check=True)
        outputs = {}
        for ext in ("otf", "ttf"):
            path = work / f"{args.source.stem}.{ext}"
            with TTFont(path, checkChecksums=2) as font:
                font.ensureDecompiled()
            outputs[args.directory / path.name] = path.read_bytes()
        revision = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=False)
        manifest = {"commit": revision.stdout.strip(), "source": str(args.source),
                    "source_sha256": content_hash(source), "toolchain": toolchain(),
                    "outputs": {p.name: hashlib.sha256(data).hexdigest() for p, data in outputs.items()}}
        outputs[args.directory / f"{args.source.stem}.json"] = json.dumps(manifest, indent=2) + "\n"
        publish_files(outputs)


if __name__ == "__main__":
    main()
