#!/usr/bin/env python3
"""Cross-platform, ownership-aware installer for Smart Vibe Kit 2.0."""

from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


VERSION = "2.0.0"
INSTALLER_DIR = Path(__file__).resolve().parent
SKILL_BUNDLE = (INSTALLER_DIR.parent / "skill").resolve()
COMPATIBILITY_FILE = SKILL_BUNDLE / "compatibility.json"
SKILLS = ("svk-interview", "svk-refresh", "svk-next", "svk-check")
SHARED_ENTRY = ".smart-vibe-kit-2"
OWNER_FILE = ".svk-owner.json"


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".%s.%s.tmp" % (path.name, uuid.uuid4().hex))
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def load_compatibility():
    return read_json(COMPATIBILITY_FILE)


def safe_destination(value):
    destination = Path(value).expanduser().resolve()
    anchor = Path(destination.anchor).resolve()
    home = Path(os.path.abspath(os.path.expanduser("~")))
    if destination in (anchor, home):
        raise ValueError("Refusing unsafe skill destination: %s" % destination)
    return destination


def resolve_destinations(target, scope="user", project_root=None, explicit_destination=None):
    compatibility = load_compatibility()
    hosts = compatibility["hosts"]
    if explicit_destination:
        return [{"destination": safe_destination(explicit_destination), "hosts": [target]}]
    requested = list(hosts) if target == "all" else [item.strip() for item in target.split(",") if item.strip()]
    unknown = sorted(set(requested) - set(hosts))
    if unknown:
        raise ValueError("Unknown installer targets: %s" % ", ".join(unknown))
    if scope == "project":
        if not project_root:
            project_root = "."
        base = Path(project_root).expanduser().resolve()
    grouped = {}
    for host in requested:
        configured = hosts[host]["project_root" if scope == "project" else "user_root"]
        destination = (base / configured).resolve() if scope == "project" else Path(configured).expanduser().resolve()
        destination = safe_destination(destination)
        grouped.setdefault(str(destination), []).append(host)
    return [{"destination": Path(path), "hosts": names} for path, names in sorted(grouped.items())]


def owner_payload(kind):
    return {"owner": "smart-vibe-kit", "kind": kind, "version": VERSION}


def is_owned(path):
    marker = Path(path) / OWNER_FILE
    if not marker.is_file():
        return False
    try:
        return read_json(marker).get("owner") == "smart-vibe-kit"
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def entries():
    return SKILLS + (SHARED_ENTRY,)


