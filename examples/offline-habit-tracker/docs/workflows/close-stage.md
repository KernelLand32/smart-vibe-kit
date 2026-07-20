# close-stage

Sign a stage (or phase) exit.

## Steps

1. Confirm all non-blocked stage tasks are `done` (or explicitly deferred with ADR).  
2. Walk `docs/checklists/stage-gate.md`.  
3. Record gate **Go** with date in the deliverable and/or tasks revision log.  
4. If phase complete: write `docs/archives/phase-N-slug.md` from `docs/_templates/phase-archive.md`; reset `docs/tasks.md` for the next phase **after** a new authorize ADR.  
5. Update registry “current phase” section.  

## Done when

- Stage map shows stage `done`  
- Next stage is either unauthorized (stopped) or opened via the authorize procedure  
