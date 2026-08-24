# Verification strategy

Project: **Pocket List**

## Required gates

1. Structure: all profile-required artifacts exist and contain substantive text.
2. State: task IDs, dependencies, status, and `next_action` agree.
3. Evidence: every completed task has a corresponding evidence record.
4. References: relative Markdown links resolve inside the project.
5. Safety: no incomplete transaction or live lock remains.

## Evidence format

Evidence is JSON with `summary`, `commands`, `artifacts`, and `result` fields. Store one record per completed task in `.svk/evidence.jsonl`.

## Release gate

The project is release-ready only when the SVK Check result is `PASS` and task 3.1.1 has evidence.
