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

Begin with an explicit cooperative human attestation, then finish task 1.1.2 after reviewing this document. The attestation records what the caller says happened; it is not authenticated identity.
