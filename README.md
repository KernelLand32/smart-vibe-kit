# Smart Vibe Kit

**Agent skill:** `/smart-vibe-kit <project idea>`

Still vibe coding—just with a spine.

You type a short project idea. The skill drops an organized process into your workspace: `AGENTS.md`, phased tasks, ADRs, claim-labeled specs, and verification gates. Next session (and the next agent), you’re not starting from zero—you’re reading the same ground truth. How you write that idea matters a lot; see [Writing the project idea](#writing-the-project-idea).

Works with the [Agent Skills](https://agentskills.io/specification) standard on **Cursor, Claude Code, Codex, Gemini CLI**, and anything else that loads skills from `.agents/skills` or `.claude/skills`.

You’ll need **Python 3** for the installer and verifiers.

---

## Why this exists

Coding agents are great at sounding finished. They’re weaker at:

- Telling a real fact from a confident guess (APIs, versions, market claims, compliance)
- Knowing what to read next without stuffing the whole docs tree into context
- Agreeing on what “done” means without a test that passed and something that actually ran
- Exploring before inventing UI and architecture fiction
- Leaving a trail when they guess wrong, instead of quietly rewriting history

Most “start a project with AI” flows race to the first files. You get a repo that *looks* complete on shaky assumptions. Smart Vibe Kit aims at a different first win: a **process that survives agent sessions**—scoped reading, labeled claims, authorized stage changes, and three gates before anything can be marked `done`.

It grew out of a real phased, evidence-gated practice ([references/origin.md](references/origin.md)), then got generalized and packed as one slash skill so the same habits travel across tools.

---

## Philosophy

Five things the kit won’t budge on:

1. **Repo beats memory.** After bootstrap, the project docs win. Missing fact? Stop and flag it—don’t invent a tidy default.
2. **Read only what you need.** The registry lists the minimum docs for the current task. Dumping everything into context is how sessions go sideways.
3. **“Done” means it ran.** Docs fidelity, automated tests, and runtime evidence (with narrow waivers for explore/process work). Nice prose alone doesn’t close implementation work.
4. **Stages open on purpose.** Exploration, design, and build unlock through ADRs—not because an agent “felt” the next step.
5. **Wrong guesses become decisions.** Fix the specs, record it in an ADR or registry audit, and preferably lock it with a test or structural check. No silent patches.

Vibe is fine for the idea. Shipping truth is citations, pins, and commands that actually ran.

---

## What it solves

| Pain | What you get |
|------|----------------|
| Empty docs nobody trusts | Idea-specific first drafts (charter, research profile, domain specs)—not `{placeholder}` soup |
| Invented APIs / versions / stats | Claim tables, confidence tags (`[ASSUMPTION]`, `[OPEN QUESTION]`, P0–P4), research when the domain needs it |
| Context stuffed with the wrong docs | A **document registry**: each task ID → short reading list |
| “Done” = the model said so | **Three gates** (docs / tests / runtime) before `done` |
| Scope creep mid-flight | Phase → stage → task; stages open only via an **authorize ADR** |
| Domains bleeding into each other | Constitution **domain walls** tuned to your project |
| Yesterday’s bad path coming back | Accepted ADRs stay put; supersede or abandon—don’t quietly edit history |
| Rules that only work in one IDE | Portable skill + installer (shared `.agents/skills` path) |

It does **not** scaffold an app unless you ask for code in the same message. Process first; build when a stage says so.

---

## How it works

### Writing the project idea

Whatever you write after `/smart-vibe-kit` becomes the seed for the charter, research profile, domain walls, and Stage 1 tasks. Thin seeds → thin (or invented) docs. Aim for **about 2–6 sentences**, or a tight bullet list: short enough to paste into chat, clear enough that a stranger could tell what v1 is and isn’t.

**Put these in if you can** (any order):

| Piece | Ask yourself | Example |
|-------|--------------|---------|
| **Who** | Who is this for, in what mess? | “Adults with ADHD who abandon cloud habit apps” |
| **Job** | What do they actually get in v1? | “Log habits offline on one device” |
| **Shape** | App, library, plugin, data/ML, infra…? | “Local-first mobile or desktop app” |
| **Constraints** | Hard limits—don’t let the agent “creatively” skip these | “Local encryption; no mandatory account” |
| **Non-goals** | What must *not* show up in v1? | “No social feed, coaches, or clinical treatment claims” |
| **Walls** | What should stay separate? | “Product UX vs crypto/library choices” |
| **Risks** | What could kill this, or needs research? | “Encryption UX friction; store format undecided” |
| **Stack lean** (optional) | Preferences only—say so | “Prefer Rust or TypeScript if it fits offline-first” |

**Say it out loud when it’s true:**

- Regulated / medical / legal / finance → so research and the non-reliance banner kick in
- Must plug into a specific host or API (DAW, EHR, a named cloud) → so exploration points at the right P0 sources
- “Skip live research” or you paste links yourself → so the agent doesn’t pretend it browsed the web

**A pattern that works** (fill in, drop the brackets):

```text
/smart-vibe-kit
[one-liner product].
For [primary users] who [situation / pain].
v1 ships [one concrete outcome], as a [app | library | plugin | …].
Hard constraints: […].
Non-goals for v1: [at least three].
Keep separate: [domain wall A] vs [domain wall B].
Open risks: […].
```

**Examples**

Weak (the agent will fill in gaps—often badly):

```text
/smart-vibe-kit habit app
```

Better:

```text
/smart-vibe-kit offline-first habit tracker for ADHD with local encryption
```

Strong (enough to write a real charter from):

```text
/smart-vibe-kit offline-first habit tracker for adults with ADHD who abandon cloud apps.
v1: log habits on one device with a locally encrypted store; no account required.
Non-goals: social feed, coaches, sync, clinical treatment or diagnosis claims.
Walls: product/UX must not invent crypto APIs; engineering must not redefine user outcomes.
Risks: encryption UX friction; platform (mobile vs desktop) undecided.
Stack lean: prefer whatever supports solid local encryption—treat as assumption until pinned.
```

**Things that usually go wrong**

- Platform fantasy (“build the OS for X”) with no concrete v1
- Feature laundry lists with no users or non-goals
- “Like Competitor Y, but better” with no constraints or differentiation
- Stack pins stated as facts (“we use Library Z 4.2”) with no source—say “prefer Z” or “TBD”
- Asking for a full app scaffold in the same breath unless you **also** want code now (default is process-only)

Clearer idea → less guessing at bootstrap → fewer `[ASSUMPTION]` / `[OPEN QUESTION]` rows on day one.

### One command

Everything after the skill name is that idea:

```text
/smart-vibe-kit offline-first habit tracker for ADHD with local encryption
```

The skill only runs when you invoke it (`disable-model-invocation: true`). It will:

1. Run a **research gate** (live web when the domain needs it; always write research profile + landscape)
2. Bootstrap the full process tree for **your** idea ([references/required-structure.md](references/required-structure.md))
3. Open Phase 1 · Stage 1 **Exploration** via ADR (invoke means “go explore,” not “ship fiction”)
4. Copy workflows and checklists into the project
5. Run `python scripts/verify_structure.py --root . --bootstrap` until it passes
6. Hand you one **Next action**

After that, trust the project’s `AGENTS.md` and `docs/`. Day-to-day work uses named procedures under `docs/workflows/` (specify, authorize, implement, verify, recover, refresh, …)—not more slash commands.

### The operating picture

```text
Constitution / AGENTS  → non-negotiables + read order
Registry               → task → minimum docs
Tasks index            → status + Next action (keep it short)
Deliverable specs      → living truth + claims you can check
ADRs                   → decisions + stage open/close
Verification gates     → what “done” is allowed to mean
```

Time hierarchy: **Phase → Stage → Task**. Typical arc: explore → structure → design → implement → validate. Longer write-up: [references/method.md](references/method.md).

### After bootstrap

In a normal session:

1. Read `AGENTS.md` / `docs/constitution.md`
2. Open `docs/tasks.md` → **Next action**
3. Load only the registry docs for that task
4. Follow the workflow that Next action names (`docs/workflows/…`)
5. Mark `done` only when the gates (or an honest explore waiver) hold up

If the workspace already looks like Smart Vibe Kit, invoke again and pick **refresh / extend / abort** (see [references/workflows/refresh.md](references/workflows/refresh.md); after bootstrap the same file lives under `docs/workflows/`).

---

## Install (Windows / macOS / Linux)

```bash
# One shared install (Cursor, Gemini, Codex project, and other .agents hosts)
python scripts/install.py --target agents --scope user

# Everything (Cursor + Claude + Codex + Gemini + agents; paths deduped)
python scripts/install.py --target all --scope user

# Project-scoped (commit .agents/skills for the team)
python scripts/install.py --target all --scope project --project-root .
```

Wrappers:

```powershell
.\scripts\install.ps1 -Target agents -Scope user
.\scripts\install.ps1 -Target all -Scope user
```

```bash
./scripts/install.sh agents user
./scripts/install.sh all user
```

| Target | User path | Project path |
|--------|-----------|--------------|
| **agents** | `~/.agents/skills/smart-vibe-kit/` | `.agents/skills/smart-vibe-kit/` |
| cursor | `~/.cursor/skills/…` | `.cursor/skills/…` |
| claude | `~/.claude/skills/…` | `.claude/skills/…` |
| codex | `~/.codex/skills/…` | `.agents/skills/…` |
| gemini | `~/.gemini/skills/…` | `.gemini/skills/…` |

Handy extras:

```bash
python scripts/install.py --list
python scripts/install.py --what-if --target all
python scripts/install.py --uninstall --target agents --scope user
python scripts/verify_skill_package.py
```

Full installer notes: [install.md](install.md). Host-specific bits: [adapters/](adapters/).

---

## What you get

A bootstrapped workspace includes things like:

- `AGENTS.md` + `docs/constitution.md`
- `docs/tasks.md`, `docs/registry.md`, roadmap, toolchain pins
- Research profile + landscape
- Charter + authorize ADRs
- At least two domain deliverable areas with claim tables and open questions
- `docs/workflows/` and `docs/checklists/`
- `scripts/verify_structure.py` (`--bootstrap` checks the full tree)

See a finished example: [examples/offline-habit-tracker/](examples/offline-habit-tracker/).

---

## Package layout

```text
smart-vibe-kit/
  SKILL.md              ← slash entry (/smart-vibe-kit)
  skill.json            ← version + install path manifest
  references/           ← method, constitution, bootstrap, research-gate, workflows
  assets/templates/     ← copied, then rewritten for your idea
  scripts/              ← install.py (+ ps1/sh), verify_*
  adapters/             ← host notes + Claude legacy command
  examples/             ← golden bootstrap tree
  tests/                ← unit tests (repo only; not copied into skill installs)
```

---

## Development

```bash
python scripts/verify_skill_package.py
python -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Upgrade notes: [UPGRADE.md](UPGRADE.md).

---

## Community

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
