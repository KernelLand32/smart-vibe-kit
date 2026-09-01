"""Transactional, harness-neutral project operations for SVK 2.1."""

from __future__ import print_function

import json
import os
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .constants import (
    EVIDENCE_INDEX_FILE,
    GOVERNANCE_FILE,
    INSTALL_FILE,
    INTERVIEW_FILE,
    LOCK_FILE,
    PLAN_FILE,
    PROFILE_FILE,
    SCHEMA_VERSION,
    STATE_FILE,
    TRANSITION_LOCK_FILE,
    VERIFIERS_FILE,
    VERSION,
)
from .evidence import add_attestation, initial_index, load_receipt, receipt_fresh, run_verifier
from .governance import build_governance
from .interview import final_session, session_path
from .plan import build_plan
from .profile import build_profile
from .render import build_state, next_action, render_documents
from .util import (
    atomic_write,
    copy_tree_files,
    read_json,
    remove_empty_parents,
    safe_project_root,
    unique_sibling,
    utc_now,
    write_json,
    write_json_exclusive,
)
from .verify import check_project


INTERVIEW_QUESTIONS = (
    "What should this project accomplish, and who needs it?",
    "Which observable outcomes prove the first useful version works?",
    "What is explicitly outside scope?",
    "Is it user-facing, does it include a UI, or will it be deployed?",
    "Which platforms and external integrations must it support?",
    "Will it handle secrets, sensitive data, money, safety, or regulated activity?",
    "Which claims require current research or primary-source citations?",
    "What constraints, risks, and human approval points cannot be negotiated?",
    "What deliverables, bounded tasks, dependencies, artifacts, and verifiers form the approved plan?",
)

GREENFIELD_METADATA = {".git", ".gitignore", ".gitattributes", ".editorconfig", "LICENSE", "README.md"}
GENERATED_DOCUMENTS = ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md")


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


def _transaction(operation, status, before_revision, after_revision, task_id=None, details=None):
    value = {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "id": uuid.uuid4().hex,
        "operation": operation,
        "status": status,
        "recorded_at": utc_now(),
        "before_revision": before_revision,
        "after_revision": after_revision,
    }
    if task_id is not None:
        value["task_id"] = task_id
    if details is not None:
        value["details"] = details
    return value


def _write_stage(stage, target_root, answers, charter_accepted):
    profile = build_profile(answers)
    plan, verifiers = build_plan(profile, answers)
    state = build_state(profile, plan, charter_accepted=charter_accepted)
    documents = render_documents(profile, state)
    interview = final_session(target_root, answers)
    # Store a portable project identity, not a machine-specific absolute path.
    interview["target"] = profile["slug"]
    write_json(stage / PROFILE_FILE, profile)
    write_json(stage / PLAN_FILE, plan)
    write_json(stage / VERIFIERS_FILE, verifiers)
    write_json(stage / STATE_FILE, state)
    write_json(stage / INTERVIEW_FILE, interview)
    write_json(stage / EVIDENCE_INDEX_FILE, initial_index(profile, charter_accepted=charter_accepted))
    write_json(
        stage / INSTALL_FILE,
        {"schema_version": SCHEMA_VERSION, "owner": "smart-vibe-kit", "version": VERSION, "created_at": utc_now()},
    )
    for relative, content in documents.items():
        atomic_write(stage / relative, content)
    transaction = _transaction("scaffold", "committed", 0, state["state_revision"])
    write_json(stage / ".svk/transactions" / ("scaffold-%s.json" % transaction["id"]), transaction)
    build_governance(stage, documents.keys())
    return profile, plan, state, documents


