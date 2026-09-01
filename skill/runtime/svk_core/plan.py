"""Structured plan and verifier contracts for SVK 2.1."""

from __future__ import print_function

import copy
import re

from .constants import SCHEMA_VERSION, TASK_ID_PATTERN, VERSION
from .util import utc_now


TASK_KINDS = ("research", "design", "implementation", "migration", "verification", "documentation")
DEFAULT_SIZING_POLICY = {
    "max_subsystems": 1,
    "max_acceptance_items": 5,
    "max_verifiers": 3,
    "max_scope_hints": 12,
}


def _strings(value, name, allow_empty=False):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError("%s must be an array of non-empty strings." % name)
    if not allow_empty and not value:
        raise ValueError("%s must not be empty." % name)
    return [item.strip() for item in value]


def validate_verifiers(verifiers):
    if not isinstance(verifiers, dict) or not verifiers:
        raise ValueError("verifiers must be a non-empty object.")
    normalized = {}
    for verifier_id, definition in sorted(verifiers.items()):
        if not isinstance(verifier_id, str) or not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", verifier_id):
            raise ValueError("Invalid verifier ID: %r" % verifier_id)
        if not isinstance(definition, dict):
            raise ValueError("Verifier %s must be an object." % verifier_id)
        allowed = {"kind", "argv", "cwd", "timeout_seconds", "expected_exit_codes", "artifacts", "environment", "check"}
        unknown = set(definition) - allowed
        if unknown:
            raise ValueError("Verifier %s has unknown fields: %s" % (verifier_id, ", ".join(sorted(unknown))))
        kind = definition.get("kind", "command")
        if kind == "builtin":
            if definition.get("check") != "governed":
                raise ValueError("Builtin verifier %s must use check=governed." % verifier_id)
            normalized[verifier_id] = {"kind": "builtin", "check": "governed"}
            continue
        if kind != "command":
            raise ValueError("Verifier %s kind must be command or builtin." % verifier_id)
        argv = _strings(definition.get("argv"), "verifier %s argv" % verifier_id)
        cwd = definition.get("cwd", ".")
        if not isinstance(cwd, str) or not cwd.strip():
            raise ValueError("Verifier %s cwd must be a non-empty relative path." % verifier_id)
        timeout = definition.get("timeout_seconds", 120)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
            raise ValueError("Verifier %s timeout_seconds must be between 1 and 3600." % verifier_id)
        exits = definition.get("expected_exit_codes", [0])
        if not isinstance(exits, list) or not exits or any(isinstance(item, bool) or not isinstance(item, int) for item in exits):
            raise ValueError("Verifier %s expected_exit_codes must be a non-empty integer array." % verifier_id)
        artifacts = _strings(definition.get("artifacts", []), "verifier %s artifacts" % verifier_id, allow_empty=True)
        environment = definition.get("environment", {"inherit": "safe-defaults", "set": {}})
        if not isinstance(environment, dict) or set(environment) - {"inherit", "set"}:
            raise ValueError("Verifier %s environment has an invalid shape." % verifier_id)
        if environment.get("inherit", "safe-defaults") not in ("safe-defaults", "none"):
            raise ValueError("Verifier %s environment.inherit must be safe-defaults or none." % verifier_id)
        values = environment.get("set", {})
        if not isinstance(values, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in values.items()):
            raise ValueError("Verifier %s environment.set must contain string values." % verifier_id)
        normalized[verifier_id] = {
            "kind": "command",
            "argv": argv,
            "cwd": cwd.strip(),
            "timeout_seconds": timeout,
            "expected_exit_codes": exits,
            "artifacts": artifacts,
            "environment": {"inherit": environment.get("inherit", "safe-defaults"), "set": values},
        }
    return normalized


