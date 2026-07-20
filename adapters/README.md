# Adapters

The canonical package is the **Agent Skills** directory: `SKILL.md` + `references/` + `assets/` + `scripts/`.

**Installer:** `python scripts/install.py` (Windows / macOS / Linux). Wrappers: `install.ps1`, `install.sh`.

**Only slash command across all hosts:** `/smart-vibe-kit`.

| Target | User path | Project path | Notes |
|--------|-----------|--------------|-------|
| **agents** | `~/.agents/skills/smart-vibe-kit/` | `.agents/skills/smart-vibe-kit/` | Shared convention — start here |
| cursor | `~/.cursor/skills/…` | `.cursor/skills/…` | [cursor/](cursor/) |
| claude | `~/.claude/skills/…` | `.claude/skills/…` | [claude/](claude/) (+ optional legacy command) |
| codex | `~/.codex/skills/…` | `.agents/skills/…` | [codex/](codex/) |
| gemini | `~/.gemini/skills/…` | `.gemini/skills/…` | [gemini/](gemini/) |

See [../install.md](../install.md) and [../README.md](../README.md).
