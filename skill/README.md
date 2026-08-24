# Smart Vibe Kit skill bundle

This folder is the installable behavior package. It contains four explicit user actions and one shared deterministic runtime.

```text
skills/
  svk-interview/
  svk-refresh/
  svk-next/
  svk-check/
runtime/
schemas/
compatibility.json
VERSION
```

The skills are intentionally thin. They route contextual judgment to the agent and deterministic state, generation, checking, locking, and rendering work to `runtime/svk.py`.

Cross-harness claims and their evidence level are documented in [`COMPATIBILITY.md`](COMPATIBILITY.md) and `compatibility.json`.

Installation and removal are deliberately outside this package. See `../installer/README.md` from the source distribution.
