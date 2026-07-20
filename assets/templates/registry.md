# Document registry

**Purpose:** Map each task to the **minimum** authoritative docs. Prevents context dumping and unsupported inference.

**Rule:** If a decision is not answered by a registry-listed section, tag `[DECISION NEEDED]` or `[OPEN QUESTION]` — do not guess.

---

## How to use

1. Find the task ID in [tasks.md](tasks.md).  
2. Load **only** the sections below for that task.  
3. After implementation, fill **Verified** cells and run verification gates.

---

## Source reliability tiers

| Tier | Meaning |
|------|---------|
| **P0** | Primary external / measured ground truth |
| **P1** | Verified local (command output, logs, hashes) |
| **P2** | Accepted project ADR |
| **P3** | Derived; must cite P0–P2 |
| **P4** | Model memory — **not a source** |

---

## Current phase — task → required reading

| Task | Deliverable spec | Verify with |
|------|------------------|-------------|
| {P.S.N} | [{path}]({path}) | {command or gate} |

---

## Decision audit (high-risk gaps)

If an agent would need to decide these **without** reading the listed source, the answer is missing — update the spec or ADR first.

| Decision | Authoritative answer must be in |
|----------|--------------------------------|
| {example} | {path} |

---

## Maintenance

| When | Update |
|------|--------|
| New task | Add a registry row |
| New deliverable | Link from registry (+ roadmap if used) |
| Repeated AI mistake | New ADR + audit row |
