# Codex / OpenAI Agents adapter notes

1. Install:

```bash
python scripts/install.py --target codex --scope user
python scripts/install.py --target agents --scope project --project-root .
```

2. Paths:

| Scope | Path |
|-------|------|
| User | `~/.codex/skills/smart-vibe-kit/` |
| Project | `.agents/skills/smart-vibe-kit/` |

3. Entrypoint remains `SKILL.md` (agentskills.io).  
4. **Only slash command / skill invoke:** `/smart-vibe-kit <project idea>`.  
5. If your Codex build requires an explicit allow-list, add a skills entry whose path is the install folder:

```yaml
# Illustrative only — confirm key names for your Codex version
skills:
  - name: smart-vibe-kit
    path: ~/.codex/skills/smart-vibe-kit
```
