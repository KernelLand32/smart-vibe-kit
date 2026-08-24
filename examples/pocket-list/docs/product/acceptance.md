# Pocket List acceptance examples

## Add a task

Given no data file exists, when the user runs `pocket_list.py --data tasks.json add "Buy tea"`, the command prints `Added 1: Buy tea`, exits successfully, and creates a JSON file containing unfinished task 1.

Given task 1 already exists, when the user starts a new process and adds `Call Sam`, the command creates task 2 without changing task 1.

Given blank task text, when the user runs `add "   "`, the command explains that task text is required, exits unsuccessfully, and leaves the data file byte-for-byte unchanged.

## List unfinished tasks

Given unfinished tasks 1 and 3 and completed task 2, when the user runs `list`, the output contains tasks 1 and 3 in that order and does not contain task 2.

Given no unfinished tasks, when the user runs `list`, the command prints `No unfinished tasks.` and exits successfully.

## Complete a task

Given unfinished task 1, when the user runs `done 1`, the command prints `Completed 1: <text>`, exits successfully, and preserves every other task.

Given task 99 does not exist, when the user runs `done 99`, the command returns a useful error, exits unsuccessfully, and leaves the data unchanged.

## Data safety and portability

Given malformed JSON, every command reports the data problem and leaves the file unchanged. The acceptance suite runs in temporary directories on Windows, macOS, and Linux without network access or third-party packages.
