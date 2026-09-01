"""Deterministic project, evidence, governance, and package verification."""

from __future__ import print_function

import ast
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from .constants import (
    CORE_DOCUMENTS,
    EVIDENCE_INDEX_FILE,
    EVIDENCE_RUNS_DIR,
    GOVERNANCE_FILE,
    INSTALL_FILE,
    INTERVIEW_FILE,
    LOCK_FILE,
    MODULES,
    MODULE_DOCUMENTS,
    PLAN_FILE,
    PROFILE_FILE,
    SCHEMA_VERSION,
    STATE_FILE,
    STATUS_VALUES,
    TASK_ID_PATTERN,
    TRANSITION_LOCK_FILE,
    VERIFIERS_FILE,
    VERSION,
)
from .evidence import receipt_fresh
from .governance import validate_governance_shape
from .interview import validate_session
from .plan import validate_plan, validate_verifiers
from .profile import expected_document_count, profile_name, select_modules
from .render import render_documents
from .util import parse_utc, read_json, safe_relative_path, sha256_file


LEVEL_RANK = {"PASS": 0, "WARN": 1, "BLOCKED": 2, "ERROR": 3}
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|\[PLACEHOLDER\]|<fill(?:-|\s)", re.IGNORECASE)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def diagnostic(code, level, message, path=None, pointer=None, category=None, remediation=None):
    value = {
        "code": code,
        "level": level,
        "category": category or (code.split("-", 2)[1].lower() if "-" in code else "project"),
        "message": message,
    }
    if path:
        value["path"] = str(path).replace("\\", "/")
    if pointer:
        value["pointer"] = pointer
    if remediation:
        value["remediation"] = remediation
    return value


def overall(diagnostics):
    if not diagnostics:
        return "PASS"
    return max((item["level"] for item in diagnostics), key=lambda level: LEVEL_RANK[level])


def _load(path, code, diagnostics):
    try:
        return read_json(path)
    except FileNotFoundError:
        diagnostics.append(diagnostic(code + ".MISSING", "ERROR", "Required JSON file is missing.", path))
    except (ValueError, json.JSONDecodeError) as error:
        diagnostics.append(diagnostic(code + ".INVALID_JSON", "ERROR", str(error), path))
    return None


def _exact_fields(value, required, optional, code, diagnostics, pointer=""):
    if not isinstance(value, dict):
        diagnostics.append(diagnostic(code + "-TYPE", "ERROR", "Expected an object.", pointer=pointer or "/"))
        return False
    missing = set(required) - set(value)
    unknown = set(value) - set(required) - set(optional)
    if missing:
        diagnostics.append(diagnostic(code + "-REQUIRED", "ERROR", "Missing fields: %s" % ", ".join(sorted(missing)), pointer=pointer or "/"))
    if unknown:
        diagnostics.append(diagnostic(code + "-UNKNOWN", "ERROR", "Unknown fields: %s" % ", ".join(sorted(unknown)), pointer=pointer or "/"))
    return not missing and not unknown


