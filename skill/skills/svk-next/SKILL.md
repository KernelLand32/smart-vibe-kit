---
name: svk-next
description: Lease, execute, verify, block, or finish exactly one Smart Vibe Kit task with revision-bound ownership and SVK-created receipts. Use only when the user explicitly invokes SVK Next or unmistakably asks to run this named action in an existing SVK project.
metadata:
  version: "2.1.0"
---

# SVK Next

This action is explicit-only. If selected implicitly, show the invocation and do not begin work or acquire a lease.

1. Run `python scripts/entry.py --root <project> show`. Read only the task packet and named scope unless more context is essential.
2. Stop on contract errors, incomplete transactions, orphan receipts, or another lease. Never steal ownership.
3. Begin with `begin --owner <stable-owner>`. For a human gate, also provide `--allow-human-gate --human-actor <label> --human-reason <reason>` after the human acts.
4. Perform only the leased task. The lease does not authorize publishing, production changes, spending, secret access, destructive work, or external communication.
5. Run every required verifier through `verify --owner <owner> --task <id> --verifier <id>`. Do not substitute prose or a hand-written evidence file for a receipt.
6. Finish with `finish --owner <owner> --task <id> --receipts <id,id>`. If unresolved, use `block --reason <specific blocker>`.
7. Report the completed task, receipt IDs, check result, and newly promoted task, then stop. Never execute the promoted task in the same invocation.

See [the contract](references/contract.md) for freshness, leases, receipts, and recovery rules.
