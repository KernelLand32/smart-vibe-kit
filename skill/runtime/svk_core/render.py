"""Render an adaptive, populated project operating system."""

from __future__ import print_function

import copy

from .constants import CORE_DOCUMENTS, MODULE_DOCUMENTS, SCHEMA_VERSION, VERSION
from .util import utc_now


MODULE_TASKS = {
    "research": ("Establish the research baseline", "docs/research/brief.md"),
    "product": ("Confirm requirements and acceptance criteria", "docs/product/requirements.md"),
    "design": ("Define the design and accessibility baseline", "docs/design/system.md"),
    "engineering": ("Validate architecture and interfaces", "docs/engineering/architecture.md"),
    "operations": ("Make delivery and recovery procedures executable", "docs/operations/runbook.md"),
    "security": ("Review threats and data handling", "docs/security/threat-model.md"),
    "regulated": ("Complete control traceability and risk review", "docs/compliance/controls.md"),
    "collaboration": ("Assign ownership and decision paths", "docs/collaboration/ownership.md"),
}


def _bullet(values, fallback):
    values = [str(value).strip() for value in values if str(value).strip()]
    if not values:
        values = [fallback]
    return "\n".join("- %s" % value for value in values)


def _system_task(task_id, title, status, depends_on, human_gate, artifact, acceptance, deliverable, risk="normal"):
    return {
        "id": task_id,
        "kind": "documentation" if task_id != "4.1.1" else "verification",
        "title": title,
        "goal_id": "system",
        "deliverable_id": deliverable,
        "status": status,
        "depends_on": list(depends_on),
        "dependency_rationale": {dependency: "SVK setup prerequisite." for dependency in depends_on},
        "human_gate": bool(human_gate),
        "acceptance": list(acceptance),
        "expected_artifacts": [artifact],
        "scope_hints": [artifact],
        "required_verifiers": [] if task_id == "1.1.2" else ["svk-governed"],
        "risk": risk,
        "size_signals": {
            "subsystems": 1,
            "acceptance_items": len(acceptance),
            "verifier_count": 0 if task_id == "1.1.2" else 1,
            "scope_hints": 1,
        },
        "completion_receipts": [],
    }


def build_tasks(profile, plan, charter_accepted=False):
    tasks = [
        _system_task(
            "1.1.1",
            "Capture the project interview, profile, and approved plan",
            "done",
            [],
            False,
            ".svk/plan.json",
            ["The profile and approved plan pass deterministic validation."],
            "interview",
        ),
        _system_task(
            "1.1.2",
            "Review and accept the project charter",
            "done" if charter_accepted else "in_progress",
            ["1.1.1"],
            True,
            "docs/adr/0001-project-charter.md",
            ["A human attests that scope, goals, non-goals, constraints, modules, and plan are accepted."],
            "charter",
        ),
    ]
    index = 1
    setup_ids = []
    for module in profile["modules"]:
        if module == "core":
            continue
        title, artifact = MODULE_TASKS[module]
        task_id = "2.%d.1" % index
        tasks.append(
            _system_task(
                task_id,
                title,
                "pending",
                ["1.1.2"],
                module in ("security", "regulated"),
                artifact,
                ["The artifact contains project-specific decisions, risks, and observable completion evidence."],
                "module-%s" % module,
                risk="high" if module in ("security", "regulated") else "normal",
            )
        )
        setup_ids.append(task_id)
        index += 1
    for item in plan["tasks"]:
        task = copy.deepcopy(item)
        task["status"] = "pending"
        task["completion_receipts"] = []
        tasks.append(task)
    release_dependencies = [task["id"] for task in plan["tasks"]]
    release_verifiers = list(dict.fromkeys(["svk-governed"] + plan["release_verifiers"]))
    release_task = _system_task(
        "4.1.1",
        "Run the release-readiness verification gate",
        "pending",
        release_dependencies,
        False,
        "docs/verification.md",
        ["Every approved release verifier passes against the current project inputs."],
        "release",
    )
    release_task["required_verifiers"] = release_verifiers
    release_task["size_signals"]["verifier_count"] = len(release_verifiers)
    release_task["dependency_rationale"] = {
        dependency: "Release readiness requires every approved project task to be complete."
        for dependency in release_dependencies
    }
    tasks.append(release_task)
    if charter_accepted:
        completed = {task["id"] for task in tasks if task["status"] == "done"}
        for task in tasks:
            if task["status"] == "pending" and set(task["depends_on"]).issubset(completed):
                task["status"] = "in_progress"
                break
    return tasks


