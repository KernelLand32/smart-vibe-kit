#!/usr/bin/env python3
"""Verify the Smart Vibe Kit *skill package* (not a bootstrapped project).

Usage:
  python scripts/verify_skill_package.py
  python scripts/verify_skill_package.py --root /path/to/smart-vibe-kit

Exit 0 = pass.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".ps1",
    ".sh",
    ".json",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".csv",
    ".html",
    ".js",
    ".ts",
    ".xml",
}

# Machine-/person-specific path leaks (package must stay generic).
PRIVACY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Windows user profile path", re.compile(r"[A-Za-z]:\\Users\\", re.I)),
    ("Windows user profile path", re.compile(r"[A-Za-z]:/Users/", re.I)),
    ("macOS /Users home path", re.compile(r"/Users/[A-Za-z0-9_.-]+/")),
    ("Linux /home path", re.compile(r"/home/[A-Za-z0-9_.-]+/")),
    ("AppData path", re.compile(r"\\AppData\\", re.I)),
    ("file:// URI", re.compile(r"file:///?", re.I)),
]

# Generic docs may mention these env vars / tilde paths — allowed.
PRIVACY_ALLOW_LINE = re.compile(
    r"%USERPROFILE%|%HOME%|~/\.cursor|~/\.claude|~/\.codex|~/\.agents|~/\.gemini|"
    r"Path\.home\(\)|USERPROFILE|os\.environ"
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
EMAIL_ALLOW = re.compile(
    r"@(example\.com|localhost|agentskills\.io|github\.com|python\.org)|"
    r"actions/(checkout|setup-python)@|"
    r"@v\d",
    re.I,
)

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".agents",
    ".cursor",
    ".claude",
    ".codex",
    ".gemini",
}


def load_manifest(root: Path) -> list[str]:
    text = (root / "scripts" / "install-manifest.txt").read_text(encoding="utf-8")
    paths: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(line.replace("\\", "/"))
    return paths


def scan_privacy(root: Path) -> list[str]:
    """Fail if committed package text embeds machine-specific paths or emails."""
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        # Do not flag this file's own pattern definitions.
        if rel == "scripts/verify_skill_package.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if "re.compile(" in line and ("Users" in line or "AppData" in line or "file:" in line):
                continue
            hard_user = re.search(r"[A-Za-z]:\\Users\\|[A-Za-z]:/Users/", line, re.I)
            if PRIVACY_ALLOW_LINE.search(line) and not hard_user:
                pass
            else:
                for label, pat in PRIVACY_PATTERNS:
                    if pat.search(line):
                        hits.append(f"{rel}:{i}: {label}: {line.strip()[:120]}")
            for m in EMAIL_RE.finditer(line):
                addr = m.group(0)
                if EMAIL_ALLOW.search(line) or EMAIL_ALLOW.search(addr):
                    continue
                hits.append(f"{rel}:{i}: email: {addr}")
            if len(hits) >= 30:
                hits.append("… (truncated)")
                return hits
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Smart Vibe Kit skill package")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    root = (args.root or Path(__file__).resolve().parent.parent).resolve()

    errors: list[str] = []

    skill = root / "SKILL.md"
    if not skill.is_file():
        errors.append("SKILL.md missing")
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    front = skill.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^name:\s*[\"']?([^\s\"']+)", front, re.M)
    name = m.group(1) if m else None
    if name != "smart-vibe-kit":
        errors.append(f"SKILL.md name must be smart-vibe-kit, got {name!r}")
    if root.name != "smart-vibe-kit":
        errors.append(
            f"folder name should be smart-vibe-kit when installed (got {root.name!r})"
        )

    vm = re.search(r'version:\s*["\']([^"\']+)["\']', front)
    skill_ver = vm.group(1) if vm else None

    meta_path = root / "skill.json"
    if not meta_path.is_file():
        errors.append("skill.json missing")
    else:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("name") != "smart-vibe-kit":
            errors.append("skill.json name mismatch")
        if skill_ver and meta.get("version") != skill_ver:
            errors.append(
                f"version mismatch SKILL.md={skill_ver!r} skill.json={meta.get('version')!r}"
            )
        if meta.get("entrypoint") != "SKILL.md":
            errors.append("skill.json entrypoint must be SKILL.md")

    for rel in load_manifest(root):
        if not (root / rel).exists():
            errors.append(f"manifest path missing: {rel}")

    privacy = scan_privacy(root)
    if privacy:
        errors.append(
            "personal/machine-specific content found (keep skill generic):\n    - "
            + "\n    - ".join(privacy)
        )

    if errors:
        print(f"FAIL - skill package at {root}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS - skill package OK at {root}")
    print(f"  name={name} version={skill_ver}")
    print(f"  manifest entries={len(load_manifest(root))}")
    print("  privacy scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
