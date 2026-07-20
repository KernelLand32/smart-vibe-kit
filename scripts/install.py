#!/usr/bin/env python3
"""Cross-platform Smart Vibe Kit installer (Windows / macOS / Linux).

Installs the Agent Skills package into popular AI coding hosts.

Examples:
  python scripts/install.py
  python scripts/install.py --target all --scope user
  python scripts/install.py --target cursor --scope project --project-root .
  python scripts/install.py --list
  python scripts/install.py --uninstall --target agents --scope user
  python scripts/install.py --what-if --target all
  python scripts/install.py --link   # symlink package (dev)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

SKILL_NAME = "smart-vibe-kit"
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PACKAGE_ROOT / "scripts" / "install-manifest.txt"

# Native + shared destinations. `agents` is the agentskills.io interoperability path
# (Cursor, Gemini CLI, Codex project, and others discover ~/.agents/skills).
# Codex *project* path equals `agents` project path - installer dedupes by resolved path.
HOSTS: dict[str, dict[str, str]] = {
    "agents": {
        "user": "~/.agents/skills/" + SKILL_NAME,
        "project": ".agents/skills/" + SKILL_NAME,
        "note": "Shared Agent Skills path (Cursor, Gemini, Codex project, ...)",
    },
    "cursor": {
        "user": "~/.cursor/skills/" + SKILL_NAME,
        "project": ".cursor/skills/" + SKILL_NAME,
        "note": "Cursor native",
    },
    "claude": {
        "user": "~/.claude/skills/" + SKILL_NAME,
        "project": ".claude/skills/" + SKILL_NAME,
        "note": "Claude Code (+ many hosts that also scan .claude/skills)",
    },
    "codex": {
        "user": "~/.codex/skills/" + SKILL_NAME,
        "project": ".agents/skills/" + SKILL_NAME,
        "note": "OpenAI Codex (user: ~/.codex; project: .agents)",
    },
    "gemini": {
        "user": "~/.gemini/skills/" + SKILL_NAME,
        "project": ".gemini/skills/" + SKILL_NAME,
        "note": "Gemini CLI native (also reads .agents/skills)",
    },
}

ALL_TARGETS = ["agents", "cursor", "claude", "codex", "gemini"]


def home_dir() -> Path:
    # Windows: USERPROFILE; Unix: HOME. Path.home() handles both.
    return Path.home()


def expand_dest(pattern: str, project_root: Path) -> Path:
    if pattern.startswith("~/"):
        return (home_dir() / pattern[2:]).resolve()
    if pattern.startswith("~\\"):
        return (home_dir() / pattern[2:].replace("\\", "/")).resolve()
    return (project_root / pattern).resolve()


def load_manifest() -> list[str]:
    if not MANIFEST.is_file():
        raise SystemExit(f"Missing manifest: {MANIFEST}")
    paths: list[str] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(line.replace("\\", "/"))
    return paths


def backup_dir(dest: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = Path(str(dest) + f".bak-{stamp}")
    dest.rename(backup)
    return backup


def copy_tree_from_manifest(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for rel in load_manifest():
        src = PACKAGE_ROOT / rel
        if not src.exists():
            raise FileNotFoundError(f"Manifest path missing in package: {rel}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)

    example_src = PACKAGE_ROOT / "examples" / "offline-habit-tracker"
    if example_src.is_dir():
        example_dest = dest / "examples" / "offline-habit-tracker"
        example_dest.parent.mkdir(parents=True, exist_ok=True)
        if example_dest.exists():
            shutil.rmtree(example_dest)
        shutil.copytree(example_src, example_dest)
        print("  + examples/offline-habit-tracker")


def link_package(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    os.symlink(PACKAGE_ROOT, dest, target_is_directory=True)


def install_claude_legacy(scope: str, project_root: Path, what_if: bool) -> None:
    if scope == "project":
        cmd_dir = project_root / ".claude" / "commands"
    else:
        cmd_dir = home_dir() / ".claude" / "commands"
    src = PACKAGE_ROOT / "adapters" / "claude" / "smart-vibe-kit.md"
    target = cmd_dir / "smart-vibe-kit.md"
    print(f"  + legacy Claude command: {target}")
    if what_if:
        return
    cmd_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)


def resolve_targets(target: str) -> list[str]:
    if target == "all":
        return list(ALL_TARGETS)
    if target not in HOSTS:
        raise SystemExit(
            f"Unknown target {target!r}. Choose: all, {', '.join(HOSTS)}"
        )
    return [target]


def print_list(project_root: Path) -> None:
    print(f"Package: {PACKAGE_ROOT}")
    print(f"Home:    {home_dir()}")
    print(f"Project: {project_root}")
    print()
    print(f"{'Host':<10} {'Scope':<8} {'Path'}")
    print("-" * 72)
    for name, cfg in HOSTS.items():
        for scope in ("user", "project"):
            path = expand_dest(cfg[scope], project_root)
            marker = " [installed]" if (path / "SKILL.md").is_file() else ""
            print(f"{name:<10} {scope:<8} {path}{marker}")
        print(f"{'':10} {'note':<8} {cfg['note']}")
        print()


def install(
    targets: list[str],
    scope: str,
    project_root: Path,
    *,
    what_if: bool,
    no_backup: bool,
    link: bool,
    also_legacy_claude: bool,
) -> int:
    # Dedupe by resolved destination (codex project == agents project).
    seen: set[Path] = set()
    for name in targets:
        dest = expand_dest(HOSTS[name][scope], project_root)
        if dest in seen:
            print(f"-> {name} ({scope}): {dest} (skip duplicate path)")
            continue
        seen.add(dest)
        print(f"-> {name} ({scope}): {dest}")
        if what_if:
            if name == "claude" and also_legacy_claude:
                install_claude_legacy(scope, project_root, True)
            continue
        if dest.exists() or dest.is_symlink():
            if no_backup:
                if dest.is_symlink() or dest.is_file():
                    dest.unlink()
                else:
                    shutil.rmtree(dest)
            else:
                if dest.is_symlink():
                    backup = Path(
                        str(dest)
                        + f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    )
                    dest.rename(backup)
                    print(f"  backup -> {backup}")
                else:
                    backup = backup_dir(dest)
                    print(f"  backup -> {backup}")
        if link:
            try:
                link_package(dest)
                print("  mode: symlink -> package root")
            except OSError as exc:
                print(
                    f"  symlink failed ({exc}); falling back to copy",
                    file=sys.stderr,
                )
                copy_tree_from_manifest(dest)
        else:
            copy_tree_from_manifest(dest)

        if name == "claude" and also_legacy_claude:
            install_claude_legacy(scope, project_root, what_if)

    print()
    print("Done. Only slash command: /smart-vibe-kit <project idea>")
    print("Tip: prefer --target agents for one shared install across many hosts.")
    return 0


def uninstall(
    targets: list[str],
    scope: str,
    project_root: Path,
    *,
    what_if: bool,
) -> int:
    seen: set[Path] = set()
    for name in targets:
        dest = expand_dest(HOSTS[name][scope], project_root)
        if dest in seen:
            continue
        seen.add(dest)
        exists = dest.exists() or dest.is_symlink()
        print(f"-> uninstall {name} ({scope}): {dest}" + ("" if exists else " (absent)"))
        if what_if or not exists:
            continue
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    print("Done.")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Avoid Windows cp1252 crashes on console output
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Install Smart Vibe Kit into AI coding host skill directories"
    )
    parser.add_argument(
        "--target",
        "-t",
        default="all",
        help=f"Host: all | {' | '.join(HOSTS)} (default: all)",
    )
    parser.add_argument(
        "--scope",
        "-s",
        choices=("user", "project"),
        default="user",
        help="user = home dir; project = --project-root (default: user)",
    )
    parser.add_argument(
        "--project-root",
        "-p",
        type=Path,
        default=Path.cwd(),
        help="Project root for --scope project (default: cwd)",
    )
    parser.add_argument(
        "--also-legacy-claude-command",
        action="store_true",
        help="Also copy adapters/claude/smart-vibe-kit.md to .claude/commands/",
    )
    parser.add_argument(
        "--what-if",
        "--dry-run",
        action="store_true",
        help="Print destinations only; do not write",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Replace existing install without .bak-TIMESTAMP",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Symlink to this package (dev). Falls back to copy if unsupported.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show destinations and whether SKILL.md is installed",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove installed skill directories for the chosen target/scope",
    )
    args = parser.parse_args(argv)
    project_root = args.project_root.resolve()

    if args.list:
        print_list(project_root)
        return 0

    targets = resolve_targets(args.target)
    if args.uninstall:
        return uninstall(
            targets, args.scope, project_root, what_if=args.what_if
        )
    return install(
        targets,
        args.scope,
        project_root,
        what_if=args.what_if,
        no_backup=args.no_backup,
        link=args.link,
        also_legacy_claude=args.also_legacy_claude_command,
    )


if __name__ == "__main__":
    raise SystemExit(main())
