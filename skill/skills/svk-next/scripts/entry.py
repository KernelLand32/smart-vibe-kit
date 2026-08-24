#!/usr/bin/env python3
"""Installed/source-tree wrapper for SVK Next."""

import subprocess
import sys
from pathlib import Path


def runtime_path():
    here = Path(__file__).resolve()
    candidates = (here.parents[3] / "runtime" / "svk.py", here.parents[2] / ".smart-vibe-kit-2" / "runtime" / "svk.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Smart Vibe Kit 2 runtime was not installed beside this skill.")


if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, str(runtime_path()), "next"] + sys.argv[1:]))
