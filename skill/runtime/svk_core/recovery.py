"""Explicit inspection and recovery for interrupted SVK 2.1 writes."""

from __future__ import print_function

import json
from datetime import datetime, timezone
from pathlib import Path

from .constants import EVIDENCE_INDEX_FILE, EVIDENCE_RUNS_DIR, LOCK_FILE, PROFILE_FILE, STATE_FILE
from .render import render_documents
from .util import atomic_write, parse_utc, read_json, safe_project_root, sha256_file, utc_now, write_json, write_json_exclusive
from .verify import _validate_receipt_shape, check_project


def inspect_recovery(project_root):
    root = safe_project_root(project_root)
    index = read_json(root / EVIDENCE_INDEX_FILE)
    indexed = {item.get("id") for item in index.get("records", []) if item.get("kind") == "verification"}
    runs = root / EVIDENCE_RUNS_DIR
    orphans = sorted(path.name for path in runs.iterdir() if path.is_dir() and path.name not in indexed) if runs.exists() else []
    incomplete = []
    for path in sorted((root / ".svk/transactions").glob("*.json")):
        value = read_json(path)
        if value.get("status") == "in_progress":
            incomplete.append({"path": path.relative_to(root).as_posix(), "snapshot": str(path.with_suffix(".state-snapshot").exists()), "operation": value.get("operation")})
    lease = None
    lease_path = root / LOCK_FILE
    if lease_path.exists():
        lease = read_json(lease_path)
        try:
            lease["expired"] = parse_utc(lease.get("expires_at")) <= datetime.now(timezone.utc)
        except (TypeError, ValueError):
            lease["expired"] = None
    return {
        "result": "BLOCKED" if orphans or incomplete else "PASS",
        "orphan_receipts": orphans,
        "incomplete_transactions": incomplete,
        "lease": lease,
    }


def index_orphan_receipts(project_root, approve=False):
    if not approve:
        raise PermissionError("Indexing orphan receipts requires explicit --approve recovery permission.")
    root = safe_project_root(project_root)
    state = read_json(root / STATE_FILE)
    verifier_file = read_json(root / ".svk/verifiers.json")
    index = read_json(root / EVIDENCE_INDEX_FILE)
    indexed = {item.get("id") for item in index["records"]}
    task_ids = {task.get("id") for task in state["tasks"]}
    verifier_ids = set(verifier_file["verifiers"])
    added = []
    for directory in sorted((root / EVIDENCE_RUNS_DIR).iterdir()):
        if not directory.is_dir() or directory.name in indexed:
            continue
        receipt_path = directory / "receipt.json"
        receipt = read_json(receipt_path)
        diagnostics = []
        _validate_receipt_shape(receipt, directory.name, task_ids, verifier_ids, diagnostics, receipt_path.relative_to(root).as_posix())
        errors = [item for item in diagnostics if item["level"] == "ERROR"]
        if errors:
            raise ValueError("Orphan receipt %s is invalid: %s" % (directory.name, json.dumps(errors, sort_keys=True)))
        index["records"].append({
            "id": directory.name, "kind": "verification", "task_id": receipt["task_id"],
            "verifier_id": receipt["verifier_id"], "result": receipt["result"],
            "recorded_at": receipt["finished_at"], "path": receipt_path.relative_to(root).as_posix(),
            "receipt_sha256": sha256_file(receipt_path),
        })
        added.append(directory.name)
    write_json(root / EVIDENCE_INDEX_FILE, index)
    return {"status": "indexed", "receipt_ids": added, "check": check_project(root)}


def rollback_incomplete_transactions(project_root, approve=False):
    if not approve:
        raise PermissionError("Rolling back interrupted transactions requires explicit --approve recovery permission.")
    root = safe_project_root(project_root)
    recovered = []
    for path in sorted((root / ".svk/transactions").glob("*.json")):
        transaction = read_json(path)
        if transaction.get("status") != "in_progress":
            continue
        snapshot = path.with_suffix(".state-snapshot")
        if not snapshot.is_file():
            raise RuntimeError("Transaction lacks its state snapshot and cannot be auto-recovered: %s" % path)
        atomic_write(root / STATE_FILE, snapshot.read_text(encoding="utf-8"))
        state = read_json(root / STATE_FILE)
        documents = render_documents(read_json(root / PROFILE_FILE), state)
        for relative in ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md"):
            atomic_write(root / relative, documents[relative])
        lease = transaction.get("details", {}).get("lease")
        lease_path = root / LOCK_FILE
        if isinstance(lease, dict) and not lease_path.exists():
            write_json_exclusive(lease_path, lease)
        transaction["status"] = "rolled_back"
        transaction["recorded_at"] = utc_now()
        write_json(path, transaction)
        snapshot.unlink()
        recovered.append(path.relative_to(root).as_posix())
    return {"status": "rolled-back", "transactions": recovered, "check": check_project(root)}


def clear_expired_lease(project_root, approve=False):
    if not approve:
        raise PermissionError("Clearing an expired lease requires explicit --approve recovery permission.")
    root = safe_project_root(project_root)
    path = root / LOCK_FILE
    lease = read_json(path)
    if parse_utc(lease.get("expires_at")) > datetime.now(timezone.utc):
        raise PermissionError("The lease is not expired; only its owner may clear it during ordinary operation.")
    path.unlink()
    return {"status": "cleared-expired", "lease": lease, "check": check_project(root)}
