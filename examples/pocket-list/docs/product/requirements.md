# Pocket List requirements

## User and problem

Pocket List serves one person who wants a task list that is quick to use from a terminal and remains available offline. The first release should make three everyday actions dependable: capture a task, see unfinished work, and mark work complete.

## First-release requirements

1. `add <text>` creates one unfinished task and confirms its numeric ID.
2. Task text must contain at least one non-whitespace character. Invalid input exits unsuccessfully without changing stored data.
3. `list` prints unfinished tasks in ascending ID order. A new process must see tasks saved by an earlier process.
4. `done <id>` marks exactly one existing unfinished task complete and confirms the change.
5. Unknown or already-completed IDs exit unsuccessfully without changing other tasks.
6. Data is stored in a human-readable local JSON file. A missing file means an empty list; malformed data produces a clear error and is not overwritten.
7. The program runs on Python 3.11 or newer using only the standard library and makes no network requests.

## Explicitly outside the first release

- accounts, sign-in, sync, sharing, and collaboration;
- graphical or browser interfaces;
- due dates, reminders, tags, priorities, and recurring tasks;
- automatic repair of malformed data.

## Product decisions

- IDs increase monotonically and are not reused after completion.
- Completed tasks remain in the JSON file so later versions can expose history without changing the format.
- Commands use `--data <path>` in tests and automation; the default data location is `.pocket-list.json` in the current directory.
