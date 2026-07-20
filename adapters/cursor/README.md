# Cursor adapter notes

1. Install:

```bash
python scripts/install.py --target cursor --scope user
# Cursor also loads the shared path:
python scripts/install.py --target agents --scope user
```

2. Cursor discovers skills from:

| Scope | Paths |
|-------|--------|
| User | `~/.cursor/skills/`, `~/.agents/skills/`, also `~/.claude/skills/`, `~/.codex/skills/` |
| Project | `.cursor/skills/`, `.agents/skills/`, also `.claude/skills/`, `.codex/skills/` |

3. Directory name must match frontmatter `name: smart-vibe-kit`.  
4. **Only slash command:** `/smart-vibe-kit <project idea>`.  
5. `disable-model-invocation: true` — user must invoke; the agent should not auto-bootstrap.  
6. Optional stub `adapters/cursor/smart-vibe-kit.command.md` points at `SKILL.md`; the full skill install is enough.
