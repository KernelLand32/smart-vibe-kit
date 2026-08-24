# ADR 0001: Project charter

Project: **Pocket List**

Status: **accepted**

## Context

Build a small offline command-line task list for one person. The program stores its data locally and keeps working without an internet connection.

## Decision

Use the **lean** SVK profile with these modules: core, product.

## Consequences

- The scaffold grows from project signals rather than a fixed file quota.
- Machine-readable state controls task progression.
- A human must accept this charter before autonomous task progression.

## Acceptance

Accept with `svk-next finish --task 1.1.2 --owner <owner> --evidence <file>` after reviewing this document.
