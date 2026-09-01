"""Narrow, auditable pending-plan edits for SVK 2.1."""

from __future__ import print_function

import copy
import json
import uuid
from pathlib import Path

from .constants import LOCK_FILE, PLAN_FILE, PROFILE_FILE, STATE_FILE, VERIFIERS_FILE
from .operations import GENERATED_DOCUMENTS, _render_generated, _restore_text_snapshot, _text_snapshot, _transaction, _transition
from .plan import validate_plan
from .render import next_action
from .util import atomic_write, read_json, safe_project_root, utc_now, write_json
from .verify import check_project


def _pending(state, task_id):
    task = next((item for item in state["tasks"] if item.get("id") == task_id), None)
    if task is None or task.get("status") != "pending":
        raise ValueError("Plan edits may target only pending tasks: %s" % task_id)
    return task


def _apply_edit(plan, state, edit):
    if not isinstance(edit, dict) or edit.get("operation") not in ("insert", "add-dependency", "supersede", "split"):
        raise ValueError("Plan edit operation must be insert, add-dependency, supersede, or split.")
    operation = edit["operation"]
    planned = {task["id"]: task for task in plan["tasks"]}
    state_by_id = {task["id"]: task for task in state["tasks"]}
    if operation == "insert":
        task = copy.deepcopy(edit.get("task"))
        if not isinstance(task, dict) or task.get("id") in state_by_id:
            raise ValueError("Inserted task must be a new full task contract.")
        plan["tasks"].append(task)
        runtime_task = copy.deepcopy(task)
        runtime_task.update({"status": "pending", "completion_receipts": []})
        release_index = next(index for index, item in enumerate(state["tasks"]) if item["id"] == "4.1.1")
        state["tasks"].insert(release_index, runtime_task)
    elif operation == "add-dependency":
        task_id = edit.get("task_id")
        dependency = edit.get("dependency_id")
        rationale = edit.get("rationale")
        _pending(state, task_id)
        if task_id not in planned or dependency not in planned or not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("Dependency edit requires two planned task IDs and a rationale.")
        for task in (planned[task_id], state_by_id[task_id]):
            if dependency not in task["depends_on"]:
                task["depends_on"].append(dependency)
            task["dependency_rationale"][dependency] = rationale.strip()
    else:
        task_id = edit.get("task_id")
        _pending(state, task_id)
        if task_id not in planned:
            raise ValueError("Target is not an approved plan task: %s" % task_id)
        dependents = [task["id"] for task in plan["tasks"] if task_id in task.get("depends_on", [])]
        replacements = copy.deepcopy(edit.get("tasks", [])) if operation == "split" else []
        if operation == "supersede" and dependents:
            raise ValueError("Cannot supersede a referenced task without first editing its dependents: %s" % ", ".join(dependents))
        if operation == "split" and (not isinstance(replacements, list) or len(replacements) < 2):
            raise ValueError("Splitting requires at least two replacement task contracts.")
        plan["tasks"] = [task for task in plan["tasks"] if task["id"] != task_id]
        state_by_id[task_id]["status"] = "superseded"
        state_by_id[task_id]["supersedes"] = []
        if operation == "split":
            replacement_ids = [task.get("id") for task in replacements]
            if len(replacement_ids) != len(set(replacement_ids)) or any(identifier in state_by_id for identifier in replacement_ids):
                raise ValueError("Split replacement IDs must be unique and new.")
            plan["tasks"].extend(replacements)
            release_index = next(index for index, item in enumerate(state["tasks"]) if item["id"] == "4.1.1")
            for replacement in replacements:
                runtime_task = copy.deepcopy(replacement)
                runtime_task["supersedes"] = [task_id]
                runtime_task.update({"status": "pending", "completion_receipts": []})
                state["tasks"].insert(release_index, runtime_task)
                release_index += 1
            replacement = edit.get("replace_dependency_with") or replacement_ids[-1]
            if replacement not in replacement_ids:
                raise ValueError("replace_dependency_with must name one split replacement.")
            for task in plan["tasks"]:
                if task_id in task.get("depends_on", []):
                    position = task["depends_on"].index(task_id)
                    task["depends_on"][position] = replacement
                    task["dependency_rationale"][replacement] = task["dependency_rationale"].pop(task_id)
            for task in state["tasks"]:
                if task_id in task.get("depends_on", []) and task["id"] != "4.1.1":
                    position = task["depends_on"].index(task_id)
                    task["depends_on"][position] = replacement
                    task["dependency_rationale"][replacement] = task["dependency_rationale"].pop(task_id)


def apply_plan_edit(project_root, owner, edit, reviewer, reason, approve=False):
    if not approve:
        raise PermissionError("Plan mutation requires explicit --approve human review.")
    if not all(isinstance(value, str) and value.strip() for value in (owner, reviewer, reason)):
        raise ValueError("Plan edits require non-empty owner, reviewer, and reason values.")
    root = safe_project_root(project_root)
    with _transition(root, owner.strip(), "plan-edit"):
        if (root / LOCK_FILE).exists():
            raise RuntimeError("Plan edits are forbidden while a task lease exists.")
        checked = check_project(root, ignore_transition=True)
        if checked["result"] in ("ERROR", "BLOCKED"):
            raise RuntimeError("Project is not safe for a plan edit.")
        plan_path = root / PLAN_FILE
        state_path = root / STATE_FILE
        plan_before = plan_path.read_text(encoding="utf-8")
        state_before = state_path.read_text(encoding="utf-8")
        generated_before = _text_snapshot(root, GENERATED_DOCUMENTS)
        plan = json.loads(plan_before)
        state = json.loads(state_before)
        _apply_edit(plan, state, edit)
        plan["reviewer"] = reviewer.strip()
        plan["review_reason"] = reason.strip()
        plan["reviewed_at"] = utc_now()
        verifier_file = read_json(root / VERIFIERS_FILE)
        validate_plan(plan, read_json(root / PROFILE_FILE), verifier_file["verifiers"].keys())
        release = next(task for task in state["tasks"] if task["id"] == "4.1.1")
        release["depends_on"] = [task["id"] for task in plan["tasks"]]
        release["dependency_rationale"] = {task_id: "Release readiness requires every approved project task." for task_id in release["depends_on"]}
        release["required_verifiers"] = list(dict.fromkeys(["svk-governed"] + plan["release_verifiers"]))
        release["size_signals"]["verifier_count"] = len(release["required_verifiers"])
        state["state_revision"] += 1
        state["updated_at"] = utc_now()
        state["next_action"] = next_action(state["tasks"])
        transaction = _transaction("plan-edit", "in_progress", state["state_revision"] - 1, state["state_revision"], details={"edit": edit, "reviewer": reviewer.strip(), "reason": reason.strip()})
        transaction_path = root / ".svk/transactions" / ("plan-%s.json" % transaction["id"])
        write_json(transaction_path, transaction)
        try:
            write_json(plan_path, plan)
            write_json(state_path, state)
            _render_generated(root, read_json(root / PROFILE_FILE), state)
            transaction["status"] = "committed"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            result = check_project(root, ignore_transition=True)
            if result["result"] not in ("PASS", "WARN"):
                raise ValueError("Plan edit failed its semantic gate: %s" % json.dumps(result, sort_keys=True))
            return {"status": "committed", "operation": edit["operation"], "state_revision": state["state_revision"], "check": result}
        except Exception:
            atomic_write(plan_path, plan_before)
            atomic_write(state_path, state_before)
            _restore_text_snapshot(root, generated_before)
            transaction["status"] = "rolled_back"
            transaction["recorded_at"] = utc_now()
            write_json(transaction_path, transaction)
            raise
