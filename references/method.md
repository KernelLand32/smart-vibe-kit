# METHOD — the working system

This is the **generalized operating model**. Domain examples are placeholders only.

---

## 1. Layers of truth

```text
Constitution / AGENTS     → non-negotiable rules + read order for agents
Registry                  → task ID → minimum docs to load (scoped context)
Tasks index (active)      → current phase/stage status + next action
Phase archives            → closed phases (immutable history)
Deliverable specs         → living truth for a topic (with claim tables)
ADRs                      → irreversible decisions; authorize stage transitions
Roadmap                   → long-horizon map (required at bootstrap; not day-to-day execution)
Verification gates        → what “done” is allowed to mean
```

**Rule:** The tasks index tracks **status and evidence pointers only**. It does not duplicate long spec prose.

---

## 2. Time hierarchy

| Level | Meaning | Who opens it |
|-------|---------|--------------|
| **Phase** | Large capability slice (weeks–months) | Stakeholder / lead |
| **Stage** | Ordered slice inside a phase (explore → design → build) | **Authorize ADR** required |
| **Cut / track** | Parallel or sequenced delivery inside a stage (e.g. MVP then full) | Tasks index + deliverable |
| **Task** | Atomic unit with ID, status, linked spec | Tasks index |

Stages are not invented mid-flight by agents. A stage becomes active only when an **authorize ADR** is accepted and the tasks index is updated.

Typical stage progression (adapt names to domain):

1. **Explore / research** — inventory facts; forbid implementation fiction  
2. **Structure / IA** — information architecture or system shape  
3. **Design / specify** — interaction, interface, or detailed design; sign a gate  
4. **Implement** — code against frozen prior stages; cuts if needed  
5. **Validate / close** — gates + archive  

Abandoned wrong paths get an ADR (`abandon` / `supersede`) so agents do not resurrect them.

---

## 3. Task lifecycle

Statuses:

| Status | Meaning |
|--------|---------|
| `not_started` | Scheduled; no evidence yet |
| `in_progress` | Active work |
| `blocked` | Waiting on dependency (name it) |
| `done` | **All three gates pass** + evidence cited |

Transitions:

```text
not_started → in_progress → done
                 ↘ blocked → in_progress → done
```

**Forbidden:** marking `done` because a doc says the feature exists, or because the agent “thinks” it works.

**Explore / process waiver:** inventory and authorize tasks in an Exploration stage may be `done` with Gate 1 only when `docs/verification-gates.md` waiver rules are met and the revision log records `waiver: explore-doc` or `waiver: process`.

---

## 4. Specs vs decisions vs tasks

| Artifact | Answers | Must not |
|----------|---------|----------|
| **Deliverable spec** | What is true / required for a topic | Track every micro-task status |
| **ADR** | Why we chose X (or authorized stage Y) | Be silently rewritten when accepted |
| **Tasks index** | What is next; what’s done; where evidence lives | Hold long normative prose |
| **Registry** | What to read for task T | List every file in the repo |

---

## 5. Claim discipline

Load-bearing facts in specs use a **Verifiable claims** table:

| Claim | Tier | Source | Verified |
|-------|------|--------|----------|
| … | P0–P3 | URL / path / ADR | command + date, or TBD |

Confidence tags in prose:

| Tag | Use |
|-----|-----|
| *(none)* | Directly cited from P0 in-section |
| `[VERIFIED: …]` | Ran a command / produced an artifact |
| `[INFERRED FROM: …]` | Logical consequence of a cited fact |
| `[ASSUMPTION: …]` | Provisional; not “done” evidence |
| `[DECISION NEEDED]` | Stakeholder must choose |
| `[OPEN QUESTION: ID]` | Tracked ambiguity |
| `TBD` | Unknown — **never** present as fact |

Source tiers:

| Tier | Meaning |
|------|---------|
| **P0** | Primary external or measured ground truth |
| **P1** | Verified on this machine (logs, hashes, tool output) |
| **P2** | Accepted project ADR |
| **P3** | Derived; must cite P0–P2 |
| **P4** | Model memory / vibes — **not a source** |

---

## 6. Three verification gates

Before any task or stage may be `done`:

1. **Doc fidelity** — claims have Source + Verified; no false certainty  
2. **Tests** — automated check that would fail if the change is wrong  
3. **Runtime** — a real command/binary ran this session; output captured  

See [../assets/templates/verification-gates.md](../assets/templates/verification-gates.md) and [checklists/done.md](checklists/done.md).

---

## 7. Scoped retrieval (anti-dump)

Agents **do not** load the whole docs tree. Every session:

1. Read `AGENTS.md` / constitution  
2. Open `registry.md` for the **current task ID only**  
3. Open `tasks.md` for status / next action  
4. Load **only** the deliverable sections listed in the registry  
5. Stop and flag if a required fact is missing  

This is the primary anti-hallucination mechanism: less irrelevant context, more authoritative context.

---

## 8. Failure → decision

When humans or agents invent a wrong “fact”:

1. Record the correction  
2. Add or supersede an **ADR** (or registry “decision audit” row)  
3. Add a test or structural check if the mistake is repeatable  
4. Never “fix forward” in silence  

---

## 9. Separation of concerns (customize)

Projects often need **hard walls** between doc trees (e.g. library vs application, research vs product). Encode walls in the constitution:

> Specs in area A must not contain concepts from area B except at an explicit bridge doc.

Wrong-layer content is a process bug, not a style nit.

---

## 10. Comparison to Spec Kit (spirit, not clone)

| Spec Kit idea | Smart Vibe Kit analogue |
|---------------|-------------------------|
| Constitution | kit `references/constitution.md` → project `docs/constitution.md` + `AGENTS.md` |
| `/specify` | **specify** procedure → deliverable spec + claim tables |
| `/plan` | **authorize** + roadmap + stage map |
| `/tasks` | **plan-tasks** → numbered tasks index |
| `/implement` | **implement** against **frozen** prior stage |
| Quality bar | **Three gates** + runtime evidence (+ explore waivers) |
| Extra (this kit) | Registry-scoped reads; hallucination → ADR; stage authorize gates |
| Slash commands | **Only** `/smart-vibe-kit` — other Spec Kit commands are procedures in `docs/workflows/` |
