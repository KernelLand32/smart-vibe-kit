# Refresh runtime contract

Refresh reads the profile, approved plan, revisioned state, governed views, evidence index, receipts, transaction journal, and leases. It performs no writes and returns `project`, `profile`, `modules`, `stage`, `state_revision`, `active_task`, `blocker`, `next_action`, and `check`.

`check.result` is one of `PASS`, `WARN`, `BLOCKED`, or `ERROR`. Refresh reports that result but does not change it. It returns enough context for a new model session to decide what to do next.