def _string(value, code, diagnostics, pointer, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        diagnostics.append(diagnostic(code, "ERROR", "Expected a non-empty string." if not allow_empty else "Expected a string.", pointer=pointer))
        return False
    return True


def _string_array(value, code, diagnostics, pointer, allow_empty=True, unique=False):
    valid = isinstance(value, list) and (allow_empty or bool(value)) and all(isinstance(item, str) and item.strip() for item in value)
    if valid and unique:
        valid = len(value) == len(set(value))
    if not valid:
        detail = "non-empty " if not allow_empty else ""
        uniqueness = " unique" if unique else ""
        diagnostics.append(diagnostic(code, "ERROR", "Expected a %sarray of non-empty%s strings." % (detail, uniqueness), pointer=pointer))
    return valid


def _required_paths(profile):
    required = list(CORE_DOCUMENTS) + [
        PROFILE_FILE,
        STATE_FILE,
        PLAN_FILE,
        VERIFIERS_FILE,
        GOVERNANCE_FILE,
        EVIDENCE_INDEX_FILE,
        INTERVIEW_FILE,
        INSTALL_FILE,
    ]
    for module in profile.get("modules", []):
        required.extend(MODULE_DOCUMENTS.get(module, ()))
    return required


def _validate_profile(profile, diagnostics):
    required = {
        "schema_version", "svk_version", "title", "slug", "idea", "goals", "non_goals",
        "constraints", "platforms", "integrations", "research_tier", "risk", "team_size",
        "signals", "profile", "modules", "expected_document_count",
    }
    if not _exact_fields(profile, required, set(), "SVK-PROFILE", diagnostics):
        if not isinstance(profile, dict):
            return
    if profile.get("schema_version") != SCHEMA_VERSION or profile.get("svk_version") != VERSION:
        diagnostics.append(diagnostic("SVK-PROFILE-VERSION", "ERROR", "Profile schema/version must be SVK %s." % VERSION, pointer="/schema_version"))
    for field in ("title", "slug", "idea"):
        _string(profile.get(field), "SVK-PROFILE-%s" % field.upper(), diagnostics, "/" + field)
    if isinstance(profile.get("slug"), str) and not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", profile["slug"]):
        diagnostics.append(diagnostic("SVK-PROFILE-SLUG", "ERROR", "slug must use lowercase words separated by hyphens.", pointer="/slug"))
    for field in ("goals", "non_goals", "constraints", "platforms", "integrations"):
        _string_array(profile.get(field), "SVK-PROFILE-%s" % field.upper(), diagnostics, "/" + field, allow_empty=(field != "goals"))
    tier = profile.get("research_tier")
    if isinstance(tier, bool) or not isinstance(tier, int) or tier < 0 or tier > 3:
        diagnostics.append(diagnostic("SVK-PROFILE-RESEARCH", "ERROR", "research_tier must be 0 through 3.", pointer="/research_tier"))
    if profile.get("risk") not in ("low", "normal", "high"):
        diagnostics.append(diagnostic("SVK-PROFILE-RISK", "ERROR", "risk must be low, normal, or high.", pointer="/risk"))
    team_size = profile.get("team_size")
    if isinstance(team_size, bool) or not isinstance(team_size, int) or team_size < 1:
        diagnostics.append(diagnostic("SVK-PROFILE-TEAM", "ERROR", "team_size must be a positive integer.", pointer="/team_size"))
    signals = profile.get("signals")
    signal_names = {"user_facing", "ui", "deployable", "sensitive_data", "regulated"}
    if not isinstance(signals, dict) or set(signals) != signal_names or any(not isinstance(value, bool) for value in signals.values()):
        diagnostics.append(diagnostic("SVK-PROFILE-SIGNALS", "ERROR", "signals must contain exactly the five boolean project signals.", pointer="/signals"))
    modules = profile.get("modules")
    if not isinstance(modules, list) or not modules or "core" not in modules or len(modules) != len(set(modules)) or any(item not in MODULES for item in modules):
        diagnostics.append(diagnostic("SVK-PROFILE-MODULES", "ERROR", "Modules must be unique, known, and include core.", pointer="/modules"))
        return
    try:
        answer_view = dict(signals or {})
        answer_view.update({"research_tier": tier, "integrations": profile.get("integrations"), "team_size": team_size})
        required_modules = set(select_modules(answer_view))
        missing = required_modules - set(modules)
        if missing:
            diagnostics.append(diagnostic("SVK-PROFILE-UNSAFE-DOWNGRADE", "ERROR", "Required modules were removed: %s" % ", ".join(sorted(missing)), pointer="/modules"))
        expected = expected_document_count(modules)
        if profile.get("expected_document_count") != expected:
            diagnostics.append(diagnostic("SVK-PROFILE-DOCUMENT-COUNT", "ERROR", "expected_document_count must be %d." % expected, pointer="/expected_document_count"))
        expected_name = profile_name(modules, {"risk": profile.get("risk")})
        if profile.get("profile") != expected_name:
            diagnostics.append(diagnostic("SVK-PROFILE-LABEL", "ERROR", "Profile label must be %s." % expected_name, pointer="/profile"))
    except (TypeError, ValueError) as error:
        diagnostics.append(diagnostic("SVK-PROFILE-DERIVATION", "ERROR", str(error)))


TASK_REQUIRED = {
    "id", "kind", "title", "goal_id", "deliverable_id", "status", "depends_on",
    "dependency_rationale", "human_gate", "acceptance", "expected_artifacts", "scope_hints",
    "required_verifiers", "risk", "size_signals", "completion_receipts",
}
TASK_OPTIONAL = {"blocker", "no_artifact_reason", "size_waiver", "supersedes", "legacy_completion"}


def _validate_task(task, index, verifier_ids, diagnostics):
    pointer = "/tasks/%d" % index
    if not _exact_fields(task, TASK_REQUIRED, TASK_OPTIONAL, "SVK-TASK", diagnostics, pointer):
        if not isinstance(task, dict):
            return None
    task_id = task.get("id")
    if not isinstance(task_id, str) or not re.match(TASK_ID_PATTERN, task_id):
        diagnostics.append(diagnostic("SVK-TASK-ID", "ERROR", "Invalid task ID: %r" % task_id, pointer=pointer + "/id"))
        return None
    for field in ("title", "goal_id", "deliverable_id"):
        _string(task.get(field), "SVK-TASK-%s" % field.upper(), diagnostics, pointer + "/" + field)
    if task.get("kind") not in ("research", "design", "implementation", "migration", "verification", "documentation"):
        diagnostics.append(diagnostic("SVK-TASK-KIND", "ERROR", "Invalid task kind.", pointer=pointer + "/kind"))
    if task.get("status") not in STATUS_VALUES:
        diagnostics.append(diagnostic("SVK-TASK-STATUS", "ERROR", "Invalid task status.", pointer=pointer + "/status"))
    dependencies_valid = _string_array(task.get("depends_on"), "SVK-TASK-DEPS", diagnostics, pointer + "/depends_on", unique=True)
    rationale = task.get("dependency_rationale")
    if dependencies_valid and (not isinstance(rationale, dict) or set(rationale) != set(task["depends_on"]) or any(not isinstance(value, str) or not value.strip() for value in rationale.values())):
        diagnostics.append(diagnostic("SVK-TASK-DEP-RATIONALE", "ERROR", "Every dependency requires one rationale.", pointer=pointer + "/dependency_rationale"))
    if not isinstance(task.get("human_gate"), bool):
        diagnostics.append(diagnostic("SVK-TASK-HUMAN-GATE", "ERROR", "human_gate must be boolean.", pointer=pointer + "/human_gate"))
    acceptance_valid = _string_array(task.get("acceptance"), "SVK-TASK-ACCEPTANCE", diagnostics, pointer + "/acceptance", allow_empty=False)
    artifacts_valid = _string_array(task.get("expected_artifacts"), "SVK-TASK-ARTIFACTS", diagnostics, pointer + "/expected_artifacts")
    scope_valid = _string_array(task.get("scope_hints"), "SVK-TASK-SCOPE", diagnostics, pointer + "/scope_hints", allow_empty=False, unique=True)
    verifiers_valid = _string_array(task.get("required_verifiers"), "SVK-TASK-VERIFIERS", diagnostics, pointer + "/required_verifiers", allow_empty=bool(task.get("human_gate")), unique=True)
    receipts_valid = _string_array(task.get("completion_receipts"), "SVK-TASK-RECEIPTS", diagnostics, pointer + "/completion_receipts", unique=True)
    if verifiers_valid:
        unknown = set(task["required_verifiers"]) - set(verifier_ids)
        if unknown:
            diagnostics.append(diagnostic("SVK-TASK-VERIFIER-UNKNOWN", "ERROR", "Unknown verifiers: %s" % ", ".join(sorted(unknown)), pointer=pointer + "/required_verifiers"))
    if artifacts_valid and not task["expected_artifacts"] and not (isinstance(task.get("no_artifact_reason"), str) and task.get("no_artifact_reason", "").strip()):
        diagnostics.append(diagnostic("SVK-TASK-ARTIFACT-RATIONALE", "ERROR", "A task without artifacts requires no_artifact_reason.", pointer=pointer))
    for field in ("expected_artifacts", "scope_hints"):
        if isinstance(task.get(field), list):
            for position, relative in enumerate(task[field]):
                candidate = Path(relative) if isinstance(relative, str) else Path("/")
                if not isinstance(relative, str) or candidate.is_absolute() or ".." in candidate.parts:
                    diagnostics.append(diagnostic("SVK-TASK-PATH", "ERROR", "Task paths must remain project-relative.", pointer="%s/%s/%d" % (pointer, field, position)))
    if task.get("risk") not in ("low", "normal", "high"):
        diagnostics.append(diagnostic("SVK-TASK-RISK", "ERROR", "Task risk must be low, normal, or high.", pointer=pointer + "/risk"))
    signals = task.get("size_signals")
    if not isinstance(signals, dict) or set(signals) != {"subsystems", "acceptance_items", "verifier_count", "scope_hints"} or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in signals.values()):
        diagnostics.append(diagnostic("SVK-TASK-SIZE", "ERROR", "Task size_signals has an invalid shape.", pointer=pointer + "/size_signals"))
    elif acceptance_valid and scope_valid and verifiers_valid:
        expected = {"acceptance_items": len(task["acceptance"]), "verifier_count": len(task["required_verifiers"]), "scope_hints": len(task["scope_hints"])}
        if signals["subsystems"] < 1 or any(signals[key] != value for key, value in expected.items()):
            diagnostics.append(diagnostic("SVK-TASK-SIZE-DRIFT", "ERROR", "Task size_signals do not match the task contract.", pointer=pointer + "/size_signals"))
    if task.get("status") == "blocked" and not (isinstance(task.get("blocker"), str) and task.get("blocker", "").strip()):
        diagnostics.append(diagnostic("SVK-TASK-BLOCKER", "ERROR", "Blocked tasks require a blocker reason.", pointer=pointer + "/blocker"))
    if receipts_valid and any(not SHA256_RE.match(item) for item in task.get("completion_receipts", [])):
        diagnostics.append(diagnostic("SVK-TASK-RECEIPT-ID", "ERROR", "Receipt IDs must be 64-character lowercase hex strings.", pointer=pointer + "/completion_receipts"))
    return task_id


