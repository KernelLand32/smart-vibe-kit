---
name: svk-interview
description: Interview the user about a greenfield project, checkpoint the interview, propose and review a bounded execution plan, then create an adaptive Smart Vibe Kit scaffold. Use only when the user explicitly invokes SVK Interview or unmistakably asks to run this named action in a new project.
metadata:
  version: "2.1.0"
---

# SVK Interview

This action is explicit-only. If selected implicitly, explain how to invoke it and do not modify files.

1. Inspect the target without modifying it. Refuse a filesystem root, home folder, existing project, or partial SVK folder.
2. Start or resume the durable sibling checkpoint with `python scripts/entry.py --root <project> start --idea <idea>` or `show`.
3. Ask only questions that materially affect users, outcomes, exclusions, constraints, risk, modules, acceptance, task boundaries, dependencies, artifacts, or verification. Save each completed section with `checkpoint`.
4. Propose a structured plan that covers every accepted goal through deliverables and bounded `3.x.x` tasks. Each task needs acceptance criteria, scope hints, expected artifacts or a no-artifact reason, dependencies with rationale, risk, size signals, and registered verifiers.
5. Present the profile, modules, plan, sizing exceptions, and meaningful assumptions. Do not set `plan_approved` until a human explicitly accepts the proposal.
6. Write the final answers JSON outside the target and run `python scripts/entry.py --root <project> scaffold --answers <json>`. Add `--charter-accepted` only when a human explicitly reviewed and accepted the charter during Interview.
7. Report the generated profile, modules, files, approved plan, exact next action, and check result.

The model proposes project-specific work. The deterministic runtime validates coverage, boundedness, dependencies, verifiers, safety, and the committed scaffold. See [the contract](references/contract.md).