def validate_bundle():
    if not SKILL_BUNDLE.is_dir():
        raise FileNotFoundError("Sibling skill bundle is missing: %s" % SKILL_BUNDLE)
    if (SKILL_BUNDLE / "VERSION").read_text(encoding="utf-8").strip() != VERSION:
        raise ValueError("Installer and skill bundle versions disagree.")
    for name in SKILLS:
        source = SKILL_BUNDLE / "skills" / name
        if not (source / "SKILL.md").is_file() or not (source / "scripts/entry.py").is_file():
            raise FileNotFoundError("Skill bundle is incomplete: %s" % name)
    completed = subprocess.run(
        [sys.executable, "-B", str(SKILL_BUNDLE / "runtime" / "svk.py"), "check", "--package", "--root", str(SKILL_BUNDLE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if completed.returncode != 0:
        detail = completed.stdout.strip() or completed.stderr.strip() or "unknown package-check failure"
        raise ValueError("Skill bundle failed package validation: %s" % detail)


def _policy_key_for_hosts(hosts):
    configured = load_compatibility()["hosts"]
    values = [configured[host].get("frontmatter_policy_key") for host in hosts if host in configured]
    keys = {value for value in values if value}
    if len(keys) == 1 and all(values):
        return next(iter(keys))
    return None


def _inject_policy_key(skill_file, key):
    if not key:
        return
    path = Path(skill_file)
    text = path.read_text(encoding="utf-8")
    closing = text.find("\n---", 4)
    if not text.startswith("---\n") or closing < 0:
        raise ValueError("Cannot adapt invalid SKILL.md frontmatter: %s" % path)
    adapted = text[:closing] + "\n%s: true" % key + text[closing:]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(adapted)


def _copy_source_to_stage(stage, hosts):
    stage.mkdir(parents=False, exist_ok=False)
    policy_key = _policy_key_for_hosts(hosts)
    for name in SKILLS:
        target = stage / name
        shutil.copytree(str(SKILL_BUNDLE / "skills" / name), str(target), symlinks=False)
        _inject_policy_key(target / "SKILL.md", policy_key)
        write_json(target / OWNER_FILE, owner_payload("skill"))
    shared = stage / SHARED_ENTRY
    shared.mkdir()
    shutil.copytree(str(SKILL_BUNDLE / "runtime"), str(shared / "runtime"), symlinks=False)
    shutil.copytree(str(SKILL_BUNDLE / "schemas"), str(shared / "schemas"), symlinks=False)
    shutil.copy2(str(SKILL_BUNDLE / "VERSION"), str(shared / "VERSION"))
    shutil.copy2(str(COMPATIBILITY_FILE), str(shared / "compatibility.json"))
    write_json(shared / OWNER_FILE, owner_payload("shared-runtime"))


def preflight(destination, uninstall=False):
    destination = safe_destination(destination)
    if destination.exists() and not destination.is_dir():
        raise NotADirectoryError("Skill destination is not a directory: %s" % destination)
    conflicts = []
    for name in entries():
        path = destination / name
        if path.exists() and not is_owned(path):
            conflicts.append(str(path))
        if uninstall and not path.exists():
            continue
    if conflicts:
        raise PermissionError("Refusing to replace or remove unowned paths: %s" % ", ".join(conflicts))


def install_destination(destination, dry_run=False, hosts=None):
    destination = safe_destination(destination)
    hosts = list(hosts or ["agents"])
    preflight(destination)
    if dry_run:
        return {"destination": str(destination), "action": "would-install", "entries": list(entries()), "policy_adapter": _policy_key_for_hosts(hosts)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=False, exist_ok=True) if not destination.exists() else None
    stage = destination.parent / (".svk-install-stage-%s" % uuid.uuid4().hex)
    backup = destination.parent / (".svk-install-backup-%s" % uuid.uuid4().hex)
    moved_old = []
    moved_new = []
    try:
        _copy_source_to_stage(stage, hosts)
        backup.mkdir(parents=False, exist_ok=False)
        for name in entries():
            current = destination / name
            if current.exists():
                shutil.move(str(current), str(backup / name))
                moved_old.append(name)
            shutil.move(str(stage / name), str(current))
            moved_new.append(name)
        return {
            "destination": str(destination),
            "action": "installed",
            "entries": list(entries()),
            "backup": str(backup),
            "moved_old": moved_old,
            "moved_new": moved_new,
            "policy_adapter": _policy_key_for_hosts(hosts),
        }
    except Exception:
        for name in reversed(moved_new):
            current = destination / name
            if current.exists() and is_owned(current):
                shutil.rmtree(str(current))
        for name in reversed(moved_old):
            saved = backup / name
            if saved.exists():
                shutil.move(str(saved), str(destination / name))
        raise
    finally:
        if stage.exists():
            shutil.rmtree(str(stage))


def rollback_install(receipt):
    destination = safe_destination(receipt["destination"])
    backup = Path(receipt["backup"]).resolve()
    if backup.parent != destination.parent:
        raise ValueError("Backup path is outside the installation transaction.")
    for name in reversed(receipt["moved_new"]):
        current = destination / name
        if current.exists() and is_owned(current):
            shutil.rmtree(str(current))
    for name in reversed(receipt["moved_old"]):
        saved = backup / name
        if saved.exists():
            shutil.move(str(saved), str(destination / name))


def finalize_install(receipt):
    backup = Path(receipt["backup"]).resolve()
    destination = safe_destination(receipt["destination"])
    if backup.parent != destination.parent or not backup.name.startswith(".svk-install-backup-"):
        raise ValueError("Invalid backup receipt.")
    if backup.exists():
        shutil.rmtree(str(backup))


def uninstall_destination(destination, dry_run=False):
    destination = safe_destination(destination)
    preflight(destination, uninstall=True)
    present = [name for name in entries() if (destination / name).exists()]
    if dry_run:
        return {"destination": str(destination), "action": "would-uninstall", "entries": present}
    quarantine = destination.parent / (".svk-uninstall-%s" % uuid.uuid4().hex)
    quarantine.mkdir(parents=False, exist_ok=False)
    moved = []
    try:
        for name in present:
            shutil.move(str(destination / name), str(quarantine / name))
            moved.append(name)
        return {"destination": str(destination), "action": "uninstalled", "entries": moved, "quarantine": str(quarantine)}
    except Exception:
        for name in reversed(moved):
            saved = quarantine / name
            if saved.exists():
                shutil.move(str(saved), str(destination / name))
        raise


def rollback_uninstall(receipt):
    destination = safe_destination(receipt["destination"])
    quarantine = Path(receipt["quarantine"]).resolve()
    if quarantine.parent != destination.parent:
        raise ValueError("Quarantine path is outside the uninstall transaction.")
    for name in reversed(receipt["entries"]):
        saved = quarantine / name
        if saved.exists():
            shutil.move(str(saved), str(destination / name))


def finalize_uninstall(receipt):
    quarantine = Path(receipt["quarantine"]).resolve()
    destination = safe_destination(receipt["destination"])
    if quarantine.parent != destination.parent or not quarantine.name.startswith(".svk-uninstall-"):
        raise ValueError("Invalid uninstall receipt.")
    if quarantine.exists():
        shutil.rmtree(str(quarantine))


def run_transaction(destinations, uninstall=False, dry_run=False):
    for item in destinations:
        preflight(item["destination"], uninstall=uninstall)
    receipts = []
    rollback = rollback_uninstall if uninstall else rollback_install
    finalize = finalize_uninstall if uninstall else finalize_install
    try:
        for item in destinations:
            if uninstall:
                receipt = uninstall_destination(item["destination"], dry_run=dry_run)
            else:
                receipt = install_destination(item["destination"], dry_run=dry_run, hosts=item["hosts"])
            receipt["hosts"] = item["hosts"]
            receipts.append(receipt)
        if not dry_run:
            for receipt in receipts:
                finalize(receipt)
        return receipts
    except Exception:
        if not dry_run:
            for receipt in reversed(receipts):
                rollback(receipt)
        raise


def build_parser():
    parser = argparse.ArgumentParser(description="Install Smart Vibe Kit 2.0 skills")
    parser.add_argument("--target", default="agents", help="Host ID, comma-separated IDs, or all")
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project-root")
    parser.add_argument("--dest", help="Explicit skill root; intended for testing or custom hosts")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true", dest="list_targets")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        validate_bundle()
        compatibility = load_compatibility()
        if args.list_targets:
            print(json.dumps(compatibility, indent=2, sort_keys=True))
            return 0
        destinations = resolve_destinations(args.target, args.scope, args.project_root, args.dest)
        results = run_transaction(destinations, uninstall=args.uninstall, dry_run=args.dry_run)
        print(json.dumps({"version": VERSION, "results": results}, indent=2, sort_keys=True))
        return 0
    except (FileNotFoundError, FileExistsError, PermissionError, ValueError, json.JSONDecodeError, OSError) as error:
        print("Installer error: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