def _validate_state(state, profile, plan, verifier_ids, diagnostics):
    required = {"schema_version", "kit_version", "state_revision", "project", "stage", "charter", "tasks", "next_action", "authorizations", "updated_at"}
    if not _exact_fields(state, required, set(), "SVK-STATE", diagnostics):
        if not isinstance(state, dict):
            return
    if state.get("schema_version") != SCHEMA_VERSION or state.get("kit_version") != VERSION:
        diagnostics.append(diagnostic("SVK-STATE-VERSION", "ERROR", "State schema/version must be SVK %s." % VERSION, pointer="/schema_version"))
    revision = state.get("state_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        diagnostics.append(diagnostic("SVK-STATE-REVISION", "ERROR", "state_revision must be a positive integer.", pointer="/state_revision"))
    if state.get("stage") not in ("charter", "execution", "complete"):
        diagnostics.append(diagnostic("SVK-STATE-STAGE", "ERROR", "stage must be charter, execution, or complete.", pointer="/stage"))
    charter = state.get("charter")
    if not isinstance(charter, dict) or set(charter) != {"accepted"} or not isinstance(charter.get("accepted"), bool):
        diagnostics.append(diagnostic("SVK-STATE-CHARTER", "ERROR", "charter must contain only boolean accepted.", pointer="/charter"))
    tasks = state.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 4:
        diagnostics.append(diagnostic("SVK-TASKS-EMPTY", "ERROR", "State must contain at least four tasks.", pointer="/tasks"))
        return
    ids = []
    by_id = {}
    for index, task in enumerate(tasks):
        task_id = _validate_task(task, index, verifier_ids, diagnostics)
        if task_id:
            ids.append(task_id)
            by_id[task_id] = task
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        diagnostics.append(diagnostic("SVK-TASK-DUPLICATE", "ERROR", "Duplicate task IDs: %s" % ", ".join(duplicates), pointer="/tasks"))
    for task_id, task in by_id.items():
        for dependency in task.get("depends_on", []):
            if dependency not in by_id:
                diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-MISSING", "ERROR", "Task %s depends on unknown task %s." % (task_id, dependency)))
            elif dependency == task_id:
                diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-SELF", "ERROR", "Task %s cannot depend on itself." % task_id))
    visiting = set()
    visited = set()

    def visit(task_id):
        if task_id in visiting:
            diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-CYCLE", "ERROR", "Task dependency cycle includes %s." % task_id))
            return
        if task_id in visited or task_id not in by_id:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in by_id:
        visit(task_id)
    complete_statuses = ("done", "superseded")
    for task_id, task in by_id.items():
        if task.get("status") not in ("in_progress", "blocked", "done"):
            continue
        incomplete = [dependency for dependency in task.get("depends_on", []) if by_id.get(dependency, {}).get("status") not in complete_statuses]
        if incomplete:
            diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-INCOMPLETE", "ERROR", "Task %s advanced before dependencies completed: %s" % (task_id, ", ".join(incomplete))))
    active = [task for task in tasks if isinstance(task, dict) and task.get("status") in ("in_progress", "blocked")]
    blocked = [task for task in active if task.get("status") == "blocked"]
    if blocked:
        diagnostics.append(diagnostic("SVK-TASK-BLOCKED", "BLOCKED", "Task %s is blocked: %s" % (blocked[0].get("id"), blocked[0].get("blocker"))))
    all_complete = all(task.get("status") in complete_statuses for task in tasks if isinstance(task, dict))
    if len(active) != 1 and not (all_complete and not active):
        diagnostics.append(diagnostic("SVK-ACTIVE-COUNT", "ERROR", "Exactly one task must be active until completion; found %d." % len(active), pointer="/tasks"))
    action = state.get("next_action")
    if all_complete and action is None:
        pass
    elif not isinstance(action, dict) or set(action) != {"task_id", "instruction"} or action.get("task_id") not in by_id:
        diagnostics.append(diagnostic("SVK-NEXT-ACTION", "ERROR", "next_action must name a real task with exact fields.", pointer="/next_action"))
    elif len(active) == 1 and (action.get("task_id") != active[0].get("id") or action.get("instruction") != active[0].get("title")):
        diagnostics.append(diagnostic("SVK-NEXT-MISMATCH", "ERROR", "next_action does not match the active task.", pointer="/next_action"))
    authorizations = state.get("authorizations")
    if not isinstance(authorizations, list):
        diagnostics.append(diagnostic("SVK-AUTHORIZATIONS-TYPE", "ERROR", "authorizations must be an array.", pointer="/authorizations"))
    else:
        for index, authorization in enumerate(authorizations):
            required_auth = {"task_id", "actor", "reason", "recorded_at", "kind"}
            pointer = "/authorizations/%d" % index
            if _exact_fields(authorization, required_auth, set(), "SVK-AUTHORIZATION", diagnostics, pointer):
                if authorization.get("kind") != "cooperative-human-attestation":
                    diagnostics.append(diagnostic("SVK-AUTHORIZATION-KIND", "ERROR", "Unknown authorization kind.", pointer=pointer + "/kind"))
                for field in ("task_id", "actor", "reason"):
                    _string(authorization.get(field), "SVK-AUTHORIZATION-VALUE", diagnostics, pointer + "/" + field)
                try:
                    parse_utc(authorization.get("recorded_at"))
                except (TypeError, ValueError):
                    diagnostics.append(diagnostic("SVK-AUTHORIZATION-DATE", "ERROR", "recorded_at must be an ISO-8601 timestamp.", pointer=pointer + "/recorded_at"))
    accepted = bool(isinstance(charter, dict) and charter.get("accepted"))
    charter_task = by_id.get("1.1.2", {})
    if accepted != (charter_task.get("status") == "done"):
        diagnostics.append(diagnostic("SVK-CHARTER-STATE", "ERROR", "Charter acceptance and task 1.1.2 disagree."))
    if state.get("stage") == "charter" and accepted:
        diagnostics.append(diagnostic("SVK-STATE-STAGE-CHARTER", "ERROR", "Accepted charter cannot remain in charter stage.", pointer="/stage"))
    if state.get("stage") == "complete" and not all_complete:
        diagnostics.append(diagnostic("SVK-STATE-STAGE-COMPLETE", "ERROR", "Complete stage requires every task to be done or superseded.", pointer="/stage"))
    if profile and state.get("project") != profile.get("slug"):
        diagnostics.append(diagnostic("SVK-PROJECT-MISMATCH", "ERROR", "State and profile identify different projects."))
    try:
        parse_utc(state.get("updated_at"))
    except (TypeError, ValueError):
        diagnostics.append(diagnostic("SVK-STATE-DATE", "ERROR", "updated_at must be an ISO-8601 timestamp.", pointer="/updated_at"))
    if isinstance(plan, dict):
        plan_by_id = {task.get("id"): task for task in plan.get("tasks", []) if isinstance(task, dict)}
        for task_id, planned in plan_by_id.items():
            actual = by_id.get(task_id)
            if actual is None:
                diagnostics.append(diagnostic("SVK-PLAN-STATE-TASK-MISSING", "ERROR", "State omits approved plan task %s." % task_id))
                continue
            for field in planned:
                if actual.get(field) != planned.get(field):
                    diagnostics.append(diagnostic("SVK-PLAN-STATE-DRIFT", "ERROR", "Task %s field %s differs from the approved plan." % (task_id, field)))


def _validate_interview(value, root, profile, diagnostics):
    try:
        validate_session(value)
    except (TypeError, ValueError) as error:
        diagnostics.append(diagnostic("SVK-INTERVIEW-SHAPE", "ERROR", str(error), INTERVIEW_FILE))
        return
    if value.get("schema_version") != SCHEMA_VERSION or value.get("kit_version") != VERSION or value.get("status") != "scaffolded":
        diagnostics.append(diagnostic("SVK-INTERVIEW-STATE", "ERROR", "Project Interview checkpoint must be a scaffolded SVK %s session." % VERSION, INTERVIEW_FILE))
    if not isinstance(profile, dict) or value.get("target") != profile.get("slug"):
        diagnostics.append(diagnostic("SVK-INTERVIEW-TARGET", "ERROR", "Interview target differs from the project slug.", INTERVIEW_FILE))


def _validate_receipt_shape(receipt, run_id, task_ids, verifier_ids, diagnostics, path):
    required = {
        "schema_version", "kit_version", "run_id", "task_id", "verifier_id", "owner", "started_at", "finished_at",
        "cwd", "argv", "resolved_executable", "exit_code", "timed_out", "expected_exit_codes", "stdout", "stderr",
        "inputs_before", "inputs_after", "input_changed_during_run", "artifacts", "missing_artifacts", "result",
    }
    if not _exact_fields(receipt, required, set(), "SVK-RECEIPT", diagnostics, pointer="/"):
        return
    if receipt.get("schema_version") != SCHEMA_VERSION or receipt.get("kit_version") != VERSION or receipt.get("run_id") != run_id:
        diagnostics.append(diagnostic("SVK-RECEIPT-VERSION", "ERROR", "Receipt identity/version is invalid.", path))
    if receipt.get("task_id") not in task_ids or receipt.get("verifier_id") not in verifier_ids:
        diagnostics.append(diagnostic("SVK-RECEIPT-SUBJECT", "ERROR", "Receipt names an unknown task or verifier.", path))
    if receipt.get("result") not in ("pass", "fail") or not isinstance(receipt.get("timed_out"), bool) or not isinstance(receipt.get("input_changed_during_run"), bool):
        diagnostics.append(diagnostic("SVK-RECEIPT-RESULT", "ERROR", "Receipt outcome fields are invalid.", path))
    if not isinstance(receipt.get("owner"), str) or not receipt.get("owner", "").strip():
        diagnostics.append(diagnostic("SVK-RECEIPT-OWNER", "ERROR", "Receipt owner must be a non-empty label.", path))
    if not isinstance(receipt.get("cwd"), str) or not isinstance(receipt.get("resolved_executable"), str):
        diagnostics.append(diagnostic("SVK-RECEIPT-COMMAND", "ERROR", "Receipt cwd and resolved executable must be strings.", path))
    argv = receipt.get("argv")
    expected_exits = receipt.get("expected_exit_codes")
    exit_code = receipt.get("exit_code")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) for item in argv):
        diagnostics.append(diagnostic("SVK-RECEIPT-ARGV", "ERROR", "Receipt argv must contain command-array strings.", path))
    if not isinstance(expected_exits, list) or not expected_exits or any(isinstance(item, bool) or not isinstance(item, int) for item in expected_exits):
        diagnostics.append(diagnostic("SVK-RECEIPT-EXITS", "ERROR", "Receipt expected_exit_codes must contain integers.", path))
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        diagnostics.append(diagnostic("SVK-RECEIPT-EXIT", "ERROR", "Receipt exit_code must be an integer.", path))
    for field in ("stdout", "stderr"):
        descriptor = receipt.get(field)
        if not isinstance(descriptor, dict) or set(descriptor) != {"sha256", "bytes", "truncated"} or not SHA256_RE.match(str(descriptor.get("sha256", ""))) or isinstance(descriptor.get("bytes"), bool) or not isinstance(descriptor.get("bytes"), int) or descriptor.get("bytes", -1) < 0 or not isinstance(descriptor.get("truncated"), bool):
            diagnostics.append(diagnostic("SVK-RECEIPT-OUTPUT", "ERROR", "Receipt %s descriptor is invalid." % field, path))
    for field in ("inputs_before", "inputs_after"):
        descriptor = receipt.get(field)
        if not isinstance(descriptor, dict) or set(descriptor) != {"sha256", "entries"} or not SHA256_RE.match(str(descriptor.get("sha256", ""))) or isinstance(descriptor.get("entries"), bool) or not isinstance(descriptor.get("entries"), int) or descriptor.get("entries", -1) < 0:
            diagnostics.append(diagnostic("SVK-RECEIPT-INPUT", "ERROR", "Receipt input descriptor is invalid.", path))
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or any(
        not isinstance(item, dict)
        or set(item) != {"path", "kind", "sha256"}
        or not isinstance(item.get("path"), str)
        or item.get("kind") not in ("file", "directory")
        or not SHA256_RE.match(str(item.get("sha256", "")))
        for item in (artifacts if isinstance(artifacts, list) else [])
    ):
        diagnostics.append(diagnostic("SVK-RECEIPT-ARTIFACT", "ERROR", "Receipt artifact descriptors are invalid.", path))
    missing = receipt.get("missing_artifacts")
    if not isinstance(missing, list) or any(not isinstance(item, str) or not item for item in (missing if isinstance(missing, list) else [])):
        diagnostics.append(diagnostic("SVK-RECEIPT-MISSING", "ERROR", "Receipt missing_artifacts must contain path strings.", path))
    expected_pass = (
        isinstance(expected_exits, list)
        and isinstance(exit_code, int) and not isinstance(exit_code, bool)
        and receipt.get("timed_out") is False
        and exit_code in expected_exits
        and missing == []
        and receipt.get("input_changed_during_run") is False
    )
    if receipt.get("result") in ("pass", "fail") and (receipt.get("result") == "pass") != expected_pass:
        diagnostics.append(diagnostic("SVK-RECEIPT-DERIVATION", "ERROR", "Receipt result is inconsistent with its runtime facts.", path))
    try:
        started = parse_utc(receipt.get("started_at"))
        finished = parse_utc(receipt.get("finished_at"))
        if finished < started:
            raise ValueError("finished before started")
    except (TypeError, ValueError):
        diagnostics.append(diagnostic("SVK-RECEIPT-DATE", "ERROR", "Receipt timestamps are invalid.", path))


