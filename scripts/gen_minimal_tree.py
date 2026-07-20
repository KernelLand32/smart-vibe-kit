#!/usr/bin/env python3
"""Write a minimal valid --bootstrap tree into --out (for tests + examples)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def copy_skill_script(out: Path) -> None:
    src = PACKAGE / "scripts" / "verify_structure.py"
    dest = out / "scripts" / "verify_structure.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_refs(out: Path) -> None:
    wf = out / "docs" / "workflows"
    cl = out / "docs" / "checklists"
    tpl = out / "docs" / "_templates"
    adr = out / "docs" / "adr"
    for d in (wf, cl, tpl, adr):
        d.mkdir(parents=True, exist_ok=True)
    for name in (
        "constitute.md",
        "specify.md",
        "authorize.md",
        "plan-tasks.md",
        "implement.md",
        "verify.md",
        "close-stage.md",
        "recover.md",
        "refresh.md",
    ):
        shutil.copy2(
            PACKAGE / "references" / "workflows" / name,
            wf / name,
        )
    for name in ("done.md", "stage-gate.md", "pr.md"):
        shutil.copy2(
            PACKAGE / "references" / "checklists" / name,
            cl / name,
        )
    shutil.copy2(
        PACKAGE / "assets" / "templates" / "workflows-README.md",
        wf / "README.md",
    )
    shutil.copy2(
        PACKAGE / "assets" / "templates" / "deliverable-spec.md",
        tpl / "deliverable-spec.md",
    )
    shutil.copy2(
        PACKAGE / "assets" / "templates" / "phase-archive.md",
        tpl / "phase-archive.md",
    )
    shutil.copy2(
        PACKAGE / "assets" / "templates" / "adr.md",
        adr / "_template.md",
    )
    # Full strategy / gates templates with project name substituted
    for tpl_name, dest_name in (
        ("documentation-strategy.md", "documentation-strategy.md"),
        ("verification-gates.md", "verification-gates.md"),
    ):
        raw = (PACKAGE / "assets" / "templates" / tpl_name).read_text(encoding="utf-8")
        # Templates have no {Project} today; copy as-is (already rewrite-ready)
        (out / "docs" / dest_name).write_text(raw, encoding="utf-8")



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--name", default="HabitVault")
    args = parser.parse_args()
    out: Path = args.out.resolve()
    name = args.name

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    write(
        out / "AGENTS.md",
        f"""# {name} — instructions for AI agents

**This file and `docs/` are authoritative.**

**Slash command:** only `/smart-vibe-kit` (bootstrap). Ongoing work uses `docs/workflows/`.

## Read order

1. docs/constitution.md
2. docs/registry.md
3. docs/tasks.md
4. Registry-listed deliverables only
5. docs/verification-gates.md
6. docs/toolchain-pins.md

## Quick commands

```text
python scripts/verify_structure.py --root .
python scripts/verify_structure.py --root . --bootstrap
```
""",
    )

    write(
        out / "docs" / "constitution.md",
        f"""# Constitution — {name}

## Article I — Repo beats memory
Repository wins over training data.

## Article II — Scoped retrieval
Load only registry-listed docs for the current task.

## Article III — Execution grounds done
Three gates, plus explore/process waivers in verification-gates.md.

## Article IV — Domain wall
Product specs must not invent crypto APIs. Engineering notes must not redefine user outcomes.
Research landscape must not prescribe pixel UI.

## Article V — Toolchain and pins
See docs/toolchain-pins.md.

## Article VI — Product constraints
v1 is offline-first, local encryption, single-device. No cloud sync in v1.

## Article VII — Decisions are ADRs
Accepted ADRs are immutable; supersede to change.

## Article VIII — Tasks index is not a novel
Status and evidence only in tasks.md. Archives under docs/archives/.

## Article IX — Hallucination incident response
Correct spec, ADR/audit row, add test when repeatable.
""",
    )

    write(
        out / "docs" / "registry.md",
        """# Document registry

| Task | Deliverable spec | Verify with |
|------|------------------|-------------|
| 1.1.1 | docs/adr/0002-authorize-phase1-stage1.md | waiver: process |
| 1.1.2 | docs/product/overview.md | Gate 1 |
| 1.1.3 | docs/product/overview.md | Gate 1 |
| 1.1.4 | docs/engineering/constraints.md | Gate 1 |
| 1.1.5 | docs/product/overview.md | stage-gate checklist |

## Decision audit

| Decision | Authoritative answer must be in |
|----------|--------------------------------|
| Encryption library choice | docs/engineering/constraints.md + toolchain-pins |
""",
    )

    write(
        out / "docs" / "tasks.md",
        f"""# Phase 1 — Foundation (Stage 1: Exploration)

> **Authorization:** docs/adr/0002-authorize-phase1-stage1.md

**Scope:** Inventory users, analogues, and constraints for {name}.  
**Deliverable:** docs/product/overview.md

## Stage map

| Stage | Status |
|-------|--------|
| 1 Exploration | in_progress |
| 2 Design | not_started |

## Stage 1 — tasks

| ID | Status | Task | Spec |
|----|--------|------|------|
| 1.1.1 | done | Authorize Stage 1 | ADR-0002 |
| 1.1.2 | in_progress | Problem / user inventory | product/overview |
| 1.1.3 | not_started | Analogue survey | product/overview |
| 1.1.4 | not_started | Constraints and domain walls | engineering/constraints |
| 1.1.5 | not_started | Stage 1 gate | product/overview |

**Next action:** 1.1.2 — Complete user inventory claims in docs/product/overview.md

## Revision log

| Date | Change |
|------|--------|
| 2026-07-20 | Opened Phase 1 Stage 1; 1.1.1 done waiver: process |
""",
    )

    write(
        out / "docs" / "toolchain-pins.md",
        f"""# Toolchain pins — {name}

