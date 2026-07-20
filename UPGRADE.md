# Upgrade guide

## Skill package (Cursor / Claude / Codex / Gemini / shared)

1. Get Smart Vibe Kit **1.0.0** (or newer).  
2. Re-run:

```bash
python scripts/install.py --target all --scope user
# or one shared path:
python scripts/install.py --target agents --scope user
```

Previous installs become `*.bak-TIMESTAMP` unless `--no-backup`.  
3. Confirm:

```bash
python scripts/verify_skill_package.py
python scripts/install.py --list
```

Installing the skill does **not** rewrite project `docs/`. Tests and `gen_minimal_tree.py` stay in the source repo only. The golden example is copied when `examples/offline-habit-tracker/` exists in the package you install from.

## Existing bootstrapped projects

To align a project with the **current** skill’s required structure:

1. Copy missing templates from the skill `assets/templates/` (constitution, toolchain-pins, research files, archives README).  
2. Copy `references/checklists/*` → `docs/checklists/` and `references/workflows/*` → `docs/workflows/` (includes `refresh.md`).  
3. Ensure `docs/_templates/phase-archive.md` exists.  
4. Replace project verifier with skill `scripts/verify_structure.py`.  
5. Update `AGENTS.md` quick commands to:

```text
python scripts/verify_structure.py --root .
python scripts/verify_structure.py --root . --bootstrap
```

6. Run:

```bash
python scripts/verify_structure.py --root . --bootstrap
```

7. Fix until exit 0. Prefer **extend** / **refresh** (see `docs/workflows/refresh.md`) over deleting accepted ADRs.

There are still **no** additional slash commands — use `docs/workflows/` procedures by name.