def _validate_evidence(root, state, verifiers, diagnostics):
    index = _load(root / EVIDENCE_INDEX_FILE, "SVK-EVIDENCE", diagnostics)
    if not isinstance(index, dict):
        return
    if not _exact_fields(index, {"schema_version", "kit_version", "project", "records"}, set(), "SVK-EVIDENCE", diagnostics):
        return
    if index.get("schema_version") != SCHEMA_VERSION or index.get("kit_version") != VERSION:
        diagnostics.append(diagnostic("SVK-EVIDENCE-VERSION", "ERROR", "Evidence index version is invalid.", EVIDENCE_INDEX_FILE))
    records = index.get("records")
    if not isinstance(records, list):
        diagnostics.append(diagnostic("SVK-EVIDENCE-RECORDS", "ERROR", "Evidence records must be an array.", EVIDENCE_INDEX_FILE))
        return
    task_by_id = {task.get("id"): task for task in (state or {}).get("tasks", []) if isinstance(task, dict)}
    task_ids = set(task_by_id)
    verifier_ids = set((verifiers or {}).get("verifiers", {}))
    record_ids = []
    receipts = {}
    attestations = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict) or record.get("kind") not in ("attestation", "verification"):
            diagnostics.append(diagnostic("SVK-EVIDENCE-RECORD", "ERROR", "Evidence record %d has an invalid kind/shape." % position, EVIDENCE_INDEX_FILE))
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            diagnostics.append(diagnostic("SVK-EVIDENCE-ID", "ERROR", "Evidence records require IDs.", EVIDENCE_INDEX_FILE))
            continue
        record_ids.append(record_id)
        if record.get("task_id") not in task_ids:
            diagnostics.append(diagnostic("SVK-EVIDENCE-TASK", "ERROR", "Evidence names unknown task %r." % record.get("task_id"), EVIDENCE_INDEX_FILE))
        if record["kind"] == "attestation":
            required = {"id", "kind", "task_id", "result", "summary", "actor", "recorded_at", "artifacts"}
            if _exact_fields(record, required, set(), "SVK-EVIDENCE-ATTESTATION", diagnostics):
                attestations.add(record.get("task_id"))
            continue
        required = {"id", "kind", "task_id", "verifier_id", "result", "recorded_at", "path", "receipt_sha256"}
        if not _exact_fields(record, required, set(), "SVK-EVIDENCE-VERIFICATION", diagnostics):
            continue
        if not SHA256_RE.match(record_id):
            diagnostics.append(diagnostic("SVK-EVIDENCE-RECEIPT-ID", "ERROR", "Verification ID must be a 64-character lowercase digest-style ID.", EVIDENCE_INDEX_FILE))
            continue
        try:
            receipt_path = safe_relative_path(root, record.get("path"), must_exist=True, expect_file=True)
            if record.get("path") != "%s/%s/receipt.json" % (EVIDENCE_RUNS_DIR, record_id):
                raise ValueError("Receipt path is not canonical for its ID.")
            if not SHA256_RE.match(str(record.get("receipt_sha256", ""))) or sha256_file(receipt_path) != record.get("receipt_sha256"):
                raise ValueError("Receipt failed its immutable digest check.")
            receipt = read_json(receipt_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            diagnostics.append(diagnostic("SVK-EVIDENCE-RECEIPT", "ERROR", str(error), record.get("path")))
            continue
        _validate_receipt_shape(receipt, record_id, task_ids, verifier_ids, diagnostics, record.get("path"))
        if (
            record.get("task_id") != receipt.get("task_id")
            or record.get("verifier_id") != receipt.get("verifier_id")
            or record.get("result") != receipt.get("result")
        ):
            diagnostics.append(diagnostic("SVK-EVIDENCE-RECEIPT-MISMATCH", "ERROR", "Receipt subject or result differs from its index record.", record.get("path")))
        receipts[record_id] = receipt
    duplicates = sorted({item for item in record_ids if record_ids.count(item) > 1})
    if duplicates:
        diagnostics.append(diagnostic("SVK-EVIDENCE-DUPLICATE", "ERROR", "Duplicate evidence IDs: %s" % ", ".join(duplicates), EVIDENCE_INDEX_FILE))
    runs_root = root / EVIDENCE_RUNS_DIR
    if runs_root.exists():
        orphan_ids = sorted(path.name for path in runs_root.iterdir() if path.is_dir() and path.name not in receipts)
        if orphan_ids:
            diagnostics.append(diagnostic("SVK-EVIDENCE-ORPHAN", "BLOCKED", "Unindexed receipt directories require recovery: %s" % ", ".join(orphan_ids), EVIDENCE_RUNS_DIR, remediation="Run svk recover inspect."))
    authorizations = {item.get("task_id") for item in (state or {}).get("authorizations", []) if isinstance(item, dict)}
    for task_id, task in task_by_id.items():
        if task.get("status") != "done":
            continue
        if task_id == "1.1.1":
            if task_id not in attestations:
                diagnostics.append(diagnostic("SVK-EVIDENCE-INTERVIEW", "ERROR", "Completed Interview task lacks its attestation.", EVIDENCE_INDEX_FILE))
            continue
        if task.get("human_gate") and task_id not in authorizations:
            diagnostics.append(diagnostic("SVK-EVIDENCE-HUMAN", "ERROR", "Completed human-gate task %s lacks a cooperative attestation." % task_id, STATE_FILE))
        if task.get("legacy_completion"):
            diagnostics.append(diagnostic("SVK-EVIDENCE-LEGACY", "WARN", "Task %s was completed under the 2.0 self-report contract." % task_id, STATE_FILE))
            continue
        completed_receipts = task.get("completion_receipts", [])
        completed = [receipts.get(run_id) for run_id in completed_receipts]
        for verifier_id in task.get("required_verifiers", []):
            matches = [receipt for receipt in completed if receipt and receipt.get("verifier_id") == verifier_id and receipt.get("task_id") == task_id and receipt.get("result") == "pass"]
            if not matches:
                diagnostics.append(diagnostic("SVK-EVIDENCE-MISSING", "ERROR", "Completed task %s lacks a passing %s receipt." % (task_id, verifier_id), EVIDENCE_INDEX_FILE))
                continue
            if not any(receipt_fresh(root, task, receipt) for receipt in matches):
                diagnostics.append(diagnostic("SVK-EVIDENCE-STALE", "ERROR", "Task %s receipt for %s no longer matches current inputs." % (task_id, verifier_id), EVIDENCE_INDEX_FILE))


def _validate_markdown_file(root, path, relative, diagnostics):
    try:
        safe_relative_path(root, relative, must_exist=True, expect_file=True)
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        diagnostics.append(diagnostic("SVK-MARKDOWN-READ", "ERROR", str(error), relative))
        return
    if PLACEHOLDER_RE.search(text):
        diagnostics.append(diagnostic("SVK-PLACEHOLDER", "ERROR", "Unresolved placeholder text found.", relative))
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.strip("<>")
        try:
            resolved = (path.parent / target).resolve(strict=False)
            resolved.relative_to(root)
            lexical = resolved.relative_to(root).as_posix()
            safe_relative_path(root, lexical, must_exist=True)
        except (OSError, ValueError):
            diagnostics.append(diagnostic("SVK-LINK-MISSING-OR-ESCAPE", "ERROR", "Relative link is missing, linked, or escapes the project: %s" % target, relative))


def _validate_governance(root, profile, state, governance, diagnostics, scope):
    if governance is None:
        return
    try:
        validate_governance_shape(governance)
    except ValueError as error:
        diagnostics.append(diagnostic("SVK-GOVERNANCE-SHAPE", "ERROR", str(error), GOVERNANCE_FILE))
        return
    files = governance["files"]
    for relative in _required_paths(profile or {}):
        if relative not in files:
            diagnostics.append(diagnostic("SVK-GOVERNANCE-MISSING", "ERROR", "Required path is not registered: %s" % relative, GOVERNANCE_FILE))
    rendered = {}
    if profile and state:
        try:
            rendered = render_documents(profile, state)
        except (KeyError, TypeError, ValueError):
            # Shape diagnostics are emitted by the profile/state validators. A
            # malformed contract must be reportable rather than crashing while
            # computing the generated projection.
            rendered = {}
    governed_markdown = set()
    for relative, policy in sorted(files.items()):
        role = policy["role"]
        try:
            path = safe_relative_path(root, relative, must_exist=(role != "optional_governed"), expect_file=True)
        except (OSError, ValueError) as error:
            diagnostics.append(diagnostic("SVK-GOVERNANCE-PATH", "ERROR", str(error), relative))
            continue
        if not path.exists():
            continue
        if role == "immutable_provenance" and sha256_file(path) != policy.get("sha256"):
            diagnostics.append(diagnostic("SVK-INTEGRITY-IMMUTABLE", "ERROR", "Immutable provenance digest changed.", relative))
        if role == "generated_projection":
            expected = rendered.get(relative)
            if expected is None or path.read_text(encoding="utf-8") != expected:
                diagnostics.append(diagnostic("SVK-GENERATED-DRIFT", "ERROR", "Generated projection differs from current state.", relative, remediation="Re-render this projection through an SVK state operation."))
        if relative.endswith(".md"):
            governed_markdown.add(relative)
            _validate_markdown_file(root, path, relative, diagnostics)
    if scope == "all-docs":
        for path in sorted(root.rglob("*.md")):
            relative = path.relative_to(root).as_posix()
            if relative not in governed_markdown:
                _validate_markdown_file(root, path, relative, diagnostics)


def _validate_transactions_and_locks(root, state, diagnostics, ignore_transition=False):
    transaction_dir = root / ".svk" / "transactions"
    if transaction_dir.exists():
        for path in sorted(transaction_dir.glob("*.json")):
            transaction = _load(path, "SVK-TRANSACTION", diagnostics)
            if not isinstance(transaction, dict):
                continue
            required = {"schema_version", "kit_version", "id", "operation", "status", "recorded_at", "before_revision", "after_revision"}
            optional = {"task_id", "details"}
            _exact_fields(transaction, required, optional, "SVK-TRANSACTION", diagnostics)
            if transaction.get("schema_version") != SCHEMA_VERSION or transaction.get("kit_version") != VERSION:
                diagnostics.append(diagnostic("SVK-TRANSACTION-VERSION", "ERROR", "Transaction version is invalid.", path.relative_to(root)))
            if transaction.get("status") not in ("committed", "rolled_back", "in_progress"):
                diagnostics.append(diagnostic("SVK-TRANSACTION-STATUS", "ERROR", "Unknown transaction status.", path.relative_to(root)))
            elif transaction.get("status") == "in_progress":
                diagnostics.append(diagnostic("SVK-TRANSACTION-INCOMPLETE", "BLOCKED", "Incomplete transaction requires recovery inspection.", path.relative_to(root), remediation="Run svk recover inspect."))
    lock_path = root / LOCK_FILE
    if lock_path.exists():
        lock = _load(lock_path, "SVK-LOCK", diagnostics)
        required = {"schema_version", "kit_version", "owner", "task_id", "state_revision", "created_at", "expires_at"}
        if isinstance(lock, dict) and _exact_fields(lock, required, set(), "SVK-LOCK", diagnostics):
            if lock.get("schema_version") != SCHEMA_VERSION or lock.get("kit_version") != VERSION:
                diagnostics.append(diagnostic("SVK-LOCK-VERSION", "ERROR", "Lease version is invalid.", LOCK_FILE))
            active = [task for task in (state or {}).get("tasks", []) if task.get("status") in ("in_progress", "blocked")]
            if len(active) != 1 or lock.get("task_id") != active[0].get("id") or lock.get("state_revision") != (state or {}).get("state_revision"):
                diagnostics.append(diagnostic("SVK-LOCK-STATE-MISMATCH", "ERROR", "Lease task/revision does not match active state.", LOCK_FILE))
            try:
                expires = parse_utc(lock.get("expires_at"))
                expired = expires <= datetime.now(timezone.utc)
            except (TypeError, ValueError):
                diagnostics.append(diagnostic("SVK-LOCK-EXPIRY", "ERROR", "Lease expires_at is invalid.", LOCK_FILE))
                expired = False
            diagnostics.append(diagnostic("SVK-LOCK-EXPIRED" if expired else "SVK-LOCK-PRESENT", "BLOCKED", "Task lease %s." % ("expired; confirm the owner is inactive before recovery" if expired else "is active"), LOCK_FILE))
    transition = root / TRANSITION_LOCK_FILE
    if transition.exists() and not ignore_transition:
        diagnostics.append(diagnostic("SVK-TRANSITION-LOCK-PRESENT", "BLOCKED", "A short SVK state transition is in progress.", TRANSITION_LOCK_FILE))


def _validate_install(root, diagnostics):
    install = _load(root / INSTALL_FILE, "SVK-INSTALL", diagnostics)
    required = {"schema_version", "owner", "version", "created_at"}
    if isinstance(install, dict) and _exact_fields(install, required, set(), "SVK-INSTALL", diagnostics):
        if install.get("schema_version") != SCHEMA_VERSION or install.get("owner") != "smart-vibe-kit" or install.get("version") != VERSION:
            diagnostics.append(diagnostic("SVK-INSTALL-OWNER", "ERROR", "Install record must identify Smart Vibe Kit %s." % VERSION, INSTALL_FILE))


def check_project(root, scope="governed", ignore_transition=False):
    root = Path(root).resolve()
    if scope not in ("governed", "all-docs"):
        raise ValueError("Check scope must be governed or all-docs.")
    diagnostics = []
    profile = _load(root / PROFILE_FILE, "SVK-PROFILE", diagnostics)
    state = _load(root / STATE_FILE, "SVK-STATE", diagnostics)
    plan = _load(root / PLAN_FILE, "SVK-PLAN", diagnostics)
    verifier_file = _load(root / VERIFIERS_FILE, "SVK-VERIFIERS", diagnostics)
    governance = _load(root / GOVERNANCE_FILE, "SVK-GOVERNANCE", diagnostics)
    interview = _load(root / INTERVIEW_FILE, "SVK-INTERVIEW", diagnostics)
    if profile is not None:
        _validate_profile(profile, diagnostics)
    verifier_ids = set()
    if isinstance(verifier_file, dict):
        if _exact_fields(verifier_file, {"schema_version", "kit_version", "verifiers"}, set(), "SVK-VERIFIERS", diagnostics):
            if verifier_file.get("schema_version") != SCHEMA_VERSION or verifier_file.get("kit_version") != VERSION:
                diagnostics.append(diagnostic("SVK-VERIFIERS-VERSION", "ERROR", "Verifier registry version is invalid.", VERIFIERS_FILE))
            else:
                try:
                    normalized = validate_verifiers(verifier_file.get("verifiers"))
                    if normalized != verifier_file.get("verifiers"):
                        diagnostics.append(diagnostic("SVK-VERIFIERS-NORMALIZATION", "ERROR", "Verifier registry is not in canonical form.", VERIFIERS_FILE))
                    verifier_ids = set(normalized)
                except ValueError as error:
                    diagnostics.append(diagnostic("SVK-VERIFIERS-SHAPE", "ERROR", str(error), VERIFIERS_FILE))
    if isinstance(plan, dict) and isinstance(profile, dict):
        try:
            validate_plan(plan, profile, verifier_ids)
        except ValueError as error:
            diagnostics.append(diagnostic("SVK-PLAN-SHAPE", "ERROR", str(error), PLAN_FILE))
    if state is not None:
        _validate_state(state, profile, plan, verifier_ids, diagnostics)
    if interview is not None:
        _validate_interview(interview, root, profile, diagnostics)
    if isinstance(profile, dict):
        for relative in _required_paths(profile):
            try:
                path = safe_relative_path(root, relative, must_exist=True, expect_file=True)
                if path.stat().st_size == 0:
                    diagnostics.append(diagnostic("SVK-FILE-EMPTY", "ERROR", "Required file is empty.", relative))
            except (OSError, ValueError) as error:
                diagnostics.append(diagnostic("SVK-FILE-MISSING-OR-UNSAFE", "ERROR", str(error), relative))
    _validate_evidence(root, state, verifier_file, diagnostics)
    _validate_governance(root, profile, state, governance, diagnostics, scope)
    _validate_transactions_and_locks(root, state, diagnostics, ignore_transition=ignore_transition)
    _validate_install(root, diagnostics)
    return {"schema_version": SCHEMA_VERSION, "result": overall(diagnostics), "diagnostics": diagnostics}


def package_check(bundle_root):
    bundle_root = Path(bundle_root).resolve()
    diagnostics = []
    expected = ("svk-interview", "svk-refresh", "svk-next", "svk-check")
    expected_hosts = {
        "agents", "codex", "cursor", "claude", "gemini", "antigravity", "grok", "copilot",
        "qwen", "kimi", "opencode", "pi", "goose", "roo", "junie", "cline", "kiro", "windsurf",
    }
    version_path = bundle_root / "VERSION"
    if not version_path.exists() or version_path.read_text(encoding="utf-8").strip() != VERSION:
        diagnostics.append(diagnostic("SVK-PACKAGE-VERSION", "ERROR", "VERSION must be %s." % VERSION, "VERSION"))
    for name in expected:
        root = bundle_root / "skills" / name
        skill_path = root / "SKILL.md"
        yaml_path = root / "agents/openai.yaml"
        entry_path = root / "scripts/entry.py"
        for path in (skill_path, yaml_path, entry_path):
            if not path.is_file() or path.stat().st_size == 0:
                diagnostics.append(diagnostic("SVK-PACKAGE-FILE", "ERROR", "Required skill file is missing or empty.", path.relative_to(bundle_root)))
        if skill_path.exists():
            text = skill_path.read_text(encoding="utf-8")
            if not text.startswith("---\n") and not text.startswith("---\r\n"):
                diagnostics.append(diagnostic("SVK-PACKAGE-FRONTMATTER", "ERROR", "SKILL.md requires YAML frontmatter.", skill_path.relative_to(bundle_root)))
            for required in ("name: %s" % name, 'version: "%s"' % VERSION):
                if required not in text:
                    diagnostics.append(diagnostic("SVK-PACKAGE-METADATA", "ERROR", "Missing metadata: %s" % required, skill_path.relative_to(bundle_root)))
            if any(key in text for key in ("disable-model-invocation:", "disableModelInvocation:")):
                diagnostics.append(diagnostic("SVK-PACKAGE-HOST-KEY", "ERROR", "Canonical source contains host-only metadata.", skill_path.relative_to(bundle_root)))
            if PLACEHOLDER_RE.search(text):
                diagnostics.append(diagnostic("SVK-PACKAGE-PLACEHOLDER", "ERROR", "Skill contains unresolved placeholder text.", skill_path.relative_to(bundle_root)))
        if yaml_path.exists() and "allow_implicit_invocation: false" not in yaml_path.read_text(encoding="utf-8"):
            diagnostics.append(diagnostic("SVK-PACKAGE-IMPLICIT", "ERROR", "OpenAI metadata must disable implicit invocation.", yaml_path.relative_to(bundle_root)))
    if any(bundle_root.rglob("install.py")) or any(bundle_root.rglob("install.ps1")) or any(bundle_root.rglob("install.sh")):
        diagnostics.append(diagnostic("SVK-PACKAGE-SEPARATION", "ERROR", "Installer files must not be stored inside skill/."))
    compatibility = _load(bundle_root / "compatibility.json", "SVK-COMPATIBILITY", diagnostics)
    if isinstance(compatibility, dict):
        hosts = compatibility.get("hosts", {})
        if compatibility.get("schema_version") != SCHEMA_VERSION or compatibility.get("kit_version") != VERSION:
            diagnostics.append(diagnostic("SVK-COMPATIBILITY-VERSION", "ERROR", "Compatibility metadata must use SVK %s." % VERSION, "compatibility.json"))
        try:
            date.fromisoformat(compatibility.get("evaluated_on", ""))
        except (TypeError, ValueError):
            diagnostics.append(diagnostic("SVK-COMPATIBILITY-DATE", "ERROR", "evaluated_on must be an ISO date.", "compatibility.json"))
        for required_host in sorted(expected_hosts):
            if required_host not in hosts:
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-HOST", "ERROR", "Compatibility metadata omits %s." % required_host))
        for host, details in hosts.items():
            if not isinstance(details, dict):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-HOST-SHAPE", "ERROR", "Host %s metadata must be an object." % host))
                continue
            for field in ("user_root", "project_root", "invocation", "status", "runtime_tested"):
                if field not in details:
                    diagnostics.append(diagnostic("SVK-COMPATIBILITY-FIELD", "ERROR", "Host %s requires %s." % (host, field)))
            if not isinstance(details.get("runtime_tested"), bool):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-RUNTIME", "ERROR", "Host %s runtime_tested must be boolean." % host))
            if host != "agents" and not str(details.get("evidence_url", "")).startswith("https://"):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-EVIDENCE", "ERROR", "Host %s requires an HTTPS evidence URL." % host))
    schema_names = (
        "project-profile.schema.json", "project-state.schema.json", "plan.schema.json", "verifiers.schema.json",
        "governance.schema.json", "evidence-index.schema.json", "verification-receipt.schema.json", "interview-session.schema.json",
        "transaction.schema.json", "lease.schema.json", "command-envelope.schema.json",
    )
    for schema_name in schema_names:
        schema = _load(bundle_root / "schemas" / schema_name, "SVK-SCHEMA", diagnostics)
        if isinstance(schema, dict) and (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("additionalProperties") is not False):
            diagnostics.append(diagnostic("SVK-SCHEMA-CONTRACT", "ERROR", "%s must use JSON Schema 2020-12 and reject undeclared top-level properties." % schema_name))
    for path in bundle_root.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            diagnostics.append(diagnostic("SVK-PACKAGE-PYTHON", "ERROR", str(error), path.relative_to(bundle_root)))
    forbidden_names = {"__pycache__", ".pytest_cache", "node_modules", ".DS_Store"}
    for path in bundle_root.rglob("*"):
        relative = path.relative_to(bundle_root)
        if any(part in forbidden_names for part in relative.parts):
            diagnostics.append(diagnostic("SVK-PACKAGE-CACHE", "ERROR", "Generated cache or platform metadata is not allowed.", relative))
            break
        if path.is_symlink():
            diagnostics.append(diagnostic("SVK-PACKAGE-LINK", "ERROR", "Skill bundle must not contain symbolic links.", relative))
            break
    return {"schema_version": SCHEMA_VERSION, "result": overall(diagnostics), "diagnostics": diagnostics}


def manifest_matches(root):
    """Backward-compatible helper; 2.1 uses role-aware governed checks."""
    result = check_project(root)
    return not any(
        item["level"] == "ERROR" and item["code"].startswith(("SVK-INTEGRITY", "SVK-GENERATED", "SVK-GOVERNANCE"))
        for item in result["diagnostics"]
    )
