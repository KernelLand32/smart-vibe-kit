# Next runtime contract

`begin` creates a revision-bound lease in `.svk/locks/next.json`. A short transition lock serializes state changes, preventing two callers from choosing the same task between a check and a write. Lease expiry is evidence for recovery review, not permission to steal ownership.

Human gates require explicit permission, a human actor label, and a reason. These are cooperative attestations, not authenticated identity.

`verify` runs a registered verifier without a shell, with a timeout, constrained environment, captured output, input fingerprints, and artifact checks. It creates a receipt under `.svk/evidence/runs/<receipt-id>/` and indexes its canonical path and SHA-256 digest. A task finishes only when every required verifier has a passing, task-bound, untampered, fresh receipt. Prose or manually created evidence JSON is not accepted.

`finish` validates the lease, revision, authorization, receipt coverage, and freshness; advances exactly one task; journals the transition; releases the lease; and stops. `block` records a specific reason. `clear-lock --force` is explicit recovery and must not be inferred from ordinary use.
