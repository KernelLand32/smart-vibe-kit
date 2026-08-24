# Task ledger

Project: **Pocket List**

The machine-readable source of truth is [`.svk/state.json`](../.svk/state.json). This table mirrors every task ID and status for humans.

| ID | Status | Task | Evidence target |
|---|---|---|---|
| 1.1.1 | done | Capture the project interview and adaptive profile | `.svk/project.json` |
| 1.1.2 | done | Review and accept the project charter | `docs/adr/0001-project-charter.md` |
| 2.1.1 | done | Confirm requirements and acceptance criteria | `docs/product/requirements.md` |
| 3.1.1 | done | Implement and verify: Add a task and save it locally | `Implementation and tests for: Add a task and save it locally` |
| 3.2.1 | in_progress | Implement and verify: List unfinished tasks after restarting the program | `Implementation and tests for: List unfinished tasks after restarting the program` |
| 3.3.1 | pending | Implement and verify: Mark a task complete without losing other tasks | `Implementation and tests for: Mark a task complete without losing other tasks` |
| 4.1.1 | pending | Run the release-readiness verification gate | `docs/verification.md` |

## Execution rule

Exactly one task may be active. SVK Next performs or advances that task and then stops.
