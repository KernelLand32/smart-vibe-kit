# Refresh runtime contract

Refresh reads `.svk/project.json`, `.svk/state.json`, the generated Markdown, evidence, transactions, and lock state. It performs no writes and returns JSON containing `project`, `profile`, `modules`, `stage`, `active_task`, `blocker`, `next_action`, and `check`.

`check.result` is one of `PASS`, `WARN`, `BLOCKED`, or `ERROR`. Refresh reports that result but does not change it. It returns enough context for a new model session to decide what to do next.
