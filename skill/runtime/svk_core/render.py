"""Render an adaptive, populated project operating system."""

from __future__ import print_function

from .constants import CORE_DOCUMENTS, MODULE_DOCUMENTS, VERSION
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


def build_tasks(profile, charter_accepted=False):
    tasks = [
        {
            "id": "1.1.1",
            "title": "Capture the project interview and adaptive profile",
            "status": "done",
            "depends_on": [],
            "human_gate": False,
            "artifact": ".svk/project.json",
            "verification": "The project profile passes SVK semantic validation.",
        },
        {
            "id": "1.1.2",
            "title": "Review and accept the project charter",
            "status": "done" if charter_accepted else "in_progress",
            "depends_on": ["1.1.1"],
            "human_gate": True,
            "artifact": "docs/adr/0001-project-charter.md",
            "verification": "A human confirms scope, goals, non-goals, constraints, and selected modules.",
        },
    ]
    index = 1
    previous = "1.1.2"
    for module in profile["modules"]:
        if module == "core":
            continue
        title, artifact = MODULE_TASKS[module]
        task_id = "2.%d.1" % index
        tasks.append(
            {
                "id": task_id,
                "title": title,
                "status": "pending",
                "depends_on": [previous],
                "human_gate": module in ("security", "regulated"),
                "artifact": artifact,
                "verification": "The artifact contains project-specific decisions and evidence.",
            }
        )
        previous = task_id
        index += 1
    implementation_previous = previous
    for goal_index, goal in enumerate(profile.get("goals", []), 1):
        task_id = "3.%d.1" % goal_index
        tasks.append(
            {
                "id": task_id,
                "title": "Implement and verify: %s" % goal,
                "status": "pending",
                "depends_on": [implementation_previous],
                "human_gate": False,
                "artifact": "Implementation and tests for: %s" % goal,
                "verification": "The goal has observable passing evidence and respects the accepted constraints.",
            }
        )
        implementation_previous = task_id
    if not profile.get("goals"):
        tasks.append(
            {
                "id": "3.1.1",
                "title": "Define and implement the first useful project increment",
                "status": "pending",
                "depends_on": [implementation_previous],
                "human_gate": False,
                "artifact": "Project implementation and tests",
                "verification": "A useful increment is implemented with observable passing evidence.",
            }
        )
        implementation_previous = "3.1.1"
    tasks.append(
        {
            "id": "4.1.1",
            "title": "Run the release-readiness verification gate",
            "status": "pending",
            "depends_on": [implementation_previous],
            "human_gate": False,
            "artifact": "docs/verification.md",
            "verification": "All required checks pass and evidence is recorded.",
        }
    )
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
    completed = {task["id"] for task in tasks if task["status"] == "done"}
    for task in tasks:
        if task["status"] == "pending" and set(task["depends_on"]).issubset(completed):
            return {"task_id": task["id"], "instruction": task["title"]}
    return None


def build_state(profile, charter_accepted=False):
    tasks = build_tasks(profile, charter_accepted=charter_accepted)
    action = next_action(tasks)
    return {
        "schema_version": "2.0",
        "kit_version": VERSION,
        "project": profile["slug"],
        "stage": "charter" if not charter_accepted else "execution",
        "charter": {"accepted": bool(charter_accepted)},
        "tasks": tasks,
        "next_action": action,
        "authorizations": [],
        "updated_at": utc_now(),
    }


def _task_table(tasks):
    rows = ["| ID | Status | Task | Evidence target |", "|---|---|---|---|"]
    for task in tasks:
        rows.append(
            "| %s | %s | %s | `%s` |"
            % (task["id"], task["status"], task["title"], task["artifact"])
        )
    return "\n".join(rows)


def _module_summary(profile):
    return ", ".join(profile["modules"])


def _header(title, profile):
    return "# %s\n\nProject: **%s**\n\n" % (title, profile["title"])


def _core_documents(profile, state):
    action = state["next_action"]
    action_text = "Complete" if action is None else "%s — %s" % (action["task_id"], action["instruction"])
    agents = _header("Agent operating contract", profile) + """This repository uses Smart Vibe Kit 2.0 as a small, evidence-backed project operating system.

## Current objective

%s

## Working rules

- Read [.svk/project.json](.svk/project.json), [.svk/state.json](.svk/state.json), and [docs/tasks.md](docs/tasks.md) before changing project artifacts.
- Work on only the exact `next_action` recorded in state.
- Never infer permission for destructive actions, external publication, spending, secrets, or production changes.
- Record verifiable evidence before marking work complete.
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

Exactly one task may be active. SVK Next performs or advances that task and then stops.
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

Accept with `svk-next finish --task 1.1.2 --owner <owner> --evidence <file>` after reviewing this document.
""" % (charter_status, profile["idea"], profile["profile"], _module_summary(profile))

    verification = _header("Verification strategy", profile) + """## Required gates

1. Structure: all profile-required artifacts exist and contain substantive text.
2. State: task IDs, dependencies, status, and `next_action` agree.
3. Evidence: every completed task has a corresponding evidence record.
4. References: relative Markdown links resolve inside the project.
5. Safety: no incomplete transaction or live lock remains.

## Evidence format

Evidence is JSON with `summary`, `commands`, `artifacts`, and `result` fields. Store one record per completed task in `.svk/evidence.jsonl`.

## Release gate

The project is release-ready only when the SVK Check result is `PASS` and task 3.1.1 has evidence.
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
- The related task is complete only after evidence is appended to `.svk/evidence.jsonl`.

## Initial direction

This artifact was selected because the interview activated the **%s** module. Refine it during its assigned task; preserve confirmed facts and label new assumptions.
""" % (purpose, profile["idea"], method, module)
    return result


def render_documents(profile, state):
    documents = _core_documents(profile, state)
    documents.update(_module_documents(profile))
    return documents
