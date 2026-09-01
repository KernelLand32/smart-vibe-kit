"""Deterministic, reversible SVK 2.0 to 2.1 project migration."""

from __future__ import print_function

import copy
import json
import shutil
import uuid
from pathlib import Path

from .constants import EVIDENCE_INDEX_FILE, INSTALL_FILE, INTERVIEW_FILE, PLAN_FILE, PROFILE_FILE, SCHEMA_VERSION, STATE_FILE, VERIFIERS_FILE, VERSION
from .evidence import initial_index
from .governance import build_governance
from .plan import DEFAULT_SIZING_POLICY, validate_plan, validate_verifiers
from .profile import build_profile
from .render import build_state, next_action, render_documents
from .util import atomic_write, copy_tree_files, read_json, safe_project_root, utc_now, write_json
from .verify import check_project


GENERATED = ("AGENTS.md", "docs/tasks.md", "docs/adr/0001-project-charter.md")
PROFILE_FIELDS_20 = {"schema_version", "svk_version", "title", "slug", "idea", "goals", "non_goals", "constraints", "platforms", "integrations", "research_tier", "risk", "team_size", "signals", "profile", "modules", "expected_document_count"}
STATE_FIELDS_20 = {"schema_version", "kit_version", "project", "stage", "charter", "tasks", "next_action", "authorizations", "updated_at"}
TASK_FIELDS_20 = {"id", "title", "status", "depends_on", "human_gate", "artifact", "verification", "blocker"}


def inspect_migration(project_root):
    root = safe_project_root(project_root)
    profile = read_json(root / PROFILE_FILE)
    state = read_json(root / STATE_FILE)
    if profile.get("svk_version") == VERSION and state.get("kit_version") == VERSION:
        return {"result": "PASS", "status": "already-current", "from": VERSION, "to": VERSION, "unknown_fields": []}
    unknown = []
    unknown.extend("project.json/%s" % name for name in sorted(set(profile) - PROFILE_FIELDS_20))
    unknown.extend("state.json/%s" % name for name in sorted(set(state) - STATE_FIELDS_20))
    for index, task in enumerate(state.get("tasks", [])):
        unknown.extend("state.json/tasks/%d/%s" % (index, name) for name in sorted(set(task) - TASK_FIELDS_20))
    valid_20 = profile.get("svk_version") == "2.0.0" and state.get("kit_version") == "2.0.0"
    return {
        "result": "ERROR" if not valid_20 or unknown else "PASS",
        "status": "ready" if valid_20 and not unknown else "blocked",
        "from": profile.get("svk_version"), "to": VERSION,
        "unknown_fields": unknown,
        "legacy_manifest": (root / ".svk/baselines/manifest.json").is_file(),
        "legacy_evidence": (root / ".svk/evidence.jsonl").is_file(),
    }


def _safe_old_artifact(root, value):
    if not isinstance(value, str) or not value.strip():
        return []
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or not (root / candidate).exists():
        return []
    return [candidate.as_posix()]


def _converted_plan(root, profile, old_state):
    goals = [{"id": "goal-%d" % (index + 1), "title": title} for index, title in enumerate(profile["goals"])]
    old_plan_tasks = [task for task in old_state.get("tasks", []) if str(task.get("id", "")).startswith("3.")]
    deliverables = []
    tasks = []
    for index, goal in enumerate(goals):
        old = old_plan_tasks[index] if index < len(old_plan_tasks) else None
        identifier = "migrated-goal-%d" % (index + 1)
        acceptance = [old.get("verification")] if old and old.get("verification") else ["The migrated goal has observable passing evidence."]
        deliverables.append({"id": identifier, "goal_id": goal["id"], "title": goal["title"], "acceptance": acceptance})
        task_id = old.get("id") if old else "3.%d.1" % (index + 1)
        dependencies = [item for item in (old.get("depends_on", []) if old else []) if str(item).startswith("3.")]
        artifacts = _safe_old_artifact(root, old.get("artifact") if old else None)
        task = {
            "id": task_id, "kind": "implementation", "title": old.get("title") if old else "Implement and verify: %s" % goal["title"],
            "goal_id": goal["id"], "deliverable_id": identifier, "depends_on": dependencies,
            "dependency_rationale": {item: "Preserved from the SVK 2.0 task graph." for item in dependencies},
            "human_gate": bool(old.get("human_gate", False)) if old else False, "acceptance": acceptance,
            "expected_artifacts": artifacts, "scope_hints": artifacts or ["AGENTS.md"],
            "required_verifiers": ["svk-governed"], "risk": profile["risk"],
            "size_signals": {"subsystems": 1, "acceptance_items": len(acceptance), "verifier_count": 1, "scope_hints": len(artifacts or ["AGENTS.md"])},
        }
        if not artifacts:
            task["no_artifact_reason"] = "SVK 2.0 stored a narrative artifact label; migration preserves the task without inventing a path."
        tasks.append(task)
    plan = {
        "schema_version": SCHEMA_VERSION, "kit_version": VERSION, "project": profile["slug"],
        "review_status": "approved", "reviewer": "SVK 2.0 migration", "reviewed_at": utc_now(),
        "review_reason": "A human explicitly approved deterministic preservation of the 2.0 task graph.",
        "goals": goals, "deliverables": deliverables, "tasks": tasks,
        "release_verifiers": ["svk-governed"], "sizing_policy": copy.deepcopy(DEFAULT_SIZING_POLICY),
    }
    verifiers = {"schema_version": SCHEMA_VERSION, "kit_version": VERSION, "verifiers": validate_verifiers({"svk-governed": {"kind": "builtin", "check": "governed"}})}
    validate_plan(plan, profile, verifiers["verifiers"].keys())
    return plan, verifiers


