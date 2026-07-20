# Procedures (not slash commands)

**Only slash command:** `/smart-vibe-kit <project idea>` — see [../SKILL.md](../SKILL.md).

Everything below is a **named procedure** for agents after bootstrap. Prefer the copies under the project’s `docs/workflows/` (vendored at bootstrap). Do **not** register these as host slash commands.

| Procedure | Workflow | Purpose |
|-----------|----------|---------|
| constitute | [workflows/constitute.md](workflows/constitute.md) | Create/update constitution + `AGENTS.md` |
| specify | [workflows/specify.md](workflows/specify.md) | Write or update a deliverable spec + claim table |
| authorize | [workflows/authorize.md](workflows/authorize.md) | Open a stage via ADR; freeze prior stage |
| plan-tasks | [workflows/plan-tasks.md](workflows/plan-tasks.md) | Break stage into numbered tasks; update registry |
| implement | [workflows/implement.md](workflows/implement.md) | Execute next `not_started` / `in_progress` task |
| verify | [workflows/verify.md](workflows/verify.md) | Run three gates; collect evidence |
| close-stage | [workflows/close-stage.md](workflows/close-stage.md) | Sign stage gate; archive if phase complete |
| recover | [workflows/recover.md](workflows/recover.md) | Hallucination / wrong-guess response |
| refresh | [workflows/refresh.md](workflows/refresh.md) | Refresh / extend / abort on existing SVK workspace |

---

## Default session bootstrap (after project exists)

1. Read project `AGENTS.md`  
2. Read `docs/tasks.md` — current phase/stage and **Next action**  
3. Read registry row for that action’s task ID  
4. Load only listed deliverables  
5. If Next action names a procedure, open `docs/workflows/{procedure}.md`  

---

## Status vocabulary (shared)

`not_started` · `in_progress` · `blocked` · `done`
