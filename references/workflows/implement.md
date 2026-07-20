# implement

Execute the **Next action** (or explicit task ID) against frozen specs.

## Steps

1. Bootstrap: `AGENTS.md` → `docs/tasks.md` → registry → listed specs only.  
2. Set task `in_progress` if it was `not_started`.  
3. Implement the smallest change that satisfies the linked spec.  
4. Update the deliverable spec in the **same change** when behavior/docs drift.  
5. Do not expand into unauthorized stage scope.  
6. If a fact is missing, stop with `[DECISION NEEDED]` / `[OPEN QUESTION]` — do not invent.  
7. When ready, run [verify.md](verify.md) before flipping status to `done`.  

## Done when

- Behavior matches the frozen prior-stage decisions  
- Evidence paths exist for the required gates (or explore/process waiver)  
- `docs/tasks.md` status updated **only after** verify  
