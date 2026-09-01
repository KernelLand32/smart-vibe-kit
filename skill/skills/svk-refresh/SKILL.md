---
name: svk-refresh
description: Reconstruct a compact Smart Vibe Kit briefing from governed project state, the approved plan, evidence receipts, and deterministic diagnostics without changing the project. Use only when the user explicitly invokes SVK Refresh or asks to run this named action.
metadata:
  version: "2.1.0"
---

# SVK Refresh

This action is explicit-only and strictly read-only.

1. Run `python scripts/entry.py --root <project>` before opening broad source context.
2. Do not repair drift, clear leases, recover transactions, rewrite state, or begin work.
3. Read only the active task's named artifacts when more context is needed.
4. Return project, profile, modules, stage, state revision, active task, blocker, exact next action, and check result.
5. Surface stable diagnostic codes for `ERROR` or `BLOCKED` and stop. Recommend SVK Check without mutating the project.

See [the contract](references/contract.md) for the output and read-only guarantee.
