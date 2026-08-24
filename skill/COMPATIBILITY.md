# Harness compatibility

Last reviewed: 2026-08-23. [`compatibility.json`](compatibility.json) contains the machine-readable paths, invocation forms, policy adapters, source links, and validation flags.

Compatibility is reported at the harness level because the harness controls skill discovery, commands, tools, filesystem access, and approvals. Rows without runtime certification should be treated as beta integrations.

| Harness | Explicit use | Support level |
|---|---|---|
| OpenAI Codex | `$svk-interview` and the other `$svk-*` names, or the host skill selector | Package metadata validated; runtime integration not yet certified |
| Cursor | `/svk-*` | Documented native paths and explicit-only policy adapter |
| Claude Code | `/svk-*` | Documented native paths and explicit-only policy adapter |
| xAI Grok Build | `/svk-*` from shared `.agents` skills | Documented shared path and explicit-only policy adapter |
| GitHub Copilot CLI | Name the `svk-*` skill explicitly; `/skills` manages discovery | Documented shared path; activation remains host-managed |
| Qwen Code | `/svk-*` or `/skills` | Documented native paths and explicit-only policy adapter |
| Kimi Code CLI | `/skill:svk-*` | Documented native paths and camelCase explicit-only adapter |
| Gemini CLI | Named request plus activation consent; `/skills` manages skills | Supported through host-managed activation; explicit-only package policy is unavailable |
| Google Antigravity | Named request or host skill UI | Discovery paths supported; activation and policy behavior remain host-managed |
| OpenCode | Skill tool or named request | Discovery supported; host permissions control access |
| Goose | `/skills <name>` or named request | Shared `.agents` packaging |
| Roo Code | Named request | Shared `.agents` packaging |
| Junie | `/svk-*` or `$svk-*` | Shared `.agents` packaging |
| Cline | `/svk-*`, a named request, or the Skills menu | Native `.cline/skills` packaging |
| Kiro | Name the `svk-*` skill or use the Agent Steering & Skills panel | Native path packaging; activation remains host-managed |
| Windsurf | `@svk-*` or the Skills panel | Native workspace and global packaging |

The source documentation for every row is linked in [`compatibility.json`](compatibility.json), including [OpenAI](https://developers.openai.com/codex/skills/), [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Kimi Code](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/skills.md), and [Antigravity](https://antigravity.google/docs/skills).

## Models are not harnesses

DeepSeek, GLM, MiniMax, Qwen, Kimi, and other model families can run inside different products. A model name alone does not define skill folders, invocation syntax, tools, or permissions. Evaluate the complete harness-and-model combination.

## Operating systems

SVK requires Python 3.8+ and uses only the standard library. Windows is verified for 2.0.0. macOS and Linux support is preview until runtime certification is available. The supplied CI matrix covers Windows, macOS, and Linux on Python 3.8 and 3.12.
