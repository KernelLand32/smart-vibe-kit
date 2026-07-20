# refresh / extend

Re-run `/smart-vibe-kit` against a workspace that **already** looks like Smart Vibe Kit, after the user chooses **refresh**, **extend**, or **abort**.

Detection (all must exist): `AGENTS.md`, `docs/tasks.md`, `docs/registry.md`, `docs/adr/0002-authorize-phase1-stage1.md`.

## abort

Stop. Do not write files.

## refresh

Bring process artifacts up to the **current skill version** without changing product intent.

| May overwrite / replace | Must not clobber without asking |
|-------------------------|----------------------------------|
| `scripts/verify_structure.py` | Accepted ADRs (`docs/adr/0001+` bodies) |
| `docs/checklists/*` | Domain deliverables under `docs/{area}/` |
| `docs/workflows/*` (re-vendor from skill) | `docs/tasks.md` status / evidence / Next action |
| `docs/_templates/*` | `docs/research/profile.md` substance |
| Missing required-structure paths (create) | User-edited Article IV–VI walls (merge carefully) |

Steps:

1. Re-vendor checklists, workflows (including this file), `_templates` (deliverable-spec + phase-archive), verifier script.  
2. Add any **new** required-structure paths that are missing (e.g. `docs/toolchain-pins.md`) with first-pass content — do not wipe existing good files.  
3. Update `AGENTS.md` quick commands / read order if the skill template changed; keep project-specific walls.  
4. Do **not** reset task statuses to rewrite history.  
5. Run:

```bash
python scripts/verify_structure.py --root . --bootstrap
```

6. Hand off: list refreshed paths + current **Next action**.

## extend

Add scope (new domain area, phase, or research) while preserving history.

| Allowed | Forbidden |
|---------|-------------|
| New `docs/{area}/` deliverables | Deleting or silently editing accepted ADRs |
| New registry rows + tasks for new work | Marking explore fiction as implement-ready |
| New `proposed` ADRs (user must accept) | Opening a new stage without authorize ADR |
| Append roadmap phases | Inventing APIs/versions |

Steps:

1. Confirm what to extend (user one-liner).  
2. Write new deliverables + registry rows + tasks; set **Next action**.  
3. If a new stage is needed → **authorize** procedure (`proposed` until user accepts).  
4. Run `python scripts/verify_structure.py --root . --bootstrap`.  
5. Hand off Next action.

## Done when

- User choice honored  
- `--bootstrap` exits 0  
- Accepted ADRs unchanged (unless user explicitly asked to supersede)  
