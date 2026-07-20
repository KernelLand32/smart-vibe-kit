# Shared `.agents/skills` adapter notes

This is the **recommended single install** for cross-host use.

```bash
python scripts/install.py --target agents --scope user
python scripts/install.py --target agents --scope project --project-root .
```

| Scope | Path |
|-------|------|
| User | `~/.agents/skills/smart-vibe-kit/` |
| Project | `.agents/skills/smart-vibe-kit/` |

Hosts known to load this convention include **Cursor**, **Gemini CLI**, **OpenAI Codex** (project scope), and other Agent Skills–compatible agents. Claude Code still prefers `~/.claude/skills` — use `--target all` or also install `--target claude` if you need Claude Code specifically.
