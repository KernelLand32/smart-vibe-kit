# ADR-NNNN — Open Phase {P} Stage {S}: {Name}

- **Status:** proposed  
- **Date:** YYYY-MM-DD  
- **Deciders:** {stakeholder / project owner}  
- **Depends on:** {prior stage exit / ADR}

> Move to `accepted` only after the decider confirms (chat approval is enough).  
> **Bootstrap exception:** ADR-0002 may be `accepted` in the same `/smart-vibe-kit` run that the user invoked, because invoking the command is the authorization to open Phase 1 · Stage 1 Exploration.

## Context

Prior stage is signed (or this is bootstrap Stage 1). Stakeholder authorizes the next stage against frozen inputs.

## Decision

1. **Phase {P} · Stage {S}: {Name}** is **open**.  
2. Deliverable index: [{path}]({path}).  
3. **In scope:** {bullets}.  
4. **Out of scope / forbidden:** {bullets — prevent fiction}.  
5. Later work requires a new authorize ADR — agents must not invent stage openings.

## Consequences

| Allowed now | Still forbidden |
|-------------|-----------------|
| | |

## Verification

| Check | Artifact |
|-------|----------|
| Tasks index updated | `docs/tasks.md` Next action |
| Registry rows added | `docs/registry.md` |
| Prior stage marked `done` | stage map |
