# Toolchain pins — {Project}

**Authority:** This file is the only place agents may read version pins from.  
Do not invent versions. Prefer `[ASSUMPTION]` or `TBD` until verified.

| Component | Pin | Source | Verified |
|-----------|-----|--------|----------|
| Language / runtime | TBD | | TBD |
| Package manager | TBD | | TBD |
| Key framework / SDK | TBD | | TBD |
| CI / test runner | TBD | | TBD |

## Verify commands

```text
# Replace with real pin-check commands for this stack
{verify-toolchain-script}
```

## Rules

1. Update this file in the same change as a pin bump.  
2. Gate 1 fails if docs claim a version that disagrees with this table.  
3. Exploration stage may leave rows `TBD` — do not mark implement tasks `done` on TBD pins.
