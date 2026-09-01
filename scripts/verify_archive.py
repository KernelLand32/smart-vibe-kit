#!/usr/bin/env python3
"""Build, extract, and verify an SVK release archive in a clean directory."""

from __future__ import print_function

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "skill" / "VERSION").read_text(encoding="utf-8").strip()
ARCHIVE_ROOT = "smart-vibe-kit-%s" % VERSION


def safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(str(archive), "r") as handle:
        for member in handle.infolist():
            target = (destination / member.filename).resolve()
            try:
                target.relative_to(destination)
            except ValueError:
                raise ValueError("Archive member escapes extraction root: %s" % member.filename)
        handle.extractall(str(destination))


def main():
    with tempfile.TemporaryDirectory(prefix="svk-archive-check-") as temporary:
        base = Path(temporary)
        archive = base / (ARCHIVE_ROOT + ".zip")
        build = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "build_release.py"), "--output", str(archive)]
        )
        if build.returncode != 0:
            return build.returncode
        extracted = base / "extracted"
        safe_extract(archive, extracted)
        release_root = extracted / ARCHIVE_ROOT
        completed = subprocess.run(
            [sys.executable, "-B", str(release_root / "scripts" / "release_check.py")],
            cwd=str(release_root),
        )
        payload = {
            "version": VERSION,
            "archive": archive.name,
            "extracted_root": ARCHIVE_ROOT,
            "result": "PASS" if completed.returncode == 0 else "ERROR",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
