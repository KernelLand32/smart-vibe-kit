#!/usr/bin/env python3
"""Build a deterministic Smart Vibe Kit release archive and checksum."""

from __future__ import print_function

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "skill/VERSION").read_text(encoding="utf-8").strip()
ARCHIVE_ROOT = "smart-vibe-kit-%s" % VERSION
FIXED_TIME = (2026, 8, 23, 0, 0, 0)
EXCLUDED_PARTS = {".git", "dist", "__pycache__", ".pytest_cache", "node_modules"}


def source_files():
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.relative_to(ROOT).as_posix()):
        if not path.is_file():
            continue
        parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDED_PARTS for part in parts) or path.suffix in (".pyc", ".pyo"):
            continue
        yield path


def build(output):
    output = Path(output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".%s." % output.name, suffix=".tmp", dir=str(output.parent))
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(str(temporary), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in source_files():
                relative = path.relative_to(ROOT).as_posix()
                info = zipfile.ZipInfo("%s/%s" % (ARCHIVE_ROOT, relative), FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o755 if path.suffix in (".py", ".ps1", ".sh") else 0o644) << 16
                archive.writestr(info, path.read_bytes())
        os.replace(str(temporary), str(output))
    finally:
        if temporary.exists():
            temporary.unlink()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(output.suffix + ".sha256")
    with checksum.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("%s  %s\n" % (digest, output.name))
    return digest, checksum


def main(arguments=None):
    parser = argparse.ArgumentParser(description="Build the Smart Vibe Kit release archive")
    parser.add_argument("--output", default=str(ROOT / "dist" / (ARCHIVE_ROOT + ".zip")))
    args = parser.parse_args(arguments)
    completed = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/release_check.py")])
    if completed.returncode != 0:
        return completed.returncode
    digest, checksum = build(args.output)
    print("archive=%s" % Path(args.output).expanduser().resolve())
    print("sha256=%s" % digest)
    print("checksum=%s" % checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
