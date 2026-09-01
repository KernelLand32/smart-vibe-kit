# Pocket List worked example

Pocket List is the worked example for Smart Vibe Kit 2.1. It starts with a small project idea, shows why Interview selected a Lean scaffold, records a reviewed execution plan, and follows several bounded Next tasks into working code.

The example intentionally stops partway through implementation. The `add` command works and is tested; the active task is to implement `list`. That makes Refresh and Next useful when you open the folder instead of presenting a finished project with nowhere to continue.

## Project idea

Build a small offline command-line task list for one person. The first release must add a task, list unfinished tasks after restarting, and mark a task complete. It uses Python's standard library, stores human-readable JSON locally, and excludes accounts, sync, collaboration, and graphical interfaces.

The complete structured input is in [interview-answers.json](interview-answers.json).

## What Interview decided

Interview selected the **Lean** profile with the **Core** and **Product** areas, producing 16 managed scaffold artifacts. “Lean” means this low-risk, local project receives the core operating documents plus product requirements; it does not mean fewer implementation tasks or weaker verification.

- Product is needed because the command-line behavior requires clear requirements and observable acceptance examples.
- Design is not needed because there is no graphical interface.
- Engineering and Operations are not needed because the first release has no service, deployment, database server, or external integration.
- Security, Research, Regulated, and Collaboration are not needed for this low-risk, single-person, local-only scope.

Those decisions are recorded in [`.svk/project.json`](.svk/project.json). The reviewed goal-to-deliverable-to-task structure is recorded separately in [`.svk/plan.json`](.svk/plan.json), so another harness does not have to reconstruct it from chat history.

## What the Next runs accomplished

1. **Task `1.1.2` — charter:** the project boundary, constraints, and selected areas were reviewed and accepted.
2. **Task `2.1.1` — product definition:** the rough idea became seven requirements, explicit exclusions, storage decisions, and acceptance examples.
3. **Task `3.1.1` — implementation:** `add` was implemented with strict data validation and atomic JSON persistence.
4. **Task `3.1.2` — focused verification:** four persistence regressions were run after implementation instead of folding all work into one vague goal task.

SVK ran the registered checks itself and stored immutable receipts under [`.svk/evidence/runs`](.svk/evidence/runs). The index in [`.svk/evidence/index.json`](.svk/evidence/index.json) binds each receipt to its task and verifier. Each Next run completed one task, promoted one dependency-ready task, and stopped.

## Current handoff

Refresh reports:

```text
Project: Pocket List
Profile: Lean
Areas: Core, Product
Stage: execution
Active task: 3.2.1 — Implement restart-safe unfinished-task listing
Blocker: none
Check: PASS
```

A new agent can now read the active task, [requirements](docs/product/requirements.md), [acceptance examples](docs/product/acceptance.md), existing [implementation](pocket_list.py), and [tests](tests/test_pocket_list.py) without reconstructing the project from chat history.

## Verify the example

From the release root:

```text
python -B skill/runtime/svk.py refresh --root examples/pocket-list
python -B skill/runtime/svk.py check --root examples/pocket-list
python -B -m unittest discover -s examples/pocket-list/tests -v
python -B examples/pocket-list/pocket_list.py --data <temporary-file> add "Buy tea"
```

Refresh and Check return `PASS`; the test suite contains four passing tests. Replace `<temporary-file>` with a disposable path suitable for your operating system when running the smoke command.

Do not run Next against the checked-in example unless you intentionally want to advance its stored task state.

## Suggested reading order

1. [interview-answers.json](interview-answers.json) — the facts supplied to Interview.
2. [`.svk/project.json`](.svk/project.json) — the resulting profile and selected areas.
3. [`docs/adr/0001-project-charter.md`](docs/adr/0001-project-charter.md) — the accepted scope.
4. [`docs/tasks.md`](docs/tasks.md) — completed, active, and pending work.
5. [`docs/product/requirements.md`](docs/product/requirements.md) — the product decisions produced by one Next task.
6. [`pocket_list.py`](pocket_list.py) and [`tests/test_pocket_list.py`](tests/test_pocket_list.py) — the first implemented goal and its evidence-producing tests.
7. [`.svk/plan.json`](.svk/plan.json) — the approved deliverables, bounded tasks, dependencies, and verifier requirements.
8. [`.svk/evidence/index.json`](.svk/evidence/index.json) — the receipt index behind completed-task claims.
9. [`.svk/state.json`](.svk/state.json) — the exact revisioned machine-readable handoff.
