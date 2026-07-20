# Contributing to Smart Vibe Kit

Thanks for contributing. This repository is an [Agent Skills](https://agentskills.io/specification) package: instructions + templates + scripts that agents run via `/smart-vibe-kit`.

## Quick start (developers)

```bash
python scripts/verify_skill_package.py
python -m unittest discover -s tests -v
python scripts/install.py --what-if --target agents --scope user
```

Regenerate the golden example / test fixture (dev only):

```bash
python scripts/gen_minimal_tree.py --out examples/offline-habit-tracker --name HabitVault
python scripts/gen_minimal_tree.py --out tests/fixtures/minimal_bootstrap
python scripts/verify_structure.py --root examples/offline-habit-tracker --bootstrap --strict
```

## What to change where

| Area | Location |
|------|----------|
| Slash entry / procedure | `SKILL.md` |
| Mandatory bootstrap tree | `references/required-structure.md`, `references/bootstrap.md` |
| Method / constitution | `references/method.md`, `references/constitution.md` |
| Templates | `assets/templates/` |
| Installer hosts/paths | `scripts/install.py`, `skill.json`, `install.md` |
| Verifiers | `scripts/verify_structure.py`, `scripts/verify_skill_package.py` |
| Install file list | `scripts/install-manifest.txt` |

**Do not** add extra slash commands. Ongoing work stays as procedures under `docs/workflows/` after bootstrap.

Keep the package **generic**: no absolute home-directory paths, no personal emails in committed files. `python scripts/verify_skill_package.py` runs a privacy scan.

## Pull requests

1. Fork and branch from `main` (or the default branch).  
2. Make focused changes; bump `version` in `SKILL.md` and `skill.json` together when behavior changes.  
3. If you add installable files, update `scripts/install-manifest.txt`.  
4. Ensure CI checks pass (verify + unit tests).  
5. Open a PR with: what changed, why, and how you tested.

## Issues

Use the issue templates when possible. Include host (Cursor / Claude / Codex / Gemini), OS, and install command.

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md) — do not file public issues for vulnerabilities.
