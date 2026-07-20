# Origin notes (optional)

How this kit was inferred from a host repository’s real practice — not from a verbal process description.

## Observed artifacts → kit concepts

| Observed in host | Generalized concept |
|------------------|---------------------|
| `AGENTS.md` read order + hard rules | Constitution + agent entry |
| `docs/registry.md` task → minimum docs | Scoped retrieval registry |
| `docs/subtasks.md` phase/stage + Next action | Active tasks index |
| `docs/subtasks-phaseN.md` archives | Phase archives |
| Deliverable specs + Verifiable claims | Living specs + claim tables |
| Confidence tags / P0–P4 tiers | Claim discipline |
| `docs/adr/` + stage-open ADRs | Decisions + **authorize** gates |
| Abandon ADR for bad fiction | Recover / supersede path |
| `verification-gates.md` (doc / tests / runtime) | Three gates |
| Domain walls (e.g. model ≠ plugin) | Constitution Article IV |
| Automate what hosts can; document manual remainder | Verify workflow |

## What was dropped

Product names, DSP/plugin/DAW specifics, exact toolchain pins, and any rule that only makes sense inside that product.

## What was added for portability

- Spec Kit–style **procedure** map (not extra slash commands; only `/smart-vibe-kit`)  
- Install + skill entry (`SKILL.md`)  
- Path aliases in the structural verifier + `--bootstrap` mode  
- Explicit authorize-stage ADR template  

This file is historical. Day-to-day use starts at [../README.md](../README.md) and [../SKILL.md](../SKILL.md).