| Component | Pin | Source | Verified |
|-----------|-----|--------|----------|
| Language | TBD | | TBD |
| Local DB | TBD | | TBD |
| Encryption lib | TBD | | TBD |

## Verify commands

```text
# Fill when stack is chosen
```
""",
    )

    write(
        out / "docs" / "roadmap.md",
        f"""# Roadmap — {name}

| Phase | Name | Intent | Status |
|-------|------|--------|--------|
| 1 | Foundation | Exploration and constraints | in_progress |
| 2 | Core loops | Habit tracking MVP offline | planned |
| 3 | Hardening | Encryption UX and export | planned |
| 4 | Optional sync | Only if ADR supersedes offline-only | planned |
""",
    )

    write(
        out / "docs" / "research" / "profile.md",
        f"""# Research profile — {name}

| Field | Value |
|-------|-------|
| name | {name} |
| one_liner | Offline-first habit tracker with local encryption for ADHD users |
| primary_users | Adults with ADHD who abandon cloud habit apps |
| v1_outcome | Log habits offline with encrypted local store |
| non_goals | Social feed; coach marketplace; mandatory accounts |
| domain_walls | Product vs engineering crypto details; no clinical ADHD treatment claims |
| stack_lean | ASSUMPTION: mobile or desktop local-first stack — see toolchain-pins |
| risks | Encryption UX friction; ADHD onboarding abandonment; false clinical claims |
| phase1_name | Foundation |
| research_gate | skipped — evergreen consumer app pattern; no regulated clinical claims in v1 |
""",
    )

    write(
        out / "docs" / "research" / "landscape.md",
        """# Research landscape

## Gate decision

| Item | Value |
|------|-------|
| Outcome | skipped |
| Reasons | Well-known evergreen consumer pattern; no medical/legal claims in v1 charter |
| Topics | n/a |
| Date | 2026-07-20 |

## If skipped

Skipped live research: habit-tracker UX is evergreen. Stack pins remain TBD.
No competitor feature matrix invented. Clinical ADHD treatment claims are out of scope.
""",
    )

    write(
        out / "docs" / "adr" / "0001-project-charter.md",
        f"""# ADR-0001: Project charter — {name}

**Status:** accepted  
**Date:** 2026-07-20  

## Context

User invoked /smart-vibe-kit for an offline-first habit tracker with local encryption for ADHD users.

## Decision

1. v1 outcome: encrypted local habit logging offline.
2. Non-goals: social, coaches, mandatory cloud accounts, clinical treatment claims.
3. Domain walls: per docs/constitution.md Article IV.

## Consequences

Agents must not invent APIs, versions, or medical claims.

## Verification

| Check | Artifact |
|-------|----------|
| Charter | this ADR accepted |
| Research | docs/research/profile.md |
""",
    )

    write(
        out / "docs" / "adr" / "0002-authorize-phase1-stage1.md",
        f"""# ADR-0002 — Open Phase 1 Stage 1: Exploration

- **Status:** accepted  
- **Date:** 2026-07-20  
- **Deciders:** user via /smart-vibe-kit invoke  

## Decision

1. Phase 1 · Stage 1: Exploration is open for {name}.
2. In scope: inventories, analogue notes with citations, open questions.
3. Forbidden: implementation fiction, fake APIs, pixel UI as authority, clinical claims.

## Verification

| Check | Artifact |
|-------|----------|
| Tasks index | docs/tasks.md Next action |
""",
    )

    write(
        out / "docs" / "archives" / "README.md",
        """# Archives

Closed phases live here as phase-N-slug.md.

No closed phases yet.
""",
    )

    write(
        out / "docs" / "product" / "overview.md",
        f"""# Product overview — {name}

> **Status:** in_progress  
> **Registry:** tasks 1.1.2–1.1.5  

Offline-first habit tracking for ADHD users with local encryption.

## Verifiable claims

| Claim | Tier | Source | Verified |
|-------|------|--------|----------|
| v1 is single-device offline | P2 | docs/adr/0001-project-charter.md | charter accepted 2026-07-20 |
| No clinical treatment claims in v1 | P2 | docs/adr/0001-project-charter.md | charter accepted 2026-07-20 |

## Users

Adults with ADHD who need low-friction local logging. OPEN QUESTION OQ-01 on platform.

## Open questions

| ID | Question | Status |
|----|----------|--------|
| OQ-01 | Mobile vs desktop for v1? | open |

## Verification (gate checklist)

| Gate | Requirement | Status |
|------|-------------|--------|
| 1 Doc fidelity | Claim table for this doc | in_progress |
| 2 Tests | n/a explore | not_started |
| 3 Runtime | n/a explore | not_started |
""",
    )

    write(
        out / "docs" / "engineering" / "constraints.md",
        f"""# Engineering constraints — {name}

> **Status:** not_started  

## Verifiable claims

| Claim | Tier | Source | Verified |
|-------|------|--------|----------|
| Encryption library not chosen yet | P3 | docs/toolchain-pins.md | TBD — task 1.1.4 |

## Constraints

- Local encrypted store; no cloud sync in v1 (constitution Article VI).
- Do not invent SDK names until toolchain-pins Verified.

## Open questions

| ID | Question | Status |
|----|----------|--------|
| OQ-E01 | Which encryption library? | open |

## Verification (gate checklist)

| Gate | Requirement | Status |
|------|-------------|--------|
| 1 Doc fidelity | Claim table | not_started |
| 2 Tests | n/a explore | not_started |
| 3 Runtime | n/a explore | not_started |
""",
    )

    copy_refs(out)
    copy_skill_script(out)
    print(f"Wrote minimal bootstrap tree to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
