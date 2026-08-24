# Agent operating contract

Project: **Pocket List**

This repository uses Smart Vibe Kit 2.0 as a small, evidence-backed project operating system.

## Current objective

3.2.1 — Implement and verify: List unfinished tasks after restarting the program

## Working rules

- Read [.svk/project.json](.svk/project.json), [.svk/state.json](.svk/state.json), and [docs/tasks.md](docs/tasks.md) before changing project artifacts.
- Work on only the exact `next_action` recorded in state.
- Never infer permission for destructive actions, external publication, spending, secrets, or production changes.
- Record verifiable evidence before marking work complete.
- Run the SVK check action after editing operating documents.
- Stop after one task when using SVK Next.

## Selected operating modules

core, product

## Navigation

- [Project constitution](docs/constitution.md)
- [Task ledger](docs/tasks.md)
- [Artifact registry](docs/registry.md)
- [Verification strategy](docs/verification.md)
