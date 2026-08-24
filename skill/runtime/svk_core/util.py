"""Dependency-free filesystem, JSON, hashing, and safety helpers."""

from __future__ import print_function

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .constants import VERSION


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    atomic_write(path, payload)


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, str(path))
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def append_json_line(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_manifest(root, relative_paths):
    root = Path(root)
    return {
        str(relative).replace("\\", "/"): sha256_file(root / relative)
        for relative in sorted(relative_paths)
    }


def safe_project_root(value):
    root = Path(value).expanduser().resolve()
    anchor = Path(root.anchor).resolve()
    home = Path(os.path.abspath(os.path.expanduser("~")))
    if root == anchor:
        raise ValueError("SVK refuses to operate on a filesystem root: %s" % root)
    if root == home:
        raise ValueError("SVK refuses to operate directly on the home directory: %s" % root)
    return root


def ensure_within(path, parent):
    resolved = Path(path).resolve()
    base = Path(parent).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise ValueError("Path escapes the allowed root: %s" % resolved)
    return resolved


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def title_from_path(path):
    value = Path(path).name.replace("-", " ").replace("_", " ").strip()
    return value.title() or "Project"


def owned_marker(kind, source="smart-vibe-kit"):
    return {"owner": source, "kind": kind, "version": VERSION}


def remove_empty_parents(path, stop):
    current = Path(path)
    stop = Path(stop).resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def unique_sibling(root, label):
    import uuid

    root = Path(root).resolve()
    return root.parent / (".%s-%s" % (label, uuid.uuid4().hex))


def copy_tree_files(source, destination, created=None):
    """Copy a staged tree without following links and return created files."""
    source = Path(source)
    destination = Path(destination)
    if created is None:
        created = []
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_symlink():
            raise ValueError("Symbolic links are not accepted in an SVK transaction: %s" % item)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            if target.exists():
                raise FileExistsError("Destination already exists: %s" % target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(target))
            created.append(target)
    return created
