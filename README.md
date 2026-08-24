# Smart Vibe Kit 2.0.0

**Give an AI agent a project it can understand, continue, and hand off.**

Smart Vibe Kit (SVK) helps you start a software project with an AI coding agent without leaving the project trapped inside one long chat.

You begin with an idea. SVK asks the questions that matter, writes the answers into the project, and creates a practical task list. From then on, any supported agent can open the folder, see what has happened, find the next task, and move the project forward one step at a time.

SVK does not choose your framework or generate the whole application during setup. It creates the working structure around the application: goals, boundaries, decisions, tasks, checks, and a small amount of machine-readable state.

## Contents

- [Why SVK exists](#why-svk-exists)
- [The philosophy](#the-philosophy)
- [The four SVK actions](#the-four-svk-actions)
- [What does SVK create?](#what-does-svk-create)
- [Requirements](#requirements)
- [Install SVK](#install-svk)
- [Use SVK in your harness](#use-svk-in-your-harness)
- [Write a useful first prompt](#write-a-useful-first-prompt)
- [Start your first project](#start-your-first-project)
- [Come back in a later session](#come-back-in-a-later-session)
- [How SVK decides which files you need](#how-svk-decides-which-files-you-need)
- [How tasks, locks, and evidence work](#how-tasks-locks-and-evidence-work)
- [Use the Python runtime directly](#use-the-python-runtime-directly)
- [Safety](#safety)
- [Compatibility](#compatibility)
- [Current limitations](#current-limitations)
- [Troubleshooting](#troubleshooting)
- [For contributors](#for-contributors)

## Why SVK exists

Imagine starting an application with an AI agent on Monday.

During the conversation, you explain that the first version is for one person, must work offline, and should not require an account. The agent asks useful questions. Together you decide that sync and collaboration can wait. It writes some code, and by the end of the session the project seems to be moving in the right direction.

On Tuesday, you open a new chat.

The new agent can see the code, but it cannot see the reasoning that produced it. An account system now looks like a sensible addition. Cloud storage looks like the obvious way to support several devices. Neither choice is absurd, but both contradict decisions made the day before.

This is the problem SVK is built around. It is not mainly that AI agents are incapable. It is that the working understanding of a project often lives in the least durable place: the current conversation.

### Code does not tell the whole story

A repository may show that SQLite is installed, but not whether it was chosen for privacy, portability, or convenience. It may show that there is no login screen, but not whether accounts are postponed or forbidden. It may contain an unfinished function without saying whether that function is the current priority.

Without those explanations, a new agent has to infer intent from implementation. That works until several interpretations are plausible.

### A large plan is not enough either

A single planning document can capture the original idea, but it usually becomes less useful as the project changes. It may say what should happen eventually without saying what is active now. It may mark an item complete without recording what proved it. Two sessions can also edit the plan in incompatible ways.

SVK therefore keeps both readable project documents and a small machine-readable state. The documents explain the project to people and agents. The state records facts that should not be guessed, such as the active task, its dependencies, and whether the project charter has been accepted.

### “Continue working” is too open-ended

An agent asked to continue autonomously has to decide how far “continue” extends. Does it complete one function, a feature, the entire backlog, a deployment, or a public release? The longer it runs, the more likely it is to cross a boundary that the user never meant to delegate.

SVK replaces that vague instruction with a smaller promise: find the current task, complete or block that task, record what happened, and stop. The user remains in control of when the next unit begins.

### The goal is a project another agent can continue

SVK does not store entire conversations. Discussion is useful while decisions are being made, but most of it is unnecessary once the outcome, constraints, and next task have been recorded.

Instead, it preserves the things a capable new agent needs in order to make the next sound decision:

- the intended outcome and the user it serves;
- explicit boundaries and non-goals;
- decisions that would otherwise be easy to reverse accidentally;
- the current task and its dependencies;
- unresolved questions and blockers;
- evidence supporting work already marked complete.

With those facts in the repository, another agent can continue without access to the earlier conversation.

## The philosophy

SVK is based on a division of responsibility between the human, the language model, the runtime, and the repository.

### The conversation is a workshop; the repository is the record

Conversation is where ideas are explored. People change their minds, compare alternatives, and answer follow-up questions there. Saving all of that as permanent context would create noise.

The repository receives the result of that thinking: the agreed goal, important constraints, open decisions, current work, and evidence. This keeps the handoff smaller and more useful than a transcript dump.

### The model handles meaning; code handles invariants

A language model is well suited to understanding a rough idea, noticing missing information, explaining tradeoffs, doing research, and adapting the work to the project.

It is not the best place to enforce rules such as “exactly one task is active,” “do not overwrite an existing scaffold,” or “a completed task must have evidence.” Those rules should behave the same way no matter which model is running.

SVK therefore asks the model to determine what the project means and uses deterministic Python code for the bookkeeping that must be repeatable.

```text
Human intent -> model understands and clarifies it -> runtime records and validates it
```

This is also why the model does not freely invent a different planning structure for every project. It identifies the project’s needs; the runtime maps those needs to maintained document types.

### Refresh rebuilds context from the current project

At the start of a session, Refresh reads the stored project profile, task state, evidence, locks, and validation result. It returns the current task and the information needed to resume it.

This briefing comes from the files as they exist now, so it can be checked and repeated. It does not depend on chat history or a model retaining details between sessions.

### Autonomy is useful when its boundary is visible

SVK is designed to make an agent more independent inside one task, not to give it unlimited authority over the project.

Within the active task, the agent should inspect, reason, edit, test, and recover from ordinary problems without asking the user about every small step. At the task boundary, it stops. Destructive operations, publication, spending, production changes, and human approvals still require whatever permission they would normally require.

### Add documents only when they have a job

More documentation is not automatically better. Extra files cost attention, can disagree with one another, and eventually become stale.

SVK begins with a core that every project needs, then adds areas only when the interview reveals a reason. A user interface creates design questions. Sensitive data creates security questions. Deployment creates operational questions. Each added document has a defined decision or handoff purpose.

### Completion is a claim; evidence is what supports it

An agent can be confident and wrong. A green checkmark in a task list is only a statement unless something records how the result was checked.

SVK asks for a short evidence record when a task finishes: what changed, which commands or tools were used, which artifacts matter, and whether the result passed. This does not prove every possible property of the work, but it gives the next agent something concrete to inspect.

### Human approvals remain human decisions

Some decisions change the meaning or risk of the project. Accepting the initial charter, approving regulated claims, or taking over another agent’s locked task are examples.

SVK calls these human gates. The runtime can record that a gate was entered, but it cannot turn an agent’s judgment into human approval. The person remains part of the process where their authority is actually required.

### The workflow stays consistent across harnesses

The four SVK actions have the same responsibilities in every supported coding harness, while installation paths and invocation syntax follow each harness's own interface.

Codex uses `$svk-next`, many tools use `/svk-next`, Kimi uses `/skill:svk-next`, and Windsurf uses `@svk-next`. Some hosts ask the model to activate a named skill instead. SVK keeps the workflow consistent while documenting the real interface of each host.

Together, these ideas produce the normal flow:

```text
Your idea
   |
   v
Interview -> durable project understanding + one current task
                                               |
                                               v
                                             Next
                                               |
                               one task completed or blocked

Refresh -> rebuild the current briefing from the repository
Check   -> compare the repository’s records and report disagreements
```

## The four SVK actions

The actions are easiest to understand as one continuous project. [`examples/pocket-list`](examples/pocket-list/README.md) contains the complete state described below, including working application code and tests.

**Pocket List** is an offline command-line task list for one person. Its first release must add a task, list unfinished tasks after a restart, and mark a task complete. It uses Python's standard library, stores human-readable JSON locally, and excludes accounts, sync, collaboration, and graphical interfaces.

### SVK Interview

Interview turns an idea into the durable starting point described above. Use it once, in a new or unscaffolded project folder.

The example's [saved interview answers](examples/pocket-list/interview-answers.json) supplied the scope, goals, constraints, platforms, and risk signals. The opening idea can be summarized as:

```text
Build a small offline command-line task list for one person.
Save human-readable JSON locally and use only Python's standard library.
The first release must add, list, and complete tasks.
Do not add accounts, sync, collaboration, or a graphical interface.
```

Interview classified the project and returned this result:

```text
Project: Pocket List
Profile: Lean
Areas selected: Core, Product
Health check: PASS
Next task: 1.1.2 — Review and accept the project charter
```

Why did it select Product? Because this is a user-facing tool with behaviors that need requirements and acceptance examples. Why did it not select Design, Operations, Security, or Collaboration? The idea has no graphical interface, deployment, sensitive data, or team workflow.

The **Lean** label summarizes the selection. The useful output is the recorded scope, non-goals, task sequence, verification rules, and one active task. Interview also created three implementation tasks from the three accepted goals, followed by a release-readiness task.

### SVK Next

Next performs the one task that the project currently identifies. It does not choose a more interesting task or continue through the rest of the list.

The first task is charter review. Beginning it without human approval produces this refusal:

```text
Task 1.1.2 is a human gate; begin again with explicit --allow-human-gate.
```

That is expected behavior. The tool prepared the charter; it did not approve the charter on the user’s behalf.

After the charter was reviewed and accepted, the first Next run finished that task and stopped:

```text
Completed: 1.1.2 — Review and accept the project charter
Promoted:  2.1.1 — Confirm requirements and acceptance criteria
Check:     PASS
```

The second Next run worked on task `2.1.1`. It turned the idea into seven behavioral requirements, explicit exclusions, storage decisions, and acceptance examples. It then recorded the affected files and promoted the first implementation goal:

```text
Completed: 2.1.1 — Confirm requirements and acceptance criteria
Changed:   docs/product/requirements.md
           docs/product/acceptance.md
Promoted:  3.1.1 — Implement and verify: Add a task and save it locally
Check:     PASS
Stopped:   yes
```

The third Next run moved from planning into application code. It implemented only the `add` goal, including strict JSON validation, atomic local writes, four tests, and a command-line smoke check:

```text
Completed: 3.1.1 — Implement and verify: Add a task and save it locally
Changed:   pocket_list.py
           tests/test_pocket_list.py
Tests:     4 passed
Promoted:  3.2.1 — Implement and verify: List unfinished tasks after restarting the program
Check:     PASS
Stopped:   yes
```

This is the intended unit of autonomy: understand one task, do its project work, verify it, update the durable record, and return control to the user. The three Next runs were separate actions; none continued into the task it had just promoted.

If the work cannot be completed, Next records the blocker and leaves that task as the next action. It never treats “blocked” as “skip this and carry on.”

### SVK Refresh

Refresh answers, “If I opened this folder with no previous conversation, what would I need to know right now?” It reads the project and does not change it.

After the three Next runs above, Refresh returned:

```text
Project: Pocket List
Profile: Lean
Areas: Core, Product
Stage: execution
Active task: 3.2.1 — Implement and verify: List unfinished tasks after restarting the program
Blocker: none
Health check: PASS
```

The result identifies the exact implementation goal to resume. The agent can then read that task's requirements, acceptance examples, current code, and tests instead of loading every project document.

### SVK Check

Check compares the project’s records. It is useful after manual edits, when Refresh reports a problem, or before an important milestone.

On the healthy Pocket List project, it returned:

```json
{
  "diagnostics": [],
  "result": "PASS"
}
```

For example, changing task `3.2.1` to `pending` in `docs/tasks.md` while the machine state still calls it `in_progress` produces this diagnostic:

```text
Code:    SVK-TASK-STATUS-DRIFT
Level:   ERROR
Message: docs/tasks.md statuses differ from state.
Path:    docs/tasks.md
Result:  ERROR
```

Restoring the correct status returns Check to `PASS`. Check does not repair the file itself; deciding which record is correct remains a deliberate action.

Check is read-only. It reports one of four results:

| Result | What it means |
|---|---|
| `PASS` | The required files and records agree with each other. |
| `WARN` | SVK found something worth reviewing, but work can continue. |
| `BLOCKED` | A lock, blocked task, or interrupted update needs attention first. |
| `ERROR` | Required state is missing, malformed, or contradictory. |

Taken together, the four actions have distinct jobs:

```text
Interview decides what project this is.
Next changes the project by one task.
Refresh explains where the project stands.
Check verifies that its records agree.
```

## What does SVK create?

Every project receives a small core set of files:

```text
AGENTS.md                         instructions for any agent working in the repo
docs/constitution.md             project goals, boundaries, and working rules
docs/tasks.md                    the human-readable task list
docs/registry.md                 an index of the project documents
docs/verification.md             how the project will be checked
docs/adr/0001-project-charter.md the initial project decision record

.svk/project.json                the project description and selected modules
.svk/state.json                  the current stage and next action
.svk/evidence.jsonl              evidence from completed tasks
.svk/install.json                information about the scaffold installation
```

SVK does not add documents just because a project sounds large. Interview looks for concrete facts in your answers: who will use the result, whether it has a UI, where it runs, what data it handles, how it will be released, and who is responsible for it. Each fact can activate an additional project area:

| When this sounds like your project | Area and documents added | What they help you decide and record |
|---|---|---|
| The work depends on facts that may be outdated or need evidence, such as laws, prices, scientific claims, market conditions, or a changing external API. | **Research:** `brief.md` and `sources.md` | Which claims the project relies on, which sources support them, when those sources were checked, and what remains uncertain. |
| Someone will use the result and you need a clear definition of useful, correct, and complete behavior. This includes command-line tools, libraries, automations, and internal tools—not only commercial apps. | **Product:** `requirements.md` and `acceptance.md` | Who the users are, what they need to accomplish, how the product should behave, and what observable evidence will show that each requirement works. |
| People will interact with screens, forms, menus, or other visual controls. | **Design:** `system.md` and `accessibility.md` | Page and component behavior, visual consistency, responsive layouts, keyboard use, accessibility expectations, and empty, loading, and error states. |
| The project has multiple components, an API, a database, external integrations, or technical boundaries that another developer or agent must understand. | **Engineering:** `architecture.md` and `interfaces.md` | How components and data fit together, what each interface promises, where failures can occur, and where the system should be tested. |
| The result will be deployed, updated, monitored, backed up, restored, or supported after release. | **Operations:** `runbook.md` and `release.md` | How to build and release it, check its health, respond to incidents, roll it back safely, and recover its data. |
| The project handles accounts, permissions, secrets, payments, personal information, confidential data, or other valuable assets. | **Security:** `threat-model.md` and `data-handling.md` | What needs protection, who or what could misuse it, where trust changes, which safeguards are required, and how data should be stored or removed. |
| A law, contract, certification, or industry rule requires documented controls, traceability, review, or approval. | **Regulated:** `controls.md`, `traceability.md`, and `risk-register.md` | Which obligations apply, how each one is addressed and verified, who owns it, and which risks or exceptions still need approval. |
| Several people or agents will contribute and it may become unclear who decides, reviews, or owns each part. | **Collaboration:** `ownership.md` and `decisions.md` | Area owners, reviewers, decision paths, important decisions and their context, and what a useful handoff must contain. |

These areas can be combined. For example, Pocket List activates **Product** because a person must be able to add, list, and complete tasks. It does not activate **Design** because it has no graphical interface, or **Operations** because its first release is a local command-line program rather than a deployed service. See the resulting files in the [Pocket List worked example](examples/pocket-list/).

Interview creates these as working documents filled with project-specific information, not empty templates. You can review the proposed areas before accepting the project charter.

### Where do the file counts come from?

“10 files or 30 files” is shorthand for a small scaffold versus a much broader one. It refers to files managed by SVK, not the total number of files in your project. Your application source code, tests, images, dependencies, build output, and Git files are separate and are not part of this comparison.

The count is calculated from three parts:

1. **Six core documents** are created for every project: `AGENTS.md`, the constitution, task list, document registry, project charter, and verification plan.
2. **Four machine-readable records** track the project description, current state, evidence, and SVK installation under `.svk/`.
3. **Optional areas** add their working documents. Most add two; the Regulated area adds three.

That produces counts such as:

| Selected structure | Calculation | SVK-managed artifacts |
|---|---:|---:|
| Core only | 6 core documents + 4 state records | **10** |
| Core + Product, as in Pocket List | 6 + 4 + 2 Product documents | **12** |
| Core + Product + Design + Engineering + Operations | 6 + 4 + 8 area documents | **18** |
| Core + every optional area | 6 + 4 + 17 area documents | **27** |

So “30 files” is a rounded way of saying “nearly the full scaffold”; it is not an exact tier or a target. In version 2.0.0, selecting every area produces 27 managed artifacts. SVK may also create internal baseline and transaction records under `.svk/`, so the number shown by your file browser can be higher than the `expected_document_count` in `.svk/project.json`.

The useful question is therefore not “How many files should this project have?” It is “Which decisions must remain clear when another person, model, or session continues the work?” The selected areas answer that question; the file count simply follows from them.

### What are Lean, Standard, Extended, and Regulated profiles?

After choosing the relevant documents, SVK gives the project a short profile label. The label is a summary of the structure the project needs; it is not a subscription tier, a quality rating, or something you normally have to choose yourself.

| Profile | In plain language |
|---|---|
| **Lean** | A low-risk project with only the core and one or two extra areas. A small personal tool is a likely example. |
| **Standard** | The normal case for an application or product with several concerns but no unusually broad or regulated scope. |
| **Extended** | A project with high risk or many connected areas, such as product, design, deployment, security, research, and team coordination. |
| **Regulated** | A project where legal, industry, or formal compliance requirements need explicit records and human approval. |

The profile is calculated from the selected areas. SVK does not select a profile or add documents merely to reach a preferred file count.

## Requirements

- Python 3.8 or newer
- No third-party Python packages
- The complete release folder, with `installer/` and `skill/` beside each other

The installer reads the `skill/` folder during installation, so keep both top-level folders together.

## Install SVK

Run installation commands from the root of this release.

### Install for one user

On Windows:

```powershell
py -3 installer\install.py --target agents
```

You can also use the PowerShell launcher:

```powershell
.\installer\install.ps1 --target agents
```

On macOS or Linux:

```sh
python3 installer/install.py --target agents
```

The `agents` target uses the shared `~/.agents/skills` location. Several harnesses can read skills from there.

For a host-specific location, replace `agents` with the harness ID. For example:

```text
python installer/install.py --target cursor
python installer/install.py --target claude
python installer/install.py --target gemini
python installer/install.py --target qwen
```

You can install several targets together:

```text
python installer/install.py --target claude,cursor,qwen
```

Or install every maintained target:

```text
python installer/install.py --target all
```

The installer avoids duplicate copies when several harnesses share the same destination.

### See every available target

```text
python installer/install.py --list
```

This prints the destination, invocation method, compatibility status, and supporting documentation for each harness.

### Install inside one project

Use project scope when you want the skills to travel with a particular repository:

```text
python installer/install.py --target agents --scope project --project-root /path/to/project
```

Choose the project-specific target if the harness does not read `.agents/skills`. For example:

```text
python installer/install.py --target cursor --scope project --project-root /path/to/project
```

### Preview, update, or uninstall

Preview an installation without writing anything:

```text
python installer/install.py --target all --dry-run
```

Run the same installation command again to update an existing SVK 2.x installation.

Remove an installation:

```text
python installer/install.py --target agents --uninstall
```

The installer marks the folders it owns. It will not replace or remove a same-named folder that does not have an SVK ownership marker.

See [installer/README.md](installer/README.md) for the installer reference.

## Use SVK in your harness

SVK installs four skills: `svk-interview`, `svk-refresh`, `svk-next`, and `svk-check`. The behavior is the same in every harness, but the way you select a skill is not.

The examples below show the exact form to use. If you installed SVK while the harness was open and the skills do not appear, reload its skills or start a new session.

### Quick reference

| Harness | Install target | Start Interview | Find or reload skills |
|---|---|---|---|
| [Codex](https://developers.openai.com/codex/skills/) | `codex` | `$svk-interview Your idea` | Skill selector |
| [Cursor](https://cursor.com/docs/context/skills) | `cursor` | `/svk-interview Your idea` | Type `/` and search for the skill |
| [Claude Code](https://code.claude.com/docs/en/skills) | `claude` | `/svk-interview Your idea` | `/skills` |
| [Grok Build](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/08-skills.md) | `grok` | `/svk-interview Your idea` | `grok inspect` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) | `copilot` | Ask it to use `svk-interview` for your idea | `/skills list` or `/skills reload` |
| [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) | `qwen` | `/svk-interview Your idea` | `/skills` |
| [Kimi Code CLI](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/skills.md) | `kimi` | `/skill:svk-interview Your idea` | Use Kimi’s skill command list |
| [Gemini CLI](https://geminicli.com/docs/cli/using-agent-skills/) | `gemini` | Ask it to activate and run `svk-interview` | `/skills list` or `/skills reload` |
| [Google Antigravity](https://antigravity.google/docs/skills) | `antigravity` | Ask it to use `svk-interview` | Skills UI or a new session |
| [OpenCode](https://opencode.ai/docs/skills/) | `opencode` | Ask it to load and use `svk-interview` | Ask which skills are available |
| [Goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills/) | `goose` | `/skills svk-interview`, then send the idea | `/skills` or `goose skills list` |
| [Roo Code](https://docs.roocode.com/features/skills) | `roo` | Ask it to use `svk-interview` | Restart or check the discovered skills |
| [Junie](https://junie.jetbrains.com/docs/agent-skills.html) | `junie` | `/svk-interview Your idea` or `$svk-interview` | `/skills` |
| [Cline](https://docs.cline.bot/customization/skills) | `cline` | `/svk-interview Your idea` | Skills menu in the Cline panel |
| [Kiro](https://kiro.dev/docs/skills/) | `kiro` | Ask it to use `svk-interview` | Agent Steering & Skills panel |
| [Windsurf / Cascade](https://docs.windsurf.com/windsurf/cascade/skills) | `windsurf` | `@svk-interview Your idea` | Cascade Customizations → Skills |

After Interview, use the same host-specific form for the other three names. For example, Claude Code uses `/svk-next`, Kimi uses `/skill:svk-next`, Codex uses `$svk-next`, and Windsurf uses `@svk-next`. Hosts that use model-led activation should receive an explicit named request for each action.

### Codex

Install with `--target codex`. In Codex, explicitly select a skill with `$`:

```text
$svk-interview Build a private offline-first notes app.
$svk-refresh
$svk-next
$svk-check
```

Type `$` or use the available skill selector to browse installed skills. Codex reads the shared `.agents/skills` locations. SVK also ships Codex policy metadata that prevents automatic invocation.

### Cursor

Install with `--target cursor`. Type `/` in chat, search for the SVK action, and select it:

```text
/svk-interview Build a private offline-first notes app.
```

Cursor normally watches skill folders for changes. If the commands do not appear, open a new chat or restart Cursor. Cursor can also discover shared `.agents/skills`, but the `cursor` target uses its native `.cursor/skills` location.

### Claude Code

Install with `--target claude`, then use the four skills as slash commands:

```text
/svk-interview Build a private offline-first notes app.
/svk-refresh
/svk-next
/svk-check
```

Use `/skills` to view or manage them. If `.claude/skills` did not exist when Claude Code started, restart the session after installing.

### Grok Build

Install with `--target grok`. SVK uses the shared `.agents/skills` path, which Grok Build discovers alongside its native `.grok/skills` path.

Invoke the actions with `/svk-interview`, `/svk-refresh`, `/svk-next`, and `/svk-check`. Use `grok inspect` or `grok inspect --json` to confirm discovery.

### GitHub Copilot CLI

Install with `--target copilot`, reload the skill index, and name the action in your request:

```text
Use the svk-interview skill for this idea: Build a private offline-first notes app.
```

Use `/skills list` to inspect the skills and `/skills reload` after an installation. Copilot CLI documents a `skill` tool and `/skills` management command, but not a universal `/<skill-name>` form for custom skills. The `copilot` target uses its supported shared `.agents/skills` location.

### Qwen Code

Install with `--target qwen`. Use `/skills` to confirm that the four actions are enabled, then run:

```text
/svk-interview Build a private offline-first notes app.
```

Qwen Code watches its skill folders in normal interactive use. Restart bare or non-interactive sessions if a new skill is not detected.

### Kimi Code CLI

Install with `--target kimi`. Kimi namespaces direct skill invocation under `/skill:`:

```text
/skill:svk-interview Build a private offline-first notes app.
/skill:svk-refresh
/skill:svk-next
/skill:svk-check
```

### Gemini CLI

Install with `--target gemini`. Reload and confirm discovery:

```text
/skills reload
/skills list
```

Gemini CLI manages skills through `/skills`, but its documented flow is activation by the agent rather than a direct `/svk-interview` command. Be explicit:

```text
Activate and run the svk-interview skill for this idea: Build a private offline-first notes app.
```

Gemini asks for consent when it activates a skill. Approve that activation if you want the action to run. Use the same wording for `svk-refresh`, `svk-next`, and `svk-check`.

### Google Antigravity

Install with `--target antigravity`. Open the project, confirm the skills in Antigravity’s skill interface if available, and ask for the action by name:

```text
Use the svk-interview skill for this idea: Build a private offline-first notes app.
```

Antigravity documents skill discovery and model-led activation, but not one universal slash form across all of its interfaces. Use the named prompt above unless your current Antigravity interface shows the skill as a selectable command.

### OpenCode

Install with `--target opencode`. OpenCode discovers the shared `.agents/skills` location and exposes discovered skills to the model through its `skill` tool.

Request the skill explicitly:

```text
Load and use the svk-interview skill for this idea: Build a private offline-first notes app.
```

If it is not found, check OpenCode’s `skill` permissions. A matching `deny` rule hides a skill completely.

### Goose

Install with `--target goose`. Goose uses the shared `.agents/skills` location. In the CLI, load Interview and then send the idea:

```text
/skills svk-interview
Build a private offline-first notes app.
```

You can also say, “Use the svk-interview skill for this idea…”. Run `goose skills list` or `/skills` to inspect what Goose discovered. The built-in Skills extension must be enabled; it is enabled by default.

### Roo Code

Install with `--target roo`. Roo discovers `.agents/skills` and selects a matching skill from its description. Because SVK actions are meant to be deliberate, name the action in your request:

```text
Use the svk-interview skill for this idea: Build a private offline-first notes app.
```

Roo indexes skills at startup and watches them for changes. If it chooses the wrong skill, confirm the requested name and make sure another project-level skill is not overriding it.

### Junie

Install with `--target junie`. Junie reads the shared `.agents/skills` location and supports both direct forms:

```text
/svk-interview Build a private offline-first notes app.
```

or reference it in a prompt:

```text
$svk-interview Build a private offline-first notes app.
```

Use `/skills` to rescan, list, enable, or disable skills.

### Cline

Install with `--target cline`. The adapter uses Cline's native `.cline/skills` locations. Cline can also read project-level Claude-compatible skills, but SVK does not rely on that compatibility path for a user install.

Open the Skills menu from the Cline panel and confirm that the four skills are enabled. Then use:

```text
/svk-interview Build a private offline-first notes app.
```

Cline can also select skills automatically. SVK still requires an explicit request, so use the slash command or name the skill directly.

### Kiro

Install with `--target kiro`. Kiro reads `.kiro/skills` and activates relevant skills through the agent. Name the action so the intended skill is unambiguous:

```text
Use the svk-interview skill for this idea: Build a private offline-first notes app.
```

Use the Agent Steering & Skills section in the Kiro panel to inspect, import, or manage the installation. SVK does not claim a direct `/svk-interview` form for Kiro 2.0.0.

### Windsurf / Cascade

Install with `--target windsurf`. The adapter uses `.windsurf/skills` for a project install and `~/.codeium/windsurf/skills` for a user install.

Windsurf skills are invoked with an `@` mention, not a slash command:

```text
@svk-interview Build a private offline-first notes app.
@svk-refresh
@svk-next
@svk-check
```

Use Cascade’s Customizations → Skills panel to inspect them.

### Other Agent Skills hosts

If your harness supports the open Agent Skills folder convention but is not listed above, install with `--target agents`. Then use the host’s normal way of explicitly selecting a skill.

If your tool does not support Agent Skills at all, use the [Python runtime](#use-the-python-runtime-directly) or provide the relevant `SKILL.md` to the agent manually. Aider and raw model APIs fall into this category unless another layer adds skill discovery, filesystem access, and tool execution.

## Write a useful first prompt

Interview will ask follow-up questions, so your first prompt does not need to be a finished specification. It should still give the agent enough to understand the shape of the project.

A useful project idea usually answers some of these questions:

- **What are you building?** Name the product or tool in concrete terms.
- **Who is it for?** A personal tool, a small team, customers, children, clinicians, developers, or someone else?
- **What should people be able to do?** Mention the few outcomes that define the first useful version.
- **Where will it run?** Web, mobile, desktop, command line, a server, or several platforms?
- **What matters most?** Privacy, speed, simplicity, accessibility, offline use, low cost, or another priority?
- **What should the first version leave out?** A clear non-goal can prevent a great deal of wasted work.
- **Are there known constraints or risks?** Examples include a required language, an existing API, sensitive information, payments, legal rules, or a fixed deployment environment.

You do not have to answer every question. Include what you already know and let Interview find the important gaps.

### The same idea, from terrible to excellent

#### Terrible

```text
Make me a notes app.
```

The agent knows the broad category, but almost nothing else. “Notes app” could mean a mobile product, a browser extension, a team wiki, or a command-line tool. Interview can recover by asking many questions, but the first exchange does little work.

#### Meh

```text
Build a cross-platform notes app with a modern UI and lots of useful features.
```

This adds a platform goal and says that a UI matters, but the important words are still vague. “Modern” does not describe an interaction, and “lots of useful features” gives no basis for deciding what belongs in the first version.

#### Good

```text
Build a desktop notes app for Windows, macOS, and Linux. It should let one person create, edit, search, and organize plain-text notes. Keep the interface simple and make the app usable without an internet connection.
```

Now the agent knows the user, platforms, main jobs, interface direction, and offline requirement. Interview can focus on real decisions such as storage, export, accessibility, packaging, and whether formatted text is needed.

#### Best

```text
Build a private, offline-first desktop notes app for individual writers on Windows, macOS, and Linux.

For the first release, users should be able to create, edit, delete, search, tag, and export plain-text notes. Notes should be stored locally and remain usable with no account and no network connection. The interface should be keyboard-friendly and easy to read.

Privacy and reliable local storage matter more than collaboration features. Do not include cloud sync, shared notebooks, mobile apps, or rich-text editing in the first release. I have not chosen a programming language or desktop framework yet and want that decision researched.
```

This version gives Interview enough information to separate known requirements from open decisions. It identifies the user, the first-release outcome, important qualities, explicit non-goals, supported platforms, data expectations, and one decision that still needs research.

It is “best” because the details change the plan—not because it is long. A two-sentence prompt can be excellent for a small, well-defined tool. A two-page prompt can still be poor if it is full of adjectives and never says who the product is for or what success looks like.

### A reusable prompt shape

Use this as a guide, not a form you must fill out:

```text
Build [what] for [who] on [platform or environment].

The first useful version should let them [main outcomes].
[Quality or constraint] matters most because [reason].

Do not include [clear non-goals] in the first version.
Known constraints: [technology, integration, data, budget, legal, or operational facts].
Open decisions I want help with: [questions you have not settled].
```

Good first prompts describe the problem and the boundaries. Avoid choosing technical details just to make the prompt look complete; when a technology decision is genuinely open, say that it is open.

## Start your first project

### 1. Create a new project folder

```text
mkdir offline-notes
cd offline-notes
```

Interview is designed for a new folder. It will not overwrite an SVK-generated path that already exists.

### 2. Start Interview

Write your idea using the guidance above, then use the invocation form for your harness. For example:

```text
Codex:       $svk-interview Build a private offline-first notes app for Windows, macOS, and Linux.
Claude Code: /svk-interview Build a private offline-first notes app for Windows, macOS, and Linux.
Kimi Code:   /skill:svk-interview Build a private offline-first notes app for Windows, macOS, and Linux.
Windsurf:    @svk-interview Build a private offline-first notes app for Windows, macOS, and Linux.
```

For a selector-based host, say:

```text
Use the svk-interview skill for this idea: Build a private offline-first notes app for Windows, macOS, and Linux.
```

### 3. Answer the questions

You do not need to prepare a formal specification. Answer in ordinary language. If you do not know something yet, say so; the interview can record an assumption or leave the matter for a later task.

Before writing files, the agent should summarize what it understood, which project areas it plans to include, and any important assumptions.

### 4. Review the project charter

The project charter is the initial agreement about what you are building. In 2.0.0, reviewing it through task `1.1.2` is the normal path after Interview.

This is intentional. Starting an interview means “help me prepare this project,” not “approve every decision for me.”

### 5. Run Next when you are ready

Invoke `svk-next` using your harness’s syntax. The agent completes only the active task and stops with a short report of what changed and how it was checked.

Run it again when you want to begin the following task.

## Come back in a later session

Start with `svk-refresh` in the project folder. Refresh should tell you:

- what the project is;
- which supporting areas were selected;
- the current stage;
- the active task;
- whether anything is blocked;
- the exact next action;
- whether the stored state is healthy.

If Refresh reports a problem, run `svk-check`. Resolve the reported issue before asking Next to change the project.

You can change models or harnesses between sessions. Install SVK for the new harness, open the same project folder, and start with Refresh. It reconstructs the handoff from the project files without requiring access to the earlier conversation.

## How SVK decides which files you need

An LLM can judge whether a project involves a UI, deployment, sensitive data, regulation, several contributors, or a need for up-to-date research. It is less reliable at inventing a different file tree from scratch every time.

SVK splits those jobs:

1. The agent learns the facts of the project through the interview.
2. The Python runtime maps those facts to a fixed set of useful project areas.
3. Templates for those areas are filled with the project’s actual information.
4. The completed scaffold is validated before it is committed.

The current mapping is:

| Project fact | Area added |
|---|---|
| Every project | Core |
| User-facing behavior | Product |
| A user interface | Product and Design |
| Deployment | Engineering and Operations |
| External integrations | Engineering |
| Sensitive data | Security |
| Work affected by regulation | Research, Security, and Regulated |
| A stated need for current research | Research |
| More than one contributor | Collaboration |

You can request optional areas during the interview. You cannot remove an area that is required by a risk you have identified. For example, marking a project as regulated necessarily adds its research, security, and compliance records.

The agent therefore decides which areas the project needs, while deterministic rules map those areas to known documents. The [file-count explanation](#where-do-the-file-counts-come-from) shows the exact calculation; the count is a result of the project’s needs, not a quota chosen in advance.

## How tasks, locks, and evidence work

### Tasks

The readable task list lives in `docs/tasks.md`. The same task state is stored in `.svk/state.json` so the runtime can validate it.

Until the project is finished, exactly one task should be active. A task can move through these states:

```text
pending -> in_progress -> done
                 \-> blocked -> done
```

A completed task moves at most one dependency-ready task from `pending` to `in_progress`. SVK does not choose a later task just because it looks easier.

### Locks

When Next begins work, it creates `.svk/locks/next.json`. The lock records the task and its owner so two agents do not work on the same task at the same time.

A lock that appears old is not automatic permission to take over. First confirm that the owning agent is no longer working. Forced lock removal is an explicit recovery action.

### Evidence

To finish a task, the agent records:

```json
{
  "summary": "What was established or changed",
  "commands": ["Commands, tools, or checks actually used"],
  "artifacts": ["Relevant files or external evidence"],
  "result": "pass"
}
```

`result` can be `pass`, `fail`, or `partial`, but only `pass` can complete a task. The runtime adds the task ID, owner, and time before appending the record to `.svk/evidence.jsonl`.

## Use the Python runtime directly

Most people should use the four installed skills and let the agent call the runtime. The commands below are useful for automation, debugging, adapter development, or manual recovery.

Run them from the release root.

### Show the standard interview topics

```text
python skill/runtime/svk.py interview --questions
```

### Prepare interview answers

The runtime accepts a JSON file. Only `title` and `idea` are required, but fuller answers produce a better scaffold.

```json
{
  "title": "Offline Notes",
  "idea": "Build a private offline-first notes application.",
  "goals": ["Create and search local notes"],
  "non_goals": ["No hosted collaboration in the first release"],
  "constraints": ["Run on Windows, macOS, and Linux"],
  "platforms": ["Windows", "macOS", "Linux"],
  "integrations": [],
  "team_size": 1,
  "risk": "low",
  "research_tier": 0,
  "user_facing": true,
  "ui": true,
  "deployable": false,
  "sensitive_data": false,
  "regulated": false
}
```

Optional `include_modules` and `exclude_modules` arrays can refine the result. An exclusion cannot remove an area required by the stated project facts, including integrations, team size, research tier, sensitive data, deployment, or regulation.

### Create the scaffold

```text
python skill/runtime/svk.py interview --root /path/to/project --answers /path/to/answers.json
```

The normal workflow creates a proposed charter, lets a person review it, and finishes task `1.1.2` through Next. The lower-level `--charter-accepted` option is intended only for controlled automation that has already captured explicit human approval; it marks the charter complete and promotes the first dependency-ready task during scaffold creation.

### Refresh or check a project

```text
python skill/runtime/svk.py refresh --root /path/to/project
python skill/runtime/svk.py check --root /path/to/project
```

### View and begin the active task

```text
python skill/runtime/svk.py next --root /path/to/project show
python skill/runtime/svk.py next --root /path/to/project begin --owner my-agent
```

If a human has agreed to enter a human-approval task:

```text
python skill/runtime/svk.py next --root /path/to/project begin --owner my-agent --allow-human-gate
```

This flag records that the human agreed to enter the task. It does not let the agent make the approval itself.

### Finish or block a task

After doing the work, create the evidence JSON and finish with the same owner and task ID:

```text
python skill/runtime/svk.py next --root /path/to/project finish --owner my-agent --task 1.1.2 --evidence /path/to/evidence.json
```

If the task cannot be completed:

```text
python skill/runtime/svk.py next --root /path/to/project block --owner my-agent --task 2.1.1 --reason "Required API documentation is unavailable"
```

### Clear a confirmed stale lock

The matching owner can clear its own lock:

```text
python skill/runtime/svk.py next --root /path/to/project clear-lock --owner my-agent
```

Use `--force` only after confirming that no agent is still working under the lock:

```text
python skill/runtime/svk.py next --root /path/to/project clear-lock --force
```

### Verify the distributable skill package

```text
python skill/runtime/svk.py check --package --root skill
```

The runtime prints JSON. Project checks return a nonzero exit code for `ERROR` or `BLOCKED` results.

## Safety

### Creating a project

Interview builds the scaffold in a temporary sibling folder, validates it, checks for collisions, copies it into the project, and validates the result again. If the operation fails, it removes only the paths created by that attempt.

The runtime refuses to scaffold:

- a filesystem root;
- your home directory;
- a project where any generated destination path already exists;
- a staged tree containing symbolic links.

It also records enough transaction information for Check to detect an interrupted update.

### Installing the skills

The installer validates all four skills before writing them. It stages a multi-target install before committing it and rolls back if a later destination fails.

It only updates or removes directories carrying an SVK ownership marker. A folder with the same name but no marker is left alone.

### What an SVK action does not authorize

Running Interview, Refresh, Next, or Check does not grant permission for unrelated destructive actions, production changes, publication, purchases, messages to third parties, or human approvals. The agent still has to follow the permissions and safety rules of its harness.

## Compatibility

SVK compatibility is primarily about the **harness**, not the model. The harness controls skill discovery, commands, filesystem access, tools, and approvals.

For example, a Qwen model running inside Qwen Code has Qwen Code’s skill support. The same model called through a raw API has no skill folder or command system unless the surrounding application provides one.

### Compatibility levels in this release

- **Direct, documented selectors:** Codex, Cursor, Claude Code, Grok Build, Qwen Code, Kimi Code CLI, Junie, Cline, and Windsurf document a direct skill reference, slash form, or mention.
- **Activation through the host:** GitHub Copilot CLI, Gemini CLI, Antigravity, OpenCode, Goose, Roo, and Kiro support the skill files but use a named request, model activation, a management command, consent, or a skills interface.
- **Manual use:** Aider and raw model APIs do not provide all the pieces SVK needs by themselves. Use the Python runtime or add an adapter that provides skill discovery, files, and tools.

Direct-command integrations follow each host’s published skill documentation. Treat integrations with `runtime_tested: false` in `skill/compatibility.json` as beta until runtime certification is available.

See [skill/COMPATIBILITY.md](skill/COMPATIBILITY.md) for the readable matrix and [skill/compatibility.json](skill/compatibility.json) for paths, invocation forms, policy adapters, sources, and test status.

### Chinese and other model families

DeepSeek, GLM, MiniMax, Qwen, Kimi, and other model families can all appear inside several different products. Judge compatibility by the product around the model.

In practice, a model and harness combination must be able to:

- discover and read the relevant skill;
- follow its instructions reliably;
- read and write the project folder;
- run Python and project tools;
- respect the one-task limit and human approval boundaries;
- return enough evidence to finish a task.

### Operating systems

The runtime and installer require Python 3.8+ and use only the standard library. Windows has been exercised for 2.0.0. The repository includes a [Windows, macOS, and Linux CI matrix](.github/workflows/ci.yml) for Python 3.8 and 3.12; macOS and Linux remain preview support until those published CI runs are available.

## Current limitations

SVK 2.0.0 deliberately has a narrow first workflow:

- Interview is for a new or unscaffolded project. It does not merge an existing governance system or migrate an SVK 1.x project.
- The questions and answers are held by the current conversation until the final answers file is submitted. An interrupted interview cannot yet resume from a saved midpoint.
- SVK can decide that research records are needed, but the Python runtime does not browse the web itself. The agent must carry out and cite the research.
- Next manages the task lifecycle, but the agent still performs the actual project-specific work.
- There is no “keep going until everything is finished” command.
- Refresh never upgrades project files.
- The initial file hashes are stored, but 2.0.0 does not yet provide a three-way upgrade or automatic reconciliation workflow.
- Harness paths and invocation forms have been checked against their published documentation, but every row with `runtime_tested: false` remains a beta integration until exercised inside that harness.

## Troubleshooting

### The skills do not appear

1. Run `python installer/install.py --list` and confirm that you used the correct target.
2. Check that the destination contains four SVK skill folders and `.smart-vibe-kit-2`.
3. Use the harness’s skill reload command, skill panel, or a new session.
4. Use the invocation form in [Use SVK in your harness](#use-svk-in-your-harness). Do not assume every host uses `/svk-interview`.
5. Check whether the skill is disabled or denied in the harness.

### Interview refuses the folder

Interview will not write to a filesystem root, your home folder, or a project containing any path it intends to generate. Use a dedicated new folder.

Do not delete an existing file merely to get past the check. First decide whether you meant to start a new project or need a future import workflow for an existing one.

### Check says a task is locked

Another agent may still be working. Confirm its status before removing the lock. The age of the lock alone does not prove that it is abandoned.

### Check reports an interrupted transaction

Do not start another task. Read the paths and transaction ID in the diagnostic, inspect the affected files, and reconcile that specific interruption. SVK detects the condition but does not guess how every partial update should be repaired.

### Check reports that tasks, the charter, or evidence disagree

Check is showing that two records tell different stories. Repair the specific record named in the diagnostic, then run Check again. Regenerating the whole scaffold may destroy decisions made since the interview.

### Can I use SVK in an existing repository?

The runtime can add its files if none of the destination paths exist, but Interview does not yet analyze and merge a mature project’s current plans, rules, or documentation. Treat 2.0.0 as a new-project tool unless you have manually confirmed that the repository has no conflicting operating structure.

### Why did my project get more or fewer files than expected?

First, make sure you are comparing the same thing. `expected_document_count` counts the six core documents, four machine-state records, and documents added by the selected areas. It does not count your application code, tests, assets, dependencies, or SVK’s internal baseline and transaction records. See [Where do the file counts come from?](#where-do-the-file-counts-come-from) for examples.

Then open `.svk/project.json` and look at `signals`, `modules`, and `profile`. They show what SVK understood about the project and which areas it selected. The `expected_document_count` value shows the resulting managed-artifact count.

If the result is wrong, correct the underlying project facts. Do not add or remove files just to reach a preferred count.

### Can another model continue the project?

Yes—that is the purpose of the durable project state. Install SVK for the new harness, open the same folder, and run Refresh. Actual results still depend on the new model’s ability to follow instructions and use its tools reliably.

## For contributors

The implementation is split into two top-level packages. A worked project is included separately:

```text
smart-vibe-kit-200/
  examples/
    pocket-list/  worked project used by the README walkthrough
  installer/   installation, updates, removal, host paths, and installer tests
  skill/       the four skills, shared runtime, schemas, compatibility data, and tests
```

Installation behavior belongs in `installer/`. Project workflow behavior belongs in `skill/`. The installer reads the sibling skill bundle; the skill package does not install itself.

Run the runtime tests:

```text
python -m unittest discover -s skill/tests -v
```

Run the installer tests:

```text
python -m unittest discover -s installer/tests -v
```

Validate the package:

```text
python skill/runtime/svk.py check --package --root skill
```

The CI template runs these checks across Windows, macOS, and Linux on Python 3.8 and 3.12. Use that matrix, or run the commands above with a local Python 3.8 interpreter, to verify Python 3.8 compatibility.

## License

Apache License 2.0. See [LICENSE](LICENSE).
