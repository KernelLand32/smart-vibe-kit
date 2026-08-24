---
name: svk-check
description: Run deterministic structural and semantic verification of a Smart Vibe Kit project, including task-state, evidence, links, placeholders, required modules, locks, and transactions. Use only when the user explicitly invokes SVK Check or asks to run this named project audit.
metadata:
  version: "2.0.0"
---

# SVK Check

If this skill was selected implicitly, do not run or repair anything. Explain that SVK Check is explicit-only and show the host-appropriate invocation.

When explicitly invoked:

1. Run `python scripts/entry.py --root <project>`.
2. Report the overall `PASS`, `WARN`, `BLOCKED`, or `ERROR` result and every stable diagnostic code.
3. Distinguish structural absence from semantic disagreement. A non-empty file is not proof that its task, charter, evidence, or links are valid.
4. Do not automatically repair results. Checking authorizes an audit, not edits, lock removal, or transaction recovery.
5. For package maintainers only, `python scripts/entry.py --package --root <skill-bundle>` verifies the distributable skill bundle.

See [the diagnostic contract](references/contract.md) for result meanings.