def validate_plan(plan, profile, verifier_ids):
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object.")
    allowed = {
        "schema_version", "kit_version", "project", "review_status", "reviewer", "reviewed_at",
        "review_reason", "goals", "deliverables", "tasks", "release_verifiers", "sizing_policy",
    }
    unknown = set(plan) - allowed
    if unknown:
        raise ValueError("Plan has unknown fields: %s" % ", ".join(sorted(unknown)))
    if plan.get("schema_version") != SCHEMA_VERSION or plan.get("kit_version") != VERSION:
        raise ValueError("Plan schema/version must be SVK %s." % VERSION)
    if plan.get("project") != profile.get("slug"):
        raise ValueError("Plan project does not match the profile.")
    if plan.get("review_status") != "approved":
        raise ValueError("Plan must be explicitly approved before scaffolding.")
    if not isinstance(plan.get("reviewer"), str) or not plan.get("reviewer", "").strip():
        raise ValueError("Plan approval requires a reviewer label.")
    goals = plan.get("goals")
    if not isinstance(goals, list) or not goals:
        raise ValueError("Plan goals must be a non-empty array.")
    goal_ids = set()
    goal_titles = []
    for goal in goals:
        if not isinstance(goal, dict) or set(goal) != {"id", "title"}:
            raise ValueError("Each plan goal requires only id and title.")
        if not isinstance(goal.get("id"), str) or not re.match(r"^goal-[1-9][0-9]*$", goal["id"]):
            raise ValueError("Invalid plan goal ID: %r" % goal.get("id"))
        if goal["id"] in goal_ids:
            raise ValueError("Duplicate plan goal ID: %s" % goal["id"])
        if not isinstance(goal.get("title"), str) or not goal["title"].strip():
            raise ValueError("Plan goal titles must be non-empty.")
        goal_ids.add(goal["id"])
        goal_titles.append(goal["title"].strip())
    if sorted(goal_titles) != sorted(profile.get("goals", [])):
        raise ValueError("Plan goals must cover every accepted project goal exactly once.")

    deliverables = plan.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        raise ValueError("Plan deliverables must be a non-empty array.")
    deliverable_ids = set()
    deliverable_goal = {}
    for item in deliverables:
        if not isinstance(item, dict) or set(item) != {"id", "goal_id", "title", "acceptance"}:
            raise ValueError("Each deliverable requires id, goal_id, title, and acceptance.")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", identifier):
            raise ValueError("Invalid deliverable ID: %r" % identifier)
        if identifier in deliverable_ids:
            raise ValueError("Duplicate deliverable ID: %s" % identifier)
        if item.get("goal_id") not in goal_ids:
            raise ValueError("Deliverable %s names an unknown goal." % identifier)
        if not isinstance(item.get("title"), str) or not item["title"].strip():
            raise ValueError("Deliverable %s requires a title." % identifier)
        _strings(item.get("acceptance"), "deliverable %s acceptance" % identifier)
        deliverable_ids.add(identifier)
        deliverable_goal[identifier] = item["goal_id"]
    missing_goal_deliverables = goal_ids - set(deliverable_goal.values())
    if missing_goal_deliverables:
        raise ValueError("Goals without deliverables: %s" % ", ".join(sorted(missing_goal_deliverables)))

    policy = plan.get("sizing_policy")
    if not isinstance(policy, dict) or set(policy) != set(DEFAULT_SIZING_POLICY):
        raise ValueError("sizing_policy must define exactly: %s" % ", ".join(sorted(DEFAULT_SIZING_POLICY)))
    for key, default in DEFAULT_SIZING_POLICY.items():
        value = policy.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > max(default * 10, 20):
            raise ValueError("Invalid sizing policy value for %s." % key)

    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Plan tasks must be a non-empty array.")
    task_ids = set()
    by_id = {}
    covered_deliverables = set()
    required_fields = {
        "id", "kind", "title", "goal_id", "deliverable_id", "depends_on", "dependency_rationale",
        "human_gate", "acceptance", "expected_artifacts", "scope_hints", "required_verifiers",
        "risk", "size_signals",
    }
    optional_fields = {"no_artifact_reason", "size_waiver", "supersedes"}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Every plan task must be an object.")
        missing = required_fields - set(task)
        unknown = set(task) - required_fields - optional_fields
        if missing or unknown:
            raise ValueError("Task %r fields are invalid; missing=%s unknown=%s" % (task.get("id"), sorted(missing), sorted(unknown)))
        task_id = task.get("id")
        if not isinstance(task_id, str) or not re.match(TASK_ID_PATTERN, task_id) or not task_id.startswith("3."):
            raise ValueError("Executable plan task IDs must use the 3.x.x range: %r" % task_id)
        if task_id in task_ids:
            raise ValueError("Duplicate plan task ID: %s" % task_id)
        if task.get("kind") not in TASK_KINDS:
            raise ValueError("Task %s has an invalid kind." % task_id)
        if not isinstance(task.get("title"), str) or not task["title"].strip():
            raise ValueError("Task %s requires a title." % task_id)
        deliverable_id = task.get("deliverable_id")
        if deliverable_id not in deliverable_ids or task.get("goal_id") != deliverable_goal.get(deliverable_id):
            raise ValueError("Task %s goal/deliverable traceability is invalid." % task_id)
        dependencies = _strings(task.get("depends_on"), "task %s depends_on" % task_id, allow_empty=True)
        rationale = task.get("dependency_rationale")
        if not isinstance(rationale, dict) or set(rationale) != set(dependencies) or any(not isinstance(value, str) or not value.strip() for value in rationale.values()):
            raise ValueError("Task %s needs one non-empty rationale for every dependency." % task_id)
        if not isinstance(task.get("human_gate"), bool):
            raise ValueError("Task %s human_gate must be boolean." % task_id)
        acceptance = _strings(task.get("acceptance"), "task %s acceptance" % task_id)
        artifacts = _strings(task.get("expected_artifacts"), "task %s expected_artifacts" % task_id, allow_empty=True)
        scope = _strings(task.get("scope_hints"), "task %s scope_hints" % task_id)
        required_verifiers = _strings(task.get("required_verifiers"), "task %s required_verifiers" % task_id, allow_empty=bool(task.get("human_gate")))
        unknown_verifiers = set(required_verifiers) - set(verifier_ids)
        if unknown_verifiers:
            raise ValueError("Task %s names unknown verifiers: %s" % (task_id, ", ".join(sorted(unknown_verifiers))))
        if not artifacts and (not isinstance(task.get("no_artifact_reason"), str) or not task.get("no_artifact_reason", "").strip()):
            raise ValueError("Task %s requires expected artifacts or a no_artifact_reason." % task_id)
        if task.get("risk") not in ("low", "normal", "high"):
            raise ValueError("Task %s risk must be low, normal, or high." % task_id)
        signals = task.get("size_signals")
        if not isinstance(signals, dict) or set(signals) != {"subsystems", "acceptance_items", "verifier_count", "scope_hints"}:
            raise ValueError("Task %s size_signals has an invalid shape." % task_id)
        actual = {
            "acceptance_items": len(acceptance),
            "verifier_count": len(required_verifiers),
            "scope_hints": len(scope),
        }
        if any(signals.get(key) != value for key, value in actual.items()):
            raise ValueError("Task %s size_signals do not match its contract." % task_id)
        if isinstance(signals.get("subsystems"), bool) or not isinstance(signals.get("subsystems"), int) or signals["subsystems"] < 1:
            raise ValueError("Task %s subsystems must be a positive integer." % task_id)
        policy_to_signal = {
            "max_subsystems": "subsystems",
            "max_acceptance_items": "acceptance_items",
            "max_verifiers": "verifier_count",
            "max_scope_hints": "scope_hints",
        }
        exceeded = [
            policy_to_signal[key] for key, limit in policy.items()
            if signals.get(policy_to_signal[key], 0) > limit
        ]
        if exceeded and (not isinstance(task.get("size_waiver"), str) or not task.get("size_waiver", "").strip()):
            raise ValueError("Task %s exceeds sizing limits (%s) and requires a size_waiver." % (task_id, ", ".join(exceeded)))
        task_ids.add(task_id)
        by_id[task_id] = task
        covered_deliverables.add(deliverable_id)
    missing_tasks = deliverable_ids - covered_deliverables
    if missing_tasks:
        raise ValueError("Deliverables without executable tasks: %s" % ", ".join(sorted(missing_tasks)))
    for task_id, task in by_id.items():
        for dependency in task["depends_on"]:
            if dependency not in by_id:
                raise ValueError("Task %s depends on unknown plan task %s." % (task_id, dependency))
            if dependency == task_id:
                raise ValueError("Task %s cannot depend on itself." % task_id)

    visiting = set()
    visited = set()

    def visit(task_id):
        if task_id in visiting:
            raise ValueError("Plan dependency cycle includes %s." % task_id)
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id]["depends_on"]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(by_id):
        visit(task_id)
    release = _strings(plan.get("release_verifiers"), "release_verifiers")
    if set(release) - set(verifier_ids):
        raise ValueError("release_verifiers contains unknown verifier IDs.")
    return True