def next_action(tasks):
    active = [task for task in tasks if task["status"] in ("in_progress", "blocked")]
    if len(active) == 1:
        return {"task_id": active[0]["id"], "instruction": active[0]["title"]}
    completed = {task["id"] for task in tasks if task["status"] in ("done", "superseded")}
    for task in tasks:
        if task["status"] == "pending" and set(task["depends_on"]).issubset(completed):
            return {"task_id": task["id"], "instruction": task["title"]}
    return None


def build_state(profile, plan, charter_accepted=False):
    tasks = build_tasks(profile, plan, charter_accepted=charter_accepted)
    action = next_action(tasks)
    return {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "state_revision": 1,
        "project": profile["slug"],
        "stage": "charter" if not charter_accepted else "execution",
        "charter": {"accepted": bool(charter_accepted)},
        "tasks": tasks,
        "next_action": action,
        "authorizations": ([{
            "task_id": "1.1.2",
            "actor": "interview caller",
            "reason": "The caller explicitly used the charter-accepted Interview option.",
            "recorded_at": utc_now(),
            "kind": "cooperative-human-attestation",
        }] if charter_accepted else []),
        "updated_at": utc_now(),
    }


def _task_table(tasks):
    rows = ["| ID | Status | Task | Evidence target |", "|---|---|---|---|"]
    for task in tasks:
        rows.append(
            "| %s | %s | %s | `%s` |"
            % (
                task["id"],
                task["status"],
                task["title"],
                ", ".join(task.get("expected_artifacts", [])) or task.get("no_artifact_reason", "none"),
            )
        )
    return "\n".join(rows)


def _module_summary(profile):
    return ", ".join(profile["modules"])


def _header(title, profile):
    return "# %s\n\nProject: **%s**\n\n" % (title, profile["title"])


def _core_documents(profile, state):
    action = state["next_action"]
    action_text = "Complete" if action is None else "%s — %s" % (action["task_id"], action["instruction"])
    agents = _header("Agent operating contract", profile) + """This repository uses Smart Vibe Kit 2.1 as a small, evidence-backed project operating system.

## Current objective

%s

## Working rules

- Read [.svk/project.json](.svk/project.json), [.svk/plan.json](.svk/plan.json), [.svk/state.json](.svk/state.json), and [docs/tasks.md](docs/tasks.md) before changing project artifacts.
- Work on only the exact `next_action` recorded in state.
- Never infer permission for destructive actions, external publication, spending, secrets, or production changes.
- Run the task's registered SVK verifiers and use their receipt IDs before marking work complete.
- Run the SVK check action after editing operating documents.
- Stop after one task when using SVK Next.

## Selected operating modules

%s

## Navigation

- [Project constitution](docs/constitution.md)
- [Task ledger](docs/tasks.md)
- [Artifact registry](docs/registry.md)
- [Verification strategy](docs/verification.md)
""" % (action_text, _module_summary(profile))

    constitution = _header("Project constitution", profile) + """## Mission

%s

## Goals

%s

## Non-goals

%s

## Constraints

%s

## Decision principles

1. Preserve user intent and data before optimizing speed.
2. Prefer the smallest change that produces inspectable evidence.
3. Separate facts, assumptions, decisions, and unresolved risks.
4. Keep project state portable across models and coding harnesses.
5. Do not mark a task complete without its stated verification evidence.
""" % (
        profile["idea"],
        _bullet(profile["goals"], "Deliver the project idea as an inspectable, maintainable result."),
        _bullet(profile["non_goals"], "Avoid expanding scope beyond the accepted charter."),
        _bullet(profile["constraints"], "Preserve portability and make important assumptions explicit."),
    )

    tasks = _header("Task ledger", profile) + """The machine-readable source of truth is [`.svk/state.json`](../.svk/state.json). This table mirrors every task ID and status for humans.

%s

## Execution rule

Exactly one task may be active. Dependencies may branch, but SVK 2.1 still leases one task at a time. SVK Next advances that task and then stops.
""" % _task_table(state["tasks"])

    all_paths = list(CORE_DOCUMENTS)
    for module in profile["modules"]:
        all_paths.extend(MODULE_DOCUMENTS.get(module, ()))
    registry_rows = ["| Artifact | Purpose |", "|---|---|"]
    for path in all_paths:
        if path == "AGENTS.md":
            link = "../AGENTS.md"
        elif path.startswith("docs/"):
            link = path[len("docs/") :]
        else:
            link = path
        registry_rows.append("| [%s](%s) | Governed project artifact |" % (path, link))
    registry = _header("Artifact registry", profile) + "\n".join(registry_rows) + "\n"

    charter_status = "accepted" if state["charter"]["accepted"] else "proposed"
    charter = _header("ADR 0001: Project charter", profile) + """Status: **%s**

## Context

%s

## Decision

Use the **%s** SVK profile with these modules: %s.

## Consequences

- The scaffold grows from project signals rather than a fixed file quota.
- Machine-readable state controls task progression.
- A human must accept this charter before autonomous task progression.

## Acceptance

Begin with an explicit cooperative human attestation, then finish task 1.1.2 after reviewing this document. The attestation records what the caller says happened; it is not authenticated identity.
""" % (charter_status, profile["idea"], profile["profile"], _module_summary(profile))

    verification = _header("Verification strategy", profile) + """## Required gates

1. Structure: all profile-required artifacts exist and contain substantive text.
2. State: task IDs, dependencies, status, and `next_action` agree.
3. Evidence: every required verifier has a fresh SVK-created receipt bound to the task inputs.
4. References: relative Markdown links resolve inside the project.
5. Safety: no incomplete transaction or live lock remains.

## Evidence format

SVK stores immutable verifier receipts under `.svk/evidence/runs/` and indexes them in `.svk/evidence/index.json`. Human notes and cooperative attestations may add context but do not replace a required verifier receipt.

## Release gate

The project is release-ready only when the SVK Check result is `PASS` and the release task has fresh passing receipts for every configured release verifier.
"""
    return {
        "AGENTS.md": agents,
        "docs/constitution.md": constitution,
        "docs/tasks.md": tasks,
        "docs/registry.md": registry,
        "docs/adr/0001-project-charter.md": charter,
        "docs/verification.md": verification,
    }


