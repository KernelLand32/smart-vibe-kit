# plan-tasks

Break an authorized stage into numbered, evidence-backed tasks.

## Steps

1. Read the authorize ADR + deliverable index for the stage.  
2. Create task IDs `{phase}.{stage}.{n}` (stable; do not renumber casually). Use `docs/tasks.md` (canonical; avoid `subtasks.md` for new work).  
3. Each row: status, short title, link to spec section.  
4. Mark dependencies as `blocked` with named blocker.  
5. Prefer **cuts/tracks** when full scope is gated on unfinished foundation work.  
6. Update registry: every task ID → minimum docs.  
7. Set a single **Next action** line.  

## Done when

- Tasks cover authorize → build → verify for the stage (or explore inventory → gate)  
- No orphan tasks without registry rows  
- Blocked work names its dependency  
