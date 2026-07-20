# Examples

Committed golden bootstrap tree (HabitVault — offline-first habit tracker):

`examples/offline-habit-tracker/`

It must pass:

```bash
python scripts/verify_structure.py --root examples/offline-habit-tracker --bootstrap --strict
```

Regenerate (dev only — `gen_minimal_tree.py` is not installed into user skills dirs):

```bash
python scripts/gen_minimal_tree.py --out examples/offline-habit-tracker --name HabitVault
python scripts/gen_minimal_tree.py --out tests/fixtures/minimal_bootstrap
```

Install scripts copy `examples/offline-habit-tracker/` into the skill install when present.
