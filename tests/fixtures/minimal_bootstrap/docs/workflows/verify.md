# verify

Prove readiness with the three gates. See [../checklists/done.md](../checklists/done.md) (project: `docs/checklists/done.md`).

## Steps

1. **Doc fidelity** — fill Verified columns; run:

   ```bash
   python scripts/verify_structure.py --root .
   ```

2. **Tests** — run the automated suite that covers the change; fix or fail.  
   - Explore/process waiver: skip only if `docs/verification-gates.md` waiver rules apply; log `waiver: explore-doc` or `waiver: process`.  
3. **Runtime** — run the real command/host smoke; capture report path or log snippet (unless waiver).  
4. Prefer automating host/smoke checks when a harness exists; document what remains manual.  
5. Only then set task status `done` and write a revision-log line with evidence.  

## Fail

- Any required gate fails → remain `in_progress` or `blocked`  
- Do not claim “works” without the command used  

## Evidence shape

```text
[VERIFIED: {command} YYYY-MM-DD] → {report path or exit 0 summary}
```
