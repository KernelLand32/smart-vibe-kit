# Gemini CLI adapter notes

1. Install via:

```bash
python scripts/install.py --target gemini --scope user
# or shared path (also discovered by Gemini):
python scripts/install.py --target agents --scope user
```

2. Discovery (Gemini CLI):

| Scope | Paths |
|-------|--------|
| User | `~/.gemini/skills/`, `~/.agents/skills/` |
| Workspace | `.gemini/skills/`, `.agents/skills/` |

Within the same tier, `.agents/skills` takes precedence over `.gemini/skills`.

3. Entrypoint remains `SKILL.md`. Invoke `/smart-vibe-kit <project idea>` or ask Gemini to run the smart-vibe-kit skill.

4. No Gemini-specific extra files are required beyond the skill package.
