---
name: svk-check
description: Run deterministic verification of an SVK project, including strict schemas, plan/state agreement, governed files, links, receipts, freshness, leases, and transactions. Use only when the user explicitly invokes SVK Check or asks to run this named audit.
metadata:
  version: "2.1.0"
---

# SVK Check

This action is explicit-only. Checking authorizes an audit, not repair.

1. Run `python scripts/entry.py --root <project>`. This checks governed Markdown only.
2. Use `--scope all-docs` only when the user asks to audit every Markdown file in the repository.
3. Report `PASS`, `WARN`, `BLOCKED`, or `ERROR` and every stable diagnostic code.
4. Distinguish missing structure, semantic drift, stale/missing receipts, live coordination state, and recoverable journal issues.
5. Do not rewrite files, remove leases, or recover transactions automatically.
6. Package maintainers may use `python scripts/entry.py --package --root <skill-bundle>` for the distributable bundle.

See [the diagnostic contract](references/contract.md).
