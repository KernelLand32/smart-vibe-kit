# Claude Code adapter notes

1. Install:

```bash
python scripts/install.py --target claude --scope user
# Optional legacy command file for older Claude Code command loaders:
python scripts/install.py --target claude --also-legacy-claude-command
```

2. Paths:

| Scope | Skills | Legacy command (optional) |
|-------|--------|---------------------------|
| User | `~/.claude/skills/smart-vibe-kit/` | `~/.claude/commands/smart-vibe-kit.md` |
| Project | `.claude/skills/smart-vibe-kit/` | `.claude/commands/smart-vibe-kit.md` |

3. Many other tools also scan `.claude/skills` for compatibility.  
4. **Only slash command:** `/smart-vibe-kit`. See `adapters/claude/smart-vibe-kit.md` for the thin legacy command stub.
