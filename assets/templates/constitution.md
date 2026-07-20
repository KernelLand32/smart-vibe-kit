# Constitution — {Project}

Non-negotiable principles. Articles **I–III** and **VII–IX** match Smart Vibe Kit defaults.  
Customize **IV–VI** for this domain (required at bootstrap).

---

## Article I — Repo beats memory

When project docs conflict with an agent’s training data, **the repository wins**.  
If a required fact is missing, **stop and flag** (`[DECISION NEEDED]` / `[OPEN QUESTION]`). Do not invent plausible values, versions, APIs, hashes, or defaults.

## Article II — Scoped retrieval

Agents load **only** the sources listed for the current task in [registry.md](registry.md).  
Whole-repo context dumps are an anti-pattern.

## Article III — Execution grounds “done”

A task is `done` only when the three gates in [verification-gates.md](verification-gates.md) pass — **except** where that file defines an explore-stage / process-task waiver.

## Article IV — Domain wall (customize)

{Hard separations — e.g. research notes must not prescribe UI chrome; product specs must not invent upstream API names.}

## Article V — Toolchain and pins (customize)

Versions live in [toolchain-pins.md](toolchain-pins.md) and are checked by the verify commands listed there. Agents must not invent version numbers.

## Article VI — Product / architecture constraints (customize)

{Irreversible v1 constraints, or pointers to accepted ADRs.}

## Article VII — Decisions are ADRs

Accepted ADRs are **immutable**. Change course by **superseding**.  
Stage transitions and abandonments require an authorize / abandon ADR.  
Human (or explicit owner) acceptance is required to move `proposed` → `accepted`, except the bootstrap rule documented in ADR-0001.

## Article VIII — Tasks index is not a novel

[tasks.md](tasks.md) records IDs, status, links, and evidence. Long normative content belongs in deliverable specs. Closed phases archive under [archives/](archives/) as `phase-N-slug.md`.

## Article IX — Hallucination incident response

Wrong inventions become: (1) correction in the authoritative spec, (2) ADR and/or registry audit row, (3) a test or structural check when repeatable. Silent patching without documentation is a constitution violation.
