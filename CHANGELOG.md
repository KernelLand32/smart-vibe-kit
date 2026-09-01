# Changelog

## 2.1.0 — 2026-08-31

- Added reviewed goal/deliverable/task plans with deterministic coverage, dependency, sizing, artifact, and verifier validation.
- Added resumable sibling Interview checkpoints and explicit plan approval before scaffolding.
- Replaced agent-authored evidence results with SVK-executed verifiers, index-bound immutable receipt digests, input and artifact freshness checks, and receipt-gated completion.
- Added revision-bound leases, a short transition lock, durable rollback snapshots, explicit recovery inspection, and narrow recovery actions.
- Replaced the flat integrity manifest with role-aware governance for generated, mutable, append-only, immutable, and user-governed files.
- Restricted the default Markdown audit to governed files and added an explicit `all-docs` scope.
- Added deterministic, human-approved 2.0-to-2.1 project migration with user-document preservation, provenance, sibling backup, and rollback.
- Added approved pending-plan insert, split, dependency, and supersede operations.
- Hardened the installer with entry names, transaction-wide installation IDs, destination fingerprints, managed-entry digests, drift refusal, retained backups, link/reparse rejection, and a required 2.0 upgrade gate.
- Added stable JSON command/result envelopes, structured parser errors, and exit-code categories.
- Updated the CI definitions to supported Python versions and current Node 24-based GitHub actions, and added aggregate, extracted-archive, and tag-triggered release gates.
- Rebuilt the Pocket List example with a reviewed multi-task plan and real verifier receipts.
- Added Pi compatibility metadata and corrected Grok's native installation path from current primary documentation.

### Upgrade recommendation

This is a broad bug-fix and stability release. The full set of fixes and improvements is too large to enumerate here, so we recommend updating whenever you can — especially if you have hit unexpected behaviour, edge-case failures, or reliability issues in earlier versions.

Note: this release may include breaking changes and is not guaranteed to be fully backwards compatible with existing projects. If you are upgrading a live project, ask your coding agent to review the changes, update any affected integrations or configuration, and migrate the project to the new version for you.

## 2.0.0 — 2026-08-23

- Split the installer and skill bundle into separate top-level packages.
- Replaced the single bootstrap skill with `svk-interview`, `svk-refresh`, `svk-next`, and `svk-check`.
- Added adaptive module selection and machine-readable `.svk` project state.
- Added transactional scaffold and installer operations with ownership checks.
- Added semantic validation, structured evidence, execution leases, and exact next-task resolution.
- Corrected Codex discovery and explicit invocation metadata.
- Added native/shared destination data for multiple agent harnesses.
- Added cross-platform unit, adversarial, lifecycle, and installer tests.
- Added implementation tasks derived from accepted project goals before the final release gate.
- Tightened interview-answer, profile, task dependency, evidence, lock, manifest, and install-record validation.
- Kept `AGENTS.md` synchronized with the active task after every Next transition.
- Added a complete release checker, reproducible ZIP builder, and active Windows/macOS/Linux CI workflow.
- Rebuilt Pocket List as a live-tested mid-project handoff with working code and tests.
- Corrected Copilot, Cline, Kiro, Windsurf, Cursor, and Codex compatibility paths or invocation guidance against current primary documentation.