def scaffold(project_root, answers, charter_accepted=False):
    root = safe_project_root(project_root)
    classification = classify_project_root(root)
    if classification in ("existing-svk", "partial-svk", "existing-project"):
        raise FileExistsError("Interview requires a new or greenfield folder; classified %s: %s" % (classification, root))
    root.parent.mkdir(parents=True, exist_ok=True)
    stage = unique_sibling(root, "svk-21-stage")
    stage.mkdir(parents=False, exist_ok=False)
    marker = stage / ".svk-stage-owner.json"
    write_json(marker, {"owner": "smart-vibe-kit", "version": VERSION, "target": str(root)})
    root_created = False
    created = []
    created_directories = []
    try:
        profile, plan, state, _ = _write_stage(stage, root, answers, charter_accepted)
        marker.unlink()
        staged = check_project(stage)
        if staged["result"] != "PASS":
            raise ValueError("Generated scaffold failed its staged semantic gate: %s" % json.dumps(staged, sort_keys=True))
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
        result = check_project(root)
        if result["result"] != "PASS":
            raise ValueError("Committed scaffold failed its semantic gate: %s" % json.dumps(result, sort_keys=True))
        checkpoint = session_path(root)
        if checkpoint.exists():
            checkpoint.unlink()
        return {
            "root": str(root),
            "workspace_classification": classification,
            "profile": profile,
            "plan": plan,
            "state": state,
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
            shutil.rmtree(str(stage))


def refresh(project_root, scope="governed"):
    root = safe_project_root(project_root)
    result = check_project(root, scope=scope)
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
        "state_revision": state.get("state_revision"),
        "active_task": active[0] if len(active) == 1 else None,
        "blocker": blocker,
        "next_action": state.get("next_action"),
        "check": result,
    }


def _transition_path(root):
    return Path(root) / TRANSITION_LOCK_FILE


@contextmanager
def _transition(root, owner, operation):
    now = datetime.now(timezone.utc)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "owner": owner,
        "operation": operation,
        "created_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    path = _transition_path(root)
    try:
        write_json_exclusive(path, payload)
    except FileExistsError:
        raise RuntimeError("Another SVK state transition is already in progress.")
    try:
        yield
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _lock_path(root):
    return Path(root) / LOCK_FILE


def _render_generated(root, profile, state):
    documents = render_documents(profile, state)
    for relative in GENERATED_DOCUMENTS:
        atomic_write(Path(root) / relative, documents[relative])


def _text_snapshot(root, relatives):
    return {relative: (Path(root) / relative).read_text(encoding="utf-8") for relative in relatives}


def _restore_text_snapshot(root, snapshot):
    for relative, content in snapshot.items():
        atomic_write(Path(root) / relative, content)


def _load_active(root, task_id=None):
    state = read_json(Path(root) / STATE_FILE)
    active = [task for task in state.get("tasks", []) if task.get("status") in ("in_progress", "blocked")]
    if len(active) != 1:
        raise ValueError("Exactly one task must be active.")
    if task_id is not None and active[0]["id"] != task_id:
        raise ValueError("Requested task is not the active task: %s" % task_id)
    return state, active[0]


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
    return {"result": check["result"], "status": task.get("status"), "task": task, "instruction": action["instruction"], "check": check}


