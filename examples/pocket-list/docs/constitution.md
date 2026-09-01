# Project constitution

Project: **Pocket List**

## Mission

Build a small offline command-line task list for one person. The program stores its data locally and keeps working without an internet connection.

## Goals

- Add a task and save it locally
- List unfinished tasks after restarting the program
- Mark a task complete without losing other tasks

## Non-goals

- No accounts or sign-in
- No cloud sync or collaboration
- No graphical or web interface
- No due dates, reminders, tags, or recurring tasks in the first release

## Constraints

- Use Python 3.11 or newer and only the standard library
- Store data in a human-readable local JSON file
- Run without a network connection
- Keep the command syntax and stored-data behavior testable

## Decision principles

1. Preserve user intent and data before optimizing speed.
2. Prefer the smallest change that produces inspectable evidence.
3. Separate facts, assumptions, decisions, and unresolved risks.
4. Keep project state portable across models and coding harnesses.
5. Do not mark a task complete without its stated verification evidence.
