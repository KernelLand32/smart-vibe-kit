# Check diagnostic contract

- `PASS`: all required structural and semantic invariants hold.
- `WARN`: safe to inspect, but a non-blocking concern needs attention.
- `BLOCKED`: a live lease, incomplete transaction, orphan receipt, or task blocker prevents reliable progression.
- `ERROR`: a schema, plan, state, governed artifact, receipt, link, or required risk module is invalid.

Diagnostics have stable `code`, `level`, `category`, `message`, and optional `path`, JSON pointer, and remediation fields. The default scope checks governed Markdown; `all-docs` extends content checks to every Markdown file. The checker is deterministic and does not modify the project.
