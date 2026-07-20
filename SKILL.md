---
name: smart-vibe-kit
description: >-
  Bootstraps an execution-grounded project process from a project idea via
  /smart-vibe-kit. MUST create the full AGENTS.md + docs/ + scripts/ tree
  populated from the idea (not blank stubs). Runs a research gate when the
  domain needs current grounding. Use when starting a greenfield project,
  empty workspace, or when the user invokes /smart-vibe-kit.
license: Apache-2.0
compatibility: >-
  Cursor Agent Skills, Claude Code skills/commands, Codex/Agent Skills-compatible
  loaders. Needs filesystem write access; web research needs network.
metadata:
  version: "1.0.0"
  trigger: "/smart-vibe-kit"
  openstandard: "agentskills.io"
argument-hint: "<project idea>"
disable-model-invocation: true
---

# /smart-vibe-kit — bootstrap from a project idea

You are **running** Smart Vibe Kit against the **current workspace**.

**Only slash command in this kit:** `/smart-vibe-kit`. Do not register or invent other slash commands. After bootstrap, ongoing work uses project `docs/workflows/` procedures by name.

**Hard requirement:** before you finish, the workspace must contain the **entire** tree in [references/required-structure.md](references/required-structure.md). Creating only `AGENTS.md` or a partial `docs/` folder is a failed run — keep writing until the checklist passes.

## Arguments

Treat everything after the command name as the **project idea**:

| Source | How to read |
|--------|-------------|
| Host `$ARGUMENTS` | Use when provided |
| Chat after `/smart-vibe-kit` | Remaining user text |
| Missing | Ask once for a 1–3 sentence idea; do not invent a product |

Example: `/smart-vibe-kit offline-first habit tracker for ADHD with local encryption`

## Non-negotiables

- Repo docs beat training data after bootstrap  
- Do **not** invent APIs, versions, hashes, market stats, or legal claims — tag or research  
- **Real first-pass content** from the idea — no `{placeholder}` soup  
- Stage 1 = **Exploration** unless user explicitly skips to build  
- Only authorize/bootstrap doc tasks may be marked `done` (with `waiver: process`)  
- Do not scaffold application source code unless the user asked for code in the same message  

## Procedure (execute in order)

### 0. Load this package

Open these files from **this skill directory** (same folder as this `SKILL.md`):

1. [references/required-structure.md](references/required-structure.md) — mandatory output tree  
2. [references/research-gate.md](references/research-gate.md)  
3. [references/bootstrap.md](references/bootstrap.md)  
4. [references/constitution.md](references/constitution.md)  
5. Templates under [assets/templates/](assets/templates/) as you write each file  

On Cursor user installs: `~/.cursor/skills/smart-vibe-kit/` (Windows: `%USERPROFILE%\.cursor\skills\smart-vibe-kit\`).

### 1. Workspace check

1. Resolve workspace root.  
2. If `AGENTS.md` + `docs/tasks.md` + `docs/registry.md` + `docs/adr/0002-authorize-phase1-stage1.md` all exist, stop and ask: **refresh / extend / abort**, then follow [references/workflows/refresh.md](references/workflows/refresh.md) (or project `docs/workflows/refresh.md` if already vendored).  
3. If foreign heavy app repo (see bootstrap.md), ask before writing.  
4. Otherwise continue.

### 2. Research gate (mandatory)

Apply [references/research-gate.md](references/research-gate.md).

- If research is **required**: run web research (do not skip on “ask once” alone — see research-gate hard stops).  
- If **recommended**: announce reasons + topics; run research unless user declines once (then label assumptions).  
- Always write `docs/research/profile.md` and `docs/research/landscape.md`.  

### 3. Bootstrap — full tree (mandatory)

Follow [references/bootstrap.md](references/bootstrap.md) **and** every path in [references/required-structure.md](references/required-structure.md).

Copy templates, vendor checklists + workflows into `docs/`, customize constitution Articles IV–VI, write ≥2 domain areas, copy `scripts/verify_structure.py`.

### 4. Verify (mandatory)

```bash
python scripts/verify_structure.py --root . --bootstrap
```

Fix until exit 0.

### 5. Hand off

Report: name + one-liner, research yes/no, domain walls, **Next action**, list of paths created. Remind: only `/smart-vibe-kit` is a slash command; use `docs/workflows/` next.

## Ongoing use

Prefer the **project** `AGENTS.md` + `docs/`. After bootstrap, open **project** `docs/workflows/README.md` (not skill templates). Skill-side procedure map: [references/commands.md](references/commands.md).
