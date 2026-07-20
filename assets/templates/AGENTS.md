# {Project} — instructions for AI agents

**This file and `docs/` are authoritative.** When repo facts conflict with general training data, **the repository wins**. If required facts are missing, **stop and flag** — do not invent plausible values.

**Slash command:** only `/smart-vibe-kit` (bootstrap; or refresh/extend per [docs/workflows/refresh.md](docs/workflows/refresh.md)). Ongoing work uses the workflows under [docs/workflows/](docs/workflows/) — not additional slash commands.

## Read order (every session)

1. [docs/constitution.md](docs/constitution.md) — non-negotiables (esp. Articles IV–VI)  
2. [docs/registry.md](docs/registry.md) — which docs apply to the current task  
3. [docs/tasks.md](docs/tasks.md) — **current** phase / stage / next action  
4. Closed phase archives under [docs/archives/](docs/archives/) — only when needed  
5. **Only** the deliverable sections listed in the registry for your task  
6. [docs/documentation-strategy.md](docs/documentation-strategy.md) — claim labels  
7. [docs/verification-gates.md](docs/verification-gates.md) — done criteria (+ explore waivers)  
8. [docs/toolchain-pins.md](docs/toolchain-pins.md) — versions  

## Non-negotiable rules

| Rule | Detail |
|------|--------|
| **No invented APIs / schemas** | Read P0 sources or run inspect tools |
| **No invented versions** | [toolchain-pins.md](docs/toolchain-pins.md) + verify script |
| **No invented measurements** | Hashes, sizes, timings → measure, then record |
| **Label uncertainty** | Claim tags; never present `TBD` as fact |
| **Execution over prose** | Tests, CLIs, and runtime logs prove behavior |
| **Domain walls** | See constitution Article IV |
| **Stage discipline** | Do not open stages without an authorize ADR |

## Before marking work complete

1. **Doc fidelity** — Source + Verified filled for load-bearing claims  
2. **Tests** — automated proof exists and passes (unless explore/process waiver)  
3. **Runtime** — command ran this session; evidence captured (unless waiver)  

Use [docs/checklists/done.md](docs/checklists/done.md). Then update [docs/tasks.md](docs/tasks.md) **only** if evidence exists.

## When you guess wrong

Follow [docs/workflows/recover.md](docs/workflows/recover.md). Add or update an ADR. Turn hallucinations into documented decisions.

## Quick commands

```text
python scripts/verify_structure.py --root .
python scripts/verify_structure.py --root . --bootstrap
```
