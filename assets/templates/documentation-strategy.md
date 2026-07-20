# Documentation strategy

How docs stay accurate and resistant to AI hallucination.

**Entry:** `AGENTS.md` · `registry.md` · `verification-gates.md`  
**Decisions:** `docs/adr/`

---

## Goals

| Goal | Mechanism |
|------|-----------|
| Single source of truth | One deliverable spec per topic |
| Traceable decisions | ADRs |
| Scoped context | Registry |
| Living specs | Update docs in the same change as code |
| Verifiable claims | Claim tables + tags |

**Rule:** `tasks.md` tracks status and evidence only — no duplicate long prose.

---

## Claim confidence tags

| Tag | Meaning |
|-----|---------|
| *(none)* | Directly cited from P0 in-section |
| `[VERIFIED: …]` | Ran command / produced artifact |
| `[INFERRED FROM: …]` | Logical consequence of cited fact |
| `[ASSUMPTION: …]` | Provisional |
| `[DECISION NEEDED]` | Stakeholder must choose |
| `[OPEN QUESTION: ID]` | Tracked ambiguity |
| `TBD` | Unknown — **not a fact** |

---

## Source tiers

| Tier | Use |
|------|-----|
| P0 | Primary external / measured |
| P1 | Verified local |
| P2 | Accepted ADR |
| P3 | Derived (cite P0–P2) |
| P4 | Not a source |

---

## Anti-hallucination rules

1. Ground claims in primary sources or measurements.  
2. Flag gaps; do not fill them with plausible values.  
3. Respect domain walls (Constitution Article IV).  
4. Execution beats prose.  
5. Wrong guess → ADR + registry audit (+ test if repeatable).  

---

## ADR practice

| Rule | Detail |
|------|--------|
| Location | `docs/adr/NNNN-short-title.md` |
| Status | `proposed` → `accepted` → `deprecated` / `superseded` |
| Immutability | Never edit accepted body; supersede |
| Content | Context, Decision, Consequences, **Verification** |
