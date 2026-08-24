---
name: svk-interview
description: Interview the user about a greenfield project, infer a risk-appropriate project profile, and create an adaptive Smart Vibe Kit scaffold. Use only when the user explicitly invokes SVK Interview or unmistakably asks to run this named action in a new or unscaffolded project.
metadata:
  version: "2.0.0"
---

# SVK Interview

If this skill was selected implicitly, do not create or change files. Explain that SVK Interview is explicit-only and show the host-appropriate invocation.

When explicitly invoked:

1. Inspect the target folder without modifying it. Refuse a filesystem root or the user's home directory.
2. Use the user's idea as the starting point. Infer low-risk facts from repository evidence and ask only the questions whose answers materially affect scope, risk, modules, or acceptance.
3. Cover outcomes, non-goals, platforms, integrations, deployment, UI, team size, current-research needs, sensitive data, safety, money, and regulation. Never silently infer away a safety module.
4. Summarize the proposed title, goals, constraints, profile, selected modules, and meaningful assumptions. Charter review happens after the scaffold is created.
5. Write the structured answers to a temporary JSON file outside the target project. Follow [the runtime contract](references/contract.md).
6. Run `python scripts/entry.py --root <project> --answers <json>`.
7. Report the generated profile, modules, artifact count, exact next action, and semantic-check result.

The model chooses the needed operating modules; the deterministic runtime chooses the corresponding files. File count is an outcome, never a quota.
