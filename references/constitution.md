# Constitution (kit defaults)

Non-negotiable principles for any project using Smart Vibe Kit.  
At bootstrap, copy into project `docs/constitution.md` and customize **Articles IV–VI**. Keep **I–III** and **VII–IX** unless you consciously supersede them with an ADR.

---

## Article I — Repo beats memory

When project docs conflict with an agent’s training data, **the repository wins**.  
If a required fact is missing, **stop and flag** (`[DECISION NEEDED]` / `[OPEN QUESTION]`). Do not invent plausible values, versions, APIs, hashes, or defaults.

## Article II — Scoped retrieval

Agents load **only** the sources listed for the current task in the document registry.  
Whole-repo context dumps are an anti-pattern. Specs without registry rows are incomplete process, not optional polish.

## Article III — Execution grounds “done”

A task is `done` only when:

1. Documentation claims are sourced and verified  
2. Automated tests (or an explicit deferred-test waiver while `not_started`) exist  
3. Runtime evidence was produced on a real machine in the work session  

**Exception:** explore-stage / process-task waivers defined in `docs/verification-gates.md`.

Prose is necessary; prose alone is never sufficient outside those waivers.

## Article IV — Domain wall (customize)

Define which knowledge domains must not bleed into each other’s specs.  
Example placeholder (replace at bootstrap):

> Research notes must not prescribe product UI chrome. Product specs must not invent upstream API names — cite P0 or run an inspect tool.

## Article V — Toolchain and pins (customize)

Versions, SDKs, and environment pins live in `docs/toolchain-pins.md` and are checked by the commands listed there. Agents must not invent version numbers.

## Article VI — Product / architecture constraints (customize)

Encode irreversible product or architecture constraints here (or point to accepted ADRs).

## Article VII — Decisions are ADRs

Accepted ADRs are **immutable**. Change course by **superseding**, not by quietly editing history.  
Stage transitions and abandonments require an authorize / abandon ADR.  
`proposed` → `accepted` requires the user/owner (chat approval is enough), except bootstrap ADR-0002 and the ADR-0001 rule in the charter template.

## Article VIII — Tasks index is not a novel

The active tasks file records IDs, status, links, and evidence. Long normative content belongs in deliverable specs. Archive completed phases under `docs/archives/phase-N-slug.md`.

## Article IX — Hallucination incident response

Wrong inventions become:

1. A correction in the authoritative spec  
2. An ADR and/or registry audit row  
3. A test or structural verifier when the failure mode is repeatable  

Silent patching without documentation is a constitution violation.
