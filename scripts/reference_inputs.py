"""Pinned reference bytes, independent of installed fonts and mutable branches."""

import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_support import atomic_output

ROOT = Path(__file__).resolve().parent.parent
PINS = json.loads((ROOT / "scripts/data/reference-inputs.json").read_text())


def verify(data, expected, name):
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError(f"{name}: SHA-256 {actual}, expected {expected}; review input pin")
    return data


def fetch(url, path, expected):
    path = Path(path)
    if path.exists():
        verify(path.read_bytes(), expected, path)
        return path
    with urllib.request.urlopen(url, timeout=60) as response:
        data = verify(response.read(), expected, url)
    with atomic_output(path) as temporary:
        temporary.write_bytes(data)
    return path


def fetch_system_references(directory):
    """Download the exact releases used for accepted Greek/Cyrillic baselines."""
    directory = Path(directory)
    for name, pin in PINS["fonts"].items():
        output = directory / name
        if output.exists():
            verify(output.read_bytes(), pin["sha256"], output)
            continue
        archive = PINS["archives"][pin["archive"]]
        raw = fetch(archive["url"], directory / "downloads" / f"{pin['archive']}.zip", archive["sha256"])
        with zipfile.ZipFile(raw) as zipped:
            data = verify(zipped.read(pin["member"]), pin["sha256"], name)
        with atomic_output(output) as temporary:
            temporary.write_bytes(data)


def fetch_udhr(code, directory):
    name = f"udhr_{code}.xml"
    if name not in PINS["udhr"]:
        raise ValueError(f"{name}: add a reviewed checksum to reference-inputs.json first")
    url = f"https://raw.githubusercontent.com/eric-muller/udhr/{PINS['udhr_commit']}/data/udhr/{name}"
    return fetch(url, Path(directory) / name, PINS["udhr"][name])


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", action="store_true")
    parser.add_argument("--udhr", action="store_true")
    args = parser.parse_args()
    if args.fonts:
        fetch_system_references(ROOT / "build/refs")
    if args.udhr:
        for name in PINS["udhr"]:
            fetch_udhr(name.removeprefix("udhr_").removesuffix(".xml"), ROOT / "build/udhr")


if __name__ == "__main__":
    main()
