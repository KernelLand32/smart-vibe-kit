# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.3.x   | Yes |
| < 1.3   | Best effort |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Prefer one of:

1. **GitHub Private Vulnerability Reporting** (Settings → Security → Enable private vulnerability reporting on the repository, then use **Report a vulnerability** on the Security tab).  
2. If private reporting is not enabled yet, open a **private security advisory** draft once you are a maintainer, or contact the repository owners through GitHub (users with commit access).

Include:

- Description of the issue and impact  
- Steps to reproduce  
- Affected version / commit  
- Any suggested fix  

We aim to acknowledge reports within **7 days** and to share a remediation plan when practical. Timelines vary for a small volunteer-maintained skill package.

## Scope

In scope:

- The installers and verifiers (`scripts/`)  
- Instructions that could cause unsafe agent behavior if followed  
- Supply-chain issues in this repository’s release artifacts  

Out of scope:

- Bugs in third-party AI hosts (Cursor, Claude Code, Codex, Gemini CLI, …)  
- Misuse of `/smart-vibe-kit` on untrusted workspaces without reviewing agent actions  
- Vulnerabilities only in projects *generated* by the skill (those belong to the generated repo)

## Safe use note

Smart Vibe Kit is an Agent Skill: it tells an AI agent how to write files and run commands in a workspace. Treat agent sessions like untrusted automation—review diffs and commands, especially when research or install scripts run.
