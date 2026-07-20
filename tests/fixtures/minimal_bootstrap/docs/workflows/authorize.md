# authorize

Open a **stage** only with an explicit decision. Freezes prior stage outputs as inputs.

## Steps

1. Confirm prior stage gate is signed (`done` + evidence), unless this is bootstrap Stage 1.  
2. Draft an authorize ADR from `docs/adr/_template.md` / skill authorize-stage template.  
3. Set Status `proposed`. **User/owner accepts** (chat approval is enough) → `accepted`.  
   - Bootstrap exception: ADR-0002 may be `accepted` when the user invoked `/smart-vibe-kit`.  
4. Update `docs/tasks.md`: stage map, task table, **Next action**.  
5. Add registry rows for new task IDs.  
6. State **in scope** and **forbidden** clearly (prevents agent fiction).  

## Done when

- Authorize ADR `accepted`  
- Tasks index Next action points at the first real work task  
- Agents cannot “notice” a new stage without this ADR  

## Anti-patterns

- Agent invents Stage N+1 because “it feels next”  
- Implementation during an explore-only authorized stage  
- Marking authorize ADR `accepted` without user invoke/approval (except ADR-0002 bootstrap rule)  
