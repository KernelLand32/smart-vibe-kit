# Next runtime contract

SVK Next uses `.svk/locks/next.json` with exclusive creation. The lock records `owner`, `task_id`, `created_at`, and `expires_at`. Expiry is evidence for a human recovery decision, not permission to steal the lock.

Finishing requires a JSON object with:

- `summary`: what was established;
- `commands`: array of executed checks or actions;
- `artifacts`: array of relevant paths or external evidence identifiers;
- `result`: `pass`, `fail`, or `partial`.

Only `pass` may finish a task. Finish verifies the owner and task, appends evidence, marks the active task done, promotes at most one dependency-satisfied task, updates human task views, removes the matching lock, runs the semantic gate, and stops.

Use `clear-lock` only after confirming the prior owner is not active. `--force` is an explicit recovery action and must not be inferred from ordinary use.
