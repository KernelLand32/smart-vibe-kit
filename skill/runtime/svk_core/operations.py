"""Transactional project operations used by all four SVK skills."""

from __future__ import print_function

import json
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .constants import EVIDENCE_FILE, INSTALL_FILE, LOCK_FILE, MANIFEST_FILE, PROFILE_FILE, STATE_FILE, VERSION
from .profile import build_profile
from .render import build_state, next_action, render_documents
from .util import (
    append_json_line,
    atomic_write,
    copy_tree_files,
    file_manifest,
    read_json,
    remove_empty_parents,
    safe_project_root,
    unique_sibling,
    utc_now,
    write_json,
)
from .verify import check_project


INTERVIEW_QUESTIONS = (
    "What should this project accomplish, and for whom?",
    "Which outcomes prove the first useful version works?",
    "What is explicitly outside scope?",
    "Is it user-facing, does it include a UI, or will it be deployed?",
    "Which platforms and external integrations must it support?",
    "Will it handle secrets, personal/sensitive data, money, safety, or regulated activity?",
    "How current must outside research be, and which claims require citations?",
    "Who will work on it, and which constraints cannot be negotiated?",
)

GREENFIELD_METADATA = {".git", ".gitignore", ".gitattributes", ".editorconfig", "LICENSE", "README.md"}


def interview_questions():
    return list(INTERVIEW_QUESTIONS)


def classify_project_root(project_root):
    root = safe_project_root(project_root)
    if not root.exists():
        return "missing"
    if not root.is_dir():
        raise NotADirectoryError("Project root is not a directory: %s" % root)
    entries = {path.name for path in root.iterdir()}
    if not entries:
        return "empty"
    if (root / ".svk").exists():
        return "existing-svk" if (root / PROFILE_FILE).is_file() else "partial-svk"
    if entries.issubset(GREENFIELD_METADATA):
        return "greenfield-metadata"
    return "existing-project"


def _initial_evidence(profile):
    return {
        "task_id": "1.1.1",
        "recorded_at": utc_now(),
        "summary": "Project interview captured and deterministic adaptive profile generated.",
        "commands": ["svk-interview"],
        "artifacts": [PROFILE_FILE, STATE_FILE],
        "result": "pass",
        "profile": profile["profile"],
        "modules": profile["modules"],
    }


def _write_stage(stage, profile, charter_accepted):
    state = build_state(profile, charter_accepted=charter_accepted)
    documents = render_documents(profile, state)
    write_json(stage / PROFILE_FILE, profile)
    write_json(stage / STATE_FILE, state)
    atomic_write(stage / EVIDENCE_FILE, json.dumps(_initial_evidence(profile), sort_keys=True) + "\n")
    if charter_accepted:
        append_json_line(
            stage / EVIDENCE_FILE,
            {
                "task_id": "1.1.2",
                "recorded_at": utc_now(),
                "summary": "Project charter accepted during the interview.",
                "commands": ["svk-interview --charter-accepted"],
                "artifacts": ["docs/adr/0001-project-charter.md"],
                "result": "pass",
            },
        )
    for relative, content in documents.items():
        atomic_write(stage / relative, content)
    write_json(stage / INSTALL_FILE, {"owner": "smart-vibe-kit", "version": VERSION, "created_at": utc_now()})
    transaction_id = uuid.uuid4().hex
    write_json(
        stage / ".svk/transactions" / ("scaffold-%s.json" % transaction_id),
        {"id": transaction_id, "operation": "scaffold", "status": "committed", "recorded_at": utc_now()},
    )
    tracked = [
        path.relative_to(stage)
        for path in stage.rglob("*")
        if path.is_file()
        and path.relative_to(stage).as_posix() not in (MANIFEST_FILE, ".svk-stage-owner.json")
    ]
    write_json(
        stage / MANIFEST_FILE,
        {"version": VERSION, "created_at": utc_now(), "files": file_manifest(stage, tracked)},
    )


