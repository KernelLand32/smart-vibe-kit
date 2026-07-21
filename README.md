# Smart Vibe Kit

**1.0.0** · `/smart-vibe-kit <project idea>`

An [Agent Skills](https://agentskills.io/specification) package for Cursor, Claude Code, Codex, Gemini CLI, and other hosts that load skills from `.agents/skills` or `.claude/skills`.

You run one slash command with a project idea. It writes a process into the workspace (`AGENTS.md`, tasks, ADRs, specs with labeled claims, checklists, a structure checker). It does **not** scaffold application code unless you ask for that in the same message.

Needs **Python 3** for install and verify scripts.

---

## Why

Agents are good at sounding done. They are worse at:

- separating known facts from guesses (APIs, versions, compliance claims)
- reading only the docs for the current task instead of the whole tree
- agreeing what “done” means without tests and something that actually ran
- opening the next stage only when you said so
- fixing wrong guesses in the docs instead of quietly rewriting chat history

This kit bootstraps files that make those habits the default for the project. It does not make the model honest by magic—if the agent ignores the docs, you still get garbage.

Best fit: **new or mostly empty repo** and a clear idea. Not a “convert my legacy monorepo” tool.

---

## Rules (after bootstrap)

1. **Repo beats memory.** Project docs win. Missing fact → stop and flag it. Don’t invent a neat default.
2. **Read only what you need.** `docs/registry.md` lists the minimum docs per task. Don’t dump everything into context.
3. **“Done” means it ran.** Docs match reality, tests pass, runtime evidence exists (narrow waivers for explore/process-only work). Prose alone doesn’t finish implementation.
4. **Stages open on purpose.** Exploration / design / build open through ADRs—not because the agent “felt” the next step.
5. **Wrong guesses become decisions.** Fix the spec, record an ADR or registry note, preferably add a test or structural check. No silent patches.

---

## Use it

### 1. Install

```bash
# Shared install (recommended)
python scripts/install.py --target agents --scope user

# Or every supported host (paths deduped)
python scripts/install.py --target all --scope user
```

```powershell
.\scripts\install.ps1 -Target agents -Scope user
```

```bash
./scripts/install.sh agents user
```

| Target | User path | Project path |
|--------|-----------|--------------|
| **agents** | `~/.agents/skills/smart-vibe-kit/` | `.agents/skills/smart-vibe-kit/` |
| cursor | `~/.cursor/skills/…` | `.cursor/skills/…` |
| claude | `~/.claude/skills/…` | `.claude/skills/…` |
| codex | `~/.codex/skills/…` | `.agents/skills/…` |
| gemini | `~/.gemini/skills/…` | `.gemini/skills/…` |

```bash
python scripts/install.py --list
python scripts/install.py --what-if --target all
python scripts/install.py --uninstall --target agents --scope user
```

More detail: [install.md](install.md), [adapters/](adapters/).

### 2. Write a usable idea

Text after `/smart-vibe-kit` seeds the charter and Stage 1. Vague idea → vague or invented docs. Aim for **2–6 sentences** (or tight bullets).

Include when you can: who it’s for, what v1 actually delivers, app vs library vs plugin, hard constraints, non-goals, what must stay separate (domain walls), risks, optional stack preference (say “prefer”, not “we use X 4.2” without a source).

```text
/smart-vibe-kit offline-first habit tracker for adults with ADHD who abandon cloud apps.
v1: log habits on one device with a locally encrypted store; no account required.
Non-goals: social feed, coaches, sync, clinical treatment or diagnosis claims.
Walls: product/UX must not invent crypto APIs; engineering must not redefine user outcomes.
Risks: encryption UX friction; platform (mobile vs desktop) undecided.
```

Weak: `/smart-vibe-kit habit app` — the agent will guess the rest.

Also say so when true: regulated domain; must integrate a named host/API; skip live research / you pasted sources.

### 3. Run the command

```text
/smart-vibe-kit offline-first habit tracker for ADHD with local encryption
```

Only runs when you invoke it. Roughly:

1. Research gate when the domain needs current sources; always write research profile + landscape  
2. Create the full tree in [references/required-structure.md](references/required-structure.md)  
3. Accept Phase 1 · Stage 1 Exploration (invoke = explore, not ship fiction)  
4. Vendor workflows + checklists  
5. `python scripts/verify_structure.py --root . --bootstrap` until exit 0  
6. Hand you one **Next action**

After that, follow the project’s `AGENTS.md` and `docs/`. Ongoing work uses procedures under `docs/workflows/` (specify, authorize, implement, verify, …)—no extra slash commands.

If the workspace is already Smart Vibe Kit, invoke again and choose **refresh / extend / abort** ([refresh workflow](references/workflows/refresh.md)).

### 4. Normal session

1. `AGENTS.md` / `docs/constitution.md`  
2. `docs/tasks.md` → **Next action**  
3. Only the registry docs for that task  
4. The named workflow under `docs/workflows/`  
5. Mark `done` only when the gates (or an honest explore waiver) hold  

Phases → stages → tasks. Method detail: [references/method.md](references/method.md).

---

## What gets created

- `AGENTS.md`, `docs/constitution.md`  
- `docs/tasks.md`, `docs/registry.md`, roadmap, toolchain pins  
- Research profile + landscape  
- Charter + authorize ADRs  
- At least two domain areas with claim tables and open questions  
- `docs/workflows/`, `docs/checklists/`  
- `scripts/verify_structure.py`  

Example tree: [examples/offline-habit-tracker/](examples/offline-habit-tracker/).

---

## Package layout

```text
smart-vibe-kit/
  SKILL.md              slash entry
  skill.json            version + install paths
  references/           method, bootstrap, research-gate, workflows
  assets/templates/     copied then rewritten for the idea
  scripts/              install + verify
  adapters/             host notes
  examples/             sample bootstrap
  tests/                repo only (not installed into skill dirs)
```

---

## Development

```bash
python scripts/verify_skill_package.py
python -m unittest discover -s tests -v
```

[CONTRIBUTING.md](CONTRIBUTING.md) · [UPGRADE.md](UPGRADE.md)

---

## Community

- [Contributing](CONTRIBUTING.md)  
- [Code of Conduct](CODE_OF_CONDUCT.md)  
- [Security policy](SECURITY.md)  

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) — [LICENSE](LICENSE), [NOTICE](NOTICE).
