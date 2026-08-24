# Check diagnostic contract

- `PASS`: all required structural and semantic invariants hold.
- `WARN`: safe to inspect, but a non-blocking concern needs attention.
- `BLOCKED`: an ownership lock or incomplete transaction prevents reliable progression.
- `ERROR`: required artifacts, state, evidence, links, or risk modules are invalid.

Diagnostics have stable `code`, `level`, `message`, and optional `path` fields. The checker is deterministic and does not modify the project.