def scaffold(project_root, answers, charter_accepted=False):
    root = safe_project_root(project_root)
    profile = build_profile(answers)
    classification = classify_project_root(root)
    if classification in ("existing-svk", "partial-svk", "existing-project"):
        raise FileExistsError(
            "Interview requires a new or greenfield folder; classified %s: %s"
            % (classification, root)
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    stage = unique_sibling(root, "svk-stage")
    stage.mkdir(parents=False, exist_ok=False)
    marker = stage / ".svk-stage-owner.json"
    write_json(marker, {"owner": "smart-vibe-kit", "version": VERSION, "target": str(root)})
    root_created = False
    created = []
    created_directories = []
    try:
        _write_stage(stage, profile, charter_accepted)
        marker.unlink()
        stage_result = check_project(stage)
        if stage_result["result"] != "PASS":
            raise ValueError("Generated scaffold failed its semantic gate: %s" % json.dumps(stage_result, sort_keys=True))
        transaction_path = next((stage / ".svk/transactions").glob("scaffold-*.json"))
        committed_transaction = read_json(transaction_path)
        in_progress_transaction = dict(committed_transaction)
        in_progress_transaction["status"] = "in_progress"
        write_json(transaction_path, in_progress_transaction)
        if not root.exists():
            root.mkdir(parents=False, exist_ok=False)
            root_created = True
        collisions = [
            root / path.relative_to(stage)
            for path in stage.rglob("*")
            if path.is_file() and (root / path.relative_to(stage)).exists()
        ]
        if collisions:
            raise FileExistsError("Destination already exists: %s" % collisions[0])
        created_directories = [
            root / path.relative_to(stage)
            for path in stage.rglob("*")
            if path.is_dir() and not (root / path.relative_to(stage)).exists()
        ]
        copy_tree_files(stage, root, created)
        write_json(root / transaction_path.relative_to(stage), committed_transaction)
        result = check_project(root)
        if result["result"] != "PASS":
            raise ValueError("Committed scaffold failed its semantic gate: %s" % json.dumps(result, sort_keys=True))
        return {
            "root": str(root),
            "workspace_classification": classification,
            "profile": profile,
            "state": read_json(root / STATE_FILE),
            "check": result,
        }
    except Exception:
        for path in reversed(created):
            try:
                path.unlink()
                remove_empty_parents(path.parent, root)
            except OSError:
                pass
        for path in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
            try:
                path.rmdir()
            except OSError:
                pass
        if root_created:
            try:
                root.rmdir()
            except OSError:
                pass
        raise
    finally:
        if stage.exists():
            marker_path = stage / ".svk-stage-owner.json"
            if marker_path.exists() or not any(stage.iterdir()):
                shutil.rmtree(str(stage))
            else:
                # This exact path was created by this transaction; never broaden it.
                shutil.rmtree(str(stage))


def refresh(project_root):
    root = safe_project_root(project_root)
    result = check_project(root)
    try:
        profile = read_json(root / PROFILE_FILE)
    except (OSError, ValueError, json.JSONDecodeError):
        profile = {}
    try:
        state = read_json(root / STATE_FILE)
    except (OSError, ValueError, json.JSONDecodeError):
        state = {}
    active = [task for task in state.get("tasks", []) if task.get("status") in ("in_progress", "blocked")]
    blocker = next((task.get("blocker") for task in active if task.get("status") == "blocked"), None)
    return {
        "result": result["result"],
        "project": profile.get("title"),
        "profile": profile.get("profile"),
        "modules": profile.get("modules"),
        "stage": state.get("stage"),
        "active_task": active[0] if len(active) == 1 else None,
        "blocker": blocker,
        "next_action": state.get("next_action"),
        "check": result,
    }


def _lock_path(root):
    return Path(root) / LOCK_FILE


def _write_lock_exclusive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def next_show(project_root):
    root = safe_project_root(project_root)
    check = check_project(root)
    if check["result"] == "ERROR":
        return {"result": "ERROR", "status": "unsafe", "task": None, "check": check}
    state = read_json(root / STATE_FILE)
    action = state.get("next_action")
    if action is None:
        return {"result": check["result"], "status": "complete", "task": None, "check": check}
    task = next((item for item in state.get("tasks", []) if item.get("id") == action.get("task_id")), None)
    if task is None:
        raise ValueError("next_action refers to a missing task; run SVK Check.")
    return {"result": check["result"], "status": task.get("status"), "task": task, "instruction": action.get("instruction"), "check": check}


def next_begin(project_root, owner, allow_human_gate=False, ttl_minutes=120):
    root = safe_project_root(project_root)
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("A non-empty lock owner is required.")
    if ttl_minutes < 1 or ttl_minutes > 10080:
        raise ValueError("Lock TTL must be between 1 and 10080 minutes.")
    packet = next_show(root)
    if packet.get("result") == "ERROR":
        raise RuntimeError("Project state is unsafe to begin: %s" % json.dumps(packet["check"]["diagnostics"], sort_keys=True))
    task = packet.get("task")
    if task is None:
        return packet
    if task.get("human_gate") and not allow_human_gate:
        raise PermissionError("Task %s is a human gate; begin again with explicit --allow-human-gate." % task["id"])
    unsafe_diagnostics = [
        item for item in packet["check"]["diagnostics"]
        if item["level"] == "ERROR" or item["code"] in ("SVK-LOCK-PRESENT", "SVK-TRANSACTION-INCOMPLETE")
    ]
    if unsafe_diagnostics:
        raise RuntimeError("Project state is unsafe to begin: %s" % json.dumps(unsafe_diagnostics, sort_keys=True))
    now = datetime.now(timezone.utc)
    payload = {
        "owner": owner,
        "task_id": task["id"],
        "created_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=ttl_minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    try:
        _write_lock_exclusive(_lock_path(root), payload)
    except FileExistsError:
        current = read_json(_lock_path(root))
        raise RuntimeError("SVK Next is already locked by %s for task %s." % (current.get("owner"), current.get("task_id")))
    return {"status": "begun", "lock": payload, "task": task}


def _validate_evidence_payload(value):
    if not isinstance(value, dict):
        raise ValueError("Evidence must be a JSON object.")
    missing = [key for key in ("summary", "commands", "artifacts", "result") if key not in value]
    if missing:
        raise ValueError("Evidence is missing fields: %s" % ", ".join(missing))
    if value.get("result") not in ("pass", "fail", "partial"):
        raise ValueError("Evidence result must be pass, fail, or partial.")
    if not isinstance(value.get("commands"), list) or not isinstance(value.get("artifacts"), list):
        raise ValueError("Evidence commands and artifacts must be arrays.")


def _render_task_documents(root, profile, state):
    documents = render_documents(profile, state)
    for relative in ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md"):
        atomic_write(root / relative, documents[relative])


def next_finish(project_root, owner, task_id, evidence_path):
    root = safe_project_root(project_root)
    lock_path = _lock_path(root)
    lock = read_json(lock_path)
    if lock.get("owner") != owner or lock.get("task_id") != task_id:
        raise PermissionError("Lock owner/task does not match this finish request.")
    evidence = read_json(evidence_path)
    _validate_evidence_payload(evidence)
    if evidence.get("result") != "pass":
        raise ValueError("Only passing evidence can finish a task; use block for unresolved work.")

    state_path = root / STATE_FILE
    profile = read_json(root / PROFILE_FILE)
    state_before = state_path.read_text(encoding="utf-8")
    evidence_target = root / EVIDENCE_FILE
    evidence_before = evidence_target.read_text(encoding="utf-8") if evidence_target.exists() else ""
    task_docs = {
        path: (root / path).read_text(encoding="utf-8")
        for path in ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md")
    }
    state = json.loads(state_before)
    tasks = state.get("tasks", [])
    task = next((item for item in tasks if item.get("id") == task_id), None)
    if task is None or task.get("status") not in ("in_progress", "blocked"):
        raise ValueError("Task is not active: %s" % task_id)
    transaction_id = uuid.uuid4().hex
    transaction_path = root / ".svk/transactions" / ("next-%s.json" % transaction_id)
    write_json(transaction_path, {"id": transaction_id, "operation": "finish", "task_id": task_id, "status": "in_progress", "recorded_at": utc_now()})
    try:
        task["status"] = "done"
        task.pop("blocker", None)
        completed = {item["id"] for item in tasks if item.get("status") == "done"}
        promoted = None
        for candidate in tasks:
            if candidate.get("status") == "pending" and set(candidate.get("depends_on", [])).issubset(completed):
                candidate["status"] = "in_progress"
                promoted = candidate
                break
        if task_id == "1.1.2":
            state["charter"]["accepted"] = True
            state["stage"] = "execution"
        state["next_action"] = next_action(tasks)
        state["updated_at"] = utc_now()
        write_json(state_path, state)
        record = dict(evidence)
        record.update({"task_id": task_id, "owner": owner, "recorded_at": utc_now()})
        append_json_line(evidence_target, record)
        _render_task_documents(root, profile, state)
        write_json(transaction_path, {"id": transaction_id, "operation": "finish", "task_id": task_id, "status": "committed", "recorded_at": utc_now()})
        lock_path.unlink()
        result = check_project(root)
        if result["result"] not in ("PASS", "WARN"):
            raise ValueError("Post-finish semantic gate failed: %s" % json.dumps(result, sort_keys=True))
        return {"status": "finished", "completed": task_id, "promoted": promoted, "check": result}
    except Exception:
        atomic_write(state_path, state_before)
        atomic_write(evidence_target, evidence_before)
        for path, content in task_docs.items():
            atomic_write(root / path, content)
        write_json(transaction_path, {"id": transaction_id, "operation": "finish", "task_id": task_id, "status": "rolled_back", "recorded_at": utc_now()})
        if not lock_path.exists():
            _write_lock_exclusive(lock_path, lock)
        raise


def next_block(project_root, owner, task_id, reason):
    root = safe_project_root(project_root)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("A specific non-empty blocker reason is required.")
    lock_path = _lock_path(root)
    lock = read_json(lock_path)
    if lock.get("owner") != owner or lock.get("task_id") != task_id:
        raise PermissionError("Lock owner/task does not match this block request.")
    state_path = root / STATE_FILE
    profile = read_json(root / PROFILE_FILE)
    state_before = state_path.read_text(encoding="utf-8")
    task_docs = {
        path: (root / path).read_text(encoding="utf-8")
        for path in ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md")
    }
    state = json.loads(state_before)
    task = next((item for item in state.get("tasks", []) if item.get("id") == task_id), None)
    if task is None:
        raise ValueError("Unknown task: %s" % task_id)
    transaction_id = uuid.uuid4().hex
    transaction_path = root / ".svk/transactions" / ("next-%s.json" % transaction_id)
    write_json(transaction_path, {"id": transaction_id, "operation": "block", "task_id": task_id, "status": "in_progress", "recorded_at": utc_now()})
    try:
        task["status"] = "blocked"
        task["blocker"] = reason.strip()
        state["next_action"] = {"task_id": task_id, "instruction": task["title"]}
        state["updated_at"] = utc_now()
        write_json(state_path, state)
        _render_task_documents(root, profile, state)
        write_json(transaction_path, {"id": transaction_id, "operation": "block", "task_id": task_id, "status": "committed", "recorded_at": utc_now()})
        lock_path.unlink()
        result = check_project(root)
        if result["result"] not in ("BLOCKED", "WARN"):
            raise ValueError("Post-block semantic gate failed: %s" % json.dumps(result, sort_keys=True))
        return {"result": result["result"], "status": "blocked", "task_id": task_id, "reason": reason.strip(), "check": result}
    except Exception:
        atomic_write(state_path, state_before)
        for path, content in task_docs.items():
            atomic_write(root / path, content)
        write_json(transaction_path, {"id": transaction_id, "operation": "block", "task_id": task_id, "status": "rolled_back", "recorded_at": utc_now()})
        if not lock_path.exists():
            _write_lock_exclusive(lock_path, lock)
        raise


def next_clear_lock(project_root, owner=None, force=False):
    root = safe_project_root(project_root)
    path = _lock_path(root)
    if not path.exists():
        return {"status": "absent"}
    lock = read_json(path)
    if not force and lock.get("owner") != owner:
        raise PermissionError("Only the lock owner may clear it without --force.")
    path.unlink()
    return {"status": "cleared", "lock": lock}