MODULE_PURPOSES = {
    "research": (
        "Research baseline",
        "Separate current evidence from assumptions before implementation.",
        "Record source title, publisher, date, URL, claim supported, and retrieval date. Prefer primary sources and note unresolved disagreements.",
    ),
    "product": (
        "Product definition",
        "Translate the idea into user outcomes that can be accepted or rejected.",
        "For each outcome, name the user, situation, observable behavior, failure behavior, and acceptance evidence.",
    ),
    "design": (
        "Design baseline",
        "Keep interaction, visual, responsive, and accessibility decisions coherent.",
        "Define information hierarchy, component states, keyboard behavior, contrast expectations, empty/error states, and narrow-screen behavior.",
    ),
    "engineering": (
        "Engineering baseline",
        "Make boundaries, data flow, failure modes, and verification points explicit.",
        "Describe components, owned data, interfaces, trust boundaries, idempotency, observability, and test seams before implementation grows.",
    ),
    "operations": (
        "Operations baseline",
        "Make build, release, recovery, and incident actions reproducible.",
        "Record prerequisites, environment assumptions, health checks, rollout steps, rollback triggers, backup/restore checks, and ownership.",
    ),
    "security": (
        "Security baseline",
        "Identify assets, actors, boundaries, abuse cases, and mitigations early.",
        "Classify data, minimize retention, constrain secrets, validate inputs, authorize every sensitive operation, and preserve audit evidence.",
    ),
    "regulated": (
        "Compliance baseline",
        "Trace obligations to controls, evidence, owners, and residual risk.",
        "For each obligation, record scope, control, implementation artifact, verification evidence, owner, review cadence, and exception path.",
    ),
    "collaboration": (
        "Collaboration baseline",
        "Make ownership, review paths, and durable decisions visible to the team.",
        "Assign one accountable owner per area, define reviewers, record decisions with context, and make handoffs include state plus evidence.",
    ),
}


def _module_documents(profile):
    result = {}
    for module in profile["modules"]:
        if module == "core":
            continue
        title, purpose, method = MODULE_PURPOSES[module]
        for index, path in enumerate(MODULE_DOCUMENTS[module]):
            artifact_title = path.rsplit("/", 1)[-1].replace(".md", "").replace("-", " ").title()
            result[path] = _header("%s — %s" % (title, artifact_title), profile) + """## Purpose

%s

## Project application

%s

## Working method

%s

## Verification expectations

- Decisions refer to the project idea and accepted scope.
- Claims that can become stale include dated evidence.
- Risks identify an owner, mitigation, and observable completion signal.
- The related task is complete only after its required verifier receipts are recorded by SVK.

## Initial direction

This artifact was selected because the interview activated the **%s** module. Refine it during its assigned task; preserve confirmed facts and label new assumptions.
""" % (purpose, profile["idea"], method, module)
    return result


def render_documents(profile, state):
    documents = _core_documents(profile, state)
    documents.update(_module_documents(profile))
    return documents
