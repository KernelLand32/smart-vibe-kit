# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 2.0.x | Yes |
| < 2.0 | Best effort |

## Reporting

Report suspected vulnerabilities privately to the project owner. Include the affected version, reproduction steps, impact, and any proposed mitigation. Do not include credentials or unrelated personal data.

## Safety boundaries

SVK refuses filesystem roots, home directories, unowned installation replacements, unsafe manifest paths, and ambiguous project overwrites. Scaffold and install operations validate staged output before commit. Task-state updates use ownership locks, transaction records, post-change checks, and rollback on detected failure. A security bug that bypasses one of these boundaries should be treated as high priority.