def plan_migration(project_root):
    root = safe_project_root(project_root)
    inspected = inspect_migration(root)
    if inspected["status"] == "already-current":
        return {"result": "PASS", "status": "no-op", "changes": [], "decisions": []}
    if inspected["result"] != "PASS":
        return {"result": "ERROR", "status": "blocked", "changes": [], "decisions": ["Resolve unknown fields before migration."], "inspect": inspected}
    profile20 = read_json(root / PROFILE_FILE)
    state20 = read_json(root / STATE_FILE)
    answers = {key: profile20[key] for key in ("title", "slug", "idea", "goals", "non_goals", "constraints", "platforms", "integrations", "research_tier", "risk", "team_size")}
    answers.update(profile20.get("signals", {}))
    profile = build_profile(answers)
    plan, _ = _converted_plan(root, profile, state20)
    return {
        "result": "PASS", "status": "approval-required", "from": "2.0.0", "to": VERSION,
        "changes": [
            {"action": "replace", "path": ".svk", "preservation": "full sibling backup"},
            *({"action": "replace", "path": path, "preservation": "full sibling backup"} for path in GENERATED),
            {"action": "preserve", "path": "all other project files", "preservation": "current bytes and governed digest"},
        ],
        "decisions": ["Human approval is required before apply.", "2.0 completions become legacy_completion records and emit WARN until re-verified."],
        "proposed_plan": plan,
    }


def _prepare_stage(root, stage):
    profile20 = read_json(root / PROFILE_FILE)
    state20 = read_json(root / STATE_FILE)
    answers = {key: profile20[key] for key in ("title", "slug", "idea", "goals", "non_goals", "constraints", "platforms", "integrations", "research_tier", "risk", "team_size")}
    answers.update(profile20.get("signals", {}))
    profile = build_profile(answers)
    plan, verifiers = _converted_plan(root, profile, state20)
    charter_accepted = bool(state20.get("charter", {}).get("accepted"))
    state = build_state(profile, plan, charter_accepted=charter_accepted)
    old_by_id = {task.get("id"): task for task in state20.get("tasks", [])}
    for task in state["tasks"]:
        old = old_by_id.get(task["id"])
        if not old:
            continue
        if old.get("status") == "done":
            task["status"] = "done"
            if task["id"] != "1.1.1":
                task["legacy_completion"] = True
        elif old.get("status") in ("in_progress", "blocked", "pending"):
            task["status"] = old["status"]
            if old.get("blocker"):
                task["blocker"] = old["blocker"]
    active = [task for task in state["tasks"] if task["status"] in ("in_progress", "blocked")]
    if len(active) != 1:
        for task in state["tasks"]:
            if task["status"] == "in_progress":
                task["status"] = "pending"
        completed = {task["id"] for task in state["tasks"] if task["status"] in ("done", "superseded")}
        candidate = next((task for task in state["tasks"] if task["status"] == "pending" and set(task["depends_on"]).issubset(completed)), None)
        if candidate:
            candidate["status"] = "in_progress"
    state["next_action"] = next_action(state["tasks"])
    state["stage"] = "complete" if state["next_action"] is None else ("execution" if charter_accepted else "charter")
    documents = render_documents(profile, state)
    write_json(stage / PROFILE_FILE, profile); write_json(stage / PLAN_FILE, plan); write_json(stage / VERIFIERS_FILE, verifiers); write_json(stage / STATE_FILE, state)
    session = {"schema_version": SCHEMA_VERSION, "kit_version": VERSION, "session_id": uuid.uuid4().hex, "target": profile["slug"], "idea": profile["idea"], "status": "scaffolded", "sections": {"review": {"migration": "2.0-to-2.1"}}, "unresolved_questions": [], "proposal_sha256": None, "created_at": utc_now(), "updated_at": utc_now()}
    write_json(stage / INTERVIEW_FILE, session)
    evidence = initial_index(profile, charter_accepted=charter_accepted)
    write_json(stage / EVIDENCE_INDEX_FILE, evidence)
    write_json(stage / INSTALL_FILE, {"schema_version": SCHEMA_VERSION, "owner": "smart-vibe-kit", "version": VERSION, "created_at": utc_now()})
    legacy_dir = stage / ".svk/migrations/2.0"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    for source_name, target_name in ((".svk/baselines/manifest.json", "manifest.json"), (".svk/evidence.jsonl", "evidence.jsonl")):
        source = root / source_name
        if source.is_file():
            shutil.copy2(str(source), str(legacy_dir / target_name))
    for relative, content in documents.items():
        source = root / relative
        if relative not in GENERATED and source.is_file():
            content = source.read_text(encoding="utf-8")
        atomic_write(stage / relative, content)
    transaction = {"schema_version": SCHEMA_VERSION, "kit_version": VERSION, "id": uuid.uuid4().hex, "operation": "migrate-2.0-to-2.1", "status": "committed", "recorded_at": utc_now(), "before_revision": 0, "after_revision": state["state_revision"], "details": {"legacy_manifest": ".svk/migrations/2.0/manifest.json", "legacy_evidence": ".svk/migrations/2.0/evidence.jsonl"}}
    write_json(stage / ".svk/transactions" / ("migration-%s.json" % transaction["id"]), transaction)
    build_governance(stage, documents.keys())
    return state


