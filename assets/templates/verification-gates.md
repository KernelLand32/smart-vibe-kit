# Verification gates

Three gates that block “done” claims.

---

## Gate 1 — Documentation fidelity

**Question:** Does every load-bearing claim in changed docs trace to P0–P2 sources?

### Pass

- No `TBD` in **Verified** for claims tied to `done` tasks  
- Claim tags used correctly  
- Pins match [toolchain-pins.md](toolchain-pins.md)  

### Fail

- Downgrade task to `in_progress`  
- Add evidence or mark `[DECISION NEEDED]`  

---

## Gate 2 — Tests prove behavior

**Question:** Is there an automated check that would fail if the implementation is wrong?

### Pass

- Project test runner exits 0 for relevant suites  
- New behavior covered, or explicit deferred-test note while still `not_started`  

### Fail

- Do not mark `done`  
- Do not merge without fix or corrected spec  

---

## Gate 3 — Runtime execution

**Question:** Did a binary or command actually run on this machine in the current work session?

Static review is necessary, not sufficient.

### Pass

- Captured stdout/stderr or log referenced in the **Verified** column or report  
- “Works” claims include the exact command  

### Fail

- Reject completion; run the command and attach output  

---

## Explore-stage / process-task waivers

These may be marked `done` **without** Gates 2–3 when **all** apply:

1. Current authorize ADR stage is **Exploration / Discovery / Research** (or the task is pure process: authorize, registry row, charter), **and**
2. Gate 1 is satisfied for that doc task (sources or explicit `[ASSUMPTION]` / `OQ-` — no false certainty), **and**
3. The tasks revision log notes `waiver: explore-doc` or `waiver: process`.

Implement / validate stages **never** use this waiver.

## Phase / stage transition

| Gate | Requirement |
|------|-------------|
| 1 | Claim tables filled for exit criteria |
| 2 | Agreed test suites green (or explore waiver) |
| 3 | Runtime smoke / gate script recorded (or explore waiver) |
