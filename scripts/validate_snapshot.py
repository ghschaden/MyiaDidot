"""Run validation against an immutable Git tree, with private build outputs."""

import argparse
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_support import atomic_output, content_hash, file_lock, publish_files, toolchain

ROOT = Path(__file__).resolve().parent.parent


def git(*args, cwd=None):
    return subprocess.check_output(["git", "-C", str(cwd or ROOT), *args]).decode().strip()


def run_snapshot(tree, command, *, head=None, publish_proofs=False):
    tree = git("rev-parse", tree)
    head = head or git("rev-parse", "HEAD")
    with tempfile.TemporaryDirectory(prefix="myia-validation-") as directory:
        snapshot = Path(directory)
        archive = subprocess.check_output(["git", "-C", str(ROOT), "archive", tree])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(snapshot, filter="data")
        # A private index/HEAD supports tests that compare with committed sources.
        # Object access is read-only; refs and build output belong to this run.
        git("init", "-q", cwd=snapshot)
        objects = Path(git("rev-parse", "--path-format=absolute", "--git-path", "objects")).resolve()
        (snapshot / ".git/objects/info/alternates").write_text(str(objects) + "\n")
        git("update-ref", "HEAD", head, cwd=snapshot)
        git("read-tree", tree, cwd=snapshot)
        (snapshot / ".venv").symlink_to(ROOT / ".venv", target_is_directory=True)
        inputs = {}
        for name in ("refs", "udhr"):
            source = ROOT / "build" / name
            if source.exists():
                target = snapshot / "build" / name
                shutil.copytree(source, target)
                inputs[name] = content_hash(target)
        manifest = {"commit": head, "source_tree": tree, "toolchain": toolchain(), "inputs": inputs}
        build = snapshot / "build"
        build.mkdir(exist_ok=True)
        (build / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        result = subprocess.run(command, cwd=snapshot, check=False)
        if result.returncode:
            return result.returncode
        if publish_proofs:
            # The proof hook holds its publication lock throughout this call.
            proofs = build / "proofs"
            outputs = {ROOT / "build/proofs" / p.relative_to(proofs): p.read_bytes()
                       for p in proofs.rglob("*") if p.is_file()}
            outputs[ROOT / "build/proofs/manifest.json"] = json.dumps(manifest, indent=2) + "\n"
            outputs[ROOT / "build/proofs/built-from"] = head + "\n"
            with file_lock(ROOT / "build/proofs.lock"):
                publish_files(outputs)
        else:
            with atomic_output(ROOT / "build/validation" / f"{tree}.json") as temporary:
                temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--head")
    parser.add_argument("--publish-proofs", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a validation command is required")
    raise SystemExit(run_snapshot(args.tree, command, head=args.head, publish_proofs=args.publish_proofs))


if __name__ == "__main__":
    main()