def apply_migration(project_root, approve=False):
    if not approve:
        raise PermissionError("Migration apply requires explicit --approve human permission.")
    root = safe_project_root(project_root)
    planned = plan_migration(root)
    if planned["status"] == "no-op":
        return planned
    if planned["result"] != "PASS":
        raise ValueError("Migration preflight is blocked: %s" % json.dumps(planned, sort_keys=True))
    migration_id = uuid.uuid4().hex
    stage = root.parent / (".%s.svk-migration-stage-%s" % (root.name, migration_id))
    backup = root.parent / (".%s.svk-migration-backup-%s" % (root.name, migration_id))
    stage.mkdir(); backup.mkdir()
    moved = []
    installed = []
    try:
        _prepare_stage(root, stage)
        staged_check = check_project(stage)
        if staged_check["result"] not in ("PASS", "WARN"):
            raise ValueError("Staged migration failed: %s" % json.dumps(staged_check, sort_keys=True))
        for relative in (".svk",) + GENERATED:
            current = root / relative
            saved = backup / relative
            if current.exists():
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(saved)); moved.append(relative)
            source = stage / relative
            current.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(current)); installed.append(relative)
        write_json(backup / "migration-receipt.json", {"owner": "smart-vibe-kit", "migration": "2.0-to-2.1", "id": migration_id, "target": str(root), "moved": list(moved), "installed": list(installed), "created_at": utc_now()})
        result = check_project(root)
        if result["result"] not in ("PASS", "WARN"):
            raise ValueError("Committed migration failed: %s" % json.dumps(result, sort_keys=True))
        return {"result": result["result"], "status": "migrated", "backup": str(backup), "check": result}
    except Exception:
        for relative in reversed(installed):
            current = root / relative
            if current.is_dir(): shutil.rmtree(str(current))
            elif current.exists(): current.unlink()
        for relative in reversed(moved):
            saved = backup / relative
            current = root / relative
            if saved.exists():
                current.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(saved), str(current))
        if backup.exists():
            shutil.rmtree(str(backup))
        raise
    finally:
        if stage.exists(): shutil.rmtree(str(stage))


def rollback_migration(project_root, backup_path, approve=False):
    if not approve:
        raise PermissionError("Migration rollback requires explicit --approve human permission.")
    root = safe_project_root(project_root)
    backup = Path(backup_path).resolve()
    receipt = read_json(backup / "migration-receipt.json")
    if backup.parent != root.parent or receipt.get("target") != str(root) or receipt.get("owner") != "smart-vibe-kit":
        raise ValueError("Backup does not belong to this migration target.")
    for relative in receipt["installed"]:
        current = root / relative
        if current.is_dir(): shutil.rmtree(str(current))
        elif current.exists(): current.unlink()
    for relative in receipt["moved"]:
        saved = backup / relative; current = root / relative
        current.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(saved), str(current))
    return {"status": "rolled-back", "from": VERSION, "to": "2.0.0", "backup": str(backup)}
