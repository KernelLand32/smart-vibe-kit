# Interview runtime contract

Interview has two phases. `start`, `show`, `checkpoint`, and `abandon` use a durable sibling file named `.<project>.svk-interview.json`, so an unfinished interview does not contaminate the greenfield target. `scaffold` commits only after the complete staged project passes SVK Check.

The final answers object contains ordinary project facts plus `plan`, `verifiers`, `plan_approved`, `plan_reviewer`, and `plan_review_reason`. The plan maps every accepted goal to deliverables and bounded `3.x.x` tasks. Verifiers use argument arrays, never shell strings.

Every goal needs a deliverable and every deliverable needs executable tasks. Oversized tasks require a written `size_waiver`; approval cannot bypass contract validation. The runtime refuses collisions and existing projects, validates the stage, copies only absent paths, validates the final target, and removes the sibling checkpoint only after success.