def next_begin(project_root, owner, allow_human_gate=False, ttl_minutes=120, human_actor=None, human_reason=None):
    root = safe_project_root(project_root)
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("A non-empty lease owner is required.")
    if ttl_minutes < 1 or ttl_minutes > 10080:
        raise ValueError("Lease TTL must be between 1 and 10080 minutes.")
    with _transition(root, owner.strip(), "begin"):
        checked = check_project(root, ignore_transition=True)
        unsafe = [item for item in checked["diagnostics"] if item["level"] == "ERROR" or item["code"] in ("SVK-TRANSACTION-INCOMPLETE", "SVK-EVIDENCE-ORPHAN")]
        if unsafe:
            raise RuntimeError("Project is unsafe to begin: %s" % json.dumps(unsafe, sort_keys=True))
        if _lock_path(root).exists():
            current = read_json(_lock_path(root))
            raise RuntimeError("SVK Next is already leased by %s for task %s." % (current.get("owner"), current.get("task_id")))
        state, task = _load_active(root)
        state_before = (root / STATE_FILE).read_text(encoding="utf-8")
        evidence_before = (root / EVIDENCE_INDEX_FILE).read_text(encoding="utf-8")
        generated_before = _text_snapshot(root, GENERATED_DOCUMENTS)
        try:
            if task.get("status") == "blocked":
                task["status"] = "in_progress"
                task.pop("blocker", None)
            if task.get("human_gate"):
                if not allow_human_gate:
                    raise PermissionError("Task %s is a human gate; explicit human attestation is required." % task["id"])
                if not isinstance(human_actor, str) or not human_actor.strip() or not isinstance(human_reason, str) or not human_reason.strip():
                    raise ValueError("Human-gate begin requires non-empty human_actor and human_reason values.")
                authorization = {
                    "task_id": task["id"], "actor": human_actor.strip(), "reason": human_reason.strip(),
                    "recorded_at": utc_now(), "kind": "cooperative-human-attestation",
                }
                state["authorizations"].append(authorization)
                add_attestation(root, task["id"], human_actor.strip(), human_reason.strip(), task.get("expected_artifacts", []))
            state["state_revision"] += 1
            state["updated_at"] = utc_now()
            write_json(root / STATE_FILE, state)
            _render_generated(root, read_json(root / PROFILE_FILE), state)
            now = datetime.now(timezone.utc)
            lease = {
                "schema_version": SCHEMA_VERSION, "kit_version": VERSION, "owner": owner.strip(),
                "task_id": task["id"], "state_revision": state["state_revision"],
                "created_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "expires_at": (now + timedelta(minutes=ttl_minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            }
            write_json_exclusive(_lock_path(root), lease)
            return {"status": "begun", "lease": lease, "task": task}
        except Exception:
            atomic_write(root / STATE_FILE, state_before)
            atomic_write(root / EVIDENCE_INDEX_FILE, evidence_before)
            _restore_text_snapshot(root, generated_before)
            try:
                _lock_path(root).unlink()
            except FileNotFoundError:
                pass
            raise


def verify_task(project_root, owner, task_id, verifier_id):
    root = safe_project_root(project_root)
    lease = read_json(_lock_path(root))
    state, task = _load_active(root, task_id)
    if lease.get("owner") != owner or lease.get("task_id") != task_id or lease.get("state_revision") != state.get("state_revision"):
        raise PermissionError("Lease owner, task, or state revision does not match this verifier request.")
    verifier_file = read_json(root / VERIFIERS_FILE)
    definition = verifier_file.get("verifiers", {}).get(verifier_id)
    if definition is None:
        raise ValueError("Unknown verifier: %s" % verifier_id)
    if verifier_id not in task.get("required_verifiers", []):
        raise ValueError("Verifier %s is not required by task %s." % (verifier_id, task_id))
    return run_verifier(root, task, verifier_id, definition, owner)


def _validate_completion_receipts(root, task, receipt_ids):
    if not isinstance(receipt_ids, list) or len(receipt_ids) != len(set(receipt_ids)):
        raise ValueError("receipt_ids must be a unique JSON array.")
    receipts = [load_receipt(root, receipt_id) for receipt_id in receipt_ids]
    for verifier_id in task.get("required_verifiers", []):
        matches = [receipt for receipt in receipts if receipt.get("task_id") == task["id"] and receipt.get("verifier_id") == verifier_id and receipt.get("result") == "pass"]
        if not matches:
            raise ValueError("Task %s lacks a passing receipt for %s." % (task["id"], verifier_id))
        if not any(receipt_fresh(root, task, receipt) for receipt in matches):
            raise ValueError("Task %s receipt for %s is stale." % (task["id"], verifier_id))


def _promote(state):
    completed = {task["id"] for task in state["tasks"] if task["status"] in ("done", "superseded")}
    for candidate in state["tasks"]:
        if candidate["status"] == "pending" and set(candidate["depends_on"]).issubset(completed):
            candidate["status"] = "in_progress"
            return candidate
    return None


def next_finish(project_root, owner, task_id, receipt_ids, note=None):
    root = safe_project_root(project_root)
    with _transition(root, owner, "finish"):
        checked = check_project(root, ignore_transition=True)
        unsafe = [item for item in checked["diagnostics"] if item["level"] == "ERROR" or item["code"] in ("SVK-TRANSACTION-INCOMPLETE", "SVK-EVIDENCE-ORPHAN")]
        if unsafe:
            raise RuntimeError("Project is unsafe to finish: %s" % json.dumps(unsafe, sort_keys=True))
        lease = read_json(_lock_path(root))
        state, task = _load_active(root, task_id)
        if lease.get("owner") != owner or lease.get("task_id") != task_id or lease.get("state_revision") != state.get("state_revision"):
            raise PermissionError("Lease owner, task, or state revision does not match this finish request.")
        _validate_completion_receipts(root, task, receipt_ids)
        if task.get("human_gate") and not any(item.get("task_id") == task_id for item in state.get("authorizations", [])):
            raise PermissionError("Human-gate completion requires its recorded cooperative attestation.")
        before_revision = state["state_revision"]
        state_before = (root / STATE_FILE).read_text(encoding="utf-8")
        generated_before = _text_snapshot(root, GENERATED_DOCUMENTS)
        transaction = _transaction("finish", "in_progress", before_revision, before_revision + 1, task_id, {"receipt_ids": list(receipt_ids), "note": note, "lease": lease})
        transaction_path = root / ".svk/transactions" / ("next-%s.json" % transaction["id"])
        snapshot_path = transaction_path.with_suffix(".state-snapshot")
        atomic_write(snapshot_path, state_before)
        write_json(transaction_path, transaction)
        try:
            task["status"] = "done"
            task.pop("blocker", None)
            task["completion_receipts"] = list(receipt_ids)
            if task_id == "1.1.2":
                state["charter"]["accepted"] = True
                state["stage"] = "execution"
            promoted = _promote(state)
            state["next_action"] = next_action(state["tasks"])
            if state["next_action"] is None:
                state["stage"] = "complete"
            state["state_revision"] += 1
            state["updated_at"] = utc_now()
            write_json(root / STATE_FILE, state)
            _render_generated(root, read_json(root / PROFILE_FILE), state)
            transaction["status"] = "committed"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            snapshot_path.unlink()
            _lock_path(root).unlink()
            result = check_project(root, ignore_transition=True)
            if result["result"] not in ("PASS", "WARN"):
                raise ValueError("Post-finish semantic gate failed: %s" % json.dumps(result, sort_keys=True))
            return {"status": "finished", "completed": task_id, "promoted": promoted, "check": result}
        except Exception:
            atomic_write(root / STATE_FILE, state_before)
            _restore_text_snapshot(root, generated_before)
            if not _lock_path(root).exists():
                write_json_exclusive(_lock_path(root), lease)
            transaction["status"] = "rolled_back"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            try:
                snapshot_path.unlink()
            except FileNotFoundError:
                pass
            raise


def next_block(project_root, owner, task_id, reason):
    root = safe_project_root(project_root)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("A specific non-empty blocker reason is required.")
    with _transition(root, owner, "block"):
        lease = read_json(_lock_path(root))
        state, task = _load_active(root, task_id)
        if lease.get("owner") != owner or lease.get("task_id") != task_id or lease.get("state_revision") != state.get("state_revision"):
            raise PermissionError("Lease owner, task, or state revision does not match this block request.")
        before_revision = state["state_revision"]
        state_before = (root / STATE_FILE).read_text(encoding="utf-8")
        generated_before = _text_snapshot(root, GENERATED_DOCUMENTS)
        transaction = _transaction("block", "in_progress", before_revision, before_revision + 1, task_id, {"reason": reason.strip(), "lease": lease})
        transaction_path = root / ".svk/transactions" / ("next-%s.json" % transaction["id"])
        snapshot_path = transaction_path.with_suffix(".state-snapshot")
        atomic_write(snapshot_path, state_before)
        write_json(transaction_path, transaction)
        try:
            task["status"] = "blocked"
            task["blocker"] = reason.strip()
            state["next_action"] = {"task_id": task_id, "instruction": task["title"]}
            state["state_revision"] += 1
            state["updated_at"] = utc_now()
            write_json(root / STATE_FILE, state)
            _render_generated(root, read_json(root / PROFILE_FILE), state)
            transaction["status"] = "committed"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            snapshot_path.unlink()
            _lock_path(root).unlink()
            result = check_project(root, ignore_transition=True)
            if result["result"] not in ("BLOCKED", "WARN"):
                raise ValueError("Post-block semantic gate failed: %s" % json.dumps(result, sort_keys=True))
            return {"result": result["result"], "status": "blocked", "task_id": task_id, "reason": reason.strip(), "check": result}
        except Exception:
            atomic_write(root / STATE_FILE, state_before)
            _restore_text_snapshot(root, generated_before)
            if not _lock_path(root).exists():
                write_json_exclusive(_lock_path(root), lease)
            transaction["status"] = "rolled_back"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            try:
                snapshot_path.unlink()
            except FileNotFoundError:
                pass
            raise


def next_clear_lock(project_root, owner=None, force=False):
    root = safe_project_root(project_root)
    with _transition(root, owner or "recovery", "clear-lock"):
        path = _lock_path(root)
        if not path.exists():
            return {"status": "absent"}
        lease = read_json(path)
        if not force and lease.get("owner") != owner:
            raise PermissionError("Only the lease owner may clear it without --force.")
        path.unlink()
        return {"status": "cleared", "lease": lease}
