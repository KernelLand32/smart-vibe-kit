# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 2.1.x | Yes |
| 2.0.x | Migration support only |
| < 2.0 | Best effort |

## Reporting

Report suspected vulnerabilities privately to the project owner. Include the affected version, reproduction steps, impact, and any proposed mitigation. Do not include credentials or unrelated personal data.

## Safety boundaries

SVK refuses filesystem roots, home directories, unowned or drifted installation replacements, unsafe governed paths, symbolic-link/reparse escapes, and ambiguous project overwrites. Scaffold, migration, and install operations validate staged output before commit. Task changes use revision-bound leases, a transition lock, durable transactions, verifier receipts, post-change checks, and rollback on detected failure. A security bug that bypasses one of these boundaries should be treated as high priority.
