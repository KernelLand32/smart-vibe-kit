# smart-vibe-kit

Bootstrap the **full** Smart Vibe Kit process tree in the **current workspace** from a project idea.

**Only slash command:** `/smart-vibe-kit <project idea>`  
**Example:** `/smart-vibe-kit offline-first habit tracker for ADHD with local encryption`

## How to execute

1. Treat everything after the command name as the **project idea** (ask once if missing).  
2. Open and follow the installed skill package completely:

   - `%USERPROFILE%\.cursor\skills\smart-vibe-kit\SKILL.md`  
   - Especially `references/required-structure.md` (canonical tree — do not invent a shorter list)  
   - `references/research-gate.md`, `references/bootstrap.md`  
   - `assets/templates/`, `scripts/verify_structure.py`  

3. Finish with:

```bash
python scripts/verify_structure.py --root . --bootstrap
```

Partial output is a failed run. Do not create other slash commands.
