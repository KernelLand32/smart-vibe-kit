---
name: svk-next
description: Show, begin, block, or finish exactly one Smart Vibe Kit task using an ownership lock and structured evidence. Use only when the user explicitly invokes SVK Next or unmistakably asks to run this named action in an existing SVK project.
metadata:
  version: "2.0.0"
---

# SVK Next

If this skill was selected implicitly, do not begin work or acquire a lock. Explain that SVK Next is explicit-only and show the host-appropriate invocation.

When explicitly invoked:

1. Run `python scripts/entry.py --root <project> show` and read only the returned task packet plus its named artifacts.
2. Stop on state errors, incomplete transactions, or an existing lock. Never steal or silently clear ownership.
3. Begin with `python scripts/entry.py --root <project> begin --owner <stable-owner>`. A human-gate task also requires `--allow-human-gate` after the human has agreed to perform that gate.
4. Perform only that task. Do not broaden authorization to publishing, production, spending, secrets, destructive operations, or external communications.
5. Put the task's observed evidence in a JSON file following [the runtime contract](references/contract.md).
6. Finish with `python scripts/entry.py --root <project> finish --owner <owner> --task <id> --evidence <json>`. If incomplete, use `block --reason <specific blocker>`.
7. Report what changed, evidence, the newly promoted task, and then stop. Never execute the promoted task in the same invocation.
