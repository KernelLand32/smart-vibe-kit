# Task ledger

Project: **Pocket List**

The machine-readable source of truth is [`.svk/state.json`](../.svk/state.json). This table mirrors every task ID and status for humans.

| ID | Status | Task | Evidence target |
|---|---|---|---|
| 1.1.1 | done | Capture the project interview, profile, and approved plan | `.svk/plan.json` |
| 1.1.2 | done | Review and accept the project charter | `docs/adr/0001-project-charter.md` |
| 2.1.1 | done | Confirm requirements and acceptance criteria | `docs/product/requirements.md` |
| 3.1.1 | done | Implement atomic task creation and JSON persistence | `pocket_list.py` |
| 3.1.2 | done | Lock in add-command persistence regressions | `tests/test_pocket_list.py` |
| 3.2.1 | in_progress | Implement restart-safe unfinished-task listing | `pocket_list.py, tests/test_pocket_list.py` |
| 3.3.1 | pending | Implement lossless task completion | `pocket_list.py, tests/test_pocket_list.py` |
| 4.1.1 | pending | Run the release-readiness verification gate | `docs/verification.md` |

## Execution rule

Exactly one task may be active. Dependencies may branch, but SVK 2.1 still leases one task at a time. SVK Next advances that task and then stops.