def build_plan(profile, answers):
    if not isinstance(answers.get("plan"), dict):
        raise ValueError("SVK 2.1 Interview requires an explicit structured plan proposal.")
    if answers.get("plan_approved") is not True:
        raise ValueError("SVK 2.1 requires explicit plan approval before scaffolding.")
    reviewer = answers.get("plan_reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Plan approval requires a non-empty plan_reviewer label.")
    reason = answers.get("plan_review_reason", "Reviewed during SVK Interview.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Plan approval requires a non-empty review reason.")
    supplied_verifiers = copy.deepcopy(answers.get("verifiers") or {})
    supplied_verifiers.setdefault("svk-governed", {"kind": "builtin", "check": "governed"})
    verifiers = validate_verifiers(supplied_verifiers)
    proposal = copy.deepcopy(answers["plan"])
    proposal.update(
        {
            "schema_version": SCHEMA_VERSION,
            "kit_version": VERSION,
            "project": profile["slug"],
            "review_status": "approved",
            "reviewer": reviewer.strip(),
            "reviewed_at": utc_now(),
            "review_reason": reason.strip(),
            "sizing_policy": proposal.get("sizing_policy", copy.deepcopy(DEFAULT_SIZING_POLICY)),
        }
    )
    validate_plan(proposal, profile, verifiers.keys())
    verifier_file = {"schema_version": SCHEMA_VERSION, "kit_version": VERSION, "verifiers": verifiers}
    return proposal, verifier_file
