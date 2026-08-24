---
name: svk-refresh
description: Reconstruct a token-light Smart Vibe Kit project briefing from machine state, task state, evidence, and semantic checks without changing the project. Use only when the user explicitly invokes SVK Refresh or asks to run this named action after returning to an existing SVK project.
metadata:
  version: "2.0.0"
---

# SVK Refresh

If this skill was selected implicitly, do not act. Explain that SVK Refresh is explicit-only and show the host-appropriate invocation.

When explicitly invoked:

1. Run `python scripts/entry.py --root <project>` before opening broad source context.
2. Treat the action as strictly read-only. Do not repair drift, clear locks, rewrite state, or begin the next task.
3. Read only the artifacts named by the active task if more context is required.
4. Return a compact briefing: project, profile, modules, stage, active task, blocker, exact next action, and check result.
5. If the result is `ERROR` or `BLOCKED`, surface the stable diagnostic codes and stop. Recommend SVK Check; do not mutate the project.

See [the runtime contract](references/contract.md) for the output and read-only guarantees.
