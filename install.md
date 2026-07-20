# Install guide

Cross-platform installer for **Windows, macOS, and Linux**. One Python entrypoint; PowerShell / Bash wrappers call it.

## What “install” means

Copy **manifest-listed** files into AI host skill directories so `/smart-vibe-kit` is available. Installing does **not** create project docs — invoking the command does.

Canonical command:

```bash
python scripts/install.py --target all --scope user
```

## Recommended targets

| Target | User path | Project path | Why |
|--------|-----------|--------------|-----|
| **agents** (recommended single) | `~/.agents/skills/smart-vibe-kit` | `.agents/skills/smart-vibe-kit` | Shared Agent Skills convention — Cursor, Gemini CLI, Codex project, and others |
| `cursor` | `~/.cursor/skills/…` | `.cursor/skills/…` | Cursor native |
| `claude` | `~/.claude/skills/…` | `.claude/skills/…` | Claude Code (+ many hosts that also scan `.claude/skills`) |
| `codex` | `~/.codex/skills/…` | `.agents/skills/…` | OpenAI Codex |
| `gemini` | `~/.gemini/skills/…` | `.gemini/skills/…` | Gemini CLI native |
| `all` | all of the above | all (deduped) | Maximum coverage |

`all` **dedupes** identical paths (e.g. Codex project and `agents` project both resolve to `.agents/skills/smart-vibe-kit`).

## Commands

```bash
# Everything (user-wide)
python scripts/install.py

# One shared path (often enough)
python scripts/install.py --target agents --scope user

# Project-scoped for a team repo
python scripts/install.py --target all --scope project --project-root /path/to/repo

# Dry run / list / uninstall / symlink (dev)
python scripts/install.py --what-if --target all
python scripts/install.py --list
python scripts/install.py --uninstall --target cursor --scope user
python scripts/install.py --link --target agents --scope user

# Claude legacy slash file (optional)
python scripts/install.py --target claude --also-legacy-claude-command
```

### Windows (PowerShell)

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -Target agents -Scope user
.\scripts\install.ps1 -Target all -Scope project -ProjectRoot .
.\scripts\install.ps1 -List
.\scripts\install.ps1 -Uninstall -Target gemini
.\scripts\install.ps1 -AlsoLegacyClaudeCommand
```

Requires Python 3 on `PATH` (`py -3`, `python`, or `python3`).

### macOS / Linux

```bash
chmod +x scripts/install.sh
./scripts/install.sh                 # all user
./scripts/install.sh agents user
./scripts/install.sh all project "$(pwd)"
./scripts/install.sh --list
./scripts/install.sh --uninstall --target cursor --scope user
ALSO_LEGACY_CLAUDE_COMMAND=1 ./scripts/install.sh claude user
NO_BACKUP=1 ./scripts/install.sh all user
SVK_LINK=1 ./scripts/install.sh agents user
```

## Host compatibility notes

| Host | Discovers |
|------|-----------|
| **Cursor** | `.agents/skills`, `.cursor/skills`, also `.claude/skills` + `.codex/skills` |
| **Claude Code** | `~/.claude/skills`, `.claude/skills` |
| **OpenAI Codex** | `~/.codex/skills`, `.agents/skills` |
| **Gemini CLI** | `~/.gemini/skills` / `.gemini/skills`, and `~/.agents/skills` / `.agents/skills` |
| **VS Code / Copilot / others** | Often `.claude/skills` and/or `.agents/skills` (varies by build) |

Manifest: [scripts/install-manifest.txt](scripts/install-manifest.txt). Excludes `.git`, `tests/`, `gen_minimal_tree.py`.

By default an existing install is renamed to `smart-vibe-kit.bak-YYYYMMDD-HHMMSS`.

## Verify

```bash
python scripts/verify_skill_package.py
python scripts/install.py --list
```

## Uninstall

```bash
python scripts/install.py --uninstall --target all --scope user
```

Also remove `.claude/commands/smart-vibe-kit.md` if you used `--also-legacy-claude-command`.
