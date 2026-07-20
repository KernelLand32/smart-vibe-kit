# Bootstrap — populate a project from an idea

Called by `/smart-vibe-kit` after the research gate.  
Templates live in [../assets/templates/](../assets/templates/). **Copy then rewrite** — output must read as if a human started this project today.

**Authority:** The complete mandatory output tree is [required-structure.md](required-structure.md). Do not hand off until every path there exists.

**Only slash command:** `/smart-vibe-kit`. Do not invent other slash commands. Ongoing procedures live in `docs/workflows/` after this bootstrap.

## A. Derive a project profile

Always write `docs/research/profile.md` from [../assets/templates/research-profile.md](../assets/templates/research-profile.md).

## B. Write core process files

| Output | Source template / action |
|--------|--------------------------|
| `AGENTS.md` | [AGENTS.md](../assets/templates/AGENTS.md) |
| `docs/constitution.md` | [constitution.md](../assets/templates/constitution.md) — customize Articles IV–VI |
| `docs/documentation-strategy.md` | [documentation-strategy.md](../assets/templates/documentation-strategy.md) |
| `docs/verification-gates.md` | [verification-gates.md](../assets/templates/verification-gates.md) (includes explore waivers) |
| `docs/toolchain-pins.md` | [toolchain-pins.md](../assets/templates/toolchain-pins.md) |
| `docs/roadmap.md` | [roadmap.md](../assets/templates/roadmap.md) — 3–5 phases, no fake dates |
| `docs/adr/_template.md` | [adr.md](../assets/templates/adr.md) |
| `docs/adr/0001-project-charter.md` | [project-charter-adr.md](../assets/templates/project-charter-adr.md) |
| `docs/adr/0002-authorize-phase1-stage1.md` | [authorize-stage-adr.md](../assets/templates/authorize-stage-adr.md) |
| `docs/tasks.md` | [tasks.md](../assets/templates/tasks.md) |
| `docs/registry.md` | [registry.md](../assets/templates/registry.md) |
| `docs/_templates/deliverable-spec.md` | [deliverable-spec.md](../assets/templates/deliverable-spec.md) |
| `docs/research/landscape.md` | [research-landscape.md](../assets/templates/research-landscape.md) |

### ADR acceptance (bootstrap)

- **ADR-0002** (authorize Phase 1 · Stage 1 Exploration): set `accepted` — invoking `/smart-vibe-kit` is the user’s authorization for Exploration only.  
- **ADR-0001** (charter): set `accepted` if the idea was clear in the invoke message; otherwise `proposed` and **Next action** = charter review.  
- Later stages: always `proposed` until the user accepts (see authorize workflow).

### `docs/tasks.md`

Example Stage 1 map:

| ID | Status | Task |
|----|--------|------|
| 1.1.1 | `done` | Authorize Stage 1 (ADR-0002) — `waiver: process` |
| 1.1.2 | `in_progress` or `not_started` | Problem / user inventory |
| 1.1.3 | `not_started` | Competitor / analogue survey |
| 1.1.4 | `not_started` | Constraints & domain walls check |
| 1.1.5 | `not_started` | Stage 1 gate (sign-off) |

**Next action:** first incomplete exploration task.  
Use canonical name `docs/tasks.md` (not `subtasks.md`) for new projects.

### Already-SVK detection

Treat as existing Smart Vibe Kit if **all** exist: `AGENTS.md`, `docs/tasks.md`, `docs/registry.md`, `docs/adr/0002-authorize-phase1-stage1.md`. Then ask: **refresh / extend / abort** and follow [workflows/refresh.md](workflows/refresh.md) (vendored to `docs/workflows/refresh.md`).

### Foreign / heavy workspace

Ask before writing if **any** of:

- `src/`, `app/`, `pkg/`, or `lib/` with application code **and** an existing distinct README product name unrelated to the idea  
- More than ~50 tracked source files that are not process docs  
- User said this is an existing product repo and only wanted analysis  

Empty or docs-only workspaces: proceed.

## C. Domain folders + first-pass specs (≥2)

| Idea shape | Typical areas |
|------------|----------------|
| App / SaaS | `product/`, `ux/`, `engineering/`, `research/` — wait: `docs/research/` is process; use `docs/product/` + `docs/engineering/` etc. |
| Library / SDK | `api/`, `engineering/` |
| Data / ML | `data/`, `model/`, `evaluation/` |
| Plugin / embedded | `host/`, `runtime/`, `product/` |
| Infra / DevOps | `architecture/`, `operations/`, `security/` |

Do **not** put domain deliverables only under `docs/research/` (reserved for the research gate).

Each area: at least one deliverable from [deliverable-spec.md](../assets/templates/deliverable-spec.md).

## D. Vendor checklists + workflows (**required**)

Copy skill package files into the project (rewrite links to project-relative paths):

| From skill | To project |
|------------|------------|
| `references/checklists/*.md` | `docs/checklists/` |
| `references/workflows/*.md` (including `refresh.md`) | `docs/workflows/` |
| [workflows-README.md](../assets/templates/workflows-README.md) | `docs/workflows/README.md` |
| [deliverable-spec.md](../assets/templates/deliverable-spec.md) | `docs/_templates/deliverable-spec.md` |
| [phase-archive.md](../assets/templates/phase-archive.md) | `docs/_templates/phase-archive.md` |

Add `docs/archives/README.md` from [archives-README.md](../assets/templates/archives-README.md).

## E. Vendor the verifier (**required**)

Copy skill `scripts/verify_structure.py` → project `scripts/verify_structure.py`.  
Mention in `AGENTS.md` quick commands.

## F. Sanity pass (all required)

1. [required-structure.md](required-structure.md) tree fully present  
2. No unresolved `{placeholders}` outside `docs/_templates/`  
3. Every task has a registry row  
4. ADR-0002 `accepted`; ADR-0001 `accepted` or `proposed` with Next action = review  
5. Research claims cite URLs or are tagged; `profile.md` + `landscape.md` exist  
6. Regulated domain + skipped research → non-reliance banner in charter  
7. Exit 0:

```bash
python scripts/verify_structure.py --root . --bootstrap
```

## G. What not to do during bootstrap

- Do not scaffold a full application codebase unless the user explicitly asked for code in the same message  
- Do not mark exploration tasks `done` without Gate 1 (sources or labeled assumptions)  
- Do not open Stage 2 without a new authorize ADR later  
- Do not create additional slash commands  
- Do not hand off with a partial tree “to fill in later”  
