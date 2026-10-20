#!/usr/bin/env python3
"""Acquire the exact locked source for local analysis; never vendor it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def verified_bytes(data: bytes, entry: dict) -> bytes:
    digest = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if digest != entry["sha256"] or blob != entry["git_blob_sha"]:
        raise ValueError(f"Source hash mismatch: {entry['path']}")
    return data


def acquire(destination: Path, checkout: Path | None = None) -> int:
    lock = json.loads((ROOT / "source-lock.json").read_text())
    destination = destination.resolve()
    if checkout is not None:
        checkout = checkout.resolve()
    pending = []
    for entry in lock["files"]:
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe source path in lock")
        target = destination / str(relative)
        if not target.resolve().is_relative_to(destination):
            raise ValueError("Destination symlink leaves the source directory")
        if target.exists():
            verified_bytes(target.read_bytes(), entry)
            continue
        if checkout is not None:
            source = checkout / str(relative)
            if not source.resolve().is_relative_to(checkout):
                raise ValueError("Checkout symlink leaves the source directory")
            data = source.read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{relative}"
            request = Request(url, headers={"User-Agent": "name-of-the-rose/0.1.0"})
            with urlopen(request, timeout=30) as response:
                data = response.read()
        pending.append((target, verified_bytes(data, entry)))
    # Download and verify all files before writing any newly acquired file.
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(data)
            temp_path = Path(temporary.name)
        try:
            os.replace(temp_path, target)
        finally:
            temp_path.unlink(missing_ok=True)
    print(f"Verified {len(lock['files'])} source files at {lock['commit']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=ROOT / ".upstream")
    parser.add_argument("--from-checkout", type=Path,
                        help="Use an existing local source checkout instead of the network")
    args = parser.parse_args()
    try:
        return acquire(args.dest, args.from_checkout)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Source acquisition failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
